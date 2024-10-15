from nonebot import get_driver
from pydantic import BaseModel, Field


class Config(BaseModel):
    # 图片资源缓存开关
    img_cache: bool = Field(default=True)
    # 资源下载代理
    github_proxy: str = Field(default='https://gitdl.cn/')
    # 版本
    __version__ = Field(default='11.45.14')


config = Config(**get_driver().config.dict())
