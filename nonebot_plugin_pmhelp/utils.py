from io import BytesIO
import httpx
import tqdm.asyncio
from ruamel.yaml import YAML
from ssl import SSLCertVerificationError
from pathlib import Path
from typing import Dict,  Any, Union, Optional, Tuple, List
from PIL import Image
from nonebot.rule import Rule
from nonebot.params import CommandArg, Depends
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Message

from .logger import logger
from .Path import IMAGE_PATH, FONTS_PATH
from .config import config

DRIVER = get_driver()
try:
    SUPERUSERS: List[int] = [int(s) for s in DRIVER.config.superusers]
except Exception:
    SUPERUSERS = []


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


async def download(url: str, save_path: Path, exclude_json: bool = False):
    """
    下载文件(带进度条)

    :param url: url
    :param save_path: 保存路径
    :param exclude_json: 是否排除json文件
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient().stream(method='GET', url=url, follow_redirects=True) as datas:
        if exclude_json and 'application/json' in str(datas.headers['Content-Type']):
            raise Exception('file not match type')
        size = int(datas.headers['Content-Length'])
        f = save_path.open('wb')
        async for chunk in tqdm.asyncio.tqdm(iterable=datas.aiter_bytes(1),
                                             desc=url.split('/')[-1],
                                             unit='iB',
                                             unit_scale=True,
                                             unit_divisor=1024,
                                             total=size,
                                             colour='green'):
            f.write(chunk)
        f.close()


fonts = ["bahnschrift_regular.ttf",
         "SourceHanSansCN-Bold.otf", "SourceHanSerifCN-Bold.otf"]
generals = ["bg.png", "black_bord.png", "black_card2.png",
            "black2.png", "orange_bord.png", "orange_card.png", "orange.png"]


async def check_resource():
    for font in fonts:
        if (FONTS_PATH / font).exists() and (FONTS_PATH / font).is_file():
            pass
        else:
            try:
                await download(url=f'{config.github_proxy}https://raw.githubusercontent.com/CM-Edelweiss/help_resources/refs/heads/main/fonts/{font}', save_path=FONTS_PATH / font)
            except Exception as e:
                logger.warning(
                    '资源检查', f'下载<m>{font}</m>时<r>出错</r>，请尝试更换<m>github资源地址</m>{e}')

    for general in generals:
        if (IMAGE_PATH / general).exists() and (IMAGE_PATH / general).is_file():
            pass
        else:
            try:
                await download(url=f'{config.github_proxy}https://raw.githubusercontent.com/CM-Edelweiss/help_resources/refs/heads/main/general/{general}', save_path=IMAGE_PATH / general)
            except Exception as e:
                logger.warning(
                    '资源检查', f'下载<m>{general}</m>时<r>出错</r>，请尝试更换<m>github资源地址</m>{e}')
