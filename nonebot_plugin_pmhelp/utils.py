import time
import asyncio
from pathlib import Path
from .logger import logger
from ruamel.yaml import YAML
from nonebot import get_driver
from typing import Union, List
from nonebot.params import Depends
from collections import defaultdict
from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_apscheduler import scheduler


# 图片缓存
cache_help = {}
XL_list = {}

DRIVER = get_driver()
try:
    SUPERUSERS: List[int] = [int(s) for s in DRIVER.config.superusers]
except Exception:
    SUPERUSERS = []


async def get_list(list: list, type: bool = True):
    """
    整合群/用户号

    :param list: bot列表
    :param type: 是否为群
    :return: 带群/用户号的list

    """
    list_id = []
    for i in list:
        list_id.append(i["group_id" if type else "user_id"])
    return list_id


async def XlCount(key: str, frequency: int):
    if key not in XL_list:
        # 进入限制
        XL_list[key] = {
            "initial": frequency,
            "frequency": frequency - 1,
        }
        return True
    elif XL_list[key]["frequency"] > 0:
        XL_list[key]["frequency"] = XL_list[key]["frequency"] - 1
        return True
    else:
        return False


@scheduler.scheduled_job('cron', minute='*', id='job_id')
async def scheduled_job():
    # 重置次数
    for i in XL_list:
        XL_list[i]["frequency"] = XL_list[i]["initial"]


def load_yaml(path: Union[Path, str], encoding: str = 'utf-8'):
    """
    读取本地yaml文件，返回字典。

    :param path: 文件路径
    :param encoding: 编码，默认为utf-8
    :return: 字典
    """
    if isinstance(path, str):
        path = Path(path)
    yaml = YAML(typ='safe')
    return yaml.load(path.read_text(encoding=encoding)) if path.exists() else {}


def save_yaml(data: dict, path: Union[Path, str], encoding: str = 'utf-8'):
    """
    保存yaml文件

    :param data: 数据
    :param path: 保存路径
    :param encoding: 编码
    """
    if isinstance(path, str):
        path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding=encoding) as f:
        yaml = YAML(typ='safe')
        yaml.dump(
            data,
            f)


def CommandObjectID() -> int:
    """
    根据消息事件的类型获取对象id
    私聊->用户id
    群聊->群id
    频道->子频道id
        :return: 对象id
    """

    def _event_id(event):
        if event.message_type == 'private':
            return event.user_id
        elif event.message_type == 'group':
            return event.group_id
        elif event.message_type == 'guild':
            return event.channel_id

    return Depends(_event_id)


class FreqLimiter:
    """
    冷却器
    """

    def __init__(self):
        """
        初始化一个冷却器
        """
        self.next_time = defaultdict(float)

    def check(self, key: str) -> bool:
        """
        检查是否冷却结束
            :param key: key
            :return: 布尔值
        """
        return time.time() >= self.next_time[key]

    def start(self, key: str, cooldown_time: int = 0):
        """
        开始冷却
            :param key: key
            :param cooldown_time: 冷却时间(秒)
        """
        self.next_time[key] = time.time(
        ) + (cooldown_time if cooldown_time > 0 else 60)

    def left(self, key: str) -> int:
        """
        剩余冷却时间
            :param key: key
            :return: 剩余冷却时间
        """
        return int(self.next_time[key] - time.time()) + 1


freqLimiter = FreqLimiter()


async def withdraw_message(bot: Bot, message_id: int, time: int = 10):
    # 延迟撤回
    await asyncio.sleep(time)
    try:
        await bot.delete_msg(message_id=message_id)
    except Exception as e:
        logger.info('插件管理器[撤回]', f'插件权限检查<r>失败：{e}</r>')
