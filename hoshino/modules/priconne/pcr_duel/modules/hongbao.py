from .. import sv
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *
from ..pcr_duel import DuelJudger
from ..pcr_duel import DailyAmountLimiter
from ..config.duelconfig import *

class duelrandom():
    def __init__(self):
        self.random_gold_on = {}
        self.random_gold = {}
        self.rdret = {}
        self.user = {}

    def turn_on_random_gold(self, gid):
        self.random_gold_on[gid] = True

    def turn_off_random_gold(self, gid):
        self.random_gold_on[gid] = False

    def set_gold(self, gid):
        self.user[gid] = []

    def add_gold(self, gid, gold, num):
        self.random_gold[gid] = {'GOLD': gold, 'NUM': num}

    def get_gold(self, gid):
        return self.random_gold[gid]['GOLD']

    def get_num(self, gid):
        return self.random_gold[gid]['NUM']

    def add_user(self, gid, uid):
        self.user[gid].append(uid)

    def get_on_off_random_gold(self, gid):
        return self.random_gold_on[gid] if self.random_gold_on.get(gid) is not None else False

    def random_g(self, gid, gold, num):
        z = []
        ret = random.sample(range(1, gold), num - 1)
        ret.append(0)
        ret.append(gold)
        ret.sort()
        for i in range(len(ret) - 1):
            z.append(ret[i + 1] - ret[i])
        self.rdret[gid] = z

    def get_user_random_gold(self, gid, num):
        rd = random.randint(0, num - 1)
        print(rd)
        ugold = self.rdret[gid][rd]
        self.rdret[gid].remove(ugold)
        return ugold
r_gold = duelrandom()

@sv.on_prefix('发红包')
async def ramdom_gold(bot, ev: CQEvent):
    if not r_gold.get_on_off_random_gold(ev.group_id):
        if not priv.check_priv(ev, priv.SUPERUSER):
            await bot.finish(ev, '该功能仅限超级管理员使用')
        gid = ev.group_id
        msg = ev.message.extract_plain_text().split()
        if not msg[0].isdigit():
            await bot.finish(ev, '请输入正确的红包总额')
        if not msg[1].isdigit():
            await bot.finish(ev, '请输入正确的红包个数')
        gold = int(msg[0])
        num = int(msg[1])
        await bot.send(ev, f'发放红包成功，金币总额为：{gold}\n数量：{num}\n所有人可输入 领红包')
        r_gold.turn_on_random_gold(gid)
        r_gold.set_gold(gid)
        r_gold.add_gold(gid, gold, num)
        r_gold.random_g(gid, gold, num)
        await asyncio.sleep(60)
        r_gold.turn_off_random_gold(gid)
        await bot.send(ev, '红包活动已结束，请期待下次活动开启')
        r_gold.user = {}

@sv.on_fullmatch(('领红包', '领取红包'))
async def get_random_gold(bot, ev: CQEvent):
    if r_gold.get_on_off_random_gold(ev.group_id):
        uid = int(ev.user_id)
        gid = ev.group_id
        if uid in r_gold.user[gid]:
            await bot.finish(ev, '您已领过红包', at_sender=True)
        score_counter = ScoreCounter2()
        # 获取金币
        gold = r_gold.get_gold(gid)
        # 获取个数
        num = r_gold.get_num(gid)
        # 获取金额
        rd = r_gold.get_user_random_gold(gid, num)
        r_gold.add_gold(gid, gold - rd, num - 1)
        newnum = r_gold.get_num(gid)
        newgold = r_gold.get_gold(gid)
        score_counter._add_score(gid, uid, rd)
        r_gold.add_user(gid, uid)
        await bot.send(ev, f'您拆开了红包，获得了金币：{rd}个\n当前剩余{newnum}个红包，总额：{newgold}，赶快来抢吧！', at_sender=True)
        if newnum == 0:
            await bot.send(ev, f'红包已全部领取完毕')
            r_gold.turn_off_random_gold(gid)