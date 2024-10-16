from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    # 图片资源缓存开关
    img_cache: bool = True
    # 资源下载代理
    github_proxy: str = 'https://gitdl.cn/'
    # 版本
    pm_version: str = "11.45.14"


config: Config = get_plugin_config(Config)
