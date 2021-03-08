from .. import sv
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *
from ..pcr_duel import DuelJudger
from ..pcr_duel import DailyAmountLimiter
from ..config.duelconfig import *

duel_judger = DuelJudger()

@sv.on_fullmatch('武器列表')
async def weapon(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    n = duel._get_weapon(gid)
    if n == 6:
        msg = '''目前本群启用的武器是俄罗斯左轮，弹匣量为6'''
    elif n == 2:
        msg = '''目前本群启用的武器是贝雷塔687，弹匣量为2'''
    elif n == 20:
        msg = '''目前本群启用的武器是Glock，弹匣量为20'''
    elif n == 12:
        msg = '''目前本群启用的武器是战术型沙漠之鹰，弹匣量为12'''
    elif n == 10:
        msg = '''目前本群启用的武器是巴雷特，弹匣量为10'''
    else:
        msg = f'目前本群启用的是自定义武器，弹匣量为{n}'
    msg += '''
    可用的武器有
    1.俄罗斯左轮 6发 
    2.贝雷塔687  2发
    3.格洛克   20发
    4.战术型沙漠之鹰 12发
    5.巴雷特 10发
也可发送自定义武器装弹X发来定制自己的武器'''
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex(r'^切换武器(俄罗斯左轮|贝雷塔687|格洛克|战术型沙漠之鹰|巴雷特)$')
async def weaponchange(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = (ev['match'])
    weapon = (match.group(1))
    duel = DuelCounter()
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权切换武器！', at_sender=True)
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，无法切换武器。'
        await bot.send(ev, msg, at_sender=True)
        return
    if weapon == '俄罗斯左轮':
        msg = '已启用武器俄罗斯左轮，弹匣量为6'
        duel._set_weapon(gid, 6)
    if weapon == '贝雷塔687':
        msg = '已启用武器贝雷塔687，弹匣量为2'
        duel._set_weapon(gid, 2)
    if weapon == '格洛克':
        msg = '已启用武器格洛克，弹匣量为20'
        duel._set_weapon(gid, 20)
    if weapon == '战术型沙漠之鹰':
        msg = '已启用武器战术型沙漠之鹰，弹匣量为12'
        duel._set_weapon(gid, 12)
    if weapon == '巴雷特':
        msg = '已启用武器巴雷特，弹匣量为10'
        duel._set_weapon(gid, 10)
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex(f'^自定义武器装弹(\d+)发$')
async def weaponchange2(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = (ev['match'])
    n = int(match.group(1))
    duel = DuelCounter()
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权切换武器！', at_sender=True)
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，无法切换武器。'
        await bot.send(ev, msg, at_sender=True)
        return
    duel._set_weapon(gid, n)
    msg = f'已启用自定义武器，弹匣量为{n}'
    await bot.send(ev, msg, at_sender=True)