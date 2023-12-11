import json
import asyncio
from io import StringIO
from collections import UserDict
from typing import Any, Dict, Tuple, Optional, Protocol, runtime_checkable

from nonebot.utils import logger_wrapper
from nonebot.internal.driver import Response

from .exception import ActionFailed

log = logger_wrapper("Kaiheila")


def _b2s(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()


def code_to_emoji(emoji: str) -> bytes:
    return emoji.encode("unicode_escape")


ESCAPE_CHAR = "!()*-.:>[\\]`~"


def escape_kmarkdown(content: str):
    """
    将文本中的kmarkdown标识符进行转义
    """
    with StringIO() as f:
        for c in content:
            if c in ESCAPE_CHAR:
                f.write("\\")
            f.write(c)
        return f.getvalue()


def unescape_kmarkdown(content: str):
    """
    去除kmarkdown中的转义字符
    """
    with StringIO() as f:
        i = 0
        while i < len(content):
            if content[i] == "\\":
                if i + 1 < len(content) and content[i + 1] in ESCAPE_CHAR:
                    f.write(content[i + 1])
                    i += 2
                    continue

            f.write(content[i])
            i += 1
        return f.getvalue()


def _handle_api_result(response: Response) -> Any:
    """
    :说明:

      处理 API 请求返回值。

    :参数:

      * ``response: Response``: API 响应体

    :返回:

        - ``T``: API 调用返回数据

    :异常:

        - ``ActionFailed``: API 调用失败
    """
    result = json.loads(response.content)
    if isinstance(result, dict):
        log("DEBUG", "API result " + str(result))
        if result.get("code") != 0:
            raise ActionFailed(response)
        else:
            return result.get("data")


class ResultStore:
    _seq = 1
    _futures: Dict[Tuple[str, int], asyncio.Future] = {}
    _sn_map = {}

    @classmethod
    def set_sn(cls, self_id: str, sn: int) -> None:
        cls._sn_map[self_id] = sn

    @classmethod
    def get_sn(cls, self_id: str) -> int:
        return cls._sn_map.get(self_id, 0)


class AttrDict(UserDict):
    def __init__(self, data=None):
        initial = dict(data)
        for k in initial:
            if isinstance(initial[k], dict):
                initial[k] = AttrDict(initial[k])

        super().__init__(initial)

    def __getattr__(self, name):
        return self[name]


@runtime_checkable
class BytesReadable(Protocol):
    def read(self) -> bytes:
        ...
