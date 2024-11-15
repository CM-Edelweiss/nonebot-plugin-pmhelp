import datetime
from typing import List
from tortoise import fields
from tortoise.models import Model
from .Path import MANAGER_DB_PATH
from nonebot_plugin_tortoise_orm import add_model

add_model(
    __name__,
    db_name="pmhelp",
    db_url=f"sqlite://{MANAGER_DB_PATH}",
)


class PluginPermission(Model):
    # 权限
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    name: str = fields.TextField()
    """插件名称"""
    session_id: int = fields.IntField()
    """会话id"""
    session_type: str = fields.CharField(max_length=10, default="group")
    """会话类型，group/user"""
    status: bool = fields.BooleanField(default=True)
    """插件总开关"""
    ban: List[int] = fields.JSONField(default=[])
    """插件屏蔽列表"""
    statistics: dict = fields.JSONField(default=dict)
    """插件调用统计(x)"""

    class Meta:
        table = "plugin_permission"


class PluginDisable(Model):
    # 禁用
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    name: str = fields.TextField()
    """插件名称"""
    global_disable: bool = fields.BooleanField(default=False)
    """全局禁用"""
    user_id: int = fields.IntField(null=True)
    """用户id"""
    group_id: int = fields.IntField(null=True)
    """群组id"""

    class Meta:
        table = "plugin_disable"


class PluginWithdraw(Model):
    # 撤回
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    name: str = fields.TextField()
    """插件名称"""
    global_withdraw: bool = fields.BooleanField(default=False)
    """全局撤回"""
    user_id: int = fields.IntField(null=True)
    """用户id"""
    group_id: int = fields.IntField(null=True)
    """群组id"""
    time: int = fields.IntField()
    """等待时间"""

    class Meta:
        table = "plugin_withdraw"


class PluginTime(Model):
    # 限制
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    name: str = fields.TextField()
    """插件名称"""
    global_time: bool = fields.BooleanField(default=False)
    """全局限制"""
    user_id: int = fields.IntField(null=True)
    """用户id"""
    group_id: int = fields.IntField(null=True)
    """群组id"""
    type: str = fields.CharField(max_length=10, default="time")
    """限制类型 time/frequency"""
    time: int = fields.IntField(null=True)
    """限制时间/次数"""

    class Meta:
        table = "plugin_time"


class PluginStatistics(Model):
    # 统计
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    plugin_name: str = fields.TextField()
    """插件名称"""
    matcher_name: str = fields.TextField()
    """命令名称"""
    matcher_usage: str = fields.TextField(null=True)
    """命令用法"""
    group_id: int = fields.IntField(null=True)
    """群id"""
    user_id: int = fields.IntField()
    """用户id"""
    message_type: str = fields.CharField(max_length=10)
    """消息类型，group/user"""
    time: datetime.datetime = fields.DatetimeField()
    """调用时间"""

    class Meta:
        table = "plugin_statistics"
