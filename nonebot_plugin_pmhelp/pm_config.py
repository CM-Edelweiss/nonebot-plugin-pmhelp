from nonebot import get_plugin_config
from pydantic import BaseModel

class Config(BaseModel):
    # 图片资源缓存开关
    img_cache: bool = True
    # 版本
    pm_version: str = "11.45.14"
    # 自定义文本
    pm_text: str = "自定义文本"
    # 帮助文件位置
    pm_plugin: str = "1"
    pm_path: str = ""


Pm_config: Config = get_plugin_config(Config)
