import re
import json
import zlib
import asyncio
import inspect
from typing_extensions import override
from typing import Any, Dict, List, Tuple, Type, Union, Mapping, Callable, Optional

from pygtrie import StringTrie
from nonebot.utils import escape_tag
from nonebot.internal.driver import Response
from nonebot.compat import model_dump, type_validate_python
from nonebot.drivers import (
    URL,
    Driver,
    Request,
    WebSocket,
    ForwardDriver,
    HTTPClientMixin,
    WebSocketClientMixin,
)

from nonebot import get_plugin_config
from nonebot.adapters import Adapter as BaseAdapter

from . import event
from .bot import Bot
from .api.model import User
from .config import BotConfig
from .config import Config as KaiheilaConfig
from .message import Message, MessageSegment
from .api.handle import get_api_method, get_api_restype
from .utils import ResultStore, log, _handle_api_result
from .event import (
    Event,
    EventTypes,
    OriginEvent,
    SignalTypes,
    HeartbeatMetaEvent,
    LifecycleMetaEvent,
)
from .exception import (
    TokenError,
    ActionFailed,
    NetworkError,
    ReconnectError,
    ApiNotAvailable,
    RateLimitException,
    UnauthorizedException,
    KaiheilaAdapterException,
)

RECONNECT_INTERVAL = 3.0


class Adapter(BaseAdapter):
    # init all event models
    event_models: StringTrie = StringTrie(separator=".")
    for model_name in dir(event):
        model = getattr(event, model_name)
        if not inspect.isclass(model) or not issubclass(model, OriginEvent):
            continue
        event_models["." + model.__event__] = model

    @override
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.kaiheila_config: KaiheilaConfig = get_plugin_config(KaiheilaConfig)
        self.api_root = "https://www.kaiheila.cn/api/v3/"
        self.connections: Dict[str, WebSocket] = {}
        self.tasks: List[asyncio.Task] = []
        self.setup()

    # OK
    @classmethod
    @override
    def get_name(cls) -> str:
        return "Kaiheila"

    # OK
    def setup(self) -> None:
        if not isinstance(self.driver, HTTPClientMixin):
            raise RuntimeError(
                f"Current driver {self.config.driver} does not support "
                "http client requests! "
                f"{self.get_name()} Adapter need a HTTPClient Driver to work."
            )
        if not isinstance(self.driver, WebSocketClientMixin):
            raise RuntimeError(
                f"Current driver {self.config.driver} does not support "
                "websocket client! "
                f"{self.get_name()} Adapter need a WebSocketClient Driver to work."
            )
        self.driver.on_startup(self.start_forward)
        self.driver.on_shutdown(self.stop_forward)

    @override
    async def request(self, setup: Request) -> Response:
        try:
            response = await super().request(setup)
            if 200 <= response.status_code < 300:
                if not response.content:
                    raise ValueError("Empty response")
                return response
            elif response.status_code == 403:
                raise UnauthorizedException(response)
            elif response.status_code in (404, 405):
                raise ApiNotAvailable
            elif response.status_code == 429:
                raise RateLimitException(response)
            else:
                raise ActionFailed(response)
        except KaiheilaAdapterException:
            raise
        except Exception as e:
            raise NetworkError("API request failed") from e

    @override
    async def _call_api(self, bot: Bot, api: str, **data) -> Any:
        if isinstance(self.driver, ForwardDriver):
            if not self.api_root:
                raise ApiNotAvailable()

            match = re.findall(r"[A-Z]", api)
            if len(match) > 0:
                for m in match:
                    api = api.replace(m, "-" + m.lower())
            api = api.replace("_", "/")

            if api.startswith("/api/v3/"):
                api = api[len("/api/v3/") :]
            elif api.startswith("api/v3"):
                api = api[len("api/v3") :]
            api = api.strip("/")
            return await self._do_call_api(api, data, bot.token)

        else:
            raise ApiNotAvailable

    async def _do_call_api(
        self,
        api: str,
        data: Optional[Mapping[str, Any]] = None,
        token: Optional[str] = None,
    ) -> Any:
        log("DEBUG", f"Calling API <y>{api}</y>")
        data = dict(data) if data is not None else {}

        # 判断 POST 或 GET
        method = get_api_method(api) if not data.get("method") else data.get("method")

        headers = data.get("headers", {})

        files = None
        query = None
        body = None

        if "files" in data:
            files = data["files"]
            del data["files"]
        elif "file" in data:  # 目前只有asset/create接口需要上传文件（大概）
            files = {"file": data["file"]}
            del data["file"]

        if method == "GET":
            query = data
        elif method == "POST":
            body = data

        if token is not None:
            headers["Authorization"] = f"Bot {token}"

        request = Request(
            method,
            self.api_root + api,
            headers=headers,
            params=query,
            data=body,
            files=files,
            timeout=self.config.api_timeout,
        )
        result_type = get_api_restype(api)
        try:
            resp = await self.request(request)
            result = _handle_api_result(resp)
            return type_validate_python(result_type, result) if result_type else None
        except Exception as e:
            raise e

    async def _get_bot_info(self, token: str) -> User:
        return await self._do_call_api("user/me", token=token)

    async def _get_gateway(self, token: str) -> URL:
        result = await self._do_call_api(
            "gateway/index",
            data={"compress": 1 if self.kaiheila_config.compress else 0},
            token=token,
        )
        return result.url

    async def start_forward(self) -> None:
        for bot in self.kaiheila_config.kaiheila_bots:
            self.tasks.append(asyncio.create_task(self._forward_ws(bot)))

    async def stop_forward(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(
            *(asyncio.wait_for(task, timeout=10) for task in self.tasks),
            return_exceptions=True,
        )

    async def _forward_ws(self, bot_config: BotConfig) -> None:
        bot: Optional[Bot] = None

        heartbeat_task: Optional[asyncio.Task] = None

        while True:
            try:
                try:
                    url = URL(await self._get_gateway(bot_config.token))
                except TokenError as e:
                    log(
                        "ERROR",
                        f"<r><bg #f8bbd0>Token {escape_tag(bot_config.token)} was invalid. "
                        "Please get a new token from https://developer.kaiheila.cn/app/index </bg #f8bbd0></r>",
                        e,
                    )
                    return
                except Exception as e:
                    log(
                        "ERROR",
                        f"<r><bg #f8bbd0>Failed to get the Gateway URL for token {escape_tag(bot_config.token)}. "
                        "Trying to reconnect...</bg #f8bbd0></r>",
                        e,
                    )
                    continue

                headers = {}
                if bot_config.token:
                    headers["Authorization"] = f"Bot {bot_config.token}"
                request = Request("GET", url, headers=headers)

                async with self.websocket(request) as ws:
                    log(
                        "DEBUG",
                        f"WebSocket Connection to {escape_tag(str(url))} established",
                    )
                    try:
                        data_decompress_func = (
                            zlib.decompress
                            if self.kaiheila_config.compress
                            else lambda x: x
                        )
                        while True:
                            data = await ws.receive()
                            data = data_decompress_func(data)
                            json_data = json.loads(data)
                            event = self.json_to_event(
                                json_data,
                                bot and bot.self_id,
                                kaiheila_config=self.kaiheila_config,
                            )
                            if not event:
                                continue
                            if not bot:
                                if (
                                    not isinstance(event, LifecycleMetaEvent)
                                    or event.sub_type != "connect"
                                ):
                                    continue
                                bot_info = await self._get_bot_info(bot_config.token)
                                self_id = bot_info.id_
                                bot = Bot(
                                    self, self_id, bot_info.username, bot_config.token
                                )
                                self.connections[self_id] = ws
                                self.bot_connect(bot)

                                # start heartbeat
                                heartbeat_task = asyncio.create_task(
                                    self.start_heartbeat(bot)
                                )

                                log(
                                    "INFO",
                                    f"<y>Bot {escape_tag(self_id)}</y> connected",
                                )
                            asyncio.create_task(bot.handle_event(event))
                    except ReconnectError as e:
                        log(
                            "INFO",
                            "<r><bg #f8bbd0>Server requests reconnect"
                            f"{'for bot ' + escape_tag(bot.self_id) if bot else ''}.</bg #f8bbd0></r>",
                            e,
                        )
                    except TokenError:
                        raise
                    except Exception as e:
                        log(
                            "ERROR",
                            "<r><bg #f8bbd0>Error while process data from websocket"
                            f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                            e,
                        )
                    finally:
                        if heartbeat_task:
                            heartbeat_task.cancel()
                            heartbeat_task = None

                        try:
                            await ws.close()
                        except:  # noqa: E722
                            pass

                        if bot:
                            # 清空本地的 sn 计数
                            ResultStore.set_sn(bot.self_id, 0)
                            self.connections.pop(bot.self_id, None)
                            self.bot_disconnect(bot)
                            bot = None
            except Exception as e:
                log(
                    "ERROR",
                    "<r><bg #f8bbd0>Error while setup websocket to "
                    f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                    e,
                )

            await asyncio.sleep(RECONNECT_INTERVAL)

    async def start_heartbeat(self, bot: Bot) -> None:
        """
        每30s一次心跳
        :return:
        """
        while self.connections.get(bot.self_id):
            if self.connections.get(bot.self_id).closed:
                break
            try:
                await self.connections.get(bot.self_id).send(
                    json.dumps(
                        {
                            "s": 2,
                            "sn": ResultStore.get_sn(bot.self_id),  # 客户端目前收到的最新的消息 sn
                        }
                    )
                )
                await asyncio.sleep(26)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log(
                    "ERROR",
                    "<r><bg #f8bbd0>Error while sending heartbeat for bot"
                    f"{escape_tag(bot.self_id)}. Will retry after 1s ...</bg #f8bbd0></r>",
                    e,
                )
                await asyncio.sleep(1)

    @classmethod
    def json_to_event(
        cls,
        json_data: Any,
        self_id: Optional[str] = None,
        *,
        kaiheila_config: KaiheilaConfig,
    ) -> Union[OriginEvent, Event, None]:
        if not isinstance(json_data, dict):
            return None

        signal = json_data["s"]

        if signal == SignalTypes.HELLO:
            if json_data["d"]["code"] == 0:
                data = json_data["d"]
                data["post_type"] = "meta_event"
                data["sub_type"] = "connect"
                data["meta_event_type"] = "lifecycle"
                return type_validate_python(LifecycleMetaEvent, data)
            elif json_data["d"]["code"] == 40103:
                raise ReconnectError
            elif json_data["d"]["code"] == 40101:
                raise TokenError("无效的 token")
            elif json_data["d"]["code"] == 40102:
                raise TokenError("token 验证失败")
        elif signal == SignalTypes.PONG:
            data = {"post_type": "meta_event", "meta_event_type": "heartbeat"}
            log(
                "TRACE",
                f"<y>Bot {escape_tag(str(self_id))}</y> HeartBeat",
            )
            return type_validate_python(HeartbeatMetaEvent, data)
        elif signal == SignalTypes.EVENT:
            ResultStore.set_sn(self_id, json_data["sn"])
        elif signal == SignalTypes.RECONNECT:
            raise ReconnectError
        elif signal == SignalTypes.RESUME_ACK:
            # 不存在的signal，resume是不可能resume的，这辈子都不会resume的，出了问题直接重连
            return

        # 屏蔽 Bot 自身
        if json_data["d"].get("author_id") == self_id :
            return
        # 屏蔽其他Bot消息
        if json_data["d"].get("extra", {}).get("author", {}).get("bot") and kaiheila_config.kaiheila_ignore_other_bots:
            return
        try:
            data = json_data["d"]
            extra = data.get("extra")

            data["self_id"] = self_id
            data["group_id"] = data.get("target_id")
            data["time"] = data.get("msg_timestamp")
            data["user_id"] = (
                data.get("author_id") if data.get("author_id") != "1" else "SYSTEM"
            )

            if data["type"] == EventTypes.sys:
                data["post_type"] = "notice"
                data["notice_type"] = extra.get("type")
                message = Message.template("{}").format(data["content"])
                data["message"] = message
                # data['notice_type'] = data.get('channel_type').lower()
                # data['notice_type'] = 'private' if data['notice_type'] == 'person' else data['notice_type']
            else:
                data["post_type"] = "message"
                data["sub_type"] = [
                    i.name.lower() for i in EventTypes if i.value == extra.get("type")
                ][0]
                data["message_type"] = data.get("channel_type").lower()
                data["message_type"] = (
                    "private"
                    if data["message_type"] == "person"
                    else data["message_type"]
                )
                data["extra"]["content"] = data.get("content")
                data["event"] = data["extra"]

            data["message_id"] = data.get("msg_id")
            post_type = data["post_type"]
            detail_type = data.get(f"{post_type}_type")
            detail_type = f".{detail_type}" if detail_type else ""
            sub_type = data.get("sub_type")
            sub_type = f".{sub_type}" if sub_type else ""

            event_name: str = post_type + detail_type + sub_type
            if kaiheila_config.kaiheila_ignore_events and event_name.startswith(kaiheila_config.kaiheila_ignore_events):
                return

            models = cls.get_event_model(event_name)
            for model in models:
                try:
                    event = type_validate_python(model, data)
                    break
                except Exception as e:
                    log("DEBUG", "Event Parser Error", e)
            else:
                event = type_validate_python(Event, json_data)
            log("DEBUG", escape_tag(str(model_dump(event))))
            return event
        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Failed to parse event. "
                f"Raw: {escape_tag(str(json_data))}</bg #f8bbd0></r>",
                e,
            )

    @classmethod
    def add_custom_model(cls, model: Type[Event]) -> None:
        if not model.__event__:
            raise ValueError("Event model's `__event__` attribute must be set")
        cls.event_models["." + model.__event__] = model

    @classmethod
    def get_event_model(cls, event_name: str) -> List[Type[Event]]:
        """
        :说明:

          根据事件名获取对应 ``Event Model`` 及 ``FallBack Event Model`` 列表, 不包括基类 ``Event``

        :返回:

          - ``List[Type[Event]]``
        """
        return [model.value for model in cls.event_models.prefixes("." + event_name)][
            ::-1
        ]

    @classmethod
    def custom_send(
        cls,
        send_func: Callable[[Bot, Event, Union[str, Message, MessageSegment]], None],
    ):
        setattr(Bot, "send_handler", send_func)
