# Kaiheila Adapter 使用指南

**此适配器还在施工中，遇到问题请尽快反馈！**

## 配置 NoneBot

本项目仅为 Nonebot 适配器插件，要搭建 Bot 请先阅读 [Nonebot2 文档](https://v2.nonebot.dev/)

以下内容作为对于 Nonebot 文档的 `driver` 参数和 `adapter` 部分的扩充

## 安装 adapter
请使用 pip 或项目包管理工具进行安装

```shell
pip install nonebot-adapter-kaiheila
```

## 配置 Kaiheila Bot

### 申请一个 Kaiheila 机器人

首先你需要注册 [开黑啦](https://www.kaiheila.cn/) 帐号，加入 `机器人社区` 私聊 `koenigseggposche#8281` 邀请你加入 `「开黑啦」开发者内测频道` 并进行报名获取机器人内测资格。

如果你已经拥有内测资格，则需要在 [开发者平台](https://developer.kaiheila.cn/) 获取 Token 

获取流程：应用 - 新建应用 - 填入应用名称 - 我的应用 - 点击Bot图标 - 机器人 - 机器人连接模式 - Token

```plain
1/MTA2MjE=/DnbsqfmN6/IfVCrdOiGXKcQ==
```

将这个 token 填入 NoneBot 的`env`文件：

```dotenv
kaiheila_bots =[{"token": "1/MTA2MjE=/DnbsqfmN6/IfVCrdOiGXKcQ=="}]
```

## 配置驱动器

NoneBot 默认的驱动器为 FastAPI，它是一个服务端类型驱动器（ReverseDriver），而 Kaiheila 适配器至少需要一个客户端类型驱动器（ForwardDriver），所以你需要额外安装其他驱动器。

目前推荐 httpx 客户端类型驱动器，你可以使用 nb-cli 进行安装。

```shell
nb driver install httpx
```

别忘了在环境文件中写入配置：

```dotenv
driver=~httpx+~websockets
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

现在，你可以私聊自己的 Kaiheila Bot `/echo hello world`，不出意外的话，它将回复你 `hello world`。(如果在频道内请@bot发送)


## 调用 API

（感谢 @DogAddan 的贡献）

通过调用bot实例方法的形式可以调用开黑啦的所有API。

你可以在[KOOK 开发者平台](https://developer.kaiheila.cn/doc/intro)查看所有的API。API对应方法名参见[源码文件](https://github.com/Tian-que/nonebot-adapter-kaiheila/blob/master/nonebot/adapters/kaiheila/api/client.pyi)。

对于`POST asset/create`接口（上传文件/图片），你还可以直接调用`bot.upload_file(file)`方法。
