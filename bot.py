# -*- coding: utf-8 -*-
import nonebot
import os
import sys
from nonebot.drivers.aiohttp import Driver
from kaiheila.v11 import Adapter as khlbot
from nonebot.adapters.onebot import V11Adapter as onebot

nonebot.init()
driver: Driver = nonebot.get_driver()
config = driver.config
config.onebot_ws_urls = {"ws://127.0.0.1:6700/"}
driver.register_adapter(khlbot)
# driver.register_adapter(onebot)

# nonebot.load_builtin_plugins()


from kaiheila.v11.event import Event, MessageEvent
from kaiheila.v11.bot import Bot, send

from nonebot.rule import to_me
from nonebot.adapters import Message, Event
from nonebot.params import CommandArg
from nonebot.plugin import on_command



test = on_command("test")
@test.handle()
async def test_escape(bot: Bot, event: Event, message: Message = CommandArg()):

    await bot.send(event, message)

test2 = on_command("test2")
@test2.handle()
async def test_escape(bot: Bot, event: Event, message: Message = CommandArg()):

    await send(bot, event, message = 'test', reply_sender = True, is_temp_msg = True)

if __name__ == "__main__":
    nonebot.run()

