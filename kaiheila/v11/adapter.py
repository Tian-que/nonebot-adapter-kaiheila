import hmac
import json
import asyncio
import inspect
from typing import Any, Dict, List, Type, Union, Callable, Optional, cast

from pygtrie import StringTrie
from nonebot.typing import overrides
from nonebot.utils import DataclassEncoder, escape_tag
from nonebot.drivers import (
    URL,
    Driver,
    Request,
    Response,
    WebSocket,
    ForwardDriver,
    ReverseDriver,
    HTTPServerSetup,
    WebSocketServerSetup,
)

API = f'https://www.kaiheila.cn/api/v3'

import aiohttp
import zlib
from nonebot.adapters import Adapter as BaseAdapter

from . import event
from .bot import Bot
from .config import Config as KaiheilaConfig
from .event import Event, LifecycleMetaEvent, MessageEvent, NoticeEvent
from .message import Message, MessageSegment
from .exception import NetworkError, ApiNotAvailable
from .utils import ResultStore, log, _handle_api_result

RECONNECT_INTERVAL = 3.0


class Adapter(BaseAdapter):

    # init all event models
    event_models: StringTrie = StringTrie(separator=".")
    for model_name in dir(event):
        model = getattr(event, model_name)
        if not inspect.isclass(model) or not issubclass(model, Event):
            continue
        event_models["." + model.__event__] = model

    @overrides(BaseAdapter)
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.kaiheila_config: KaiheilaConfig = KaiheilaConfig(**self.config.dict())
        self.connections: Dict[str, WebSocket] = {}
        self.tasks: List[asyncio.Task] = []
        self.setup()

    # OK
    @classmethod
    @overrides(BaseAdapter)
    def get_name(cls) -> str:
        return "Kaiheila"

    # OK
    def setup(self) -> None:
        if not isinstance(self.driver, ForwardDriver):
            log(
                "WARNING",
                f"Current driver {self.config.driver} don't support forward connections! Ignored",
            )
        else:
            self.driver.on_startup(self.start_forward)
            self.driver.on_shutdown(self.stop_forward)

    @overrides(BaseAdapter)
    async def _call_api(self, bot: Bot, api: str, **data) -> Any:
        websocket = self.connections.get(bot.self_id, None)
        log("DEBUG", f"Calling API <y>{api}</y>")
        if websocket:
            seq = ResultStore.get_seq()
            json_data = json.dumps(
                {"action": api, "params": data, "echo": {"seq": seq}},
                cls=DataclassEncoder,
            )
            await websocket.send(json_data)
            return _handle_api_result(
                await ResultStore.fetch(bot.self_id, seq, self.config.api_timeout)
            )

        elif isinstance(self.driver, ForwardDriver):
            api_root = self.config.api_root.get(bot.self_id)
            if not api_root:
                raise ApiNotAvailable
            elif not api_root.endswith("/"):
                api_root += "/"

            headers = {"Content-Type": "application/json"}
            if self.kaiheila_config.onebot_access_token is not None:
                headers["Authorization"] = (
                    "Bearer " + self.kaiheila_config.onebot_access_token
                )

            request = Request(
                "POST",
                api_root + api,
                headers=headers,
                content=json.dumps(data, cls=DataclassEncoder),
                timeout=self.config.api_timeout,
            )

            try:
                response = await self.driver.request(request)

                if 200 <= response.status_code < 300:
                    if not response.content:
                        raise ValueError("Empty response")
                    result = json.loads(response.content)
                    return _handle_api_result(result)
                raise NetworkError(
                    f"HTTP request received unexpected "
                    f"status code: {response.status_code}"
                )
            except NetworkError:
                raise
            except Exception as e:
                raise NetworkError("HTTP request failed") from e
        else:
            raise ApiNotAvailable

    async def _handle_ws(self, websocket: WebSocket) -> None:
        self_id = websocket.request.headers.get("x-self-id")

        # check self_id
        if not self_id:
            log("WARNING", "Missing X-Self-ID Header")
            await websocket.close(1008, "Missing X-Self-ID Header")
            return
        elif self_id in self.bots:
            log("WARNING", f"There's already a bot {self_id}, ignored")
            await websocket.close(1008, "Duplicate X-Self-ID")
            return

        # check access_token
        response = self._check_access_token(websocket.request)
        if response is not None:
            content = cast(str, response.content)
            await websocket.close(1008, content)
            return

        await websocket.accept()
        bot = Bot(self, self_id)
        self.connections[self_id] = websocket
        self.bot_connect(bot)

        log("INFO", f"<y>Bot {escape_tag(self_id)}</y> connected")

        try:
            while True:
                data = await websocket.receive()
                json_data = json.loads(data)
                event = self.json_to_event(json_data)
                if event:
                    asyncio.create_task(bot.handle_event(event))
        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Error while process data from websocket"
                f"for bot {escape_tag(self_id)}.</bg #f8bbd0></r>",
                e,
            )
        finally:
            try:
                await websocket.close()
            except Exception:
                pass
            self.connections.pop(self_id, None)
            self.bot_disconnect(bot)

    def _check_signature(self, request: Request) -> Optional[Response]:
        x_signature = request.headers.get("x-signature")

        secret = self.kaiheila_config.onebot_secret
        if secret:
            if not x_signature:
                log("WARNING", "Missing Signature Header")
                return Response(401, content="Missing Signature", request=request)

            if request.content is None:
                return Response(400, content="Missing Content", request=request)

            body: bytes = (
                request.content
                if isinstance(request.content, bytes)
                else request.content.encode("utf-8")
            )
            sig = hmac.new(secret.encode("utf-8"), body, "sha1").hexdigest()
            if x_signature != "sha1=" + sig:
                log("WARNING", "Signature Header is invalid")
                return Response(403, content="Signature is invalid")

    def _check_access_token(self, request: Request) -> Optional[Response]:
        token = get_auth_bearer(request.headers.get("authorization"))

        access_token = self.kaiheila_config.onebot_access_token
        if access_token and access_token != token:
            msg = (
                "Authorization Header is invalid"
                if token
                else "Missing Authorization Header"
            )
            log(
                "WARNING",
                msg,
            )
            return Response(
                403,
                content=msg,
            )

    async def start_forward(self) -> None:
        for bot in self.kaiheila_config.bots:
            try:
                # json_serialize=json.dumps
                headers = {
                    'Authorization': f'Bot {bot["token"]}',
                    'Content-type': 'application/json'
                }
                params = {'compress': 1 if self.kaiheila_config.compress else 0}
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{API}/gateway/index",
                                            headers=headers,
                                            params=params) as resp:
                            
                        result = await resp.json()
                    url = _handle_api_result(result)["url"]

                    bot["gateway"] = _handle_api_result(result)["url"]

                    ws_url = URL(url)
                    self.tasks.append(asyncio.create_task(self._forward_ws(ws_url, bot["token"], bot["client_id"])))
            except Exception as e:
                log(
                    "ERROR",
                    f"<r><bg #f8bbd0>Bad url {escape_tag(url)} "
                    "in onebot forward websocket config</bg #f8bbd0></r>",
                    e,
                )

    async def stop_forward(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def _forward_ws(self, url: URL, token: str, client_id: str) -> None:
        headers = {}
        if token:
            headers[
                "Authorization"
            ] = f"Bot {token}"
        request = Request("GET", url, headers=headers)

        bot: Optional[Bot] = None

        while True:
            try:
                ws = await self.websocket(request)
            except Exception as e:
                log(
                    "ERROR",
                    "<r><bg #f8bbd0>Error while setup websocket to "
                    f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                    e,
                )
                await asyncio.sleep(RECONNECT_INTERVAL)
                continue

            log("DEBUG", f"WebSocket Connection to {escape_tag(str(url))} established")
            try:
                ws.receive_func = ws.receive_bytes if self.kaiheila_config.compress else ws.receive
                data_decompress_func = zlib.decompress if self.kaiheila_config.compress else lambda x: x
                while True:
                    try:
                        try:
                            data = await ws.receive_func()
                        except:
                            data = await ws.receive_bytes()
                        data = data_decompress_func(data)
                        json_data = json.loads(data)
                        event = self.json_to_event(json_data, bot and client_id, client_id)
                        if not event:
                            continue
                        if not bot:
                            # if (
                            #     not isinstance(event, LifecycleMetaEvent)
                            #     or event.sub_type != "connect"
                            # ):
                            #     continue
                            self_id = client_id
                            bot = Bot(self, str(self_id), event.get_session_id)
                            self.connections[str(self_id)] = ws
                            self.bot_connect(bot)
                            log(
                                "INFO",
                                f"<y>Bot {escape_tag(str(self_id))}</y> connected",
                            )
                        asyncio.create_task(bot.handle_event(event))
                    except Exception as e:
                        log(
                            "ERROR",
                            "<r><bg #f8bbd0>Error while process data from websocket"
                            f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                            e,
                        )
                        break
            finally:
                try:
                    await ws.close()
                except Exception:
                    pass
                if bot:
                    self.connections.pop(bot.self_id, None)
                    self.bot_disconnect(bot)
                    bot = None

            await asyncio.sleep(RECONNECT_INTERVAL)

    @classmethod
    def json_to_event(
        cls, json_data: Any, self_id: Optional[str] = None, client_id: Optional[str] = '',
    ) -> Optional[Event]:
        if not isinstance(json_data, dict):
            return None

        signal = json_data['s']

        # HELLO 成功连接WS的回执
        if signal == 1 and json_data['d']['code'] == 0:
            data = json_data['d']
            data["post_type"] = "meta_event"
            data["sub_type"] = 'connect'
            data["meta_event_type"] = "lifecycle"
            return LifecycleMetaEvent.parse_obj(data)

        if "type" not in json_data["d"]:
            if self_id is not None:
                ResultStore.add_result(self_id, json_data)
            return



        # PONG 心跳包，先不处理
        # Todo: 心跳包处理
        if signal == 3:
            return

        # 先屏蔽除 Event 的其他包
        # Todo: remove it
        if signal != 0:
            return

        try:
            data = json_data['d']
            extra = data.get("extra")

            data['self_id'] = self_id
            data['sub_type'] = extra.get('type')
            data['message_type'] = data.get('channel_type')
            message = Message.template("{}").format(data["content"])
            data['message'] = message

            if data['type'] == 255:
                event = NoticeEvent.parse_obj(data)
            else:
                event = MessageEvent.parse_obj(data)



            # post_type = json_data["post_type"]
            # detail_type = json_data.get(f"{post_type}_type")
            # detail_type = f".{detail_type}" if detail_type else ""
            # sub_type = json_data.get("sub_type")
            # sub_type = f".{sub_type}" if sub_type else ""
            # models = cls.get_event_model(post_type + detail_type + sub_type)
            # for model in models:
            #     try:
            #         event = model.parse_obj(json_data)
            #         break
            #     except Exception as e:
            #         log("DEBUG", "Event Parser Error", e)
            # else:
            #     event = Event.parse_obj(json_data)

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
