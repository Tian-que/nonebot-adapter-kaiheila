import inspect
from typing_extensions import Literal
from typing import TYPE_CHECKING, List, Type, Optional, Dict, Union

from pydantic import BaseModel, Field, validator
from pygtrie import StringTrie

from nonebot.typing import overrides
from nonebot.utils import escape_tag
from nonebot.adapters import Event as BaseEvent

from .message import Message
from .exception import NoLogException

if TYPE_CHECKING:
    from .bot import Bot

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


class Attachment(BaseModel):
    type_: Optional[int] = Field(None, alias="type")
    url: str
    name: str
    file_type: Optional[str] = Field(None)
    size: Optional[int] = Field(None)
    duration: Optional[float] = Field(None)
    width: Optional[int] = Field(None)
    height: Optional[int] = Field(None)


class Body(BaseModel):
    msg_id: str
    user_id: str
    author_id: str
    target_id: str
    channel_id: str
    emoji: Optional[Emoji] = None
    content: Optional[str] = None
    updated_at: int
    chat_code: str

    class Config:
        extra = "allow"

class Extra(BaseModel):
    type_: Optional[int] = Field(None, alias="type")
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

    @validator("body")
    def check_body(cls, v, values):
        if values["type_"] != 255 and v:  # 非系统消息 没有body
            raise ValueError("非系统消息不应该有body字段")
        return v

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
    author_id: str
    content: str
    msg_id: str
    msg_timestamp: int
    nonce: str
    extra: Extra

    post_type: str
    self_id: Optional[str] = None # onebot兼容


# NOP
# Models
class Sender(BaseModel):
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    card: Optional[str] = None
    area: Optional[str] = None
    level: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None

    class Config:
        extra = "allow"

# NOP
class Reply(BaseModel):
    time: int
    message_type: str
    message_id: int
    real_id: int
    sender: Sender
    message: Message

    class Config:
        extra = "allow"

# NOP
class Anonymous(BaseModel):
    id: int
    name: str
    flag: str

    class Config:
        extra = "allow"

# NOP
class File(BaseModel):
    id: str
    name: str
    size: int
    busid: int

    class Config:
        extra = "allow"

# NOP
class Status(BaseModel):
    online: bool
    good: bool

    class Config:
        extra = "allow"


# Message Events
class MessageEvent(Event):
    """消息事件"""

    __event__ = "message"

    post_type: Literal["message"] = "message"
    message_type: str  # group private 其实是person
    sub_type: str
    message: Message

    # user_id: int
    # message_id: int
    # message: Message
    # raw_message: str
    # font: int
    # sender: Sender


    to_me: bool = False
    """
    :说明: 消息是否与机器人有关

    :类型: ``bool``
    """
    reply: Optional[Reply] = None
    """
    :说明: 消息中提取的回复消息，内容为 ``get_msg`` API 返回结果

    :类型: ``Optional[Reply]``
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
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(Event)
    def get_session_id(self) -> str:
        return str(self.user_id)

    @overrides(Event)
    def is_tome(self) -> bool:
        return self.to_me


class PrivateMessageEvent(MessageEvent):
    """私聊消息"""

    __event__ = "message.private"
    message_type: Literal["private"]

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


class GroupMessageEvent(MessageEvent):
    """群消息"""

    __event__ = "message.group"
    message_type: Literal["group"]
    group_id: int
    anonymous: Optional[Anonymous] = None

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Message {self.message_id} from {self.user_id}@[群:{self.group_id}] "'
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


class GroupUploadNoticeEvent(NoticeEvent):
    """群文件上传事件"""

    __event__ = "notice.group_upload"
    notice_type: Literal["group_upload"]
    user_id: int
    group_id: int
    file: File

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class GroupAdminNoticeEvent(NoticeEvent):
    """群管理员变动"""

    __event__ = "notice.group_admin"
    notice_type: Literal["group_admin"]
    sub_type: str
    user_id: int
    group_id: int

    @overrides(NoticeEvent)
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class GroupDecreaseNoticeEvent(NoticeEvent):
    """群成员减少事件"""

    __event__ = "notice.group_decrease"
    notice_type: Literal["group_decrease"]
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int

    @overrides(NoticeEvent)
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class GroupIncreaseNoticeEvent(NoticeEvent):
    """群成员增加事件"""

    __event__ = "notice.group_increase"
    notice_type: Literal["group_increase"]
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int

    @overrides(NoticeEvent)
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class GroupBanNoticeEvent(NoticeEvent):
    """群禁言事件"""

    __event__ = "notice.group_ban"
    notice_type: Literal["group_ban"]
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int
    duration: int

    @overrides(NoticeEvent)
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class FriendAddNoticeEvent(NoticeEvent):
    """好友添加事件"""

    __event__ = "notice.friend_add"
    notice_type: Literal["friend_add"]
    user_id: int

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return str(self.user_id)


class GroupRecallNoticeEvent(NoticeEvent):
    """群消息撤回事件"""

    __event__ = "notice.group_recall"
    notice_type: Literal["group_recall"]
    user_id: int
    group_id: int
    operator_id: int
    message_id: int

    @overrides(Event)
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class FriendRecallNoticeEvent(NoticeEvent):
    """好友消息撤回事件"""

    __event__ = "notice.friend_recall"
    notice_type: Literal["friend_recall"]
    user_id: int
    message_id: int

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return str(self.user_id)


class NotifyEvent(NoticeEvent):
    """提醒事件"""

    __event__ = "notice.notify"
    notice_type: Literal["notify"]
    sub_type: str
    user_id: int
    group_id: int

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class PokeNotifyEvent(NotifyEvent):
    """戳一戳提醒事件"""

    __event__ = "notice.notify.poke"
    sub_type: Literal["poke"]
    target_id: int
    group_id: Optional[int] = None

    @overrides(Event)
    def is_tome(self) -> bool:
        return self.target_id == self.self_id

    @overrides(NotifyEvent)
    def get_session_id(self) -> str:
        if not self.group_id:
            return str(self.user_id)
        return super().get_session_id()


class LuckyKingNotifyEvent(NotifyEvent):
    """群红包运气王提醒事件"""

    __event__ = "notice.notify.lucky_king"
    sub_type: Literal["lucky_king"]
    target_id: int

    @overrides(Event)
    def is_tome(self) -> bool:
        return self.target_id == self.self_id

    @overrides(NotifyEvent)
    def get_user_id(self) -> str:
        return str(self.target_id)

    @overrides(NotifyEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.target_id}"


class HonorNotifyEvent(NotifyEvent):
    """群荣誉变更提醒事件"""

    __event__ = "notice.notify.honor"
    sub_type: Literal["honor"]
    honor_type: str

    @overrides(Event)
    def is_tome(self) -> bool:
        return self.user_id == self.self_id


# Request Events
class RequestEvent(Event):
    """请求事件"""

    __event__ = "request"
    post_type: Literal["request"]
    request_type: str

    @overrides(Event)
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.request_type}" + (
            f".{sub_type}" if sub_type else ""
        )


class FriendRequestEvent(RequestEvent):
    """加好友请求事件"""

    __event__ = "request.friend"
    request_type: Literal["friend"]
    user_id: int
    comment: str
    flag: str

    @overrides(RequestEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(RequestEvent)
    def get_session_id(self) -> str:
        return str(self.user_id)

    async def approve(self, bot: "Bot", remark: str = ""):
        return await bot.set_friend_add_request(
            flag=self.flag, approve=True, remark=remark
        )

    async def reject(self, bot: "Bot"):
        return await bot.set_friend_add_request(flag=self.flag, approve=False)


class GroupRequestEvent(RequestEvent):
    """加群请求/邀请事件"""

    __event__ = "request.group"
    request_type: Literal["group"]
    sub_type: str
    group_id: int
    user_id: int
    comment: str
    flag: str

    @overrides(RequestEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)

    @overrides(RequestEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    async def approve(self, bot: "Bot"):
        return await bot.set_group_add_request(
            flag=self.flag, sub_type=self.sub_type, approve=True
        )

    async def reject(self, bot: "Bot", reason: str = ""):
        return await bot.set_group_add_request(
            flag=self.flag, sub_type=self.sub_type, approve=False, reason=reason
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
    status: Status
    interval: int


_t = StringTrie(separator=".")

# define `model` first to avoid globals changing while `for`
model = None
for model in globals().values():
    if not inspect.isclass(model) or not issubclass(model, Event):
        continue
    _t["." + model.__event__] = model


def get_event_model(event_name) -> List[Type[Event]]:
    """
    :说明:

      根据事件名获取对应 ``Event Model`` 及 ``FallBack Event Model`` 列表

    :返回:

      - ``List[Type[Event]]``
    """
    return [model.value for model in _t.prefixes("." + event_name)][::-1]


__all__ = [
    "Event",
    "MessageEvent",
    "PrivateMessageEvent",
    "GroupMessageEvent",
    "NoticeEvent",
    "GroupUploadNoticeEvent",
    "GroupAdminNoticeEvent",
    "GroupDecreaseNoticeEvent",
    "GroupIncreaseNoticeEvent",
    "GroupBanNoticeEvent",
    "FriendAddNoticeEvent",
    "GroupRecallNoticeEvent",
    "FriendRecallNoticeEvent",
    "NotifyEvent",
    "PokeNotifyEvent",
    "LuckyKingNotifyEvent",
    "HonorNotifyEvent",
    "RequestEvent",
    "FriendRequestEvent",
    "GroupRequestEvent",
    "MetaEvent",
    "LifecycleMetaEvent",
    "HeartbeatMetaEvent",
    "get_event_model",
]
