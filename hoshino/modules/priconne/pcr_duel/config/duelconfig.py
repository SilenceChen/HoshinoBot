import asyncio
import base64
import os
import random
import sqlite3
import math
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from hoshino import Service, priv
from hoshino.modules.priconne import _pcr_data
from ..data import _dlc_data
from ..data import duel_chara
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
import copy
import json
import hoshino
from ..counter.CECounter import *
from ..counter.ScoreCounter import *
from ..counter.DuelCounter import *

DUEL_DB_PATH = os.path.expanduser('~/.hoshino/pcr_duel.db')
SCORE_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
BLACKLIST_ID = [1000, 1072, 4031, 9000, 1069, 1073,1900,1907,1910,1913,1914,1915,1916,1917,1919,9601,9602,9603,9604] # 黑名单ID
WAIT_TIME = 30 # 对战接受等待时间
WAIT_TIME_jy = 30 # 交易接受等待时间
DUEL_SUPPORT_TIME = 30 # 赌钱等待时间
DB_PATH = os.path.expanduser("~/.hoshino/pcr_duel.db")

#这里是参数设置区
SIGN_DAILY_LIMIT = 1  # 机器人每天签到的次数
DUEL_DAILY_LIMIT = 5 #每个人每日发起决斗上限
RESET_HOUR = 0  # 每日使用次数的重置时间，0代表凌晨0点，1代表凌晨1点，以此类推
GACHA_COST = 500  # 抽老婆需求
GACHA_COST_Fail = 200 #抽老婆失败补偿量
ZERO_GET_AMOUNT = 150  # 没钱补给量
WIN_NUM = 2 #下注获胜赢得的倍率
WIN_EXP = 100 #决斗胜利获得经验
SHANGXIAN_NUM = 100000 #增加女友上限所需金币
WAREHOUSE_NUM = 10 #仓库增加上限
SHANGXIAN_SW = 500 #扩充女友上限，需要的声望值
#签到部分
scoreLV = 400 #每日根据等级获得的金币（等级*参数）
SWLV = 50 #每日根据等级获得的声望（等级*参数）

BREAK_UP_SWITCH = True #分手系统开关
Zhuan_Need = 0.2 #转账所需的手续费比例
WinSWBasics = 400 #赢了获得的基础声望
LoseSWBasics = 150 #输了掉的基础声望

Remake_allow = True #是否允许重开
Remake_LIMIT = 1 #一天最多允许重开的次数

SW_COST = 500 #声望招募的声望需求量
DJ_NEED_SW = 2500 #加冕称帝消耗的声望
DJ_NEED_GOLD = 20000 #加冕称帝消耗的金币
FS_NEED_SW = 4000 #飞升所需的声望
FS_NEED_GOLD = 30000 #飞升所需的金币
DATE_DAILY_LIMIT = 2 #每天女友约会次数上限
GIFT_DAILY_LIMIT = 10 #每日购买礼物次数上限
WAIT_TIME_CHANGE = 15 #礼物交换等待时间

RECYCLE_DAILY_LIMIT = 20 #每日可以回收的次数

#第一名妻子部分
NEED_favor = 100 #成为妻子所需要的好感，为0表示关闭
favor_reduce = 50 #当输掉女友时，损失的好感度
marry_NEED_Gold = 30000 #结婚所需要的金币
marry_NEED_SW = 1000 #结婚所需的声望
#第二名妻子部分
Allow_wife2 = True #是否允许第二名妻子
NEED2_favor = 100 #成为第二名妻子所需要的好感，为0表示关闭
marry2_NEED_Gold = 30000 #结婚所需要的金币
marry2_NEED_SW = 1000 #结婚所需的声望

JB2SW_RATE = 100
SW2JB_RATE = 50

Suo_allow = True #是否允许梭哈
Suo = 2 #梭哈额外获取的金币倍率

Su_us = False #是否允许支持自己
Su_us2 = False #梭哈时，是否允许支持自己（与上个选项独立）
Safe_LV = 8 #不会再掉级的等级

#这里是庆典设置区 ~~开关类，1为开，0为关~~
Show_Cele_Not = True #查询庆典时，显示未开放的庆典
#金币庆典
Gold_Cele = 1 #群庆典初始化时，是否开启金币庆典
Gold_Cele_Num = 2 #金币庆典倍率，实际获得金币倍率为金币庆典倍率*基础倍率
#贵族签到庆典
QD_Cele = 1 #群庆典初始化时，是否开启贵族签到庆典
QD_Gold_Cele_Num = 3 #签到庆典金币倍率
QD_SW_Cele_Num = 2 #签到庆典声望倍率
#梭哈庆典
Suo_Cele = 1 #群庆典初始化时，是否开启梭哈倍率庆典
Suo_Cele_Num = 1 #梭哈额外倍率，实际获得梭哈倍率为梭哈庆典倍率*基础倍率
#免费招募庆典
FREE_DAILY = 1 #群庆典初始化时，是否开启免费招募庆典
FREE_DAILY_LIMIT = 1  # 每天免费招募的次数
#限时开放声望招募
SW_add = 0 #群庆典初始化时，是否开启无限制等级声望招募

FULLCARD_PATH = os.path.join(os.path.expanduser(hoshino.config.RES_DIR), 'img', 'priconne', 'fullcard')

NAME_DICT = {
        "1": "平民",
        "2": "骑士",
        "3": "准男爵",
        "4": "男爵",
        "5": "子爵",
        "6": "伯爵",
        "7": "侯爵",
        "8": "公爵",
        "9": "国王",
        "10": "皇帝",
        "20": "已成神"
    }

LEVEL_GIRL_NEED = {
        "1": 2,
        "2": 3,
        "3": 4,
        "4": 6,
        "5": 8,
        "6": 10,
        "7": 11,
        "8": 13,
        "9": 15,
        "10": 16,
        "20": 20
    } # 升级所需要的老婆，格式为["等级“: 需求]
LEVEL_COST_DICT = {
        "1": 0,
        "2": 100,
        "3": 300,
        "4": 500,
        "5": 1000,
        "6": 3000,
        "7": 5000,
        "8": 10000,
        "9": 15000,
        "10": DJ_NEED_GOLD
    } # 升级所需要的钱钱，格式为["等级“: 需求]
LEVEL_SW_NEED = {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 0,
        "7": 1000,
        "8": 1500,
        "9": 2000,
        "10": DJ_NEED_SW
    } # 升级所需要的声望，格式为["等级“: 需求]
LEVEL_WIN_NEED = {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 0,
        "7": 1,
        "8": 2,
        "9": 5,
        "10": 7
    } # 升级所需要的胜场，格式为["等级“: 需求]
RELATIONSHIP_DICT = {
        0:["初见","浣花溪上见卿卿，脸波明，黛眉轻。"],
        30:["相识","有美一人，清扬婉兮。邂逅相遇，适我愿兮。"],
        60:["熟悉","夕阳谁唤下楼梯，一握香荑。回头忍笑阶前立，总无语，也依依。"],
        100:["朋友","锦幄初温，兽烟不断，相对坐调笙。"],
        150:["朦胧","和羞走，倚门回首，却把青梅嗅。"],
        200:["喜欢","夜月一帘幽梦，春风十里柔情。"],
        300:["依恋","愿我如星君如月，夜夜流光相皎洁。"],
        500:["挚爱","江山看不尽，最美镜中人。"]
    }       

GIFT_DICT = {
        "玩偶"    :0,
        "礼服"    :1,
        "歌剧门票":2,
        "水晶球"  :3,
        "耳环"    :4,
        "发饰"    :5,
        "小裙子"  :6,
        "热牛奶"  :7,
        "书"      :8,
        "鲜花"    :9  
    }  

GIFTCHOICE_DICT={
        0:[0,2,1],
        1:[1,0,2],
        2:[2,1,0],
}    




Gift10=[
    "这个真的可以送给我吗，谢谢(害羞的低下了头)。",
    "你是专门为我准备的吗，你怎么知道我喜欢这个呀，谢谢你！",
    "啊，我最喜欢这个，真的谢谢你。"
]

Gift5=[
    "谢谢送我这个，我很开心。",
    "这个我很喜欢，谢谢。",
    "你的礼物我都很喜欢哦，谢谢。"
]

Gift2=[
    "送我的吗，谢谢你。",
    "谢谢你的礼物。",
    "为我准备了礼物吗，谢谢。"    
]

Gift1=[
    "不用为我特意准备礼物啦，不过还是谢谢你哦。",
    "嗯，谢谢。",
    "嗯，我收下了，谢谢你。"
]




Addgirlfail = [
    '你参加了一场贵族舞会，热闹的舞会场今天竟然没人同你跳舞。',
    '你邀请到了心仪的女友跳舞，可是跳舞时却踩掉了她的鞋，她生气的离开了。',
    '你为这次舞会准备了很久，结果一不小心在桌子上睡着了，醒来时只看到了过期的邀请函。',
    '你参加了一场贵族舞会，可是舞会上只有一名男性向你一直眨眼。',
    '你准备参加一场贵族舞会，可惜因为忘记穿礼服，被拦在了门外。',
    '你沉浸在舞会的美食之中，忘了此行的目的。',
    '你本准备参加舞会，却被会长拉去出了一晚上刀。',
    '舞会上你和另一个贵族发生了争吵，你一拳打破了他的鼻子，两人都被请出了舞会。',
    '舞会上你很快约到了一名女伴跳舞，但是她不是你喜欢的类型。',
    '你约到了一位心仪的女伴，但是她拒绝了与你回家，说想再给你一个考验。',
    '你和另一位贵族同时看中了一个女孩，但是在三人交谈时，你渐渐的失去了话题。'
]
Addgirlsuccess = [
    '你参加了一场贵族舞会，你优雅的舞姿让每位年轻女孩都望向了你。',
    '你参加了一场贵族舞会，你的帅气使你成为了舞会的宠儿。',
    '你在舞会门口就遇到了一位女孩，你挽着她的手走进了舞会。',
    '你在舞会的闲聊中无意中谈到了自己显赫的家室，你成为了舞会的宠儿。',
    '没有人比你更懂舞会，每一个女孩都为你的风度倾倒。',
    '舞会上你没有约到女伴，但是舞会后却有个女孩偷偷跟着你回了家。',
    '舞会上你和另一个贵族发生了争吵，一位女孩站出来为你撑腰，你第一次的注意到了这个可爱的女孩。',
    '你强壮的体魄让女孩们赞叹不已，她们纷纷来问你是不是一位军官。',
    '你擅长在舞会上温柔地对待每一个人，女孩们也向你投来了爱意。',
    '一个可爱的女孩一直在舞会上望着你，你犹豫了一会，向她发出了邀请。'
  
]

Login100 =[
    '今天是练习击剑的一天，不过你感觉你的剑法毫无提升。',
    '优雅的贵族从不晚起，可是你今天一直睡到了中午。',
    '今天你点了一份豪华的午餐却忘记了带钱，窘迫的你毫无贵族的姿态。',
    '今天你在路上看上了别人的女友，却没有鼓起勇气向他决斗。',
    '今天你十分抑郁，因为发现自己最近上升的只有体重。'

]

Login200 =[
    '今天是练习击剑的一天，你感觉到了你的剑法有所提升。',
    '早起的你站在镜子前许久，天底下竟然有人可以这么帅气。',
    '今天你搞到了一瓶不错的红酒，你的酒窖又多了一件存货。',
    '今天巡视领地时，一个小孩子崇拜地望着你，你感觉十分开心。',
    '今天一个朋友送你一张音乐会的门票，你打算邀请你的女友同去。',
    '今天一位国王的女友在路上向你抛媚眼，也许这就是个人魅力吧。'
    
]


Login300 =[
    '今天是练习击剑的一天，你感觉到了你的剑法大有长进。',
    '今天你救下了一个落水的小孩，他的家人说什么也要你收下一份心意。',
    '今天你巡视领地时，听到几个小女孩说想长大嫁给帅气的领主，你心里高兴极了。',
    '今天你打猎时猎到了一只鹿，你骄傲的把鹿角加入了收藏。',
    '今天你得到了一匹不错的马，说不定可以送去比赛。'
    
]

Login600 =[
    '今天是练习击剑的一天，你觉得自己已经可谓是当世剑圣。',
    '今天你因为领地治理有方，获得了皇帝的嘉奖。',
    '今天你的一位叔叔去世了，无儿无女的他，留给了你一大笔遗产。',
    '今天你在比武大会上获得了优胜，获得了全场的喝彩。',
    '今天你名下的马夺得了赛马的冠军，你感到无比的自豪。'
    
    
]

Date5 =[
    '你比约会的时间晚到了十分钟，嘟着嘴的她看起来不太满意。',
    '一向善于言辞的你，今天的约会却不时冷场，她看起来不是很开心。',
    '今天的约会上你频频打哈欠，被她瞪了好几次，早知道昨晚不该晚睡的。',
    '“为您旁边的这个姐姐买朵花吧。”你们被卖花的男孩拦下，你本想买花却发现自己忘记了带钱，她看起来不是很开心。'
]

Date10 =[
    '你带她去熟悉的餐厅吃饭，她觉得今天过得很开心。',
    '你带她去看了一场马术表演，并约她找机会一起骑马出去，她愉快的答应了。',
    '“为您旁边的这个姐姐买朵花吧。”你们被卖花的男孩拦下，你买了一束花还给了小孩一笔小费，你的女友看起来很开心。',
    '你邀请她去看一场歌剧，歌剧中她不时微笑，看起来十分开心。'
]

Date15 =[
    '你和她一同骑马出行，两个人一同去了很多地方，度过了愉快的一天。',
    '你新定做了一件最新款的礼服，约会中她称赞你比往常更加帅气。',
    '你邀请她共赴一场宴会，宴会上你们无所不谈，彼此间的了解增加了。',
    '你邀请她去看一场歌剧，歌剧中她一直轻轻地握着你的手。'  
]

Date20 =[
    '你邀请她共赴一场宴会，宴会中她亲吻了你的脸颊后，害羞的低下了头，这必然是你和她难忘的一天。',
    '约会中你们被一群暴民劫路，你为了保护她手臂受了伤。之后她心疼的抱住了你，并为你包扎了伤口。',
    '你邀请她去看你的赛马比赛，你骑着爱马轻松了夺取了第一名，冲过终点后，你大声地向着看台喊出了她的名字，她红着脸低下了头。',
    '你和她共同参加了一场盛大的舞会，两人的舞步轻盈而优雅，被评为了舞会第一名，上台时你注视着微笑的她，觉得她今天真是美极了。'
]
## 战力系统
MAX_UNIEQUIP_LEVEL = 30
LEVEL_EQUIP_NEED = {
        1: [5,2000],
        2: [10,4000],
        3: [15,6000],
        4: [20,8000],
        5: [25,10000],
        6: [30,12000],
        7: [35,14000],
        8: [40,16000],
        9: [45,18000],
        10: [50,20000],
        11: [50,20000],
        12: [50,20000],
        13: [50,20000],
        14: [50,20000],
        15: [50,20000],
        16: [50,20000],
        17: [50,20000],
        18: [50,20000],
        19: [50,20000],
        20: [55,22000],
        21: [55,22000],
        22: [55,22000],
        23: [55,22000],
        24: [55,22000],
        25: [55,22000],
        26: [55,22000],
        27: [55,22000],
        28: [55,22000],
        29: [55,22000]
} # 升级专武所需要的条件，格式为["等级“: (心碎,金币)]

DAY_BOSS_LIMIT = 3
BOSS_LIST = {
    "A":{
        1:["双足飞龙",500,5,10000,500],
        2:["野性狮鹫",1000,10,20000,1000],
        3:["针刺攀缘花",1500,15,30000,1500],
        4:["狂乱魔熊",2000,20,40000,2000],
        5:["梦魇牡羊",2500,25,50000,2500],
    },
    "B":{
        1:["巨型哥布林",3000,30,60000,3000],
        2:["莱莱",4000,40,80000,4000],
        3:["雷电",5000,50,100000,5000],
        4:["灵魂角鹿",6000,60,120000,6000],
        5:["弥诺陶洛斯",7000,70,140000,7000],
    },
}# BOSS数据，格式为["阶段":{王：名字,HP,掉落心碎,掉落金币,经验值}]

MAX_RANK = 10 #最大rank等级
RANK_LIST = {
    1: 50000,
    2: 100000,
    3: 150000,
    4: 200000,
    5: 250000,
    6: 300000,
    7: 350000,
    8: 400000,
    9: 450000,
    10: 500000,
}# rank升级要求，格式为["rank":金币]

FILE_PATH = os.path.dirname(__file__)#用于加载dlcjson
blhxlist = range(6000, 6106)
blhxlist2 = range(6106, 6206)
blhxlist3 = range(6206, 6306)
blhxlist4 = range(6306, 6406)
blhxlist5 = range(6406, 6506)
yozilist = range(1523, 1544)
genshinlist = range(7001, 7020)
bangdreamlist = range(1601, 1636)
millist = range(3001, 3055)
collelist = range(4001, 4639)
koilist = range(7100, 7104)
sakulist = range(7200, 7204)
cloverlist = range(7300, 7307)
majsoullist = range(7400, 7476)
noranekolist = range(7500, 7510)
fgolist = range(8001, 8301)

# 这里记录dlc名字和对应列表
dlcdict = {
    'blhx': blhxlist,
    'blhx2': blhxlist2,
    'blhx3': blhxlist3,
    'blhx4': blhxlist4,
    'blhx5': blhxlist5,
    'yozi': yozilist,
    'genshin': genshinlist,
    'bangdream': bangdreamlist,
    'million': millist,
    'kancolle': collelist,
    'koikake': koilist,
    'sakukoi': sakulist,
    'cloverdays': cloverlist,
    'majsoul': majsoullist,
    'noraneko': noranekolist,
    'fgo': fgolist
}

# 这里记录每个dlc的介绍
dlcintro = {
    'blhx': '碧蓝航线手游角色包。',
    'blhx2': '碧蓝航线手游角色包2。',
    'blhx3': '碧蓝航线手游角色包3。',
    'blhx4': '碧蓝航线手游角色包4。',
    'blhx5': '碧蓝航线手游角色包5。',
    'yozi': '柚子社部分角色包。',
    'genshin': '原神角色包。',
    'bangdream': '邦邦手游角色包。',
    'million': '偶像大师百万剧场角色包',
    'kancolle': '舰队collection角色包',
    'koikake': '恋×シンアイ彼女角色包',
    'sakukoi': '桜ひとひら恋もよう角色包',
    'cloverdays': 'Clover Days角色包',
    'majsoul': '雀魂角色包',
    'noraneko': 'ノラと皇女と野良猫ハート角色包',
    'fgo': 'FGO手游角色包'

}

# 这个字典保存保存每个DLC开启的群列表，pcr默认一直开启。
dlc_switch = {}

with open(os.path.join(FILE_PATH, 'dlc_config.json'), 'r', encoding='UTF-8') as f:
    dlc_switch = json.load(f, strict=False)

def save_dlc_switch():
    with open(os.path.join(FILE_PATH, 'dlc_config.json'), 'w', encoding='UTF-8') as f:
        json.dump(dlc_switch, f, ensure_ascii=False)

# 取得该群未开启的dlc所形成的黑名单
def get_dlc_blacklist(gid):
    dlc_blacklist = []
    for dlc in dlcdict.keys():
        if gid not in dlc_switch[dlc]:
            dlc_blacklist += dlcdict[dlc]
    return dlc_blacklist

# 检查有没有没加到json里的dlc
def check_dlc():
    for dlc in dlcdict.keys():
        if dlc not in dlc_switch.keys():
            dlc_switch[dlc] = []
    save_dlc_switch()
check_dlc()

# 随机生成一个pcr角色id，应该已经被替代了。
# def get_pcr_id():
#     chara_id_list = list(_pcr_data.CHARA_NAME.keys())
#     while True:
#         random.shuffle(chara_id_list)
#         if chara_id_list[0] not in BLACKLIST_ID: break
#     return chara_id_list[0]

# 生成没被约过的角色列表
def get_newgirl_list(gid):
    pcr_id_list = list(_pcr_data.CHARA_NAME.keys())
    dlc_id_list = list(_dlc_data.DLC_CHARA_NAME.keys())
    chara_id_list = pcr_id_list + dlc_id_list
    duel = DuelCounter()
    old_list = duel._get_card_list(gid)
    dlc_blacklist = get_dlc_blacklist(gid)
    new_list = []
    for card in chara_id_list:
        if card not in BLACKLIST_ID and card not in old_list and card not in dlc_blacklist:
            new_list.append(card)
    return new_list

#增加角色经验
def add_exp(gid,uid,cid,exp):
    CE = CECounter()
    now_level = CE._get_card_level(gid, uid, cid)
    need_exp = (now_level+1)*100
    exp_info = CE._get_card_exp(gid, uid, cid)
    now_exp = exp_info+exp
    if now_exp>=need_exp:
        now_exp = now_exp-need_exp
        now_level = now_level+1
    CE._add_card_exp(gid, uid, cid, now_level, now_exp)
    return now_level

#返回好感对应的关系和文本
def get_relationship(favor):
    for relation in RELATIONSHIP_DICT.keys():
        if favor >= relation:
            relationship = RELATIONSHIP_DICT[relation]
    return relationship[0],relationship[1]


#查询单角色战力
def get_card_ce(gid,uid,cid):
    duel = DuelCounter()
    CE = CECounter()
    #获取角色等级
    level_info = CE._get_card_level(gid, uid, cid)
    level_ce = level_info*10
    #获取角色好感信息
    favor= duel._get_favor(gid,uid,cid)
    #计算角色好感战力加成
    favor_ce = math.ceil(favor/500*200)
    #计算角色专武战力加成
    equip_ce = 0
    equip = duel._get_uniequip(gid, uid, cid)
    if equip>0:
        equip_ce = equip*100
    #计算角色rank战力加成
    rank = duel._get_rank(gid, uid, cid)
    card_ce=math.ceil((100+level_ce+favor_ce+equip_ce)*(1+rank/10))
    return card_ce

#获取战力排行榜
def get_power_rank(gid):
    duel = DuelCounter()
    girls = duel._get_cards_byrank(gid,20)
    if len(girls)>0:
        data = sorted(girls,key=lambda cus:cus[1],reverse=True)
        new_data = []
        for girl_data in data:
            gid1, rank, uid, cid = girl_data
            gpower = get_card_ce(gid1,uid,cid)
            new_data.append((rank,gpower,uid,cid))
        rankData = sorted(new_data,key=lambda cus:cus[1],reverse=True)
        return rankData
    else:
        return []

# 取爵位名
def get_noblename(level: int):
    return NAME_DICT[str(level)]

# 取爵位对应等级
def get_noblelevel(name):
    for level in NAME_DICT:
        if NAME_DICT[level] == name:
            return int(level)
    return 0
# 返回升级到爵位所需要的胜场数
def get_nobleWin(level: int):
    numdict = LEVEL_WIN_NEED
    return numdict[str(level)]

# 返回爵位对应的女友数
def get_girlnum(level: int):
    numdict = LEVEL_GIRL_NEED
    return numdict[str(level)]

# 返回对应的女友上限
def get_girlnum_buy(gid,uid):
    numdict = LEVEL_GIRL_NEED
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    num = duel._get_warehouse(gid, uid)
    housenum = int(numdict[str(level)])+num
    return housenum

# 返回升级到爵位所需要的金币数
def get_noblescore(level: int):
    numdict = LEVEL_COST_DICT
    return numdict[str(level)]

# 返回升级到爵位所需要的声望数
def get_noblesw(level: int):
    numdict = LEVEL_SW_NEED
    return numdict[str(level)]

# 判断当前女友数是否大于于上限
def girl_outlimit(gid,uid):
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    girlnum = get_girlnum_buy(gid, uid)
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist) 
    if cidnum > girlnum:
        return True
    else: 
        return False
        
        
#魔改图片拼接 
def concat_pic(pics, border=0):
    num = len(pics)
    w= pics[0].size[0]
    h_sum = 0
    for pic in pics:
        h_sum += pic.size[1]
    des = Image.new('RGBA', (w, h_sum + (num-1) * border), (255, 255, 255, 255))
    h = 0
    for i, pic in enumerate(pics):
        des.paste(pic, (0, (h + i*border)), pic)
        h += pic.size[1]        
    return des

def get_nv_icon(cid):
    c = duel_chara.fromid(cid)
    mes = c.icon.cqcode
    path = os.path.join(FULLCARD_PATH,f'{cid}31.png')
    if  os.path.exists(path):
        img = Image.open(path)
        bio = BytesIO()
        img.save(bio, format='PNG')
        base64_str = 'base64://' + base64.b64encode(bio.getvalue()).decode()
        mes = f"[CQ:image,file={base64_str}]"   
    return mes
    
#根据角色id和礼物id，返回增加的好感和文本

def check_gift(cid,giftid):
    lastnum = cid%10
    if lastnum == giftid:
        favor = 10
        text = random.choice(Gift10)
        return favor, text
    num1=lastnum%3
    num2=giftid%3
    choicelist = GIFTCHOICE_DICT[num1]

    if num2 == choicelist[0]:
        favor = 5
        text = random.choice(Gift5)
        return favor, text
    if num2 == choicelist[1]:
        favor = 2
        text = random.choice(Gift2)
        return favor, text        
    if num2 == choicelist[2]:
        favor = 1
        text = random.choice(Gift1)
        return favor, text

async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
    return d
def uid2card(uid, user_card_dict):
    return str(uid) if uid not in user_card_dict.keys() else user_card_dict[uid]

