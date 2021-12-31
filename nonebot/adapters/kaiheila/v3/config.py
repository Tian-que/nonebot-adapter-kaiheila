from typing import List, Optional

from pydantic import Field, BaseModel

class Config(BaseModel):
    """
    Kaiheila 配置类

    :配置项:

      - ``token`` : Kaiheila 开发者中心获得
      - ``compress`` : 是否开启压缩, 默认为 False

    :示例:

    .. code-block:: default
    
        bots = ["bot1_token", "bot2_token"]
    """
    bots: List[str] = Field(default_factory=list)

    compress: Optional[bool] = Field(default=False)

    class Config:
        extra = "allow"
        allow_population_by_field_name = True
