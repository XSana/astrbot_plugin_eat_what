import random
from pathlib import Path
from typing import List, Optional

from PIL import Image as PILImage

import astrbot.api.message_components as Comp
from astrbot.api import logger, llm_tool
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import BaseMessageComponent, Image, Reply
from astrbot.core.star import StarTools
from astrbot.core.star.filter.permission import PermissionType
from data.plugins.astrbot_plugin_eat_what.datastore import EatWhatCategory, EatWhatDataStore


@register("eat_what", "XSana", "根据吃什么、喝什么关键字随机返回菜品或饮品", "1.1.1")
class EatWhat(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # 初始化
        self.data_store = EatWhatDataStore(StarTools.get_data_dir())
        self.food = self.data_store.food
        self.drink = self.data_store.drink

        # 关键词
        self.eat_keywords = self.config.get("eat_keywords") or []
        self.drink_keywords = self.config.get("drink_keywords") or []

        logger.info(f"eat_keywords: {self.eat_keywords}")
        logger.info(f"drink_keywords: {self.drink_keywords}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_keyword_detect(self, event: AstrMessageEvent):
        message_text = event.message_str or ""
        if not message_text:
            return

        for category, keywords in (
                (self.food, self.eat_keywords),
                (self.drink, self.drink_keywords)
        ):
            if not keywords:
                continue
            if self._match_keywords(message_text, keywords):
                chain = self._build_recommendation_chain(category)
                if chain is not None:
                    yield event.chain_result(chain)
                    event.stop_event()
                return

    @llm_tool("eat_what")
    async def llm_eat_what(self, event: AstrMessageEvent):
        """
        Call this tool when the user expresses a positive intention to ask
        what they should drink or wants a recommendation for a beverage.

        Use this tool in situations where the user:

        1) Explicitly asks what to drink or requests drink suggestions, e.g.:
           - "喝什么？"
           - "推荐一个饮料"
           - "我想喝点东西"
           - "来点喝的"

        2) Clearly shows a desire to drink something, such as:
           - "有啥好喝的推荐吗"
           - "有点渴，喝点啥好"
           - "不知道喝什么，你帮我选一个"

        Do NOT call this tool when the user is refusing or negating the idea of drinking,
        or explicitly saying they don't want a drink, for example:
           - "不喝点啥"
           - "今天不想喝东西"
           - "先不喝了"
           - "不要给我推荐喝的"

        This tool responds with a randomly selected drink item from the configured list,
        returned as a message chain (image and/or text depending on configuration).
        """
        chain = self._build_recommendation_chain(self.food)
        if chain is not None:
            yield event.chain_result(chain)
            event.stop_event()

    @llm_tool("drink_what")
    async def llm_drink_what(self, event: AstrMessageEvent):
        """
        Call this tool when the user expresses an intention to ask what they should drink
        or wants a recommendation for a beverage.
        Use this tool in situations where the user:
        1) Explicitly asks what to drink or requests drink suggestions, e.g.:
           - "喝什么？"
           - "推荐一个饮料"
           - "我想喝点东西"
           - "来点喝的"
        2) Shows clear intent related to wanting a drink, even without explicit keywords.
           Examples:
           - "口渴了，喝啥好"
           - "不知道喝点什么"
           - "给我推荐点喝的吧"
        This tool responds with a randomly selected drink item from the configured list,
        returned as a message chain (image and/or text depending on configuration).
        """
        chain = self._build_recommendation_chain(self.drink)
        if chain is not None:
            yield event.chain_result(chain)
            event.stop_event()

    @filter.command_group("eat_what")
    def eat_what(self):
        pass

    @eat_what.command("add")
    @filter.permission_type(PermissionType.ADMIN)
    async def add(self, event: AstrMessageEvent, type: str, name: str):
        category = self._get_category(type)
        if category is None:
            yield event.plain_result("类型错误，请使用 food 或 drink。")
        else:
            images = self._collect_images(
                getattr(event.message_obj, "message", None)
            )
            if not images:
                yield event.plain_result("添加失败：未检测到图片，请附带或引用一张图片。")
            elif len(images) > 1:
                yield event.plain_result("添加失败：目前仅支持一次添加一张图片。")
            elif name in category.items:
                yield event.plain_result(f"添加失败：「{name}」已存在")
            else:
                image = images[0]
                image_path = category.dir / f"{name}.jpg"
                try:
                    await self._save_image_as_jpg(image, image_path)
                    category.items.append(name)
                    yield event.plain_result(f"添加成功：「{name}」")
                except Exception as e:
                    logger.error(f"[eat_what] add {image_path} failed: {e}")
                    yield event.plain_result(f"添加失败：{e}")

        event.stop_event()

    @eat_what.command("del")
    @filter.permission_type(PermissionType.ADMIN)
    async def del_(self, event: AstrMessageEvent, type: str, name: str):
        category = self._get_category(type)
        if category is None:
            yield event.plain_result("类型错误，请使用 food 或 drink。")
        else:
            image_path = category.dir / f"{name}.jpg"

            if not image_path.exists():
                yield event.plain_result(f"删除失败：「{name}」不存在")
            else:
                try:
                    image_path.unlink()
                    if name in category.items:
                        category.items.remove(name)
                    yield event.plain_result(f"删除成功：「{name}」")
                except Exception as e:
                    logger.error(f"[eat_what] delete {image_path} failed: {e}")
                    yield event.plain_result(f"删除失败：{e}")

        event.stop_event()

    @eat_what.command("list")
    async def list(self, event: AstrMessageEvent, type: str):
        category = self._get_category(type)
        if category is None:
            yield event.plain_result("类型错误，请使用 food 或 drink。")
        else:
            if type == "food":
                yield event.plain_result(f"目前有 {len(self.food.items)} 个食物：\n{self.food.items}")
            else:
                yield event.plain_result(f"目前有 {len(self.drink.items)} 个饮料：\n{self.drink.items}")

        event.stop_event()

    def _get_category(self, type_: str) -> Optional[EatWhatCategory]:
        if type_ == "food":
            return self.food
        if type_ == "drink":
            return self.drink
        return None

    def _build_recommendation_chain(self, category: EatWhatCategory) -> Optional[List[BaseMessageComponent]]:
        if not category.items:
            return None
        name = random.choice(category.items)
        word = category.word
        image_path = str(category.dir / f"{name}.jpg")

        return [
            Comp.Image.fromFileSystem(image_path),
            Comp.Plain(f"推荐你{word}{name}")
        ]

    @staticmethod
    def _match_keywords(text: str, keywords: List[str]) -> Optional[str]:
        for keyword in keywords:
            if keyword in text:
                return keyword
        return None

    def _collect_images(self, components: List[BaseMessageComponent]) -> List[Image]:
        images: List[Image] = []
        if not components:
            return images

        for comp in components:
            if isinstance(comp, Image):
                images.append(comp)
            elif isinstance(comp, Reply) and comp.chain:
                images.extend(self._collect_images(comp.chain))
        return images

    @staticmethod
    async def _save_image_as_jpg(image_comp: Image, target_path: Path) -> None:
        src_path = await image_comp.convert_to_file_path()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with PILImage.open(src_path) as im:
            if im.mode in ("RGBA", "LA") or (
                    im.mode == "P" and "transparency" in im.info
            ):
                im_rgba = im.convert("RGBA")
                bg = PILImage.new("RGB", im_rgba.size, (255, 255, 255))
                alpha = im_rgba.split()[-1]  # A 通道
                bg.paste(im_rgba, mask=alpha)
                work = bg
            else:
                work = im.convert("RGB")

            max_width = 500
            w, h = work.size
            if w > max_width:
                scale = max_width / float(w)
                new_size = (max_width, int(h * scale))
                work = work.resize(new_size, PILImage.Resampling.LANCZOS)

            work.save(target_path, format="JPEG", quality=90, optimize=True)

    async def terminate(self):
        logger.info("[eat_what] plugin terminated")
