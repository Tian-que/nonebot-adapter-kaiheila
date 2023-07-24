from .model import *

api_method_map = {
    'asset/create': {'method': 'POST', 'type': URL},
    'blacklist/create': {'method': 'POST', 'type': None},
    'blacklist/delete': {'method': 'POST', 'type': None},
    'blacklist/list': {'method': 'GET', 'type': BlackListsReturn},
    'channel-user/get-joined-channel': {'method': 'GET', 'type': GetUserJoinedChannelReturn},
    'channel-role/create': {'method': 'POST', 'type': ChannelRoleReturn},
    'channel-role/delete': {'method': 'POST', 'type': None},
    'channel-role/index': {'method': 'GET', 'type': ChannelRoleInfo},
    'channel-role/update': {'method': 'POST', 'type': ChannelRoleReturn},
    'channel-role/sync': {'method': 'POST', 'type': ChannelRoleSyncResult},
    'channel/create': {'method': 'POST', 'type': Channel},
    'channel/delete': {'method': 'POST', 'type': None},
    'channel/update': {'method': 'POST', 'type': Channel},
    'channel/list': {'method': 'GET', 'type': ChannelsReturn},
    'channel/move-user': {'method': 'POST', 'type': None},
    'channel/user-list': {'method': 'GET', 'type': List[User]},
    'channel/view': {'method': 'GET', 'type': Channel},
    'direct-message/add-reaction': {'method': 'POST', 'type': None},
    'direct-message/create': {'method': 'POST', 'type': MessageCreateReturn},
    'direct-message/delete': {'method': 'POST', 'type': None},
    'direct-message/delete-reaction': {'method': 'POST', 'type': None},
    'direct-message/list': {'method': 'GET', 'type': DirectMessagesReturn},
    'direct-message/reaction-list': {'method': 'GET', 'type': List[ReactionUser]},
    'direct-message/update': {'method': 'POST', 'type': None},
    'direct-message/view': {'method': 'GET', 'type': DirectMessage},
    'gateway/index': {'method': 'GET', 'type': URL},
    'guild-boost/history': {'method': 'GET', 'type': GuildBoostReturn},
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
