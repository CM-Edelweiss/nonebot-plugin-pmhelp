import time
import httpx
import asyncio
from typing import (
    Dict,
    Any,
    Union,
    Optional,
    Tuple,
    List,
)
from jose import jwt
from PIL import Image
from io import BytesIO
from pathlib import Path
from .logger import logger
from ruamel.yaml import YAML
from nonebot import get_driver
from nonebot.rule import Rule
from .pm_config import Pm_config
from collections import defaultdict
from ssl import SSLCertVerificationError
from nonebot.params import CommandArg, Depends
from nonebot_plugin_apscheduler import scheduler
from fastapi import Header, HTTPException, Depends
from nonebot.adapters.onebot.v11 import Message, Bot


# 图片缓存
cache_help = {}
XL_list = {}

DRIVER = get_driver()
try:
    SUPERUSERS: List[int] = [int(s) for s in DRIVER.config.superusers]
except Exception:
    SUPERUSERS = []


requestAdaptor = """
requestAdaptor(api) {
    api.headers["token"] = localStorage.getItem("token");
    return api;
},
"""
responseAdaptor = """
responseAdaptor(api, payload, query, request, response) {
    if (response.data.detail == '登录验证失败或已失效，请重新登录') {
        window.location.href = '/pmhelp/login'
        window.localStorage.clear()
        window.sessionStorage.clear()
        window.alert('登录验证失败或已失效，请重新登录')
    }
    return payload
},
"""


def authentication():
    def inner(token: Optional[str] = Header(...)):
        try:
            payload = jwt.decode(
                token, Pm_config.pm_secret_key, algorithms="HS256"
            )
            if (
                not (username := payload.get("username"))
                or username != Pm_config.pm_username
            ):
                raise HTTPException(status_code=400, detail="登录验证失败或已失效，请重新登录")
        except (jwt.JWTError, jwt.ExpiredSignatureError, AttributeError):
            raise HTTPException(status_code=400, detail="登录验证失败或已失效，请重新登录")

    return Depends(inner)


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


def save_yaml(data: dict, path: Union[Path, str] = None, encoding: str = 'utf-8'):
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


def fullmatch(msg: Message = CommandArg()) -> bool:
    return not bool(msg)


fullmatch_rule = Rule(fullmatch)


async def get_img(url: str,
                  *,
                  headers: Optional[Dict[str, str]] = None,
                  params: Optional[Dict[str, Any]] = None,
                  timeout: Optional[int] = 20,
                  save_path: Optional[Union[str, Path]] = None,
                  size: Optional[Union[Tuple[int, int], float]] = None,
                  mode: Optional[str] = None,
                  crop: Optional[Tuple[int, int, int, int]] = None,
                  **kwargs) -> Union[None, Image.Image]:
    """
    说明：
        httpx的get请求封装，获取图片
    参数：
        :param url: url
        :param headers: 请求头
        :param params: params
        :param timeout: 超时时间
        :param save_path: 保存路径，为空则不保存
        :param size: 图片尺寸，为空则不做修改
        :param mode: 图片模式，为空则不做修改
        :param crop: 图片裁剪，为空则不做修改
    """
    if save_path and Path(save_path).exists():
        img = Image.open(save_path)
    else:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url,
                                        headers=headers,
                                        params=params,
                                        timeout=timeout,
                                        **kwargs)
                if resp.headers.get('etag') == 'W/"6363798a-13c7"' or resp.headers.get(
                        'content-md5') == 'JeG5b/z8SpViMmO/E9eayA==':
                    return None
                if resp.headers.get('Content-Type') not in ['image/png', 'image/jpeg']:
                    return None
                resp = resp.read()
                img = Image.open(BytesIO(resp))
        except SSLCertVerificationError:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url.replace('https', 'http'),
                                        headers=headers,
                                        params=params,
                                        timeout=timeout,
                                        **kwargs)
                if resp.headers.get('etag') == 'W/"6363798a-13c7"' or resp.headers.get(
                        'content-md5') == 'JeG5b/z8SpViMmO/E9eayA==':
                    return None
                if resp.headers.get('Content-Type') not in ['image/png', 'image/jpeg']:
                    return None
                resp = resp.read()
                img = Image.open(BytesIO(resp))
    if size:
        if isinstance(size, float):
            img = img.resize(
                (int(img.size[0] * size), int(img.size[1] * size)), Image.LANCZOS)
        elif isinstance(size, tuple):
            img = img.resize(size, Image.LANCZOS)
    if mode:
        img = img.convert(mode)
    if crop:
        img = img.crop(crop)
    if save_path and not Path(save_path).exists():
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path)
    return img


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
