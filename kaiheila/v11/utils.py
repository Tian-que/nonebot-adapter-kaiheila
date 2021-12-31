import sys
import asyncio
from typing import Any, Dict, Tuple, Optional

from nonebot.utils import logger_wrapper

from .exception import ActionFailed, NetworkError

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

# todo 搞懂这玩意
# 这里应该维护一个队列，每次放入消息后取出最小sn值的event

    # //收到消息
    # public function processEvent($frame)
    # {
    #     //仅在连接状态接收事件消息
    #     if ($this->status != self::STATUS_CONNECTED) {
    #         return;
    #     }
    #     $sn = $frame->sn;
    #     //先将消息放入接收队列
    #     $this->recvQueue[$sn] = $frame;
    #     //再按顺序从接收队列中读取
    #     while (true) {
    #         if (isset($this->recvQueue[$this->maxSn + 1])) {
    #             $this->maxSn++;
    #             $outFrame = $this->recvQueue[$this->maxSn];
    #             unset($this->recvQueue[$this->maxSn]);
    #             $this->processDataFrame($outFrame);
    #         } else {
    #             break;
    #         }
    #     }
    # }
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

    @classmethod
    def get_seq(cls) -> int:
        s = cls._seq
        cls._seq = (cls._seq + 1) % sys.maxsize
        return s

    @classmethod
    def add_result(cls, self_id: str, result: Dict[str, Any]):
        if isinstance(result["sn"], int):
            future = cls._futures.get((self_id, result["sn"]))
            if future:
                future.set_result(result)

    @classmethod
    async def fetch(
        cls, self_id: str, seq: int, timeout: Optional[float]
    ) -> Dict[str, Any]:
        future = asyncio.get_event_loop().create_future()
        cls._futures[(self_id, seq)] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise NetworkError("WebSocket API call timeout") from None
        finally:
            del cls._futures[(self_id, seq)]
