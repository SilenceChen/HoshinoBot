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
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
import copy
import json
DUEL_DB_PATH = os.path.expanduser('~/.hoshino/pcr_duel.db')
SCORE_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
DB_PATH = os.path.expanduser("~/.hoshino/pcr_duel.db")
class CECounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DUEL_DB_PATH), exist_ok=True)
        self._create_exptable()
        self._create_guajitable()
    
    def _connect(self):
        return sqlite3.connect(DUEL_DB_PATH)
        
    def _create_exptable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS EXPTABLE
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           CID           INT    NOT NULL,
                           LEVEL           INT    NOT NULL,
                           EXP           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except:
            raise Exception('创建角色等级经验表发生错误')
            
    def _create_guajitable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS GUAJITABLE
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           CID           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建角色挂机表发生错误')
          
    #重置角色等级
    def _set_card_exp(self, gid, uid, cid, level=0, exp=0):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO EXPTABLE (GID, UID, CID, LEVEL, EXP) VALUES (?, ?, ?, ?, ?)",
                (gid, uid, cid, level, exp),
            )
            
    #查询角色等级信息
    def _get_card_level(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT LEVEL FROM EXPTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid,cid)).fetchone()
            if r is None:
               CE = CECounter()
               CE._set_card_exp(gid,uid,cid)
               return 0
            return r[0]
        except Exception as e:
            raise Exception('错误:\n' + str(e))
            return 0
            
    #查询角色经验信息
    def _get_card_exp(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT EXP FROM EXPTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid,cid)).fetchone()
            if r is None:
               CE = CECounter()
               CE._set_card_exp(gid,uid,cid)
               return 0
            return r[0]
        except Exception as e:
            raise Exception('错误:\n' + str(e))
            return 0
            
    #更新角色等级、经验信息
    def _add_card_exp(self, gid, uid, cid, level, exp):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO EXPTABLE (GID, UID, CID, LEVEL, EXP) VALUES (?, ?, ?, ?, ?)",
                (gid, uid, cid, level, exp),
            )
            
    #查询绑定的挂机角色
    def _get_guaji(self, gid, uid):
        try:
            r = self._connect().execute("SELECT CID FROM GUAJITABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception as e:
            raise Exception('错误:\n' + str(e))
            return 0
            
    #设定挂机绑定角色
    def _add_guaji(self, gid, uid, cid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GUAJITABLE (GID, UID, CID) VALUES (?, ?, ?)",
                (gid, uid, cid),
            )
