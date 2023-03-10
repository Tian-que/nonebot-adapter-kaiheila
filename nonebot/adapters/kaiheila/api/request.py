import json
from typing import TYPE_CHECKING, Any, Dict

from nonebot.drivers import Request

from ..exception import (
    ActionFailed,
    NetworkError,
    ApiNotAvailable,
    RateLimitException,
    UnauthorizedException,
    KaiheilaAdapterException
)

from .model import *

if TYPE_CHECKING:
    from ..bot import Bot
    from ..adapter import Adapter


async def _request(adapter: "Adapter", bot: "Bot", request: Request) -> Any:
    try:
        response = await adapter.request(request)
        if 200 <= response.status_code < 300:
            if not response.content:
                raise ValueError("Empty response")
            return json.loads(response.content)
        elif response.status_code == 403:
            raise UnauthorizedException(response)
        elif response.status_code in (404, 405):
            raise ApiNotAvailable
        elif response.status_code == 429:
            raise RateLimitException(response)
        else:
            raise ActionFailed(response)
    except KaiheilaAdapterException:
        raise
    except Exception as e:
        raise NetworkError("API request failed") from e