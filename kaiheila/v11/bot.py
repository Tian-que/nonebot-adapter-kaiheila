import re
from typing import Any, Union, Callable, TYPE_CHECKING
import re

from nonebot.typing import overrides
from nonebot.message import handle_event

from nonebot.adapters import Bot as BaseBot
from yarl import URL

from .utils import log
from .message import Message, MessageSegment, MessageSerializer
from .event import Event, MessageEvent

if TYPE_CHECKING:
    from .event import Event
    from .adapter import Adapter
    from .message import Message, MessageSegment


def _check_at_me(bot: "Bot", event: MessageEvent):
    """
    :说明:

      检查消息开头或结尾是否存在 @机器人，去除并赋值 ``event.to_me``

    :参数:

      * ``bot: Bot``: Bot 对象
      * ``event: Event``: Event 对象
    """
    if not isinstance(event, MessageEvent):
        return

    # ensure message not empty
    # if not event.message:
    #     event.message.append(MessageSegment.text(""))

    if event.message_type == "private":
        event.to_me = True
    else:
        if bot.self_id in event.extra.mention:
            event.to_me = True
            for at in re.finditer(r"\@(?P<username>.+)\#" + bot.self_id + "+", event.message[0].data["content"]):
                if at.start() == 0:
                    event.message[0].data["content"] = event.message[0].data["content"][at.end():].lstrip()
                elif at.pos + at.end() == len(event.message[0].data["content"].rstrip()):
                    event.message[0].data["content"] = event.message[0].data["content"][:at.start()].rstrip()
                # else:
                #     event.message[0].data["content"] = event.message[0].data["content"][:at.pos] + event.message[0].data["content"][at.end():]
                break


def _check_nickname(bot: "Bot", event: MessageEvent):
    """
    :说明:

      检查消息开头是否存在昵称，去除并赋值 ``event.to_me``

    :参数:

      * ``bot: Bot``: Bot 对象
      * ``event: Event``: Event 对象
    """
    first_msg_seg = event.message[0]
    if first_msg_seg.type != "text":
        return

    first_text = first_msg_seg.data["content"]

    nicknames = set(filter(lambda n: n, bot.config.nickname))
    if nicknames:
        # check if the user is calling me with my nickname
        nickname_regex = "|".join(nicknames)
        m = re.search(rf"^({nickname_regex})([\s,，]*|$)", first_text, re.IGNORECASE)
        if m:
            nickname = m.group(1)
            log("DEBUG", f"User is calling me {nickname}")
            event.to_me = True
            first_msg_seg.data["content"] = first_text[m.end() :]


async def send(
    bot: "Bot",
    event: Event,
    message: Union[str, Message, MessageSegment],
    reply_sender: bool = False,
    is_temp_msg: bool = False,
    **kwargs: Any,
) -> Any:

    # 保证Message格式
    message = message if isinstance(message, Message) else Message(message)

    # 构造参数
    params = {}

    # type & content
    params["type"], data = await MessageSerializer(message).serialize()
    if params["type"] in (1, 9, 10):
        params["content"] = data
    else:
        raise ValueError(f"Invalid message type: {params['type']}")

    # quote
    if reply_sender:
        params["quote"] = getattr(event, "message_id")

    # api 
    if event.channel_type == 'GROUP':

        # temp_target_id
        if is_temp_msg:
            params["temp_target_id"] = getattr(event, "user_id")

        # target_id
        if getattr(event, "target_id", None):
            params["target_id"] = getattr(event, "target_id")

        api = 'message/create'
    else:
        # target_id
        if getattr(event, "target_id", None):
            params["target_id"] = getattr(event, "user_id")

        api = 'direct-message/create'

    return await bot.call_api(api = api, **params)


class Bot(BaseBot):
    """
    Kaiheila Bot 适配。
    """

    send_handler: Callable[
        ["Bot", Event, Union[str, Message, MessageSegment]], Any
    ] = send

    def __init__(self, adapter: "Adapter", self_id: str, session_id: str, name: str, token: str):
        """
        :参数:

          * ``adapter: Adapter``: 适配器
          * ``self_id: str``: 机器人 ID
          * ``session_id``: 会话 ID
          * ``name: str``: 机器人用户名
          * ``token``: 机器人 token

        """
        super().__init__(adapter, self_id)
        self.session_id: str = session_id
        self_name: str = name
        self.token: str = token

    @overrides(BaseBot)
    async def call_api(self, api: str, **data) -> Any:
        """
        :说明:

          调用 kaiheila 协议 API

        :参数:

          * ``api: str``: API 名称
          * ``**data: Any``: API 参数

        :返回:

          - ``Any``: API 调用返回数据

        :异常:

          - ``NetworkError``: 网络错误
          - ``ActionFailed``: API 调用失败
        """
        return await super().call_api(api, **data)

    async def handle_event(self, event: Event) -> None:
        if isinstance(event, MessageEvent):
            _check_at_me(self, event)
            _check_nickname(self, event)
            pass

        await handle_event(self, event)

    @overrides(BaseBot)
    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        **kwargs,
    ) -> Any:

        """
        :说明:

          根据 ``event``  向触发事件的主体发送消息。

        :参数:

          * ``event: Event``: Event 对象
          * ``message: Union[str, Message, MessageSegment]``: 要发送的消息
          * ``reply_sender: bool``: 是否回复事件主体
          * ``is_temp_msg: bool``: 是否临时消息
          * ``**kwargs``: 覆盖默认参数

        :返回:

          - ``Any``: API 调用返回数据

        :异常:

          - ``ValueError``: 缺少 ``user_id``, ``group_id``
          - ``NetworkError``: 网络错误
          - ``ActionFailed``: API 调用失败
        """
        return await self.__class__.send_handler(self, event, message, **kwargs)

    async def upload_file(self, file_path: str) -> str:
        result = await self.call_api("asset/create", file = open(file_path, "rb"))
        return result.get("url")
