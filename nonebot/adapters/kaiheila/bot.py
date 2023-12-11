from pathlib import Path
from io import BytesIO, BufferedReader
from typing_extensions import override
from typing import TYPE_CHECKING, Any, Union, Literal, BinaryIO, Callable, Optional

from nonebot.message import handle_event

from nonebot.adapters import Bot as BaseBot

from .event import Event, MessageEvent
from .utils import log, escape_kmarkdown
from .api import ApiClient, MessageCreateReturn
from .message import (
    Text,
    Mention,
    Message,
    KMarkdown,
    MessageSegment,
    MessageSerializer,
)

if TYPE_CHECKING:
    from os import PathLike

    from .adapter import Adapter


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
    if not event.message:
        event.message.append(MessageSegment.text(""))

    if event.message_type == "private":
        event.to_me = True
        return

    def _is_at_me_seg(seg: MessageSegment):
        return isinstance(seg, Mention) and seg.data["user_id"] == bot.self_id

    # check the first segment
    if _is_at_me_seg(event.message[0]):
        event.to_me = True
        event.message.pop(0)

        # 去除mention之后的空格
        if event.message and isinstance(event.message[0], Text):
            event.message[0].plain_text = event.message[0].plain_text.lstrip()
            if not event.message[0].plain_text:
                del event.message[0]

    if not event.to_me:
        # check the last segment
        i = -1
        last_msg_seg = event.message[i]
        if (
            isinstance(last_msg_seg, Text)
            and not last_msg_seg.plain_text.strip()
            and len(event.message) >= 2
        ):
            i -= 1
            last_msg_seg = event.message[i]

        if _is_at_me_seg(last_msg_seg):
            event.to_me = True
            del event.message[i:]

    # 避免消息为空
    if event.message == 0:
        event.message.append(MessageSegment.text(""))


def _check_nickname(bot: "Bot", event: MessageEvent):
    """
    :说明:

      检查消息开头是否存在昵称，去除并赋值 ``event.to_me``

    :参数:

      * ``bot: Bot``: Bot 对象
      * ``event: Event``: Event 对象
    """
    nicknames = set(filter(lambda n: n, bot.config.nickname))
    first_seg = event.message[0]

    if isinstance(first_seg, Text):
        first_text = first_seg.data["text"]

        for nickname in nicknames:
            if first_text.startswith(nickname):
                log("DEBUG", f"User is calling me {nickname}")
                event.to_me = True
                first_seg.data["text"] = first_text.removeprefix(nickname)
                break
    elif isinstance(first_seg, KMarkdown):
        first_text = first_seg.data["raw_content"]

        for nickname in nicknames:
            if first_text.startswith(nickname):
                log("DEBUG", f"User is calling me {nickname}")
                event.to_me = True
                first_seg.data["raw_content"] = first_text.removeprefix(nickname)
                first_seg.data["content"] = first_seg.data["content"].removeprefix(
                    escape_kmarkdown(nickname)
                )
                break


async def send(
    bot: "Bot",
    event: Event,
    message: Union[str, Message, MessageSegment],
    reply_sender: bool = False,
    is_temp_msg: bool = False,
    **kwargs: Any,
) -> Any:
    # 构造参数
    params = {**kwargs}

    # quote
    if reply_sender:
        params.setdefault("quote", getattr(event, "message_id"))

    # message_type
    if event.channel_type == "GROUP":
        params.setdefault("message_type", "channel")

        # temp_target_id
        if is_temp_msg:
            params.setdefault("user_id", getattr(event, "user_id"))

        # target_id
        if getattr(event, "target_id", None):
            params.setdefault("channel_id", getattr(event, "target_id"))
    else:
        params.setdefault("message_type", "private")

        # target_id
        if getattr(event, "target_id", None):
            params.setdefault("user_id", getattr(event, "user_id"))

    params.setdefault("message", message)

    return await bot.send_msg(**params)


class Bot(BaseBot, ApiClient):
    """
    Kaiheila Bot 适配。
    """

    send_handler: Callable[
        ["Bot", Event, Union[str, Message, MessageSegment], bool, bool], Any
    ] = send

    def __init__(self, adapter: "Adapter", self_id: str, name: str, token: str):
        """
        :参数:

          * ``adapter: Adapter``: 适配器
          * ``self_id: str``: 机器人 ID
          * ``name: str``: 机器人用户名
          * ``token``: 机器人 token

        """
        super().__init__(adapter, self_id)
        self.self_name: str = name
        self.token: str = token

    @override
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

    @override
    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        reply_sender: bool = False,
        is_temp_msg: bool = False,
        **kwargs,
    ) -> MessageCreateReturn:
        """
        :说明:

          根据 ``event``  向触发事件的主体发送消息。

        :参数:

          * ``event: Event``: Event 对象
          * ``message: Union[str, Message, MessageSegment]``: 要发送的消息
          * ``reply_sender: bool``: 是否回复原消息
          * ``is_temp_msg: bool``: 是否临时消息
          * ``**kwargs``: 覆盖默认参数

        :返回:

          - ``Any``: API 调用返回数据

        :异常:

          - ``ValueError``: 缺少 ``user_id``, ``channel_id``
          - ``NetworkError``: 网络错误
          - ``ActionFailed``: API 调用失败
        """
        return await self.__class__.send_handler(
            self, event, message, reply_sender, is_temp_msg, **kwargs
        )

    async def send_private_msg(
        self,
        *,
        user_id: str,
        message: Union[str, Message, MessageSegment],
        quote: Optional[str] = None,
    ) -> MessageCreateReturn:
        """发送私聊消息。

        user_id: 对方用户ID
        message: 要发送的内容，字符串类型将作为纯文本消息发送
        quote: 回复某条消息的消息ID
        """
        return await self.send_msg(
            message_type="private", user_id=user_id, message=message, quote=quote
        )

    async def send_channel_msg(
        self,
        *,
        channel_id: str,
        message: Union[str, Message, MessageSegment],
        quote: Optional[str] = None,
    ) -> MessageCreateReturn:
        """发送频道消息。

        channel_id: 频道ID
        message: 要发送的内容，字符串类型将作为纯文本消息发送
        quote: 回复某条消息的消息ID
        """
        return await self.send_msg(
            message_type="channel", channel_id=channel_id, message=message, quote=quote
        )

    async def send_temp_msg(
        self,
        *,
        user_id: str,
        channel_id: str,
        message: Union[str, Message, MessageSegment],
        quote: Optional[str] = None,
    ) -> MessageCreateReturn:
        """发送频道临时消息。该消息不会存数据库，但是会在频道内只给该用户推送临时消息。用于在频道内针对用户的操作进行单独的回应通知等。

        channel_id: 频道ID
        message: 要发送的内容，字符串类型将作为纯文本消息发送
        quote: 回复某条消息的消息ID
        """
        return await self.send_msg(
            message_type="temp",
            user_id=user_id,
            channel_id=channel_id,
            message=message,
            quote=quote,
        )

    async def send_msg(
        self,
        *,
        message_type: Literal["private", "channel", "temp", ""] = "",
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        message: Union[str, Message, MessageSegment],
        quote: Optional[str] = None,
    ) -> MessageCreateReturn:
        """发送消息。

        参数:
            message_type: 消息类型，支持 `private`、`channel`、`temp`，分别对应私聊、频道，如不传入，则根据传入的 `*_id` 参数判断
            user_id: 对方用户ID（消息类型为 `private`、`temp` 时需要）
            channel_id: 频道ID（消息类型为 `channel`、`temp` 时需要）
            message: 要发送的内容，字符串类型将作为纯文本消息发送
            quote: 回复某条消息的消息ID
        """
        # 接口文档：
        # https://developer.kaiheila.cn/doc/http/direct-message#%E5%8F%91%E9%80%81%E7%A7%81%E4%BF%A1%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF
        # https://developer.kaiheila.cn/doc/http/message#%E5%8F%91%E9%80%81%E9%A2%91%E9%81%93%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF
        params = {}

        # type & content
        if isinstance(message, Message):
            serialized_data = await MessageSerializer(message).serialize(self)
        else:
            serialized_data = await MessageSerializer(Message(message)).serialize(self)
        params = {**params, **serialized_data}

        # quote
        if quote is not None:
            params["quote"] = quote

        # target_id & api
        if message_type == "channel":
            params["target_id"] = channel_id
            api = "message_create"
        elif message_type == "private":
            params["target_id"] = user_id
            api = "directMessage_create"
        elif message_type == "temp":
            params["target_id"] = channel_id
            params["temp_target_id"] = user_id
            api = "message_create"
        else:
            if channel_id and not user_id:
                params["target_id"] = channel_id
                api = "message_create"
            elif not channel_id and user_id:
                params["target_id"] = user_id
                api = "directMessage_create"
            elif channel_id and user_id:
                params["target_id"] = channel_id
                params["temp_target_id"] = user_id
                api = "message_create"
            else:
                raise ValueError("channel_id 和 user_id 不能同时为 None")

        return await self.call_api(api, **params)

    async def upload_file(
        self,
        file: Union[str, "PathLike[str]", BinaryIO, bytes],
        filename: Optional[str] = None,
    ) -> str:
        """
        上传文件。

        参数:
            file: 文件，可以是文件路径（str, PathLike[str]）、打开的文件流（BinaryIO）、或二进制数据（bytes）
            filename: 文件名

        返回值:
            文件的 URL
        """
        if isinstance(file, BytesIO):
            file = file.getvalue()
        elif isinstance(file, BufferedReader):
            file = file.read()
        elif isinstance(file, str) or isinstance(file, Path):
            with open(file, "rb") as img:
                file = img.read()
        # 经过测试，服务器会用从文件读取到的mime覆盖掉我们传过去的mime
        file = (filename or "upload-file", file, "application/octet-stream")
        result = await self.asset_create(file=file)
        return result.url
