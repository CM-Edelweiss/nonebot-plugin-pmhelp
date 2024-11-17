import asyncio
import datetime
import contextlib
from ..models import (
    PluginPermission,
    PluginStatistics,
    PluginDisable,
    PluginTime,
    PluginWithdraw,
)
from ..utils import (
    SUPERUSERS,
    load_yaml,
    save_yaml,
    freqLimiter,
    XlCount,
    withdraw_message,
)
from ..logger import logger
from tortoise.queryset import Q
from ..Path import PLUGIN_CONFIG
from ..pm_config import Pm_config
from nonebot.matcher import Matcher
from nonebot import plugin as nb_plugin
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    PrivateMessageEvent,
    GroupMessageEvent,
    Bot,
)
from .model import MatcherInfo, PluginInfo
from nonebot.message import run_preprocessor
from typing import Dict, List, Any, Optional
from nonebot.exception import IgnoredException
from nonebot.internal.matcher import current_event, current_matcher

# 屏蔽插件名称
HIDDEN_PLUGINS = [
    'nonebot_plugin_apscheduler',
    'nonebot_plugin_gocqhttp',
    'nonebot_plugin_htmlrender',
    'nonebot_plugin_imageutils',
    'nonebot_plugin_localstore',
    'nonebot_plugin_tortoise_orm',
    'nonebot_plugin_manageweb',
    'nonebot_plugin_alconna',
    'nonebot_plugin_uninfo',
    'single_session',
    'uniseg',
]


class PluginManager:
    plugins: Dict[str, PluginInfo] = {}
    for file in PLUGIN_CONFIG.iterdir():
        if file.is_file() and file.name.endswith('.yml'):
            data = load_yaml(file)
            plugins[file.name.replace('.yml', '')] = PluginInfo.parse_obj(data)

    @classmethod
    def save(cls):
        """
        保存数据
        """
        for name, plugin in cls.plugins.items():
            save_yaml(plugin.dict(exclude={'status'}),
                      PLUGIN_CONFIG / f'{name}.yml')

    @classmethod
    async def init(cls):
        plugin_list = nb_plugin.get_loaded_plugins()
        if not await PluginDisable.all().exists() and await PluginPermission.all().exists():
            perms = await PluginPermission.filter(Q(status=False) | Q(ban__not=[])).all()
            for perm in perms:
                with contextlib.suppress(Exception):
                    if perm.session_type == 'group':
                        if not perm.status:
                            await PluginDisable.update_or_create(name=perm.name, group_id=perm.session_id)
                        for ban_user in perm.ban:
                            await PluginDisable.update_or_create(name=perm.name, group_id=perm.session_id,
                                                                 user_id=ban_user)
                    elif not perm.status:
                        await PluginDisable.update_or_create(name=perm.name, user_id=perm.session_id)
            await PluginPermission.all().delete()
        await PluginDisable.filter(global_disable=False, group_id=None, user_id=None).delete()
        for plugin in plugin_list:
            if plugin.name not in HIDDEN_PLUGINS:
                if plugin.name not in cls.plugins:
                    if metadata := plugin.metadata:
                        cls.plugins[plugin.name] = PluginInfo.parse_obj({
                            'name':        metadata.name,
                            'module_name': plugin.name,
                            'description': metadata.description,
                            'usage':       metadata.usage,
                            'show':        metadata.extra.get('show', True),
                            'priority':    metadata.extra.get('priority', 99),
                            'cooldown':    metadata.extra.get('cooldown')
                        })
                    else:
                        cls.plugins[plugin.name] = PluginInfo(
                            name=plugin.name, module_name=plugin.name)
                if cls.plugins[plugin.name].matchers is None:
                    cls.plugins[plugin.name].matchers = []
                matchers = plugin.matcher
                for matcher in matchers:
                    if matcher._default_state:
                        with contextlib.suppress(Exception):
                            matcher_info = MatcherInfo.parse_obj(
                                matcher._default_state)
                            if matcher_info.pm_name not in [m.pm_name for m in cls.plugins[plugin.name].matchers]:
                                cls.plugins[plugin.name].matchers.append(
                                    matcher_info)
        cls.save()
        logger.success('插件管理器', '<g>初始化完成</g>')

    @classmethod
    async def get_plugin_list(cls, message_type: str, session_id: int) -> List[PluginInfo]:
        """
        获取插件列表（供帮助图使用）
            :param message_type: 消息类型
            :param session_id: 消息ID
        """
        load_plugins = [p.name for p in nb_plugin.get_loaded_plugins()]
        plugin_list = sorted(cls.plugins.values(), key=lambda x: x.priority)
        plugin_list = [
            p for p in plugin_list if p.show and p.module_name in load_plugins]
        for plugin in plugin_list:
            if await PluginDisable.filter(name=plugin.module_name, global_disable=True).exists():
                plugin.status = "black"
            elif await PluginWithdraw.filter(name=plugin.module_name, global_withdraw=True).exists():
                plugin.status = "green"
            elif await PluginTime.filter(name=plugin.module_name, global_time=True).exists():
                plugin.status = "blue"

            elif message_type == 'group':
                if await PluginDisable.filter(name=plugin.module_name, group_id=session_id, user_id=None).exists():
                    plugin.status = "black"
                elif await PluginWithdraw.filter(name=plugin.module_name, group_id=session_id, user_id=None).exists():
                    plugin.status = "green"
                elif await PluginTime.filter(name=plugin.module_name, group_id=session_id, user_id=None).exists():
                    plugin.status = "blue"
                else:
                    plugin.status = "orange"
            elif message_type == 'guild':
                plugin.status = "orange"
            else:
                if await PluginDisable.filter(name=plugin.module_name, user_id=session_id).exists():
                    plugin.status = "black"
                elif await PluginWithdraw.filter(name=plugin.module_name, user_id=session_id).exists():
                    plugin.status = "green"
                elif await PluginTime.filter(name=plugin.module_name, user_id=session_id).exists():
                    plugin.status = "blue"
                else:
                    plugin.status = "orange"

            if plugin.matchers:
                plugin.matchers.sort(key=lambda x: x.pm_priority)
        return plugin_list

    @classmethod
    async def get_plugin_list_for_admin(cls) -> List[dict]:
        """
        获取插件列表（供Web UI使用）
        """
        load_plugins = [p.name for p in nb_plugin.get_loaded_plugins()]
        plugin_list = [p.dict(exclude={'status'})
                       for p in cls.plugins.values()]
        for plugin in plugin_list:
            plugin['matchers'].sort(key=lambda x: x['pm_priority'])
            plugin['isLoad'] = plugin['module_name'] in load_plugins
            plugin['status'] = not await PluginDisable.filter(name=plugin['module_name'], global_disable=True).exists()
        plugin_list.sort(key=lambda x: (
            x['isLoad'], x['status'], -x['priority']), reverse=True)
        return plugin_list


@run_preprocessor
async def _(event: MessageEvent, bot: Bot, matcher: Matcher):
    if event.user_id in SUPERUSERS:
        return
    if not matcher.plugin_name or matcher.plugin_name in HIDDEN_PLUGINS:
        return
    if not isinstance(event, (PrivateMessageEvent, GroupMessageEvent)):
        return

    # 权限检查
    is_ignored = False
    message_bool = False
    try:
        # 禁用
        if await PluginDisable.get_or_none(name=matcher.plugin_name, global_disable=True):
            is_ignored = True
        if await PluginDisable.get_or_none(name=matcher.plugin_name, user_id=event.user_id, group_id=None):
            is_ignored = True
        elif isinstance(event, GroupMessageEvent) and (
                perms := await PluginDisable.filter(name=matcher.plugin_name, group_id=event.group_id)):
            user_ids = [p.user_id for p in perms]
            if None in user_ids or event.user_id in user_ids:
                is_ignored = True
        # 限流
        if (id := await PluginTime.get_or_none(name=matcher.plugin_name, global_time=True)) or \
                (id := await PluginTime.get_or_none(name=matcher.plugin_name, user_id=event.user_id, group_id=None)):
            if id.type == "time":
                if freqLimiter.check(f'{matcher.plugin_name}-{event.user_id}'):
                    freqLimiter.start(
                        f'{matcher.plugin_name}-{event.user_id}', id.time)
                else:
                    msg = f'{matcher.plugin_name}冷却ing...剩余{freqLimiter.left(f"{matcher.plugin_name}-{event.user_id}")}秒'
                    is_ignored = message_bool = True
            else:
                if not await XlCount(f'{matcher.plugin_name}-{event.user_id}', id.time):
                    msg = f'{matcher.plugin_name}本分钟使用次数达到上限...'
                    is_ignored = message_bool = True

        elif isinstance(event, GroupMessageEvent) and (
                perms := await PluginTime.filter(name=matcher.plugin_name, group_id=event.group_id)):
            user_ids = {}
            for p in perms:
                if (p.user_id == None) and (id := await PluginTime.get_or_none(name=matcher.plugin_name, user_id=None, group_id=event.group_id)):
                    user_ids[event.user_id] = id.time
                else:
                    user_ids[p.user_id] = p.time
            if None in user_ids or event.user_id in user_ids:
                if id.type == "time":
                    if freqLimiter.check(f'{matcher.plugin_name}-{event.group_id}-{event.user_id}'):
                        freqLimiter.start(
                            f'{matcher.plugin_name}-{event.group_id}-{event.user_id}',  user_ids[event.user_id])
                    else:
                        msg = f'{matcher.plugin_name}冷却ing...剩余{freqLimiter.left(f"{matcher.plugin_name}-{event.group_id}-{event.user_id}")}秒'
                        is_ignored = message_bool = True
                else:
                    if not await XlCount(f'{matcher.plugin_name}-{event.group_id}-{event.user_id}', user_ids[event.user_id]):
                        msg = f'{matcher.plugin_name}本分钟使用次数达到上限...'
                        is_ignored = message_bool = True
    except Exception as e:
        logger.info('插件管理器', f'插件权限检查<r>失败：{e}</r>')

    if message_bool and Pm_config.pm_message and msg:
        await bot.send(event=event, message=msg, reply_message=True)

    if is_ignored:
        raise IgnoredException('插件使用权限已禁用')

    with contextlib.suppress(Exception):
        # 命令调用统计
        if matcher.plugin_name in PluginManager.plugins and 'pm_name' in matcher.state:
            if matcher_info := list(filter(lambda x: x.pm_name == matcher.state['pm_name'],
                                           PluginManager.plugins[matcher.plugin_name].matchers)):
                matcher_info = matcher_info[0]
                await PluginStatistics.create(plugin_name=matcher.plugin_name,
                                              matcher_name=matcher_info.pm_name,
                                              matcher_usage=matcher_info.pm_usage,
                                              group_id=event.group_id if isinstance(
                                                  event, GroupMessageEvent) else None,
                                              user_id=event.user_id,
                                              message_type=event.message_type,
                                              time=datetime.datetime.now())


@Bot.on_called_api
async def _(bot: Bot, exception: Optional[Exception], api: str, data: Any, result: Any):
    if exception or str(api) != "send_msg":
        return
    try:
        event = current_event.get()
        matcher = current_matcher.get()
    except LookupError:
        return
    if event.user_id in SUPERUSERS:
        return
    if not matcher.plugin_name or matcher.plugin_name in HIDDEN_PLUGINS:
        return
    if not isinstance(event, (PrivateMessageEvent, GroupMessageEvent)):
        return
    try:
        tasks = []
        if (id := await PluginWithdraw.get_or_none(name=matcher.plugin_name, global_withdraw=True)) or \
                (id := await PluginWithdraw.get_or_none(name=matcher.plugin_name, user_id=event.user_id, group_id=None)):
            tasks.append(asyncio.ensure_future(withdraw_message(
                bot=bot, message_id=result["message_id"], time=id.time)))
        elif isinstance(event, GroupMessageEvent) and (
                perms := await PluginWithdraw.filter(name=matcher.plugin_name, group_id=event.group_id)):
            user_ids = {}
            for p in perms:
                if (p.user_id == None) and (id := await PluginWithdraw.get_or_none(name=matcher.plugin_name, user_id=None, group_id=event.group_id)):
                    user_ids[event.user_id] = id.time
                else:
                    user_ids[p.user_id] = p.time
            if None in user_ids or event.user_id in user_ids:
                tasks.append(asyncio.ensure_future(withdraw_message(
                    bot=bot, message_id=result["message_id"], time=user_ids[event.user_id])))
    except Exception as e:
        logger.info('插件管理器[撤回]', f'插件权限检查<r>失败：{e}</r>')
