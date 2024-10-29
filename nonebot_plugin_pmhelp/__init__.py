from nonebot import on_regex, on_command
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageEvent,
    Bot,
)
from nonebot.params import RegexDict
from nonebot.typing import T_State
from nonebot.plugin import PluginMetadata

from .utils import (
    SUPERUSERS,
    DRIVER,
    CommandObjectID,
    fullmatch_rule,
    cache_help,
    get_list,
)
from .plugin.manage import PluginManager
from .models import PluginDisable, PluginTime
from .logger import logger
from .draw_help import draw_help
from .pm_config import Config

# 加载web
from . import web_api, web_page

__plugin_meta__ = PluginMetadata(
    name='PM帮助',
    description='根据加载的nonebot2插件管理器，可以自动生成帮助图，源自LittlePaimon',
    usage='help',
    type="application",
    homepage="https://github.com/CM-Edelweiss/nonebot-plugin-pmhelp",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={
        'author': 'CM-Edelweiss',
        'version': '1.2',
        'priority': 1,
    },
)


@DRIVER.on_startup
async def startup():
    await PluginManager.init()


manage_cmd = on_regex(
    r"^pm (?P<func>ban|unban) (?P<plugin>([\w ]*)|all|全部) ?(-g (?P<group>([\w ]*)|all|全部) ?)?(-u (?P<user>([\w ]*)|all|全部) ?)?(-x (?P<type>(t|f))(?P<time>([\d ]*)) ?)?",
    priority=2,
    block=True,
    state={
        "pm_name": "pm-ban|unban",
        "pm_description": "禁用|取消禁用插件的群|用户使用权限或者进行限流",
        "pm_usage": "pm ban|unban <插件名>",
        "pm_priority": 2,
    },
)
help_cmd = on_command(
    "help",
    aliases={"帮助", "菜单", "pm help"},
    priority=1,
    rule=fullmatch_rule,
    block=True,
    state={
        "pm_name": "pm-help",
        "pm_description": "查看本帮助",
        "pm_usage": "help",
        "pm_priority": 1,
    },
)


@manage_cmd.handle()
async def _(
    event: GroupMessageEvent,
    bot: Bot,
    state: T_State,
    match: dict = RegexDict(),
    session_id: int = CommandObjectID(),
):
    if event.user_id not in SUPERUSERS and event.sender.role not in ["admin", "owner"]:
        await manage_cmd.finish("你没有权限使用该命令", at_sender=True)
    state["session_id"] = session_id
    state["bool"] = match["func"] == "unban"
    state["plugin_no_exist"] = []
    state["type"] = ("time" if match["type"] == "t" else "frequency")
    state["time"] = match["time"] if match["time"] else 10
    if any(w in match["plugin"] for w in {"all", "全部"}):
        state["is_all"] = True
        state["plugin"] = list(PluginManager.plugins.keys())
    else:
        state["is_all"] = False
        state["plugin"] = []
        for plugin in match["plugin"].strip().split(" "):
            if plugin in PluginManager.plugins.keys():
                state["plugin"].append(plugin)
            elif module_name := list(
                filter(
                    lambda x: PluginManager.plugins[x].name == plugin,
                    PluginManager.plugins.keys(),
                )
            ):
                state["plugin"].append(module_name[0])
            else:
                state["plugin_no_exist"].append(plugin)
    state["group_all"] = False
    if not match["group"] or event.user_id not in SUPERUSERS:
        state["group"] = [event.group_id]
    elif any(w in match["group"] for w in {"all", "全部"}) and event.user_id in SUPERUSERS:
        state["group_all"] = True
        state["group"] = await get_list(await bot.get_group_list(), True)
    else:
        state["group"] = [int(group)
                          for group in match["group"].strip().split(" ")]

    state["user_all"] = False
    if match["user"] and any(w in match["user"] for w in {"all", "全部"}):
        state["user_all"] = True
        state["user"] = await get_list(await bot.get_group_member_list(group_id=event.group_id), False)
    else:
        state["user"] = (
            [int(user) for user in match["user"].strip().split(" ")]
            if match["user"] and (str(int(match["user"]))).isdigit()
            else None
        )


@manage_cmd.handle()
async def _(
    event: PrivateMessageEvent,
    bot: Bot,
    state: T_State,
    match: dict = RegexDict(),
    session_id: int = CommandObjectID(),
):
    if event.user_id not in SUPERUSERS:
        await manage_cmd.finish("你没有权限使用该命令", at_sender=True)
    state["session_id"] = session_id
    state["bool"] = match["func"] == "unban"
    state["plugin_no_exist"] = []
    state["type"] = ("time" if match["type"] == "t" else "frequency")
    state["time"] = match["time"] if match["time"] else 10
    if any(w in match["plugin"] for w in {"all", "全部"}):
        state["is_all"] = True
        state["plugin"] = [
            p for p in PluginManager.plugins.keys() if p != "nonebot_plugin_pmhelp"
        ]
    else:
        state["is_all"] = False
        state["plugin"] = []
        for plugin in match["plugin"].strip().split(" "):
            if plugin in PluginManager.plugins.keys():
                state["plugin"].append(plugin)
            elif module_name := list(
                filter(
                    lambda x: PluginManager.plugins[x].name == plugin,
                    PluginManager.plugins.keys(),
                )
            ):
                state["plugin"].append(module_name[0])
            else:
                state["plugin_no_exist"].append(plugin)
    state["group_all"] = False
    if match["group"] and any(w in match["group"] for w in {"all", "全部"}):
        state["group_all"] = True
        state["group"] = await get_list(await bot.get_group_list(), True)
    else:
        state["group"] = (
            [int(group) for group in match["group"].strip().split(" ")]
            if match["group"] and (str(int(match["group"]))).isdigit()
            else None
        )
    state["user_all"] = False
    if match["user"] and any(w in match["user"] for w in {"all", "全部"}):
        state["user_all"] = True
        state["user"] = await get_list(await bot.get_friend_list(), False)
    else:
        state["user"] = (
            [int(user) for user in match["user"].strip().split(" ")]
            if match["user"] and (str(int(match["user"]))).isdigit()
            else None
        )


@manage_cmd.got('bool')
async def _(state: T_State):
    if not state['group'] and not state['user']:
        await manage_cmd.finish('用法：pm ban|unban 插件名 -g 群号列表 -u 用户列表 -x t|f 时间/次数', at_sender=True)
    if state['session_id'] in cache_help:
        del cache_help[state['session_id']]
    if not state['plugin'] and state['plugin_no_exist']:
        await manage_cmd.finish(f'没有叫{" ".join(state["plugin_no_exist"])}的插件')
    extra_msg = f'，但没有叫{" ".join(state["plugin_no_exist"])}的插件。' if state['plugin_no_exist'] else '。'
    cache_help.clear()
    filter_arg = {}
    if state['type']:
        if state['group']:
            filter_arg['group_id__in'] = state['group']
            if state['user']:
                filter_arg['user_id__in'] = state['user']
                logger.info('插件管理器',
                            f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}群<m>{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}</m>中用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件</m>使用权限，<m>类型{state["type"]}-时间{state["time"]}</m>')
                msg = f'已{"开启" if not state["bool"] else "关闭"}群{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}中用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件使用限制，\n类型{state["type"]}-时间{state["time"]} {extra_msg}'
            else:
                filter_arg['user_id'] = None
                logger.info('插件管理器',
                            f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}群<m>{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}</m>的<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件</m>使用权限，<m>类型{state["type"]}-时间{state["time"]}</m>')
                msg = f'已{"启用" if not state["bool"] else "禁用"}群{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}的{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件使用限制，\n类型{state["type"]}-时间{state["time"]} {extra_msg}'
        else:
            filter_arg['user_id__in'] = state['user']
            filter_arg['group_id'] = None
            logger.info('插件管理器',
                        f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件</m>使用权限，<m>类型{state["type"]}-时间{state["time"]}</m>')
            msg = f'已{"启用" if not state["bool"] else "禁用"}用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件使用限制，\n类型{state["type"]}-时间{state["time"]} {extra_msg}'
        await PluginTime.filter(name__in=state['plugin'], **filter_arg).delete()
        if state['bool']:
            pass
        else:
            for plugin in state['plugin']:
                if state['group']:
                    for group in state['group']:
                        if state['user']:
                            for user in state['user']:
                                await PluginTime.update_or_create(name=plugin, group_id=group, user_id=user, type=state['type'], time=state['time'])
                        else:
                            await PluginTime.update_or_create(name=plugin, group_id=group, user_id=None, type=state['type'], time=state['time'])
                else:
                    for user in state['user']:
                        await PluginTime.update_or_create(name=plugin, user_id=user, group_id=None, type=state['type'], time=state['time'])
    else:
        if state['group']:
            filter_arg['group_id__in'] = state['group']
            if state['user']:
                filter_arg['user_id__in'] = state['user']
                logger.info('插件管理器',
                            f'已{"<g>启用</g>" if state["bool"] else "<r>禁用</r>"}群<m>{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}</m>中用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的插件<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}</m>使用权限')
                msg = f'已{"启用" if state["bool"] else "禁用"}群{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}中用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的插件{" ".join(state["plugin"]) if not state["is_all"] else "全部"}使用权限{extra_msg}'
            else:
                filter_arg['user_id'] = None
                logger.info('插件管理器',
                            f'已{"<g>启用</g>" if state["bool"] else "<r>禁用</r>"}群<m>{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}</m>的插件<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}</m>使用权限')
                msg = f'已{"启用" if state["bool"] else "禁用"}群{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}的插件{" ".join(state["plugin"]) if not state["is_all"] else "全部"}使用权限{extra_msg}'
        else:
            filter_arg['user_id__in'] = state['user']
            filter_arg['group_id'] = None
            logger.info('插件管理器',
                        f'已{"<g>启用</g>" if state["bool"] else "<r>禁用</r>"}用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的插件<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}</m>使用权限')
            msg = f'已{"启用" if state["bool"] else "禁用"}用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的插件{" ".join(state["plugin"]) if not state["is_all"] else "全部"}使用权限{extra_msg}'
        if state['bool']:
            await PluginDisable.filter(name__in=state['plugin'], **filter_arg).delete()
        else:
            for plugin in state['plugin']:
                if state['group']:
                    for group in state['group']:
                        if state['user']:
                            for user in state['user']:
                                await PluginDisable.update_or_create(name=plugin, group_id=group, user_id=user)
                        else:
                            await PluginDisable.update_or_create(name=plugin, group_id=group, user_id=None)
                else:
                    for user in state['user']:
                        await PluginDisable.update_or_create(name=plugin, user_id=user, group_id=None)

    await manage_cmd.finish(msg)


@help_cmd.handle()
async def _(event: MessageEvent, session_id: int = CommandObjectID()):
    if session_id in cache_help:
        await help_cmd.finish(cache_help[session_id])
    else:
        plugin_list = await PluginManager.get_plugin_list(
            event.message_type,
            (
                event.user_id
                if isinstance(event, PrivateMessageEvent)
                else (
                    event.group_id
                    if isinstance(event, GroupMessageEvent)
                    else event.guild_id
                )
            ),
        )
        img = await draw_help(plugin_list)
        cache_help[session_id] = img
        await help_cmd.finish(img)
