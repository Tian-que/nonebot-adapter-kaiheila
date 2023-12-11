from typing import List, Optional

from pydantic import Field, BaseModel


class BotConfig(BaseModel):
    """
    Kaiheila Bot 配置类
    :配置项:
      - ``token``: Kaiheila 开发者中心获得
    """

    token: str

    class Config:
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

    class Config:
        extra = "allow"
        allow_population_by_field_name = True
