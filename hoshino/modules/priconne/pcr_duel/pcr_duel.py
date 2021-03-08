import asyncio
import base64
import os
import random
import sqlite3
import math
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from . import sv
from hoshino import Service, priv
from hoshino.modules.priconne.wiki import data as wikidata
from .data import duel_chara
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
import copy
import json
from .counter.CECounter import *
from .counter.ScoreCounter import *
from .counter.DuelCounter import *
from .config.duelconfig import *

@sv.on_fullmatch(['贵族决斗帮助','贵族帮助','贵族指令'])
async def duel_help(bot, ev: CQEvent):
    msg='''
╔                                       ╗    
        贵族决斗相关指令
   1.创建贵族
   2.贵族签到
   3.查询贵族/贵族查询/我的贵族
   4.贵族等级表
   5.招募女友/贵族舞会
   6.免费招募   (仅限庆典期间)
   7.本群贵族
   8.增加容量/增加女友上限
   9.升级爵位/升级贵族/贵族升级
   10.贵族决斗@xx
   11.支持(1|2)号xx金币  (普通下注)
   12.梭哈支持(1|2)号    (全部家当下注)
   13.领金币/领取金币  (金币为0才能领取)
   14.为@xx转账xx金币
   15.查女友/查询女友/查看女友 +角色名
   16.确认重开  (慎用，会初始化您的贵族)
   17.分手 +角色名  (需要支付一定的金币及声望作为分手费)
   18.金币排行榜/金币排行
   19.声望排行榜/声望排行
   20.女友排行榜/女友排行
   
   --声望系统-- 具体指令发送: 声望系统帮助/声望帮助
   --商城系统-- 具体指令发送: 商城系统帮助/商城帮助
   --礼物系统-- 具体指令发送: 礼物系统帮助/礼物帮助
   --专武系统-- 具体指令发送: 专武系统帮助/专武帮助
   --战斗系统-- 具体指令发送: 战斗系统帮助/战斗帮助
   --DLC系统-- 具体指令发送: dlc系统帮助/dlc帮助
   
  一个女友只属于一位群友
╚                                        ╝
'''  
    await bot.send(ev, msg)

@sv.on_fullmatch(['贵族表','贵族等级表'])
async def duel_biao(bot, ev: CQEvent):
    i = 2
    msg =f'"1": "{get_noblename(1)}",  最多可持有{get_girlnum(1)}名女友，每日签到额外获得{scoreLV * 1}金币，{SWLV * 1}声望，初始等级。\n'
    while(i<=6):
        msg +=f'"{i}": "{get_noblename(i)}",  升级需要{get_noblescore(i)}金币，需要{get_nobleWin(i)}胜场，最多可持有{get_girlnum(i)}名女友，每日签到额外获得{scoreLV * i}金币，{SWLV * i}声望，保持等级最少持有{get_girlnum(i-1)}名女友。\n'
        i = i+1
    while(i < Safe_LV):
        msg += f'"{i}": "{get_noblename(i)}",  升级需要{get_noblescore(i)}金币，{get_noblesw(i)}声望，需要{get_nobleWin(i)}胜场，最多可持有{get_girlnum(i)}名女友，每日签到额外获得{scoreLV * i}金币，{SWLV * i}声望，保持等级最少持有{get_girlnum(i-1)}名女友。\n'
        i = i+1
    while(i <= 10):
        msg += f'"{i}": "{get_noblename(i)}",  升级需要{get_noblescore(i)}金币，{get_noblesw(i)}声望，需要{get_nobleWin(i)}胜场，最多可持有{get_girlnum(i)}名女友，每日签到额外获得{scoreLV * i}金币，{SWLV * i}声望，不会再掉级。\n'
        i = i+1
    msg += f'"11": "神",  升级需要{FS_NEED_GOLD}币，{FS_NEED_SW}声望，无女友上限，每日签到额外获得{scoreLV * 20}金币，{SWLV * 20}声望，可以拥有两名妻子\n'
    await bot.send(ev, msg)

# noinspection SqlResolve
class RecordDAO:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS limiter"
                "(key TEXT NOT NULL, num INT NOT NULL, date INT, PRIMARY KEY(key))"
            )

    def exist_check(self, key):
        try:
            key = str(key)
            with self.connect() as conn:
                conn.execute("INSERT INTO limiter (key,num,date) VALUES (?, 0,-1)", (key,), )
            return
        except:
            return

    def get_num(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT num FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def clear_key(self, key):
        key = str(key)
        self.exist_check(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=0 WHERE key=?", (key,), )
        return

    def increment_key(self, key, num):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=num+? WHERE key=?", (num, key,))
        return

    def get_date(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT date FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def set_date(self, date, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET date=? WHERE key=?", (date, key,), )
        return
db = RecordDAO(DB_PATH)

class DailyAmountLimiter(DailyNumberLimiter):
    def __init__(self, types, max_num, reset_hour):
        super().__init__(max_num)
        self.reset_hour = reset_hour
        self.type = types

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < self.max)

    def check10(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < 10)

    def get_num(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        return db.get_num(key)

    def increase(self, key, num=1):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.increment_key(key, num)

    def reset(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.clear_key(key)
daily_sign_limiter = DailyAmountLimiter("sign", SIGN_DAILY_LIMIT, RESET_HOUR)
daily_free_limiter = DailyAmountLimiter("free", FREE_DAILY_LIMIT, RESET_HOUR)
daily_duel_limiter = DailyAmountLimiter("duel", DUEL_DAILY_LIMIT, RESET_HOUR)
daily_Remake_limiter = DailyAmountLimiter("Remake", Remake_LIMIT, RESET_HOUR)

# 记录决斗和下注数据
class DuelJudger:
    def __init__(self):
        self.on = {}
        self.accept_on = {}
        self.support_on = {}
        self.fire_on = {}
        self.deadnum = {}
        self.support = {}
        self.turn = {}
        self.duelid = {}
        self.isaccept = {}
        self.hasfired_on = {}

    def set_support(self, gid):
        self.support[gid] = {}

    def get_support(self, gid):
        return self.support[gid] if self.support.get(gid) is not None else 0

    def add_support(self, gid, uid, id, score):
        self.support[gid][uid] = [id, score]

    def get_support_id(self, gid, uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][0]
        else:
            return 0

    def get_support_score(self, gid, uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][1]
        else:
            return 0

    # 五个开关：决斗，接受，下注， 开枪, 是否已经开枪

    def get_on_off_status(self, gid):
        return self.on[gid] if self.on.get(gid) is not None else False

    def turn_on(self, gid):
        self.on[gid] = True

    def turn_off(self, gid):
        self.on[gid] = False

    def get_on_off_accept_status(self, gid):
        return self.accept_on[gid] if self.accept_on.get(gid) is not None else False

    def turn_on_accept(self, gid):
        self.accept_on[gid] = True

    def turn_off_accept(self, gid):
        self.accept_on[gid] = False

    def get_on_off_support_status(self, gid):
        return self.support_on[gid] if self.support_on.get(gid) is not None else False

    def turn_on_support(self, gid):
        self.support_on[gid] = True

    def turn_off_support(self, gid):
        self.support_on[gid] = False

    def get_on_off_fire_status(self, gid):
        return self.fire_on[gid] if self.fire_on.get(gid) is not None else False

    def turn_on_fire(self, gid):
        self.fire_on[gid] = True

    def turn_off_fire(self, gid):
        self.fire_on[gid] = False

    def get_on_off_hasfired_status(self, gid):
        return self.hasfired_on[gid] if self.hasfired_on.get(gid) is not None else False

    def turn_on_hasfired(self, gid):
        self.hasfired_on[gid] = True

    def turn_off_hasfired(self, gid):
        self.hasfired_on[gid] = False

    # 记录决斗者id
    def init_duelid(self, gid):
        self.duelid[gid] = []

    def set_duelid(self, gid, id1, id2):
        self.duelid[gid] = [id1, id2]

    def get_duelid(self, gid):
        return self.duelid[gid] if self.accept_on.get(gid) is not None else [0, 0]

    # 查询一个决斗者是1号还是2号
    def get_duelnum(self, gid, uid):
        return self.duelid[gid].index(uid) + 1

    # 记录由谁开枪
    def init_turn(self, gid):
        self.turn[gid] = 1

    def get_turn(self, gid):
        return self.turn[gid] if self.turn[gid] is not None else 0

    def change_turn(self, gid):
        if self.get_turn(gid) == 1:
            self.turn[gid] = 2
            return 2
        else:
            self.turn[gid] = 1
            return 1

    # 记录子弹位置
    def init_deadnum(self, gid):
        self.deadnum[gid] = None

    def set_deadnum(self, gid, num):
        self.deadnum[gid] = num

    def get_deadnum(self, gid):
        return self.deadnum[gid] if self.deadnum[gid] is not None else False

    # 记录是否接受
    def init_isaccept(self, gid):
        self.isaccept[gid] = False

    def on_isaccept(self, gid):
        self.isaccept[gid] = True

    def off_isaccept(self, gid):
        self.isaccept[gid] = False

    def get_isaccept(self, gid):
        return self.isaccept[gid] if self.isaccept[gid] is not None else False
duel_judger = DuelJudger()

@sv.on_fullmatch('贵族签到')
async def noblelogin(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    guid = gid, uid
    if not daily_sign_limiter.check(guid):
        await bot.send(ev, '今天已经签到过了哦，明天再来吧。', at_sender=True)
        return
    duel = DuelCounter()
    
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    #根据概率随机获得收益。 
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if prestige == None :
       score_counter._set_prestige(gid,uid,0)
    daily_sign_limiter.increase(guid)    
    loginnum_ = ['1','2', '3', '4']  
    r_ = [0.3, 0.4, 0.2, 0.1]  
    sum_ = 0
    ran = random.random()
    for num, r in zip(loginnum_, r_):
        sum_ += r
        if ran < sum_ :break
    Bonus = {'1':[200,Login100],
             '2':[500,Login200],
             '3':[700,Login300],    
             '4':[1000,Login600]
            }             
    score1 = Bonus[num][0]
    score1 = 3 * score1
    text1 = random.choice(Bonus[num][1])
    
    #根据爵位的每日固定收入
    level = duel._get_level(gid, uid)
    score2 = 300*level
    SW2 = 100*level
    scoresum = score1+score2
    noblename = get_noblename(level)
    score = score_counter._get_score(gid, uid)  
    if duel._get_QC_CELE(gid) == 1:
     scoresum = scoresum * QD_Gold_Cele_Num
     SW2 = SW2 * QD_SW_Cele_Num
     msg = f'\n{text1}\n签到成功！\n[庆典举办中]\n您领取了：\n\n{score1}金币(随机)和\n{score2}金币以及{SW2}声望({noblename}爵位)'
    else:
     msg = f'\n{text1}\n签到成功！\n您领取了：\n\n{score1}金币(随机)和\n{score2}金币以及{SW2}声望({noblename}爵位)'
    score_counter._add_prestige(gid,uid,SW2)
    score_counter._add_score(gid, uid, scoresum)
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist)
    
    if cidnum > 0:
        cid = random.choice(cidlist)
        c = duel_chara.fromid(cid)
        nvmes = get_nv_icon(cid)
        msg +=f'\n\n今天向您请安的是\n{c.name}{nvmes}'   
    #随机获得一件礼物
    select_gift = random.choice(list(GIFT_DICT.keys()))
    gfid = GIFT_DICT[select_gift]
    duel._add_gift(gid,uid,gfid)
    msg +=f'\n随机获得了礼物[{select_gift}]'
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_fullmatch('免费招募')
async def noblelogin(bot, ev: CQEvent):
   gid = ev.group_id
   uid = ev.user_id
   duel = DuelCounter()  
   if duel._get_FREE_CELE(gid) != 1:
    await bot.send(ev, '当前未开放免费招募庆典！', at_sender=True)
    return
   else:
    guid = gid, uid
    if not daily_free_limiter.check(guid):
        await bot.send(ev, '今天已经免费招募过了喔，明天再来吧。(免费招募次数每天0点刷新)', at_sender=True)
        return 
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return  
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再参加舞会吧。'
        await bot.send(ev, msg, at_sender=True)
        return             
    else:
        # 防止女友数超过上限
        level = duel._get_level(gid, uid)
        noblename = get_noblename(level)
        girlnum = get_girlnum_buy(gid,uid)
        cidlist = duel._get_cards(gid, uid)
        cidnum = len(cidlist)
        if cidnum >= girlnum:
            msg = '您的女友已经满了哦，您转为获得500声望。'
            score_counter._add_prestige(gid, uid, 500)
            daily_free_limiter.increase(guid)  
            await bot.send(ev, msg, at_sender=True)
            return
        score = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        if prestige == None:
           score_counter._set_prestige(gid,uid,0)
        newgirllist = get_newgirl_list(gid)
        # 判断女友是否被抢没和该用户是否已经没有女友
        if len(newgirllist) == 0:
            if cidnum!=0:
                await bot.send(ev, '这个群已经没有可以约到的新女友了哦。', at_sender=True)
                return        
            else : 
                score_counter._reduce_score(gid, uid, GACHA_COST)
                cid = 9999
                c = duel_chara.fromid(1059)
                duel._add_card(gid, uid, cid)
                msg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
                await bot.send(ev, msg, at_sender=True)
                return

        # 招募女友成功
        daily_free_limiter.increase(guid)  
        cid = random.choice(newgirllist)
        c = duel_chara.fromid(cid)
        nvmes = get_nv_icon(cid)
        duel._add_card(gid, uid, cid)
        wintext = random.choice(Addgirlsuccess)
        msg = f'\n{wintext}\n招募女友成功！\n新招募的女友为：{c.name}{nvmes}'
        await bot.send(ev, msg, at_sender=True)
       
@sv.on_fullmatch(['本群贵族状态','查询本群贵族','本群贵族'])
async def group_noble_status(bot, ev: CQEvent):
    gid = ev.group_id
    duel = DuelCounter()
    newgirllist = get_newgirl_list(gid)
    newgirlnum = len(newgirllist)
    l1_num = duel._get_level_num(gid,1)
    l2_num = duel._get_level_num(gid,2)
    l3_num = duel._get_level_num(gid,3)
    l4_num = duel._get_level_num(gid,4)
    l5_num = duel._get_level_num(gid,5)
    l6_num = duel._get_level_num(gid,6)
    l7_num = duel._get_level_num(gid,7)
    l8_num = duel._get_level_num(gid,8)
    l9_num = duel._get_level_num(gid,9)
    lA_num = duel._get_level_num(gid,10)
    lB_num = duel._get_level_num(gid,20)
    dlctext = ''
    for dlc in dlcdict.keys():
        if gid in dlc_switch[dlc]:
            dlctext += f'{dlc},'
    msg=f'''
╔                          ╗
         本群贵族
    神：{lB_num}名  
  皇帝：{lA_num}名  
  国王：{l9_num}名  
  公爵：{l8_num}名  
  侯爵：{l7_num}名
  伯爵：{l6_num}名
  子爵：{l5_num}名
  男爵：{l4_num}名
  准男爵：{l3_num}名
  骑士：{l2_num}名
  平民：{l1_num}名
  已开启DLC:
  {dlctext}
  还有{newgirlnum}名单身女友 
╚                          ╝
'''
    await bot.send(ev, msg)

@sv.on_prefix(['查看贵族人员'])
async def group_noble_members(bot, ev: CQEvent):
    gid = ev.group_id
    duel = DuelCounter()
    args = ev.message.extract_plain_text().split()
    if not args:
        await bot.send(ev, '请输入 查看贵族人员+贵族等级。', at_sender=True)
        return
    name = args[0]
    level = get_noblelevel(name)
    if level == 0:
        await bot.send(ev, '请输入正确的贵族等级。', at_sender=True)
        return
    members = duel._get_level_members(gid,level)
    number = len(members)
    if number==0:
        await bot.finish(ev,f'本群暂时无人是{name}爵位。', at_sender=True)
    msg = f'本群{name}爵位的人员如下：\n'
    for uid in members:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        user_card = uid2card(uid, user_card_dict)
        cidlist = duel._get_cards(gid, uid)
        cidnum = len(cidlist)
        msg += f'{user_card}，QQ号为：{uid}，女友数：{cidnum}\n'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('创建贵族')
async def add_noble(bot, ev: CQEvent):
    try:
        gid = ev.group_id
        uid = ev.user_id
        duel = DuelCounter()
        if duel._get_level(gid, uid) != 0:
            msg = '您已经在本群创建过贵族了，请发送 查询贵族 查询。'
            await bot.send(ev, msg, at_sender=True)
            return
        
        #判定本群女友是否已空，如果空则分配一个复制人可可萝。
        newgirllist = get_newgirl_list(gid)
        if len(newgirllist) == 0:
            cid = 9999
            c = duel_chara.fromid(1059)
            girlmsg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
        else:
            cid = random.choice(newgirllist)
            c = duel_chara.fromid(cid)
            girlmsg = f'为您分配的初始女友为：{c.name}{c.icon.cqcode}'
        duel._add_card(gid, uid, cid)
        duel._set_level(gid, uid, 1)
        msg = f'\n创建贵族成功！\n您的初始爵位是平民\n可以拥有1名女友。\n初始金币为1000，初始声望为0\n{girlmsg}'
        score_counter = ScoreCounter2()
        score_counter._set_prestige(gid,uid,0)
        score_counter._add_score(gid, uid, 1000)
        
        await bot.send(ev, msg, at_sender=True)        
            

    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

@sv.on_fullmatch(['增加容量', '增加女友上限'])
async def add_warehouse(bot, ev: CQEvent):
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    gid = ev.group_id
    uid = ev.user_id
    current_score = score_counter._get_score(gid, uid)
    prestige = score_counter._get_prestige(gid,uid)
    if duel._get_level(gid, uid) <= 9:
        msg = '只有成为皇帝后，才能扩充女友上限喔'
        await bot.send(ev, msg, at_sender=True)
        return
    if prestige < SHANGXIAN_SW:
        msg = '扩充女友上限，需要{SHANGXIAN_SW}声望，您的声望不足喔'
        await bot.send(ev, msg, at_sender=True)
        return
    if current_score < SHANGXIAN_NUM:
        msg = f'增加女友上限需要消耗{SHANGXIAN_NUM}金币，您的金币不足哦'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        housenum=duel._get_warehouse(gid, uid)
        if housenum>=WAREHOUSE_NUM:
            msg = f'您已增加{WAREHOUSE_NUM}次上限，无法继续增加了哦'
            await bot.send(ev, msg, at_sender=True)
            return
        duel._add_warehouse(gid, uid, 1)
        score_counter._reduce_score(gid, uid, SHANGXIAN_NUM)
        score_counter._reduce_prestige(gid, uid, SHANGXIAN_SW)
        last_score = current_score-SHANGXIAN_NUM
        myhouse = get_girlnum_buy(gid, uid)
        msg = f'您消耗了{SHANGXIAN_NUM}金币，{SHANGXIAN_SW}声望，增加了1个女友上限，目前的女友上限为{myhouse}名'
        await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['查询贵族', '贵族查询', '我的贵族'])
async def inquire_noble(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    level = duel._get_level(gid, uid)
    noblename = get_noblename(level)
    girlnum = get_girlnum_buy(gid, uid)
    score = score_counter._get_score(gid, uid)
    charalist = []

    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist)
    Winnum = duel._get_WLCWIN(gid, uid)
    Losenum = duel._get_WLCLOSE(gid, uid)
    ADMITnum = duel._get_ADMIT(gid, uid)
    if Losenum == 0:
        winprobability = 100
    else:
        winprobability = (Winnum / (Winnum + Losenum)) * 100
    if Winnum == 0:
        winprobability = 0
    prestige = score_counter._get_prestige(gid, uid)
    if prestige == None:
        prestige = 0
        partmsg = f'您的声望为{prestige}点'
    else:
        partmsg = f'您的声望为{prestige}点'
    nv_names = ''
    if cidnum == 0:
        msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您的胜场数为{Winnum}
  负场数为{Losenum}
  累计认输场数为{ADMITnum}
  胜率为{winprobability}%
  您共可拥有{girlnum}名女友
  您目前没有女友。
  发送[贵族约会]
  可以招募女友哦。

╚                          ╝
'''
        await bot.send(ev, msg, at_sender=True)

    else:
        shuzi_flag = 0
        for cid in cidlist:
            is_equip = duel._get_uniequip(gid,uid,cid)
            # 替换复制人可可萝
            if cid == 9999:
                cid = 1059
                is_equip = 0
            charalist.append(duel_chara.Chara(cid, 0, is_equip))
            c = duel_chara.fromid(cid)
            shuzi_flag = shuzi_flag + 1
            nv_names = nv_names + c.name + ' '
            if shuzi_flag == 6:
                nv_names = nv_names + '\n'
                shuzi_flag = 0

        # 制图部分，六个一行
        num = copy.deepcopy(cidnum)
        position = 6
        if num <= 6:
            res = duel_chara.gen_team_pic(charalist, star_slot_verbose=False)
        else:
            num -= 6
            res = duel_chara.gen_team_pic(charalist[0:position], star_slot_verbose=False)
            while (num > 0):
                if num >= 6:
                    res1 = duel_chara.gen_team_pic(charalist[position:position + 6], star_slot_verbose=False)
                else:
                    res1 = duel_chara.gen_team_pic(charalist[position:], star_slot_verbose=False)
                res = concat_pic([res, res1])
                position += 6
                num -= 6

        bio = BytesIO()
        res.save(bio, format='PNG')
        base64_str = 'base64://' + base64.b64encode(bio.getvalue()).decode()
        mes = f"[CQ:image,file={base64_str}]"

        # 判断是否开启声望

        msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您的胜场数为{Winnum}
  负场数为{Losenum}
  累计认输场数为{ADMITnum}
  胜率为{winprobability}%
  您共可拥有{girlnum}名女友
  您已拥有{cidnum}名女友
  她们是：
  {nv_names}
    {mes}   
╚                          ╝
'''
        # 判断有无妻子
        q = 0
        queen = duel._search_queen(gid, uid)
        queen2 = duel._search_queen2(gid, uid)
        if queen != 0:
            c = duel_chara.fromid(queen)
            q = q + 1
        if queen2 != 0:
            c2 = duel_chara.fromid(queen2)
            q = q + 1
        if q == 2:
            msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您的胜场数为{Winnum}
  负场数为{Losenum}
  累计认输场数为{ADMITnum}
  胜率为{winprobability}%
  您的妻子是{c.name}和{c2.name}
  您共可拥有{girlnum}名女友
  您已拥有{cidnum}名女友
  她们是：
  {nv_names}
    {mes}  

╚                          ╝
'''
        if q == 1:
            if queen != 0:
                c = duel_chara.fromid(queen)
            if queen2 != 0:
                c = duel_chara.fromid(queen2)
            msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您的胜场数为{Winnum}
  负场数为{Losenum}
  累计认输场数为{ADMITnum}
  胜率为{winprobability}%
  您的妻子是{c.name}
  您共可拥有{girlnum}名女友
  您已拥有{cidnum}名女友
  她们是：
  {nv_names}
    {mes}  

╚                          ╝
'''

        await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['招募女友', '贵族舞会'])
async def add_girl(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再参加舞会吧。'
        await bot.send(ev, msg, at_sender=True)
        return            
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        # 防止女友数超过上限
        level = duel._get_level(gid, uid)
        noblename = get_noblename(level)
        girlnum = get_girlnum_buy(gid,uid)
        cidlist = duel._get_cards(gid, uid)
        cidnum = len(cidlist)
        if cidnum >= girlnum:
            msg = '您的女友已经满了哦，快点发送[升级贵族]进行升级吧。'
            await bot.send(ev, msg, at_sender=True)
            return
        score = score_counter._get_score(gid, uid)
        if score < GACHA_COST:
            msg = f'您的金币不足{GACHA_COST}哦。'
            await bot.send(ev, msg, at_sender=True)
            return
        prestige = score_counter._get_prestige(gid,uid)
        if prestige == None:
           score_counter._set_prestige(gid,uid,0)
        if prestige < 0 and level >7:
            msg = f'您现在身败名裂（声望为负），无法招募女友！。'
            await bot.send(ev, msg, at_sender=True)
            return
        newgirllist = get_newgirl_list(gid)
        # 判断女友是否被抢没和该用户是否已经没有女友
        if len(newgirllist) == 0:
            if cidnum!=0:
                await bot.send(ev, '这个群已经没有可以约到的新女友了哦。', at_sender=True)
                return        
            else : 
                score_counter._reduce_score(gid, uid, GACHA_COST)
                cid = 9999
                c = duel_chara.fromid(1059)
                duel._add_card(gid, uid, cid)
                msg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
                await bot.send(ev, msg, at_sender=True)
                return

        score_counter._reduce_score(gid, uid, GACHA_COST)

        # 招募女友失败
        if random.random() < 0.4:
            losetext = random.choice(Addgirlfail)
            msg = f'\n{losetext}\n您花费了{GACHA_COST}金币，但是没有约到新的女友。获得了{GACHA_COST_Fail}金币补偿。'
            score_counter._add_score(gid, uid, GACHA_COST_Fail)
            score = score_counter._get_score(gid, uid)
            await bot.send(ev, msg, at_sender=True)
            return

        # 招募女友成功
        cid = random.choice(newgirllist)
        c = duel_chara.fromid(cid)
        nvmes = get_nv_icon(cid)
        duel._add_card(gid, uid, cid)
        wintext = random.choice(Addgirlsuccess)
        
        msg = f'\n{wintext}\n招募女友成功！\n您花费了{GACHA_COST}金币\n新招募的女友为：{c.name}{nvmes}'
        await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['升级爵位', '升级贵族', '贵族升级'])
async def add_girl(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    score = score_counter._get_score(gid, uid)
    level = duel._get_level(gid, uid)
    noblename = get_noblename(level)
    girlnum = get_girlnum(level)
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist)
    Winnum = duel._get_WLCWIN(gid, uid)

    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再升级爵位吧。'
        await bot.send(ev, msg, at_sender=True)
        return
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    if level == 9:
        msg = f'您已经是国王了， 需要通过声望加冕称帝哦。'
        await bot.send(ev, msg, at_sender=True)
        return

    if level == 10:
        msg = f'您是本群的皇帝， 再往前一步就能成神了，请飞升成神。'
        await bot.send(ev, msg, at_sender=True)
        return

    if level == 20:
        msg = f'您已经到达了世界的巅峰， 无法再继续提升了。'
        await bot.send(ev, msg, at_sender=True)
        return

    if cidnum < girlnum:
        msg = f'您的女友没满哦。\n需要达到{girlnum}名女友\n您现在有{cidnum}名。'
        await bot.send(ev, msg, at_sender=True)
        return
    prestige = score_counter._get_prestige(gid, uid)
    needscore = get_noblescore(level + 1)
    futurename = get_noblename(level + 1)
    needWin = get_nobleWin(level + 1)
    needSW = get_noblesw(level + 1)
    if score < needscore:
        msg = f'您的金币不足哦。\n升级到{futurename}需要{needscore}金币'
        await bot.send(ev, msg, at_sender=True)
        return
    if Winnum < needWin:
        msg = f'您的胜场不足哦。\n升级到{futurename}需要{needWin}胜场'
        await bot.send(ev, msg, at_sender=True)
        return
    if level > 5:
        if prestige == None:
            score_counter._set_prestige(gid, uid, 0)
            await bot.finish(ev, '您还未开启声望系统哦，已为您开启！', at_sender=True)

        if prestige < needSW:
            await bot.finish(ev, f'您的声望不足哦。升级到{futurename}需要{needSW}声望', at_sender=True)
        score_counter._reduce_prestige(gid, uid, needSW)
    score_counter._reduce_score(gid, uid, needscore)
    duel._add_level(gid, uid)
    newlevel = duel._get_level(gid, uid)
    newnoblename = get_noblename(newlevel)
    newgirlnum = get_girlnum_buy(gid, uid)
    msg = f'花费了{needscore}金币和{needSW}声望\n您成功由{noblename}升到了{newnoblename}\n可以拥有{newgirlnum}名女友了哦。'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix('贵族决斗')
async def nobleduel(bot, ev: CQEvent):
    if ev.message[0].type == 'at':
        id2 = int(ev.message[0].data['qq'])
    else:
        await bot.finish(ev, '参数格式错误, 请重试')
    if duel_judger.get_on_off_status(ev.group_id):
        await bot.send(ev, "此轮决斗还没结束，请勿重复使用指令。")
        return

    gid = ev.group_id
    duel_judger.turn_on(gid)
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    id1 = ev.user_id
    duel = DuelCounter()
    is_overtime = 0
    prestige = score_counter._get_prestige(gid,id1)
    prestige2 = score_counter._get_prestige(gid,id2)
    level1 = duel._get_level(gid, id1)
    level2 = duel._get_level(gid, id2)
    if id2 == id1:
        await bot.send(ev, "不能和自己决斗！", at_sender=True)
        duel_judger.turn_off(ev.group_id)
        return

    if duel._get_level(gid, id1) == 0:
        msg = f'[CQ:at,qq={id1}]决斗发起者还未在创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id1) == {}:
        msg = f'[CQ:at,qq={id1}]您没有女友，不能参与决斗哦。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return

    if duel._get_level(gid, id2) == 0:
        msg = f'[CQ:at,qq={id2}]被决斗者还未在本群创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id2) == {}:
        msg = f'[CQ:at,qq={id2}]您没有女友，不能参与决斗哦。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    #判定每日上限
    guid = gid ,id1
    if not daily_duel_limiter.check(guid):
        await bot.send(ev, '今天的决斗次数已经超过上限了哦，明天再来吧。', at_sender=True)
        duel_judger.turn_off(ev.group_id)
        return
    daily_duel_limiter.increase(guid)



    # 判定双方的女友是否已经超过上限

    # 这里设定大于才会提醒，就是可以超上限1名，可以自己改成大于等于。
    if girl_outlimit(gid,id1):
        msg = f'[CQ:at,qq={id1}]您的女友超过了爵位上限，本次决斗获胜只能获得金币哦。'
        await bot.send(ev, msg)
    if girl_outlimit(gid,id2):
        msg = f'[CQ:at,qq={id2}]您的女友超过了爵位上限，本次决斗获胜只能获得金币哦。'
        await bot.send(ev, msg)
    duel_judger.init_isaccept(gid)
    duel_judger.set_duelid(gid, id1, id2)
    duel_judger.turn_on_accept(gid)
    msg = f'[CQ:at,qq={id2}]对方向您发起了优雅的贵族决斗，请在{WAIT_TIME}秒内[接受/拒绝]。'

    await bot.send(ev, msg)
    await asyncio.sleep(WAIT_TIME)
    duel_judger.turn_off_accept(gid)
    if duel_judger.get_isaccept(gid) is False:
        msg = '决斗被拒绝。'
        duel_judger.turn_off(gid)
        await bot.send(ev, msg, at_sender=True)
        return
    duel = DuelCounter()
    level1 = duel._get_level(gid, id1)
    noblename1 = get_noblename(level1)
    level2 = duel._get_level(gid, id2)
    noblename2 = get_noblename(level2)
    id1Win = duel._get_WLCWIN(gid,id1)
    id2Win = duel._get_WLCWIN(gid,id2)
    n = duel._get_weapon(gid)
    if n == 6:
        msg = '''目前本群启用的武器是俄罗斯左轮，弹匣量为6\n'''
    elif n == 2:
        msg = '''目前本群启用的武器是贝雷塔687，弹匣量为2\n'''
    elif n == 20:
        msg = '''目前本群启用的武器是Glock，弹匣量为20\n'''
    elif n == 12:
        msg = '''目前本群启用的武器是战术型沙漠之鹰，弹匣量为12\n'''
    elif n == 10:
        msg = '''目前本群启用的武器是巴雷特，弹匣量为10\n'''
    else:
        msg = f'目前本群启用的是自定义武器，弹匣量为{n}\n'
    if duel._get_GOLD_CELE(gid) == 1:
        msg += f'''对方接受了决斗！    
1号：[CQ:at,qq={id1}]
爵位为：{noblename1}
累计胜场:{id1Win}
2号：[CQ:at,qq={id2}]
爵位为：{noblename2}
累计胜场:{id2Win}
其他人请在{DUEL_SUPPORT_TIME}秒选择支持的对象
[庆典举办中]支持成功时，金币的获取量将会变为{Gold_Cele_Num * WIN_NUM}倍！
[支持1/2号xxx金币]'''
    else:
        msg += f'''对方接受了决斗！    
1号：[CQ:at,qq={id1}]
爵位为：{noblename1}
累计胜场:{id1Win}
2号：[CQ:at,qq={id2}]
爵位为：{noblename2}
累计胜场:{id2Win}
其他人请在{DUEL_SUPPORT_TIME}秒选择支持的对象
支持成功时，金币的获取量将会变为{WIN_NUM}倍！
[支持1/2号xxx金币]'''

    await bot.send(ev, msg)
    duel_judger.turn_on_support(gid)
    x = duel._get_weapon(gid) + 1
    deadnum = int(math.floor( random.uniform(1,x) ))
    print ("死的位置是", deadnum)
    duel_judger.set_deadnum(gid, deadnum)
    await asyncio.sleep(DUEL_SUPPORT_TIME)
    duel_judger.turn_off_support(gid)
    duel_judger.init_turn(gid)
    duel_judger.turn_on_fire(gid)
    duel_judger.turn_off_hasfired(gid)
    msg = f'支持环节结束，下面请决斗双方轮流[开枪]。\n[CQ:at,qq={id1}]先开枪，30秒未开枪自动认输'

    await bot.send(ev, msg)
    n = 1
    while (n <= duel._get_weapon(gid)):
        wait_n = 0
        while (wait_n < 30):
            if duel_judger.get_on_off_hasfired_status(gid):
                break

            wait_n += 1
            await asyncio.sleep(1)
        if wait_n >= 30:
            # 超时未开枪的胜负判定
            loser = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
            winner = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
            msg = f'[CQ:at,qq={loser}]\n你明智的选择了认输。'
            await bot.send(ev, msg)

            # 记录本局为超时局。
            is_overtime = 1

            break
        else:
            if n == duel_judger.get_deadnum(gid):
                # 被子弹打到的胜负判定
                loser = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
                winner = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
                msg = f'[CQ:at,qq={loser}]\n砰！你死了。'
                await bot.send(ev, msg)
                break
            else:
                id = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
                id2 = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
                msg = f'[CQ:at,qq={id}]\n砰！松了一口气，你并没有死。\n[CQ:at,qq={id2}]\n轮到你开枪了哦。'
                await bot.send(ev, msg)
                n += 1
                duel_judger.change_turn(gid)
                duel_judger.turn_off_hasfired(gid)
                duel_judger.turn_on_fire(gid)
    score_counter = ScoreCounter2()
    cidlist = duel._get_cards(gid, loser)
    selected_girl = random.choice(cidlist)
    queen = duel._search_queen(gid,loser)
    queen2 = duel._search_queen2(gid,loser)

    CE = CECounter()
    bangdinwin = CE._get_guaji(gid,winner)
    bangdinlose = CE._get_guaji(gid,loser)
    #判断决斗胜利者是否有绑定角色,有则增加经验值
    bd_msg=''
    if bangdinwin:
        bd_info = duel_chara.fromid(bangdinwin)
        card_level=add_exp(gid,winner,bangdinwin,WIN_EXP)
        nvmes = get_nv_icon(bangdinwin)
        bd_msg = f"[CQ:at,qq={winner}]您绑定的女友{bd_info.name}获得了{WIN_EXP}点经验，目前等级为{card_level}\n{nvmes}"
        await bot.send(ev, bd_msg)

    #判定被输掉的是否是复制人可可萝，是则换成金币。
    if selected_girl==9999:
        score_counter._add_score(gid, winner, 300)
        c = duel_chara.fromid(1059)
        nvmes = get_nv_icon(1059)
        duel._delete_card(gid, loser, selected_girl)
        msg = f'[CQ:at,qq={winner}]\n您赢得了神秘的可可萝，但是她微笑着消失了。\n本次决斗获得了300金币。'
        await bot.send(ev, msg)
        msg = f'[CQ:at,qq={loser}]\n您输掉了贵族决斗，被抢走了女友\n{c.name}，\n只要招募，她就还会来到你的身边哦。{nvmes}'
        await bot.send(ev, msg)

    #判断被输掉的是否为妻子。
    elif selected_girl==queen:
        score_counter._add_score(gid, winner, 1000)
        msg = f'[CQ:at,qq={winner}]您赢得的角色为对方的妻子，\n您改为获得1000金币。'
        await bot.send(ev, msg)
        score_counter._reduce_prestige(gid,loser,300)
        msg = f'[CQ:at,qq={loser}]您差点输掉了妻子，额外失去了300声望。'
        await bot.send(ev, msg)

    elif selected_girl==queen2:
        score_counter._add_score(gid, winner, 1000)
        msg = f'[CQ:at,qq={winner}]您赢得的角色为对方的二妻，\n您改为获得1000金币。'
        await bot.send(ev, msg)
        score_counter._reduce_prestige(gid,loser,200)
        msg = f'[CQ:at,qq={loser}]您差点输掉了二妻，额外失去了200声望。'
        await bot.send(ev, msg)
    #判断被输掉的是否为绑定经验获取角色。
    elif selected_girl==bangdinlose:
        score_counter._add_score(gid, winner, 1000)
        msg = f'[CQ:at,qq={winner}]您赢得的角色为对方的绑定女友，\n您改为获得1000金币。'
        await bot.send(ev, msg)
        score_counter._reduce_prestige(gid,loser,500)
        msg = f'[CQ:at,qq={loser}]您差点输掉了绑定女友，额外失去了500声望。'
        await bot.send(ev, msg)


    elif girl_outlimit(gid,winner):
        score_counter._add_score(gid, winner, 1000)
        msg = f'[CQ:at,qq={winner}]您的女友超过了爵位上限，\n本次决斗获得了1000金币。'
        c = duel_chara.fromid(selected_girl)
        #判断好感是否足够，足够则扣掉好感
        favor = duel._get_favor(gid,loser,selected_girl)
        if favor>=favor_reduce:
            c = duel_chara.fromid(selected_girl)
            duel._reduce_favor(gid,loser,selected_girl,favor_reduce)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您与{c.name}的好感下降了50点。\n{c.icon.cqcode}'
            await bot.send(ev, msg)
        else:
            duel._delete_card(gid, loser, selected_girl)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗且对方超过了爵位上限，您的女友恢复了单身。\n{c.name}{c.icon.cqcode}'
            await bot.send(ev, msg)

    else:
        c = duel_chara.fromid(selected_girl)
        #判断好感是否足够，足够则扣掉好感
        favor = duel._get_favor(gid,loser,selected_girl)
        if favor>=favor_reduce:
            duel._reduce_favor(gid,loser,selected_girl,favor_reduce)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您与{c.name}的好感下降了50点。\n{c.icon.cqcode}'
            await bot.send(ev, msg)
            score_counter._add_score(gid, winner, 300)
            msg = f'[CQ:at,qq={winner}]您赢得了决斗，对方女友仍有一定好感。\n本次决斗获得了300金币。'
            await bot.send(ev, msg)
        else:
            c = duel_chara.fromid(selected_girl)
            duel._delete_card(gid, loser, selected_girl)
            duel._add_card(gid, winner, selected_girl)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您被抢走了女友\n{c.name}{c.icon.cqcode}'
            await bot.send(ev, msg)
        #判断赢家的角色列表里是否有复制人可可萝。
            wincidlist = duel._get_cards(gid, winner)
            if 9999 in wincidlist:
                duel._delete_card(gid, winner, 9999)
                score_counter._add_score(gid, winner, 300)
                msg = f'[CQ:at,qq={winner}]\n“主人有了女友已经不再孤单了，我暂时离开了哦。”\n您赢得了{c.name},可可萝微笑着消失了。\n您获得了300金币。'
                await bot.send(ev, msg)

    # 判断胜者败者是否需要增减声望
    level_loser = duel._get_level(gid, loser)
    level_winner = duel._get_level(gid, winner)
    wingold = 800 + (level_loser * 100)
    if is_overtime == 1:
        if n != duel._get_weapon(gid):
            wingold = 100
    score_counter._add_score(gid, winner, wingold)
    msg = f'[CQ:at,qq={winner}]本次决斗胜利获得了{wingold}金币。'
    await bot.send(ev, msg)
    winprestige = score_counter._get_prestige(gid, winner)
    if winprestige == None:
        winprestige == 0
    if winprestige != None:
        level_cha = level_loser - level_winner
        level_zcha = max(level_cha, 0)
        winSW = WinSWBasics + (level_zcha * 20)
        if is_overtime == 1:
            if n != duel._get_weapon(gid):
                if level_loser < 6:
                    winSW = 0
                else:
                    winSW = 150
        score_counter._add_prestige(gid, winner, winSW)
        msg = f'[CQ:at,qq={winner}]决斗胜利使您的声望上升了{winSW}点。'
        await bot.send(ev, msg)
    loseprestige = score_counter._get_prestige(gid, loser)
    if loseprestige == -1:
        loseprestige == 0
    if loseprestige != -1:
        level_cha = level_loser - level_winner
        level_zcha = max(level_cha, 0)
        LOSESW = LoseSWBasics + (level_zcha * 10)
        score_counter._reduce_prestige(gid, loser, LOSESW)
        msg = f'[CQ:at,qq={loser}]决斗失败使您的声望下降了{LOSESW}点。'
        await bot.send(ev, msg)

    # 判定败者是否掉爵位，皇帝不会因为决斗掉爵位。
    level_loser = duel._get_level(gid, loser)
    if level_loser > 1 and level_loser < Safe_LV:
        noblename_loser = get_noblename(level_loser)
        girlnum_loser = get_girlnum(level_loser - 1)
        cidlist_loser = duel._get_cards(gid, loser)
        cidnum_loser = len(cidlist_loser)
        if cidnum_loser < girlnum_loser:
            duel._reduce_level(gid, loser)
            new_noblename = get_noblename(level_loser - 1)
            msg = f'[CQ:at,qq={loser}]\n您的女友数为{cidnum_loser}名\n小于爵位需要的女友数{girlnum_loser}名\n您的爵位下降到了{new_noblename}'
            await bot.send(ev, msg)
    # 结算负场
    duel._add_Lose(gid, loser)
    # 结算下注金币，判定是否为超时局。

    if is_overtime == 1:
        if n != duel._get_weapon(gid):
            if level_loser < 6:
                msg = '认输警告！本局为超时局/认输局，不进行金币结算，支持的金币全部返还。胜者获得的声望为0，金币大幅减少。'
            else:
                msg = '认输警告！本局为超时局/认输局，不进行金币结算，支持的金币全部返还。胜者获得的声望减半，金币大幅减少，不计等级差。'
            await bot.send(ev, msg)
            duel._add_ADMIT(gid, loser)
            duel_judger.set_support(ev.group_id)
            duel_judger.turn_off(ev.group_id)
            return

    support = duel_judger.get_support(gid)
    # 结算胜场，避免超时局刷胜场
    duel._add_Win(gid, winner)
    winuid = []
    supportmsg = '金币结算:\n'
    winnum = duel_judger.get_duelnum(gid, winner)

    if support != 0:
        for uid in support:
            support_id = support[uid][0]
            support_score = support[uid][1]
            if support_id == winnum:
                winuid.append(uid)
                # 这里是赢家获得的金币结算，可以自己修改倍率。
                if duel._get_GOLD_CELE(gid) == 1:
                    winscore = support_score * WIN_NUM * Gold_Cele_Num
                else:
                    winscore = support_score * WIN_NUM
                score_counter._add_score(gid, uid, winscore)
                supportmsg += f'[CQ:at,qq={uid}]+{winscore}金币\n'
            else:
                score_counter._reduce_score(gid, uid, support_score)
                supportmsg += f'[CQ:at,qq={uid}]-{support_score}金币\n'
    await bot.send(ev, supportmsg)
    duel_judger.set_support(ev.group_id)
    duel_judger.turn_off(ev.group_id)
    return

@sv.on_fullmatch('接受')
async def duelaccept(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_accept_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[1]:
            gid = ev.group_id
            msg = '贵族决斗接受成功，请耐心等待决斗开始。'
            await bot.send(ev, msg, at_sender=True)
            duel_judger.turn_off_accept(gid)
            duel_judger.on_isaccept(gid)
        else:
            print('不是被决斗者')
    else:
        print('现在不在决斗期间')

@sv.on_fullmatch('拒绝')
async def duelrefuse(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_accept_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[1]:
            gid = ev.group_id
            msg = '您已拒绝贵族决斗。'
            await bot.send(ev, msg, at_sender=True)
            duel_judger.turn_off_accept(gid)
            duel_judger.off_isaccept(gid)

@sv.on_fullmatch('开枪')
async def duelfire(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_fire_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]:
            duel_judger.turn_on_hasfired(gid)
            duel_judger.turn_off_fire(gid)

@sv.on_rex(r'^支持(1|2)号(\d+)(金币|币)$')
async def on_input_duel_score(bot, ev: CQEvent):
    try:
        if duel_judger.get_on_off_support_status(ev.group_id):
            gid = ev.group_id
            uid = ev.user_id

            match = ev['match']
            select_id = int(match.group(1))
            input_score = int(match.group(2))
            score_counter = ScoreCounter2()
            # 若下注该群下注字典不存在则创建
            if duel_judger.get_support(gid) == 0:
                duel_judger.set_support(gid)
            support = duel_judger.get_support(gid)
            # 检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
            # 检查是否是决斗人员
            duellist = duel_judger.get_duelid(gid)
            if uid in duellist and Su_us != True:
                msg = '决斗参与者不能支持。'
                await bot.send(ev, msg, at_sender=True)
                return
            if input_score > 30000:
                msg = '每次支持金币不能超过3万。'
                await bot.send(ev, msg, at_sender=True)
                return
            # 检查金币是否足够下注
            if score_counter._judge_score(gid, uid, input_score) == 0:
                msg = '您的金币不足。'
                await bot.send(ev, msg, at_sender=True)
                return
            else:
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'支持{select_id}号成功。'
                await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

@sv.on_rex(r'^梭哈支持(1|2)号$')
async def on_input_duel_score2(bot, ev: CQEvent):
    try:
        if duel_judger.get_on_off_support_status(ev.group_id):
            gid = ev.group_id
            duel = DuelCounter()
            uid = ev.user_id
            if Suo_allow != True:
                msg = '管理员禁止梭哈。'
                await bot.send(ev, msg, at_sender=True)
                return
            score_counter = ScoreCounter2()
            match = ev['match']
            select_id = int(match.group(1))
            current_score = score_counter._get_score(gid, uid)
            input_score = current_score
            score_counter = ScoreCounter2()
            # 若下注该群下注字典不存在则创建
            if duel_judger.get_support(gid) == 0:
                duel_judger.set_support(gid)
            support = duel_judger.get_support(gid)
            # 检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
            # 检查是否是决斗人员
            duellist = duel_judger.get_duelid(gid)
            if uid in duellist and Su_us2 != True:
                msg = '决斗参与者不能支持。'
                await bot.send(ev, msg, at_sender=True)
                return
            if current_score>30000:
                msg = '您的金币大于3万，不能梭哈支持。'
                await bot.send(ev, msg, at_sender=True)
                return
            # 检查金币是否足够下注
            if score_counter._judge_score(gid, uid, input_score) == 0:
                msg = '您的金币不足。'
                await bot.send(ev, msg, at_sender=True)
                return
            else:
             if duel._get_SUO_CELE(gid) == 1:
                input_score =  Suo * current_score * Suo_Cele_Num
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'梭哈支持{select_id}号{current_score}金币成功，[庆典举办中]胜利时，将获得相对于平常值{Suo*Suo_Cele_Num}倍的金币！'
                await bot.send(ev, msg, at_sender=True)
             else:
                input_score =  Suo * current_score
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'梭哈支持{select_id}号{current_score}金币成功，胜利时，将获得相对于平常值{Suo}倍的金币！'
                await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

# 以下部分与赛跑的重合，有一个即可，两个插件都装建议注释掉。
@sv.on_prefix(['领金币', '领取金币'])
async def add_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter2()
        gid = ev.group_id
        uid = ev.user_id

        current_score = score_counter._get_score(gid, uid)
        if current_score == 0:
            score_counter._add_score(gid, uid, ZERO_GET_AMOUNT)
            msg = f'您已领取{ZERO_GET_AMOUNT}金币'
            await bot.send(ev, msg, at_sender=True)
            return
        else:
            msg = '金币为0才能领取哦。'
            await bot.send(ev, msg, at_sender=True)
            return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

@sv.on_prefix(['查金币', '查询金币', '查看金币','我的金币'])
async def get_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter2()
        gid = ev.group_id
        uid = ev.user_id

        current_score = score_counter._get_score(gid, uid)
        msg = f'您的金币为{current_score}'
        await bot.send(ev, msg, at_sender=True)
        return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

@sv.on_rex(f'^为(.*)充值(\d+)金币$')
async def cheat_score(bot, ev: CQEvent):
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
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    score_counter._add_score(gid, id, num)
    score = score_counter._get_score(gid, id)
    msg = f'已为[CQ:at,qq={id}]充值{num}金币。\n现在共有{score}金币。'
    await bot.send(ev, msg)

@sv.on_rex(f'^为(.*)转账(\d+)金币$')
async def cheat_score(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
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
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    if duel._get_level(gid, id) < 7:
        await bot.finish(ev, '该用户等级过低，无法接受转账喔（接受转账需要等级达到伯爵）。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < num:
        msg = f'您的金币不足{num}哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        score_counter._reduce_score(gid, uid, num)
        scoreyou = score_counter._get_score(gid, uid)
        num2 = num * (1-Zhuan_Need)
        score_counter._add_score(gid, id, num2)
        score = score_counter._get_score(gid, id)
        msg = f'已为[CQ:at,qq={id}]转账{num}金币。\n扣除{Zhuan_Need*100}%手续费，您的金币剩余{scoreyou}金币，对方金币剩余{score}金币。'
        await bot.send(ev, msg)

@sv.on_fullmatch('重置决斗')
async def init_duel(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置决斗哦。', at_sender=True)
    duel_judger.turn_off(ev.group_id)
    msg = '已重置本群决斗状态！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['查女友', '查询女友', '查看女友'])
async def search_girl(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    if not args:
        await bot.send(ev, '请输入查女友+pcr角色名。', at_sender=True)
        return
    name = args[0]
    cid = duel_chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    duel = DuelCounter()
    owner = duel._get_card_owner(gid, cid)
    c = duel_chara.fromid(cid)
    #判断是否是妻子。
    nvmes = get_nv_icon(cid)
    lh_msg = ''
    jishu=0
    if duel._get_queen_owner(gid,cid) !=0 :
        owner = duel._get_queen_owner(gid,cid)
        await bot.finish(ev, f'\n{c.name}现在是\n[CQ:at,qq={owner}]的妻子哦。{nvmes}{lh_msg}', at_sender=True)

    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}{lh_msg}', at_sender=True)
        return
    else:
        store_flag = duel._get_store(gid, owner, cid)
        if store_flag>0:
            msg = f'{c.name}现在正在以{store_flag}金币的价格寄售中哦\n寄售人为[CQ:at,qq={owner}]哦。{nvmes}{lh_msg}'
        else:
            msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦。{nvmes}{lh_msg}'
        await bot.send(ev, msg)

#重置某一用户的金币，只用做必要时删库用。
@sv.on_prefix('重置金币')
async def reset_score(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能使用重置金币功能哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>=2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入重置金币+被重置者QQ', at_sender=True)
    else :
        id = args[0]
        duel = DuelCounter()
        if duel._get_level(gid, id) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        score_counter = ScoreCounter2()    
        current_score = score_counter._get_score(gid, id)
        score_counter._reduce_score(gid, id,current_score)
        await bot.finish(ev, f'已清空用户{id}的金币。', at_sender=True)
        
#注意会清空此人的角色以及贵族等级，只用做必要时删库用。 
@sv.on_prefix('重置角色')
async def reset_chara(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能使用重置角色功能哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>=2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入重置角色+被重置者QQ', at_sender=True)
    else :
        id = args[0]
        duel = DuelCounter()
        if duel._get_level(gid, id) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        cidlist = duel._get_cards(gid, id)
        for cid in cidlist:
            duel._delete_card(gid, id, cid)
        score_counter = ScoreCounter2()    
        current_score = score_counter._get_score(gid, id)
        score_counter._reduce_score(gid, id,current_score)
        queen = duel._search_queen(gid,id)
        duel._delete_queen_owner(gid,queen)
        duel._set_level(gid, id, 0)    
        await bot.finish(ev, f'已清空用户{id}的女友和贵族等级。', at_sender=True)

@sv.on_prefix('确认重开')
async def reset_CK(bot, ev: CQEvent):
        gid = ev.group_id
        uid = ev.user_id
        guid = gid, uid
        if Remake_allow == False:
         await bot.finish(ev, '管理员不允许自行重开。', at_sender=True)
        if not daily_Remake_limiter.check(guid):
            await bot.send(ev, '一天最多重开一次！', at_sender=True)
            return
        duel = DuelCounter()
        score_counter = ScoreCounter2()
        prestige = score_counter._get_prestige(gid,uid)
        if prestige < 0:
            await bot.finish(ev, '您现在身败名裂（声望为负），无法重开！请联系管理员重开！', at_sender=True)
        if duel._get_level(gid, uid) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        cidlist = duel._get_cards(gid, uid)
        for cid in cidlist:
            duel._delete_card(gid, uid, cid)
        score_counter = ScoreCounter2()
        current_score = score_counter._get_score(gid, uid)
        score_counter._reduce_score(gid, uid,current_score)
        queen = duel._search_queen(gid,uid)
        queen2 = duel._search_queen2(gid,uid)
        duel._delete_queen_owner(gid,queen)
        duel._delete_queen2_owner(gid,queen2)
        duel._clear_uniequip(gid,uid)
        duel._set_level(gid, uid, 0)
        score_counter._set_prestige(gid,uid,0)
        daily_Remake_limiter.increase(guid)
        duel._WLC_Remake(gid,uid)
        i = 0
        while(i<=10):
            while(duel._get_gift_num(gid,uid,i)!=0):
                duel._reduce_gift(gid,uid,i)
            i += 1
        await bot.finish(ev, f'已清空您的女友和贵族等级，金币等。', at_sender=True)

@sv.on_prefix('分手')
async def breakup(bot, ev: CQEvent):
    if BREAK_UP_SWITCH == True:
        args = ev.message.extract_plain_text().split()
        gid = ev.group_id
        uid = ev.user_id
        duel = DuelCounter()
        level = duel._get_level(gid, uid)
        if duel_judger.get_on_off_status(ev.group_id):
                msg = '现在正在决斗中哦，请决斗后再来谈分手事宜吧。'
                await bot.finish(ev, msg, at_sender=True)
        if level == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        if not args:
            await bot.finish(ev, '请输入分手+pcr角色名。', at_sender=True)
        name = args[0]
        cid = duel_chara.name2id(name)
        if cid == 1000:
            await bot.finish(ev, '请输入正确的pcr角色名。', at_sender=True)
        score_counter = ScoreCounter2()
        needscore = 400+level*100
        needSW = 100+level*15
        if level == 20:
            needSW = 600
        score = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        cidlist = duel._get_cards(gid, uid)
        if cid not in cidlist:
            await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)
        #检测是否是妻子
        queen = duel._search_queen(gid,uid)
        if cid==queen:
            await bot.finish(ev, '不可以和您的妻子分手哦。', at_sender=True)
        if score < needscore:
            msg = f'您的爵位分手一位女友需要{needscore}金币和{needSW}声望哦。\n分手不易，做好准备再来吧。'
            await bot.finish(ev, msg, at_sender=True)
        if prestige < needSW:
            msg = f'您的爵位分手一位女友需要{needscore}金币和{needSW}声望哦。\n分手不易，做好准备再来吧。'
            await bot.finish(ev, msg, at_sender=True)
        score_counter._reduce_score(gid, uid, needscore)
        score_counter._reduce_prestige(gid, uid, needSW)
        duel._delete_card(gid, uid, cid)
        c = duel_chara.fromid(cid)
        msg = f'\n“真正离开的那次，关门声最小。”\n你和{c.name}分手了。失去了{needscore}金币分手费,声望减少了{needSW}。\n{c.icon.cqcode}'
        await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(('金币排行榜', '金币排行'))
async def Race_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = score_counter._get_score(gid, uid)
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族决斗金币排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 金币: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))        
        
@sv.on_fullmatch(('声望排行榜', '声望排行'))
async def SW_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = score_counter._get_prestige(gid, uid)
                if score_dict[user_card_dict[uid]] == None:
                   score_dict[user_card_dict[uid]] = 0
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决声望排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 声望: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))      

@sv.on_fullmatch(('女友排行榜', '女友排行'))
async def SW_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        duel = DuelCounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                cidlist = duel._get_cards(gid, uid)
                score_dict[user_card_dict[uid]] = cidnum = len(cidlist)
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决女友数排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 女友数: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))     

@sv.on_fullmatch(('查询庆典','庆典状况','当前庆典'))
async def GET_Cele(bot, ev: CQEvent):
   duel = DuelCounter()
   gid = ev.group_id
   if Show_Cele_Not == True:
    if duel._get_GOLD_CELE(gid) == 1:
       msg = f'\n当前正举办押注金币庆典，当支持成功时，获得的金币将变为原来的{Gold_Cele_Num}倍\n'
    else:
       msg = f'\n当前未举办金币庆典\n'
    if duel._get_QC_CELE(gid) == 1:
       msg += f'当前正举办贵族签到庆典，签到时获取的声望将变为{QD_SW_Cele_Num}倍，金币将变为{QD_Gold_Cele_Num}倍\n'
    else:
       msg += f'当前未举办签到庆典\n'
    if duel._get_SUO_CELE(gid) == 1:
       msg += f'当前正举办梭哈倍率庆典，梭哈时的倍率将额外提升{Suo_Cele_Num}倍\n'
    else:
       msg += f'当前未举办梭哈倍率庆典\n'
    if duel._get_FREE_CELE(gid) == 1:
       msg += f'当前正举办免费招募庆典，每日可免费招募{FREE_DAILY_LIMIT}次\n'
    else:
       msg += f'当前未举办免费招募庆典\n'
    if duel._get_SW_CELE(gid) == 1:
       msg += f'当前正举办限时开启声望招募庆典'
    else:
       msg += f'当前未举办限时开启声望招募庆典'
    await bot.send(ev, msg, at_sender=True)
   else:   
    if duel._get_GOLD_CELE(gid) == 1:
       msg = f'\n当前正举办押注金币庆典，当支持成功时，获得的金币将变为原来的{Gold_Cele_Num}倍\n'
    else:
       msg = f'\n'
    if duel._get_QC_CELE(gid) == 1:
       msg += f'当前正举办贵族签到庆典，签到时获取的声望将变为{QD_SW_Cele_Num}倍，金币将变为{QD_Gold_Cele_Num}倍\n'
    if duel._get_SUO_CELE(gid) == 1:
       msg += f'当前正举办梭哈倍率庆典，梭哈时的倍率将额外提升{Suo_Cele_Num}倍\n'
    if duel._get_FREE_CELE(gid) == 1:
       msg += f'当前正举办免费招募庆典，每日可免费招募{FREE_DAILY_LIMIT}次\n'
    if duel._get_SW_CELE(gid) == 1:
       msg += f'当前正举办限时开启声望招募庆典'
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_rex(r'^开启本群(金币|签到|梭哈倍率|免费招募|声望招募)庆典$')
async def ON_Cele_SWITCH(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权开放庆典！', at_sender=True)
    duel = DuelCounter()
    if duel._get_SW_CELE(gid) == None:
        await bot.finish(ev, '本群庆典未初始化，请先发"初始化本群庆典"初始化数据！', at_sender=True)
    match = (ev['match'])
    cele = (match.group(1))
    if cele == '金币':
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,1,QC_Data,SUO_Data,SW_Data,FREE_Data)
        msg = f'已开启本群金币庆典，当支持成功时，获得的金币将变为原来的{Gold_Cele_Num}倍\n'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '签到':
        GC_Data = duel._get_GOLD_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,1,SUO_Data,SW_Data,FREE_Data)
        msg = f'已开启本群贵族签到庆典，签到时获取的声望将变为{QD_SW_Cele_Num}倍，金币将变为{QD_Gold_Cele_Num}倍\n'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '梭哈倍率':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,1,SW_Data,FREE_Data)
        msg = f'已开启本群梭哈倍率庆典，梭哈时的倍率将额外提升{Suo_Cele_Num}倍\n'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '免费招募':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,SUO_Data,SW_Data,1)
        msg = f'已开启本群免费招募庆典，每日可免费招募{FREE_DAILY_LIMIT}次\n'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '声望招募':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,SUO_Data,1,FREE_Data)
        msg = f'已开启本群限时开启声望招募庆典\n'
        await bot.send(ev, msg, at_sender=True)
        return
    msg = f'庆典名匹配出错！请输入金币/签到/梭哈/免费招募/声望招募庆典中的一个！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex(r'^关闭本群(金币|签到|梭哈倍率|免费招募|声望招募)庆典$')
async def OFF_Cele_SWITCH(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权开放庆典！', at_sender=True)
    match = (ev['match'])
    cele = (match.group(1))
    duel = DuelCounter()
    if duel._get_SW_CELE(gid) == None:
        await bot.finish(ev, '本群庆典未初始化，请先发"初始化本群庆典"初始化数据！', at_sender=True)
    if cele == '金币':
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,0,QC_Data,SUO_Data,SW_Data,FREE_Data)
        msg = f'\n已关闭本群金币庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '签到':
        GC_Data = duel._get_GOLD_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,0,SUO_Data,SW_Data,FREE_Data)
        msg = f'\n已关闭本群贵族签到庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '梭哈倍率':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,0,SW_Data,FREE_Data)
        msg = f'\n已关闭本群梭哈倍率庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '免费招募':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,SUO_Data,SW_Data,0)
        msg = f'\n已关闭本群免费招募庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '声望招募':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,SUO_Data,0,FREE_Data)
        msg = f'\n已关闭本群限时声望招募庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    msg = f'庆典名匹配出错！请输入金币/签到/梭哈/免费招募/声望招募庆典中的一个！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('初始化本群庆典')
async def initialization(bot, ev: CQEvent):
    uid = ev.user_id
    gid = ev.group_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权初始化庆典！', at_sender=True)
    duel = DuelCounter()
    duel._initialization_CELE(gid,Gold_Cele,QD_Cele,Suo_Cele,SW_add,FREE_DAILY)
    msg = f'已成功初始化本群庆典！\n您可发送查询庆典来查看本群庆典情况！\n'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('胜场修改')
async def chat_Win(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权修改胜场！', at_sender=True)
    duel._chat_Win(gid, uid)
    await bot.finish(ev, '已将您的胜场修改为999！', at_sender=True)