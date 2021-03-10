# ref: https://github.com/GWYOG/GWYOG-Hoshino-plugins/blob/master/pcravatarguess
# Originally written by @GWYOG
# Reflacted by @Ice-Cirno
# GPL-3.0 Licensed
# Thanks to @GWYOG for his great contribution!

import asyncio
import os
import random

from hoshino import Service, util
from hoshino.modules.priconne import _pcr_data, chara
from hoshino.typing import CQEvent
from hoshino.typing import MessageSegment as Seg
from hoshino.util import DailyNumberLimiter
from . import GameMaster
import math, sqlite3, os, random, asyncio
from hoshino.modules.priconne import daylimiter
from hoshino.modules.priconne.pcr_duel.counter.ScoreCounter import ScoreCounter2

COUNT_PATH = os.path.expanduser("~/.hoshino/pcr_avatarguess.db")
SCORE_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
db = daylimiter.RecordDAO(COUNT_PATH)
WINNER_SCORE = 200 #答对获得金币
WINNER_SW = 50 #答对获得声望数量
WINNER_HEART = 1 #答对获得心碎数量，如果没有缝合专武系统请改为0
MAX_GUESS_NUM = daylimiter.AVATAR_GUESS_MAX_NUM#每日最多获得金币次数
INIT_TIME = daylimiter.INIT_TIME #每日重置时间
daily_avatar_limiter = daylimiter.DailyAmountLimiter("avatarguess", MAX_GUESS_NUM, INIT_TIME, db)
PATCH_SIZE = 32
ONE_TURN_TIME = 20
DB_PATH = os.path.expanduser("~/.hoshino/pcr_avatar_guess.db")
BLACKLIST_ID = [1000,1072, 1908, 4031, 9000]
blhxlist = range(6000,6506)
yozilist = range(1523,1544)
genshinlist = range(7001,7020)
bangdreamlist = range(1601,1636)
millist = range(3001,3055)
collelist = range(4001,4639)
koilist = range(7100,7104)
sakulist = range(7200,7204)
cloverlist = range(7300,7307)
majsoullist = range(7400,7476)
noranekolist = range(7500,7510)
fgolist = range(8001,8301)
BLACKLIST_ID += blhxlist
BLACKLIST_ID += yozilist
BLACKLIST_ID += genshinlist
BLACKLIST_ID += bangdreamlist
BLACKLIST_ID += millist
BLACKLIST_ID += collelist
BLACKLIST_ID += koilist
BLACKLIST_ID += sakulist
BLACKLIST_ID += cloverlist
BLACKLIST_ID += majsoullist
BLACKLIST_ID += noranekolist
BLACKLIST_ID += fgolist

gm = GameMaster(DB_PATH)
sv = Service(
    "pcr-avatar-guess",
    bundle="pcr娱乐",
    help_="""
[猜头像] 猜猜bot随机发送的头像的一小部分来自哪位角色
[猜头像排行] 显示小游戏的群排行榜(只显示前十)
""".strip(),
)

async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
    return d

def uid2card(uid, user_card_dict):
    return str(uid) if uid not in user_card_dict.keys() else user_card_dict[uid]



@sv.on_fullmatch(("猜头像排行", "猜头像排名", "猜头像排行榜", "猜头像群排行"))
async def description_guess_group_ranking(bot, ev: CQEvent):
    ranking = gm.db.get_ranking(ev.group_id)
    msg = ["【猜头像小游戏排行榜】"]
    for i, item in enumerate(ranking):
        uid, count = item
        m = await bot.get_group_member_info(
            self_id=ev.self_id, group_id=ev.group_id, user_id=uid
        )
        name = m["card"] or m["nickname"] or str(uid)
        msg.append(f"第{i + 1}名：{name} 猜对{count}次")
    await bot.send(ev, "\n".join(msg))


@sv.on_fullmatch("猜头像")
async def avatar_guess(bot, ev: CQEvent):
    if gm.is_playing(ev.group_id):
        await bot.finish(ev, "【猜头像】游戏仍在进行中…")
    with gm.start_game(ev.group_id) as game:
        ids = list(_pcr_data.CHARA_NAME.keys())
        game.answer = random.choice(ids)
        while chara.is_npc(game.answer):
            game.answer = random.choice(ids)
        c = chara.fromid(game.answer)
        #print(c.name)
        img = c.icon.open()
        w, h = img.size
        l = random.randint(0, w - PATCH_SIZE)
        u = random.randint(0, h - PATCH_SIZE)
        cropped = img.crop((l, u, l + PATCH_SIZE, u + PATCH_SIZE))
        cropped = Seg.image(util.pic2b64(cropped))
        await bot.send(ev, f"【猜头像】猜猜这个图片是哪位角色头像的一部分?({ONE_TURN_TIME}s后公布答案) {cropped}")
        await asyncio.sleep(ONE_TURN_TIME)
        if game.winner:
            return
    await bot.send(ev, f"【猜头像】正确答案是：{c.name} {c.icon.cqcode}\n很遗憾，没有人答对~")


@sv.on_message()
async def on_input_chara_name(bot, ev: CQEvent):
    game = gm.get_game(ev.group_id)
    gid = ev.group_id
    uid = ev.user_id    
    if not game or game.winner:
        return
    c = chara.fromname(ev.message.extract_plain_text())
    if c.id != chara.UNKNOWN and c.id == game.answer:
        game.winner = ev.user_id
        n = game.record()
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        user_card = uid2card(ev.user_id, user_card_dict)        
        msg = f"【猜头像】正确答案是：{c.name}{c.icon.cqcode}\n{Seg.at(ev.user_id)}猜对了，真厉害！TA已经猜对{n}次了~\n(此轮游戏将在几秒后自动结束，请耐心等待)"
        guid = gid,uid
        if  daily_avatar_limiter.check(guid):
            score_counter = ScoreCounter2()
            daily_avatar_limiter.increase(guid)
            dailynum = daily_avatar_limiter.get_num(guid)
            score_counter._add_score(gid, uid, WINNER_SCORE)
            score_counter._add_prestige(gid, uid, WINNER_SW)
            randomHeart = random.randint(0,WINNER_HEART)
            heartMsg = ''
            if randomHeart>0:
                score_counter._add_pcrheart(gid,uid,randomHeart)
                heartMsg = f'，并幸运地捡到了{randomHeart}个心碎'
            msg += f'\n{user_card}获得了{WINNER_SCORE}金币及{WINNER_SW}声望哦{heartMsg}。(今天第{dailynum}/{MAX_GUESS_NUM}次)'
          
        await bot.send(ev, msg)