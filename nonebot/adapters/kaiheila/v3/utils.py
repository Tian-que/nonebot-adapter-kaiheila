import asyncio
from typing import Any, Dict, Tuple, Optional

from nonebot.utils import logger_wrapper

from .exception import ActionFailed

log = logger_wrapper("Kaiheila")

def _b2s(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()

def code_to_emoji(emoji: str) -> str:
    emoji = emoji.encode("unicode_escape")

def _handle_api_result(result: Optional[Dict[str, Any]]) -> Any:
    """
    :说明:

      处理 API 请求返回值。

    :参数:

      * ``result: Optional[Dict[str, Any]]``: API 返回数据

    :返回:

        - ``Any``: API 调用返回数据

    :异常:

        - ``ActionFailed``: API 调用失败
    """
    if isinstance(result, dict):
        if result.get("code") != 0:
            raise ActionFailed(**result)
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
