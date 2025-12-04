from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import List  # Dict 已经不需要了，可以删掉

from astrbot.api import logger


@dataclass
class EatWhatCategory:
    word: str
    dir: Path
    items: List[str]


class EatWhatDataStore:

    def __init__(self, data_dir) -> None:
        self._plugin_dir = Path(__file__).resolve().parent
        self._assets_dir = self._plugin_dir / "assets"

        self._data_dir = data_dir
        self._foods_dir = self._data_dir / "foods"
        self._drinks_dir = self._data_dir / "drinks"

        self._init_flag_file = self._data_dir / ".initialized"

        self._init_data_from_assets()

        self.food_items = (
            [p.stem for p in self._foods_dir.iterdir() if p.is_file()]
            if self._foods_dir.exists()
            else []
        )
        self.drink_items = (
            [p.stem for p in self._drinks_dir.iterdir() if p.is_file()]
            if self._drinks_dir.exists()
            else []
        )

        self.food = EatWhatCategory(
            word="吃",
            dir=self._foods_dir,
            items=self.food_items,
        )
        self.drink = EatWhatCategory(
            word="喝",
            dir=self._drinks_dir,
            items=self.drink_items,
        )

        logger.info(f"[eat_what:init] Loaded food items: {self.food_items}")
        logger.info(f"[eat_what:init] Loaded drink items: {self.drink_items}")

    def _init_data_from_assets(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)

        if self._init_flag_file.exists():
            logger.info(
                "[eat_what:init] Data already initialized, skip copying from assets."
            )
            return

        for sub in ("foods", "drinks"):
            src_dir = self._assets_dir / sub
            dst_dir = self._data_dir / sub
            dst_dir.mkdir(parents=True, exist_ok=True)

            if not src_dir.exists():
                logger.warning(
                    f"[eat_what:init] Assets directory not found: {src_dir}"
                )
                continue

            copied = 0
            for src_file in src_dir.iterdir():
                if not src_file.is_file():
                    continue
                dst_file = dst_dir / src_file.name
                if dst_file.exists():
                    continue
                shutil.copy2(src_file, dst_file)
                copied += 1

            logger.info(
                f"[eat_what:init] Initialized {sub} data from assets, copied {copied} files."
            )

        try:
            self._init_flag_file.write_text("initialized", encoding="utf-8")
        except Exception as e:
            logger.warning(
                f"[eat_what:init] Failed to write init flag file: {e}"
            )