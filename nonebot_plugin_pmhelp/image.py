from typing import (
    Tuple,
    Union,
    Literal,
    Optional,
    Dict,
    Any,
)
from io import BytesIO
from pathlib import Path
from .Path import FONTS_PATH
from .pm_config import Pm_config
from nonebot.utils import run_sync
from PIL.ImageFont import FreeTypeFont
from PIL import Image, ImageDraw, ImageFont
from nonebot.adapters.onebot.v11 import MessageSegment


class PMImage:

    def __init__(self,
                 image: Union[Image.Image, Path, None] = None,
                 *,
                 size: Tuple[int, int] = (200, 200),
                 color: Union[str, Tuple[int, int, int, int],
                              Tuple[int, int, int]] = (255, 255, 255, 255),
                 mode: Literal["1", "CMYK", "F", "HSV", "I", "L",
                               "LAB", "P", "RGB", "RGBA", "RGBX", "YCbCr"] = 'RGBA'
                 ):
        """
        初始化图像，优先读取image参数，如无则新建图像

        :param image: PIL对象或图像路径
        :param size: 图像大小
        :param color: 图像颜色
        :param mode: 图像模式
        """
        if image:
            self.image = Image.open(image) if isinstance(
                image, Path) else image.copy()
        else:
            if mode == 'RGB' and isinstance(color, tuple):
                color = (color[0], color[1], color[2])
            self.image = Image.new(mode, size, color)
        self.draw = ImageDraw.Draw(self.image)

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    @property
    def size(self) -> Tuple[int, int]:
        return self.image.size

    @property
    def mode(self) -> str:
        return self.image.mode

    def show(self) -> None:
        self.image.show()

    def convert(self, mode: str):
        return self.image.convert(mode)

    def save(self, path: Union[str, Path], **kwargs):
        """
        保存图像

        :param path: 保存路径
        """
        self.image.save(path, **kwargs)

    def save_to_io(self, **kwargs) -> BytesIO:
        """
        将图像保存到BytesIO中
        """
        bio = BytesIO()
        self.image.save(bio, **kwargs)
        return bio

    def text_length(self, text: str, font: ImageFont.ImageFont) -> int:
        return int(self.draw.textlength(text, font))

    def text_size(self, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
        return self.draw.textsize(text, font)

    @run_sync
    def paste(self,
              image: Union[Image.Image, 'PMImage'],
              pos: Tuple[int, int],
              alpha: bool = True,
              ):
        """
        粘贴图像
            :param image: 图像
            :param pos: 位置
            :param alpha: 是否透明
        """
        if image is None:
            return
        if isinstance(image, PMImage):
            image = image.image
        if alpha:
            image = image.convert('RGBA')
            if self.image.mode != 'RGBA':
                self.image = self.convert('RGBA')
            self.image.alpha_composite(image, pos)
        else:
            self.image.paste(image, pos)
        self.draw = ImageDraw.Draw(self.image)

    @run_sync
    def text(self,
             text: str,
             width: Union[float, Tuple[float, float]],
             height: Union[float, Tuple[float, float]],
             font: ImageFont.ImageFont,
             color: Union[str, Tuple[int, int, int, int]] = 'white',
             align: Literal['left', 'center', 'right'] = 'left'
             ):
        """
        写文本
            :param text: 文本
            :param width: 位置横坐标
            :param height: 位置纵坐标
            :param font: 字体
            :param color: 颜色
            :param align: 对齐类型
        """
        if align == 'left':
            if isinstance(width, tuple):
                width = width[0]
            if isinstance(height, tuple):
                height = height[0]
            self.draw.text((width, height), text, color, font)
        elif align in ['center', 'right']:
            _, _, w, h = self.draw.textbbox((0, 0), text, font)
            if align == 'center':
                w = width[0] + (width[1] - width[0] - w) / \
                    2 if isinstance(width, tuple) else width
                h = height[0] + (height[1] - height[0] - h) / \
                    2 if isinstance(height, tuple) else height
            else:
                if isinstance(width, tuple):
                    width = width[1]
                w = width - w
                h = height[0] if isinstance(height, tuple) else height
            self.draw.text((w, h),
                           text,
                           color,
                           font)
        else:
            raise ValueError('对齐类型必须为\'left\', \'center\'或\'right\'')

    @run_sync
    def text_box(self,
                 text: str,
                 width: Tuple[int, int],
                 height: Tuple[int, int],
                 font: ImageFont.ImageFont,
                 color: Union[str, Tuple[int, int, int, int]] = 'white'):
        text_height = self.draw.textbbox((0, 0), text=text, font=font)[
            3] - self.draw.textbbox((0, 0), text=text, font=font)[1]
        width_now = width[0]
        height_now = height[0]
        for c in text:
            if c in ['.', '。'] and width_now == width[0] and c == text[-1]:
                continue
            if c == '^':
                width_now = width[0]
                height_now += text_height
                continue
            c_length = self.draw.textlength(c, font=font)
            if width_now == width[0] and height_now >= height[1]:
                break
            self.draw.text((width_now, height_now), c, color, font=font)
            if width_now + c_length > width[1]:
                width_now = width[0]
                height_now += text_height
            else:
                width_now += c_length

    @run_sync
    def stretch(self,
                pos: Tuple[int, int],
                length: int,
                type: Literal['width', 'height'] = 'height'):
        """
        将某一部分进行拉伸
            :param pos: 拉伸的部分
            :param length: 拉伸的目标长/宽度
            :param type: 拉伸方向，width:横向, height: 竖向
        """
        if pos[0] <= 0:
            raise ValueError('起始轴必须大于等于0')
        if pos[1] <= pos[0]:
            raise ValueError('结束轴必须大于起始轴')
        if type == 'height':
            if pos[1] >= self.height:
                raise ValueError('终止轴必须小于图片高度')
            top = self.image.crop((0, 0, self.width, pos[0]))
            bottom = self.image.crop((0, pos[1], self.width, self.height))
            if length == 0:
                self.image = Image.new(
                    'RGBA', (self.width, top.height + bottom.height))
                self.image.paste(top, (0, 0))
                self.image.paste(bottom, (0, top.height))
            else:
                center = self.image.crop((0, pos[0], self.width, pos[1])).resize((self.width, length),
                                                                                 Image.Resampling.LANCZOS)
                self.image = Image.new(
                    'RGBA', (self.width, top.height + center.height + bottom.height))
                self.image.paste(top, (0, 0))
                self.image.paste(center, (0, top.height))
                self.image.paste(bottom, (0, top.height + center.height))
            self.draw = ImageDraw.Draw(self.image)
        elif type == 'width':
            if pos[1] >= self.width:
                raise ValueError('终止轴必须小于图片宽度')
            top = self.image.crop((0, 0, pos[0], self.height))
            bottom = self.image.crop((pos[1], 0, self.width, self.height))
            if length == 0:
                self.image = Image.new(
                    'RGBA', (top.width + bottom.width, self.height))
                self.image.paste(top, (0, 0))
                self.image.paste(bottom, (top.width, 0))
            else:
                center = self.image.crop((pos[0], 0, pos[1], self.height)).resize((length, self.height),
                                                                                  Image.Resampling.LANCZOS)
                self.image = Image.new(
                    'RGBA', (top.width + center.width + bottom.width, self.height))
                self.image.paste(top, (0, 0))
                self.image.paste(center, (top.width, 0))
                self.image.paste(bottom, (top.width + center.width, 0))
            self.draw = ImageDraw.Draw(self.image)
        else:
            raise ValueError('类型必须为\'width\'或\'height\'')


class FontManager:
    """
    字体管理器，获取字体路径中的所有字体
    """

    def __init__(self):
        self.font_path = FONTS_PATH
        fonts = [font_name.stem + font_name.suffix for font_name in FONTS_PATH.iterdir()
                 if font_name.is_file()]
        self.fonts = fonts
        self.fonts_cache = {}

    def get(self, font_name: str = 'hywh.ttf', size: int = 25, variation: Optional[str] = None) -> FreeTypeFont:
        """
        获取字体，如果已在缓存中，则直接返回

        :param font_name: 字体名称
        :param size: 字体大小
        :param variation: 字体变体
        """
        if 'ttf' not in font_name and 'ttc' not in font_name and 'otf' not in font_name:
            font_name += '.ttf'
        if font_name not in self.fonts:
            font_name = font_name.replace('.ttf', '.ttc')
        if font_name not in self.fonts:
            raise FileNotFoundError(
                f'不存在字体文件 {font_name} ，请补充至字体资源中,资源第一次下载请重启应用')
        if f'{font_name}-{size}' in self.fonts_cache:
            font = self.fonts_cache[f'{font_name}-{size}']
        else:
            font = ImageFont.truetype(str(self.font_path / font_name), size)
        self.fonts_cache[f'{font_name}-{size}'] = font
        if variation:
            font.set_variation_by_name(variation)
        return font


font_manager = FontManager()

cache_image: Dict[str, Any] = {}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}


async def load_image(
        path: Union[Path, str],
        *,
        size: Optional[Union[Tuple[int, int], float]] = None,
        crop: Optional[Tuple[int, int, int, int]] = None,
        mode: Optional[str] = None,
) -> Image.Image:
    """
    读取图像，并预处理

    :param path: 图片路径
    :param size: 预处理尺寸
    :param crop: 预处理裁剪大小
    :param mode: 预处理图像模式
    :return: 图像对象
    """
    path = Path(path)
    if Pm_config.img_cache and str(path) in cache_image:
        img = cache_image[str(path)]
    else:
        if path.exists():
            img = Image.open(path)
        else:
            raise FileNotFoundError(f'{path} not found')
        if Pm_config.img_cache:
            cache_image[str(path)] = img
        elif cache_image:
            cache_image.clear()
    if mode:
        img = img.convert(mode)
    if size:
        if isinstance(size, float):
            img = img.resize(
                (int(img.size[0] * size), int(img.size[1] * size)), Image.LANCZOS)
        elif isinstance(size, tuple):
            img = img.resize(size, Image.LANCZOS)
    if crop:
        img = img.crop(crop)
    return img


def MessageBuild_Image(
    img: Union[Image.Image, PMImage, Path, str],
    *,
    size: Optional[Union[Tuple[int, int], float]] = None,
    crop: Optional[Tuple[int, int, int, int]] = None,
    quality: Optional[int] = 100,
    mode: Optional[str] = None
) -> MessageSegment:
    """
    说明：
    图片预处理并构造成MessageSegment
        :param img: 图片Image对象或图片路径
        :param size: 预处理尺寸
        :param crop: 预处理裁剪大小
        :param quality: 预处理图片质量
        :param mode: 预处理图像模式
        :return: MessageSegment.image
    """
    if isinstance(img, (str, Path)):
        img = load_image(path=img, size=size, mode=mode, crop=crop)
    else:
        if isinstance(img, PMImage):
            img = img.image
        if size:
            if isinstance(size, float):
                img = img.resize(
                    (int(img.size[0] * size), int(img.size[1] * size)), Image.LANCZOS)
            elif isinstance(size, tuple):
                img = img.resize(size, Image.LANCZOS)
        if crop:
            img = img.crop(crop)
        if mode:
            img = img.convert(mode)
    bio = BytesIO()
    img.save(bio, format='JPEG' if img.mode ==
             'RGB' else 'PNG', quality=quality)
    return MessageSegment.image(bio)
