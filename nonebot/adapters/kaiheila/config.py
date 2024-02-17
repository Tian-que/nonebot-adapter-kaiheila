from typing import List, Optional, Tuple

from pydantic import Field, BaseModel
from nonebot.compat import PYDANTIC_V2, ConfigDict


class BotConfig(BaseModel):
    """
    Kaiheila Bot 配置类
    :配置项:
      - ``token``: Kaiheila 开发者中心获得
    """

    token: str

    if PYDANTIC_V2:
        model_config = ConfigDict(
            extra="ignore",
            populate_by_name=True,
        )
    else:

        class Config(ConfigDict):
            extra = "ignore"
            allow_population_by_field_name = True


class Config(BaseModel):
    """
    Kaiheila 配置类

    :配置项:

      - ``kaiheila_bots`` : Kaiheila 开发者中心获得
      - ``compress`` : 是否开启压缩, 默认为 False

    :示例:

    .. code-block:: default

        bots = [{"token": "token1"}, {"token": "token2"}]
    """

    kaiheila_bots: List["BotConfig"] = Field(default_factory=list)
    compress: Optional[bool] = Field(default=False)
    kaiheila_ignore_events: Tuple[str, ...] = Field(default_factory=tuple)
    kaiheila_ignore_other_bots: Optional[bool] = Field(default=True)

    if PYDANTIC_V2:
        model_config = ConfigDict(
            extra="allow",
            populate_by_name=True,
        )
    else:

        class Config(ConfigDict):
            extra = "allow"
            allow_population_by_field_name = True
