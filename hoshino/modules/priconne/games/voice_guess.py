# Partially refer to the code of priconne games in HoshinoBot by @Ice-Cirno
# Under GPL-3.0 License

import aiohttp
import requests
from bs4 import BeautifulSoup
import sqlite3, os, random, asyncio

import hoshino
from hoshino import Service
from hoshino.modules.priconne import chara
from hoshino.typing import MessageSegment, CQEvent
from . import GameMaster
from hoshino.modules.priconne import daylimiter
from hoshino.modules.priconne.pcr_duel.counter.ScoreCounter import ScoreCounter2


sv = Service('voiceguess', bundle='pcr娱乐', help_='''
[cygames] 猜猜随机的"cygames"语音来自哪位角色
[猜ub] 猜猜这个ub语音来自哪位角色?
'''.strip())

DOWNLOAD_THRESHOLD = 76
MULTIPLE_VOICE_ESTERTION_ID_LIST = ['0044']
ONE_TURN_TIME = 20
HOSHINO_RES_PATH = os.path.expanduser(hoshino.config.RES_DIR)
DIR_PATH = os.path.join(HOSHINO_RES_PATH, 'voice_ci')
ADIR_PATH = os.path.join(HOSHINO_RES_PATH, 'ub_voice')
DB_PATH = os.path.expanduser("~/.hoshino/pcr_voice_guess.db")
SCORE_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
WINNER_SCORE = 200 #答对获得金币
WINNER_SW = 50 #答对获得声望数量
WINNER_HEART = 1 #答对获得心碎数量，如果没有缝合专武系统请改为0

db = daylimiter.RecordDAO(DB_PATH)
MAX_GUESS_NUM = daylimiter.VOICE_GUESS_MAX_NUM#每日最多获得金币次数
INIT_TIME = daylimiter.INIT_TIME #每日重置时间
daily_desc_limiter = daylimiter.DailyAmountLimiter("voiceguess", MAX_GUESS_NUM, INIT_TIME, db)

gm = GameMaster(DB_PATH)

async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
    return d

def uid2card(uid, user_card_dict):
    return str(uid) if uid not in user_card_dict.keys() else user_card_dict[uid]

def get_estertion_id_list():
    url = 'https://redive.estertion.win/sound/vo_ci/'
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    l = []
    for a in soup.find_all('a'):
        s = a['href'][:-1]
        if s.isdigit():
            l.append(s)
    return l

def get_estertion_aid_list():
    url = 'https://redive.estertion.win/sound/unit_battle_voice/'
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    l = []
    for a in soup.find_all('a'):
        s = a['href'][:-1]
        if s.isdigit():
            l.append(s)
    return l

def estertion_id2chara_id(estertion_id):
    return (estertion_id + 1000)


async def download(url, path):
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                content = await resp.read()
                with open(path, 'wb') as f:
                    f.write(content)
        return True
    except:
        return False


async def download_voice_ci(bot, ev: CQEvent, logger):
    if not os.path.exists(DIR_PATH):
        os.makedirs(DIR_PATH)
    file_name_list = os.listdir(DIR_PATH)
    file_name_list_no_suffix = [file.rsplit('.', 1)[0] for file in file_name_list]
    if len(file_name_list) < DOWNLOAD_THRESHOLD:
        count = 0
        await bot.send(ev, '正在下载"cygames"语音资源，请耐心等待')
        estertion_id_list = get_estertion_id_list()
        for eid in estertion_id_list:
            file_number_list = ['001'] if eid not in MULTIPLE_VOICE_ESTERTION_ID_LIST else ['001', '002']
            for file_number in file_number_list:
                url = f'https://redive.estertion.win/sound/vo_ci/{eid}/vo_ci_1{eid[1:]}01_{file_number}.m4a'
                file_name = url.split('/')[-1]
                if file_name.rsplit('.', 1)[0] not in file_name_list_no_suffix:
                    file_path = os.path.join(DIR_PATH, file_name)
                    logger.info(f'准备下载{file_name}...')
                    if not await download(url, file_path):
                        logger.info(f'下载{file_name}失败, 准备删除文件.')
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        logger.info(f'删除文件{file_name}成功.')
                    else:
                        logger.info(f'下载{file_name}成功!')
                        count = count + 1
        await bot.send(ev, f'下载完毕，此次下载"cygames"语音包{count}个，目前共{len(os.listdir(DIR_PATH))}个. 如果您使用的是go-cqhttp，请更新到v0.9.28或更高的版本并自行配置ffmpeg，否则无法发送m4a格式的语音.')

async def download_ub_voice(bot, ev: CQEvent, logger):
    if not os.path.exists(ADIR_PATH):
        os.makedirs(ADIR_PATH)
    file_name_list = os.listdir(ADIR_PATH)
    file_name_list_no_suffix = [file.rsplit('.', 1)[0] for file in file_name_list]
    if len(file_name_list) < DOWNLOAD_THRESHOLD:
        count = 0
        await bot.send(ev, '正在下载角色UB语音资源，请耐心等待')
        estertion_id_list = get_estertion_aid_list()
        for eid in estertion_id_list:
            file_number_list = ['100','200','300']
            for file_number in file_number_list:
                url = f'https://redive.estertion.win/sound/unit_battle_voice/{eid}/vo_btl_{eid}_ub_{file_number}.m4a'
                file_name = url.split('/')[-1]
                if file_name.rsplit('.', 1)[0] not in file_name_list_no_suffix:
                    file_path = os.path.join(ADIR_PATH, file_name)
                    logger.info(f'准备下载{file_name}...')
                    if not await download(url, file_path):
                        logger.info(f'下载{file_name}失败, 准备删除文件.')
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        logger.info(f'删除文件{file_name}成功.')
                    else:
                        logger.info(f'下载{file_name}成功!')
                        count = count + 1
        await bot.send(ev, f'下载完毕，此次下载ub语音包{count}个，目前共{len(os.listdir(ADIR_PATH))}个. 如果您使用的是go-cqhttp，请更新到v0.9.28或更高的版本并自行配置ffmpeg，否则无法发送m4a格式的语音.')

@sv.on_fullmatch(("猜ub排行", "猜ub排行榜", "猜ub群排行"))
async def description_guess_group_ranking(bot, ev: CQEvent):
    ranking = gm.db.get_ranking(ev.group_id)
    msg = ["【猜ub小游戏排行榜】"]
    for i, item in enumerate(ranking):
        uid, count = item
        m = await bot.get_group_member_info(self_id=ev.self_id, group_id=ev.group_id, user_id=uid)
        name = m["card"] or m["nickname"] or str(uid)
        msg.append(f"第{i + 1}名: {name}, 猜对{count}次")
    await bot.send(ev, "\n".join(msg))


@sv.on_prefix('cygames')
async def cygames_voice_guess(bot, ev: CQEvent):
    if gm.is_playing(ev.group_id):
        await bot.finish(ev, "【cygames】游戏仍在进行中…")
    with gm.start_game(ev.group_id) as game:
        await download_voice_ci(bot, ev, sv.logger)
        file_list = os.listdir(DIR_PATH)
        chosen_file = random.choice(file_list)
        file_path = os.path.join(DIR_PATH, chosen_file)
        await bot.send(ev, f'【cygames】猜猜这个“cygames”语音来自哪位角色? ({ONE_TURN_TIME}s后公布答案)')
        await bot.send(ev, MessageSegment.record(f'file:///{os.path.abspath(file_path)}'))
        estertion_id = chosen_file[7:10]
        chara_id = estertion_id2chara_id(int(estertion_id))
        game.answer = chara_id
        await asyncio.sleep(ONE_TURN_TIME)
        # 结算
        if game.winner:
            return
        c = chara.fromid(game.answer)
    await bot.send(ev, f"【cygames】正确答案是: {c.name} {c.icon.cqcode}\n很遗憾，没有人答对~")

@sv.on_prefix('猜ub')
async def voice_guess(bot, ev: CQEvent):
    if gm.is_playing(ev.group_id):
        await bot.finish(ev, "【猜ub】游戏仍在进行中…")
    with gm.start_game(ev.group_id) as game:
        file_list = os.listdir(ADIR_PATH)
        chosen_file = random.choice(file_list)
        file_path = os.path.join(ADIR_PATH, chosen_file)
        await bot.send(ev, f'【猜ub】猜猜这个ub语音来自哪位角色? ({ONE_TURN_TIME}s后公布答案)')
        await bot.send(ev, MessageSegment.record(f'file:///{os.path.abspath(file_path)}'))
        estertion_id = chosen_file[7:11]
        chara_id = int(estertion_id)
        game.answer = chara_id
        await asyncio.sleep(ONE_TURN_TIME)
        # 结算
        if game.winner:
            return
        c = chara.fromid(game.answer)
    await bot.send(ev, f"【猜ub】正确答案是: {c.name} {c.icon.cqcode}\n很遗憾，没有人答对~")


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
        msg = f"【猜ub】正确答案是：{c.name}{c.icon.cqcode}\n{MessageSegment.at(ev.user_id)}猜对了，真厉害！TA已经猜对{n}次了~\n(此轮游戏将在几秒后自动结束，请耐心等待)"
        guid = gid, uid
        if daily_desc_limiter.check(guid):
            score_counter = ScoreCounter2()
            daily_desc_limiter.increase(guid)
            dailynum = daily_desc_limiter.get_num(guid)
            score_counter._add_score(gid, uid, WINNER_SCORE)
            score_counter._add_prestige(gid, uid, WINNER_SW)
            randomHeart = random.randint(0, WINNER_HEART)
            heartMsg = ''
            if randomHeart > 0:
                score_counter._add_pcrheart(gid, uid, randomHeart)
                heartMsg = f'，并幸运地捡到了{randomHeart}个心碎'
            msg += f'\n{user_card}获得了{WINNER_SCORE}金币及{WINNER_SW}声望哦{heartMsg}。(今天第{dailynum}/{MAX_GUESS_NUM}次)'

        await bot.send(ev, msg)
