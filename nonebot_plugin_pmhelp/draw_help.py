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


async def draw_plugin_card(plugin: PluginInfo):
    matchers = plugin.matchers
    matcher_groups = [matchers[i:i + 3] for i in range(0, len(matchers), 3)]
    # 确定长度
    total_height = 66
    for matcher_group in matcher_groups:
        max_length = max(len(matcher.pm_description)
                         for matcher in matcher_group)
        max_height = max_length // 13 * 22 + 59 + 15
        total_height += max_height + 6
    total_height -= 6
    img = PMImage(size=(1080, total_height),
                  color=(255, 255, 255, 0), mode='RGBA')
    await img.paste


async def draw_help(plugin_list: List[PluginInfo]):
    bg = PMImage(await load_image(IMAGE_PATH / 'bg.png'))
    img = PMImage(size=(1080, 1000 + 600 * len(plugin_list)),
                  color=(255, 255, 255, 0), mode='RGBA')
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

    await img.text(Pm_config.pm_name, 38, 40, fm.get('SourceHanSerifCN-Bold.otf', 72), 'black')
    await img.text(f'V{Pm_config.pm_version}', 1040, 75, fm.get('bahnschrift_regular', 36), 'black', 'right')
    await img.text('灰色为禁用，蓝色为限流，绿色使用后撤回', 1040, 105, fm.get('SourceHanSerifCN-Bold.otf', 22), 'black', 'right')
    await img.text(Pm_config.pm_text, 1040, 130, fm.get('SourceHanSerifCN-Bold.otf', 22), 'black', 'right')

    height_now = 172
    for plugin in plugin_list:
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

        plugin_name = plugin.name.replace('\n', '')
        name_length = img.text_length(
            plugin_name, fm.get('SourceHanSerifCN-Bold.otf', 30))
        await img.paste(plugin_line, (40, height_now))
        await plugin_name_bg.stretch((23, plugin_name_bg.width - 36), int(name_length), 'width')
        await img.paste(plugin_name_bg, (40, height_now))
        await img.text(plugin_name, 63, height_now + 5, fm.get('SourceHanSerifCN-Bold.otf', 30), 'white')
        height_now += plugin_line.height + 11
        if plugin.matchers and (matchers := [matcher for matcher in plugin.matchers if matcher.pm_show and (matcher.pm_usage or matcher.pm_name)]):
            matcher_groups = [matchers[i:i + 3]
                              for i in range(0, len(matchers), 3)]
            for matcher_group in matcher_groups:
                max_length = max(len(matcher.pm_description.replace(
                    '\n', '')) if matcher.pm_description else 0 for matcher in matcher_group)
                max_height = math.ceil(max_length / 16) * 22 + 40
                await matcher_card.stretch((5, matcher_card.height - 5), max_height, 'height')
                for matcher in matcher_group:
                    await img.paste(matcher_card, (40 + 336 * matcher_group.index(matcher), height_now))
                    await img.text(matcher.pm_usage or matcher.pm_name, 40 + 336 * matcher_group.index(matcher) + 15, height_now + 10, fm.get('SourceHanSansCN-Bold.otf', 24), 'black')
                    if matcher.pm_description:
                        await img.text_box(matcher.pm_description.replace('\n', '^'), (40 + 336 * matcher_group.index(matcher) + 10, 40 + 336 * matcher_group.index(matcher) + matcher_card.width - 22),
                                           (height_now + 44, height_now + max_height - 10), fm.get('SourceHanSansCN-Bold.otf', 18), '#40342d')
                height_now += max_height + 10 + 6
        elif plugin.usage:
            text_height = len(plugin.usage) // 43 * 22 + 45
            await matcher_card.stretch((5, matcher_card.width - 5), 990, 'width')
            await matcher_card.stretch((5, matcher_card.height - 5), text_height, 'height')
            await img.paste(matcher_card, (40, height_now))
            await img.text_box(plugin.usage.replace('\n', '^'), (50, 1030), (height_now + 10, height_now + text_height - 10), fm.get('SourceHanSansCN-Bold.otf', 18), '#40342d')
            height_now += matcher_card.height + 6
        height_now += 19
    await img.text('CREATED BY NoneBot2 / CM-Edelweiss / CMHopeSunshine', (0, 1080), height_now + 8, fm.get('SourceHanSerifCN-Bold.otf', 24), 'black', 'center')
    height_now += 70
    await bg.stretch((50, bg.height - 50), height_now - 100, 'height')
    await bg.paste(img, (0, 0))

    return MessageBuild_Image(bg, quality=80, mode='RGB')
