import asyncio
import base64
import os
import random
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from hoshino import Service, priv
from hoshino.modules.priconne import _pcr_data
from hoshino.modules.priconne import chara
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
from hoshino.typing import MessageSegment as Seg


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
        print(date)
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET date=? WHERE key=?", (date, key,), )
        return

class DailyAmountLimiter(DailyNumberLimiter):
    def __init__(self, types, max_num, reset_hour,db):
        super().__init__(max_num)
        self.reset_hour = reset_hour
        self.type = types
        self.db = db

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != self.db.get_date(key):
            self.db.set_date(day, key)
            self.db.clear_key(key)
        return bool(self.db.get_num(key) < self.max)

    def check10(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != self.db.get_date(key):
            self.db.set_date(day, key)
            self.db.clear_key(key)
        return bool(self.db.get_num(key) < 10)

    def get_num(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        return self.db.get_num(key)

    def get_today_num(self,key):
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != self.db.get_date(key):
            return 0
        return self.db.get_num(key)

    def increase(self, key, num=1):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        self.db.increment_key(key, num)

    def reset(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        self.db.clear_key(key)

INIT_TIME = 0 #每日重置时间
AVATAR_GUESS_MAX_NUM = 20 #猜头像每日次数
DESC_GUESS_MAX_NUM = 20 #猜角色每日次数
VOICE_GUESS_MAX_NUM = 20 #猜ub每日次数
CARD_GUESS_MAX_NUM = 20 #猜卡面每日次数
STORY_GUESS_MAX_NUM = 20 #猜剧情每日次数

sv = Service(
    "pcr-daily-limiter",
    bundle="pcr查询",
    help_="""
[查看小游戏] 查看我参与的小游戏情况
""".strip()
)
@sv.on_fullmatch(("查看小游戏", "查看小游戏数据"))
async def query_games_data(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    guid = gid, uid
    msg = ["小游戏参与情况："]
    # 猜头像
    adb = RecordDAO(os.path.expanduser("~/.hoshino/pcr_avatarguess.db"))
    a_limiter = DailyAmountLimiter("avatarguess", AVATAR_GUESS_MAX_NUM, INIT_TIME, adb)
    a_dailynum = a_limiter.get_today_num(guid)
    msg.append(f'--【猜头像】本日已参与{a_dailynum}/{AVATAR_GUESS_MAX_NUM}次')
    # 猜角色
    bdb = RecordDAO(os.path.expanduser("~/.hoshino/pcr_descguess.db"))
    b_limiter = DailyAmountLimiter("descguess", DESC_GUESS_MAX_NUM, INIT_TIME, bdb)
    b_dailynum = b_limiter.get_today_num(guid)
    msg.append(f'--【猜角色】本日已参与{b_dailynum}/{DESC_GUESS_MAX_NUM}次')
    # 猜ub
    cdb = RecordDAO(os.path.expanduser("~/.hoshino/pcr_voice_guess.db"))
    c_limiter = DailyAmountLimiter("voiceguess", VOICE_GUESS_MAX_NUM, INIT_TIME, cdb)
    c_dailynum = c_limiter.get_today_num(guid)
    msg.append(f'--【猜ub】本日已参与{c_dailynum}/{VOICE_GUESS_MAX_NUM}次')
    # 猜卡面
    ddb = RecordDAO(os.path.expanduser("~/.hoshino/pcr_cardguess.db"))
    d_limiter = DailyAmountLimiter("cardguess", CARD_GUESS_MAX_NUM, INIT_TIME, ddb)
    d_dailynum = d_limiter.get_today_num(guid)
    msg.append(f'--【猜卡面】本日已参与{d_dailynum}/{CARD_GUESS_MAX_NUM}次')
    # 猜剧情
    edb = RecordDAO(os.path.expanduser("~/.hoshino/pcr_storyguess.db"))
    e_limiter = DailyAmountLimiter("storyguess", STORY_GUESS_MAX_NUM, INIT_TIME, edb)
    e_dailynum = e_limiter.get_today_num(guid)
    msg.append(f'--【猜剧情】本日已参与{e_dailynum}/{STORY_GUESS_MAX_NUM}次')

    msgAll = "\n".join(msg)
    await bot.send(ev, f'{Seg.at(ev.user_id)}{msgAll}')