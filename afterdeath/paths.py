"""Filesystem locations for game assets and player data.

Every module must build asset paths through this module instead of hardcoding
absolute paths, so the game runs from any folder and from the PyInstaller build.
"""

import sys
from pathlib import Path

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # PyInstaller: bundled data lives in _MEIPASS, the player's data next to the exe.
    ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    USER_DATA_DIR = Path(sys.executable).resolve().parent / "userdata"
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent
    USER_DATA_DIR = ROOT_DIR / "userdata"

# --- Read-only assets ---------------------------------------------------------
ASSETS_DIR = ROOT_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "audio" / "music"
SFX_DIR = ASSETS_DIR / "audio" / "sfx"
FONTS_DIR = ASSETS_DIR / "fonts"
IMAGES_DIR = ASSETS_DIR / "images"
SPRITES_DIR = ASSETS_DIR / "sprites"
MAPS_DIR = ASSETS_DIR / "maps"

PORTRAITS_DIR = IMAGES_DIR / "portraits"
UI_DIR = IMAGES_DIR / "ui"
ITEMS_DIR = IMAGES_DIR / "items"
STATUS_GIFS_DIR = IMAGES_DIR / "status_effects"
BATTLE_BACKGROUNDS_DIR = IMAGES_DIR / "battle_backgrounds"
PLAYER_GIFS_DIR = SPRITES_DIR / "players"
ENEMY_GIFS_DIR = SPRITES_DIR / "enemies"
OVERWORLD_SPRITES_DIR = SPRITES_DIR / "overworld"

FONT_PATH = str(FONTS_DIR / "Pixellari.ttf")

# --- Writable player data -----------------------------------------------------
SAVES_DIR = USER_DATA_DIR / "saves"
SETTINGS_FILE = USER_DATA_DIR / "game_settings.json"
CHARACTER_DATA_FILE = USER_DATA_DIR / "character_data.json"

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)


def music(name: str) -> str:
    return str(MUSIC_DIR / name)


def sfx(name: str) -> str:
    return str(SFX_DIR / name)


def ui_image(name: str) -> str:
    return str(UI_DIR / name)


def item_image(category: str, name: str) -> str:
    return str(ITEMS_DIR / category / name)


def player_gif(species: str) -> str:
    return str(PLAYER_GIFS_DIR / f"{species}_Player_GIF.gif")


def enemy_gif(name: str) -> str:
    return str(ENEMY_GIFS_DIR / name)


def overworld_sprite(name: str) -> str:
    return str(OVERWORLD_SPRITES_DIR / name)


def species_sprite(species: str) -> str:
    return overworld_sprite(f"{species}_32p.png")


def map_file(name: str) -> str:
    return str(MAPS_DIR / name)
