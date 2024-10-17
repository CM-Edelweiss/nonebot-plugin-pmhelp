from pathlib import Path
from nonebot import require
#先导入(注意格式化移动)
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store


# 资源路径
RESOURCE_BASE_PATH = store.get_plugin_cache_file("pmhelp_data")
RESOURCE_BASE_PATH.mkdir(parents=True, exist_ok=True)

# 图片路径
IMAGE_PATH = RESOURCE_BASE_PATH / 'general'
IMAGE_PATH.mkdir(parents=True, exist_ok=True)

# 数据库路径
DATABASE_PATH = RESOURCE_BASE_PATH / 'database'
DATABASE_PATH.mkdir(parents=True, exist_ok=True)
MANAGER_DB_PATH = DATABASE_PATH / 'manager.db'

# 字体路径
FONTS_PATH = RESOURCE_BASE_PATH / 'fonts'
FONTS_PATH.mkdir(parents=True, exist_ok=True)

# 插件管理器文件存放目录
# 用户修改
PLUGIN_CONFIG = Path() / 'config' / 'plugins'
PLUGIN_CONFIG.mkdir(parents=True, exist_ok=True)
