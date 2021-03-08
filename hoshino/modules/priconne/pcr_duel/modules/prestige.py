from .. import sv
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *
from ..pcr_duel import DuelJudger
from ..pcr_duel import DailyAmountLimiter
from ..config.duelconfig import *

duel_judger = DuelJudger()

@sv.on_fullmatch(['声望系统帮助','声望帮助'])
async def gift_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             声望系统帮助
1. 开启声望系统  (伯爵以上功能)
2. 查询声望
3. 加冕称帝 (国王称帝)
4. 飞升成神/成神飞升 (皇帝成神)
5. 皇室婚礼 +角色名 (娶正妻)
6. 贵族婚礼 +角色名 (娶二房)
7. 离婚 +角色名 (不走法律途径就要付出血的代价)
8. 声望招募
9. 用xx声望兑换金币 (汇率:1声望=50金币)
10. 兑换xx声望 (汇率:100金币=1声望)
注:
声望可以从决斗、每日签到、免费招募以及小游戏中获得。
小游戏指令：查看小游戏
╚                                        ╝
 '''
    await bot.send(ev, msg)

# 国王以上声望部分。
@sv.on_fullmatch('开启声望系统')
async def open_prestige(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid, uid)
    if prestige != None:
        await bot.finish(ev, '您已经开启了声望系统哦。', at_sender=True)
    score_counter._set_prestige(gid, uid, 0)
    msg = '成功开启声望系统！殿下，向着成为皇帝的目标进发吧。'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('查询声望')
async def inquire_prestige(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid, uid)
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)
    msg = f'您的声望为{prestige}点。'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['加冕称帝', '加冕仪式'])
async def be_emperor(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid, uid)

    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)
    if level != 9:
        await bot.finish(ev, '只有国王才能进行加冕仪式哦。', at_sender=True)
    if prestige < DJ_NEED_SW:
        await bot.finish(ev, f'加冕仪式需要{DJ_NEED_SW}声望，您的声望不足哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < DJ_NEED_GOLD:
        await bot.finish(ev, f'加冕仪式需要{DJ_NEED_GOLD}金币，您的金币不足哦。', at_sender=True)
    score_counter._reduce_score(gid, uid, DJ_NEED_GOLD)
    score_counter._reduce_prestige(gid, uid, DJ_NEED_SW)
    duel._set_level(gid, uid, 10)
    msg = f'\n礼炮鸣响，教皇领唱“感恩赞美歌”。“皇帝万岁！”\n在民众的欢呼声中，你加冕为了皇帝。\n花费了{DJ_NEED_SW}点声望，{DJ_NEED_GOLD}金币。'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['飞升成神', '成神飞升'])
async def be_feisheng(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid, uid)

    if level != 10:
        await bot.finish(ev, '只有皇帝才能飞升哦。', at_sender=True)
    if prestige < FS_NEED_SW:
        await bot.finish(ev, f'飞升成神需要{FS_NEED_SW}声望，您的声望不足哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < FS_NEED_GOLD:
        await bot.finish(ev, f'飞升成神需要{FS_NEED_GOLD}金币，您的金币不足哦。', at_sender=True)
    score_counter._reduce_score(gid, uid, FS_NEED_GOLD)
    score_counter._reduce_prestige(gid, uid, FS_NEED_SW)
    duel._set_level(gid, uid, 20)
    msg = f'\n光柱冲天，你感觉无尽的力量涌入了自己的体内。\n在民众的惊讶的目光中，你飞升成神了。\n花费了{FS_NEED_SW}点声望，{FS_NEED_GOLD}金币。'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix('皇室婚礼')
async def marry_queen(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid, uid)
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)
    if level <= 7:
        await bot.finish(ev, '只有8级(公爵)及以上才可以举办皇室婚礼哦。', at_sender=True)
    if duel._search_queen(gid, uid) != 0 and duel._search_queen2(gid, uid) != 0:
        await bot.finish(ev, '您的妻子数已达上限!', at_sender=True)
    if duel._search_queen(gid, uid) != 0:
        await bot.finish(ev, '您已经有一名妻子了，达到神以后，您可以举办贵族婚礼再娶一名妻子！', at_sender=True)
    if not args:
        await bot.finish(ev, '请输入皇室婚礼+角色名。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的角色名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)
    queen2 = duel._search_queen2(gid, uid)
    if cid == queen2:
        await bot.finish(ev, '该角色已经是您的妻子了！', at_sender=True)
    if prestige < marry_NEED_SW:
        await bot.finish(ev, f'您的声望不足，不能结婚哦（结婚需要{marry_NEED_SW}声望）。', at_sender=True)
    if prestige < 0:
        await bot.finish(ev, f'您现在身败名裂，不能结婚哦（结婚需要{marry_NEED_SW}声望）。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < marry_NEED_Gold:
        await bot.finish(ev, f'皇室婚礼需要{marry_NEED_Gold}金币，您的金币不足哦。', at_sender=True)
    favor = duel._get_favor(gid, uid, cid)
    if favor < NEED_favor:
        await bot.finish(ev, f'举办婚礼的女友需要达到{NEED_favor}好感，您的好感不足哦。', at_sender=True)
    score_counter._reduce_score(gid, uid, marry_NEED_Gold)
    score_counter._reduce_prestige(gid, uid, marry_NEED_SW)
    duel._set_queen_owner(gid, cid, uid)
    nvmes = get_nv_icon(cid)
    c = duel_chara.fromid(cid)
    msg = f'繁杂的皇室礼仪过后\n\n{c.name}与[CQ:at,qq={uid}]\n\n正式踏上了婚礼的殿堂\n成为了他的妻子。\n让我们为他们表示祝贺！\n妻子不会因决斗被抢走了哦。\n{nvmes}'
    await bot.send(ev, msg)

@sv.on_prefix('贵族婚礼')
async def marry_queen2(bot, ev: CQEvent):
    if Allow_wife2 == False:
        await bot.finish(ev, '管理员不允许第二名妻子喔。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid, uid)
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)
    if duel._search_queen(gid, uid) == 0:
        await bot.finish(ev, '您还没有正妻，您需要先举办皇室婚礼喔！', at_sender=True)
    if level <= 10:
        await bot.finish(ev, '只有成神后及以上才可以举办贵族婚礼哦。', at_sender=True)
    if duel._search_queen(gid, uid) != 0 and duel._search_queen2(gid, uid) != 0:
        await bot.finish(ev, '您的妻子数已达上限!', at_sender=True)
    if not args:
        await bot.finish(ev, '请输入贵族婚礼+角色名。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的角色名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)
    queen = duel._search_queen(gid, uid)
    if cid == queen:
        await bot.finish(ev, '该角色已经是您的妻子了！', at_sender=True)
    if prestige < marry2_NEED_SW:
        await bot.finish(ev, f'您的声望不足，不能结婚哦（结婚需要{marry2_NEED_SW}声望）。', at_sender=True)
    if prestige < 0:
        await bot.finish(ev, f'您现在身败名裂，不能结婚哦（结婚需要{marry2_NEED_SW}声望）。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < marry2_NEED_Gold:
        await bot.finish(ev, f'皇室婚礼需要{marry2_NEED_Gold}金币，您的金币不足哦。', at_sender=True)
    favor = duel._get_favor(gid, uid, cid)
    if favor < NEED2_favor:
        await bot.finish(ev, f'举办婚礼的女友需要达到{NEED2_favor}好感，您的好感不足哦。', at_sender=True)
    score_counter._reduce_score(gid, uid, marry2_NEED_Gold)
    score_counter._reduce_prestige(gid, uid, marry2_NEED_SW)
    duel._set_queen2_owner(gid, cid, uid)
    nvmes = get_nv_icon(cid)
    c = duel_chara.fromid(cid)
    msg = f'简约的贵族礼仪过后\n\n{c.name}与[CQ:at,qq={uid}]\n\n正式踏上了婚礼的殿堂\n成为了他的第二名妻子。\n让我们为他们表示祝贺！\n妻子不会因决斗被抢走了哦。\n{nvmes}'
    await bot.send(ev, msg)

@sv.on_prefix('离婚')
async def lihun_queen(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    args = ev.message.extract_plain_text().split()
    if duel._search_queen(gid,uid) ==0:
        await bot.finish(ev, '您没有妻子！。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if not args:
        await bot.finish(ev, '请输入离婚+角色名。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的角色名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)
    queen = duel._search_queen(gid,uid)
    queen2 = duel._search_queen2(gid,uid)
    if cid != queen and cid != queen2:
       await bot.finish(ev, '该角色并不是你的妻子哦。', at_sender=True)
    if prestige < 3000:
        await bot.finish(ev, '离婚需要3000声望，您的声望现在离婚可能身败名裂哦。', at_sender=True)
    if score < 20000:
        await bot.finish(ev, '离婚需要20000金币，您的金币不足哦。', at_sender=True)
    score_counter._reduce_score(gid,uid,20000)
    score_counter._reduce_prestige(gid,uid,3000)
    duel._delete_card(gid, uid, cid)
    c = duel_chara.fromid(queen)
    nvmes = get_nv_icon(queen)
    msg = f'花费了20000金币，[CQ:at,qq={uid}]总算将他的妻子{c.name}赶出家门\n，引起了众人的不满，损失3000声望。{nvmes}'
    await bot.send(ev, msg)
    duel._delete_queen_owner(gid,cid)
    duel._delete_queen2_owner(gid,cid)

@sv.on_fullmatch('声望招募')
async def add_girl(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_SW_CELE(gid) != 1 and duel._get_level(gid, uid) != 20:
        msg = '目前不在限时开放声望招募期间，只有神能参与！'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg, at_sender=True)
        return
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再参加舞会吧。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        # 防止女友数超过上限
        level = duel._get_level(gid, uid)
        noblename = get_noblename(level)
        girlnum = get_girlnum_buy(gid, uid)
        cidlist = duel._get_cards(gid, uid)
        cidnum = len(cidlist)
        score = score_counter._get_score(gid, uid)
        needSW2 = SW_COST
        prestige = score_counter._get_prestige(gid, uid)
        if prestige == None:
            score_counter._set_prestige(gid, uid, 0)
        if prestige < needSW2:
            msg = f'您的声望不足{needSW2}哦。'
            await bot.send(ev, msg, at_sender=True)
            return

        newgirllist = get_newgirl_list(gid)
        # 判断女友是否被抢没和该用户是否已经没有女友
        if len(newgirllist) == 0:
            if cidnum != 0:
                await bot.send(ev, '这个群已经没有可以约到的新女友了哦。', at_sender=True)
                return
            else:
                score_counter._reduce_prestige(gid, uid, needSW2)
                cid = 9999
                c = duel_chara.fromid(1059)
                duel._add_card(gid, uid, cid)
                msg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
                await bot.send(ev, msg, at_sender=True)
                return

        score_counter._reduce_prestige(gid, uid, needSW2)
        # 招募女友成功
        cid = random.choice(newgirllist)
        c = duel_chara.fromid(cid)
        nvmes = get_nv_icon(cid)
        duel._add_card(gid, uid, cid)
        wintext = random.choice(Addgirlsuccess)

        msg = f'\n{wintext}\n招募女友成功！\n您花费了{needSW2}声望\n新招募的女友为：{c.name}{nvmes}'
        await bot.send(ev, msg, at_sender=True)

@sv.on_rex(f'^为(.*)充值(\d+)声望$')
async def cheat_SW(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '不要想着走捷径哦。', at_sender=True)
    gid = ev.group_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid, id)
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '该用户尚未开启声望系统哦！。', at_sender=True)
    score_counter._add_prestige(gid, id, num)
    msg = f'已为[CQ:at,qq={id}]充值{num}声望。'
    await bot.send(ev, msg)


@sv.on_rex(f'^扣除(.*)的(\d+)声望$')
async def cheat_SW2(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '不要想着走捷径哦。', at_sender=True)
    gid = ev.group_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid, id)
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '该用户尚未开启声望系统哦！。', at_sender=True)
    score_counter._reduce_prestige(gid, id, num)
    msg = f'已扣除[CQ:at,qq={id}]的{num}声望。'
    await bot.send(ev, msg)

@sv.on_rex(f'^用(\d+)声望兑换金币$')
async def cheat_score(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    num = int(match.group(1))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还没有在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '您未开启声望系统哦！。', at_sender=True)
    if num < 200:
        await bot.finish(ev, '200声望起兑换哦！。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    pay_score=num
    num2 = num * SW2JB_RATE
    if prestige < pay_score:
        msg = f'您的声望只有{score}，无法兑换哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        score_counter._reduce_prestige(gid, uid, pay_score)
        score_counter._add_score(gid,uid,num2)
        scoreyou = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        msg = f'使用{num}声望兑换{num2}金币成功\n您的声望剩余{prestige}，金币为{scoreyou}。'
        await bot.send(ev, msg, at_sender=True)

@sv.on_rex(f'^兑换(\d+)声望$')
async def cheat_score(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    num = int(match.group(1))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还没有在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '您未开启声望系统哦！。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    pay_score=num*JB2SW_RATE
    if score < pay_score:
        msg = f'兑换{num}声望需要{pay_score}金币，您的金币只有{score}，无法兑换哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        score_counter._reduce_score(gid, uid, pay_score)
        score_counter._add_prestige(gid,uid,num)
        scoreyou = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        msg = f'兑换{num}声望成功，扣除{pay_score}金币\n您的声望为{prestige}，金币剩余{scoreyou}。'
        await bot.send(ev, msg, at_sender=True)