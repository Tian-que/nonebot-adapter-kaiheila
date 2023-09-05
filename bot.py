import nonebot
from nonebot.adapters.kaiheila import Adapter, Bot

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

@driver.on_bot_connect()
def _(bot: Bot):
    bot.upload_file()


if __name__ == "__main__":
    nonebot.run()
