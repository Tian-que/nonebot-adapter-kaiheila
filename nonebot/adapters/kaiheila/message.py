from dataclasses import dataclass
from typing import Any, Type, Tuple, Union, Mapping, Iterable, Dict, cast

from deprecated import deprecated
from kmarkdown_it import KMarkdownIt
from lazy import lazy
from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment
from nonebot.typing import overrides

from .exception import UnsupportedMessageType, UnsupportedMessageOperation, InvalidMessage

msg_type_map = {
    "text": 1,
    "image": 2,
    "video": 3,
    "file": 4,
    "audio": 8,
    "kmarkdown": 9,
    "card": 10,
}

rev_msg_type_map = {}
for msg_type, code in msg_type_map.items():
    rev_msg_type_map[code] = msg_type

# 根据协议消息段类型显示消息段内容
segment_text = {
    "text": "[文字]",
    "image": "[图片]",
    "video": "[视频]",
    "file": "[文件]",
    "audio": "[音频]",
    "kmarkdown": "[KMarkdown消息]",
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
        if self.type in ["text", "kmarkdown"]:
            return str(self.data["content"])
        elif self.type == "at":
            return str(f"@{self.data['user_name']}")
        else:
            return segment_text.get(msg_type_map.get(self.type, ""), "[未知类型消息]")

    @lazy
    def plain_text(self):
        if self.type == "text":
            return str(self.data["content"])
        elif self.type == "kmarkdown":
            return kmd_it.extract_plain_text(self.data["content"])
        else:
            return ""

    @overrides(BaseMessageSegment)
    def __add__(self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]) -> "Message":
        return Message(self.conduct(other))

    @overrides(BaseMessageSegment)
    def __radd__(self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]) -> "Message":
        if isinstance(other, str):
            other = MessageSegment(self.type, {"content": other})
        return Message(other.conduct(self))

    def conduct(self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]) -> "MessageSegment":
        """
        连接两个或多个 MessageSegment，必须同时为 text 或 KMarkdown
        """
        if self.type != "text" and self.type != "kmarkdown":
            raise UnsupportedMessageOperation()

        if isinstance(other, str):
            return MessageSegment(self.type, {"content": self.data["content"] + other})
        elif isinstance(other, MessageSegment):
            other = [other]

        seg = self
        for o in other:
            if o.type == seg.type:
                seg = MessageSegment(seg.type, {"content": seg.data["content"] + o.data["content"]})
            else:
                raise UnsupportedMessageOperation()
        return seg

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
        return MessageSegment("kmarkdown", {
            "content": content
        })

    @staticmethod
    def Card(content: str) -> "MessageSegment":
        return MessageSegment("card", {
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
        if isinstance(other, str):
            return self[0] + other
        else:
            return super().__add__(other)

    @overrides(BaseMessage)
    def __radd__(self, other: Union[str, Mapping, Iterable[Mapping]]) -> "Message":
        if isinstance(other, str):
            return other + self[0]
        else:
            return super().__add__(other)

    @overrides(BaseMessage)
    def __iadd__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> "Message":
        if self[0].type == "text" or self[0].type == "kmarkdown":
            self[0] = self[0].conduct(other)
            return self
        raise UnsupportedMessageOperation()

    @staticmethod
    @overrides(BaseMessage)
    def _construct(
            msg: Union[str, Mapping, Iterable[Mapping]]
    ) -> Iterable[MessageSegment]:
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

    def reduce(self) -> None:
        """合并消息内连续的纯文本段和 KMarkdown 段。"""
        index = 1
        while index < len(self):
            prev = self[index - 1]
            cur = self[index]
            if prev.type == "text" and cur.type == "text" \
                    or prev.type == "kmarkdown" and cur.type == "kmarkdown":
                # 重新构造MessageSegment，确保lazy字段更新
                self[index - 1] = MessageSegment(prev.type, {
                    "content": prev.data["content"] + cur.data["content"]
                })
                del self[index]
            else:
                index += 1


@dataclass
class MessageSerializer:
    """
    开黑啦 协议 Message 序列化器。
    """
    message: Message

    def __post_init__(self):
        self.message.reduce()

    async def serialize(self, for_send: bool = True) -> Tuple[int, str]:
        if len(self.message) != 1:
            raise InvalidMessage()

        msg_type = self.message[0].type
        msg_type_code = msg_type_map[msg_type]
        # bot 发送消息只支持这三种类型
        if msg_type in ("text", "kmarkdown", "card"):
            return msg_type_code, self.message[0].data['content']
        elif msg_type in ("image", "audio", "video", "file") and not for_send:
            return msg_type_code, self.message[0].data['file_key']
        else:
            raise UnsupportedMessageType()


@dataclass
class MessageDeserializer:
    """
    开黑啦 协议 Message 反序列化器。
    """
    type_code: int
    data: Dict

    def __post_init__(self):
        self.type = rev_msg_type_map.get(self.type_code, "")

    def deserialize(self) -> Message:
        if self.type == "text":
            return Message(MessageSegment.text(self.data["content"]))
        elif self.type == "image":
            return Message(MessageSegment.image(self.data["content"]))
        elif self.type == "video":
            return Message(MessageSegment.video(self.data["attachments"]["url"]))
        elif self.type == "file":
            return Message(MessageSegment.file(self.data["attachments"]["url"]))
        elif self.type == "kmarkdown":
            return Message(MessageSegment.KMarkdown(self.data["content"]))
        elif self.type == "card":
            return Message(MessageSegment.Card(self.data["content"]))
        else:
            return Message(MessageSegment(self.type, self.data))
