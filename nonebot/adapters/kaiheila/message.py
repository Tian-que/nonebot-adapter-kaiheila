from dataclasses import dataclass
from typing import Any, Type, Tuple, Union, Mapping, Iterable, Dict, cast, Optional

from deprecated import deprecated
from nonebot.typing import overrides

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment
from .exception import UnsupportedMessageType, UnsupportedMessageOperation
from .utils import unescape_kmarkdown

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

    @property
    def plain_text(self):
        if self.type == "text":
            return self.data["content"]
        elif self.type == "kmarkdown":
            return self.data["raw_content"]
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

    def _conduct_single(self, other: "MessageSegment") -> "MessageSegment":
        if self.type == "text":
            return MessageSegment("text", {"content": self.data["content"] + other.data["content"]})
        elif self.type == "kmarkdown":
            return MessageSegment("kmarkdown", {"content": self.data["content"] + other.data["content"],
                                                "raw_content": self.data["raw_content"] + other.data["raw_content"]})
        else:
            raise UnsupportedMessageOperation()

    def conduct(self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]) -> "MessageSegment":
        """
        连接两个或多个 MessageSegment，必须同时为 text 或 KMarkdown
        """
        if self.type != "text" and self.type != "kmarkdown":
            raise UnsupportedMessageOperation()

        if isinstance(other, str):
            other = [MessageSegment.text(other)]
        elif isinstance(other, MessageSegment):
            other = [other]

        seg = self
        for o in other:
            if o.type == seg.type:
                seg = self._conduct_single(o)
            else:
                raise UnsupportedMessageOperation()
        return seg

    @overrides(BaseMessageSegment)
    def is_text(self) -> bool:
        if self.type == "kmarkdown":
            return self.data["raw_content"] == self.data["content"]
        else:
            return self.type == "text"

    @staticmethod
    @deprecated("用 KMarkdown 语法 (met)用户id/here/all(met) 代替")
    def at(user_id: str) -> "MessageSegment":
        return MessageSegment.KMarkdown(f"(met){user_id}(met)", user_id)

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
    def KMarkdown(content: str, raw_content: Optional[str] = None) -> "MessageSegment":
        """
        构造KMarkdown消息段

        @param content: KMarkdown消息内容（语法参考：https://developer.kookapp.cn/doc/kmarkdown）
        @param raw_content: （可选）消息段的纯文本内容
        """
        if raw_content is None:
            raw_content = ""

        return MessageSegment("kmarkdown", {
            "content": content,
            "raw_content": raw_content
        })

    @staticmethod
    def Card(content: str) -> "MessageSegment":
        """
        构造卡片消息

        @param content: KMarkdown消息内容（语法参考：https://developer.kookapp.cn/doc/cardmessage）
        """
        return MessageSegment("card", {
            "content": content
        })

    @staticmethod
    def quote(msg_id: str) -> "MessageSegment":
        return MessageSegment("quote", {
            "msg_id": msg_id
        })


class Message(BaseMessage[MessageSegment]):
    """
    开黑啦 v3 协议 Message 适配。
    """

    @classmethod
    @overrides(BaseMessage)
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @staticmethod
    @overrides(BaseMessage)
    def _construct(
            msg: Union[str, Mapping, Iterable[Mapping]]
    ) -> Iterable[MessageSegment]:
        if isinstance(msg, Mapping):
            msg = cast(Mapping[str, Any], msg)
            yield MessageSegment(msg["type"], msg.get("content") or {})
        elif isinstance(msg, Iterable) and not isinstance(msg, str):
            for seg in msg:
                yield MessageSegment(seg["type"], seg.get("content") or {})
        elif isinstance(msg, str):
            yield MessageSegment("text", {"content": msg})

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

    def serialize(self, for_send: bool = True) -> Tuple[int, str]:
        if len(self.message) != 1:
            self.message = self.message.copy()
            self.message.reduce()

            if len(self.message) != 1:
                raise UnsupportedMessageOperation()

        msg_type = self.message[0].type
        msg_type_code = msg_type_map[msg_type]
        # bot 发送消息只支持"text", "kmarkdown", "card"
        # 经测试还支持"image", "video", "file"
        if msg_type in ("text", "kmarkdown", "card"):
            return msg_type_code, self.message[0].data['content']
        elif msg_type in ("image", "video", "file"):
            return msg_type_code, self.message[0].data['file_key']
        elif msg_type == "audio" and not for_send:
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
            content = self.data["content"]
            raw_content = self.data["kmarkdown"]["raw_content"]

            # raw_content默认strip掉首尾空格，但是开黑啦本体的聊天界面中不会strip，所以这里还原了
            unescaped = unescape_kmarkdown(content)
            is_plain_text = unescaped.strip() == raw_content
            if is_plain_text:
                raw_content = unescaped

            # 如果是KMarkdown消息是纯文本，直接构造纯文本消息
            # 目的是让on_command等依赖__str__的规则能够在消息存在转义字符时正常工作
            if is_plain_text:
                return Message(MessageSegment.text(raw_content))
            else:
                return Message(MessageSegment.KMarkdown(content, raw_content))
        elif self.type == "card":
            return Message(MessageSegment.Card(self.data["content"]))
        else:
            return Message(MessageSegment(self.type, self.data))
