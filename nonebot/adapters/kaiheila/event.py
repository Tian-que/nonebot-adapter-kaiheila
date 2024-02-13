import inspect
from enum import IntEnum
from typing import List, Type, Union, Optional
from typing_extensions import Literal, override

from pygtrie import StringTrie
from nonebot.utils import escape_tag
from nonebot.compat import model_dump
from pydantic import Field, HttpUrl, BaseModel, validator

from nonebot.adapters import Event as BaseEvent

from .utils import AttrDict
from .compat import model_validator
from .exception import NoLogException
from .message import Message, MessageDeserializer
from .api import Role, User, Emoji, Guild, Channel


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


class Attachment(BaseModel):
    type: str
    name: str
    url: HttpUrl
    file_type: Optional[str] = Field(None)
    size: Optional[int] = Field(None)
    duration: Optional[float] = Field(None)
    width: Optional[int] = Field(None)
    hight: Optional[int] = Field(None)


class Extra(BaseModel):
    type_: Union[int, str] = Field(None, alias="type")
    guild_id: Optional[str] = Field(None)
    channel_name: Optional[str] = Field(None)
    mention: Optional[List[str]] = Field(None)
    mention_all: Optional[bool] = Field(None)
    mention_roles: Optional[List[str]] = Field(None)
    mention_here: Optional[bool] = Field(None)
    author: Optional[User] = Field(None)
    body: Optional[AttrDict] = Field(None)
    attachments: Optional[Attachment] = Field(None)
    code: Optional[str] = Field(None)

    @validator("body", pre=True)
    def convert_body(cls, v):
        if v is None:
            return None

        if not isinstance(v, dict):
            raise TypeError("body must be dict")
        if not isinstance(v, AttrDict):
            v = AttrDict(v)
        return v

    class Config:
        arbitrary_types_allowed = True


class OriginEvent(BaseEvent):
    """为了区分信令中非Event事件，增加了前置OriginEvent"""

    __event__ = ""

    post_type: str

    @override
    def get_type(self) -> str:
        return self.post_type

    @override
    def get_event_name(self) -> str:
        return self.post_type

    @override
    def get_event_description(self) -> str:
        return escape_tag(str(model_dump(self)))

    @override
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @override
    def get_plaintext(self) -> str:
        raise ValueError("Event has no message!")

    @override
    def get_user_id(self) -> str:
        raise ValueError("Event has no message!")

    @override
    def get_session_id(self) -> str:
        raise ValueError("Event has no message!")

    @override
    def is_tome(self) -> bool:
        return False


class Kmarkdown(BaseModel):
    raw_content: str
    mention_part: list
    mention_role_part: list


class EventMessage(BaseModel):
    type: Union[int, str]
    guild_id: Optional[str] = None
    channel_name: Optional[str] = None
    mention: Optional[List] = None
    mention_all: Optional[bool] = None
    mention_roles: Optional[List] = None
    mention_here: Optional[bool] = None
    nav_channels: Optional[List] = None
    author: User

    kmarkdown: Optional[Kmarkdown] = None

    code: Optional[str] = None
    attachments: Optional[Attachment] = None

    content: Message

    @model_validator(mode="before")
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
    type_: int = Field(alias="type")
    """1:文字消息\n2:图片消息\n3:视频消息\n4:文件消息\n8:音频消息\n9:KMarkdown\n10:card消息\n255:系统消息\n其它的暂未开放"""
    target_id: str
    """
    发送目的\n
    频道消息类时, 代表的是频道 channel_id\n
    如果 channel_type 为 GROUP 组播且 type 为 255 系统消息时，则代表服务器 guild_id"""
    author_id: str = None
    content: str
    msg_id: str
    msg_timestamp: int
    nonce: str
    extra: Extra
    user_id: str

    post_type: str
    self_id: Optional[str] = None  # onebot兼容

    @override
    def get_event_description(self) -> str:
        return escape_tag(str(model_dump(self)))

    @override
    def get_plaintext(self) -> str:
        return self.content

    @override
    def get_user_id(self) -> str:
        return self.user_id

    @override
    def get_session_id(self) -> str:
        raise ValueError("Event has no message!")

    @override
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

    @override
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.message_type}" + (
            f".{sub_type}" if sub_type else ""
        )

    @override
    def get_message(self) -> Message:
        return self.message

    @override
    def get_plaintext(self) -> str:
        return self.message.extract_plain_text()

    @override
    def is_tome(self) -> bool:
        return self.to_me

    @property
    def message(self) -> Message:
        return self.event.content


class PrivateMessageEvent(MessageEvent):
    """私聊消息"""

    __event__ = "message.private"
    message_type: Literal["private"]

    @override
    def get_session_id(self) -> str:
        return f"user_{self.user_id}"

    @override
    def get_event_description(self) -> str:
        return (
            f'Message {self.msg_id} from {self.user_id} "'
            + "".join(
                escape_tag(str(x)) if x.is_text() else f"<le>{escape_tag(str(x))}</le>"
                for x in self.message
            )
            + '"'
        )


class ChannelMessageEvent(MessageEvent):
    """公共频道消息"""

    __event__ = "message.group"
    message_type: Literal["group"]
    group_id: str

    @override
    def get_event_description(self) -> str:
        return (
            f'Message {self.msg_id} from {self.user_id}@[服务器:{self.extra.guild_id}][频道:{self.group_id}] "'
            + "".join(
                escape_tag(str(x)) if x.is_text() else f"<le>{escape_tag(str(x))}</le>"
                for x in self.event.content
            )
        )

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


# Notice Events
class NoticeEvent(Event):
    """通知事件"""

    __event__ = "notice"
    post_type: Literal["notice"]
    notice_type: str

    @override
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.notice_type}" + (
            f".{sub_type}" if sub_type else ""
        )


# Channel Events
class ChannelNoticeEvent(NoticeEvent):
    """频道消息事件"""

    group_id: int

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class ChannelAddReactionEvent(ChannelNoticeEvent):
    """频道内用户添加 reaction"""

    __event__ = "notice.added_reaction"
    notice_type: Literal["added_reaction"]

    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Notice {self.msg_id} from {self.extra.body.user_id}@"
            f"[服务器:{self.target_id}]"
            f"[频道:{self.extra.body.channel_id}] "
            + f'add Emoji "{self.extra.body.emoji.name}" '
            + ""
            + f"to {self.extra.body.msg_id}"
            + '"'
        )


class ChannelDeletedReactionEvent(ChannelNoticeEvent):
    """频道内用户删除 reaction"""

    __event__ = "notice.deleted_reaction"
    notice_type: Literal["deleted_reaction"]

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Notice {self.msg_id} from {self.extra.body.user_id}@"
            f"[服务器:{self.target_id}]"
            f"[频道{self.extra.body.channel_id}] "
            + f'delete Emoji "{self.extra.body.emoji.name}" '
            + f"from {self.extra.body.msg_id}"
        )


class ChannelUpdatedMessageEvent(ChannelNoticeEvent):
    """频道消息更新"""

    __event__ = "notice.updated_message"
    notice_type: Literal["updated_message"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.user_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] "
            + f"update message {self.extra.body.msg_id} "
            + f'to "{self.extra.body.content}'
            + '"'
        )


class ChannelDeleteMessageEvent(ChannelNoticeEvent):
    """频道消息被删除"""

    __event__ = "notice.deleted_message"
    notice_type: Literal["deleted_message"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.user_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] "
            + f'delete message "{self.extra.body.msg_id}" '
        )


class ChannelAddedEvent(ChannelNoticeEvent):
    """新增频道"""

    __event__ = "notice.added_channel"
    notice_type: Literal["added_channel"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.user_id}@[服务器:{self.target_id}] "
            + f'新增频道 "[{self.extra.body.name}:{self.extra.body.id}]'
            + '"'
        )


class ChannelUpdatedEvent(ChannelNoticeEvent):
    """修改频道信息"""

    __event__ = "notice.updated_channel"
    notice_type: Literal["updated_channel"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.user_id}@[服务器:{self.target_id}] "
            + f'修改频道信息 "[{self.extra.body.name}:{self.extra.body.id}]'
            + '"'
        )


class ChannelDeleteEvent(ChannelNoticeEvent):
    """删除频道"""

    __event__ = "notice.deleted_channel"
    notice_type: Literal["deleted_channel"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.user_id}@[服务器:{self.target_id}] "
            + f'删除频道 "[{self.extra.body.id}]'
            + '"'
        )


class ChannelPinnedMessageEvent(ChannelNoticeEvent):
    """新增频道置顶消息"""

    __event__ = "notice.pinned_message"
    notice_type: Literal["pinned_message"]

    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Notice {self.msg_id} from {self.extra.body.operator_id}@"
            f"[服务器:{self.target_id}]"
            f"[频道{self.extra.body.channel_id}] "
            + f'新增频道置顶消息 "{self.extra.body.msg_id}" '
        )


class ChannelUnpinnedMessageEvent(ChannelNoticeEvent):
    """取消频道置顶消息"""

    __event__ = "notice.unpinned_message"
    notice_type: Literal["unpinned_message"]

    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Notice {self.msg_id} from {self.extra.body.operator_id}@"
            f"[服务器:{self.target_id}]"
            f"[频道{self.extra.body.channel_id}] "
            + f'取消频道置顶消息 "{self.extra.body.msg_id}" '
        )


# Private Events
class PrivateNoticeEvent(NoticeEvent):
    """私聊消息事件"""

    pass


class PrivateUpdateMessageEvent(PrivateNoticeEvent):
    """私聊消息更新"""

    __event__ = "notice.updated_private_message"
    notice_type: Literal["updated_private_message"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.extra.body.author_id} "
            + f"修改了消息 {self.extra.body.msg_id} "
            + f'to "{self.extra.body.content}'
            + '"'
        )


class PrivateDeleteMessageEvent(PrivateNoticeEvent):
    """私聊消息删除"""

    __event__ = "notice.deleted_private_message"
    notice_type: Literal["deleted_private_message"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.extra.body.author_id} "
            + f"删除了消息 {self.extra.body.msg_id} "
        )


class PrivateAddReactionEvent(PrivateNoticeEvent):
    """私聊内用户添加 reaction"""

    __event__ = "notice.private_added_reaction"
    notice_type: Literal["private_added_reaction"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.extra.body.user_id} "
            + f"add Emoji {self.extra.body.emoji.name} "
            + f'to "{self.extra.body.msg_id}'
            + '"'
        )


class PrivateDeleteReactionEvent(PrivateNoticeEvent):
    """私聊内用户取消 reaction"""

    __event__ = "notice.private_deleted_reaction"
    notice_type: Literal["private_deleted_reaction"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.extra.body.user_id} "
            + f"delete Emoji {self.extra.body.emoji.name} "
            + f'from "{self.extra.body.msg_id}'
            + '"'
        )


# Guild Events
class GuildNoticeEvent(NoticeEvent):
    """服务器相关事件"""

    group_id: int

    @override
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

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'用户 "{self.extra.body.user_id}" 加入服务器'
        )


class GuildMemberDecreaseNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员退出"""

    __event__ = "notice.exited_guild"
    notice_type: Literal["exited_guild"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'用户 "{self.extra.body.user_id}" 退出服务器'
        )


class GuildMemberUpdateNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员信息更新(修改昵称)"""

    __event__ = "notice.updated_guild_member"
    notice_type: Literal["updated_guild_member"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'用户 "{self.extra.body.user_id}" 修改昵称为 "{self.extra.body.nickname}"'
        )


class GuildMemberOnlineNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员上线"""

    __event__ = "notice.guild_member_online"
    notice_type: Literal["guild_member_online"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'成员 "{self.extra.body.user_id}" 上线'
        )


class GuildMemberOfflineNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员下线"""

    __event__ = "notice.guild_member_offline"
    notice_type: Literal["guild_member_offline"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
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

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'增加角色 "{self.extra.body.role_id}:{self.extra.body.name}" '
        )


class GuildRoleDeleteNoticeEvent(GuildRoleNoticeEvent):
    """服务器角色增加"""

    __event__ = "notice.deleted_role"
    notice_type: Literal["deleted_role"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'删除角色 "{self.extra.body.role_id}:{self.extra.body.name}" '
        )


class GuildRoleUpdateNoticeEvent(GuildRoleNoticeEvent):
    """服务器角色增加"""

    __event__ = "notice.updated_role"
    notice_type: Literal["updated_role"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'更改角色 "{self.extra.body.role_id}:{self.extra.body.name}" '
        )


# Guild Events
class GuildUpdateNoticeEvent(GuildNoticeEvent):
    """服务器信息更新"""

    __event__ = "notice.updated_guild"
    notice_type: Literal["updated_guild"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'信息更新 "{self.extra.body.id}:{self.extra.body.name}" '
        )


class GuildDeleteNoticeEvent(GuildNoticeEvent):
    """服务器删除"""

    __event__ = "notice.deleted_guild"
    notice_type: Literal["deleted_guild"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}] "
            + f'删除 "{self.extra.body.id}:{self.extra.body.name}" '
        )


class GuildAddBlockListNoticeEvent(GuildNoticeEvent):
    """服务器封禁用户"""

    __event__ = "notice.added_block_list"
    notice_type: Literal["added_block_list"]

    @override
    def get_event_description(self) -> str:
        block_list = " ".join(self.extra.body.user_id)
        return (
            f"Notice {self.msg_id} from {self.extra.body.operator_id}@[服务器:{self.target_id}] "
            + f'封禁用户 "{self.extra.body.remark}:{block_list}" '
        )


class GuildDeleteBlockListNoticeEvent(GuildNoticeEvent):
    """服务器取消封禁用户"""

    __event__ = "notice.deleted_block_list"
    notice_type: Literal["deleted_block_list"]

    @override
    def get_event_description(self) -> str:
        block_list = " ".join(self.extra.body.user_id)
        return (
            f"Notice {self.msg_id} from {self.extra.body.operator_id}@[服务器:{self.target_id}] "
            + f'取消封禁用户 "{block_list}" '
        )


# User Events
class UserNoticeEvent(NoticeEvent):
    """用户相关事件列表"""

    group_id: int

    @override
    def get_session_id(self) -> str:
        return f"Guild_{self.group_id}_{self.user_id}"


class UserJoinAudioChannelNoticeEvent(UserNoticeEvent):
    """用户加入语音频道"""

    __event__ = "notice.joined_channel"
    notice_type: Literal["joined_channel"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] "
            + f'用户 "{self.extra.body.user_id}" 加入语音频道 '
        )


class UserJoinAudioChannelEvent(UserNoticeEvent):
    """用户退出语音频道"""

    __event__ = "notice.exited_channel"
    notice_type: Literal["exited_channel"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id}@[服务器:{self.target_id}][频道{self.extra.body.channel_id}] "
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

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id} "
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

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id} "
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

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id} "
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

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    @override
    def get_event_description(self) -> str:
        return (
            f"Notice {self.msg_id} from {self.author_id} "
            + f'用户 "{self.extra.body.user_id}@{self.extra.body.user_info.nickname}" 点击 Card 消息'
            + f' "{self.extra.body.msg_id}" 中的 Button '
        )


# Meta Events
class MetaEvent(OriginEvent):
    """元事件"""

    __event__ = "meta_event"
    post_type: Literal["meta_event"]
    meta_event_type: str

    @override
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.meta_event_type}" + (
            f".{sub_type}" if sub_type else ""
        )

    @override
    def get_log_string(self) -> str:
        raise NoLogException


class LifecycleMetaEvent(MetaEvent):
    """生命周期元事件"""

    __event__ = "meta_event.lifecycle"
    meta_event_type: Literal["lifecycle"]
    sub_type: str

    session_id: str

    @override
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
    "HeartbeatMetaEvent",
]
