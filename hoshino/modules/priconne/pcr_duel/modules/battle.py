from .. import sv
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *
from ..pcr_duel import DuelJudger
from ..pcr_duel import DailyAmountLimiter
from ..config.duelconfig import *
from hoshino.modules.priconne.wiki import data as wikidata

duel_judger = DuelJudger()

@sv.on_fullmatch(['战斗系统帮助','战斗帮助'])
async def gift_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             战斗系统帮助
1. 绑定女友 +角色名 (绑定xx女友作为决斗伴侣，会获取经验值升级)
2. 我的女友 +角色名 (查看女友战力等信息)
3. 查看绑定/查看战斗女友
4. boss列表 (查看boss数据)
5. 挑战[ABC][1-5] (用绑定女友挑战boss，每日三次)
6. rank等级表/rank表 (查看rank等级提升需求)
7. 升级rank/rank升级/提升rank +角色名 (升级女友的rank)
注:
提高女友战力可以更容易打败boss哦。
战力计算器：
    基础战力 = 100 + 等级*10 + 好感度*0.4 + 专武等级*100
    女友战力 = 基础战力*(1+rank/10)
    最大rank等级为10级，达到r10可以增幅2倍战力
╚                                        ╝
 '''
    await bot.send(ev, msg)

@sv.on_prefix(['绑定女友'])
async def card_bangdin(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    if not args:
        await bot.send(ev, '请输入绑定女友+pcr角色名。', at_sender=True)
        return
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    CE = CECounter()
    c = duel_chara.fromid(cid)
    nvmes = get_nv_icon(cid)
    owner = duel._get_card_owner(gid, cid)
    if uid!=owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法绑定哦。'
        await bot.send(ev, msg)
        return
    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        return
    if uid==owner:
        CE._add_guaji(gid,uid,cid)
        msg = f"女友{c.name}绑定成功\n之后决斗、挑战boss{c.name}可以获得经验值哦\n每位贵族只能绑定一位女友参与战斗哦~\n{nvmes}"
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['查看绑定','查看战斗女友'])
async def get_bangdin(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    duel = DuelCounter()
    cid = CE._get_guaji(gid,uid)
    if cid==0:
        msg = '您尚未绑定任何角色参与战斗。'
        await bot.finish(ev, msg)
    owner = duel._get_card_owner(gid, cid)
    c = duel_chara.fromid(cid)
    if uid!=owner:
        msg = f'您绑定了：{c.name}，但她已不在您身边，请重新绑定您的女友。'
        await bot.finish(ev, msg)
    nvmes = get_nv_icon(cid)
    msg = f"您当前绑定的女友是：{c.name}，每位贵族只能绑定一位女友参与战斗哦~\n{nvmes}"
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['我的女友','女友信息','查看女友信息'])
async def my_girl(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    if not args:
        await bot.send(ev, '请输入女友信息+pcr角色名。', at_sender=True)
        return
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    CE = CECounter()
    c = duel_chara.fromid(cid)
    nvmes = get_nv_icon(cid)
    owner = duel._get_card_owner(gid, cid)
    if uid!=owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法查看哦。'
        await bot.send(ev, msg)
        return
    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        return
    if uid==owner:
        queen_msg = ''
        if duel._get_queen_owner(gid, cid) != 0:
            queen_msg = f'现在是您的妻子\n'
        if duel._get_queen2_owner(gid, cid) != 0:
            queen_msg = f'现在是您的二妻\n'
        if duel._get_favor(gid, uid, cid) == None:
            duel._set_favor(gid, uid, cid, 0)
        favor = duel._get_favor(gid, uid, cid)
        relationship, text = get_relationship(favor)
        card_ce = get_card_ce(gid, uid, cid)
        level_info = CE._get_card_level(gid, uid, cid)
        is_equip = duel._get_uniequip(gid, uid, cid)
        rank = duel._get_rank(gid, uid, cid)
        eq_msg = ''
        if is_equip:
            uniquie = wikidata.get_uniquei_name(cid)
            eq_msg = f"\n装备了专武：" + uniquie + f'\n当前专武等级为：{is_equip}/{MAX_UNIEQUIP_LEVEL}级'
        msg = f'\n{c.name}目前的等级是{level_info}级，rank等级为：{rank}级，战斗力为{card_ce}点{eq_msg}\n{queen_msg}对你的好感是{favor}\n你们的关系是{relationship}\n“{text}”{nvmes}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['boss列表'])
async def boss_list(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    duel = DuelCounter()
    cid = CE._get_guaji(gid, uid)
    msg = '当前可挑战的boss列表（首次挑战不消耗次数）：\n'
    for stage in BOSS_LIST:
        bosses = BOSS_LIST[stage]
        msg += f'{stage}面：\n'
        num = 1
        while (num <= 5):
            boss_info = bosses[num]
            is_challenge = duel._get_bossbattle(gid,uid,cid,stage,num)
            if is_challenge>0:
                challenge_msg = ''
            else:
                challenge_msg = '(尚未挑战)'
            msg += f'"{stage}{num}": "{boss_info[0]}"，HP{boss_info[1]}，击杀奖励{boss_info[2]}心碎和{boss_info[3]}金币，{boss_info[4]}经验值。(推荐女友战力{boss_info[1]}以上){challenge_msg}\n'
            num = num + 1
    await bot.send(ev, msg)

daily_boss_limiter = DailyAmountLimiter("boss", DAY_BOSS_LIMIT, RESET_HOUR)
@sv.on_rex(r'^挑战(a|b|c)(1|2|3|4|5)$')
async def boss_battle(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    cid = CE._get_guaji(gid, uid)
    if cid == 0:
        msg = '您尚未绑定角色，请发送 绑定女友+角色名。'
        await bot.finish(ev, msg)
    owner = duel._get_card_owner(gid, cid)
    c = duel_chara.fromid(cid)
    if uid != owner:
        msg = f'您绑定了：{c.name}，但她已不在您身边，请重新绑定您的女友。'
        await bot.finish(ev, msg)

    guid = gid, uid
    match = ev['match']
    stage = match.group(1)
    stage = stage.upper()
    boss = int(match.group(2))
    bossInfo = BOSS_LIST[stage][boss]
    if not bossInfo:
        await bot.finish(ev, f'不存在该boss，请输入 挑战(A/B/C)(1/2/3/4/5)，例如：挑战A1。', at_sender=True)
    card_ce = get_card_ce(gid, uid, cid)
    bossHP = bossInfo[1]
    if math.ceil(bossHP/card_ce) >= 3:
        msg = f'您的女友还很脆弱(战力{card_ce})，战力与HP差2倍以上，无法挑战{bossInfo[0]}(HP{bossHP})，请提升女友战力后重试！'
        await bot.finish(ev, msg,at_sender=True)
    is_challenge = duel._get_bossbattle(gid,uid,cid,stage,boss)
    if is_challenge==0: #首次挑战
        challenge_msg = "[首次挑战]"
        need_limiter = False
    else:
        challenge_msg = ''
        need_limiter = True
        if not daily_boss_limiter.check(guid):
            await bot.finish(ev, f'非首次挑战或今天已经挑战了{DAY_BOSS_LIMIT}次boss了哦，明天再来吧。', at_sender=True)
    heart = bossInfo[2]
    score = bossInfo[3]
    jingyan = bossInfo[4]
    if card_ce>=bossHP: #击杀boss
        score_counter._add_score(gid,uid,score)
        score_counter._add_pcrheart(gid,uid,heart)
        card_level = add_exp(gid, uid, cid, jingyan)
        nvmes = get_nv_icon(cid)
        msg = f'{challenge_msg}{bossInfo[0]}:“嘤嘤嘤o(╥﹏╥)o”！\n您的女友{c.name}战力超群，一击秒杀了{bossInfo[0]}，您获得了{heart}心碎和{score}金币\n您的女友获得了{jingyan}经验值，目前等级为{card_level}\n{nvmes}'
    else:
        heart = math.ceil((card_ce/bossHP)*heart)
        score = math.ceil((card_ce/bossHP)*bossInfo[3])
        jingyan = math.ceil((card_ce/bossHP)*bossInfo[4])
        score_counter._add_score(gid, uid, score)
        score_counter._add_pcrheart(gid, uid, heart)
        card_level = add_exp(gid, uid, cid, jingyan)
        nvmes = get_nv_icon(cid)
        msg = f'{challenge_msg}{bossInfo[0]}:“吼吼吼(*^▽^*)”！\n您的女友{c.name}经不住{bossInfo[0]}的攻击，饮恨败北，仅磨掉了它{card_ce}HP。\n您获得了{heart}心碎和{score}金币\n您的女友获得了{jingyan}经验值，目前等级为{card_level}\n{nvmes}'
    if need_limiter==True:
        daily_boss_limiter.increase(guid)
    else:
        duel._add_bossbattle(gid,uid,cid,stage,boss)
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['女友rank等级表','rank表','rank等级表'])
async def rank_list(bot, ev: CQEvent):
    msg = '女友rank等级需求表：\n'
    rank = 1
    while (rank <= 10):
        rankInfo = RANK_LIST[rank]
        noblename = get_noblename(rank)
        ce_up = 1+rank/10
        msg += f'"R{rank}": 需求贵族等级≥{noblename}，消耗{rankInfo}金币，女友战力提升为{ce_up}倍\n'
        rank = rank + 1
    await bot.send(ev, msg)

@sv.on_prefix(['升级rank','rank升级','提升rank'])
async def up_rank(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 rank升级+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    rank = duel._get_rank(gid,uid,cid)
    if rank==MAX_RANK:
        await bot.finish(ev, '该女友rank已升至满级，无法继续升级啦。', at_sender=True)
    new_rank = rank + 1
    level = duel._get_level(gid,uid)
    if new_rank>level:
        await bot.finish(ev, '您的贵族等级不足，请发送[升级贵族]提升您的等级吧。', at_sender=True)
    rank_score = RANK_LIST[int(new_rank)]
    score_counter = ScoreCounter2()
    myscore = score_counter._get_score(gid,uid)
    if myscore < rank_score:
        await bot.finish(ev, f'升级rank所需金币不足！\n由{rank}级升至{new_rank}级需要：{rank_score}个，您当前剩余：{myscore}个',at_sender=True)
    score_counter._reduce_score(gid, uid, rank_score)
    duel._up_rank(gid,uid,cid)
    c = duel_chara.fromid(cid)
    msg = f'\n您花费了{rank_score}金币为{c.name}提升了rank，当前rank等级为：{new_rank}级，女友战斗力大大提升！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['战力榜','女友战力榜','战力排行榜'])
async def girl_power_rank(bot, ev: CQEvent):
    ranking_list = get_power_rank(ev.group_id)
    msg = '本群女友战力排行榜(仅展示rank>0的)：\n'
    if len(ranking_list)>0:
        rank = 1
        for girl in ranking_list:
            if rank<=10:
                user_card_dict = await get_user_card_dict(bot, ev.group_id)
                rank1,power,uid,cid = girl
                user_card = uid2card(uid, user_card_dict)
                c = duel_chara.fromid(cid)
                msg += f'第{rank}名: {user_card}的 {c.name}(rank{rank1})，战斗力{power}点\n'
            rank = rank+1
    else:
        msg += '暂无女友上榜'
    await bot.send(ev, msg)