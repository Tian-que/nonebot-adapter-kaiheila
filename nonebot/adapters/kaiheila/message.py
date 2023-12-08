import json
import warnings
from abc import ABC
from dataclasses import dataclass
from typing import Any, Type, Union, Iterable, Dict, Optional, TypedDict, TYPE_CHECKING, Self, cast

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment
from typing_extensions import override

from .exception import UnsupportedMessageType, UnsupportedMessageOperation
from .utils import unescape_kmarkdown, escape_kmarkdown


class MessageSegment(BaseMessageSegment["Message"], ABC):
    """
    开黑啦 协议 MessageSegment 适配。具体方法参考协议消息段类型或源码。

    https://developer.kaiheila.cn/doc/event/message
    """

    # 已知：
    # command/shell_command使用message_seg = Message[0]; str(message_seg) if message_seg.is_text()
    # startswith/endswith/keyword使用event.get_plaintext()
    # regex使用str(Message)

    @classmethod
    @override
    def get_message_class(cls) -> Type["Message"]:
        return Message

    def __str__(self) -> str:
        return "[未知类型消息]"

    @property
    def plain_text(self):
        return ""

    async def _serialize_for_send(self) -> Dict:
        raise NotImplementedError()

    # @override
    # def __add__(self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]) -> "Message":
    #     return Message(self.conduct(other))
    #
    # @override
    # def __radd__(self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]) -> "Message":
    #     if isinstance(other, str):
    #         other = Text.create(other)
    #     return Message(other.conduct(self))

    def conduct(self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]) -> "MessageSegment":
        """
        连接两个或多个 MessageSegment，必须为纯文本段或 KMarkdown 段
        """
        if isinstance(other, str):
            other = [Text(other)]
        elif isinstance(other, MessageSegment):
            other = [other]
        msg = Message([self, *other])
        msg.reduce()

        if len(msg) != 1:
            raise UnsupportedMessageOperation("必须为纯文本段或 KMarkdown 段")
        else:
            return msg[0]

    @override
    def is_text(self) -> bool:
        return False

    @staticmethod
    def at(user_id: str) -> "MessageSegment":
        warnings.warn(
            "用 KMarkdown 语法 (met)用户id/here/all(met) 代替",
            DeprecationWarning,
        )
        return MessageSegment.KMarkdown(f"(met){user_id}(met)", "@" + user_id)

    @staticmethod
    def text(text: str) -> "MessageSegment":
        """
        构造文本消息段

        @param text: 消息内容
        """
        return Text.create(text)

    @staticmethod
    def KMarkdown(content: str, raw_content: Optional[str] = None) -> "MessageSegment":
        """
        构造KMarkdown消息段

        @param content: KMarkdown消息内容（语法参考：https://developer.kookapp.cn/doc/kmarkdown）
        @param raw_content: （可选）消息段的纯文本内容
        """
        return KMarkdown.create(content, raw_content)

    @staticmethod
    def Card(content: Any) -> "MessageSegment":
        """
        构造卡片消息

        @param content: 卡片消息内容（语法参考：https://developer.kookapp.cn/doc/cardmessage）
        """
        return Card.create(content)

    @staticmethod
    def image(file_key: str) -> "MessageSegment":
        return Image.create(file_key)

    @staticmethod
    def video(file_key: str,
              title: Optional[str] = None) -> "MessageSegment":
        return Video.create(file_key, title)

    @staticmethod
    def audio(file_key: str,
              title: Optional[str] = None,
              cover_file_key: Optional[str] = None) -> "MessageSegment":
        return Audio.create(file_key, title, cover_file_key)

    @staticmethod
    def file(file_key: str,
             title: Optional[str] = None) -> "MessageSegment":
        return File.create(file_key, title)

    @staticmethod
    def quote(msg_id: str) -> "MessageSegment":
        return MessageSegment("quote", {
            "msg_id": msg_id
        })


class ReceivableMessageSegment(MessageSegment):
    @classmethod
    def type_code(cls) -> int:
        """
        对应开黑啦协议里消息的type属性
        """
        return -1

    @classmethod
    def _deserialize(cls, raw_data: Dict) -> Self:
        raise NotImplementedError()


class SendOnlyMessageSegment(MessageSegment):
    ...


@dataclass
class Text(ReceivableMessageSegment):
    if TYPE_CHECKING:
        class _TextData(TypedDict):
            text: str

        data: _TextData

    @classmethod
    @override
    def type_code(cls) -> int:
        return 1

    @override
    def __str__(self) -> str:
        return self.data["text"]

    @property
    @override
    def plain_text(self):
        return self.data["text"]

    @override
    def is_text(self) -> bool:
        return True

    @override
    async def _serialize_for_send(self) -> Dict:
        return {"type": self.type_code(), "content": self.data["text"]}

    @classmethod
    @override
    def _deserialize(cls, raw_data: Dict) -> Self:
        return cls.create(raw_data["content"])

    @classmethod
    def create(cls, text: str):
        return cls("text", {"text": text})


@dataclass
class KMarkdown(ReceivableMessageSegment):
    if TYPE_CHECKING:
        class _KMarkdownData(TypedDict):
            content: str
            raw_content: str

        data: _KMarkdownData

    @classmethod
    @override
    def type_code(cls) -> int:
        return 9

    @override
    def __str__(self) -> str:
        return self.data["content"]

    @property
    def plain_text(self):
        return self.data["raw_content"]

    @override
    def is_text(self) -> bool:
        return True

    @override
    async def _serialize_for_send(self) -> Dict:
        return {"type": self.type_code(), "content": self.data["content"]}

    @classmethod
    @override
    def _deserialize(cls, raw_data: Dict) -> Self:
        content = raw_data["content"]
        raw_content = raw_data["kmarkdown"]["raw_content"]

        # raw_content默认strip掉首尾空格，但是开黑啦本体的聊天界面中不会strip，所以这里还原了
        unescaped = unescape_kmarkdown(content)
        is_plain_text = unescaped.strip() == raw_content
        if is_plain_text:
            raw_content = unescaped

        return cls.create(content, raw_content)

    @classmethod
    def create(cls, content: str, raw_content: Optional[str]):
        if raw_content is None:
            raw_content = ""

        return cls("kmarkdown", {
            "content": content,
            "raw_content": raw_content
        })


@dataclass
class Card(ReceivableMessageSegment):
    if TYPE_CHECKING:
        class _CardData(TypedDict):
            content: str

        data: _CardData

    @classmethod
    @override
    def type_code(cls) -> int:
        return 10

    @override
    def __str__(self) -> str:
        return "[卡片消息]"

    @override
    async def _serialize_for_send(self) -> Dict:
        return {"type": self.type_code(), "content": self.data["content"]}

    @classmethod
    @override
    def _deserialize(cls, raw_data: Dict) -> Self:
        return cls.create(raw_data["content"])

    @classmethod
    def create(cls, content: Any):
        if not isinstance(content, str):
            content = json.dumps(content)

        return cls("card", {
            "content": content
        })


class Media(ReceivableMessageSegment):
    if TYPE_CHECKING:
        class _MediaData(TypedDict):
            file_key: str

        data: _MediaData

    @override
    async def _serialize_for_send(self) -> Dict:
        return {"type": self.type_code(), "content": self.data["file_key"]}


class Image(Media):
    @classmethod
    @override
    def type_code(cls) -> int:
        return 2

    @override
    def __str__(self) -> str:
        return "[图片]"

    @classmethod
    @override
    def _deserialize(cls, raw_data: Dict) -> Self:
        return cls.create(raw_data["attachments"]["url"])

    @classmethod
    def create(cls, file_key: str):
        return cls("image", {
            "file_key": file_key
        })


class Video(Media):
    if TYPE_CHECKING:
        class _VideoData(Media._MediaData):
            title: Optional[str]

        data: _VideoData

    @classmethod
    @override
    def type_code(cls) -> int:
        return 3

    @override
    def __str__(self) -> str:
        return "[视频]"

    @classmethod
    def create(cls, file_key: str, title: Optional[str] = None):
        return cls("video", {
            "file_key": file_key,
            "title": title
        })

    @classmethod
    @override
    def _deserialize(cls, raw_data: Dict) -> Self:
        return cls.create(raw_data["attachments"]["url"], raw_data["attachments"]["name"])


class Audio(Media):
    if TYPE_CHECKING:
        class _AudioData(Media._MediaData):
            title: Optional[str]
            cover_file_key: Optional[str]

        data: _AudioData

    @classmethod
    @override
    def type_code(cls) -> int:
        return 8

    @override
    def __str__(self) -> str:
        return "[音频]"

    async def _serialize_for_send(self) -> Dict:
        # 转化为卡片消息发送
        return await _convert_to_card_message(Message(self))._serialize_for_send()

    @classmethod
    @override
    def _deserialize(cls, raw_data: Dict) -> Self:
        return cls.create(raw_data["attachments"]["url"])

    @classmethod
    def create(cls, file_key: str,
               title: Optional[str] = None,
               cover_file_key: Optional[str] = None):
        return cls("audio", {
            "file_key": file_key,
            "title": title,
            "cover_file_key": cover_file_key
        })


class File(Media):
    if TYPE_CHECKING:
        class _FileData(Media._MediaData):
            title: Optional[str]

        data: _FileData

    @classmethod
    @override
    def type_code(cls) -> int:
        return 4

    @override
    def __str__(self) -> str:
        return "[文件]"

    @classmethod
    @override
    def _deserialize(cls, raw_data: Dict) -> Self:
        return cls.create(raw_data["attachments"]["url"], raw_data["attachments"]["name"])

    @classmethod
    def create(cls, file_key: str,
               title: Optional[str] = None):
        return cls("file", {
            "file_key": file_key,
            "title": title
        })


class Quote(SendOnlyMessageSegment):
    if TYPE_CHECKING:
        class _QuoteData(TypedDict):
            msg_id: str

        data: _QuoteData

    @override
    def __str__(self) -> str:
        return "[引用消息]"

    @classmethod
    def create(cls, msg_id: str):
        return cls("quote", {
            "msg_id": msg_id
        })


class Message(BaseMessage[MessageSegment]):
    """
    开黑啦 v3 协议 Message 适配。
    """

    @classmethod
    @override
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @staticmethod
    @override
    def _construct(msg: str) -> Iterable[MessageSegment]:
        yield Text(msg)

    @override
    def extract_plain_text(self) -> str:
        return "".join(seg.plain_text for seg in self)

    def reduce(self) -> None:
        """合并消息内连续的纯文本段和 KMarkdown 段。"""
        index = 1
        while index < len(self):
            prev = self[index - 1]
            cur = self[index]

            if isinstance(prev, Text) and isinstance(cur, Text):
                self[index - 1] = Text.create(prev.data["text"] + cur.data["text"])
                del self[index]
            elif isinstance(prev, KMarkdown) and isinstance(cur, KMarkdown):
                self[index - 1] = KMarkdown.create(
                    prev.data["content"] + cur.data["content"],
                    prev.data["raw_content"] + cur.data["raw_content"],
                )
                del self[index]
            elif isinstance(prev, KMarkdown) and isinstance(cur, Text):
                self[index - 1] = KMarkdown.create(
                    prev.data["content"] + escape_kmarkdown(cur.data["text"]),
                    prev.data["raw_content"] + cur.data["text"],
                )
                del self[index]
            elif isinstance(prev, Text) and isinstance(cur, KMarkdown):
                self[index - 1] = MessageSegment.KMarkdown(
                    escape_kmarkdown(prev.data["text"]) + cur.data["content"],
                    prev.data["text"] + cur.data["raw_content"],
                )
                del self[index]
            else:
                index += 1


def _convert_to_card_message(msg: Message) -> MessageSegment:
    cards = []
    modules = []

    for seg in msg:
        if isinstance(seg, Card):
            if len(modules) != 0:
                cards.append({"type": "card", "theme": "none", "size": "lg", "modules": modules})
                modules = []
            cards.extend(json.loads(seg.data['content']))
        elif isinstance(seg, Text):
            modules.append(
                {
                    "type": "section",
                    "text": {"type": "plain-text", "content": seg.data["text"]},
                }
            )
        elif isinstance(seg, KMarkdown):
            modules.append(
                {
                    "type": "section",
                    "text": {"type": "kmarkdown", "content": seg.data["content"]},
                }
            )
        elif isinstance(seg, Image):
            modules.append(
                {
                    "type": "container",
                    "elements": [{"type": "image", "src": seg.data["file_key"]}],
                }
            )
        elif isinstance(seg, (Audio, Video, File)):
            mod = {
                "type": seg.type,
                "src": seg.data["file_key"],
            }
            if seg.data.get("title") is not None:
                mod["title"] = seg.data["title"]
            if seg.data.get("cover_file_key") is not None:
                mod["cover"] = seg.data["cover_file_key"]
            modules.append(mod)
        else:
            raise UnsupportedMessageType(seg.type)

    if len(modules) != 0:
        cards.append({"type": "card", "theme": "none", "size": "lg", "modules": modules})

    return Card.create(cards)


@dataclass
class MessageSerializer:
    """
    开黑啦 协议 Message 序列化器。
    """
    message: Message

    async def serialize(self) -> Dict:
        serialized_data = {}

        # quote
        quote = self.message.get("quote")
        if len(quote) > 0:
            self.message = self.message.exclude("quote")
            serialized_data["quote"] = cast(Quote, quote[-1]).data["msg_id"]

        # 大于一段时，先尝试合并text与kmarkdown
        if len(self.message) != 1:
            self.message = self.message.copy()
            self.message.reduce()

        # 文字与媒体混发时，转化为卡片消息发送
        if len(self.message) != 1:
            card_msg = Message(_convert_to_card_message(self.message))
            serialized_data = {
                **serialized_data,
                **(await MessageSerializer(card_msg).serialize())
            }
        else:
            serialized_data = {
                **serialized_data,
                **(await self.message[0]._serialize_for_send())
            }
        return serialized_data


_msg_type_map = {
    Text: Text.type_code(),
    Image: Image.type_code(),
    Video: Video.type_code(),
    File: File.type_code(),
    Audio: Audio.type_code(),
    KMarkdown: KMarkdown.type_code(),
    Card: Card.type_code(),
}

_rev_msg_type_map = {}
for msg_type, code in _msg_type_map.items():
    _rev_msg_type_map[code] = msg_type


@dataclass
class MessageDeserializer:
    """
    开黑啦 协议 Message 反序列化器。
    """
    type_code: int
    data: Dict

    def __post_init__(self):
        self.type = _rev_msg_type_map.get(self.type_code, "")

    def deserialize(self) -> Message:
        if self.type == KMarkdown:
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
        else:
            return Message(self.type._deserialize(self.data))
