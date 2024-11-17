from nonebot import require
require("nonebot_plugin_localstore")
require("nonebot_plugin_tortoise_orm")
require("nonebot_plugin_apscheduler")
from .utils import (
    SUPERUSERS,
    DRIVER,
    CommandObjectID,
    fullmatch_rule,
    cache_help,
    get_list,
)
from .logger import logger
from .pm_config import Config
# 加载web
from . import web_api, web_page
from .draw_help import draw_help
from nonebot.typing import T_State
from nonebot.params import RegexDict
from .plugin.manage import PluginManager
from nonebot import on_regex, on_command
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageEvent,
    Bot,
)
from .models import PluginDisable, PluginTime, PluginWithdraw


__plugin_meta__ = PluginMetadata(
    name='PM帮助',
    description='自动插件管理器，可以自动生成帮助图，并对群/私聊进行权限管理，例如禁用，限流，撤回',
    usage='help',
    type="application",
    homepage="https://github.com/CM-Edelweiss/nonebot-plugin-pmhelp",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={
        'author': 'CM-Edelweiss',
        'version': '1.3.0',
        'priority': 1,
    },
)


@DRIVER.on_startup
async def startup():
    # 初始化
    await PluginManager.init()


manage_cmd = on_regex(
    r"^pm (?P<func>ban|unban) (?P<plugin>([\w ]*)|all|全部) ?(-g (?P<group>([\w ]*)|all|全部) ?)?(-u (?P<user>([\w ]*)|all|全部) ?)?(-x (?P<type>(t|f))(?P<time>([\d ]*)) ?)?(-w (?P<withdraw>([\d ]*)) ?)?",
    priority=2,
    block=True,
    state={
        "pm_name": "pm-ban|unban",
        "pm_description": "禁用|取消禁用插件的群|用户使用权限/进行限流/延迟撤回",
        "pm_usage": "pm ban|unban <中/英插件名>",
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
    state["user_id"] = event.user_id
    state["bool"] = match["func"] == "unban"
    state["plugin_no_exist"] = []
    state["type"] = match["type"]
    state["withdraw"] = match["withdraw"]
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
    state["user_id"] = event.user_id
    state["bool"] = match["func"] == "unban"
    state["plugin_no_exist"] = []
    state["type"] = match["type"]
    state["withdraw"] = match["withdraw"]
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
    if not state['group'] and not state['user'] and (state["user_id"] not in SUPERUSERS):
        await manage_cmd.finish('用法：pm ban|unban 插件名 -g 群号列表 -u 用户列表 -x t|f 时间/次数', at_sender=True)
    if state['session_id'] in cache_help:
        del cache_help[state['session_id']]
    if not state['plugin'] and state['plugin_no_exist']:
        await manage_cmd.finish(f'没有叫{" ".join(state["plugin_no_exist"])}的插件')
    extra_msg = f'，但没有叫{" ".join(state["plugin_no_exist"])}的插件。' if state['plugin_no_exist'] else '。'
    filter_arg = {}
    # 撤回
    if state["withdraw"]:
        if state["user_id"] in SUPERUSERS:
            await PluginWithdraw.filter(name__in=state['plugin'], global_withdraw=True).delete()
        if state['group']:
            filter_arg['group_id__in'] = state['group']
            if state['user']:
                filter_arg['user_id__in'] = state['user']
                logger.info('插件管理器',
                            f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}群<m>{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}</m>中用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的插件<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}</m>的延迟撤回{"" if  state["bool"] else ",时间:"+state["withdraw"]}')
                msg = f'已{"启用" if not state["bool"] else "禁用"}群{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}中用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的插件{" ".join(state["plugin"]) if not state["is_all"] else "全部"}的延迟撤回{"" if  state["bool"] else ",时间:"+state["withdraw"]} {extra_msg}'
            else:
                filter_arg['user_id'] = None
                logger.info('插件管理器',
                            f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}群<m>{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}</m>的插件<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}</m>的延迟撤回{"" if  state["bool"] else ",时间:"+state["withdraw"]}')
                msg = f'已{"启用" if not state["bool"] else "禁用"}群{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}的插件{" ".join(state["plugin"]) if not state["is_all"] else "全部"}的延迟撤回{"" if  state["bool"] else ",时间:"+state["withdraw"]}{extra_msg}'
        elif state['user']:
            filter_arg['user_id__in'] = state['user']
            filter_arg['group_id'] = None
            logger.info('插件管理器',
                        f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的插件<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}</m>的延迟撤回{"" if  state["bool"] else ",时间:"+state["withdraw"]}')
            msg = f'已{"启用" if not state["bool"] else "禁用"}用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的插件{" ".join(state["plugin"]) if not state["is_all"] else "全部"}的延迟撤回{"" if  state["bool"] else ",时间:"+state["withdraw"]}{extra_msg}'
        elif state["user_id"] in SUPERUSERS:
            logger.info('插件管理器',
                        f'已{"<g>启用全局</g>" if not state["bool"] else "<r>禁用全局</r>"}插件<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}</m>的延迟撤回{"" if  state["bool"] else ",时间:"+state["withdraw"]}')
            msg = f'已{"启用全局" if not state["bool"] else "禁用全局"}插件{" ".join(state["plugin"]) if not state["is_all"] else "全部"}的延迟撤回{"" if  state["bool"] else ",时间:"+state["withdraw"]} {extra_msg}'
        await PluginWithdraw.filter(name__in=state['plugin'], **filter_arg).delete()
        if not state['bool']:
            for plugin in state['plugin']:
                if state['group']:
                    for group in state['group']:
                        if state['user']:
                            for user in state['user']:
                                await PluginWithdraw.update_or_create(name=plugin, group_id=group, user_id=user, time=state["withdraw"])
                        else:
                            await PluginWithdraw.update_or_create(name=plugin, group_id=group, user_id=None, time=state["withdraw"])
                elif state['user']:
                    for user in state['user']:
                        await PluginWithdraw.update_or_create(name=plugin, user_id=user, group_id=None, time=state["withdraw"])
                else:
                    await PluginWithdraw.create(name=plugin, global_withdraw=True, time=state["withdraw"])
    # 限流
    elif state['type']:
        state["type"] = ("frequency" if state['type'] == "f" else "time")
        t = '' if state['bool'] else f'类型:{"倒计时类" if state["type"] == "time" else "每分钟类"}\n数值:{state["time"]}'
        if state["user_id"] in SUPERUSERS:
            await PluginTime.filter(name__in=state['plugin'], global_time=True).delete()
        if state['group']:
            filter_arg['group_id__in'] = state['group']
            if state['user']:
                filter_arg['user_id__in'] = state['user']
                logger.info('插件管理器',
                            f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}群<m>{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}</m>中用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件</m>限流限制，<m>{t}</m>')
                msg = f'已{"开启" if not state["bool"] else "关闭"}群{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}中用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件限流限制\n{t} {extra_msg}'
            else:
                filter_arg['user_id'] = None
                logger.info('插件管理器',
                            f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}群<m>{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}</m>的<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件</m>限流限制，<m>{t}</m>')
                msg = f'已{"启用" if not state["bool"] else "禁用"}群{" ".join(map(str, state["group"])) if not state["group_all"] else "全部"}的{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件限流限制\n{t} {extra_msg}'
        elif state['user']:
            filter_arg['user_id__in'] = state['user']
            filter_arg['group_id'] = None
            logger.info('插件管理器',
                        f'已{"<g>启用</g>" if not state["bool"] else "<r>禁用</r>"}用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件</m>限流限制，<m>{t}</m>')
            msg = f'已{"启用" if not state["bool"] else "禁用"}用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件限流限制\n{t} {extra_msg}'
        elif state["user_id"] in SUPERUSERS:
            logger.info('插件管理器',
                        f'已{"<g>启用全局</g>" if not state["bool"] else "<r>禁用全局</r>"}<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件</m>限流限制，<m>{t}</m>')
            msg = f'已{"启用全局" if not state["bool"] else "禁用全局"}{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件限流限制\n{t} {extra_msg}'
        else:
            await manage_cmd.finish("你没有权限使用该命令", at_sender=True)
        await PluginTime.filter(name__in=state['plugin'], **filter_arg).delete()
        if not state['bool']:
            for plugin in state['plugin']:
                if state['group']:
                    for group in state['group']:
                        if state['user']:
                            for user in state['user']:
                                await PluginTime.update_or_create(name=plugin, group_id=group, user_id=user, type=state['type'], time=state['time'])
                        else:
                            await PluginTime.update_or_create(name=plugin, group_id=group, user_id=None, type=state['type'], time=state['time'])
                elif state['user']:
                    for user in state['user']:
                        await PluginTime.update_or_create(name=plugin, user_id=user, group_id=None, type=state['type'], time=state['time'])
                else:
                    await PluginTime.create(name=plugin, global_time=True, type=state['type'], time=state['time'])
    # 禁用
    else:
        if state["user_id"] in SUPERUSERS:
            await PluginDisable.filter(name__in=state['plugin'], global_disable=True).delete()
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
        elif state['user']:
            filter_arg['user_id__in'] = state['user']
            filter_arg['group_id'] = None
            logger.info('插件管理器',
                        f'已{"<g>启用</g>" if state["bool"] else "<r>禁用</r>"}用户<m>{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}</m>的插件<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}</m>使用权限')
            msg = f'已{"启用" if state["bool"] else "禁用"}用户{" ".join(map(str, state["user"])) if not state["user_all"] else "全部"}的插件{" ".join(state["plugin"]) if not state["is_all"] else "全部"}使用权限{extra_msg}'
        elif state["user_id"] in SUPERUSERS:
            logger.info('插件管理器',
                        f'已{"<g>启用全局</g>" if state["bool"] else "<r>禁用全局</r>"}<m>{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件</m>使用权限')
            msg = f'已{"启用全局" if state["bool"] else "禁用全局"}{" ".join(state["plugin"]) if not state["is_all"] else "全部"}插件使用权限 {extra_msg}'
        else:
            await manage_cmd.finish("你没有权限使用该命令", at_sender=True)
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
                elif state['user']:
                    for user in state['user']:
                        await PluginDisable.update_or_create(name=plugin, user_id=user, group_id=None)
                else:
                    await PluginDisable.create(name=plugin, global_disable=True)
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
