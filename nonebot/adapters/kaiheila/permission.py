from nonebot.permission import Permission

from .event import ChannelMessageEvent, PrivateMessageEvent

# todo 增加更多权限


async def _private(event: PrivateMessageEvent) -> bool:
    return True


PRIVATE = Permission(_private)
"""
- **说明**: 匹配任意私聊消息类型事件
"""


async def _group(event: ChannelMessageEvent) -> bool:
    return True


GROUP = Permission(_group)
"""
- **说明**: 匹配任意群聊消息类型事件
"""

__all__ = ["PRIVATE", "GROUP"]
