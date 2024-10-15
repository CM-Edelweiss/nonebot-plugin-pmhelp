from pathlib import Path
from typing import Optional, Union
from tortoise import Tortoise
from nonebot.log import logger
from .manage import *

from ..Path import MANAGER_DB_PATH

DATABASE = {
    'connections': {
        'manage':       {
            'engine':      'tortoise.backends.sqlite',
            'credentials': {'file_path': MANAGER_DB_PATH},
        },
    },
    'apps':        {
        'manage':        {
            'models':             [manage.__name__],
            'default_connection': 'manage',
        },
    },
    'use_tz': False,
    'timezone': 'Asia/Shanghai'
}


def register_database(db_name: str, models: str, db_path: Optional[Union[str, Path]]):
    """
    注册数据库
    """
    if db_name in DATABASE['connections'] and db_name in DATABASE['apps']:
        DATABASE['apps'][db_name]['models'].append(models)
    else:
        DATABASE['connections'][db_name] = {
            'engine':      'tortoise.backends.sqlite',
            'credentials': {'file_path': db_path},
        }
        DATABASE['apps'][db_name] = {
            'models':             [models],
            'default_connection': db_name,
        }


async def connect():
    """
    建立数据库连接
    """
    try:
        await Tortoise.init(DATABASE)
        await Tortoise.generate_schemas()
        logger.opt(colors=True).success('<u><y>[数据库]</y></u><g>连接成功</g>')
    except Exception as e:
        logger.opt(colors=True).warning(f'<u><y>[数据库]</y></u><r>连接失败:{e}</r>')
        raise e


async def disconnect():
    """
    断开数据库连接
    """
    await Tortoise.close_connections()
    logger.opt(colors=True).success('<u><y>[数据库]</y></u><r>连接已断开</r>')
