from amis import (
    Radios, InputNumber, Alert, Card, Tpl,
    Cards, CRUD, Static, Page, Html,
    Remark, InputPassword, AmisAPI,
    Wrapper, Horizontal, Form, Transfer,
    DisplayModeEnum, InputText, Textarea, Switch,
    ActionType, Dialog, InputSubForm, LevelEnum, Action
)

# -------------css-------------------#
# 背景图
background_css = {
    "position": "absolute",
    "top": "0",
    "left": "0",
    "width": "100%",
    "height": "100%",
    "background": "url('https://www.loliapi.com/acg/') no-repeat center center",
    "background-size": "cover",
    "backdrop-filter": "blur(10px)",
    "-webkit-backdrop-filter": "blur(10px)",
}
# 圆角/透明
rounded_css_curd = {
    "background-color": "rgba(255, 255, 255, 0.9)",
    "border-radius": "2em",
    "width": "350px",
    "transform": "translateX(5%)"
}
rounded_css_9 = {
    "background-color": "rgba(255, 255, 255, 0.9)",
    "border-radius": "2em",
}
rounded_css_8 = {
    "background-color": "rgba(255, 255, 255, 0.8)",
    "border-radius": "2em",
}

# -------------登录-------------------#
login_logo = Html(
    html="""
<p align="center">
    <a href="https://github.com/CM-Edelweiss/nonebot-plugin-pmhelp/">
        <img src="https://img.picui.cn/free/2024/10/28/671f78556a9ee.png" width="256" height="256" alt="PMHELP">
    </a>
</p>
<h1 align="center">Nonebot-plugin-pmhelp 控制台</h1>
<div align="center">
    <a href="https://github.com/CM-Edelweiss/nonebot-plugin-pmhelp" target="_blank">
        Github仓库</a>
</div>
<br>
<br>
"""
)

login_api = AmisAPI(
    url="/pmhelp/api/login",
    method="post",
    adaptor="""
        if (payload.status == 0) {
            localStorage.setItem("token", payload.data.token);
        }
        return payload;
    """,
)

login_body = Wrapper(className="w-2/5 mx-auto my-0 m:w-full", body=Form(
    api=login_api,
    title="",
    body=[
        login_logo,
        InputText(
            name="username",
            label="用户名",
            labelRemark=Remark(
                shape="circle", content="后台管理用户名，默认为pmhelp"),
        ),
        InputPassword(
            name="password",
            label="密码",
            labelRemark=Remark(
                shape="circle", content="后台管理密码，默认为admin"),
        ),
    ],
    mode=DisplayModeEnum.horizontal,
    style=rounded_css_9,
    actions=[Action(label='登录', level=LevelEnum.primary, type='submit', style={
        "display": "table",
        "margin": "0 auto",
        "border-radius": "2em",
    })],
    horizontal=Horizontal(left=3, right=7, offset=5),
    redirect="/pmhelp/admin",
))

login_page = Page(title="", body=login_body, style=background_css)

# -------------禁用-------------------#
ban_form = Form(title='',
                api='post:/pmhelp/api/set_plugin_bans',
                initApi='get:/pmhelp/api/get_plugin_bans?module_name=${module_name}',
                body=[
                    Transfer(
                        type='tabs-transfer',
                        name='bans',
                        value='${bans}',
                        label='',
                        resultTitle='已被禁用列表',
                        selectMode='tree',
                        joinValues=False,
                        extractValue=True,
                        statistics=True,
                        multiple=True,
                        menuTpl='${left_label}',
                        valueTpl='${right_label}',
                        source='get:/pmhelp/api/get_groups_and_members',
                    )])

permission_button = ActionType.Dialog(label='使用',
                                      icon='fa fa-times-circle',
                                      dialog=Dialog(title='${name}使用权限设置', size='lg', body=ban_form))

# -------------撤回-------------------#
withdraw_form = Form(title='',
                     api='post:/pmhelp/api/set_withdraw_bans',
                     initApi='get:/pmhelp/api/get_withdraw_bans?module_name=${module_name}',
                     body=[
                         Transfer(
                             type='tabs-transfer',
                             name='bans',
                             value='${bans}',
                             label='',
                             resultTitle='撤回管理列表',
                             selectMode='tree',
                             joinValues=False,
                             extractValue=True,
                             statistics=True,
                             multiple=True,
                             menuTpl='${left_label}',
                             valueTpl='${right_label}',
                             source='get:/pmhelp/api/get_groups_and_members',
                         ),
                         Switch(
                             label='是否为全局撤回',
                             value='${show}',
                             name='all',
                         ),
                         InputNumber(label='延迟撤回时间',
                                     description='单位为秒。清除用户时不生效（无法精确化时间）',
                                     name='time',
                                     value=10,
                                     min=1,
                                     clearValueOnEmpty=True,
                                     required=True,
                                     )
                     ])


withdraw_button = ActionType.Dialog(label='撤回',
                                    icon='fa fa-hourglass',
                                    dialog=Dialog(title='${name}撤回管理设置', size='lg', body=withdraw_form))

# -------------限流-------------------#
xl_form = Form(title='',
               api='post:/pmhelp/api/set_message_bans',
               initApi='get:/pmhelp/api/get_message_bans?module_name=${module_name}',
               body=[
                   Transfer(
                       type='tabs-transfer',
                       name='bans',
                       value='${bans}',
                       label='',
                       resultTitle='限流管理列表',
                       selectMode='tree',
                       joinValues=False,
                       extractValue=True,
                       statistics=True,
                       multiple=True,
                       menuTpl='${left_label}',
                       valueTpl='${right_label}',
                       source='get:/pmhelp/api/get_groups_and_members',
                   ),
                   Switch(
                       label='是否为全局限流',
                       value='${show}',
                       name='all',
                   ),
                   Radios(
                       label='限流类型',
                       name='type',
                       options=[
                            {
                                "label": "倒计时类",
                                "value": "time"
                            },
                           {
                                "label": "每分钟类",
                                "value": "frequency"
                            }
                       ],
                       selectFirst=True,
                   ),
                   InputNumber(label='限流值',
                               description='倒计时类：单位为秒，每分钟类：单位为次。清除用户时不生效（无法精确化时间）',
                               name='time',
                               value=10,
                               min=1,
                               clearValueOnEmpty=True,
                               required=True,
                               )
               ])

xl_button = ActionType.Dialog(label='限流',
                              icon='fa fa-spinner',
                              dialog=Dialog(title='${name}限流管理设置', size='lg', body=xl_form))

# -------------信息-------------------#
command_form = InputSubForm(name='matchers',
                            label='命令列表',
                            multiple=True,
                            btnLabel='${pm_name}',
                            value='${matchers}',
                            description='该插件下具体的命令使用方法设置',
                            addButtonText='添加命令',
                            form=Form(
                                title='命令信息设置',
                                mode=DisplayModeEnum.horizontal,
                                labelAlign='right',
                                body=[
                                    InputText(label='命令标识名称', name='pm_name', value='${pm_name}', required=True,
                                              description='仅用于标识命令，不会显示在帮助图中，所以若是本身已有的命令，请勿修改！'),
                                    InputText(label='命令用法', name='pm_usage', value='${pm_usage}',
                                              description='命令的使用方法，建议不要太长'),
                                    Textarea(label='命令详细描述', name='pm_description', value='${pm_description}',
                                             description='命令的详细描述，可以用^强制换行', showCounter=False),
                                    Switch(label='是否展示', name='pm_show', value='${pm_show}',
                                           description='是否在帮助图中展示该命令'),
                                    InputNumber(label='展示优先级', name='pm_priority', value='${pm_priority}',
                                                description='在帮助图中展示的优先级，数字越小越靠前', min=0, max=99,
                                                displayMode='enhance'),
                                ]
                            ))
detail_form = Form(title='',
                   api='post:/pmhelp/api/set_plugin_detail',
                   submitText='保存修改',
                   mode=DisplayModeEnum.horizontal,
                   labelAlign='right',
                   body=[
                       InputText(label='插件名称', name='name', value='${name}', required=True,
                                 description='插件显示的名称，建议不要过长'),
                       Static(label='插件模块名', name='module_name',
                              value='${module_name}'),
                       Textarea(label='插件描述', name='description', value='${description}', clearable=True,
                                description='仅用于在本管理页面中显示，不会在帮助图中显示', showCounter=False),
                       Textarea(label='插件使用说明', name='usage', value='${usage}', clearable=True,
                                description='会在该插件没有具体命令的使用说明时，显示在帮助图中', showCounter=False),
                       Switch(label='是否展示', name='show', value='${show}',
                              description='是否在帮助图中展示该插件'),
                       InputNumber(label='展示优先级', name='priority', value='${priority}',
                                   description='在帮助图及本管理页面中展示的顺序，数字越小越靠前',
                                   min=0, max=99, displayMode='enhance'),
                       command_form
                   ])
tips_alert = Alert(level='info',
                   body='以下设置用于在本管理页面以及help帮助图中显示插件的信息，不会影响插件的实际使用，你可以修改这些信息来自定义帮助图效果。')

detail_button = ActionType.Dialog(label='信息',
                                  size='lg',
                                  icon='fa fa-pencil',
                                  dialog=Dialog(title='${name}信息设置', size='lg', body=[tips_alert, detail_form]))

# -------------卡片-------------------#
card = Card(
    header=Card.Header(title='$name',
                       subTitle='$module_name',
                       description='$description',
                       avatarText='$name',
                       avatarTextClassName='overflow-hidden'),
    actions=[detail_button, permission_button, xl_button, withdraw_button],
    style=rounded_css_curd,
    className='m-l',
    toolbar=[
        Tpl(tpl='未加载', className='label label-warning', hiddenOn='${isLoad}'),
        Switch(name='enable',
               value='${status}',
               onText='启用',
               offText='禁用',
               visibleOn='${isLoad}',
               onEvent={
                   'change': {
                       'actions': [{
                           'actionType': 'ajax',
                           'api':      {
                                   'url':    '/pmhelp/api/set_plugin_status',
                                   'method': 'post',
                                   'data': {
                                       'status':   '${event.data.value}',
                                       'plugin':   '${module_name}'
                                   },
                                   'messages': {
                                       'success': '插件设置成功',
                                       'failed':  '插件设置失败'
                                   }
                                   }
                       }]
                   }
               })
    ])


class CardsCRUD(CRUD, Cards):
    """卡片CRUD"""


cards_curd = CardsCRUD(mode='cards',
                       title='',
                       syncLocation=False,
                       api='/pmhelp/api/get_plugins',
                       loadDataOnce=True,
                       source='${rows | filter:name:match:keywords_name | filter:description:match:keywords_description}',
                       filter={
                           'body': [
                               InputText(name='keywords_name', label='插件名'),
                               InputText(name='keywords_description',
                                         label='插件描述'),
                               Action(
                                   label='搜索', level=LevelEnum.primary, type='submit')
                           ],
                           "style": rounded_css_9,
                           "mode": DisplayModeEnum.inline
                       },
                       style=rounded_css_8,
                       perPage=12,
                       autoJumpToTopOnPagerChange=True,
                       placeholder='暂无插件信息',
                       headerToolbar=[
                           'switch-per-page',
                           'pagination',
                           ActionType.Ajax(
                               label='刷新用户列表',
                               api='/pmhelp/api/get_groups_flushed',
                               confirmText='该操作将会重新刷新群和好友列表',
                               level=LevelEnum.info,
                           )],
                       footerToolbar=[],
                       card=card)

admin_app = Page(title="PMHELP插件管理器", body=cards_curd, style=background_css)
