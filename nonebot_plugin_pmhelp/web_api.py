import datetime
import asyncio
from typing import Optional

from fastapi import FastAPI
from fastapi import Header, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from jose import jwt
from nonebot.adapters.onebot.v11 import Adapter
from nonebot import get_app, get_adapter
from pydantic import BaseModel


from .plugin.manage import PluginManager, PluginInfo
from .models import PluginDisable
from .utils import DRIVER
from .pm_config import Pm_config
from .web_page import login_page, admin_app
from .logger import logger

requestAdaptor = """
requestAdaptor(api) {
    api.headers["token"] = localStorage.getItem("token");
    return api;
},
"""
responseAdaptor = """
responseAdaptor(api, payload, query, request, response) {
    if (response.data.detail == '登录验证失败或已失效，请重新登录') {
        window.location.href = '/pmhelp/login'
        window.localStorage.clear()
        window.sessionStorage.clear()
        window.alert('登录验证失败或已失效，请重新登录')
    }
    return payload
},
"""


def authentication():
    def inner(token: Optional[str] = Header(...)):
        try:
            payload = jwt.decode(
                token, Pm_config.pm_secret_key, algorithms="HS256"
            )
            if (
                not (username := payload.get("username"))
                or username != Pm_config.pm_username
            ):
                raise HTTPException(status_code=400, detail="登录验证失败或已失效，请重新登录")
        except (jwt.JWTError, jwt.ExpiredSignatureError, AttributeError):
            raise HTTPException(status_code=400, detail="登录验证失败或已失效，请重新登录")

    return Depends(inner)


class UserModel(BaseModel):
    username: str
    password: str


@DRIVER.on_startup
async def init_web():
    if not Pm_config.pm_enable_web:
        return
    try:
        app: FastAPI = get_app()
        logger.info(
            "PM Web UI",
            f"<g>启用成功</g>，默认地址为<m>http://127.0.0.1:{DRIVER.config.port}/pmhelp/login</m>",
        )
    except Exception as e:
        return logger.info('PM Web UI', f'启用<r>失败：{e}</r>')

    @app.post("/pmhelp/api/login", response_class=JSONResponse)
    async def login(user: UserModel):
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
            await asyncio.sleep(0.2)
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
        return result

    @app.get('/pmhelp/api/get_plugins', response_class=JSONResponse, dependencies=[authentication()])
    async def get_plugins():
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

    @app.post('/pmhelp/api/set_plugin_detail', response_class=JSONResponse, dependencies=[authentication()])
    async def set_plugin_detail(plugin_info: PluginInfo):
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

    @app.get("/pmhelp", response_class=RedirectResponse)
    async def redirect_page():
        return RedirectResponse("/pmhelp/login")

    @app.get("/pmhelp/login", response_class=HTMLResponse)
    async def login_page_app():
        return login_page.render(site_title="登录 | PMHELP 后台管理", theme="ang")

    @app.get("/pmhelp/admin", response_class=HTMLResponse)
    async def admin_page_app():
        return admin_app.render(
            site_title="PMHELP 后台管理",
            theme="ang",
            requestAdaptor=requestAdaptor,
            responseAdaptor=responseAdaptor,
        )
