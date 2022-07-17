import inspect
from typing_extensions import Literal
from typing import TYPE_CHECKING, List, Type, Optional, Dict, Union

from pydantic import BaseModel, Field, root_validator, HttpUrl
from pygtrie import StringTrie

from nonebot.typing import overrides
from nonebot.utils import escape_tag
from nonebot.adapters import Event as BaseEvent
from enum import IntEnum

from .message import Message, MessageDeserializer
from .exception import NoLogException

if TYPE_CHECKING:
    from .bot import Bot

class EventTypes(IntEnum):
    """
    事件主要格式
    Kaiheila 协议事件，字段与 Kaiheila 一致。各事件字段参考 `Kaiheila 文档`

    .. Kaiheila 文档:
        https://developer.kaiheila.cn/doc/event/event-introduction#事件主要格式
    """

    text = 1
    image = 2
    video = 3
    file = 4
    audio = 8
    kmarkdown = 9
    card = 10
    sys = 255

class SignalTypes(IntEnum):
    """
    信令类型
    Kaiheila 协议信令，字段与 Kaiheila 一致。各事件字段参考 `Kaiheila 文档`

    .. Kaiheila 文档:
        https://developer.kaiheila.cn/doc/websocket#信令格式
    """

    EVENT = 0
    HELLO = 1
    PING = 2
    PONG = 3
    RESUME = 4
    RECONNECT = 5
    RESUME_ACK = 6
    SYS = 255

class Role(BaseModel):
    role_id: Optional[int] = Field(None)
    name: Optional[str] = Field(None)
    color: Optional[int] = Field(None)
    position: Optional[int] = Field(None)
    hoist: Optional[int] = Field(None)
    mentionable: Optional[int] = Field(None)
    permissions: Optional[int] = Field(None)

class Channel(BaseModel):
    id_: Optional[str] = Field(None, alias="id")
    name: Optional[str] = Field(None)
    user_id: Optional[str] = Field(None)
    guild_id: Optional[str] = Field(None)
    topic: Optional[str] = Field(None)
    is_category: Optional[bool] = Field(None)
    parent_id: Optional[str] = Field(None)
    level: Optional[int] = Field(None)
    slow_mode: Optional[int] = Field(None)
    type: Optional[int] = Field(None)
    permission_overwrites: Optional[List[Dict]] = Field(None)
    permission_users: Optional[List[Dict[str, Union["User", int]]]] = Field(None)
    master_id: Optional[str] = Field(None)
    permission_sync: Optional[int] = Field(None)
    limit_amount: Optional[int] = Field(None)

class User(BaseModel):
    """
    开黑啦 User 字段

    https://developer.kaiheila.cn/doc/objects
    """
    id_: Optional[str] = Field(None, alias="id")
    username: Optional[str] = Field(None)
    nickname: Optional[str] = Field(None)
    identify_num: Optional[str] = Field(None)
    online: Optional[bool] = Field(None)
    bot: Optional[bool] = Field(None)
    os: Optional[str] = Field(None)
    status: Optional[int] = Field(None)
    avatar: Optional[str] = Field(None)
    vip_avatar: Optional[str] = Field(None)
    mobile_verified: Optional[bool] = Field(None)
    roles: Optional[List[int]] = Field(None)
    joined_at: Optional[int] = Field(None)
    active_time: Optional[int] = Field(None)

class Guild(BaseModel):
    id_: Optional[str] = Field(None, alias="id")
    name: Optional[str] = Field(None)
    topic: Optional[str] = Field(None)
    master_id: Optional[str] = Field(None)
    icon: Optional[str] = Field(None)
    notify_type: Optional[int] = Field(None)  # 通知类型, 0代表默认使用服务器通知设置，1代表接收所有通知, 2代表仅@被提及，3代表不接收通知
    region: Optional[str] = Field(None)
    enable_open: Optional[bool] = Field(None)
    open_id: Optional[str] = Field(None)
    default_channel_id: Optional[str] = Field(None)
    welcome_channel_id: Optional[str] = Field(None)
    roles: Optional[List[Role]] = Field(None)
    channels: Optional[List[Channel]] = Field(None)

class Emoji(BaseModel):
    id_: str = Field(alias="id")
    name: str

    # 转义 unicdoe 为 emoji表情
    @root_validator(pre=True)
    def parse_emoji(cls, values: dict):
        values['id'] = chr(int(values['id'][2:-2]))
        values['name'] = chr(int(values['name'][2:-2]))
        return values

class Attachment(BaseModel):
    type: str
    name: str
    url: HttpUrl
    file_type: Optional[str] = Field(None)
    size: Optional[int] = Field(None)
    duration: Optional[float] = Field(None)
    width: Optional[int] = Field(None)
    hight: Optional[int] = Field(None)

class Body(BaseModel):
    msg_id: Optional[str]
    user_id: Optional[str]
    author_id: Optional[str]
    group_id: Optional[str]
    channel_id: Optional[str]
    emoji: Optional[Emoji] = None
    content: Optional[str] = None
    updated_at: Optional[str]
    chat_code: Optional[str]

    class Config:
        extra = "allow"

class Extra(BaseModel):
    type_: Union[int, str] = Field(None, alias="type")
    guild_id: Optional[str] = Field(None)
    channel_name: Optional[str] = Field(None)
    mention: Optional[List[str]] = Field(None)
    mention_all: Optional[bool] = Field(None)
    mention_roles: Optional[List[str]] = Field(None)
    mention_here: Optional[bool] = Field(None)
    author: Optional[User] = Field(None)
    body: Optional[Body] = Field(None)
    attachments: Optional[Attachment] = Field(None)
    code: Optional[str] = Field(None)

    # @validator("body")
    # def check_body(cls, v, values):
    #     if values["type_"] != 255 and v:  # 非系统消息 没有body
    #         raise ValueError("非系统消息不应该有body字段")
    #     return v

class OriginEvent(BaseEvent):
    """为了区分信令中非Event事件，增加了前置OriginEvent"""

    __event__ = ""

    @overrides(BaseEvent)
    def get_type(self) -> str:
        return self.post_type

    @overrides(BaseEvent)
    def get_event_name(self) -> str:
        return self.post_type

    @overrides(BaseEvent)
    def get_event_description(self) -> str:
        return escape_tag(str(self.dict()))

    @overrides(BaseEvent)
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_plaintext(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_user_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_session_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def is_tome(self) -> bool:
        return False

class Kmarkdown(BaseModel):
    raw_content: str
    mention_part: list
    mention_role_part: list

class EventMessage(BaseModel):
    type: Union[int, str]
    guild_id: Optional[str]
    channel_name: Optional[str]
    mention: Optional[List]
    mention_all: Optional[bool]
    mention_roles: Optional[List]
    mention_here: Optional[bool]
    nav_channels: Optional[List]
    author: User

    kmarkdown: Optional[Kmarkdown]

    code: Optional[str] = None
    attachments: Optional[Attachment] = None

    content: Message

    @root_validator(pre=True)
    def parse_message(cls, values: dict):
        values["content"] = MessageDeserializer(
            values["type"],
            values,
        ).deserialize()
        return values

class Event(OriginEvent):
    """
    事件主要格式，来自 d 字段
    Kaiheila 协议事件，字段与 Kaiheila 一致。各事件字段参考 `Kaiheila 文档`

    .. Kaiheila 文档:
        https://developer.kaiheila.cn/doc/event/event-introduction
    """
    __event__ = ""
    channel_type: Literal["PERSON", "GROUP"]
    type_: int = Field(alias="type")  # 1:文字消息, 2:图片消息，3:视频消息，4:文件消息， 8:音频消息，9:KMarkdown，10:card消息，255:系统消息, 其它的暂未开放
    target_id: str
    author_id: str = None
    content: str
    msg_id: str
    msg_timestamp: int
    nonce: str
    extra: Extra
    user_id: str

    post_type: str
    self_id: Optional[str] = None # onebot兼容

    @overrides(BaseEvent)
    def get_type(self) -> str:
        return self.post_type

    @overrides(BaseEvent)
    def get_event_name(self) -> str:
        return self.post_type

    @overrides(BaseEvent)
    def get_event_description(self) -> str:
        return escape_tag(str(self.dict()))

    @overrides(BaseEvent)
    def get_plaintext(self) -> str:
        return self.content

    @overrides(BaseEvent)
    def get_user_id(self) -> str:
        return self.user_id

    @overrides(BaseEvent)
    def get_session_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def is_tome(self) -> bool:
        return False

# Message Events
class MessageEvent(Event):
    """消息事件"""

    __event__ = "message"

    post_type: Literal["message"] = "message"
    message_type: str  # group private 其实是person
    sub_type: str
    event: EventMessage

    to_me: bool = False
    """
    :说明: 消息是否与机器人有关

    :类型: ``bool``
    """

    @overrides(Event)
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.message_type}" + (
            f".{sub_type}" if sub_type else ""
        )

    @overrides(Event)
    def get_message(self) -> Message:
        return self.message

    @overrides(Event)
    def get_plaintext(self) -> str:
        return self.message.extract_plain_text()

    @overrides(Event)
    def is_tome(self) -> bool:
        return self.to_me

    @property
    def message(self) -> Message:
        return self.event.content

class PrivateMessageEvent(MessageEvent):
    """私聊消息"""

    __event__ = "message.private"
    message_type: Literal["private"]

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f"user_{self.user_id}"

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Message {self.message_id} from {self.user_id} "'
            + "".join(
                map(
                    lambda x: escape_tag(str(x))
                    if x.is_text()
                    else f"<le>{escape_tag(str(x))}</le>",
                    self.message,
                )
            )
            + '"'
        )

class ChannelMessageEvent(MessageEvent):
    """公共频道消息"""

    __event__ = "message.group"
    message_type: Literal["group"]
    group_id: str


    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f"channel_{self.group_id}_user_{self.user_id}"

    @overrides(MessageEvent)
    def get_event_description(self) -> str:
        return (
            f'Message {self.message_id} from {self.user_id}@[服务器:{self.extra.guild_id}][频道:{self.group_id}] "'
            + "".join(
                map(
                    lambda x: escape_tag(str(x))
                    if x.is_text()
                    else f"<le>{escape_tag(str(x))}</le>",
                    self.event.content,
                )
            )
            + '"'
        )

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

# Notice Events
class NoticeEvent(Event):
    """通知事件"""

    __event__ = "notice"
    post_type: Literal["notice"]
    notice_type: str

    @overrides(Event)
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.notice_type}" + (
            f".{sub_type}" if sub_type else ""
        )

# Channel Events
class ChannelNoticeEvent(NoticeEvent):
    """频道消息事件"""

    group_id: int

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

class ChannelAddReactionEvent(ChannelNoticeEvent):
    """频道内用户添加 reaction"""

    __event__ = "notice.added_reaction"
    notice_type: Literal["added_reaction"]


    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.extra.body.user_id}@[服务器:{self.target_id}][频道:{self.extra.body.channel_id}] '
            + f'add Emoji "{self.extra.body.emoji.name}" ' + ''
            + f'to {self.extra.body.msg_id}'
        )

class ChannelDeletedReactionEvent(ChannelNoticeEvent):
    """频道内用户删除 reaction"""

    __event__ = "notice.deleted_reaction"
    notice_type: Literal["deleted_reaction"]

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.extra.body.user_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] '
            + f'delete Emoji "{self.extra.body.emoji.name}" '
            + f'from {self.extra.body.msg_id}'
        )

class ChannelUpdatedMessageEvent(ChannelNoticeEvent):
    """频道消息更新"""

    __event__ = "notice.updated_message"
    notice_type: Literal["updated_message"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.user_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] '
            + f'update message {self.extra.body.msg_id} '
            + f'to "{self.extra.body.content}' + '"'
        )

class ChannelDeleteMessageEvent(ChannelNoticeEvent):
    """频道消息被删除"""

    __event__ = "notice.deleted_message"
    notice_type: Literal["deleted_message"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.user_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] '
            + f'delete message "{self.extra.body.msg_id}" '
        )

class ChannelAddedEvent(ChannelNoticeEvent):
    """新增频道"""

    __event__ = "notice.added_channel"
    notice_type: Literal["added_channel"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.user_id}@[服务器:{self.target_id}] '
            + f'新增频道 "[{self.extra.body.name}:{self.extra.body.id}]' + '"'
        )

class ChannelUpdatedEvent(ChannelNoticeEvent):
    """修改频道信息"""

    __event__ = "notice.updated_channel"
    notice_type: Literal["updated_channel"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.user_id}@[服务器:{self.target_id}] '
            + f'修改频道信息 "[{self.extra.body.name}:{self.extra.body.id}]' + '"'
        )

class ChannelDeleteEvent(ChannelNoticeEvent):
    """删除频道"""

    __event__ = "notice.deleted_channel"
    notice_type: Literal["deleted_channel"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.user_id}@[服务器:{self.target_id}] '
            + f'删除频道 "[{self.extra.body.id}]' + '"'
        )

class ChannelPinnedMessageEvent(ChannelNoticeEvent):
    """新增频道置顶消息"""

    __event__ = "notice.pinned_message"
    notice_type: Literal["pinned_message"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.extra.body.operator_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] '
            + f'新增频道置顶消息 "{self.extra.body.msg_id}" '
        )

class ChannelUnpinnedMessageEvent(ChannelNoticeEvent):
    """取消频道置顶消息"""

    __event__ = "notice.unpinned_message"
    notice_type: Literal["unpinned_message"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.extra.body.operator_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] '
            + f'取消频道置顶消息 "{self.extra.body.msg_id}" '
        )

# Private Events
class PrivateNoticeEvent(NoticeEvent):
    "私聊消息事件"
    pass

class PrivateUpdateMessageEvent(PrivateNoticeEvent):
    """私聊消息更新"""

    __event__ = "notice.updated_private_message"
    notice_type: Literal["updated_private_message"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.extra.body.author_id} '
            + f'修改了消息 {self.extra.body.msg_id} '
            + f'to "{self.extra.body.content}' + '"'
        )

class PrivateDeleteMessageEvent(PrivateNoticeEvent):
    """私聊消息删除"""

    __event__ = "notice.deleted_private_message"
    notice_type: Literal["deleted_private_message"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.extra.body.author_id} '
            + f'删除了消息 {self.extra.body.msg_id} '
        )

class PrivateAddReactionEvent(PrivateNoticeEvent):
    """私聊内用户添加 reaction"""

    __event__ = "notice.private_added_reaction"
    notice_type: Literal["private_added_reaction"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.extra.body.user_id} '
            + f'add Emoji {self.extra.body.emoji.name} '
            + f'to "{self.extra.body.msg_id}' + '"'
        )

class PrivateDeleteReactionEvent(PrivateNoticeEvent):
    """私聊内用户取消 reaction"""

    __event__ = "notice.private_deleted_reaction"
    notice_type: Literal["private_deleted_reaction"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.extra.body.user_id} '
            + f'delete Emoji {self.extra.body.emoji.name} '
            + f'from "{self.extra.body.msg_id}' + '"'
        )

# Guild Events
class GuildNoticeEvent(NoticeEvent):
    """服务器相关事件"""
    group_id: int

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"Guild_{self.group_id}_user_{self.user_id}"

    def get_guild_id(self):
        return self.target_id

# Guild Member Events
class GuildMemberNoticeEvent(GuildNoticeEvent):
    """服务器成员相关事件"""
    pass

class GuildMemberIncreaseNoticeEvent(GuildMemberNoticeEvent):
    """新成员加入服务器"""

    __event__ = "notice.joined_guild"
    notice_type: Literal["joined_guild"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'用户 "{self.extra.body.user_id}" 加入服务器'
        )

class GuildMemberDecreaseNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员退出"""

    __event__ = "notice.exited_guild"
    notice_type: Literal["exited_guild"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'用户 "{self.extra.body.user_id}" 退出服务器'
        )

class GuildMemberUpdateNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员信息更新(修改昵称)"""

    __event__ = "notice.updated_guild_member"
    notice_type: Literal["updated_guild_member"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'用户 "{self.extra.body.user_id}" 修改昵称为 "{self.extra.body.nickname}"'
        )

class GuildMemberOnlineNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员上线"""

    __event__ = "notice.guild_member_online"
    notice_type: Literal["guild_member_online"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'成员 "{self.extra.body.user_id}" 上线'
        )

class GuildMemberOfflineNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员下线"""

    __event__ = "notice.guild_member_offline"
    notice_type: Literal["guild_member_offline"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'成员 "{self.extra.body.user_id}" 离线'
        )

# Guild Role Events
class GuildRoleNoticeEvent(GuildNoticeEvent):
    """服务器角色相关事件"""
    pass

class GuildRoleAddNoticeEvent(GuildRoleNoticeEvent):
    """服务器角色增加"""

    __event__ = "notice.added_role"
    notice_type: Literal["added_role"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'增加角色 "{self.extra.body.role_id}:{self.extra.body.name}" '
        )

class GuildRoleDeleteNoticeEvent(GuildRoleNoticeEvent):
    """服务器角色增加"""

    __event__ = "notice.deleted_role"
    notice_type: Literal["deleted_role"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'删除角色 "{self.extra.body.role_id}:{self.extra.body.name}" '
        )

class GuildRoleUpdateNoticeEvent(GuildRoleNoticeEvent):
    """服务器角色增加"""

    __event__ = "notice.updated_role"
    notice_type: Literal["updated_role"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'更改角色 "{self.extra.body.role_id}:{self.extra.body.name}" '
        )

# Guild Events
class GuildUpdateNoticeEvent(GuildNoticeEvent):
    """服务器信息更新"""

    __event__ = "notice.updated_guild"
    notice_type: Literal["updated_guild"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'信息更新 "{self.extra.body.id}:{self.extra.body.name}" '
        )

class GuildDeleteNoticeEvent(GuildNoticeEvent):
    """服务器删除"""

    __event__ = "notice.deleted_guild"
    notice_type: Literal["deleted_guild"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}] '
            + f'删除 "{self.extra.body.id}:{self.extra.body.name}" '
        )

class GuildAddBlockListNoticeEvent(GuildNoticeEvent):
    """服务器封禁用户"""

    __event__ = "notice.added_block_list"
    notice_type: Literal["added_block_list"]

    @overrides(Event)
    def get_event_description(self) -> str:
        block_list = ' '.join(self.extra.body.user_id)
        return (
            f'Notice {self.message_id} from {self.extra.operator_id}@[服务器:{self.target_id}] '
            + f'封禁用户 "{self.extra.body.remark}:{block_list}" '
        )

class GuildDeleteBlockListNoticeEvent(GuildNoticeEvent):
    """服务器取消封禁用户"""

    __event__ = "notice.deleted_block_list"
    notice_type: Literal["deleted_block_list"]

    @overrides(Event)
    def get_event_description(self) -> str:
        block_list = ' '.join(self.extra.body.user_id)
        return (
            f'Notice {self.message_id} from {self.extra.operator_id}@[服务器:{self.target_id}] '
            + f'取消封禁用户 "{block_list}" '
        )



# User Events
class UserNoticeEvent(NoticeEvent):
    """用户相关事件列表"""

    group_id: int
    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"Guild_{self.group_id}_{self.user_id}"

class UserJoinAudioChannelNoticeEvent(UserNoticeEvent):
    """用户加入语音频道"""

    __event__ = "notice.joined_channel"
    notice_type: Literal["joined_channel"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] '
            + f'用户 "{self.extra.body.user_id}" 加入语音频道 '
        )

class UserJoinAudioChannelEvent(UserNoticeEvent):
    """用户退出语音频道"""

    __event__ = "notice.exited_channel"
    notice_type: Literal["exited_channel"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] '
            + f'用户 "{self.extra.body.user_id}" 退出语音频道 '
        )

class UserInfoUpdateNoticeEvent(UserNoticeEvent):
    """
    用户信息更新

    该事件与服务器无关, 遵循以下条件:
        - 仅当用户的 用户名 或 头像 变更时
        - 仅通知与该用户存在关联的用户或 Bot
            a. 存在聊天会话
            b. 双方好友关系
    """

    __event__ = "notice.user_updated"
    notice_type: Literal["user_updated"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id} '
            + f'用户变更信息 "{self.extra.body.username}:{self.extra.body.avatar}" '
        )

class SelfJoinGuildNoticeEvent(NoticeEvent):
    """
    自己新加入服务器

    当自己被邀请或主动加入新的服务器时, 产生该事件
    """

    __event__ = "notice.self_joined_guild"
    notice_type: Literal["self_joined_guild"]
    user_id: str
    group_id: int

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id} '
            + f'Bot 加入服务器 "{self.extra.body.guild_id}" '
        )

class SelfExitGuildNoticeEvent(NoticeEvent):
    """
    自己退出服务器

    当自己被踢出服务器或被拉黑或主动退出服务器时, 产生该事件
    """

    __event__ = "notice.self_exited_guild"
    notice_type: Literal["self_exited_guild"]
    user_id: str
    group_id: int

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id} '
            + f'Bot 退出服务器 "{self.extra.body.guild_id}" '
        )

class CartBtnClickNoticeEvent(NoticeEvent):
    """
    Card 消息中的 Button 点击事件
    """

    __event__ = "notice.message_btn_click"
    notice_type: Literal["message_btn_click"]
    user_id: str
    group_id: int

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Notice {self.message_id} from {self.author_id} '
            + f'用户 "{self.extra.body.user_id}@{self.extra.body.user_info.nickname}" 点击 Card 消息'
            + f' "{self.extra.body.msg_id}" 中的 Button '
        )

# Meta Events
class MetaEvent(OriginEvent):
    """元事件"""

    __event__ = "meta_event"
    post_type: Literal["meta_event"]
    meta_event_type: str

    @overrides(Event)
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.meta_event_type}" + (
            f".{sub_type}" if sub_type else ""
        )

    @overrides(Event)
    def get_log_string(self) -> str:
        raise NoLogException

class LifecycleMetaEvent(MetaEvent):
    """生命周期元事件"""

    __event__ = "meta_event.lifecycle"
    meta_event_type: Literal["lifecycle"]
    sub_type: str

    session_id = str
    @overrides(BaseEvent)
    def get_session_id(self) -> str:
        return self.session_id

class HeartbeatMetaEvent(MetaEvent):
    """心跳元事件"""

    __event__ = "meta_event.heartbeat"
    meta_event_type: Literal["heartbeat"]


_t = StringTrie(separator=".")

# define `model` first to avoid globals changing while `for`
model = None
for model in globals().values():
    if not inspect.isclass(model) or not issubclass(model, OriginEvent):
        continue
    _t["." + model.__event__] = model


def get_event_model(event_name) -> List[Type[OriginEvent]]:
    """
    :说明:

      根据事件名获取对应 ``Event Model`` 及 ``FallBack Event Model`` 列表

    :返回:

      - ``List[Type[Event]]``
    """
    return [model.value for model in _t.prefixes("." + event_name)][::-1]


__all__ = [
    "EventTypes",
    "SignalTypes",
    "Role",
    "Channel",
    "User",
    "Guild",
    "Emoji",
    "Attachment",
    "Body",
    "Extra",
    "OriginEvent",
    "Kmarkdown",
    "EventMessage",
    "Event",
    "MessageEvent",
    "PrivateMessageEvent",
    "ChannelMessageEvent",
    "NoticeEvent",
    "ChannelNoticeEvent",
    "ChannelAddReactionEvent",
    "ChannelDeletedReactionEvent",
    "ChannelUpdatedMessageEvent",
    "ChannelDeleteMessageEvent",
    "ChannelAddedEvent",
    "ChannelUpdatedEvent",
    "ChannelDeleteEvent",
    "ChannelPinnedMessageEvent",
    "ChannelUnpinnedMessageEvent",
    "PrivateNoticeEvent",
    "PrivateUpdateMessageEvent",
    "PrivateDeleteMessageEvent",
    "PrivateAddReactionEvent",
    "PrivateDeleteReactionEvent",
    "GuildNoticeEvent",
    "GuildMemberNoticeEvent",
    "GuildMemberIncreaseNoticeEvent",
    "GuildMemberDecreaseNoticeEvent",
    "GuildMemberUpdateNoticeEvent",
    "GuildMemberOnlineNoticeEvent",
    "GuildMemberOfflineNoticeEvent",
    "GuildRoleNoticeEvent",
    "GuildRoleAddNoticeEvent",
    "GuildRoleDeleteNoticeEvent",
    "GuildRoleUpdateNoticeEvent",
    "GuildUpdateNoticeEvent",
    "GuildDeleteNoticeEvent",
    "GuildAddBlockListNoticeEvent",
    "GuildDeleteBlockListNoticeEvent",
    "UserNoticeEvent",
    "UserJoinAudioChannelNoticeEvent",
    "UserJoinAudioChannelEvent",
    "UserInfoUpdateNoticeEvent",
    "SelfJoinGuildNoticeEvent",
    "SelfExitGuildNoticeEvent",
    "CartBtnClickNoticeEvent",
    "MetaEvent",
    "LifecycleMetaEvent",
    "HeartbeatMetaEvent"
]

