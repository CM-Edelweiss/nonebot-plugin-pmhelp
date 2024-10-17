import nonebot_plugin_localstore as store
from pathlib import Path
from nonebot import require
# 先导入(注意格式化移动)
require("nonebot_plugin_localstore")


# 资源路径
RESOURCE_BASE_PATH = Path(__file__).parent / "pmhelp_data"
# 图片路径
IMAGE_PATH = RESOURCE_BASE_PATH / 'general'
# 字体路径
FONTS_PATH = RESOURCE_BASE_PATH / 'fonts'


# 数据库路径
DATABASE_PATH = store.get_plugin_cache_file("pmhelp_data") / 'database'
DATABASE_PATH.mkdir(parents=True, exist_ok=True)
MANAGER_DB_PATH = DATABASE_PATH / 'manager.db'


# 插件管理器文件存放目录
# 用户修改
PLUGIN_CONFIG = Path() / 'config' / 'plugins'
PLUGIN_CONFIG.mkdir(parents=True, exist_ok=True)
