from .model import (
    URL,
    Role,
    User,
    Guild,
    Channel,
    UserChat,
    GuildEmoji,
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

class ApiClient:
    async def asset_create(self, *, file) -> URL: ...
    async def blacklist_create(
        self,
        *,
        guild_id: str,
        target_id: str,
        remark: str | None = ...,
        del_msg_days: str | None = ...,
    ) -> None: ...
    async def blacklist_delete(self, *, guild_id: str, target_id: str) -> None: ...
    async def blacklist_list(self, *, guild_id: str) -> BlackListsReturn: ...
    async def channelUser_getJoinedChannel(
        self,
        *,
        guild_id: str,
        user_id: str,
        page: int | None = ...,
        page_size: int | None = ...,
    ) -> GetUserJoinedChannelReturn: ...
    async def channelRole_create(
        self, *, channel_id: str, type: str | None = ..., value: str | None = ...
    ) -> ChannelRoleReturn: ...
    async def channelRole_delete(
        self,
        *,
        channel_id: str,
        type: str | None = ...,
        value: str | None = ...,
    ) -> None: ...
    async def channelRole_index(self, *, channel_id: str) -> ChannelRoleInfo: ...
    async def channelRole_update(
        self,
        *,
        channel_id: str,
        type: str | None = ...,
        value: str | None = ...,
        allow: int | None = ...,
        deny: int | None = ...,
    ) -> ChannelRoleReturn: ...
    async def channelRole_sync(
        self,
        *,
        channel_id: str,
    ) -> ChannelRoleSyncResult: ...
    async def channel_create(
        self,
        *,
        guild_id: str,
        name: str,
        parent_id: str | None = ...,
        type: int | None = ...,
        limit_amount: int | None = ...,
        voice_quality: str | None = ...,
        is_category: int | None = ...,
    ) -> Channel: ...
    async def channel_delete(self, *, channel_id: str) -> None: ...
    async def channel_update(
        self,
        *,
        channel_id: str,
        name: str | None = ...,
        topic: str | None = ...,
        slow_mode: int | None = ...,
    ) -> Channel: ...
    async def channel_list(
        self,
        *,
        guild_id: str,
        type: int | None = ...,
        page: int | None = ...,
        page_size: int | None = ...,
    ) -> ChannelsReturn: ...
    async def channel_moveUser(
        self,
        *,
        target_id: str,
        user_ids: list[int],
    ) -> None: ...
    async def channel_userList(self, *, channel_id: str) -> list[User]: ...
    async def channel_view(self, *, target_id: str) -> Channel: ...
    async def directMessage_addReaction(self, *, msg_id: str, emoji: str) -> None: ...
    async def directMessage_create(
        self,
        *,
        content: str,
        type: int | None = ...,
        target_id: str | None = ...,
        chat_code: str | None = ...,
        quote: str | None = ...,
        nonce: str | None = ...,
    ) -> MessageCreateReturn: ...
    async def directMessage_delete(self, *, msg_id: str) -> None: ...
    async def directMessage_deleteReaction(
        self, *, msg_id: str, emoji: str, user_id: str | None = ...
    ) -> None: ...
    async def directMessage_list(
        self,
        *,
        chat_code: str | None = ...,
        target_id: str | None = ...,
        msg_id: str | None = ...,
        flag: str | None = ...,
        page: int | None = ...,
        page_size: int | None = ...,
    ) -> DirectMessagesReturn: ...
    async def directMessage_reactionList(
        self, *, msg_id: str, emoji: str
    ) -> list[ReactionUser]: ...
    async def directMessage_update(
        self, *, content: str, msg_id: str | None = ..., quote: str | None = ...
    ) -> None: ...
    async def directMessage_view(
        self, *, chat_code: str, msg_id: str
    ) -> DirectMessage: ...
    async def gateway_index(self, *, compress: int | None = ...) -> URL: ...
    async def guildBoost_history(
        self, *, guild_id: str, start_time: int | None = ..., end_time: int | None = ...
    ) -> GuildBoostReturn: ...
    async def guildEmoji_create(
        self, *, guild_id: str, emoji: bytes | None = ..., name: str | None = ...
    ) -> GuildEmoji: ...
    async def guildEmoji_delete(self, *, id: str) -> None: ...
    async def guildEmoji_list(
        self, *, guild_id: str, page: int | None = ..., page_size: int | None = ...
    ) -> GuildEmojisReturn: ...
    async def guildEmoji_update(self, *, id: str, name: str) -> None: ...
    async def guildMute_create(
        self, *, guild_id: str = ..., target_id: str = ..., type: int = ...
    ) -> None: ...
    async def guildMute_delete(
        self, *, guild_id: str = ..., target_id: str = ..., type: int = ...
    ) -> None: ...
    async def guildMute_list(
        self, *, guild_id: str, return_type: str | None = ...
    ) -> None: ...
    async def guildRole_create(
        self, *, guild_id: str, name: str | None = ...
    ) -> Role: ...
    async def guildRole_delete(self, *, guild_id: str, role_id: int) -> None: ...
    async def guildRole_grant(
        self, *, guild_id: str, user_id: str, role_id: int
    ) -> GuildRoleReturn: ...
    async def guildRole_list(
        self, *, guild_id: str, page: int | None = ..., page_size: int | None = ...
    ) -> RolesReturn: ...
    async def guildRole_revoke(
        self, *, guild_id: str, user_id: str, role_id: int
    ) -> GuildRoleReturn: ...
    async def guildRole_update(
        self,
        *,
        guild_id: str,
        role_id: int,
        name: str | None = ...,
        color: int | None = ...,
        hoist: int | None = ...,
        mentionable: int | None = ...,
        permissions: int | None = ...,
    ) -> Role: ...
    async def guild_kickout(self, *, guild_id: str, target_id: str) -> None: ...
    async def guild_leave(self, *, guild_id: str) -> None: ...
    async def guild_list(
        self,
        *,
        page: int | None = ...,
        page_size: int | None = ...,
        sort: str | None = ...,
    ) -> GuildsReturn: ...
    async def guild_nickname(
        self,
        *,
        guild_id: str = ...,
        nickname: str | None = ...,
        user_id: str | None = ...,
    ) -> None: ...
    async def guild_userList(
        self,
        *,
        guild_id: str,
        channel_id: str | None = ...,
        search: str | None = ...,
        role_id: int | None = ...,
        mobile_verified: int | None = ...,
        active_time: int | None = ...,
        joined_at: int | None = ...,
        page: int | None = ...,
        page_size: int | None = ...,
        filter_user_id: str | None = ...,
    ) -> GuildUsersReturn: ...
    async def guild_view(self, *, guild_id: str) -> Guild: ...
    async def intimacy_index(self, *, user_id: str) -> IntimacyIndexReturn: ...
    async def intimacy_update(
        self,
        *,
        user_id: str,
        score: int | None = ...,
        social_info: str | None = ...,
        img_id: str | None = ...,
    ) -> None: ...
    async def invite_create(
        self,
        *,
        guild_id: str | None = ...,
        channel_id: str | None = ...,
        duration: int | None = ...,
        setting_times: int | None = ...,
    ) -> URL: ...
    async def invite_delete(
        self, *, url_code: str, guild_id: str | None = ..., channel_id: str | None = ...
    ) -> None: ...
    async def invite_list(
        self,
        *,
        guild_id: str | None = ...,
        channel_id: str | None = ...,
        page: int | None = ...,
        page_size: int | None = ...,
    ) -> InvitesReturn: ...
    async def message_addReaction(self, *, msg_id: str, emoji: str) -> None: ...
    async def message_create(
        self,
        *,
        content: str,
        target_id: str,
        type: int | None = ...,
        quote: str | None = ...,
        nonce: str | None = ...,
        temp_target_id: str | None = ...,
    ) -> MessageCreateReturn: ...
    async def message_delete(self, *, msg_id: str) -> None: ...
    async def message_deleteReaction(
        self, *, msg_id: str, emoji: str, user_id: str | None = ...
    ) -> None: ...
    async def message_list(
        self,
        *,
        target_id: str,
        msg_id: str | None = ...,
        pin: int | None = ...,
        flag: str | None = ...,
        page_size: int | None = ...,
    ) -> ChannelMessagesReturn: ...
    async def message_reactionList(
        self, *, msg_id: str, emoji: str
    ) -> list[ReactionUser]: ...
    async def message_update(
        self,
        *,
        msg_id: str,
        content: str,
        quote: str | None = ...,
        temp_target_id: str | None = ...,
    ) -> None: ...
    async def message_view(self, *, msg_id: str) -> ChannelMessage: ...
    async def userChat_create(self, *, target_id: str) -> UserChat: ...
    async def userChat_delete(self, *, chat_code: str) -> None: ...
    async def userChat_list(
        self, *, page: int | None = ..., page_size: int | None = ...
    ) -> UserChatsReturn: ...
    async def userChat_view(self, *, chat_code: str) -> UserChat: ...
    async def user_me(self) -> User: ...
    async def user_offline(self) -> None: ...
    async def user_view(self, *, user_id: str, guild_id: str | None = ...) -> User: ...
