from nonebot import get_driver
from pydantic import BaseModel, Field


class Config(BaseModel):
    # 图片资源缓存开关
    img_cache: bool = Field(default=True)
    # 资源下载代理
    github_proxy: str = Field(default='https://gitdl.cn/')


config = Config(**get_driver().config.dict())
