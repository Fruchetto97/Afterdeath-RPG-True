"""Every asset the code refers to must exist in the repository."""

import importlib
import pkgutil
from pathlib import Path

import pytest

import afterdeath
from afterdeath import paths
from afterdeath.data.status_effects import STATUS_EFFECTS_CONFIG
from afterdeath.overworld import maps
from afterdeath.overworld.enemies import ENEMIES_DATA

SPECIES = ["Maedo", "Minnago", "Sapifer", "Selkio"]


def all_modules():
    return [m.name for m in pkgutil.walk_packages(afterdeath.__path__, prefix="afterdeath.")]


@pytest.mark.parametrize("module", all_modules())
def test_every_module_imports(module):
    importlib.import_module(module)


def test_font_exists():
    assert Path(paths.FONT_PATH).exists()


@pytest.mark.parametrize("species", SPECIES)
def test_species_assets_exist(species):
    assert Path(paths.player_gif(species)).exists()
    assert Path(paths.species_sprite(species)).exists()
    assert (paths.PORTRAITS_DIR / f"{species}_Base_Icon.png").exists()


def test_map_configs_point_to_existing_files():
    configs = {cfg for cfg, _spawn in maps.MAP_TRANSITIONS.values()}
    for cfg in configs:
        assert Path(cfg.Config_Data.TMX_PATH).exists(), cfg.__name__
        assert Path(cfg.Config_Data.MUSIC_PATH).exists(), cfg.__name__


def test_enemy_sprites_exist():
    missing = []
    for enemy in ENEMIES_DATA:
        for key in ("image_path", "death_image_path"):
            if enemy.get(key) and not Path(enemy[key]).exists():
                missing.append(f"{enemy.get('name')}: {enemy[key]}")
        gif = enemy.get("battle_character", {}).get("gif_path")
        if gif and not Path(gif).exists():
            missing.append(f"{enemy.get('name')}: {gif}")
    assert not missing, "\n".join(missing)


def test_battle_backgrounds_available():
    assert list(paths.BATTLE_BACKGROUNDS_DIR.glob("*.png"))


def test_status_effect_gifs_follow_naming_convention():
    gifs = {p.name for p in paths.STATUS_GIFS_DIR.glob("*_gif.gif")}
    found = [name for name in STATUS_EFFECTS_CONFIG if f"{name.capitalize()}_gif.gif" in gifs]
    assert found, "no status effect GIF matches the <Name>_gif.gif convention"
