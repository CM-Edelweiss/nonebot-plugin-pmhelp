<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-pmhelp

_✨ NoneBot 插件简单描述 ✨_


</div>
<h4 align="center">✨提取于<a href="https://github.com/CMHopeSunshine/LittlePaimon" target="_blank">LittlePaimon</a>的帮助插件✨</h4>




## 📖 介绍

LittlePaimon帮助插件真好用，为什么不独立出来呢（？

（~~因为直接照搬，有问题请多多指出~~）

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

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| img_cache | 否 | True | 图片资源缓存开关 |
| github_proxy | 否 | https://gitdl.cn/ | 资源下载代理 |
| __version__ | 否 | 11.45.14 | 版本号 |

## 🎉 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| help | 所有 | 否 | 全部 | 打开所有帮助 |

## 丨💸鸣谢
- 来自[LittlePaimon](https://github.com/CMHopeSunshine/LittlePaimon)帮助插件代码