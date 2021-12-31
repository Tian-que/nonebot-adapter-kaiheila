from typing import Optional

from nonebot.exception import AdapterException
from nonebot.exception import ActionFailed as BaseActionFailed
from nonebot.exception import NetworkError as BaseNetworkError
from nonebot.exception import NoLogException as BaseNoLogException
from nonebot.exception import ApiNotAvailable as BaseApiNotAvailable


class KaiheilaAdapterException(AdapterException):
    def __init__(self):
        super().__init__("Kaiheila")


class NoLogException(BaseNoLogException, KaiheilaAdapterException):
    pass


class ActionFailed(BaseActionFailed, KaiheilaAdapterException):
    """
    :说明:

      API 请求返回错误信息。

    :参数:

      * ``retcode: Optional[int]``: 错误码
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.info = kwargs

    def __repr__(self):
        return (
            f"<ActionFailed "
            + ", ".join(f"{k}={v}" for k, v in self.info.items())
            + ">"
        )

    def __str__(self):
        return self.__repr__()


class NetworkError(BaseNetworkError, KaiheilaAdapterException):
    """
    :说明:

      网络错误。

    :参数:

      * ``retcode: Optional[int]``: 错误码
    """

    def __init__(self, msg: Optional[str] = None):
        super().__init__()
        self.msg = msg

    def __repr__(self):
        return f"<NetWorkError message={self.msg}>"

    def __str__(self):
        return self.__repr__()


class ApiNotAvailable(BaseApiNotAvailable, KaiheilaAdapterException):
    pass

class UnsupportedMessageType(KaiheilaAdapterException):
    """
    :说明:

      在发送不支持的消息类型时抛出，开黑啦 Bot 仅支持发送以下三种消息类型: "text"、"KMarkdown" 和 "Card", 尝试发送其他类型时抛出此异常。
    """
    pass

class ReconnectError(KaiheilaAdapterException):
    """
    :说明:

      服务端通知客户端, 代表该连接已失效, 请重新连接。客户端收到后应该主动断开当前连接。
    """
    pass
