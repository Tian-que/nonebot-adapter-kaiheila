# Kaiheila Adapter 使用指南

**此适配器还在施工中，遇到问题请尽快反馈！**

## 配置 Kaiheila Bot

### 申请一个 Kaiheila 机器人

首先你需要注册 [开黑啦](https://www.kaiheila.cn/) 帐号，加入 `机器人社区` 私聊 `冰飞FlappyIce#1437` 邀请你加入 `「开黑啦」开发者内测频道` 并进行报名获取机器人内测资格。

如果你已经拥有内测资格，则需要在 [开发者平台](https://developer.kaiheila.cn/) 获取 Token 

获取流程：应用 - 新建应用 - 填入应用名称 - 我的应用 - 点击Bot图标 - 机器人 - 机器人连接模式 - Token

```plain
1/MTA2MjE=/DnbsqfmN6/IfVCrdOiGXKcQ==
```

将这个 token 填入 NoneBot 的`env`文件：

```dotenv
kaiheila_bots =[{"token": "1/MTA2MjE=/DnbsqfmN6/IfVCrdOiGXKcQ=="}]
```

如果你需要让你的 Bot 响应除了 `/` 开头之外的消息，你需要向BotFather 发送 `/setprivacy` 并选择 `Disable`。

## 配置 NoneBot

## 配置驱动器

NoneBot 默认的驱动器为 FastAPI，它是一个服务端类型驱动器（ReverseDriver），而 Kaiheila 适配器至少需要一个客户端类型驱动器（ForwardDriver），所以你需要额外安装其他驱动器。

HTTPX 是推荐的客户端类型驱动器，你可以使用 nb-cli 进行安装。

```shell
nb driver install httpx
```

别忘了在环境文件中写入配置：

```dotenv
driver=~fastapi+~httpx
```

## 第一次对话


```python
import nonebot
from nonebot.adapters.kaiheila import Adapter as KaiheilaAdapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(KaiheilaAdapter)

nonebot.load_builtin_plugins("echo")

nonebot.run()
```

现在，你可以私聊自己的 Kaiheila Bot `/echo hello world`，不出意外的话，它将回复你 `hello world`。