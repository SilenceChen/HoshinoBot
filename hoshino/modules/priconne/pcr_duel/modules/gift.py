# 礼物系统
from .. import sv
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *
from ..pcr_duel import DuelJudger
from ..pcr_duel import DailyAmountLimiter
from ..config.duelconfig import *

duel_judger = DuelJudger()
class GiftChange:
    def __init__(self):
        self.giftchange_on={}
        self.waitchange={}
        self.isaccept = {}
        self.changeid = {}

 #礼物交换开关
    def get_on_off_giftchange_status(self, gid):
        return self.giftchange_on[gid] if self.giftchange_on.get(gid) is not None else False

    def turn_on_giftchange(self, gid):
        self.giftchange_on[gid] = True

    def turn_off_giftchange(self, gid):
        self.giftchange_on[gid] = False
    #礼物交换发起开关
    def get_on_off_waitchange_status(self, gid):
        return self.waitchange[gid] if self.waitchange.get(gid) is not None else False

    def turn_on_waitchange(self, gid):
        self.waitchange[gid] = True

    def turn_off_waitchange(self, gid):
        self.waitchange[gid] = False
    #礼物交换是否接受开关
    def turn_on_accept_giftchange(self, gid):
        self.isaccept[gid] = True

    def turn_off_accept_giftchange(self, gid):
        self.isaccept[gid] = False

    def get_isaccept_giftchange(self, gid):
        return self.isaccept[gid] if self.isaccept[gid] is not None else False
    #记录礼物交换请求接收者id
    def init_changeid(self, gid):
        self.changeid[gid] = []

    def set_changeid(self, gid, id2):
        self.changeid[gid] = id2

    def get_changeid(self, gid):
        return self.changeid[gid] if self.changeid.get(gid) is not None else 0
gift_change = GiftChange()

daily_gift_limiter = DailyAmountLimiter("gift", GIFT_DAILY_LIMIT, RESET_HOUR)
daily_date_limiter = DailyAmountLimiter("date", DATE_DAILY_LIMIT, RESET_HOUR)

@sv.on_fullmatch(['礼物系统帮助','礼物帮助'])
async def gift_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             礼物系统帮助
1. 查好感+女友名
2. 贵族约会+女友名 (1天限1次)
3. 买礼物  (300金币，一天限5次）
4. 送礼+女友名+礼物 空格隔开
5. 用xx与@xx交换xx
6. 买情报+女友名  (500金币，可了解女友喜好)
7. 我的礼物 (查询礼物仓库)
8. 好感列表
9. 重置礼物交换(限管理，交换卡住时用)
注:
通过约会或者送礼可以提升好感
决斗输掉某女友会扣除50好感，不够则被抢走
女友喜好与原角色无关，只是随机生成，仅供娱乐
╚                                        ╝
 '''
    await bot.send(ev, msg)


@sv.on_prefix(['查好感','查询好感'])
async def girl_story(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if not args:
        await bot.finish(ev, '请输入查好感+女友名。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)

    if duel._get_favor(gid,uid,cid)== None:
        duel._set_favor(gid,uid,cid,0)
    favor= duel._get_favor(gid,uid,cid)
    relationship,text = get_relationship(favor)
    c = duel_chara.fromid(cid)
    nvmes = get_nv_icon(cid)
    msg = f'\n{c.name}对你的好感是{favor}\n你们的关系是{relationship}\n“{text}”\n{nvmes}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['每日约会','女友约会', '贵族约会'])
async def daily_date(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if not args:
        await bot.finish(ev, '请输入贵族约会+女友名。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    guid = gid ,uid
    if not daily_date_limiter.check(guid):
        await bot.finish(ev, '今天已经和女友约会过了哦，明天再来吧。', at_sender=True)

    loginnum_ = ['1','2', '3', '4']
    r_ = [0.2, 0.4, 0.35, 0.05]
    sum_ = 0
    ran = random.random()
    for num, r in zip(loginnum_, r_):
        sum_ += r
        if ran < sum_ :break
    Bonus = {'1':[5,Date5],
             '2':[10,Date10],
             '3':[15,Date15],
             '4':[20,Date20]
            }
    favor = Bonus[num][0]
    text = random.choice(Bonus[num][1])
    duel._add_favor(gid,uid,cid,favor)
    c = duel_chara.fromid(cid)
    nvmes = get_nv_icon(cid)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    msg = f'\n\n{text}\n\n你和{c.name}的好感上升了{favor}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{nvmes}'
    daily_date_limiter.increase(guid)
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['抽礼物','买礼物','购买礼物'])
async def buy_gift(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    guid = gid ,uid
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来买礼物吧。'
        await bot.finish(ev, msg, at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 300:
        await bot.finish(ev, '购买礼物需要300金币，您的金币不足哦。', at_sender=True)
    if not daily_gift_limiter.check(guid):
        await bot.finish(ev, f'今天购买礼物已经超过{GIFT_DAILY_LIMIT}次了哦，明天再来吧。', at_sender=True)
    select_gift = random.choice(list(GIFT_DICT.keys()))
    gfid = GIFT_DICT[select_gift]
    duel._add_gift(gid,uid,gfid)
    msg = f'\n您花费了300金币，\n买到了[{select_gift}]哦，\n欢迎下次惠顾。'
    score_counter._reduce_score(gid,uid,300)
    daily_gift_limiter.increase(guid)
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['送礼物', '送礼', '赠送礼物'])
async def give_gift(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if gift_change.get_on_off_giftchange_status(ev.group_id):
        await bot.finish(ev, "有正在进行的礼物交换，礼物交换结束再来送礼物吧。")
    if len(args) != 2:
        await bot.finish(ev, '请输入 送礼物+女友名+礼物名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    gift = args[1]
    if gift not in GIFT_DICT.keys():
        await bot.finish(ev, '请输入正确的礼物名。', at_sender=True)
    gfid = GIFT_DICT[gift]
    if duel._get_gift_num(gid, uid, gfid) == 0:
        await bot.finish(ev, '你的这件礼物的库存不足哦。', at_sender=True)
    duel._reduce_gift(gid, uid, gfid)
    favor, text = check_gift(cid, gfid)
    duel._add_favor(gid, uid, cid, favor)
    current_favor = duel._get_favor(gid, uid, cid)
    relationship = get_relationship(current_favor)[0]
    c = duel_chara.fromid(cid)
    nvmes = get_nv_icon(cid)
    msg = f'\n{c.name}:“{text}”\n\n你和{c.name}的好感上升了{favor}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{nvmes}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['我的礼物', '礼物仓库', '查询礼物', '礼物列表'])
async def my_gift(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    msg = f'\n您的礼物仓库如下:'
    giftmsg = ''
    for gift in GIFT_DICT.keys():
        gfid = GIFT_DICT[gift]
        num = duel._get_gift_num(gid, uid, gfid)
        if num != 0:
            # 补空格方便对齐
            length = len(gift)
            msg_part = '    ' * (4 - length)
            giftmsg += f'\n{gift}{msg_part}: {num}件'
    if giftmsg == '':
        await bot.finish(ev, '您现在没有礼物哦，快去发送 买礼物 购买吧。', at_sender=True)
    msg += giftmsg
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex(f'^用(.*)与(.*)交换(.*)$')
async def change_gift(bot, ev: CQEvent):
    gid = ev.group_id
    duel = DuelCounter()
    if gift_change.get_on_off_giftchange_status(ev.group_id):
        await bot.finish(ev, "有正在进行的礼物交换，请勿重复使用指令。")
    gift_change.turn_on_giftchange(gid)
    id1 = ev.user_id
    match = ev['match']
    try:
        id2 = int(ev.message[1].data['qq'])
    except:
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, '参数格式错误')
    if id2 == id1:
        await bot.send(ev, "不能和自己交换礼物！", at_sender=True)
        gift_change.turn_off_giftchange(ev.group_id)
        return
    gift1 = match.group(1)
    gift2 = match.group(3)
    if gift1 not in GIFT_DICT.keys():
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, f'礼物1不存在。')
    if gift2 not in GIFT_DICT.keys():
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, f'礼物2不存在。')
    gfid1 = GIFT_DICT[gift1]
    gfid2 = GIFT_DICT[gift2]
    if gfid2 == gfid1:
        await bot.send(ev, "不能交换相同的礼物！", at_sender=True)
        gift_change.turn_off_giftchange(ev.group_id)
        return

    if duel._get_gift_num(gid, id1, gfid1) == 0:
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, f'[CQ:at,qq={id1}]\n您的{gift1}的库存不足哦。')
    if duel._get_gift_num(gid, id2, gfid2) == 0:
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, f'[CQ:at,qq={id2}]\n您的{gift2}的库存不足哦。')
    level2 = duel._get_level(gid, id2)
    noblename = get_noblename(level2)
    gift_change.turn_on_waitchange(gid)
    gift_change.set_changeid(gid, id2)
    gift_change.turn_off_accept_giftchange(gid)
    msg = f'[CQ:at,qq={id2}]\n尊敬的{noblename}您好：\n\n[CQ:at,qq={id1}]试图用[{gift1}]交换您的礼物[{gift2}]。\n\n请在{WAIT_TIME_CHANGE}秒内[接受交换/拒绝交换]。'
    await bot.send(ev, msg)
    await asyncio.sleep(WAIT_TIME_CHANGE)
    gift_change.turn_off_waitchange(gid)
    if gift_change.get_isaccept_giftchange(gid) is False:
        msg = '\n礼物交换被拒绝。'
        gift_change.init_changeid(gid)
        gift_change.turn_off_giftchange(gid)
        await bot.finish(ev, msg, at_sender=True)
    duel._reduce_gift(gid, id1, gfid1)
    duel._add_gift(gid, id1, gfid2)
    duel._reduce_gift(gid, id2, gfid2)
    duel._add_gift(gid, id2, gfid1)
    msg = f'\n礼物交换成功！\n您使用[{gift1}]交换了\n[CQ:at,qq={id2}]的[{gift2}]。'
    gift_change.init_changeid(gid)
    gift_change.turn_off_giftchange(gid)
    await bot.finish(ev, msg, at_sender=True)

@sv.on_fullmatch('接受交换')
async def giftchangeaccept(bot, ev: CQEvent):
    gid = ev.group_id
    if gift_change.get_on_off_waitchange_status(gid):
        if ev.user_id == gift_change.get_changeid(gid):
            msg = '\n礼物交换接受成功，请耐心等待礼物交换结束。'
            await bot.send(ev, msg, at_sender=True)
            gift_change.turn_off_waitchange(gid)
            gift_change.turn_on_accept_giftchange(gid)

@sv.on_fullmatch('拒绝交换')
async def giftchangerefuse(bot, ev: CQEvent):
    gid = ev.group_id
    if gift_change.get_on_off_waitchange_status(gid):
        if ev.user_id == gift_change.get_changeid(gid):
            msg = '\n礼物交换拒绝成功，请耐心等待礼物交换结束。'
            await bot.send(ev, msg, at_sender=True)
            gift_change.turn_off_waitchange(gid)
            gift_change.turn_off_accept_giftchange(gid)

@sv.on_prefix(['购买情报', '买情报'])
async def buy_information(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来买情报吧。'
        await bot.finish(ev, msg, at_sender=True)
    if not args:
        await bot.finish(ev, '请输入买情报+女友名。', at_sender=True)
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 500:
        await bot.finish(ev, '购买女友情报需要500金币，您的金币不足哦。', at_sender=True)
    score_counter._reduce_score(gid, uid, 500)
    last_num = cid % 10
    like = ''
    normal = ''
    dislike = ''
    for gift in GIFT_DICT.keys():
        if GIFT_DICT[gift] == last_num:
            favorite = gift
            continue
        num1 = last_num % 3
        num2 = GIFT_DICT[gift] % 3
        choicelist = GIFTCHOICE_DICT[num1]

        if num2 == choicelist[0]:
            like += f'{gift}\n'
            continue
        if num2 == choicelist[1]:
            normal += f'{gift}\n'
            continue
        if num2 == choicelist[2]:
            dislike += f'{gift}\n'
            continue
    c = duel_chara.fromid(cid)
    nvmes = get_nv_icon(cid)
    msg = f'\n花费了500金币，您买到了以下情报：\n{c.name}最喜欢的礼物是:\n{favorite}\n喜欢的礼物是:\n{like}一般喜欢的礼物是:\n{normal}不喜欢的礼物是:\n{dislike}{nvmes}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('重置礼物交换')
async def init_change(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置礼物交换哦。', at_sender=True)
    gift_change.turn_off_giftchange(ev.group_id)
    msg = '已重置本群礼物交换状态！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['好感列表', '女友好感列表'])
async def get_favorlist(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    cidlist = duel._get_cards(gid, uid)
    if len(cidlist) == 0:
        await bot.finish(ev, '您现在还没有女友哦。', at_sender=True)
    favorlist = []
    for cid in cidlist:
        favor = duel._get_favor(gid, uid, cid)
        if favor != 0 and favor != None:
            favorlist.append({"cid": cid, "favor": favor})
    if len(favorlist) == 0:
        await bot.finish(ev, '您的女友好感全部为0哦。', at_sender=True)
    rows_by_favor = sorted(favorlist, key=lambda r: r['favor'], reverse=True)
    msg = '\n您好感0以上的女友的前10名如下所示:\n'
    num = min(len(rows_by_favor), 10)
    for i in range(0, num):
        cid = rows_by_favor[i]["cid"]
        favor = rows_by_favor[i]["favor"]
        c = duel_chara.fromid(cid)
        msg += f'{c.name}:{favor}点\n'
    await bot.send(ev, msg, at_sender=True)