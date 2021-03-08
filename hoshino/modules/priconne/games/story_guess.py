import asyncio
import os
import random
import hoshino
from hoshino import Service, util, R
from hoshino.modules.priconne import _pcr_data, chara
from hoshino.typing import CQEvent
from hoshino.typing import MessageSegment as Seg
from hoshino.util import DailyNumberLimiter
from . import GameMaster
import math, sqlite3, os, random, asyncio
from hoshino.modules.priconne import daylimiter
from hoshino.modules.priconne.pcr_duel.counter.ScoreCounter import ScoreCounter2

STORY_PATH = os.path.join(os.path.expanduser(hoshino.config.RES_DIR), 'img', 'priconne', 'story')
COUNT_PATH = os.path.expanduser("~/.hoshino/pcr_storyguess.db")
SCORE_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
db = daylimiter.RecordDAO(COUNT_PATH)
WINNER_SCORE = 500 #胜利者金币奖励
WINNER_SW = 100 #胜利者声望奖励
WINNER_HEART = 2 #胜利者心碎奖励
MAX_GUESS_NUM = daylimiter.STORY_GUESS_MAX_NUM  # 每日最多获得金币次数
INIT_TIME = daylimiter.INIT_TIME  # 每日重置时间
daily_avatar_limiter = daylimiter.DailyAmountLimiter("storyguess", MAX_GUESS_NUM, INIT_TIME, db)
PATCH_SIZE = 150
ONE_TURN_TIME = 20
DB_PATH = os.path.expanduser("~/.hoshino/pcr_story_guess.db")
BLACKLIST_ID = [1000, 1072, 1908, 4031, 9000]

gm = GameMaster(DB_PATH)
sv = Service(
    "pcr-story-guess",
    bundle="pcr娱乐",
    help_="""
[猜剧情] 猜猜bot随机发送的剧情图片是哪位角色的
[猜剧情排行] 显示小游戏的群排行榜(只显示前十)
""".strip(),
)


async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card'] != '' else m['nickname']
    return d


def uid2card(uid, user_card_dict):
    return str(uid) if uid not in user_card_dict.keys() else user_card_dict[uid]


@sv.on_fullmatch(("猜剧情排行", "猜剧情排名", "猜剧情排行榜", "猜剧情群排行"))
async def description_guess_group_ranking(bot, ev: CQEvent):
    ranking = gm.db.get_ranking(ev.group_id)
    msg = ["【猜剧情小游戏排行榜】"]
    for i, item in enumerate(ranking):
        uid, count = item
        m = await bot.get_group_member_info(
            self_id=ev.self_id, group_id=ev.group_id, user_id=uid
        )
        name = m["card"] or m["nickname"] or str(uid)
        msg.append(f"第{i + 1}名：{name} 猜对{count}次")
    await bot.send(ev, "\n".join(msg))


@sv.on_fullmatch(("猜剧情","看剧情猜人物"))
async def avatar_guess(bot, ev: CQEvent):
    if gm.is_playing(ev.group_id):
        await bot.finish(ev, "【猜剧情】游戏仍在进行中…")
    with gm.start_game(ev.group_id) as game:
        files = os.listdir(STORY_PATH)
        filename = random.choice(files)
        roleimg = R.img('priconne/story', filename)
        id = filename[0:4]
        game.answer = int(id)
        c = chara.fromid(game.answer)
        await bot.send(ev, f"【猜剧情】猜猜这个剧情图片中是哪位角色?({ONE_TURN_TIME}s后公布答案) {roleimg.cqcode}")
        await asyncio.sleep(ONE_TURN_TIME)
        if game.winner:
            return
    await bot.send(ev, f"【猜剧情】正确答案是：{c.name}{c.icon.cqcode}\n很遗憾，没有人答对~")


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
        msg = f"【猜剧情】正确答案是：{c.name}{c.icon.cqcode}\n{Seg.at(ev.user_id)}猜对了，真厉害！TA已经猜对{n}次了~\n(此轮游戏将在几秒后自动结束，请耐心等待)"
        guid = gid, uid
        if daily_avatar_limiter.check(guid):
            score_counter = ScoreCounter2()
            daily_avatar_limiter.increase(guid)
            dailynum = daily_avatar_limiter.get_num(guid)
            score_counter._add_score(gid, uid, WINNER_SCORE)
            score_counter._add_prestige(gid, uid, WINNER_SW)
            randomHeart = random.randint(0, WINNER_HEART)
            heartMsg = ''
            if randomHeart > 0:
                score_counter._add_pcrheart(gid, uid, randomHeart)
                heartMsg = f'，并幸运地捡到了{randomHeart}个心碎'
            msg += f'\n{user_card}获得了{WINNER_SCORE}金币及{WINNER_SW}声望哦{heartMsg}。(今天第{dailynum}/{MAX_GUESS_NUM}次)'

        await bot.send(ev, msg)