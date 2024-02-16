from typing import Any, List, Optional, NamedTuple

from .model import (
    URL,
    Role,
    User,
    Guild,
    Channel,
    UserChat,
    RolesReturn,
    GuildsReturn,
    ReactionUser,
    DirectMessage,
    InvitesReturn,
    ChannelMessage,
    ChannelsReturn,
    ChannelRoleInfo,
    GuildRoleReturn,
    UserChatsReturn,
    BlackListsReturn,
    GuildBoostReturn,
    GuildUsersReturn,
    ChannelRoleReturn,
    GuildEmojisReturn,
    IntimacyIndexReturn,
    MessageCreateReturn,
    DirectMessagesReturn,
    ChannelMessagesReturn,
    ChannelRoleSyncResult,
    GetUserJoinedChannelReturn,
)


class ApiMethod(NamedTuple):
    method: str
    restype: Optional[type] = None


api_method_map = {
    "asset/create": ApiMethod("POST", URL),
    "blacklist/create": ApiMethod("POST", None),
    "blacklist/delete": ApiMethod("POST", None),
    "blacklist/list": ApiMethod("GET", BlackListsReturn),
    "channel-user/get-joined-channel": ApiMethod("GET", GetUserJoinedChannelReturn),
    "channel-role/create": ApiMethod("POST", ChannelRoleReturn),
    "channel-role/delete": ApiMethod("POST", None),
    "channel-role/index": ApiMethod("GET", ChannelRoleInfo),
    "channel-role/update": ApiMethod("POST", ChannelRoleReturn),
    "channel-role/sync": ApiMethod("POST", ChannelRoleSyncResult),
    "channel/create": ApiMethod("POST", Channel),
    "channel/delete": ApiMethod("POST", None),
    "channel/update": ApiMethod("POST", Channel),
    "channel/list": ApiMethod("GET", ChannelsReturn),
    "channel/move-user": ApiMethod("POST", None),
    "channel/user-list": ApiMethod("GET", List[User]),
    "channel/view": ApiMethod("GET", Channel),
    "direct-message/add-reaction": ApiMethod("POST", None),
    "direct-message/create": ApiMethod("POST", MessageCreateReturn),
    "direct-message/delete": ApiMethod("POST", None),
    "direct-message/delete-reaction": ApiMethod("POST", None),
    "direct-message/list": ApiMethod("GET", DirectMessagesReturn),
    "direct-message/reaction-list": ApiMethod("GET", List[ReactionUser]),
    "direct-message/update": ApiMethod("POST", None),
    "direct-message/view": ApiMethod("GET", DirectMessage),
    "gateway/index": ApiMethod("GET", URL),
    "guild-boost/history": ApiMethod("GET", GuildBoostReturn),
    "guild-emoji/create": ApiMethod("POST", None),
    "guild-emoji/delete": ApiMethod("POST", None),
    "guild-emoji/list": ApiMethod("GET", GuildEmojisReturn),
    "guild-emoji/update": ApiMethod("POST", None),
    "guild-mute/create": ApiMethod("POST", None),
    "guild-mute/delete": ApiMethod("POST", None),
    "guild-mute/list": ApiMethod("GET", None),
    "guild-role/create": ApiMethod("POST", Role),
    "guild-role/delete": ApiMethod("POST", None),
    "guild-role/grant": ApiMethod("POST", GuildRoleReturn),
    "guild-role/list": ApiMethod("GET", RolesReturn),
    "guild-role/revoke": ApiMethod("POST", GuildRoleReturn),
    "guild-role/update": ApiMethod("POST", Role),
    "guild/kickout": ApiMethod("POST", None),
    "guild/leave": ApiMethod("POST", None),
    "guild/list": ApiMethod("GET", GuildsReturn),
    "guild/nickname": ApiMethod("POST", None),
    "guild/user-list": ApiMethod("GET", GuildUsersReturn),
    "guild/view": ApiMethod("GET", Guild),
    "intimacy/index": ApiMethod("GET", IntimacyIndexReturn),
    "intimacy/update": ApiMethod("POST", None),
    "invite/create": ApiMethod("POST", URL),
    "invite/delete": ApiMethod("POST", None),
    "invite/list": ApiMethod("GET", InvitesReturn),
    "message/add-reaction": ApiMethod("POST", None),
    "message/create": ApiMethod("POST", MessageCreateReturn),
    "message/delete": ApiMethod("POST", None),
    "message/delete-reaction": ApiMethod("POST", None),
    "message/list": ApiMethod("GET", ChannelMessagesReturn),
    "message/reaction-list": ApiMethod("GET", List[ReactionUser]),
    "message/update": ApiMethod("POST", None),
    "message/view": ApiMethod("GET", ChannelMessage),
    "user-chat/create": ApiMethod("POST", UserChat),
    "user-chat/delete": ApiMethod("POST", None),
    "user-chat/list": ApiMethod("GET", UserChatsReturn),
    "user-chat/view": ApiMethod("GET", UserChat),
    "user/me": ApiMethod("GET", User),
    "user/offline": ApiMethod("POST", None),
    "user/view": ApiMethod("GET", User),
}


def get_api_method(api: str) -> str:
    if api not in api_method_map:
        return "POST"
    return api_method_map[api].method


def get_api_restype(api: str) -> Any:
    if api not in api_method_map:
        return None
    return api_method_map[api].restype
