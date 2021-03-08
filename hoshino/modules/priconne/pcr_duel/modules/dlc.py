# 礼物系统
from .. import sv
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *
from ..pcr_duel import DuelJudger
from ..pcr_duel import DailyAmountLimiter
from ..config.duelconfig import *

duel_judger = DuelJudger()
@sv.on_prefix(['加载dlc', '加载DLC', '开启dlc', '开启DLC'])
async def add_dlc(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能加载dlc哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args) >= 2:
        await bot.finish(ev, '指令格式错误。', at_sender=True)
    if len(args) == 0:
        await bot.finish(ev, '请输入加载dlc+dlc名。', at_sender=True)
    dlcname = args[0]
    if dlcname not in dlcdict.keys():
        await bot.finish(ev, 'DLC名填写错误。', at_sender=True)

    if gid in dlc_switch[dlcname]:
        await bot.finish(ev, '本群已开启此dlc哦。', at_sender=True)
    dlc_switch[dlcname].append(gid)
    save_dlc_switch()
    await bot.finish(ev, f'加载dlc {dlcname}  成功!', at_sender=True)

@sv.on_prefix(['卸载dlc', '卸载DLC', '关闭dlc', '关闭DLC'])
async def delete_dlc(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能卸载dlc哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args) >= 2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args) == 0:
        await bot.finish(ev, '请输入卸载dlc+dlc名。', at_sender=True)
    dlcname = args[0]
    if dlcname not in dlcdict.keys():
        await bot.finish(ev, 'DLC名填写错误', at_sender=True)

    if gid not in dlc_switch[dlcname]:
        await bot.finish(ev, '本群没有开启此dlc哦。', at_sender=True)
    dlc_switch[dlcname].remove(gid)
    save_dlc_switch()
    await bot.finish(ev, f'卸载dlc {dlcname}  成功!', at_sender=True)

@sv.on_fullmatch(['dlc列表', 'DLC列表', 'dlc介绍', 'DLC介绍'])
async def intro_dlc(bot, ev: CQEvent):
    msg = '可用DLC列表：\n\n'
    i = 1
    for dlc in dlcdict.keys():
        msg += f'{i}.{dlc}:\n'
        intro = dlcintro[dlc]
        msg += f'介绍:{intro}\n'
        num = len(dlcdict[dlc])
        msg += f'共有{num}名角色\n\n'
        i += 1
    msg += '发送 加载\卸载dlc+dlc名\n可加载\卸载dlc\n卸载的dlc不会被抽到，但是角色仍留在玩家仓库，可以被抢走。'

    await bot.finish(ev, msg)

@sv.on_fullmatch(['dlc帮助', 'DLC帮助', 'dlc指令', 'DLC指令'])
async def help_dlc(bot, ev: CQEvent):
    msg = '''
╔                                 ╗
         DLC帮助

  1.加载\卸载dlc+dlc名
  2.dlc列表(查看介绍)

  卸载的dlc不会被抽到
  但是角色仍留在仓库
  可以被他人抢走

╚                                 ╝    
'''
    await bot.finish(ev, msg)