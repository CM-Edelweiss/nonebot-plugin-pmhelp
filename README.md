<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://img.picui.cn/free/2024/10/28/671f78556a9ee.png" width="180" height="180" alt="NoneBotPluginLogo"></a>

</div>

<div align="center">

# nonebot-plugin-pmhelp


</div>
<h4 align="center">✨提取于<a href="https://github.com/CMHopeSunshine/LittlePaimon" target="_blank">LittlePaimon</a>的插件管理器✨</h4>


## 📖 介绍

提供帮助图自动生成和插件权限管理<br>
功能：全自动生成帮助图和插件禁用,限流控制<br>
虽然LittlePaimon不再维护了，但是 [@CMHopeSunshine](https://github.com/CMHopeSunshine) 的帮助插件真好用，所以把LittlePaimon帮助插件独立出来<br>
（~~因为直接照搬，有问题请pr~~）

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-pmhelp

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-pmhelp
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-pmhelp
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-pmhelp
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-pmhelp
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_pmhelp"]

</details>

## 📋 效果

帮助图(举例) <br>
![_](https://img.picui.cn/free/2024/10/28/671f9c5ad8c30.jpg)<br>
被禁用对应变黑<br>
![_](https://img.picui.cn/free/2024/10/28/671f9c5af1fc1.jpg)<br>
webui(举例)<br>
![_](https://img.picui.cn/free/2024/10/28/671f9c5ae1e92.png)<br>


## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| img_cache | 否 | True | 图片资源缓存开关 |
| pm_version | 否 | 11.45.14 | 帮助显示的版本号 |
| pm_text| 否 | 自定义文本| 自定义文本 |
| m_message| 否 | True | 被限流是否提醒 |
| pm_plugin| 否 | 1 | 管理插件文件的位置(1为统一目录，2为机器人目录，3为自定义目录) |
| pm_path| 否 | 无 | pm_plugin为3时的目录(无需引号) |
| pm_enable_web| 否 | True |后台管理开关 |
| pm_username| 否 | pmhelp |后台管理用户名 |
| pm_password| 否 | admin | 后台管理密码 |
| pm_secret_key| 否 | ... | 后台管理token密钥 |



nonebot2插件生成帮助图位于{帮助文件目录}/pm_config下<br>
或者使用webui进行修改<br>
```
webui默认地址ip:端口/pmhelp/login
```

```python
举例(xxx.yml):
description: 根据加载的nonebot2...   #插件介绍
matchers:                           #帮助图展示的指令卡片(可能需要自行配置)
- {pm_description: 禁用|取消...,     #介绍
    pm_name: pm-ban|unban,          #此帮助名
    pm_priority: 1,                 #优先级
    pm_show: true,                  #是否展示
    pm_usage: pm ban|unba...,       #触发命令
  }
-{....}
module_name: nonebot_plugin_pmhelp  #插件包名
name: PM帮助                         #插件名字
priority: 1                          #优先级
show: true                           #是否展示在帮助图中
usage: help                          #默认读取插件命令
```


```python
编写命令时实例
xxx = on_command(
    ....,
    state={
        "pm_name": #此帮助名,
        "pm_description": #介绍,
        "pm_usage": #触发命令,
        "pm_priority": #优先级,
    },
)
```



## 🎉 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| help | 所有 | 否 | 全部 | 打开所有帮助 |
| pm ban/unban <插件名> | 管理 | 否 | 全部 | 禁用/取消禁用插件的群/用户使用权限或者限流 |

```python
命令：pm ban|unban <插件名> -g <群号> -u <用户号> -x t|f <时间/次数>
参数：
    ban|unban：禁用/启用使用或者禁用/启用限流
<插件名>：可以是中/英文或者all，all表示所有插件，多个插件用空格分隔
<群号>：
    默认值：不填时为命令当前群， 可以是群号或者all，all表示所有群，多个群号用空格分隔
    权限：群主和群管只能管理本群，超级用户可以管理所有群
<用户号>：
    默认值：不填时或者填all则为本群所有用户，all私聊使用为所有好友，多个用户用空格分隔
    权限：群主和群管可以管理本群的用户，超级用户可以管理所有用户
-x 限流:
    <时间/次数>默认值： 10s
    t:多少秒后可以再次使用
    f:一分钟使用次数
额外说明：
    如果要全局禁用/启用某一个用户，需要超级用户私聊Bot来使用命令
```

## 丨💸鸣谢
- 来自[LittlePaimon](https://github.com/CMHopeSunshine/LittlePaimon)帮助插件代码