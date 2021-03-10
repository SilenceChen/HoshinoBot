from hoshino import Service

sv = Service('pcr-duel', enable_on_default=True)
from .counter.CECounter import *
from .counter.ScoreCounter import *
from .counter.DuelCounter import *

from .pcr_duel import *
from .modules.battle import *
from .modules.gift import *
from .modules.hongbao import *
from .modules.prestige import *
from .modules.store import *
from .modules.uniequip import *
from .modules.weapon import *
from .modules.dlc import *