import re
import json
from io import BytesIO
from pathlib import Path
from base64 import b64encode
from typing import Any, Type, Tuple, Union, Mapping, Iterable, Optional, Dict, List, cast
from pydantic import Field


import itertools
from dataclasses import dataclass
from nonebot.typing import overrides
from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment

from .utils import log, _b2s, escape, unescape

msg_type_map = {
    "text": 1,
    "image": 2,
    "video": 3,
    "file": 4,
    "audio": 8,
    "Kmarkdown": 9,
    "Card": 10,
}

class MessageSegment(BaseMessageSegment["Message"]):
    """
    开黑啦 协议 MessageSegment 适配。具体方法参考协议消息段类型或源码。

    https://developer.kaiheila.cn/doc/event/message
    """

    @classmethod
    @overrides(BaseMessageSegment)
    def get_message_class(cls) -> Type["Message"]:
        return Message

    @property
    def segment_text(self) -> dict:
        return {
            "text": "[文字]",
            "image": "[图片]",
            "video": "[视频]",
            "file": "[文件]",
            "audio": "[音频]",
            "kmarkdown": "[Kmarkdown消息]",
            "card": "[卡片消息]",
        }

    # 根据协议消息段类型显示消息段内容
    def __str__(self) -> str:
        if self.type in ["text", "kmarkdown", "card"]:
            return str(self.data["content"])
        elif self.type == "at":
            return str(f"@{self.data['user_name']}")
        else:
            return self.segment_text.get(self.type, "")

    @overrides(BaseMessageSegment)
    def __add__(self, other) -> "Message":
        return Message(self) + (MessageSegment.text(other) if isinstance(
            other, str) else other)

    @overrides(BaseMessageSegment)
    def __radd__(self, other) -> "Message":
        return (MessageSegment.text(other)
                if isinstance(other, str) else Message(other)) + self

    @overrides(BaseMessageSegment)
    def is_text(self) -> bool:
        return self.type == "text"

    @staticmethod
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
    def KMarkdown(content: str) -> "MessageSegment":
        return MessageSegment("KMarkdown", {
            "content": content
        })

    @staticmethod
    def Card(content: str) -> "MessageSegment":
        return MessageSegment("Card", {
            "content": content
        })

    @staticmethod
    def audio(file_key: str, duration: int) -> "MessageSegment":
        return MessageSegment("audio", {
            "file_key": file_key,
            "duration": duration
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
        return super(Message, self).__add__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @overrides(BaseMessage)
    def __radd__(self, other: Union[str, Mapping, Iterable[Mapping]]) -> "Message":
        return super(Message, self).__radd__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @staticmethod
    @overrides(BaseMessage)
    def _construct(
        msg: Union[str, Mapping, Iterable[Mapping]]
    ) -> Iterable[MessageSegment]:
        if isinstance(msg, Mapping):
            msg = cast(Mapping[str, Any], msg)
            yield MessageSegment(msg["type"], msg.get("data") or {})
            return
        elif isinstance(msg, Iterable) and not isinstance(msg, str):
            for seg in msg:
                yield MessageSegment(seg["type"], seg.get("data") or {})
            return
        elif isinstance(msg, str):

            def _iter_message(msg: str) -> Iterable[Tuple[str, str]]:
                text_begin = 0
                for cqcode in re.finditer(
                    r"\[CQ:(?P<type>[a-zA-Z0-9-_.]+)"
                    r"(?P<params>"
                    r"(?:,[a-zA-Z0-9-_.]+=[^,\]]+)*"
                    r"),?\]",
                    msg,
                ):
                # re.findall(r"\@(?P<username>.+)\#(?P<user_id>[0-9]+)", a)
                    yield "text", msg[text_begin : cqcode.pos + cqcode.start()]
                    text_begin = cqcode.pos + cqcode.end()
                    yield cqcode.group("type"), cqcode.group("params").lstrip(",")
                yield "text", msg[text_begin:]

            for type_, data in _iter_message(msg):
                if type_ == "text":
                    if data:
                        # only yield non-empty text segment
                        yield MessageSegment(type_, {"content": unescape(data)})
                else:
                    data = {
                        k: unescape(v)
                        for k, v in map(
                            lambda x: x.split("=", maxsplit=1),
                            filter(lambda x: x, (x.lstrip() for x in data.split(","))),
                        )
                    }
                    yield MessageSegment(type_, data)

    @overrides(BaseMessage)
    def extract_plain_text(self) -> str:
        return "".join(seg.data["content"] for seg in self if seg.is_text())


@dataclass
class MessageSerializer:
    """
    开黑啦 协议 Message 序列化器。
    """
    message: Message

    # bot 发送消息只支持这三种类型
    # todo 对其他类型抛出异常
    async def serialize(self) -> Tuple[str, str]:
        if self.message[0].type in ("text", "KMarkdown", "Card"):
            return msg_type_map[self.message[0].type], self.message[0].data['content']
        elif self.message[0].type in  ("image", "audio", "video", "file"):
            return self.message[0].data['file_key']


@dataclass
class MessageDeserializer:
    """
    开黑啦 协议 Message 反序列化器。
    """
    type: str
    datas: Dict

    def deserialize(self) -> Message:
        # dict_mention = {}
        # if self.mentions:
        #     for mention in self.mentions:
        #         dict_mention[mention["key"]] = mention

        if self.type == 1:
            return Message(MessageSegment.text(self.datas["content"]))
        elif self.type == 2:
            return Message(MessageSegment.image(self.datas["content"]))
        elif self.type == 3:
            return Message(MessageSegment.video(self.datas["attachments"]["url"]))
        elif self.type == 4:
            return Message(MessageSegment.file(self.datas["attachments"]["url"]))
        elif self.type == 9:
            return Message(MessageSegment.KMarkdown(self.datas["content"]))
        elif self.type == 10:
            return Message(MessageSegment.Card(self.datas["content"]))
        else:
            return Message(MessageSegment(self.type, self.data))