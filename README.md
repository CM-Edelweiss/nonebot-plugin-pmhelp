<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/CM-Edelweiss/nonebot-plugin-pmhelp/blob/main/docs_image/nb_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>

</div>

<div align="center">

# nonebot-plugin-pmhelp


</div>
<h4 align="center">✨提取于<a href="https://github.com/CMHopeSunshine/LittlePaimon" target="_blank">LittlePaimon</a>的帮助插件✨</h4>


## 📖 介绍
虽然LittlePaimon不再维护了，但是 [@CMHopeSunshine](https://github.com/CMHopeSunshine) 的帮助插件真好用，所以把LittlePaimon帮助插件独立出来（~~因为直接照搬，有问题请pr~~）

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
![_](https://github.com/CM-Edelweiss/nonebot-plugin-pmhelp/blob/main/docs_image/1.jpg)<br>
被禁用对应变黑(全部禁用)<br>
![_](https://github.com/CM-Edelweiss/nonebot-plugin-pmhelp/blob/main/docs_image/2.jpg)<br>



## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| img_cache | 否 | True | 图片资源缓存开关(无需引号) |
| pm_version | 否 | "11.45.14" | 帮助显示的版本号 |
| pm_text| 否 | "自定义文本" | 自定义文本 |
| pm_plugin| 否 | "1" | 管理插件文件的位置(1为统一目录，2为机器人目录，3为自定义目录) |
| pm_path| 否 | 无 | pm_plugin为3时的目录(无需引号) |

nonebot2插件生成帮助图位于{帮助文件目录}/pm_config下

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
| pm ban|unban <插件名> | 管理 | 否 | 全部 | 禁用/取消禁用插件的群/用户使用权限 |



## 丨💸鸣谢
- 来自[LittlePaimon](https://github.com/CMHopeSunshine/LittlePaimon)帮助插件代码