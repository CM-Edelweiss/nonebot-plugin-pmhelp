from pathlib import Path


# 资源路径
RESOURCE_BASE_PATH = Path() / 'help_data'
RESOURCE_BASE_PATH.mkdir(parents=True, exist_ok=True)

# 图片路径
IMAGE_PATH = RESOURCE_BASE_PATH / 'general'


# 数据库路径
DATABASE_PATH = RESOURCE_BASE_PATH / 'database'
DATABASE_PATH.mkdir(parents=True, exist_ok=True)
MANAGER_DB_PATH = DATABASE_PATH / 'manager.db'

# 字体路径
FONTS_PATH = RESOURCE_BASE_PATH / 'fonts'
FONTS_PATH.mkdir(parents=True, exist_ok=True)

# 插件管理器文件存放目录
PLUGIN_CONFIG = Path() / 'config' / 'plugins'
PLUGIN_CONFIG.mkdir(parents=True, exist_ok=True)
