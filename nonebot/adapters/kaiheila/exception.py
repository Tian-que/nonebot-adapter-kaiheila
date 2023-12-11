import json
from typing import Optional

from nonebot.drivers import Response
from nonebot.exception import AdapterException
from nonebot.exception import ActionFailed as BaseActionFailed
from nonebot.exception import NetworkError as BaseNetworkError
from nonebot.exception import NoLogException as BaseNoLogException
from nonebot.exception import ApiNotAvailable as BaseApiNotAvailable


class KaiheilaAdapterException(AdapterException):
    def __init__(self, *args: object):
        super().__init__("Kaiheila", *args)


class NoLogException(BaseNoLogException, KaiheilaAdapterException):
    pass


class ActionFailed(BaseActionFailed, KaiheilaAdapterException):
    """
    :说明:

        API 请求返回错误信息。

    :参数:

        * ``response: Response``: 响应体
    """

    def __init__(self, response: Response):
        self.status_code: int = response.status_code
        self.code: Optional[int] = None
        self.message: Optional[str] = None
        self.data: Optional[dict] = None
        if response.content:
            body = json.loads(response.content)
            self._prepare_body(body)

    def __repr__(self):
        return (
            f"<ActionFailed: {self.status_code}, code={self.code}, "
            f"message={self.message}, data={self.data}>"
        )

    def __str__(self):
        return self.__repr__()

    def _prepare_body(self, body: dict):
        self.code = body.get("code", None)
        self.message = body.get("message", None)
        self.data = body.get("data", None)


class UnauthorizedException(ActionFailed):
    pass


class RateLimitException(ActionFailed):
    pass


class NetworkError(BaseNetworkError, KaiheilaAdapterException):
    """
    :说明:

      网络错误。

    :参数:

      * ``msg: Optional[int]``: 错误信息
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

      在发送不支持的消息类型时抛出。
    """

    def __init__(self, message: str = ""):
        super().__init__()
        self.message = message

    def __repr__(self) -> str:
        return self.message


class UnsupportedMessageOperation(KaiheilaAdapterException):
    """
    :说明:

      在调用不支持的 Message 或 MessageSegment 操作时抛出。
    """

    def __init__(self, message: str = ""):
        super().__init__()
        self.message = message

    def __repr__(self) -> str:
        return self.message


class ReconnectError(KaiheilaAdapterException):
    """
    :说明:

      服务端通知客户端, 代表该连接已失效, 请重新连接。客户端收到后应该主动断开当前连接。
    """

    pass


class TokenError(KaiheilaAdapterException):
    """
    :说明:

      服务端通知客户端, 代表该连接已失效, 请重新连接。客户端收到后应该主动断开当前连接。
    """

    def __init__(self, msg: Optional[str] = None):
        super().__init__()
        self.msg = msg

    def __repr__(self):
        return f"<TokenError message={self.msg}>"

    def __str__(self):
        return self.__repr__()
