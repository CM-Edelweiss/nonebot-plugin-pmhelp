from pathlib import Path
from nonebot import require
from .pm_config import Pm_config
from .logger import logger
# 先导入(注意格式化移动)
require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

# 资源路径
RESOURCE_BASE_PATH = Path(__file__).parent / 'pmhelp_data'
# 图片路径
IMAGE_PATH = RESOURCE_BASE_PATH / 'general'
# 字体路径
FONTS_PATH = RESOURCE_BASE_PATH / 'fonts'


# 数据库路径
DATABASE_PATH = store.get_plugin_cache_file('pmhelp_data') / 'database'
DATABASE_PATH.mkdir(parents=True, exist_ok=True)
MANAGER_DB_PATH = DATABASE_PATH / 'manager.db'


# 插件管理器文件存放目录
if Pm_config.pm_plugin == "1":
    PM_CONFIG = store.get_plugin_cache_file('pmhelp_data')
elif Pm_config.pm_plugin == "2":
    PM_CONFIG = Path()
elif Pm_config.pm_plugin == "3" and Pm_config.pm_path:
    PM_CONFIG = Path(Pm_config.pm_path)
else:
    logger.info('插件管理器', f'<r>插件目录配置失败，请检查。</r>')
    PM_CONFIG = store.get_plugin_cache_file('pmhelp_data')
PLUGIN_CONFIG = PM_CONFIG / 'pm_config'
PLUGIN_CONFIG.mkdir(parents=True, exist_ok=True)
