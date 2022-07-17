from dataclasses import dataclass
from typing import Any, Type, Tuple, Union, Mapping, Iterable, Dict, cast

from deprecated import deprecated
from kmarkdown_it import KMarkdownIt
from lazy import lazy
from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment
from nonebot.typing import overrides

from .exception import UnsupportedMessageType

msg_type_map = {
    "text": 1,
    "image": 2,
    "video": 3,
    "file": 4,
    "audio": 8,
    "Kmarkdown": 9,
    "Card": 10,
}

# 根据协议消息段类型显示消息段内容
segment_text = {
    "text": "[文字]",
    "image": "[图片]",
    "video": "[视频]",
    "file": "[文件]",
    "audio": "[音频]",
    "kmarkdown": "[Kmarkdown消息]",
    "card": "[卡片消息]",
}

kmd_it = KMarkdownIt()


class MessageSegment(BaseMessageSegment["Message"]):
    """
    开黑啦 协议 MessageSegment 适配。具体方法参考协议消息段类型或源码。

    https://developer.kaiheila.cn/doc/event/message
    """

    # 已知：
    # command/shell_command使用message_seg = Message[0]; str(message_seg) if message_seg.is_text()
    # startswith/endswith/keyword使用event.get_plaintext()
    # regex使用str(Message)

    @classmethod
    @overrides(BaseMessageSegment)
    def get_message_class(cls) -> Type["Message"]:
        return Message

    def __str__(self) -> str:
        if self.type in ["text", "KMarkdown"]:
            return str(self.data["content"])
        elif self.type == "at":
            return str(f"@{self.data['user_name']}")
        else:
            return segment_text.get(self.type, "[未知类型消息]")

    @lazy
    def plain_text(self):
        if self.type == "text":
            return str(self.data["content"])
        elif self.type == "KMarkdown":
            return kmd_it.extract_plain_text(self.data["content"])
        else:
            return ""

    @overrides(BaseMessageSegment)
    def __add__(self, other) -> "Message":
        # TODO：判断类型
        return Message(self) + (MessageSegment.text(other) if isinstance(
            other, str) else other)

    @overrides(BaseMessageSegment)
    def __radd__(self, other) -> "Message":
        # TODO：判断类型
        return (MessageSegment.text(other)
                if isinstance(other, str) else Message(other)) + self

    @overrides(BaseMessageSegment)
    def is_text(self) -> bool:
        return self.plain_text == self.data["content"]

    @staticmethod
    @deprecated("用 KMarkdown 语法 (met)用户id/here/all(met) 代替")
    def at(user_id: str) -> "MessageSegment":
        return MessageSegment("at", {"user_id": user_id})

    @staticmethod
    def text(text: str) -> "MessageSegment":
        return MessageSegment("text", {"content": text})

    @staticmethod
    def image(file_key: str) -> "MessageSegment":
        return MessageSegment("image", {"file_key": file_key})

    @staticmethod
    def video(file_key: str) -> "MessageSegment":
        return MessageSegment("video", {
            "file_key": file_key,
        })

    @staticmethod
    def file(file_key: str) -> "MessageSegment":
        return MessageSegment("file", {
            "file_key": file_key
        })

    @staticmethod
    def audio(file_key: str, duration: int) -> "MessageSegment":
        return MessageSegment("audio", {
            "file_key": file_key,
            "duration": duration
        })

    @staticmethod
    def KMarkdown(content: str) -> "MessageSegment":
        return MessageSegment("KMarkdown", {
            "content": content
        })

    @staticmethod
    def Card(content: str) -> "MessageSegment":
        return MessageSegment("Card", {
            "content": content
        })


class Message(BaseMessage[MessageSegment]):
    """
    开黑啦 v3 协议 Message 适配。
    """

    @classmethod
    @overrides(BaseMessage)
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @overrides(BaseMessage)
    def __add__(self, other: Union[str, Mapping, Iterable[Mapping]]) -> "Message":
        # TODO：判断类型
        return super(Message, self).__add__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @overrides(BaseMessage)
    def __radd__(self, other: Union[str, Mapping, Iterable[Mapping]]) -> "Message":
        # TODO：判断类型
        return super(Message, self).__radd__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @staticmethod
    @overrides(BaseMessage)
    def _construct(
            msg: Union[str, Mapping, Iterable[Mapping]]
    ) -> Iterable[MessageSegment]:
        # TODO：重构
        if isinstance(msg, Mapping):
            msg = cast(Mapping[str, Any], msg)
            yield MessageSegment(msg["type"], msg.get("content") or {})
            return
        elif isinstance(msg, Iterable) and not isinstance(msg, str):
            for seg in msg:
                yield MessageSegment(seg["type"], seg.get("content") or {})
            return
        elif isinstance(msg, str):
            yield MessageSegment("text", {"content": msg})
            return

    @overrides(BaseMessage)
    def extract_plain_text(self) -> str:
        return "".join(seg.plain_text for seg in self)


@dataclass
class MessageSerializer:
    """
    开黑啦 协议 Message 序列化器。
    """
    message: Message

    # bot 发送消息只支持这三种类型
    # todo 要不要支持将message拆分为segment分别发送
    async def serialize(self) -> Tuple[str, str]:
        if self.message[0].type in ("text", "KMarkdown", "Card"):
            return msg_type_map[self.message[0].type], self.message[0].data['content']
        elif self.message[0].type in ("image", "audio", "video", "file"):
            return self.message[0].data['file_key']
        else:
            raise UnsupportedMessageType


@dataclass
class MessageDeserializer:
    """
    开黑啦 协议 Message 反序列化器。
    """
    type: str
    data: Dict

    def deserialize(self) -> Message:
        if self.type == 1:
            return Message(MessageSegment.text(self.data["content"]))
        elif self.type == 2:
            return Message(MessageSegment.image(self.data["content"]))
        elif self.type == 3:
            return Message(MessageSegment.video(self.data["attachments"]["url"]))
        elif self.type == 4:
            return Message(MessageSegment.file(self.data["attachments"]["url"]))
        elif self.type == 9:
            return Message(MessageSegment.KMarkdown(self.data["content"]))
        elif self.type == 10:
            return Message(MessageSegment.Card(self.data["content"]))
        else:
            return Message(MessageSegment(self.type, self.data))
