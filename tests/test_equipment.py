"""Equipment and item data consistency checks."""

from pathlib import Path

from afterdeath.player.equipment import ALL_EQUIPMENT
from afterdeath.player.items import ALL_ITEMS


def _missing_images(objects):
    missing = []
    for obj in objects:
        for attr in ("icon_path", "image_path"):
            path = getattr(obj, attr, None)
            if path and not Path(path).exists():
                missing.append(f"{obj.name}.{attr} -> {path}")
    return missing


def test_equipment_list_is_not_empty():
    assert ALL_EQUIPMENT


def test_every_weapon_has_a_weapon_type():
    weapons = [eq for eq in ALL_EQUIPMENT if getattr(eq, "type", None) == "weapon"]
    assert weapons, "expected at least one weapon"
    missing = [eq.name for eq in weapons if eq.weapon_type is None]
    assert not missing, f"weapons without weapon_type: {missing}"


def test_equipment_images_exist():
    missing = _missing_images(ALL_EQUIPMENT)
    assert not missing, "\n".join(missing)


def test_item_images_exist():
    missing = _missing_images(ALL_ITEMS)
    assert not missing, "\n".join(missing)
