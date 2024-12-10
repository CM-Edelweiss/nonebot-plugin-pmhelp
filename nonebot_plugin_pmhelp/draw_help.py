import math
from .image import (
    PMImage,
    load_image,
    MessageBuild_Image,
    font_manager as fm,
)
from typing import List
from .Path import IMAGE_PATH
from .pm_config import Pm_config
from .plugin.manage import PluginInfo


async def draw_help(plugin_list: List[PluginInfo]):
    """
    生成帮助图片

    参数:
        plugin_list (List[PluginInfo]): 插件信息列表

    返回:
        MessageBuild_Image: 生成的帮助图片
    """
    # 加载背景图片
    bg = PMImage(await load_image(IMAGE_PATH / 'bg.png'))
    # 创建一个新的图片，用于绘制帮助信息
    img = PMImage(size=(1080, 1000 + 600 * len(plugin_list)),
                  color=(255, 255, 255, 0), mode='RGBA')
    # 加载各种颜色的线条和卡片背景图片
    orange_line = await load_image(IMAGE_PATH / 'orange.png')
    orange_name_bg = await load_image(IMAGE_PATH / 'orange_card.png')
    orange_bord = await load_image(IMAGE_PATH / 'orange_bord.png')

    black_line = await load_image(IMAGE_PATH / 'black.png')
    black_name_bg = await load_image(IMAGE_PATH / 'black_card.png')
    black_bord = await load_image(IMAGE_PATH / 'black_bord.png')

    blue_line = await load_image(IMAGE_PATH / 'blue.png')
    blue_name_bg = await load_image(IMAGE_PATH / 'blue_card.png')
    blue_bord = await load_image(IMAGE_PATH / 'blue_bord.png')

    green_line = await load_image(IMAGE_PATH / 'green.png')
    green_name_bg = await load_image(IMAGE_PATH / 'green_card.png')
    green_bord = await load_image(IMAGE_PATH / 'green_bord.png')

    # 在图片上添加文字信息
    await img.text(Pm_config.pm_name, 38, 40, fm.get('SourceHanSerifCN-Bold.otf', 72), 'black')
    await img.text(f'V{Pm_config.pm_version}', 1040, 75, fm.get('bahnschrift_regular', 36), 'black', 'right')
    await img.text('灰色为禁用，蓝色为限流，绿色使用后撤回', 1040, 105, fm.get('SourceHanSerifCN-Bold.otf', 22), 'black', 'right')
    await img.text(Pm_config.pm_text, 1040, 130, fm.get('SourceHanSerifCN-Bold.otf', 22), 'black', 'right')

    # 初始化当前绘制高度
    height_now = 172
    # 遍历插件列表
    for plugin in plugin_list:
        # 根据插件状态选择不同的线条、名称背景和卡片样式
        match plugin.status:
            case "black":
                plugin_line = PMImage(black_line)
                plugin_name_bg = PMImage(black_name_bg)
                matcher_card = PMImage(black_bord)
            case "blue":
                plugin_line = PMImage(blue_line)
                plugin_name_bg = PMImage(blue_name_bg)
                matcher_card = PMImage(blue_bord)
            case "green":
                plugin_line = PMImage(green_line)
                plugin_name_bg = PMImage(green_name_bg)
                matcher_card = PMImage(green_bord)
            case _:
                plugin_line = PMImage(orange_line)
                plugin_name_bg = PMImage(orange_name_bg)
                matcher_card = PMImage(orange_bord)

        # 获取插件名称，并计算其文本长度
        plugin_name = plugin.name.replace('\n', '')
        name_length = img.text_length(
            plugin_name, fm.get('SourceHanSerifCN-Bold.otf', 30))
        # 在图片上绘制线条和名称背景
        await img.paste(plugin_line, (40, height_now))
        await plugin_name_bg.stretch((23, plugin_name_bg.width - 36), int(name_length), 'width')
        await img.paste(plugin_name_bg, (40, height_now))
        # 在名称背景上绘制插件名称
        await img.text(plugin_name, 63, height_now + 5, fm.get('SourceHanSerifCN-Bold.otf', 30), 'white')
        # 更新当前绘制高度
        height_now += plugin_line.height + 11
        # 如果启用了分片模式，则只需要绘制插件名称
        if Pm_config.sharding_mode and not plugin.sharding:
            pass
        # 如果插件有匹配器，并且这些匹配器需要显示在帮助图片中
        elif plugin.matchers and (matchers := [matcher for matcher in plugin.matchers if matcher.pm_show and matcher.pm_sharding and (matcher.pm_usage or matcher.pm_name)]):
            # 将匹配器分组，每组最多3个
            matcher_groups = [matchers[i:i + 3]
                              for i in range(0, len(matchers), 3)]
            # 遍历每个匹配器组
            for matcher_group in matcher_groups:
                # 计算每个匹配器组中描述文本的最大长度
                max_length = max(len(matcher.pm_description.replace(
                    '\n', '')) if matcher.pm_description else 0 for matcher in matcher_group)
                # 计算最大高度，用于拉伸卡片背景
                max_height = math.ceil(max_length / 16) * 22 + 40
                # 拉伸卡片背景
                await matcher_card.stretch((5, matcher_card.height - 5), max_height, 'height')
                # 遍历每个匹配器
                for matcher in matcher_group:
                    # 在图片上绘制卡片背景
                    await img.paste(matcher_card, (40 + 336 * matcher_group.index(matcher), height_now))
                    # 在卡片背景上绘制匹配器的使用方法或名称
                    await img.text(matcher.pm_usage or matcher.pm_name, 40 + 336 * matcher_group.index(matcher) + 15, height_now + 10, fm.get('SourceHanSansCN-Bold.otf', 24), 'black')
                    # 如果匹配器有描述文本
                    if matcher.pm_description:
                        # 在卡片背景上绘制描述文本
                        await img.text_box(matcher.pm_description.replace('\n', '^'), (40 + 336 * matcher_group.index(matcher) + 10, 40 + 336 * matcher_group.index(matcher) + matcher_card.width - 22),
                                           (height_now + 44, height_now + max_height - 10), fm.get('SourceHanSansCN-Bold.otf', 18), '#40342d')
                # 更新当前绘制高度
                height_now += max_height + 10 + 6
        # 如果插件有使用方法
        elif plugin.usage:
            # 计算使用方法文本的高度
            text_height = len(plugin.usage) // 43 * 22 + 45
            # 拉伸卡片背景
            await matcher_card.stretch((5, matcher_card.width - 5), 990, 'width')
            await matcher_card.stretch((5, matcher_card.height - 5), text_height, 'height')
            # 在图片上绘制卡片背景
            await img.paste(matcher_card, (40, height_now))
            # 在卡片背景上绘制使用方法文本
            await img.text_box(plugin.usage.replace('\n', '^'), (50, 1030), (height_now + 10, height_now + text_height - 10), fm.get('SourceHanSansCN-Bold.otf', 18), '#40342d')
            # 更新当前绘制高度
            height_now += matcher_card.height + 6
        # 增加额外的高度间隔
        height_now += 19
    # 在图片底部添加版权信息
    await img.text('CREATED BY NoneBot2 / CM-Edelweiss / CMHopeSunshine', (0, 1080), height_now + 8, fm.get('SourceHanSerifCN-Bold.otf', 24), 'black', 'center')
    # 更新当前绘制高度
    height_now += 70
    # 拉伸背景图片
    await bg.stretch((50, bg.height - 50), height_now - 100, 'height')
    # 将绘制好的图片粘贴到背景图片上
    await bg.paste(img, (0, 0))

    # 返回最终的帮助图片
    return await MessageBuild_Image(bg, quality=80, mode='RGB')
