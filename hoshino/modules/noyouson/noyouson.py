import os
import random

from nonebot.exceptions import CQHttpError

from hoshino import R, Service, priv
from hoshino.util import FreqLimiter, DailyNumberLimiter

sv = Service('noyouson', manage_priv=priv.SUPERUSER,
             enable_on_default=True, visible=True)

WORD_LIST = ['日', '鸡', '撒', '木', '仄', '几', '大', '擦', 'rua', 'fucking']


@sv.on_rex(r'随机木仄几')
async def noyouson(bot, ev):

    list = WORD_LIST[0:random.randint(3, 11)]
    random.shuffle(list)

    await bot.send(ev, ''.join(list))
