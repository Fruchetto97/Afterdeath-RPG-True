# Map configuration and mechanics for Foresta Dorsale Sud

import pygame
import math
import random

class Config_Data:
    NAME = "Citta_01"
    MAP_NAME = "citta_01"  # Used for save/load system
    TMX_PATH = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Mappe\Exports\Citta_01.tmx"
    TILESET_PATH = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Mappe\Tilesets\Citta_01_Tileset.png"
    MUSIC_PATH = r"C:\Users\franc\Desktop\Afterdeath_RPG\Musics\Boney Rattle.MP3"
    
    # VIGNETTE EFFECT
    HAS_VIGNETTE = True
    VIGNETTE_STRENGTH = 150  # Stronger vignette for darker borders
    VIGNETTE_POWER = 1.8    # Higher power for sharper falloff

    # FILTER EFFECT (overlay color)
    HAS_FILTER = False  # Set to True to enable filter
    FILTER_OPACITY = 18  # 10% of 255
    FILTER_COLOR = (180, 140, 255)  # Light purple (RGB)

    # Random item/equipment pools for this map
    # Each pool defines what can be found from specific objects
    RANDOM_ITEM_POOLS = {
        "prompt_random_object": {
            "items": [
                {"name": "Spacchiotti", "probability": 0.2, "quantity_min": 5, "quantity_max": 20},
                {"name": "Red Rathos Meat", "probability": 0.2, "quantity_min": 1, "quantity_max": 3},
                {"name": "Green Rathos Meat", "probability": 0.1, "quantity_min": 1, "quantity_max": 2},
                {"name": "Purple Rathos Meat", "probability": 0.1, "quantity_min": 1, "quantity_max": 1},
                {"name": "Pink Rathos Pulp", "probability": 0.1, "quantity_min": 1, "quantity_max": 1},
                {"name": "Red Rathos Pulp", "probability": 0.1, "quantity_min": 1, "quantity_max": 2},
            ],
            "equipment": [
                {"name": "spear_blusqua", "probability": 0.05, "quantity_min": 1, "quantity_max": 1},
                {"name": "staffsword_blusqua", "probability": 0.05, "quantity_min": 1, "quantity_max": 1},
            ],
            "nothing_probability": 0.1  # 10% chance to find nothing
        },
    }

    @staticmethod
    def get_random_loot(pool_name):
        """
        Get random loot from the specified pool.
        Returns: tuple (loot_type, item_name, quantity) or (None, None, 0) if nothing found
        """
        if pool_name not in Config_Data.RANDOM_ITEM_POOLS:
            return None, None, 0
        
        pool = Config_Data.RANDOM_ITEM_POOLS[pool_name]
        
        # Check if nothing is found
        nothing_chance = pool.get("nothing_probability", 0)
        if random.random() < nothing_chance:
            return None, None, 0
        
        # Combine all possible drops with their probabilities
        all_drops = []
        
        # Add items
        for item in pool.get("items", []):
            all_drops.append(("item", item))
        
        # Add equipment
        for equipment in pool.get("equipment", []):
            all_drops.append(("equipment", equipment))
        
        if not all_drops:
            return None, None, 0
        
        # Select based on probability
        total_weight = 0
        weighted_drops = []
        
        for drop_type, drop_data in all_drops:
            weight = drop_data["probability"]
            total_weight += weight
            weighted_drops.append((total_weight, drop_type, drop_data))
        
        # Normalize probabilities if they don't sum to 1
        if total_weight > 1:
            weighted_drops = [(w/total_weight, dt, dd) for w, dt, dd in weighted_drops]
            total_weight = 1
        
        # Select random drop
        rand_val = random.random() * total_weight
        current_weight = 0
        
        for weight, drop_type, drop_data in weighted_drops:
            current_weight += weight if total_weight <= 1 else drop_data["probability"]
            if rand_val <= current_weight:
                # Determine quantity
                min_qty = drop_data.get("quantity_min", 1)
                max_qty = drop_data.get("quantity_max", 1)
                quantity = random.randint(min_qty, max_qty)
                
                return drop_type, drop_data["name"], quantity
        
        # Fallback - should not reach here
        return None, None, 0

    # Bone grass mechanic
    @staticmethod
    def bone_grass_damage(player, tmx_data, is_running):
        player_center = (player.rect.centerx, player.rect.centery + tmx_data.tileheight)
        radius = tmx_data.tilewidth / 2
        on_bone_grass = False
        for layer in tmx_data.layers:
            if hasattr(layer, 'data'):
                for y, row in enumerate(layer.data):
                    for x, tile in enumerate(row):
                        if tile:
                            props = tmx_data.get_tile_properties_by_gid(tile)
                            if props and props.get('type') == 'Bone_grass':
                                tile_center = (
                                    x * tmx_data.tilewidth + tmx_data.tilewidth // 2,
                                    y * tmx_data.tileheight + tmx_data.tileheight // 2
                                )
                                dx = player_center[0] - tile_center[0]
                                dy = player_center[1] - tile_center[1]
                                if (dx*dx + dy*dy) <= (radius*radius):
                                    on_bone_grass = True
                                    break
                    if on_bone_grass:
                        break
            if on_bone_grass:
                break
        # Damage calculation
        base_damage = 0.002 if is_running else 0.001
        return on_bone_grass, base_damage

    # Prompt interaction scripts
    PROMPT_SCRIPTS = {
        "prompt_albero_dorsale": {
            "messages": [
                "This tree is made out of backbones...",
                "It looks scary..."
            ],
            
        },
        "prompt_rathos_morto_1": {
            "messages": [
                {"message": "The corpse of this dead Rathos drips some kind of black Ooze"},
                {"message": "You try to collect some of this Ooze"}
            ],
            "actions": [
                None,
                {"type": "add_item", "item": "Black Ooze"},
            ]
        },
        "prompt_random_object": {
            "actions": [
                {"type": "random_loot", "pool": "prompt_random_object"},
            ]
        },
        "prompt_staffsword_blusqua": {
            "messages": [
                "You find an old weapon embedded in the ground...",
                "It's a beautifully crafted staffsword made of Blusqua metal.",
                "You carefully extract it from the earth and add it to your equipment."
            ],
            "actions": [
                None,
                {"type": "add_equipment", "item": "staffsword_blusqua"},
                {"type": "remove_object"}
            ]
        },
        "prompt_mnemonic_altar": {
            "messages": [
                "You find a mysterious altar growing from the ground...",
                "There is a white sphere on top of it, somehow floating in mid-air...",
                "It seems to pulse with a soft light.",
                "You decide to take it, seeing a connection to the patterns of the Rebirth Towers."
            ],
            "actions": [
                None,
                None,
                None,
                {"type": "add_item", "item": "Mnemonic Fruit"}
            ]
        },
        # Add more prompt scripts here as needed
    }

    # Event interaction scripts
    EVENT_SCRIPTS = {
        "evento_ingresso_foresta_dorsale_sud": {
            "message": "DORSAL FOREST SOUTH",
            "duration": 4000
        },
        
        # Add more event scripts here as needed
    }

    # Vignette effect generator
    @staticmethod
    def create_vignette(width, height, strength=180, power=1.7):
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        cx, cy = width // 2, height // 2
        max_radius = math.hypot(cx, cy)
        for y in range(height):
            for x in range(width):
                dx = x - cx
                dy = y - cy
                dist = math.hypot(dx, dy)
                alpha = int(strength * (dist / max_radius) ** power)
                if alpha > 0:
                    vignette.set_at((x, y), (0, 0, 0, min(alpha, strength)))
        return vignette
