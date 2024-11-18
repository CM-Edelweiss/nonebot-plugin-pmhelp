import asyncio
import datetime
from jose import jwt
import importlib.util
try:
    import ujson as json
except:
    import json
from .logger import logger
from fastapi import FastAPI
from .Path import USERID_ALL
from pydantic import BaseModel
from .pm_config import Pm_config
from nonebot import get_app, get_adapter
from .utils import DRIVER, requestAdaptor
from .web_page import login_page, admin_app
from .models import PluginDisable, PluginTime
from nonebot.adapters.onebot.v11 import Adapter
from .plugin.manage import PluginManager, PluginInfo, PluginWithdraw
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse


class UserModel(BaseModel):
    username: str
    password: str


spec = importlib.util.find_spec("nonebot_plugin_manageweb")
if spec is not None:
    from nonebot import require
    require("nonebot_plugin_manageweb")
    from nonebot_plugin_manageweb.utils import responseAdaptor, authentication  # type: ignore
    from nonebot_plugin_manageweb.web.page.main import admin_app as admin  # type: ignore
    from amis import PageSchema
    mw_web = True
else:
    from .utils import responseAdaptor, authentication
    mw_web = False


@DRIVER.on_startup
async def init_web():
    """主程序"""
    if not Pm_config.pm_enable_web:
        return
    try:
        app: FastAPI = get_app()
        if mw_web:
            logger.info(
                "PM Web UI",
                f"<g>启用成功</g>，已接入<m>[MW webui]http://{DRIVER.config.host}:{DRIVER.config.port}/mw/login</m>",
            )
        else:
            logger.info(
                "PM Web UI",
                f"<g>启用成功</g>，地址为<m>http://{DRIVER.config.host}:{DRIVER.config.port}/pmhelp/login</m>",
            )
    except Exception as e:
        return logger.info('PM Web UI', f'启用<r>失败：{e}</r>')

    @app.post("/pmhelp/api/login", response_class=JSONResponse)
    async def login(user: UserModel):
        """登录api"""
        if (
            user.username != Pm_config.pm_username
            or user.password != Pm_config.pm_password
        ):
            return {"status": -100, "msg": "登录失败，请确认用户ID和密码无误"}
        token = jwt.encode(
            {
                "username": user.username,
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(minutes=30),
            },
            Pm_config.pm_secret_key,
            algorithm="HS256",
        )
        return {"status": 0, "msg": "登录成功", "data": {"token": token}}

    @app.get(
        '/pmhelp/api/get_groups_and_members',
        response_class=JSONResponse,
        dependencies=[authentication()],
    )
    async def get_groups_and_members():
        """获取群和好友列表api"""
        bots = get_adapter(Adapter).bots
        if len(bots) == 0:
            return {"status": -100, "msg": "获取群和好友列表失败，请确认已连接QQ"}
        bot = list(bots.values())[0]
        PATH = USERID_ALL / f"{bot.self_id}.json"
        if PATH.exists() and PATH.is_file():
            with open(PATH, 'r', encoding='utf-8') as load_f:
                data = json.load(load_f)
            return data
        else:
            return {"status": -100, "msg": "请使用按钮刷新群和好友列表"}

    @app.post(
        '/pmhelp/api/get_groups_flushed',
        response_class=JSONResponse,
        dependencies=[authentication()],
    )
    async def get_groups_flushed():
        """更新群和好友列表api"""
        result = []
        bots = get_adapter(Adapter).bots
        if len(bots) == 0:
            return {"status": -100, "msg": "获取群和好友列表失败，请确认已连接QQ"}
        bot = list(bots.values())[0]
        group_list = await bot.get_group_list()
        friend_list = await bot.get_friend_list()
        for group in group_list:
            group_members = await bot.get_group_member_list(group_id=group['group_id'])
            result.append(
                {
                    'left_label': f'{group["group_name"]}({group["group_id"]})',
                    'right_label': f'{group["group_name"]}(群{group["group_id"]})',
                    'value': f'群{group["group_id"]}',
                    'children': [
                        {
                            'left_label': f'{m["card"] or m["nickname"]}({m["user_id"]})',
                            'right_label': f'群({group["group_name"]}) - {m["card"] or m["nickname"]}({m["user_id"]})',
                            'value': f'群{group["group_id"]}.{m["user_id"]}',
                        }
                        for m in group_members
                        if str(m['user_id']) != bot.self_id
                    ],
                }
            )
            await asyncio.sleep(0.3)

        result = [
            {'label': '群组', 'selectMode': 'tree',
                'searchable': True, 'children': result},
            {
                'label': '好友',
                'selectMode': 'list',
                'searchable': True,
                'children': [
                    {
                        'left_label': f'{f["nickname"]}({f["user_id"]})',
                        'right_label': f'{f["nickname"]}({f["user_id"]})',
                        'value': f'{f["user_id"]}',
                    }
                    for f in friend_list
                    if str(f['user_id']) != bot.self_id
                ],
            },
        ]
        try:
            with open(USERID_ALL / f"{bot.self_id}.json", 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
        except Exception as e:
            return {"status": -100, "msg": e}
        return {"status": 0, "msg": "刷新成功"}

    @app.get('/pmhelp/api/get_plugins', response_class=JSONResponse, dependencies=[authentication()])
    async def get_plugins():
        """获取插件列表api"""
        plugins = await PluginManager.get_plugin_list_for_admin()
        return {
            'status': 0,
            'msg': 'ok',
            'data': {
                'rows': plugins,
                'total': len(plugins)
            }
        }

    @app.post('/pmhelp/api/set_plugin_status', response_class=JSONResponse, dependencies=[authentication()])
    async def set_plugin_status(data: dict):
        """保存插件禁用状态api（全局）"""
        module_name: str = data.get('plugin')
        status: bool = data.get('status')
        try:
            from .utils import cache_help
            cache_help.clear()
        except Exception:
            pass
        if status:
            await PluginDisable.filter(name=module_name, global_disable=True).delete()
        else:
            await PluginDisable.create(name=module_name, global_disable=True)
        return {'status': 0, 'msg': f'成功设置{module_name}插件状态为{status}'}

    @app.get('/pmhelp/api/get_plugin_bans', response_class=JSONResponse, dependencies=[authentication()])
    async def get_plugin_bans(module_name: str):
        """获取插件禁用状态api"""
        result = []
        bans = await PluginDisable.filter(name=module_name).all()
        for ban in bans:
            if ban.user_id and ban.group_id:
                result.append(f'群{ban.group_id}.{ban.user_id}')
            elif ban.group_id and not ban.user_id:
                result.append(f'群{ban.group_id}')
            elif ban.user_id and not ban.group_id:
                result.append(f'{ban.user_id}')
        return {
            'status': 0,
            'msg':    'ok',
            'data':   {
                'module_name': module_name,
                'bans': result
            }
        }

    @app.post('/pmhelp/api/set_plugin_bans', response_class=JSONResponse, dependencies=[authentication()])
    async def set_plugin_bans(data: dict):
        """保存插件禁用状态api（自定义）"""
        bans = data['bans']
        name = data['module_name']
        await PluginDisable.filter(name=name, global_disable=False).delete()
        for ban in bans:
            if ban.startswith('群'):
                if '.' in ban:
                    group_id = int(ban.split('.')[0][1:])
                    user_id = int(ban.split('.')[1])
                    await PluginDisable.create(name=name, group_id=group_id, user_id=user_id)
                else:
                    await PluginDisable.create(name=name, group_id=int(ban[1:]))
            else:
                await PluginDisable.create(name=name, user_id=int(ban))
        try:
            from .utils import cache_help
            cache_help.clear()
        except Exception:
            pass
        return {
            'status': 0,
            'msg':    '插件权限设置成功'
        }

    @app.get('/pmhelp/api/get_message_bans', response_class=JSONResponse, dependencies=[authentication()])
    async def get_message_bans(module_name: str):
        """获取插件限流状态api"""
        result = []
        global_time = False
        bans = await PluginTime.filter(name=module_name).all()
        for ban in bans:
            global_time = True if ban.global_time else False
            if ban.user_id and ban.group_id:
                result.append(f'群{ban.group_id}.{ban.user_id}')
            elif ban.group_id and not ban.user_id:
                result.append(f'群{ban.group_id}')
            elif ban.user_id and not ban.group_id:
                result.append(f'{ban.user_id}')
        return {
            'status': 0,
            'msg':    'ok',
            'data':   {
                'module_name': module_name,
                'bans': result,
                'show': global_time
            }
        }

    @app.post('/pmhelp/api/set_message_bans', response_class=JSONResponse, dependencies=[authentication()])
    async def set_message_bans(data: dict):
        """保存插件限流状态api"""
        bans = data['bans']
        name = data['module_name']
        type = data['type']
        time = data["time"]
        await PluginTime.filter(name=name).delete()
        if ("all" in data) and data["all"]:
            await PluginTime.create(name=name, global_time=True, type=type, time=time)
        else:
            for ban in bans:
                if ban.startswith('群'):
                    if '.' in ban:
                        group_id = int(ban.split('.')[0][1:])
                        user_id = int(ban.split('.')[1])
                        await PluginTime.update_or_create(name=name, group_id=group_id, user_id=user_id, type=type, time=time)
                    else:
                        await PluginTime.update_or_create(name=name, group_id=int(ban[1:]), type=type, time=time)
                else:
                    await PluginTime.update_or_create(name=name, user_id=int(ban), type=type, time=time)
        try:
            from .utils import cache_help
            cache_help.clear()
        except Exception:
            pass
        return {
            'status': 0,
            'msg':    '插件设置成功'
        }

    @app.get('/pmhelp/api/get_withdraw_bans', response_class=JSONResponse, dependencies=[authentication()])
    async def get_withdraw_bans(module_name: str):
        """获取插件撤回状态api"""
        result = []
        global_withdraw = False
        bans = await PluginWithdraw.filter(name=module_name).all()
        for ban in bans:
            global_withdraw = True if ban.global_withdraw else False
            if ban.user_id and ban.group_id:
                result.append(f'群{ban.group_id}.{ban.user_id}')
            elif ban.group_id and not ban.user_id:
                result.append(f'群{ban.group_id}')
            elif ban.user_id and not ban.group_id:
                result.append(f'{ban.user_id}')

        return {
            'status': 0,
            'msg':    'ok',
            'data':   {
                'module_name': module_name,
                'bans': result,
                'show': global_withdraw
            }
        }

    @app.post('/pmhelp/api/set_withdraw_bans', response_class=JSONResponse, dependencies=[authentication()])
    async def set_withdraw_bans(data: dict):
        """保存插件撤回状态api"""
        bans = data['bans']
        name = data['module_name']
        time = data["time"]
        await PluginWithdraw.filter(name=name).delete()
        if ("all" in data) and data["all"]:
            await PluginWithdraw.create(name=name, global_withdraw=True, time=time)
        else:
            for ban in bans:
                if ban.startswith('群'):
                    if '.' in ban:
                        group_id = int(ban.split('.')[0][1:])
                        user_id = int(ban.split('.')[1])
                        await PluginWithdraw.update_or_create(name=name, group_id=group_id, user_id=user_id, time=time)
                    else:
                        await PluginWithdraw.update_or_create(name=name, group_id=int(ban[1:]),  time=time)
                else:
                    await PluginWithdraw.update_or_create(name=name, user_id=int(ban),  time=time)
        try:
            from .utils import cache_help
            cache_help.clear()
        except Exception:
            pass
        return {
            'status': 0,
            'msg':    '插件设置成功'
        }

    @app.post('/pmhelp/api/set_plugin_detail', response_class=JSONResponse, dependencies=[authentication()])
    async def set_plugin_detail(plugin_info: PluginInfo):
        """yml文件保存"""
        PluginManager.plugins[plugin_info.module_name] = plugin_info
        PluginManager.save()
        try:
            from .utils import cache_help
            cache_help.clear()
        except Exception:
            pass
        return {
            'status': 0,
            'msg':    '插件信息设置成功'
        }
    if mw_web:
        # 接入mw
        admin_page = PageSchema(url='/pmhelp', icon='fa fa-gears', label='PMHELP管理器',
                                schema=admin_app)
        admin.pages[0].children.append(admin_page)
    else:
        @app.get("/pmhelp", response_class=RedirectResponse)
        async def redirect_page():
            return RedirectResponse("/pmhelp/login")

        @app.get("/pmhelp/login", response_class=HTMLResponse)
        async def login_page_app():
            return login_page.render(
                cdn='https://npm.onmicrosoft.cn',
                site_title="登录 | PMHELP 后台管理",
                site_icon="https://img.picui.cn/free/2024/10/28/671f78556a9ee.png",
                theme="ang"
            )

        @app.get("/pmhelp/admin", response_class=HTMLResponse)
        async def admin_page_app():
            return admin_app.render(
                cdn="https://npm.onmicrosoft.cn",
                site_title="PMHELP 后台管理",
                site_icon="https://img.picui.cn/free/2024/10/28/671f78556a9ee.png",
                theme="ang",
                requestAdaptor=requestAdaptor,
                responseAdaptor=responseAdaptor,
            )
