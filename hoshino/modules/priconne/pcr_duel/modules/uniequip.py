from .. import sv
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *
from ..pcr_duel import DuelJudger
from ..pcr_duel import DailyAmountLimiter
from ..config.duelconfig import *
from hoshino.modules.priconne.wiki import data as wikidata

duel_judger = DuelJudger()

@sv.on_fullmatch(['专武系统帮助','专武帮助'])
async def gift_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             专武系统帮助
1. 回收女友 +角色名 (回收女友，随机获得1~5个公主之心碎片)
2. 购买专武 +角色名 (耗费30个公主之心碎片为角色购买专武)
3. 升级专武 +角色名 (耗费公主之心碎片及金币为角色升级专武)
4. 我的公主之心 (查看公主之心数量)
注:
每位女友仅能装备一件专武，挑战boss有几率获得公主之心碎片哦。
╚                                        ╝
 '''
    await bot.send(ev, msg)

daily_recycle_limiter = DailyAmountLimiter("date", RECYCLE_DAILY_LIMIT, RESET_HOUR)

@sv.on_prefix(['回收女友', '解放女友'])
async def recycle_girl(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    guid = gid, uid
    level = duel._get_level(gid, uid)
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来回收女友吧。'
        await bot.finish(ev, msg, at_sender=True)
    if level == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    if len(args) != 1:
        await bot.finish(ev, '请输入 回收女友+女友名 中间用空格隔开。', at_sender=True)
    if not daily_recycle_limiter.check(guid):
        await bot.finish(ev, f'今天回收的女友数已经超过{RECYCLE_DAILY_LIMIT}次了哦，明天再来吧。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的pcr角色名。', at_sender=True)
    score_counter = ScoreCounter2()
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)
    # 检测是否是妻子
    c = duel_chara.fromid(cid)
    queen = duel._search_queen(gid, uid)
    if cid == queen:
        await bot.finish(ev, '不可以回收您的妻子哦。', at_sender=True)
    # 检测是否是二房
    queen2 = duel._search_queen2(gid, uid)
    if cid == queen2:
        await bot.finish(ev, '不可以回收您的二妻哦。', at_sender=True)
    if duel._get_favor(gid, uid, cid) == None:
        duel._set_favor(gid, uid, cid, 0)
    favor = duel._get_favor(gid, uid, cid)
    if favor > 30:
        await bot.finish(ev, f'{c.name}与您的好感为{favor}，超过30就不能回收哦。', at_sender=True)
    heart = random.randint(1,5)
    duel._delete_card(gid, uid, cid)
    score_counter._add_pcrheart(gid,uid,heart)
    myheart = score_counter._get_pcrheart(gid,uid)
    daily_recycle_limiter.increase(guid)
    msg = f'\n“人生有梦，各自精彩。”\n你回收了{c.name}，她现在处于单身状态了。\n本次回收获得了公主之心碎片×{heart}。\n您现在的公主之心碎片数量为：{myheart}，集齐30个就可以为您的女友购买一把专武哦。\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['购买专武','赠送专武'])
async def buy_uniquie(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 购买专武+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    uniquie = wikidata.get_uniquei_name(cid)
    if not uniquie:
        await bot.finish(ev, '该角色目前没有开放专武，无法购买哦。', at_sender=True)
    score_counter = ScoreCounter2()
    myheart = score_counter._get_pcrheart(gid,uid)
    if myheart < 30:
        await bot.finish(ev, '您的公主之心碎片不足30哦，无法购买专武。', at_sender=True)
    is_equip = duel._get_uniequip(gid,uid,cid)
    if is_equip>0:
        await bot.finish(ev, '该女友已经装备了专武，无法重复购买。', at_sender=True)
    score_counter._reduce_pcrheart(gid,uid,30)
    duel._add_favor(gid,uid,cid,50)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    duel._add_uniequip(gid,uid,cid)
    c = duel_chara.fromid(cid)
    nvmes = get_nv_icon(cid)
    msg = f'\n您花费了30个公主之心碎片为{c.name}购买了:{uniquie}\n你和{c.name}的好感上升了50点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{nvmes}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['升级专武','专武升级'])
async def up_uniquie(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 升级专武+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    equip = duel._get_uniequip(gid,uid,cid)
    if equip==0:
        await bot.finish(ev, '该角色未装备专武，无法升级哦。', at_sender=True)
    if equip==MAX_UNIEQUIP_LEVEL:
        await bot.finish(ev, '该专武已升至满级，无法继续升级啦。', at_sender=True)
    heart_score = LEVEL_EQUIP_NEED[int(equip)]
    score_counter = ScoreCounter2()
    myheart = score_counter._get_pcrheart(gid,uid)
    new_equip = int(equip) + 1
    uniquie = wikidata.get_uniquei_name(cid)
    c = duel_chara.fromid(cid)
    if myheart < heart_score[0]:
        await bot.finish(ev, f'升级专武所需公主之心碎片不足！\n由{equip}级升至{new_equip}级需要：{heart_score[0]}个，您当前剩余：{myheart}个', at_sender=True)
    myscore = score_counter._get_score(gid,uid)
    if myscore < heart_score[1]:
        await bot.finish(ev, f'升级专武所需金币不足！\n由{equip}级升至{new_equip}级需要：{heart_score[1]}个，您当前剩余：{myscore}个',at_sender=True)
    score_counter._reduce_pcrheart(gid, uid, heart_score[0])
    score_counter._reduce_score(gid, uid, heart_score[1])
    duel._up_uniequip(gid,uid,cid)
    msg = f'\n您花费了{heart_score[0]}个公主之心碎片和{heart_score[1]}金币为{c.name}升级了:{uniquie}\n当前专武等级为：{new_equip}/{MAX_UNIEQUIP_LEVEL}级，女友战斗力提升了100点！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['我的公主之心','公主之心数量'])
async def my_pcrheart(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    score_counter = ScoreCounter2()
    myheart = score_counter._get_pcrheart(gid,uid)
    msg = f'您的公主之心碎片数量为：{myheart}'
    await bot.send(ev, msg, at_sender=True)