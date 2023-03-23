from typing import TYPE_CHECKING

from nonebot.drivers import Request
from pydantic import parse_obj_as

from .model import *
from .request import _request
from ..utils import _handle_api_result

if TYPE_CHECKING:
    from nonebot.adapters.kaiheila.bot import Bot
    from nonebot.adapters.kaiheila.adapter import Adapter

api_method_map = {
    'asset/create': {'method': 'POST', 'type': URL},
    'blacklist/create': {'method': 'POST', 'type': None},
    'blacklist/delete': {'method': 'POST', 'type': None},
    'blacklist/list': {'method': 'GET', 'type': BlackListsReturn},
    'channel-role/create': {'method': 'POST', 'type': ChannelRoleReturn},
    'channel-role/delete': {'method': 'POST', 'type': None},
    'channel-role/index': {'method': 'GET', 'type': ChannelRoleInfo},
    'channel-role/update': {'method': 'POST', 'type': ChannelRoleReturn},
    'channel/create': {'method': 'POST', 'type': Channel},
    'channel/delete': {'method': 'POST', 'type': None},
    'channel/update': {'method': 'POST', 'type': Channel},
    'channel/list': {'method': 'GET', 'type': ChannelsReturn},
    'channel/move-user': {'method': 'POST', 'type': None},
    'channel/user-list': {'method': 'POST', 'type': List[User]},
    'channel/view': {'method': 'GET', 'type': Channel},
    'direct-message/add-reaction': {'method': 'POST', 'type': None},
    'direct-message/create': {'method': 'POST', 'type': MessageCreateReturn},
    'direct-message/delete': {'method': 'POST', 'type': None},
    'direct-message/delete-reaction': {'method': 'POST', 'type': None},
    'direct-message/list': {'method': 'GET', 'type': DirectMessagesReturn},
    'direct-message/reaction-list': {'method': 'GET', 'type': List[ReactionUser]},
    'direct-message/update': {'method': 'POST', 'type': None},
    'gateway/index': {'method': 'GET', 'type': URL},
    'guild-emoji/create': {'method': 'POST', 'type': None},
    'guild-emoji/delete': {'method': 'POST', 'type': None},
    'guild-emoji/list': {'method': 'GET', 'type': GuildEmojisReturn},
    'guild-emoji/update': {'method': 'POST', 'type': None},
    'guild-mute/create': {'method': 'POST', 'type': None},
    'guild-mute/delete': {'method': 'POST', 'type': None},
    'guild-mute/list': {'method': 'GET', 'type': None},
    'guild-role/create': {'method': 'POST', 'type': Role},
    'guild-role/delete': {'method': 'POST', 'type': None},
    'guild-role/grant': {'method': 'POST', 'type': GuilRoleReturn},
    'guild-role/list': {'method': 'GET', 'type': RolesReturn},
    'guild-role/revoke': {'method': 'POST', 'type': GuilRoleReturn},
    'guild-role/update': {'method': 'POST', 'type': Role},
    'guild/kickout': {'method': 'POST', 'type': None},
    'guild/leave': {'method': 'POST', 'type': None},
    'guild/list': {'method': 'GET', 'type': GuildsReturn},
    'guild/nickname': {'method': 'POST', 'type': None},
    'guild/user-list': {'method': 'GET', 'type': GuildUsersRetrun},
    'guild/view': {'method': 'GET', 'type': Guild},
    'intimacy/index': {'method': 'GET', 'type': IntimacyIndexReturn},
    'intimacy/update': {'method': 'POST', 'type': None},
    'invite/create': {'method': 'POST', 'type': URL},
    'invite/delete': {'method': 'POST', 'type': None},
    'invite/list': {'method': 'GET', 'type': InvitesReturn},
    'message/add-reaction': {'method': 'POST', 'type': None},
    'message/create': {'method': 'POST', 'type': MessageCreateReturn},
    'message/delete': {'method': 'POST', 'type': None},
    'message/delete-reaction': {'method': 'POST', 'type': None},
    'message/list': {'method': 'GET', 'type': ChannelMessagesReturn},
    'message/reaction-list': {'method': 'GET', 'type': List[ReactionUser]},
    'message/update': {'method': 'POST', 'type': None},
    'message/view': {'method': 'GET', 'type': ChannelMessage},
    'user-chat/create': {'method': 'POST', 'type': UserChat},
    'user-chat/delete': {'method': 'POST', 'type': None},
    'user-chat/list': {'method': 'GET', 'type': UserChatsReturn},
    'user-chat/view': {'method': 'GET', 'type': UserChat},
    'user/me': {'method': 'GET', 'type': User},
    'user/offline': {'method': 'POST', 'type': None},
    'user/view': {'method': 'GET', 'type': User}
}


def get_api_method(api: str) -> str:
    return api_method_map.get(api, {}).get("method", "POST")


def get_api_restype(api: str) -> Any:
    return api_method_map.get(api, {}).get("type")


async def api_handler(adapter: "Adapter", bot: "Bot", api: str, **data) -> Any:
    # 判断 POST 或 GET
    method = get_api_method(api) if not data.get("method") else data.get("method")

    headers = data.get("headers", {})

    files = None
    query = None
    body = None

    if "files" in data:
        files = data["files"]
        del data["files"]
    elif "file" in data:  # 目前只有asset/create接口需要上传文件（大概）
        files = {"file": data["file"]}
        del data["file"]

    if method == "GET":
        query = data
    elif method == "POST":
        body = data

    if bot.token is not None:
        headers["Authorization"] = f"Bot {bot.token}"

    request = Request(
        method,
        adapter.api_root + api,
        headers=headers,
        params=query,
        data=body,
        files=files,
        timeout=adapter.config.api_timeout,
    )
    result_type = get_api_restype(api)
    try:
        result = _handle_api_result(await _request(adapter, bot, request))
        return parse_obj_as(result_type, result) if result_type else None
    except Exception as e:
        raise e
