from pydantic import BaseModel
from nonebot import get_plugin_config



class Config(BaseModel):
    # 图片资源缓存开关
    img_cache: bool = True
    # 名称
    pm_name: str = "NoneBot帮助"
    # 版本
    pm_version: str = "11.45.14"
    # 自定义文本
    pm_text: str = "自定义文本"
    # 被限流是否提醒
    pm_message: bool = True
    # 帮助文件位置
    pm_plugin: str = "1"
    pm_path: str = ""
    # web开关
    pm_enable_web: bool = True
    # 后台管理用户名
    pm_username: str = "pmhelp"
    # 后台管理密码
    pm_password: str = "admin"
    # 后台管理token密钥
    pm_secret_key: str = "r99nxsvr93a5i241mvisjydxspiwxgpiyoh9nas35036fkxd7y"


Pm_config: Config = get_plugin_config(Config)
