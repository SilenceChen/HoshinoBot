from .. import sv
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *
from ..pcr_duel import DuelJudger
from ..pcr_duel import DailyAmountLimiter
from ..config.duelconfig import *

@sv.on_fullmatch(['商城系统帮助','商城帮助'])
async def gift_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             商城系统帮助
1. 以xx金币上架女友xx
2. 下架女友xx  
3. 购买女友xx
注:
当前商城货币为：金币，声望商城将在后期开放
╚                                        ╝
 '''
    await bot.send(ev, msg)

@sv.on_rex(f'^以(\d+)金币上架女友(.*)$')
async def store_shangjia(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    name = str(match.group(2))
    num = int(match.group(1))
    duel = DuelCounter()
    if not name:
        await bot.send(ev, '请输入查女友+pcr角色名。', at_sender=True)
        return
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    owner = duel._get_card_owner(gid, cid)
    c = duel_chara.fromid(cid)
    #判断是否是妻子。
    if duel._get_queen_owner(gid,cid) !=0 :
        await bot.finish(ev, f'\n{c.name}现在是\n[CQ:at,qq={owner}]的妻子，无法上架哦。', at_sender=True)
    # 判断是否是二妻。
    if duel._get_queen2_owner(gid, cid) != 0:
        await bot.finish(ev, f'\n{c.name}现在是\n[CQ:at,qq={owner}]的二妻，无法上架哦。', at_sender=True)
    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。', at_sender=True)
        return
    if uid!=owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您没有上架权限哦。'
        await bot.send(ev, msg)
        return
    if num < GACHA_COST:
        msg = f'上架金币不得少于{GACHA_COST}。'
        await bot.send(ev, msg)
        return
    duel._add_store(gid, uid, cid, num)
    nvmes = get_nv_icon(cid)
    msg = f'您以{num}金币的价格上架了女友{c.name}{nvmes}。'
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex(f'^下架女友(.*)$')
async def store_xiajia(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    name = str(match.group(1))
    duel = DuelCounter()
    if not name:
        await bot.send(ev, '请输入下架女友+pcr角色名。', at_sender=True)
        return
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    owner = duel._get_card_owner(gid, cid)
    c = duel_chara.fromid(cid)
    store_flag = duel._get_store(gid, owner, cid)
    if store_flag > 0:
        duel._delete_store(gid, uid, cid)
        nvmes = get_nv_icon(cid)
        msg = f'下架女友{c.name}成功！{nvmes}。'
        await bot.send(ev, msg, at_sender=True)
    else:
        await bot.send(ev, '该女友未在出售中。', at_sender=True)

@sv.on_rex(f'^购买女友(.*)$')
async def store_buy(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    name = str(match.group(1))
    duel = DuelCounter()
    if not name:
        await bot.send(ev, '请输入要购买的女友+pcr角色名。', at_sender=True)
        return
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    owner = duel._get_card_owner(gid, cid)
    c = duel_chara.fromid(cid)
    store_flag = duel._get_store(gid, owner, cid)
    if store_flag > 0:
        if( uid==owner ):
            await bot.send(ev, '不能购买自己上架的女友。', at_sender=True)
            return
        score_counter = ScoreCounter2()
        score = score_counter._get_score(gid, uid)
        if score < store_flag:
            msg = f'您的金币不足{store_flag}，无法购买哦。'
            await bot.send(ev, msg, at_sender=True)
            return
        duel._delete_store(gid, owner, cid)
        score_counter._add_score(gid, owner, store_flag)
        score_counter._reduce_score(gid, uid, store_flag)
        duel._delete_card(gid, owner, cid)
        duel._add_card(gid, uid, cid)
        nvmes = get_nv_icon(cid)
        msg = f'[CQ:at,qq={uid}]以{store_flag}金币的价格购买了[CQ:at,qq={owner}]的女友{c.name}。{nvmes}'
        await bot.send(ev, msg)
    else:
        await bot.send(ev, '该女友未在出售中，无法购买。', at_sender=True)
