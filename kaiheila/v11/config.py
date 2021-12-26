from typing import List, TypedDict, Optional

from pydantic import Field, AnyUrl, BaseModel


class WSUrl(AnyUrl):
    allow_schemes = {"ws", "wss"}

class BotConfig(TypedDict):
    client_id: str
    token: str
    client_secret: str

class Config(BaseModel):
    """
    Kaiheila 配置类

    :配置项:

      - ``client_id`` : Kaiheila 开发者中心获得
      - ``token`` : Kaiheila 开发者中心获得
      - ``client_secret`` : Kaiheila 开发者中心获得
      - ``compress`` : 是否开启压缩, 默认为 False

    :示例:

    .. code-block:: default
    
        bots = [{"client_id" : "bot1_client_id", "token" : "bot1_token", "client_secret" : "bot1_client_secret"},{"client_id" : "bot2_client_id", "token" : "bot2_token", "client_secret" : "bot2_client_secret"}]
    """
    bots: List[BotConfig] = Field(default_factory=list)

    compress: Optional[bool] = Field(default=False)

    class Config:
        extra = "allow"
        allow_population_by_field_name = True
