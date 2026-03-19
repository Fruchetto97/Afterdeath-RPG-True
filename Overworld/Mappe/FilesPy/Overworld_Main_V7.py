# --- Standard and third-party imports (all at top) ---
corpse_interaction_counter = {}  # Legacy - to be removed
enemy_type_interaction_counter = {}  # Track total interactions per enemy type for limit system
import sys
import time
import pygame
import os
import time
import random
import math
import pygame
from io import BytesIO
try:
    from pytmx.util_pygame import load_pygame
except ImportError:
    load_pygame = None

import json
import os
from Save_System import save_system

# Add the parent directory to sys.path to import Global_SFX
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import Global_SFX

# Import Species_Config for species-specific configurations
from Species_Config import get_species_config, get_hp_ratios

# Parse command line arguments for save file loading
LOAD_SAVE_FILE = None
if len(sys.argv) > 2 and sys.argv[1] == "--load":
    LOAD_SAVE_FILE = sys.argv[2]
    print(f"[Overworld] Loading save file: {LOAD_SAVE_FILE}")

# --- Global Variables ---
LOADED_SAVE_DATA = None  # Store loaded save data for applying to PlayerStats
LOADED_PLAYER_POSITION = None  # Store loaded player position data
LOADED_MEMORY_SKILLS_DATA = None  # Store loaded memory skills data
WORLD_STATE = {  # Active world state tracking
    "explored_maps": [],
    "maps": {}  # map_name: { "killed_enemies": [{name, spawn_x, spawn_y, death_x, death_y}], "killed_objects": [{name, x, y}] }
}

# Debug: Print initial world state
print(f"[DEBUG] Initial WORLD_STATE: {WORLD_STATE}")

def load_character_data_from_file():
    """Load character data from file if it exists, otherwise return defaults"""
    character_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "character_data.json")
    
    try:
        if os.path.exists(character_file):
            with open(character_file, 'r') as f:
                data = json.load(f)
                print(f"[Overworld] Loaded character data from file: {data}")
                return data
    except Exception as e:
        print(f"[Overworld] Error loading character data: {e}")
    
    # Return defaults if file doesn't exist or error occurred
    return {
        'name': 'Default Player',
        'species': 'Selkio',
        'gif_path': r"C:\Users\franc\Desktop\Afterdeath_RPG\Player_GIFs\Selkio_Player_GIF.gif",
        'sprite_path': r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Selkio_32p.png"
    }

def save_character_data_to_file(character_data):
    """Save character data to file"""
    character_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "character_data.json")
    
    try:
        with open(character_file, 'w') as f:
            json.dump(character_data, f, indent=2)
        print(f"[Overworld] Saved character data to file: {character_file}")
    except Exception as e:
        print(f"[Overworld] Error saving character data: {e}")

def load_and_apply_save_data(save_file_path):
    """Load save data and apply it to the game state"""
    try:
        from Save_System import save_system
        
        # Load the save file
        save_data = save_system.load_save_file(save_file_path)
        if not save_data:
            print(f"[Overworld] Failed to load save file: {save_file_path}")
            return False
        
        # Extract player data (handle both old and new format)
        player_data = save_data.get("player", save_data.get("character", {}))
        
        # Update PLAYER_CHARACTER_DATA with saved data
        global PLAYER_CHARACTER_DATA
        PLAYER_CHARACTER_DATA['name'] = player_data.get('name', 'Unknown')
        PLAYER_CHARACTER_DATA['species'] = player_data.get('species', 'Maedo')
        PLAYER_CHARACTER_DATA['gif_path'] = player_data.get('gif_path', r"C:\Users\franc\Desktop\Afterdeath_RPG\Player_GIFs\Maedo_Player_GIF.gif")
        PLAYER_CHARACTER_DATA['sprite_path'] = player_data.get('sprite_path', r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Maedo_32p.png")
        
        # DO NOT save to global character_data.json - this causes cross-character contamination
        # save_character_data_to_file(PLAYER_CHARACTER_DATA)
        
        print(f"[Overworld] Applied save data: {PLAYER_CHARACTER_DATA}")
        
        # Store the save data for later use when creating PlayerStats
        global LOADED_SAVE_DATA, LOADED_PLAYER_POSITION
        LOADED_SAVE_DATA = save_data
        
        # Load and apply world state if available
        world_state = save_data.get("world_state", {})
        print(f"[DEBUG] Raw save_data keys: {list(save_data.keys())}")
        print(f"[DEBUG] world_state content: {world_state}")
        if world_state:
            print(f"[Overworld] Loading world state: {list(world_state.keys())}")
            
            # Load interaction counters (new system)
            global corpse_interaction_counter, enemy_type_interaction_counter, WORLD_STATE
            
            # Load enemy type interaction counters (new system)
            enemy_type_interactions = world_state.get("enemy_type_interactions", {})
            if enemy_type_interactions:
                enemy_type_interaction_counter.update(enemy_type_interactions)
                print(f"[Overworld] Loaded {len(enemy_type_interactions)} enemy type interaction counters")
            
            # Load legacy corpse interactions for backward compatibility
            corpse_interactions = world_state.get("corpse_interactions", {})
            if corpse_interactions:
                corpse_interaction_counter.update(corpse_interactions)
                print(f"[Overworld] Loaded {len(corpse_interactions)} legacy corpse interaction states")
            
            # Load world state data with explicit validation
            print(f"[DEBUG] Before loading - WORLD_STATE: {WORLD_STATE}")
            WORLD_STATE["explored_maps"] = world_state.get("explored_maps", [])
            WORLD_STATE["maps"] = world_state.get("maps", {})
            print(f"[DEBUG] After loading - WORLD_STATE: {WORLD_STATE}")
            print(f"[Overworld] Loaded world state: {len(WORLD_STATE['explored_maps'])} explored maps, {len(WORLD_STATE['maps'])} map states")
            
            # Validate specific content
            for map_name, map_data in WORLD_STATE["maps"].items():
                killed_enemies = map_data.get("killed_enemies", [])
                print(f"[DEBUG] Map '{map_name}' has {len(killed_enemies)} killed enemies: {killed_enemies}")
        else:
            print(f"[DEBUG] No world_state found in save file!")
        
        # Extract and store player position if available
        world_data = save_data.get("world_data", save_data.get("world_state", {}))
        player_position = world_data.get("player_position", save_data.get("player", {}).get("position", {}))
        if player_position and player_position.get("x") is not None:
            LOADED_PLAYER_POSITION = {
                "x": player_position.get("x", None),
                "y": player_position.get("y", None),
                "current_map": player_position.get("current_map", None)
            }
            print(f"[Overworld] Loaded player position: {LOADED_PLAYER_POSITION}")
        else:
            LOADED_PLAYER_POSITION = None
        
        # --- Load Memory Skills Data ---
        try:
            print(f"[Overworld] *** MEMORY SKILLS LOAD DEBUG START ***")
            memory_skills_data = save_data.get("player", {}).get("memory_skills", {})
            
            if memory_skills_data:
                # Store memory skills data globally for access by other systems
                global LOADED_MEMORY_SKILLS_DATA
                LOADED_MEMORY_SKILLS_DATA = {
                    "equipped": memory_skills_data.get("equipped", []),
                    "skill_states": memory_skills_data.get("skill_states", {}),
                    "available_memory_points": memory_skills_data.get("available_memory_points", 10)
                }
                print(f"[Overworld] Loaded memory skills data:")
                print(f"  - Equipped skills: {LOADED_MEMORY_SKILLS_DATA['equipped']}")
                print(f"  - Skill states: {LOADED_MEMORY_SKILLS_DATA['skill_states']}")
                print(f"  - Available points: {LOADED_MEMORY_SKILLS_DATA['available_memory_points']}")
            else:
                print(f"[Overworld] No memory skills data found in save file, using defaults")
                LOADED_MEMORY_SKILLS_DATA = {
                    "equipped": [],
                    "skill_states": {},
                    "available_memory_points": 10
                }
            print(f"[Overworld] *** MEMORY SKILLS LOAD DEBUG END ***")
        except Exception as e:
            print(f"[Overworld] Error loading memory skills data: {e}")
            import traceback
            traceback.print_exc()
            # Set defaults on error
            LOADED_MEMORY_SKILLS_DATA = {
                "equipped": [],
                "skill_states": {},
                "available_memory_points": 10
            }
        
        return True
        
    except Exception as e:
        print(f"[Overworld] Error loading save data: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_game_settings():
    """Load game settings from file"""
    settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "game_settings.json")
    
    # Default settings
    settings = {
        "music_volume": 0.7,
        "sfx_volume": 0.8,
        "fullscreen": False,
        "last_save_slot": 1
    }
    
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)
                print(f"[Overworld] Loaded game settings: fullscreen={settings['fullscreen']}")
        else:
            print("[Overworld] No game settings file found, using defaults")
    except Exception as e:
        print(f"[Overworld] Error loading game settings: {e}")
    
    return settings

def apply_fullscreen_setting(settings, screen_width, screen_height):
    """Apply fullscreen setting and return the configured screen"""
    try:
        if settings['fullscreen']:
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
            print("[Overworld] Applied fullscreen mode")
        else:
            screen = pygame.display.set_mode((screen_width, screen_height))
            print("[Overworld] Applied windowed mode")
        return screen
    except Exception as e:
        print(f"[Overworld] Error applying fullscreen setting: {e}")
        # Fallback to windowed mode
        return pygame.display.set_mode((screen_width, screen_height))

# Global variables to store character data from Main_Menu
PLAYER_CHARACTER_DATA = load_character_data_from_file()

# Load save data if specified via command line FIRST
if LOAD_SAVE_FILE:
    if load_and_apply_save_data(LOAD_SAVE_FILE):
        print(f"[Overworld] Successfully loaded save file: {LOAD_SAVE_FILE}")
    else:
        print(f"[Overworld] Failed to load save file, using default character data")

# Initialize player moves system with character data AFTER save data is loaded
print(f"[Overworld] Initializing player moves for character: {PLAYER_CHARACTER_DATA.get('name', 'Unknown')}")
try:
    from Player_Moves import initialize_player_moves
    initialize_player_moves(PLAYER_CHARACTER_DATA.get('name', 'Unknown Player'))
    print(f"[Overworld] Player moves initialized successfully")
except ImportError as e:
    print(f"[Overworld] Could not initialize player moves: {e}")

def reload_weapon_proficiency_from_save():
    """Reload weapon proficiency from the most recent save file - can be called at any time"""
    try:
        print(f"[WeaponReload] *** WEAPON PROFICIENCY RELOAD DEBUG START ***")
        
        # Find the player name to locate save file
        import Player_Stats
        if not hasattr(Player_Stats, 'player_stats') or not Player_Stats.player_stats:
            print("[WeaponReload] WARNING: No player stats available")
            return False
            
        player_name = Player_Stats.player_stats.name
        print(f"[WeaponReload] Looking for save file for player: {player_name}")
        
        # Find the most recent save file for this character
        import os
        from pathlib import Path
        script_dir = Path(__file__).parent
        saves_dir = script_dir / "saves"
        
        if not saves_dir.exists():
            print("[WeaponReload] WARNING: No saves directory found")
            return False
            
        save_files = list(saves_dir.glob(f"save_{player_name}_*.json"))
        if not save_files:
            print(f"[WeaponReload] No save files found for {player_name}")
            return False
            
        # Get the most recent save file
        latest_save = max(save_files, key=lambda p: p.stat().st_mtime)
        print(f"[WeaponReload] Loading from save file: {latest_save.name}")
        
        # Load the save data
        import json
        with open(latest_save, 'r') as f:
            save_data = json.load(f)
            
        # Check if weapon proficiency data exists
        if "player" not in save_data or "weapon_proficiencies" not in save_data["player"]:
            print("[WeaponReload] No weapon proficiencies found in save file")
            return False
            
        weapon_profs = save_data["player"]["weapon_proficiencies"]
        print(f"[WeaponReload] Found weapon proficiencies in save: {weapon_profs}")
        
        # Load equipment system
        from Player_Equipment import get_main_player_equipment
        equip_obj = get_main_player_equipment()
        print(f"[WeaponReload] Equipment object retrieved: {type(equip_obj)}")
        
        if equip_obj and hasattr(equip_obj, 'weapon_proficiency'):
            prof_sys = equip_obj.weapon_proficiency
            print(f"[WeaponReload] weapon_proficiency system found: {type(prof_sys)}")
            
            # Show current state before loading
            print(f"[WeaponReload] Current weapon proficiencies BEFORE reload:")
            for wpn_class, level in prof_sys.wpn_class_proficiency.items():
                exp = prof_sys.wpn_class_exp.get(wpn_class, 0)
                if level > 0 or exp > 0:
                    print(f"[WeaponReload]   BEFORE {wpn_class}: Level {level}, EXP {exp}")
            
            restored = 0
            for wpn_class, pdata in weapon_profs.items():
                if isinstance(pdata, dict) and "proficiency" in pdata and "experience" in pdata:
                    if wpn_class in prof_sys.wpn_class_proficiency:
                        old_level = prof_sys.wpn_class_proficiency[wpn_class]
                        old_exp = prof_sys.wpn_class_exp.get(wpn_class, 0)
                        
                        prof_sys.wpn_class_proficiency[wpn_class] = pdata.get('proficiency', 0)
                        prof_sys.wpn_class_exp[wpn_class] = pdata.get('experience', 0)
                        restored += 1
                        
                        new_level = pdata.get('proficiency', 0)
                        new_exp = pdata.get('experience', 0)
                        print(f"[WeaponReload] LOADED {wpn_class}: Level {new_level}, EXP {new_exp} (was L{old_level}, E{old_exp})")
                    else:
                        print(f"[WeaponReload] WARNING: Weapon class {wpn_class} not found in proficiency system")
                else:
                    print(f"[WeaponReload] WARNING: Invalid proficiency data for {wpn_class}: {pdata}")
            
            # Show final state after loading
            print(f"[WeaponReload] Current weapon proficiencies AFTER reload:")
            for wpn_class, level in prof_sys.wpn_class_proficiency.items():
                exp = prof_sys.wpn_class_exp.get(wpn_class, 0)
                if level > 0 or exp > 0:
                    print(f"[WeaponReload]   AFTER {wpn_class}: Level {level}, EXP {exp}")
            
            print(f"[WeaponReload] Successfully reloaded {restored} weapon proficiency entries")
            print(f"[WeaponReload] *** WEAPON PROFICIENCY RELOAD DEBUG END ***")
            return True
        else:
            print("[WeaponReload] WARNING: Equipment object missing; cannot reload proficiencies")
        
        print(f"[WeaponReload] *** WEAPON PROFICIENCY RELOAD DEBUG END ***")
        return False
    except Exception as e:
        print(f"[WeaponReload] ERROR reloading weapon proficiencies: {e}")
        import traceback
        traceback.print_exc()
        return False

def initialize_player_from_loaded_save():
    """If a save was loaded before game loop start, build PlayerStats now."""
    global player_stats, pause_menu
    if LOADED_SAVE_DATA and player_stats is None:
        save_player_data = LOADED_SAVE_DATA.get("player", LOADED_SAVE_DATA.get("character", {}))
        PLAYER_CHARACTER_DATA['name'] = save_player_data.get('name', PLAYER_CHARACTER_DATA['name'])
        PLAYER_CHARACTER_DATA['species'] = save_player_data.get('species', PLAYER_CHARACTER_DATA['species'])
        save_stats = save_player_data.get('stats', {})
        player_stats_local = PlayerStats(
            name=PLAYER_CHARACTER_DATA['name'],
            gif_path=PLAYER_CHARACTER_DATA['gif_path'],
            sprite_path=PLAYER_CHARACTER_DATA['sprite_path'],
            has_extra_limbs=False,
            max_extral_limbs_hp=0,
            level=save_player_data.get('level', 1),
            exp=save_player_data.get('exp', 0),
            evo_points_hp=save_stats.get('evo_points_hp', 0),
            evo_points_regen=save_stats.get('evo_points_regen', 0),
            evo_points_stamina=save_stats.get('evo_points_stamina', 0),
            evo_points_reserve=save_stats.get('evo_points_reserve', 0),
            evo_points_strength=save_stats.get('evo_points_strength', 0),
            evo_points_dexterity=save_stats.get('evo_points_dexterity', 0),
            evo_points_special=save_stats.get('evo_points_special', 0),
            evo_points_speed=save_stats.get('evo_points_speed', 0)
        )
        # Apply variable (current) stats after construction
        # Skip read-only properties that are calculated dynamically
        readonly_properties = {'max_head_hp', 'max_body_hp', 'max_left_arm_hp', 'max_right_arm_hp', 'max_left_leg_hp', 'max_right_leg_hp', 'max_extral_limbs_hp'}
        for k, v in save_stats.items():
            if hasattr(player_stats_local, k) and k not in readonly_properties:
                setattr(player_stats_local, k, v)
        player_stats = player_stats_local
        pause_menu = PauseMenu(screen_width, screen_height, player_stats)
        print(f"[Overworld] Initialized player from save: level={player_stats.level} exp={player_stats.exp}")
        # Rebuild equipment & items from save data
        # First clear any default-populated equipment/items so only saved state remains
        try:
            from Player_Equipment import Clear_Equipment
            # Clear the main player object (which has default name "Selkio Guerriero")
            Clear_Equipment(None, reset_proficiencies=False)  # None = use main player
        except Exception as e:
            print(f"[Overworld] Warning: could not clear default equipment before rebuild: {e}")
        try:
            from Player_Items import Clear_Items
            # Clear the main player object
            Clear_Items(None)  # None = use main player
        except Exception as e:
            print(f"[Overworld] Warning: could not clear default items before rebuild: {e}")
        try:
            rebuild_equipment_from_save(LOADED_SAVE_DATA)
        except Exception as e:
            print(f"[Overworld] Equipment rebuild error: {e}")
        try:
            rebuild_items_from_save(LOADED_SAVE_DATA)
        except Exception as e:
            print(f"[Overworld] Item rebuild error: {e}")

# --- Save reconstruction helpers ---
def find_original_equipment_by_name(eq_name):
    """Find original equipment definition by name using the automated registry."""
    try:
        from Player_Equipment import find_equipment_by_name
        return find_equipment_by_name(eq_name)
    except Exception as e:
        print(f"[Overworld] Error finding equipment '{eq_name}': {e}")
        return None

def find_original_item_by_name(item_name):
    """Find original item definition by name using the automated registry."""
    try:
        from Player_Items import find_item_by_name
        return find_item_by_name(item_name)
    except Exception as e:
        print(f"[Overworld] Error finding item '{item_name}': {e}")
        return None

def rebuild_equipment_from_save(save_data):
    player_block = save_data.get('player', {})
    saved_equipment = player_block.get('equipment', {})
    if not saved_equipment:
        return
    from Player_Equipment import player_equip, PlayerEquip, Equipment, example_move1, example_move2, example_move3, example_move4, get_main_player_equipment
    name = player_block.get('name', 'Player')
    
    # Get the main player equipment object and add equipment to it
    main_player_equip = get_main_player_equipment()
    
    for eq_name, eq_data in saved_equipment.items():
        eq_type = eq_data.get('type', 'armor')
        weapon_class = eq_data.get('weapon_class')
        moves = []
        
        # Try to get icon/image paths from save first, then fall back to original definitions
        saved_icon_path = eq_data.get('icon_path')
        saved_image_path = eq_data.get('image_path')
        
        # Find original equipment to get proper icon/image paths if not in save
        original_eq = find_original_equipment_by_name(eq_name)
        icon_path = saved_icon_path if saved_icon_path else (original_eq.icon_path if original_eq else None)
        image_path = saved_image_path if saved_image_path else (original_eq.image_path if original_eq else None)
        description = original_eq.description if original_eq else f"Restored {eq_name}"
        short_description = original_eq.short_description if original_eq else f"Restored {eq_name}"
        
        # Get weapon_type from save data or fallback to original equipment
        saved_weapon_type = eq_data.get('weapon_type')
        weapon_type = saved_weapon_type if saved_weapon_type else (original_eq.weapon_type if original_eq else None)
        
        if eq_type == 'weapon':
            # Use the original equipment's moves instead of hardcoded mapping
            if original_eq and original_eq.moves:
                moves = original_eq.moves.copy()  # Use the original moves from the equipment definition
            else:
                # Fallback to hardcoded mapping if original equipment not found
                for mv in eq_data.get('moves', []):
                    if mv == 'Slash': moves.append(example_move1)
                    elif mv == 'Pierce': moves.append(example_move2)
                    elif mv == 'Smash': moves.append(example_move3)
                    elif mv == 'Ultimate': moves.append(example_move4)
        
        eq_obj = Equipment(eq_name, icon_path, image_path, eq_type, description, short_description, 
                          equipped=eq_data.get('equipped', False), moves=moves, weapon_class=weapon_class, weapon_type=weapon_type)
        
        # Load the images immediately after creation
        if icon_path or image_path:
            eq_obj.load_images()
        
        main_player_equip.add_equipment(eq_obj)
    
    # Also update the player_equip dictionary to use the saved character name
    player_equip[name] = main_player_equip
    
    # Load weapon proficiencies from save data
    saved_weapon_proficiencies = player_block.get('weapon_proficiencies', {})
    if saved_weapon_proficiencies and hasattr(main_player_equip, 'weapon_proficiency'):
        print(f"[EquipmentLoad] *** LOADING WEAPON PROFICIENCIES FROM SAVE ***")
        print(f"[EquipmentLoad] Found {len([k for k, v in saved_weapon_proficiencies.items() if v.get('proficiency', 0) > 0 or v.get('experience', 0) > 0])} weapon classes with progress")
        print(f"[EquipmentLoad] Target WeaponProficiency object ID: {id(main_player_equip.weapon_proficiency)}")
        
        # Load each weapon class proficiency
        for weapon_class, prof_data in saved_weapon_proficiencies.items():
            proficiency_level = prof_data.get('proficiency', 0)
            experience_points = prof_data.get('experience', 0)
            
            if proficiency_level > 0 or experience_points > 0:
                print(f"[EquipmentLoad] Loading {weapon_class}: Level {proficiency_level}, EXP {experience_points}")
                # Directly set the values in the weapon proficiency dictionaries
                main_player_equip.weapon_proficiency.wpn_class_proficiency[weapon_class] = proficiency_level
                main_player_equip.weapon_proficiency.wpn_class_exp[weapon_class] = experience_points
        
        print(f"[EquipmentLoad] *** WEAPON PROFICIENCIES LOADED SUCCESSFULLY ***")
        
        # Verify the load worked
        from Player_Equipment import get_main_player_equipment
        verification_equip = get_main_player_equipment()
        if hasattr(verification_equip, 'weapon_proficiency'):
            non_zero_profs = {k: {'level': verification_equip.weapon_proficiency.wpn_class_proficiency[k], 
                                  'exp': verification_equip.weapon_proficiency.wpn_class_exp[k]} 
                              for k in verification_equip.weapon_proficiency.wpn_class_proficiency.keys() 
                              if (verification_equip.weapon_proficiency.wpn_class_proficiency[k] > 0 or 
                                  verification_equip.weapon_proficiency.wpn_class_exp[k] > 0)}
            print(f"[EquipmentLoad] Verification - Loaded non-zero proficiencies: {non_zero_profs}")
    else:
        print(f"[EquipmentLoad] No weapon proficiencies found in save data or weapon_proficiency object missing")
    print(f"[Overworld] Rebuilt {len(saved_equipment)} equipment entries from save")

def rebuild_items_from_save(save_data):
    player_block = save_data.get('player', {})
    saved_items = player_block.get('items', {})
    if not saved_items:
        return
    from Player_Items import player_items, PlayerItems, Item, use_food, use_black_ooze, use_mnemonic_fruit, use_spacchiotti, get_main_player_items
    name = player_block.get('name', 'Player')
    
    # Get the main player items object and add items to it
    main_player_items = get_main_player_items()
    
    for item_name, item_data in saved_items.items():
        item_type = (item_data.get('type') or '').upper()
        if item_type not in ['MISC','FOOD','KEY']:
            continue
        count = item_data.get('count', 1)
        
        # Try to get icon/image paths from save first, then fall back to original definitions
        saved_icon_path = item_data.get('icon_path')
        saved_image_path = item_data.get('image_path')
        
        # Find original item to get proper icon/image paths and other properties if not in save
        original_item = find_original_item_by_name(item_name)
        icon_path = saved_icon_path if saved_icon_path else (original_item.icon_path if original_item else None)
        image_path = saved_image_path if saved_image_path else (original_item.image_path if original_item else None)
        description = original_item.description if original_item else f"Restored {item_name}"
        short_description = original_item.short_description if original_item else f"Restored {item_name}"
        value = original_item.value if original_item else 0
        weight = original_item.weight if original_item else 0
        reserve_restored = getattr(original_item, 'reserve_restored', 0) if original_item else 0
        
        script = None
        if item_type == 'FOOD':
            script = use_food
        elif item_name == 'Mnemonic Fruit':
            script = use_mnemonic_fruit
        elif item_name == 'Black Ooze':
            script = use_black_ooze
        elif item_name == 'Spacchiotti':
            script = use_spacchiotti
        
        itm = Item(item_name, icon_path, image_path, item_type, description, short_description, 
                  value=value, weight=weight, script=script, reserve_restored=reserve_restored)
        
        # Load the images immediately after creation
        if icon_path or image_path:
            itm.load_images()
        
        main_player_items.add_item(itm, count)
    
    # Also update the player_items dictionary to use the saved character name
    player_items[name] = main_player_items
    print(f"[Overworld] Rebuilt {len(main_player_items.items)} item entries from save")


def set_character_data(character_name, species_name):
    """Function to set character data from Main_Menu"""
    global PLAYER_CHARACTER_DATA, player_stats, player, pause_menu
    global tmx_data, selected_spawnpoint, player_group, camera, screen_width, screen_height
    import builtins
    just_saved = getattr(builtins, '_AFTERDEATH_JUST_SAVED', False)
    if just_saved:
        print('[Overworld] NOTE: set_character_data called right after a save. Skipping stat reinitialization to avoid overwriting freshly saved progress.')
    
    PLAYER_CHARACTER_DATA['name'] = character_name
    PLAYER_CHARACTER_DATA['species'] = species_name
    PLAYER_CHARACTER_DATA['gif_path'] = f"C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Player_GIFs\\{species_name}_Player_GIF.gif"
    PLAYER_CHARACTER_DATA['sprite_path'] = f"C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\characters\\{species_name}_32p.png"
    
    print(f"[Overworld] Character data set: {PLAYER_CHARACTER_DATA}")
    
    # Save to file so it persists between runs
    save_character_data_to_file(PLAYER_CHARACTER_DATA)
    
    # Create a brand new PlayerStats object instead of trying to reinitialize
    # If we have loaded save data, use it to initialize PlayerStats
    if LOADED_SAVE_DATA and not just_saved:
        save_player_data = LOADED_SAVE_DATA.get("player", LOADED_SAVE_DATA.get("character", {}))
        save_stats = save_player_data.get("stats", {})
        
        player_stats = PlayerStats(
            name=PLAYER_CHARACTER_DATA['name'],
            gif_path=PLAYER_CHARACTER_DATA['gif_path'],
            sprite_path=PLAYER_CHARACTER_DATA['sprite_path'],
            has_extra_limbs=False,
            max_extral_limbs_hp=0,
            level=save_player_data.get('level', 1),
            exp=save_player_data.get('exp', 0),
            evo_points_hp=save_stats.get('evo_points_hp', 0),
            evo_points_regen=save_stats.get('evo_points_regen', 0),
            evo_points_stamina=save_stats.get('evo_points_stamina', 0),
            evo_points_reserve=save_stats.get('evo_points_reserve', 0),
            evo_points_strength=save_stats.get('evo_points_strength', 0),
            evo_points_dexterity=save_stats.get('evo_points_dexterity', 0),
            evo_points_special=save_stats.get('evo_points_special', 0),
            evo_points_speed=save_stats.get('evo_points_speed', 0)
        )
        
        # Apply saved stats directly
        if save_stats:
            player_stats.hp = save_stats.get('hp', player_stats.hp)
            player_stats.max_hp = save_stats.get('max_hp', player_stats.max_hp)
            player_stats.regen = save_stats.get('regen', player_stats.regen)
            player_stats.max_regen = save_stats.get('max_regen', player_stats.max_regen)
            player_stats.reserve = save_stats.get('reserve', player_stats.reserve)
            player_stats.max_reserve = save_stats.get('max_reserve', player_stats.max_reserve)
            player_stats.stamina = save_stats.get('stamina', player_stats.stamina)
            player_stats.max_stamina = save_stats.get('max_stamina', player_stats.max_stamina)
            
            # Apply body part current HP (max values are calculated dynamically from total_hp)
            player_stats.head_hp = save_stats.get('head_hp', player_stats.head_hp)
            # Skip max_head_hp - it's a calculated property based on total_hp and species ratios
            player_stats.body_hp = save_stats.get('body_hp', player_stats.body_hp)
            # Skip max_body_hp - it's a calculated property based on total_hp and species ratios
            player_stats.right_arm_hp = save_stats.get('right_arm_hp', player_stats.right_arm_hp)
            # Skip max_right_arm_hp - it's a calculated property based on total_hp and species ratios
            player_stats.left_arm_hp = save_stats.get('left_arm_hp', player_stats.left_arm_hp)
            # Skip max_left_arm_hp - it's a calculated property based on total_hp and species ratios
            player_stats.right_leg_hp = save_stats.get('right_leg_hp', player_stats.right_leg_hp)
            # Skip max_right_leg_hp - it's a calculated property based on total_hp and species ratios
            player_stats.left_leg_hp = save_stats.get('left_leg_hp', player_stats.left_leg_hp)
            # Skip max_left_leg_hp - it's a calculated property based on total_hp and species ratios
        
        # Apply saved equipment and inventory if available
        saved_equipment = save_player_data.get("equipment", {})
        saved_inventory = save_player_data.get("inventory", {})
        saved_weapon_proficiencies = save_player_data.get("weapon_proficiencies", {})
        
        if saved_equipment:
            # TODO: Apply equipment to player_stats when equipment system is integrated
            print(f"[Overworld] Found saved equipment: {list(saved_equipment.keys())}")
            
        if saved_inventory:
            # TODO: Apply inventory to player_stats when inventory system is integrated
            print(f"[Overworld] Found saved inventory: {list(saved_inventory.keys())}")
            
        if saved_weapon_proficiencies:
            print(f"[Overworld] Restoring weapon proficiencies for {len(saved_weapon_proficiencies)} classes")
            try:
                from Player_Equipment import get_main_player_equipment
                equip_obj = get_main_player_equipment()
                if equip_obj and hasattr(equip_obj, 'weapon_proficiency'):
                    prof_sys = equip_obj.weapon_proficiency
                    restored = 0
                    for wpn_class, pdata in saved_weapon_proficiencies.items():
                        if wpn_class in prof_sys.wpn_class_proficiency:
                            prof_sys.wpn_class_proficiency[wpn_class] = pdata.get('proficiency', 0)
                            prof_sys.wpn_class_exp[wpn_class] = pdata.get('experience', 0)
                            restored += 1
                    print(f"[Overworld] Applied {restored} weapon proficiency entries")
                else:
                    print("[Overworld] Equipment object missing; cannot apply proficiencies")
            except Exception as e:
                print(f"[Overworld] Error applying weapon proficiencies: {e}")
        
        # Apply equipment equipped state
        if saved_equipment:
            try:
                from Player_Equipment import get_main_player_equipment
                equip_obj = get_main_player_equipment()
                if equip_obj:
                    name_map = {eq.name: eq for eq in equip_obj.get_equipment_list()}
                    applied = 0
                    for eq_name, eq_data in saved_equipment.items():
                        eq_obj = name_map.get(eq_name)
                        if not eq_obj:
                            continue
                        # Set equipped flag directly; slot conflicts handled by game logic later
                        eq_obj.equipped = bool(eq_data.get('equipped', False))
                        applied += 1
                    print(f"[Overworld] Restored equipped flags for {applied} items")
                else:
                    print("[Overworld] No equipment object to apply saved equipment state")
            except Exception as e:
                print(f"[Overworld] Error applying equipment state: {e}")
        
        print(f"[Overworld] PlayerStats loaded from save: Level {player_stats.level}, HP {player_stats.hp}/{player_stats.max_hp}")
    else:
        # Default PlayerStats for new game
        if not just_saved:  # Only create brand new stats if this is not right after saving
            player_stats = PlayerStats(
                name=PLAYER_CHARACTER_DATA['name'],
                gif_path=PLAYER_CHARACTER_DATA['gif_path'],
                sprite_path=PLAYER_CHARACTER_DATA['sprite_path'],
                has_extra_limbs=False,
                max_extral_limbs_hp=0,
                level=1,
                exp=0,
                evo_points_hp=0,
                evo_points_regen=0,
                evo_points_stamina=0,
                evo_points_reserve=0,
                evo_points_strength=0,
                evo_points_dexterity=0,
                evo_points_special=0,
                evo_points_speed=0
            )
        else:
            print('[Overworld] Skipped creating new PlayerStats due to immediate post-save load.')
    
    if 'player_stats' in globals():
        try:
            print(f"[Overworld] PlayerStats state after set_character_data: level={player_stats.level}, exp={getattr(player_stats,'exp',None)}, hp={getattr(player_stats,'hp',None)} id={id(player_stats)} just_saved={just_saved}")
        except Exception:
            pass
    
    # If we're in a full game environment, update the player and pause menu
    if 'player' in globals() and 'player_group' in globals():
        # Remove old player and recreate with new sprite
        if player in player_group:
            player_group.remove(player)
        
        # Recreate player with correct sprite path
        spawn_position = find_spawn_point(tmx_data, selected_spawnpoint)
        player = Player(spawn_position, player_group, player_stats.sprite_path)
        player.speed *= 24
        
        # Update camera to center on new player
        initial_camera_x = player.pos.x - (screen_width / camera.zoom_factor) / 2
        initial_camera_y = player.pos.y - (screen_height / camera.zoom_factor) / 2
        camera.set_position(initial_camera_x, initial_camera_y)
        
        # Recreate pause menu with updated player stats
        pause_menu = PauseMenu(screen_width, screen_height, player_stats)
        
        print(f"[Overworld] Game reinitialized successfully for {player_stats.name}")
        print(f"[Overworld] Player sprite: {player_stats.sprite_path}")
        print(f"[Overworld] Player GIF: {player_stats.gif_path}")
    
    return PLAYER_CHARACTER_DATA

def main_game_loop():
    # Ensure player is initialized from save before entering loop
    initialize_player_from_loaded_save()
    """Main game loop - contains all the game logic that was previously at module level"""
    global reserve_logic_timer, transition_timer, is_transitioning
    global message_display, clock, screen
    
    print("[Overworld] Starting main game loop...")
    
    # Initialize message display
    message_display = MessageDisplay(screen_width, screen_height)
    
    # Remove the incomplete first loop - go straight to main initialization
    print("[DEBUG] Skipping incomplete transition loop, proceeding to main game loop")
from Overworld_Menu_V2 import PauseMenu, show_pause_menu
from Enemies_List import NPC, ENEMIES_DATA, create_npc_from_data, get_enemy_data_by_name
import Map_Roadmap
# Import the real combat system instead of mockup
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import Battle_Menu_Beta_V18 as CombatSystem
try:
    import Player_Equipment
except ImportError:
    Player_Equipment = None
    print("[WARN] Player_Equipment module not found - equipment actions will be logged only")
from Player_Equipment import WeaponProficiency, Equipment, simulate_weapon_training, add_combat_experience

try:
    import Player_Items
except ImportError:
    Player_Items = None
    print("[WARN] Player_Items module not found - item actions will be logged only")

# --- Utility Functions for Object and World State Management ---
def is_object_killed_nearby(obj_name, obj_x, obj_y, killed_objects_list, tolerance=50, used_records=None):
    """
    Check if an object with the given name was killed near the specified coordinates.
    Uses proximity matching instead of exact coordinate matching to handle floating point precision.
    
    Args:
        obj_name (str): Name of the object
        obj_x, obj_y (float): Object coordinates
        killed_objects_list (list): List of killed objects from world state
        tolerance (float): Maximum distance to consider a match (default: 50 pixels)
        used_records (set): Set of already used killed object record IDs to prevent duplicates
        
    Returns:
        dict or None: The killed object record if found nearby, None otherwise
    """
    if used_records is None:
        used_records = set()
    
    for i, killed_obj in enumerate(killed_objects_list):
        # Create unique ID for this record to prevent reuse
        record_id = f"{killed_obj['name']}_{killed_obj['x']}_{killed_obj['y']}"
        
        if record_id in used_records:
            continue  # Skip already used records
            
        if killed_obj["name"] == obj_name:
            # Calculate distance between object and killed object coordinates
            distance = math.hypot(obj_x - killed_obj["x"], obj_y - killed_obj["y"])
            if distance <= tolerance:
                print(f"[ObjectKill] Found nearby killed object '{obj_name}' - distance: {distance:.1f}px (tolerance: {tolerance}px)")
                used_records.add(record_id)  # Mark this record as used
                return killed_obj
    return None

# --- PS4 Controller Support ---
class ControllerInput:
    def __init__(self):
        self.controller = None
        self.deadzone = 0.3  # Analog stick deadzone
        self.init_controller()
        
    def init_controller(self):
        """Initialize PS4 controller"""
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            print(f"[Controller] Connected: {self.controller.get_name()}")
        else:
            print("[Controller] No controller detected")
            
    def is_connected(self):
        """Check if controller is connected"""
        return self.controller is not None and self.controller.get_init()
        
    def get_left_stick(self):
        """Get left stick input (for movement)"""
        if not self.is_connected():
            return (0, 0)
        
        x = self.controller.get_axis(0)  # Left stick X
        y = self.controller.get_axis(1)  # Left stick Y
        
        # Apply deadzone
        if abs(x) < self.deadzone:
            x = 0
        if abs(y) < self.deadzone:
            y = 0
            
        return (x, y)
        
    def is_button_pressed(self, button_name):
        """Check if specific PS4 button is currently pressed"""
        if not self.is_connected():
            return False
            
        # PS4 button mapping
        button_map = {
            'x': 0,        # X button (confirm/spacebar)
            'circle': 1,   # O button (cancel/ESC)
            'square': 2,   # Square button (shift/run/info)
            'triangle': 3, # Triangle button
            'r1': 5,       # R1 button (regenerate/R)
            'l1': 4,       # L1 button
            'r2': 7,       # R2 trigger
            'l2': 6,       # L2 trigger
            'share': 8,    # Share button
            'options': 9,  # Options button
            'l3': 10,      # Left stick press
            'r3': 11,      # Right stick press
            'ps': 12,      # PS button
            'touchpad': 13 # Touchpad press
        }
        
        if button_name in button_map:
            return self.controller.get_button(button_map[button_name])
        return False
        
    def get_dpad(self):
        """Get D-pad input (returns tuple of up, down, left, right bools)"""
        if not self.is_connected():
            return (False, False, False, False)
            
        # D-pad is often mapped as hat
        if self.controller.get_numhats() > 0:
            hat = self.controller.get_hat(0)
            up = hat[1] == 1
            down = hat[1] == -1
            left = hat[0] == -1
            right = hat[0] == 1
            return (up, down, left, right)
        return (False, False, False, False)

# Initialize controller
controller_input = ControllerInput()

def get_unified_input():
    """Get unified input from keyboard and controller"""
    # If keys are disabled during transitions, return empty input
    if keys_disabled:
        return {
            # Movement
            'left': False, 'right': False, 'up': False, 'down': False,
            # Action buttons
            'confirm': False, 'cancel': False, 'run_info': False, 'regenerate': False,
            # Menu navigation
            'menu_up': False, 'menu_down': False, 'menu_left': False, 'menu_right': False,
            # Special keys
            'f11': False, 'plus': False, 'minus': False, 'debug_e': False, 'z': False
        }
    
    keys = pygame.key.get_pressed()
    
    # Movement input (keyboard + left stick + dpad)
    left_stick = controller_input.get_left_stick()
    dpad = controller_input.get_dpad()
    
    # Convert analog stick to digital input
    stick_left = left_stick[0] < -0.5
    stick_right = left_stick[0] > 0.5
    stick_up = left_stick[1] < -0.5
    stick_down = left_stick[1] > 0.5
    
    unified_input = {
        # Movement
        'left': keys[pygame.K_LEFT] or keys[pygame.K_a] or stick_left or dpad[2],
        'right': keys[pygame.K_RIGHT] or keys[pygame.K_d] or stick_right or dpad[3],
        'up': keys[pygame.K_UP] or keys[pygame.K_w] or stick_up or dpad[0],
        'down': keys[pygame.K_DOWN] or keys[pygame.K_s] or stick_down or dpad[1],
        
        # Action buttons
        'confirm': keys[pygame.K_SPACE] or controller_input.is_button_pressed('x'),
        'cancel': keys[pygame.K_ESCAPE] or controller_input.is_button_pressed('circle'),
        'run_info': keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or controller_input.is_button_pressed('square'),
        'regenerate': keys[pygame.K_r] or controller_input.is_button_pressed('r1'),
        
        # Menu navigation (also use face buttons for menus)
        'menu_up': keys[pygame.K_UP] or keys[pygame.K_w] or stick_up or dpad[0],
        'menu_down': keys[pygame.K_DOWN] or keys[pygame.K_s] or stick_down or dpad[1],
        'menu_left': keys[pygame.K_LEFT] or keys[pygame.K_a] or stick_left or dpad[2],
        'menu_right': keys[pygame.K_RIGHT] or keys[pygame.K_d] or stick_right or dpad[3],
        
        # Special keys (keep keyboard only)
        'f11': keys[pygame.K_F11],
        'debug_e': keys[pygame.K_e],
        'z': keys[pygame.K_z]  # Alternative cancel
    }
    
    return unified_input

def is_controller_button_just_pressed(event, button_name):
    """Check if controller button was just pressed (for events)"""
    # If keys are disabled during transitions, block all controller button events
    if keys_disabled:
        return False
        
    if event.type == pygame.JOYBUTTONDOWN:
        button_map = {
            'x': 0, 'circle': 1, 'square': 2, 'triangle': 3,
            'l1': 4, 'r1': 5, 'l2': 6, 'r2': 7,
            'share': 8, 'options': 9, 'l3': 10, 'r3': 11,
            'ps': 12, 'touchpad': 13
        }
        return event.button == button_map.get(button_name, -1)
    return False

def is_controller_hat_just_moved(event, direction):
    """Check if controller D-pad was just moved in direction"""
    # If keys are disabled during transitions, block all controller D-pad events
    if keys_disabled:
        return False
        
    if event.type == pygame.JOYHATMOTION and event.hat == 0:
        if direction == 'up' and event.value[1] == 1:
            return True
        elif direction == 'down' and event.value[1] == -1:
            return True
        elif direction == 'left' and event.value[0] == -1:
            return True
        elif direction == 'right' and event.value[0] == 1:
            return True
    return False


# --- Map transition timer system ---
transition_timer = 0.0
transition_duration = 500.0  # Reduced to just 500ms for basic transition
is_transitioning = False

# --- Key unbinding system for transitions ---
stored_key_states = {}
keys_disabled = False

def disable_keys():
    """Store current key states and disable key processing"""
    global stored_key_states, keys_disabled
    stored_key_states = pygame.key.get_pressed().copy() if hasattr(pygame.key.get_pressed(), 'copy') else dict(enumerate(pygame.key.get_pressed()))
    keys_disabled = True
    # Clear any pending key events
    pygame.event.clear()
    print("[DEBUG] Keys disabled and states stored for transition")

def enable_keys():
    """Restore key processing and clear stored states"""
    global stored_key_states, keys_disabled
    stored_key_states = {}
    keys_disabled = False
    # Clear any accumulated events during disabled period
    pygame.event.clear()
    print("[DEBUG] Keys enabled and stored states cleared")

def get_safe_keys():
    """Get key states, returning empty state if keys are disabled"""
    if keys_disabled:
        # Return an object that behaves like pygame.key.get_pressed() but always returns False
        class DisabledKeys:
            def __getitem__(self, key):
                return False
        return DisabledKeys()
    else:
        return pygame.key.get_pressed()

# --- Object interaction logic: run_corpse_scripts ---
def run_corpse_scripts(obj):
    obj_name = getattr(obj, 'name', None)
    norm_name = obj_name.strip().lower() if obj_name else None
    # Try to get script from ENEMIES_DATA (from Enemies_List)
    enemy_data = None
    if hasattr(obj, 'enemy_id'):
        enemy_data = ENEMIES_DATA.get(obj.enemy_id)
    elif norm_name:
        enemy_data = ENEMIES_DATA.get(norm_name)
    script = None
    if enemy_data and 'script' in enemy_data:
        script = enemy_data['script']
    else:
        # Fallback to PROMPT_SCRIPTS in map config
        prompt_scripts = getattr(map_config.Config_Data, 'PROMPT_SCRIPTS', {})
        if norm_name in prompt_scripts:
            script = prompt_scripts[norm_name]
    if script:
        if isinstance(script, dict):
            messages = script.get('messages', [])
            actions = script.get('actions', [])
            # If actions is a list of actions, match to messages by index
            if isinstance(messages, list) and isinstance(actions, list) and len(actions) == len(messages):
                prompt_interaction.start(messages, actions)
            else:
                # If actions not matched by index, just show messages
                prompt_interaction.start(messages)
            return True
        elif isinstance(script, list):
            prompt_interaction.start(script)
            return True
    # Fallback: show default prompt message if no script
    if getattr(obj, 'is_interactable', False) and hasattr(obj, 'prompt_message'):
        message_display.show_message(obj.prompt_message, 3000)
        return True
    return False

# --- Object interaction logic: run_object_script---
def run_object_script(obj):
    # Global interaction cooldown to prevent rapid multiple calls
    global last_object_interaction_time
    current_time = pygame.time.get_ticks()
    interaction_cooldown = 200  # 200ms cooldown between any object interactions
    
    if current_time - last_object_interaction_time < interaction_cooldown:
        print(f"[SCRIPT] Global interaction cooldown active, ignoring")
        return True  # Return True to prevent fallback behavior
    
    obj_name = getattr(obj, 'name', None)
    norm_name = obj_name.strip().lower() if obj_name else None
    prompt_scripts = getattr(map_config.Config_Data, 'PROMPT_SCRIPTS', {})
    print(f"[DEBUG] run_object_script: norm_name='{norm_name}', PROMPT_SCRIPTS keys={list(prompt_scripts.keys())}")
    if norm_name in prompt_scripts:
        # Update global interaction time
        last_object_interaction_time = current_time
        
        script = prompt_scripts[norm_name]
        print(f"[DEBUG] Found script for '{norm_name}': {repr(script)} (type: {type(script)})")
        
        # Check if obj is a sprite (has rect attribute) or TMX object
        is_sprite = hasattr(obj, 'rect')
        
        if isinstance(script, dict):
            messages = script.get('messages', [])
            actions = script.get('actions', [])
            
            # If no messages but actions exist, create default messages
            if not messages and actions:
                messages = ["..."] * len(actions)  # Create placeholder messages for each action
                print(f"[DEBUG] No messages found, created {len(messages)} placeholder messages for {len(actions)} actions")
            
            # If actions is a list of actions, match to messages by index
            if isinstance(messages, list) and isinstance(actions, list) and len(actions) == len(messages):
                if is_sprite:
                    prompt_interaction.start(messages, actions, None, obj)  # sprite as 4th parameter
                else:
                    prompt_interaction.start(messages, actions, obj)  # TMX object as 3rd parameter
            else:
                # If actions not matched by index, just show messages
                if is_sprite:
                    prompt_interaction.start(messages, None, None, obj)  # sprite as 4th parameter
                else:
                    prompt_interaction.start(messages, obj=obj)  # TMX object
            return True
        elif 'messages' in script:
            if is_sprite:
                prompt_interaction.start(script['messages'], None, None, obj)  # sprite as 4th parameter
            else:
                prompt_interaction.start(script['messages'], obj=obj)  # TMX object
            return True
    print(f"[DEBUG] run_object_script called for object: {obj_name if obj_name else 'Unknown'}")
    return False

# --- PlayerStats class (needed for player and menu) ---
class PlayerStats:
    # Dynamic HP distribution properties that scale with total_hp
    @property
    def max_head_hp(self):
        return int(self.total_hp * self._hp_ratios["head"] / 200)
    
    @property
    def max_body_hp(self):
        return int(self.total_hp * self._hp_ratios["body"] / 200)
    
    @property
    def max_left_arm_hp(self):
        return int(self.total_hp * self._hp_ratios["left_arm"] / 200)
    
    @property
    def max_right_arm_hp(self):
        return int(self.total_hp * self._hp_ratios["right_arm"] / 200)
    
    @property
    def max_left_leg_hp(self):
        return int(self.total_hp * self._hp_ratios["left_leg"] / 200)
    
    @property
    def max_right_leg_hp(self):
        return int(self.total_hp * self._hp_ratios["right_leg"] / 200)
    
    @property 
    def max_extral_limbs_hp(self):
        if self.has_extra_limbs and "extra_limbs" in self._hp_ratios:
            return int(self.total_hp * self._hp_ratios["extra_limbs"] / 200)
        return 0

    def _calculate_max_hp_from_parts(self):
        """Calculate max_hp as sum of all body parts (for compatibility)"""
        total = (
            self.max_body_hp +
            self.max_head_hp +
            self.max_left_arm_hp +
            self.max_right_arm_hp +
            self.max_left_leg_hp +
            self.max_right_leg_hp +
            self.max_extral_limbs_hp
        )
        return total

    def __init__(self, name, gif_path, sprite_path, has_extra_limbs, max_extral_limbs_hp,
                level, evo_points_hp, evo_points_regen, evo_points_stamina, evo_points_reserve,
                evo_points_strength, evo_points_dexterity, evo_points_special, evo_points_speed, exp):
        
        self.ability_points = 0
        self.abilities = [] 
        self.name = name
        self.gif_path = gif_path
        self.sprite_path = sprite_path
        
        # Extract species from PLAYER_CHARACTER_DATA
        self.species = PLAYER_CHARACTER_DATA.get('species', 'Unknown')

        # --- Evolution stats ---
        self.level = level
        self.exp = exp
        self.evo_points = level * 5  # Example: 5 points per level
        self.move_slots = 5 + min(level, 5)
        self.evo_points_hp = evo_points_hp
        self.evo_points_regen = evo_points_regen
        self.evo_points_stamina = evo_points_stamina
        self.evo_points_reserve = evo_points_reserve
        self.evo_points_strength = evo_points_strength
        self.evo_points_dexterity = evo_points_dexterity
        self.evo_points_special = evo_points_special
        self.evo_points_speed = evo_points_speed

    # --- Experience points ---
    # Place all stat logic back in the constructor
        # --- Experience points ---
        self.required_exp = 20 + (2 ** self.level)

        # --- Base stats ---
        # --- Base stat values and multipliers ---
        self.base_speed = 10
        self.base_special = 10
        self.base_dexterity = 10
        self.base_strength = 10
        self.base_stamina = 10
        self.base_regen = 20
        self.base_reserve = 50
        self.base_hp = 200

        # Multipliers for each stat
        self.multiplier_speed = 1
        self.multiplier_special = 2
        self.multiplier_dexterity = 2
        self.multiplier_strength = 2
        self.multiplier_stamina = 2
        self.multiplier_regen = 5
        self.multiplier_reserve = 10
        self.multiplier_hp = 20

        # Calculate stats using base + (evo_points * multiplier)
        self.speed = self.base_speed + (self.evo_points_speed * self.multiplier_speed)
        self.special = self.base_special + (self.evo_points_special * self.multiplier_special)
        self.dexterity = self.base_dexterity + (self.evo_points_dexterity * self.multiplier_dexterity)
        self.strength = self.base_strength + (self.evo_points_strength * self.multiplier_strength)
        self.max_stamina = self.base_stamina + (self.evo_points_stamina * self.multiplier_stamina)
        self.stamina = self.max_stamina  # Ensure stamina is initialized
        self.max_regen = self.base_regen + (self.evo_points_regen * self.multiplier_regen)
        self.max_reserve = self.base_reserve + (self.evo_points_reserve * self.multiplier_reserve)
        self.total_hp = self.base_hp + (self.evo_points_hp * self.multiplier_hp)

        # Current regeneration and reserve start at max
        self.regen = self.max_regen
        self.reserve = self.max_reserve
        self.stamina = self.max_stamina  # Current stamina starts at max

        # Store species configuration for HP distribution
        try:
            self._species_config = get_species_config(self.species)
            self._hp_ratios = get_hp_ratios(self.species)
            self.has_extra_limbs = self._species_config['body_parts'].get('has_extra_limbs', has_extra_limbs)
        except (KeyError, ImportError) as e:
            # Fallback to default ratios if Species_Config fails
            print(f"Warning: Species_Config error for {self.species}, using default HP distribution: {e}")
            self._species_config = None
            self._hp_ratios = {
                "head": 30, "body": 100, "left_arm": 15, "right_arm": 15,
                "left_leg": 20, "right_leg": 20, "extra_limbs": 0
            }
            self.has_extra_limbs = has_extra_limbs
            
        # Dynamically set max_hp as the sum of all body parts HP, treating body as a part
        self.max_hp = self._calculate_max_hp_from_parts()

        # Current HP for each part - initialize to max values
        self.body_hp = self.max_body_hp
        self.head_hp = self.max_head_hp
        self.left_arm_hp = self.max_left_arm_hp
        self.right_arm_hp = self.max_right_arm_hp
        self.left_leg_hp = self.max_left_leg_hp
        self.right_leg_hp = self.max_right_leg_hp
        self.extral_limbs_hp = self.max_extral_limbs_hp if self.has_extra_limbs else 0


        # Current HP is always calculated as the sum of all current part HPs, including body
        def calc_hp(self):
            total = (
                self.body_hp +
                self.head_hp +
                self.left_arm_hp +
                self.right_arm_hp +
                self.left_leg_hp +
                self.right_leg_hp
            )
            if self.has_extra_limbs:
                total += self.extral_limbs_hp
            return min(total, self.max_hp)
        self.calc_hp = calc_hp.__get__(self)
        self.hp = self.calc_hp()

        # Evo points remaining is always recalculated like HP
        def calc_evo_points_remaining(self):
            spent = (
                self.evo_points_hp + self.evo_points_regen + self.evo_points_stamina +
                self.evo_points_reserve + self.evo_points_strength + self.evo_points_dexterity +
                self.evo_points_special + self.evo_points_speed
            )
            return self.evo_points - spent
        self.calc_evo_points_remaining = calc_evo_points_remaining.__get__(self)
        self.evo_points_remaining = self.calc_evo_points_remaining()

        def update_max_hp(self):
            self.max_hp = (
            self.max_body_hp +
            self.max_head_hp +
            self.max_left_arm_hp +
            self.max_right_arm_hp +
            self.max_left_leg_hp +
            self.max_right_leg_hp +
            (self.max_extral_limbs_hp if self.has_extra_limbs else 0)
        )
        self.update_max_hp = update_max_hp.__get__(self)

        def update_main_stats(self):
            self.speed = self.base_speed + (self.evo_points_speed * self.multiplier_speed)
            self.special = self.base_special + (self.evo_points_special * self.multiplier_special)
            self.dexterity = self.base_dexterity + (self.evo_points_dexterity * self.multiplier_dexterity)
            self.strength = self.base_strength + (self.evo_points_strength * self.multiplier_strength)
            self.max_stamina = self.base_stamina + (self.evo_points_stamina * self.multiplier_stamina)
            self.max_regen = self.base_regen + (self.evo_points_regen * self.multiplier_regen)
            self.max_reserve = self.base_reserve + (self.evo_points_reserve * self.multiplier_reserve)
            self.total_hp = self.base_hp + (self.evo_points_hp * self.multiplier_hp)
            # max_*_hp properties are now calculated dynamically from total_hp
            self.hp = self.calc_hp()
        self.update_main_stats = update_main_stats.__get__(self)

        # --- Memory Skills Initialization ---
        self.equipped_memory_skills = []
        self.memory_skill_state = {}
        self.available_memory_points = 10
        
        # Load memory skills data if available
        global LOADED_MEMORY_SKILLS_DATA
        if LOADED_MEMORY_SKILLS_DATA:
            print(f"[PlayerStats] Loading memory skills from save data")
            self.equipped_memory_skills = list(LOADED_MEMORY_SKILLS_DATA.get("equipped", []))
            self.memory_skill_state = dict(LOADED_MEMORY_SKILLS_DATA.get("skill_states", {}))
            self.available_memory_points = LOADED_MEMORY_SKILLS_DATA.get("available_memory_points", 10)
            print(f"[PlayerStats] Loaded equipped memory skills: {self.equipped_memory_skills}")
        else:
            print(f"[PlayerStats] No memory skills save data found, using defaults")

    def update_evo_points_remaining(self):
        self.evo_points_remaining = self.calc_evo_points_remaining()

    def take_damage(self, amount, part=None):
        # Apply damage to the specified body part
        if part == 'head':
            self.head_hp = max(0, self.head_hp - amount)
        elif part == 'torso' or part == 'body':
            self.body_hp = max(0, self.body_hp - amount)
        elif part == 'left_arm':
            self.left_arm_hp = max(0, self.left_arm_hp - amount)
        elif part == 'right_arm':
            self.right_arm_hp = max(0, self.right_arm_hp - amount)
        elif part == 'left_leg':
            self.left_leg_hp = max(0, self.left_leg_hp - amount)
        elif part == 'right_leg':
            self.right_leg_hp = max(0, self.right_leg_hp - amount)
        elif part == 'legs':
            leg = random.choice(['left_leg', 'right_leg'])
            if leg == 'left_leg':
                self.left_leg_hp = max(0, self.left_leg_hp - amount)
            else:
                self.right_leg_hp = max(0, self.right_leg_hp - amount)
        else:
            # Default: apply damage to total HP
            self.hp = max(0, self.hp - amount)
        # Always recalculate total HP after damage
        self.hp = self.calc_hp()
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
    def use_stamina(self, amount):
        self.stamina = max(0, self.stamina - amount)
    def regen_stamina(self, amount):
        self.stamina = min(self.max_stamina, self.stamina + amount)
    def use_reserve(self, amount):
        self.reserve = max(0, self.reserve - amount)
    def regen_reserve(self, amount):
        self.reserve = min(self.max_reserve, self.reserve + amount)
    def __repr__(self):
        return f"PlayerStats(name={self.name}, hp={self.hp}/{self.max_hp}, stamina={self.stamina}/{self.max_stamina}, regen={self.regen}/{self.max_regen}, reserve={self.reserve}/{self.max_reserve})"

def Level_Up(player):
    """
    Levels up the player if current exp >= required exp.
    Increases level by 1 and carries over excess exp for next level.
    """
    while hasattr(player, 'exp') and hasattr(player, 'required_exp') and hasattr(player, 'level'):
        if player.exp >= player.required_exp:
            prev_required_exp = player.required_exp
            player.level += 1
            player.exp -= prev_required_exp
            # Update evo points and evo_points_remaining after level up
            if hasattr(player, 'evo_points'):
                player.evo_points = player.level * 5
            if hasattr(player, 'update_evo_points_remaining'):
                player.update_evo_points_remaining()
            # Update required_exp for new level (if logic is in PlayerStats)
            if hasattr(player, 'update_required_exp'):
                player.update_required_exp()
            elif hasattr(player, 'required_exp'):
                player.required_exp = 20 + (2 ** player.level)
        else:
            break
        
def Get_Exp(player, exp_amount):
    """
    Adds exp_amount to the player's current exp value.
    Args:
        player: The player object (should have an 'exp' attribute).
        exp_amount: The amount of exp to add (int or float).
    """
    if hasattr(player, 'exp'):
        player.exp += exp_amount
        # Play level up sound when exp is gained
        if 'level_up_sound' in globals() and level_up_sound:
            try:
                level_up_sound.play()
            except Exception as e:
                print(f"[ERROR] Could not play level up sound: {e}")
    else:
        raise AttributeError("Player object has no 'exp' attribute")


def load_character_frames(image_path):
    """
    Loads a 4x4 spritesheet and returns a dict of frames for directions.
    Args:
        image_path (str): Path to the PNG spritesheet.
    Returns:
        dict: {direction: [frame0, frame1, frame2, frame3]}
    """
    character_spritesheet = pygame.image.load(image_path).convert_alpha()
    sprite_width = character_spritesheet.get_width() // 4
    sprite_height = character_spritesheet.get_height() // 4
    frames = {}
    start_frames = {}
    directions = ['down', 'right', 'up', 'left']
    for row, direction in enumerate(directions):
        frames[direction] = []
        for col in range(4):
            frame_rect = pygame.Rect(col * sprite_width, row * sprite_height, sprite_width, sprite_height)
            frame = character_spritesheet.subsurface(frame_rect)
            # For 'down' direction, shift the frame 13px higher on a new surface
            if direction == 'down':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, -13))
                frames[direction].append(shifted_surface)
            # For 'right' direction, shift the frame 7px up
            elif direction == 'right':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, -7))
                frames[direction].append(shifted_surface)
            # For 'up' direction, shift the frame 1px left and 3px down
            elif direction == 'up':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (-1, 3))
                frames[direction].append(shifted_surface)
            # For 'left' direction, shift the frame 9px down
            elif direction == 'left':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, 9))
                frames[direction].append(shifted_surface)
            else:
                frames[direction].append(frame)
        # Animation should start from frame 1 (second frame) when moving
        start_frames[direction] = 1
    return {'frames': frames, 'start_frames': start_frames}

def is_player_on_bone_grass(player, tmx_data):
    """
    Return (on_bone_grass, is_moving, is_running):
    - on_bone_grass: True if the player's feet are inside a tile from the 'Bone_Grass' layer.
    - is_moving: True if the player is moving.
    - is_running: True if the player is running (sprinting).
    """
    # Circle: center = player geometric center, radius = 0.4 * tilewidth
    player_center = (player.rect.centerx, player.rect.centery + tmx_data.tileheight + 7)
    radius = tmx_data.tilewidth / 1.7

    # Check only the Bone_Grass layer
    on_bone_grass = False
    for layer in tmx_data.layers:
        if hasattr(layer, 'data') and hasattr(layer, 'name') and "Bone_Grass" in layer.name:
            for y, row in enumerate(layer.data):
                for x, tile in enumerate(row):
                    if tile:  # If there's a tile at this position in the Bone_Grass layer
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

    # Determine movement and running state
    is_moving = getattr(player, 'is_moving', False)
    # Sprinting: shift pressed and not locked and stamina > 0
    is_running = False
    return on_bone_grass, is_moving, is_running


# --- Bone grass sound rate limiting ---
last_bone_grass_sound_time = 0
last_object_interaction_time = 0  # Global cooldown for object interactions
# ...existing code...

# --- Initialize mixer before loading any sounds ---
try:
    pygame.mixer.init()
    print("Pygame mixer initialized.")
except Exception as e:
    print(f"[ERROR] Could not initialize pygame mixer: {e}")

# --- Sound Effects Loading using Global SFX System ---
try:
    pygame.mixer.init()
    print("Pygame mixer initialized.")
    # Load global SFX volume
    Global_SFX.load_global_sfx_volume()
except Exception as e:
    print(f"[ERROR] Could not initialize pygame mixer: {e}")

# --- Sound Effect for Bone Grass Damage ---
bone_grass_sound = Global_SFX.load_sound_with_global_volume(
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\knife-stab-pull-7005.mp3", 0.2)
if bone_grass_sound:
    print("Loaded bone grass damage sound with global SFX volume.")
else:
    print("Could not load bone grass sound.")

# --- Load level up sound effect ---
level_up_sound = Global_SFX.load_sound_with_global_volume(
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\cute-level-up-3-189853.mp3", 0.7)
if level_up_sound:
    print("Loaded level up sound with global SFX volume.")
else:
    print("[ERROR] Could not load level up sound.")


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Corpse(pygame.sprite.Sprite):
    def __init__(self, pos, image, name):
        super().__init__(object_group)
        # --- Create a bright placeholder image for visibility ---
        tile_w, tile_h = 32, 32  # Default tile size
        width, height = tile_w * 2, tile_h
        bright_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        bright_surface.fill((255, 0, 0))  # Bright red
        pygame.draw.rect(bright_surface, (255, 255, 0), (2, 2, width-4, height-4), 4)  # Yellow border
        pygame.draw.line(bright_surface, (255,255,255), (0,0), (width-1,height-1), 3)
        pygame.draw.line(bright_surface, (255,255,255), (width-1,0), (0,height-1), 3)
        self.image = image if image is not None else bright_surface
        
        # Position corpse at the base of the enemy, slightly to the right
        # Instead of centering on pos, place it at the bottom and offset right
        self.rect = self.image.get_rect()
        # Offset slightly to the right (16 pixels) and position at base
        corpse_x = pos[0] + 10  # 16 pixels to the right
        corpse_y = pos[1] + 22 # Keep same Y as enemy center
        # Position the bottom of the corpse at the enemy's center Y
        self.rect.midbottom = (corpse_x, corpse_y)
        
        self.name = f"{name}_corpse"
        self.is_interactable = True
        self.prompt_message = f"You see the corpse of {name}."
        self.depth_y = self.rect.bottom
        self.corpse_interacted = False  # Track if corpse has been interacted with
        print(f"[DEBUG] Corpse created: {self.name} at {self.rect.topleft}, size: {width}x{height}")
        print(f"[DEBUG] Corpse created: {self.name} at {self.rect.topleft}")

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, image_path):
        super().__init__(groups)
        frames_data = load_character_frames(image_path)
        self.frames = frames_data['frames']
        self.start_frames = frames_data['start_frames']
        self.direction = 'down'
        self.frame_index = 0
        self.animation_speed = 0.16  # Default walking animation speed
        self.animation_timer = 0
        self.is_moving = False
        self.pingpong_forward = True
        self.image = self.frames[self.direction][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        self.speed = 5
        self.pos = pygame.math.Vector2(pos)
        self.stamina_regen_timer = 0.0
        self.stamina_drain_timer = 0.0
        self.sprint_locked = False

    def update(self, keys, collision_tiles, tmx_data, dt=16):
        # --- Check if transitioning - block all movement ---
        global is_transitioning
        if is_transitioning:
            return
        
        # Get unified input (keyboard + controller)
        unified_input = get_unified_input()
        
        self.is_moving = False
        new_pos = self.pos.copy()
        
        # Check for shift/run input from keyboard or controller
        shift_pressed = unified_input['run_info']
        
        # --- Leg injury sprint lock ---
        legs_hp = player_stats.left_leg_hp + player_stats.right_leg_hp
        legs_max_hp = player_stats.max_left_leg_hp + player_stats.max_right_leg_hp
        legs_usable = legs_hp >= (legs_max_hp / 3)
        
        # If legs are too injured, lock sprint and show message
        if not legs_usable:
            self.sprint_locked = True
            # Show message if shift is pressed and message not already visible
            if shift_pressed and not message_display.is_visible:
                message_display.show_message(f"{player_stats.name}'s legs are too injured to run", 2500)
        
        can_sprint = not self.sprint_locked and player_stats.stamina > 0
        sprinting = shift_pressed and can_sprint
        move_speed = (self.speed * 1.5 if sprinting else self.speed) * (dt / 1000.0)
        
        # Movement with unified input (keyboard + controller)
        if unified_input['left']:
            new_pos.x -= move_speed
            self.direction = 'left'
            self.is_moving = True
        elif unified_input['right']:
            new_pos.x += move_speed
            self.direction = 'right'
            self.is_moving = True
        elif unified_input['up']:
            new_pos.y -= move_speed
            self.direction = 'up'
            self.is_moving = True
        elif unified_input['down']:
            new_pos.y += move_speed
            self.direction = 'down'
            self.is_moving = True
        if sprinting and self.is_moving:
            self.stamina_regen_timer = 0.0
            self.stamina_drain_timer += dt / 1000.0
            if self.stamina_drain_timer >= 0.001:
                player_stats.stamina = max(0, player_stats.stamina - 1)
                self.stamina_drain_timer -= 0.5
            if player_stats.stamina <= 0:
                self.sprint_locked = True
        else:
            self.stamina_drain_timer = 0.0
            if player_stats.stamina < player_stats.max_stamina:
                self.stamina_regen_timer += dt / 1000.0
                if self.stamina_regen_timer >= 1.0:
                    player_stats.stamina = min(player_stats.max_stamina, player_stats.stamina + 1)
                    self.stamina_regen_timer -= 1.0
            if self.sprint_locked and player_stats.stamina >= player_stats.max_stamina / 2 and legs_usable:
                self.sprint_locked = False
        if self.is_moving:
            current_image = self.frames[self.direction][self.frame_index]
            hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
                new_pos.x - current_image.get_width()//2,
                new_pos.y - current_image.get_height()//2,
                current_image, tmx_data)
            if not check_collision(hitbox_x, hitbox_y, hitbox_width, hitbox_height, collision_tiles, tmx_data):
                self.pos = new_pos
            else:
                self.is_moving = False
        # Animation logic for 4 frames per direction
        # --- Framerate-independent animation ---
        dt_seconds = dt / 1000.0
        # Adjust animation speed based on running or walking
        if sprinting and self.is_moving:
            self.animation_speed = 0.21
        else:
            self.animation_speed = 0.16
        animation_speed_dt = self.animation_speed * dt_seconds * 60 * 0.7  # 30% slower
        if self.is_moving:
            if self.frame_index == 0:
                self.frame_index = self.start_frames[self.direction]
                self.pingpong_forward = True
            self.animation_timer += animation_speed_dt
            # Increase threshold for slower animation (was 1.0)
            if self.animation_timer >= 1.5:
                if self.pingpong_forward:
                    self.frame_index += 1
                    if self.frame_index == 4:
                        self.frame_index = 2
                        self.pingpong_forward = False
                else:
                    self.frame_index -= 1
                    if self.frame_index == 0:
                        self.frame_index = 2
                        self.pingpong_forward = True
                self.animation_timer = 0
        else:
            self.frame_index = 0
            self.animation_timer = 0
            self.pingpong_forward = True
        self.image = self.frames[self.direction][self.frame_index]
        self.rect.center = self.pos

def handle_enemy_death(npc, object_group):
    """Handle enemy death after combat victory"""
    try:
        print(f"[Combat] Starting enemy death handling for {getattr(npc, 'name', 'unknown_enemy')}")
        
        # Apply damage to player as in mockup (for compatibility)
        for part in ['head', 'torso', 'left_arm', 'right_arm', 'left_leg', 'right_leg']:
            if hasattr(player_stats, 'take_damage'):
                try:
                    player_stats.take_damage(5, part=part)
                except Exception as e:
                    print(f"[Combat] Error applying damage to {part}: {e}")
        
        # Remove enemy from the map
        npc.kill()

        # --- Record enemy death in world state (copied from Combat_Mockup) ---
        spawn_x = getattr(npc, 'spawn_x', 0)
        spawn_y = getattr(npc, 'spawn_y', 0)
        death_x = getattr(npc, 'pos', None).x if hasattr(getattr(npc, 'pos', None), 'x') else getattr(npc, 'rect', None).x if hasattr(npc, 'rect') else 0
        death_y = getattr(npc, 'pos', None).y if hasattr(getattr(npc, 'pos', None), 'y') else getattr(npc, 'rect', None).y if hasattr(npc, 'rect') else 0
        
        print(f"[Combat] Enemy coords: spawn=({spawn_x}, {spawn_y}), death=({death_x}, {death_y})")
        
        # Ensure map is in world state
        if current_map_name not in WORLD_STATE["maps"]:
            WORLD_STATE["maps"][current_map_name] = {"killed_enemies": [], "killed_objects": []}
            print(f"[Combat] Created map entry for '{current_map_name}'")
        
        # Add killed enemy record
        enemy_record = {
            "name": getattr(npc, 'name', 'unknown_enemy'),
            "spawn_x": spawn_x,
            "spawn_y": spawn_y,
            "death_x": death_x,
            "death_y": death_y,
            "interactions": 0
        }
        WORLD_STATE["maps"][current_map_name]["killed_enemies"].append(enemy_record)
        print(f"[Combat] Recorded enemy death: {enemy_record}")

        # --- Create corpse ---
        death_image_path = getattr(npc, "death_image_path", None)
        death_image = None
        if death_image_path:
            try:
                death_image = pygame.image.load(death_image_path).convert_alpha()
            except Exception as e:
                print(f"[Combat] Could not load death image: {e}")
        if death_image is None:
            death_image = pygame.Surface((32,32), pygame.SRCALPHA)
            death_image.fill((80, 80, 80, 180))  # Gray fallback

        # Position fallback
        pos = None
        if hasattr(npc, 'pos') and hasattr(npc.pos, 'x') and hasattr(npc.pos, 'y'):
            pos = (npc.pos.x, npc.pos.y)
        elif hasattr(npc, 'rect'):
            pos = (npc.rect.x, npc.rect.y)
        else:
            pos = (0, 0)

        # Create corpse using Corpse class
        corpse_obj = Corpse(pos, death_image, getattr(npc, 'name', 'enemy'))
        print(f"[Combat] Corpse object created at {pos}.")

        # --- Add weapon proficiency experience ---
        try:
            import Player_Equipment
            if hasattr(Player_Equipment, 'player1') and Player_Equipment.player1:
                level_up = Player_Equipment.add_combat_experience(Player_Equipment.player1)
                if level_up:
                    print("🎉 [Combat] Weapon proficiency level increased after combat!")
                else:
                    print("[Combat] Added weapon proficiency experience after combat")
        except ImportError:
            print("[Combat] WARNING: Player_Equipment module not available for experience gain")

        print("[Combat] Enemy death handling completed successfully")
        
    except Exception as e:
        print(f"[Combat] Error handling enemy death: {e}")
        import traceback
        traceback.print_exc()

def show_game_over_screen():
    """Show game over screen and return to main menu"""
    print("[GameOver] Player defeated - returning to main menu...")
    
    try:
        # Create a simple game over screen
        screen = pygame.display.get_surface()
        if not screen:
            return
            
        screen.fill((0, 0, 0))
        
        # Load font for game over text
        try:
            font_large = pygame.font.Font(None, 72)
            font_medium = pygame.font.Font(None, 36)
        except:
            font_large = pygame.font.Font(None, 72)
            font_medium = pygame.font.Font(None, 36)
        
        # Game over text
        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 50))
        screen.blit(game_over_text, text_rect)
        
        # Return to menu text
        menu_text = font_medium.render("Returning to Main Menu...", True, (255, 255, 255))
        menu_rect = menu_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 50))
        screen.blit(menu_text, menu_rect)
        
        pygame.display.flip()
        pygame.time.wait(2000)  # Wait 2 seconds
        
        # Add main project directory to path
        import sys
        main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        if main_dir not in sys.path:
            sys.path.insert(0, main_dir)
        
        # Import the main menu module
        import Main_Menu
        
        # Create main menu instance reusing the same pygame display
        main_menu = Main_Menu.MainMenu()
        
        # Replace the screen object to reuse the same window
        main_menu.screen = screen
        
        # Show game over screen first
        main_menu.show_game_over_screen()
        
        # If player chose to continue, run the main menu
        if main_menu.running:
            main_menu.run()
            
    except Exception as e:
        print(f"[GameOver] Error returning to main menu: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: just exit cleanly
        pygame.quit()
        sys.exit()

def enemy_touches_player(player, object_group, player_stats_obj):
    """
    Detects if the player is within a 1 tile radius (circle) from any NPC enemy in object_group.
    Returns True if any enemy is within range, else False.
    """
    tmx_tilewidth = 32  # Replace with tmx_data.tilewidth if available
    player_center = (player.rect.centerx, player.rect.centery)
    for obj in object_group:
        if isinstance(obj, NPC):
            # Skip if this enemy is already marked for removal or dead
            if getattr(obj, 'is_dead', False) or not obj.alive():
                continue
            
            # Skip if this enemy is currently in combat to prevent double-triggering
            if getattr(obj, 'in_combat', False):
                continue
                
            enemy_center = (obj.rect.centerx, obj.rect.centery)
            dist = math.hypot(player_center[0] - enemy_center[0], player_center[1] - enemy_center[1])
            if dist <= tmx_tilewidth:  # 1 tile radius
                try:
                    print(f"[Combat] Enemy touch detected: {getattr(obj, 'name', 'Unknown')} vs Player")
                    
                    # Mark enemy as being in combat to prevent double-triggering
                    obj.in_combat = True
                    
                    # Store current overworld music state
                    overworld_music_playing = pygame.mixer.music.get_busy()
                    overworld_music_volume = pygame.mixer.music.get_volume()
                    
                    # Capture screenshot for battle background
                    print(f"[Combat] Capturing overworld screenshot...")
                    screenshot = pygame.display.get_surface().copy()
                    print(f"[Combat] Screenshot captured: {screenshot.get_size()}")
                    print(f"[Combat] Starting combat system...")
                    
                    # Update player stats to reflect current state before battle
                    print(f"[Combat] Current player stats before battle:")
                    print(f"  HP: {player_stats_obj.hp}/{player_stats_obj.max_hp}")
                    print(f"  Stamina: {player_stats_obj.stamina}/{player_stats_obj.max_stamina}")
                    print(f"  Strength: {player_stats_obj.strength}")
                    
                    # Start real combat system using the already imported CombatSystem
                    combat_result = CombatSystem.start_combat_from_overworld(player_stats_obj, obj, screenshot)
                    
                    # Handle combat result
                    if combat_result == 'player_win':
                        print(f"[Combat] Player won! Enemy defeated.")
                        # Mark enemy as actually dead after successful combat
                        obj.is_dead = True
                        obj.in_combat = False
                        handle_enemy_death(obj, object_group)
                        
                        # Immediately save the game state to prevent enemy respawn
                        try:
                            save_path = create_complete_save("immediate_enemy_kill")
                            if save_path:
                                print(f"[Combat] Immediate save after enemy kill successful: {save_path}")
                        except Exception as e:
                            print(f"[Combat] Error during immediate save after enemy kill: {e}")
                            
                    elif combat_result == 'enemy_win':
                        print(f"[Combat] Player lost! Game over.")
                        obj.in_combat = False
                        show_game_over_screen()
                        return True  # End game
                    else:
                        print(f"[Combat] Combat ended with no clear result")
                        # Reset the combat flag if combat was cancelled
                        obj.in_combat = False
                    
                    # Restore overworld state after battle
                    print(f"[Combat] Restoring overworld state...")
                    
                    # Ensure pause menu and game state are properly reset
                    if pause_menu:
                        pause_menu.visible = False
                        print(f"[Combat] Reset pause_menu.visible to False")
                    global game_paused
                    game_paused = False
                    print(f"[Combat] Reset game_paused to False")
                    
                    # Restart overworld music only if it was playing before and isn't playing now
                    if overworld_music_playing and not pygame.mixer.music.get_busy():
                        try:
                            pygame.mixer.music.load(r"C:\Users\franc\Desktop\Afterdeath_RPG\Musics\Boney Rattle.MP3")
                            pygame.mixer.music.set_volume(overworld_music_volume)
                            pygame.mixer.music.play(-1)  # Loop forever
                            print(f"[Combat] Overworld music restarted at volume {overworld_music_volume}")
                        except Exception as music_error:
                            print(f"[Combat] Failed to restart overworld music: {music_error}")
                    elif pygame.mixer.music.get_busy():
                        print(f"[Combat] Music is already playing, no restart needed")
                    
                    # Update player stats to reflect any changes from battle (exp, damage, etc.)
                    print(f"[Combat] Player stats after battle:")
                    print(f"  HP: {player_stats_obj.hp}/{player_stats_obj.max_hp}")
                    print(f"  Stamina: {player_stats_obj.stamina}/{player_stats_obj.max_stamina}")
                    print(f"  Strength: {player_stats_obj.strength}")
                        
                    print(f"[Combat] Combat completed successfully, overworld state restored")
                except Exception as e:
                    print(f"[ERROR] Real combat system failed: {e}")
                    import traceback
                    traceback.print_exc()
                    # Reset the combat flag on error
                    obj.in_combat = False
                    # Fallback to mockup system if combat fails
                    print("[Combat] Falling back to mockup system...")
                    try:
                        from Combat_Mockup import handle_combat
                        result = handle_combat(obj)
                        if result == "enemy_defeated":
                            obj.is_dead = True
                            handle_enemy_death(obj, object_group)
                    except Exception as fallback_error:
                        print(f"[ERROR] Fallback combat also failed: {fallback_error}")
                return True
    return False

def draw_hp_bar(screen, player, player_HP, player_max_HP):
    # HP bar settings
    bar_x, bar_y = 20, 8  # 12px above stamina bar
    bar_width, bar_height = 600, int(24 * 0.75)  # 3x stamina bar width
    # Background
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
    # Foreground (current HP)
    hp_ratio = player_HP / player_max_HP
    fg_width = int(bar_width * hp_ratio)
    pygame.draw.rect(screen, (200, 0, 0), (bar_x, bar_y, fg_width, bar_height))
    # Black border
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)

def draw_stamina_bar(screen, player):
    # Bar settings
    bar_x, bar_y = 20, 25
    bar_width, bar_height = 200, int(24 * 0.75)  # 18px height
    # Background
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
    # Foreground (current stamina)
    # Use player_stats for stamina values
    stamina = player_stats.stamina
    max_stamina = player_stats.max_stamina
    stamina_ratio = stamina / max_stamina if max_stamina > 0 else 0
    fg_width = int(bar_width * stamina_ratio)
    pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, fg_width, bar_height))
    # Black border
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)

def is_player_facing_object_center(player, tmx_data):
    """Return the object (no image) the player is inside and facing its center, or None if not found."""
    # Use the player's hitbox rect for interaction, not the sprite rect
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    player_hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    for obj in tmx_data.objects:
        if not hasattr(obj, 'image') or obj.image is None:
            obj_rect = pygame.Rect(obj.x, obj.y, getattr(obj, 'width', 0), getattr(obj, 'height', 0))
            if player_hitbox_rect.colliderect(obj_rect):
                # Get centers
                player_center = pygame.math.Vector2(player_hitbox_rect.center)
                object_center = pygame.math.Vector2(obj_rect.center)
                direction = getattr(player, 'direction', None)
                to_object = object_center - player_center
                # Allow some tolerance for being "close enough"
                tolerance = 40
                if to_object.length() > max(player_hitbox_rect.width, player_hitbox_rect.height) + tolerance:
                    continue
                # Facing direction check
                if direction == 'up' and to_object.y < -abs(to_object.x):
                    return obj
                if direction == 'down' and to_object.y > abs(to_object.x):
                    return obj
                if direction == 'left' and to_object.x < -abs(to_object.y):
                    return obj
                if direction == 'right' and to_object.x > abs(to_object.y):
                    return obj
    return None

# --- Utility: Handle SPACEBAR interaction for facing object center ---
def handle_spacebar_facing_check(player, tmx_data):
    """Call this when SPACEBAR is pressed. If player is facing object center, print 'OK'."""
    # Safety check: if pause menu has been visible for too long without user input, reset it
    if getattr(pause_menu, 'visible', False) and hasattr(pause_menu, 'last_interaction_time'):
        current_time = pygame.time.get_ticks()
        if current_time - pause_menu.last_interaction_time > 30000:  # 30 seconds
            print(f"[INTERACTION] SAFETY: Resetting stuck pause menu after 30 seconds")
            pause_menu.visible = False
    
    # Disable all interaction if pause menu is active
    if game_paused or getattr(pause_menu, 'visible', False):
        print(f"[INTERACTION] BLOCKED - game_paused={game_paused}, pause_menu.visible={getattr(pause_menu, 'visible', False)}")
        return

    # First check invisible TMX objects (no image)
    obj = is_player_facing_object_center(player, tmx_data)
    if obj:
        handled = run_object_script(obj)
        if handled:
            # Script was found and executed
            return
        # Even if no script was found, don't check visible sprites since we found an invisible object
        return

    # Use player's hitbox for all visible sprite interactions
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    player_hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)

    # --- Check for interactable corpse sprites in object_group ---
    # Use player's hitbox for interaction
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    player_hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    for sprite in object_group:
        if hasattr(sprite, 'is_interactable') and sprite.is_interactable and hasattr(sprite, 'name') and sprite.name.endswith('_corpse'):
            if player_hitbox_rect.colliderect(sprite.rect):
                from Enemies_List import get_enemy_data_by_name
                corpse_base_name = sprite.name[:-7] if sprite.name.endswith('_corpse') else sprite.name
                enemy_data = get_enemy_data_by_name(corpse_base_name)
                # All scripts and text must be defined in ENEMIES_DATA
                script = None
                repeat_script = None
                study_limit = None
                limit_script = None
                if enemy_data:
                    script = enemy_data.get('script', None)
                    repeat_script = script.get('repeat', None) if script else None
                    study_limit = enemy_data.get('study_limit', None)
                    limit_script = enemy_data.get('limit_script', None)
                
                # NEW CORPSE INTERACTION SYSTEM
                # Find the killed enemy record for this corpse to get/set interaction count
                current_map = globals().get('current_map_name', 'unknown_map')
                killed_enemies_list = WORLD_STATE["maps"].get(current_map, {}).get("killed_enemies", [])
                
                # Find this specific corpse's enemy record
                corpse_enemy_record = None
                for enemy_record in killed_enemies_list:
                    # Match by death coordinates (more reliable than spawn coordinates)
                    death_x = int(enemy_record.get('death_x', 0))
                    death_y = int(enemy_record.get('death_y', 0))
                    corpse_x = int(sprite.rect.centerx)
                    corpse_y = int(sprite.rect.centery)
                    
                    # Allow some tolerance for position matching (±25 pixels)
                    if (abs(death_x - corpse_x) <= 25 and abs(death_y - corpse_y) <= 25 and 
                        enemy_record.get('name') == corpse_base_name):
                        corpse_enemy_record = enemy_record
                        break
                
                if corpse_enemy_record is None:
                    print(f"[INTERACT] WARNING: Could not find enemy record for corpse {corpse_base_name} at {sprite.rect.center}")
                    message_display.show_message("This corpse cannot be studied.", 3500)
                    sprite.corpse_interacted = True
                    return
                
                # Get current interaction count for this specific corpse
                corpse_interactions = corpse_enemy_record.get('interactions', 0)
                
                # Get enemy type interaction count for limit system
                enemy_type = corpse_base_name
                enemy_type_interactions = enemy_type_interaction_counter.get(enemy_type, 0)
                
                # Determine which dialogue to show
                if corpse_interactions == 0:
                    # FIRST interaction with this specific corpse - show main script
                    corpse_enemy_record['interactions'] = 1
                    enemy_type_interaction_counter[enemy_type] = enemy_type_interactions + 1
                    
                    if script:
                        messages = script.get('messages', [])
                        actions = script.get('actions', [None]*len(messages))
                        prompt_interaction.start(messages, actions)
                        print(f"[INTERACT] Corpse FIRST interaction: {enemy_type} at {sprite.rect.topleft} (corpse: 1, type: {enemy_type_interaction_counter[enemy_type]})")
                    else:
                        message_display.show_message(sprite.prompt_message, 3500)
                        print(f"[INTERACT] Corpse FIRST interaction: {enemy_type} at {sprite.rect.topleft} (corpse: 1, type: {enemy_type_interaction_counter[enemy_type]})")
                
                elif study_limit is not None and enemy_type_interactions >= study_limit and limit_script:
                    # LIMIT reached for this enemy type - show limit script, no increment
                    if limit_script:
                        messages = limit_script.get('messages', ["You have already seen many bodies subjected to the same surgical procedures.", "Further study yields no new insights."])
                        actions = limit_script.get('actions', [None]*len(messages))
                        prompt_interaction.start(messages, actions)
                        print(f"[INTERACT] Enemy type LIMIT reached: {enemy_type} (type interactions: {enemy_type_interactions}/{study_limit})")
                    else:
                        message_display.show_message("You have already mastered the study of this enemy type.", 3500)
                        print(f"[INTERACT] Enemy type LIMIT reached: {enemy_type} (type interactions: {enemy_type_interactions}/{study_limit})")
                
                else:
                    # REPEAT interaction with this specific corpse - show repeat script
                    corpse_enemy_record['interactions'] = corpse_interactions + 1
                    
                    if repeat_script:
                        messages = repeat_script.get('messages', ["You have already studied this body.", "There is nothing more to learn from it."])
                        actions = repeat_script.get('actions', [None]*len(messages))
                        prompt_interaction.start(messages, actions)
                        print(f"[INTERACT] Corpse REPEAT interaction: {enemy_type} at {sprite.rect.topleft} (corpse: {corpse_enemy_record['interactions']}, type: {enemy_type_interactions})")
                    else:
                        message_display.show_message("You have already studied this body.", 3500)
                        print(f"[INTERACT] Corpse REPEAT interaction: {enemy_type} at {sprite.rect.topleft} (corpse: {corpse_enemy_record['interactions']}, type: {enemy_type_interactions})")
                
                # Mark this corpse as interacted with in this session (prevents multiple interactions per session)
                sprite.corpse_interacted = True

    # --- Check for other interactable visible objects in object_group ---
    for sprite in object_group:
        # Skip corpses (already handled above) and NPCs (enemies)
        if (hasattr(sprite, 'name') and sprite.name and sprite.name.endswith('_corpse')) or isinstance(sprite, NPC):
            continue
        
        if player_hitbox_rect.colliderect(sprite.rect):
            # Only try to run object script if sprite has a name
            if hasattr(sprite, 'name') and sprite.name:
                handled = run_object_script(sprite)
                if handled:
                    print(f"[INTERACT] Visible object script started: {sprite.name} at {sprite.rect.topleft}")
                    return  # Exit immediately after handling an object to prevent multiple interactions
                # If no script found, don't show any interaction message - object is not interactable
            # Objects without names or scripts are not interactable

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.zoom_factor = 2 # 2x zoom like in V02
        
        # Smooth camera movement variables
        self.target_x = 0.0
        self.target_y = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.lerp_speed = 0.08  # Camera smoothness (0.01 = very smooth, 0.2 = fast)
        self.deadzone_radius = 8  # Pixels of deadzone around center before camera moves

    def apply(self, entity):
        # Apply camera offset and zoom using smooth camera position
        x = (entity.rect.x - self.current_x) * self.zoom_factor
        y = (entity.rect.y - self.current_y) * self.zoom_factor
        return pygame.Rect(x, y, entity.rect.width * self.zoom_factor, entity.rect.height * self.zoom_factor)

    def apply_rect(self, rect):
        # Apply camera offset and zoom to a rect using smooth camera position
        x = (rect.x - self.current_x) * self.zoom_factor
        y = (rect.y - self.current_y) * self.zoom_factor
        return pygame.Rect(x, y, rect.width * self.zoom_factor, rect.height * self.zoom_factor)

    def update(self, target, dt=16):
        # Calculate desired camera position (center on target accounting for zoom)
        desired_x = target.x - (self.width / self.zoom_factor) / 2
        desired_y = target.y - (self.height / self.zoom_factor) / 2
        
        # Calculate current camera center
        center_x = self.current_x + (self.width / self.zoom_factor) / 2
        center_y = self.current_y + (self.height / self.zoom_factor) / 2
        
        # Calculate distance between camera center and target
        distance_from_center = math.hypot(target.x - center_x, target.y - center_y)
        
        # If distance is more than 5 tiles (160 pixels), teleport camera instantly
        tile_size = 32  # Default tile size
        teleport_distance = 5 * tile_size  # 5 tiles = 160 pixels
        
        if distance_from_center > teleport_distance:
            # Instantly teleport camera to character
            self.current_x = desired_x
            self.current_y = desired_y
            self.target_x = desired_x
            self.target_y = desired_y
        else:
            # Apply deadzone - only move camera if target is outside deadzone
            if distance_from_center > self.deadzone_radius:
                # Update target position
                self.target_x = desired_x
                self.target_y = desired_y
            
            # Smooth interpolation towards target using delta time
            dt_factor = min(dt / 16.0, 2.0)  # Normalize to 60fps, cap at 2x for stability
            lerp_amount = 1.0 - pow(1.0 - self.lerp_speed, dt_factor)
            
            self.current_x += (self.target_x - self.current_x) * lerp_amount
            self.current_y += (self.target_y - self.current_y) * lerp_amount
        
        # Limit scrolling to map size (accounting for zoom)
        max_x = self.map_width - (self.width / self.zoom_factor)
        max_y = self.map_height - (self.height / self.zoom_factor)
        
        self.current_x = max(0, min(self.current_x, max_x))
        self.current_y = max(0, min(self.current_y, max_y))
        
        # Update legacy camera rect for backward compatibility
        self.camera = pygame.Rect(-round(self.current_x), -round(self.current_y), self.width, self.height)

    def set_map_size(self, map_width, map_height):
        self.map_width = map_width
        self.map_height = map_height
        
    def set_position(self, x, y):
        """Instantly set camera position (useful for map transitions)"""
        # Ensure coordinates are within map bounds
        max_x = self.map_width - (self.width / self.zoom_factor)
        max_y = self.map_height - (self.height / self.zoom_factor)
        
        self.current_x = max(0, min(x, max_x))
        self.current_y = max(0, min(y, max_y))
        self.target_x = self.current_x
        self.target_y = self.current_y
        self.camera = pygame.Rect(-round(self.current_x), -round(self.current_y), self.width, self.height)

class MessageDisplay:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
        try:
            self.font = pygame.font.Font(font_path, 36)
        except Exception as e:
            print(f"[MessageDisplay] Could not load Pixellari.ttf: {e}")
            self.font = pygame.font.Font(None, 36)
            print("Desired Font not found, using default font")

        self.message = ""
        self.display_time = 0
        self.max_display_time = 3000  # 3 seconds in milliseconds
        self.is_visible = False
        
        # Message box properties
        self.box_height = 40  # 50% less vertically long
        self.box_y = 40  # 40 pixels from top to avoid health bar
        self.padding = 15
        
    def show_message(self, text, duration=3000):
        """Show a message for the specified duration (in milliseconds)"""
        self.message = text
        self.display_time = 0
        self.max_display_time = duration
        self.is_visible = True
        
    def update(self, dt):
        """Update the message display timer"""
        if self.is_visible:
            self.display_time += dt
            if self.display_time >= self.max_display_time:
                self.is_visible = False
                
    def draw(self, screen):
        """Draw the message box and text with a desaturated purple box and outline"""
        if self.is_visible and self.message:
            # Create semi-transparent desaturated purple surface for the message box
            text_surface = self.font.render(self.message, True, (255, 255, 255))  # White text
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()

            # Calculate box dimensions
            box_width = text_width + (self.padding * 2)
            box_x = (self.screen_width - box_width) // 2  # Center horizontally

            # Desaturated purple for outline only
            outline_color = (110, 80, 130)

            # Create the semi-transparent black box
            box_surface = pygame.Surface((box_width, self.box_height))
            box_surface.set_alpha(180)  # Semi-transparent (0=fully transparent, 255=opaque)
            box_surface.fill((0, 0, 0))

            # Draw the box
            screen.blit(box_surface, (box_x, self.box_y))

            # Draw the desaturated purple outline (3px thick)
            outline_rect = pygame.Rect(box_x, self.box_y, box_width, self.box_height)
            for i in range(3):
                pygame.draw.rect(screen, outline_color, outline_rect.inflate(i*2, i*2), 1)

            # Draw the text centered in the box (horizontally and vertically)
            text_x = box_x + (box_width - text_width) // 2
            text_y = self.box_y + (self.box_height - text_height) // 2 + 3  # Move text 6px lower
            screen.blit(text_surface, (text_x, text_y))

# Collision detection functions
def check_collision(x, y, width, height, collision_tiles, tmx_data):
    """Check if a rectangle collides with any collision tiles"""
    # Convert pixel coordinates to tile coordinates
    left_tile = int(x // tmx_data.tilewidth)
    right_tile = int((x + width - 1) // tmx_data.tilewidth)
    top_tile = int(y // tmx_data.tileheight)
    bottom_tile = int((y + height - 1) // tmx_data.tileheight)
    
    # Check all tiles that the character would overlap
    for tile_x in range(left_tile, right_tile + 1):
        for tile_y in range(top_tile, bottom_tile + 1):
            if (tile_x, tile_y) in collision_tiles:
                return True
    return False

def get_character_hitbox(char_x, char_y, char_image, tmx_data):
    """Calculate the character's 1x1 tile hitbox centered in the lower half"""
    # Character sprite dimensions
    sprite_width = char_image.get_width()
    sprite_height = char_image.get_height()
    
    # Hitbox dimensions (smaller than 1 tile, e.g. 70% of tile size)
    hitbox_width = int(tmx_data.tilewidth * 0.7) + 2 # decrease width by 1px
    hitbox_height = int(tmx_data.tileheight * 0.3) + 4  # increase height by 2px

    # Center the hitbox horizontally within the sprite
    hitbox_x = char_x + (sprite_width - hitbox_width) // 2

    # Position hitbox in the lower half of the sprite
    # Start at 3/4 down the sprite height, move 2px up
    hitbox_y = char_y + (sprite_height * 3 // 4) - (hitbox_height // 2) - 2

    return hitbox_x, hitbox_y, hitbox_width, hitbox_height


screen_width = 1280
screen_height = 720

pygame.init()


# --- Initialize PlayerStats and Pause Menu --- PLAYER, STATS, LEVEL, POINTS, INIT, EXAMPLE
if LOADED_SAVE_DATA:
    # Defer creation to set_character_data which will use LOADED_SAVE_DATA
    print("[Overworld] Detected LOADED_SAVE_DATA at module init; skipping default PlayerStats construction")
    player_stats = None
else:
    player_stats = PlayerStats(
        name=PLAYER_CHARACTER_DATA['name'],
        gif_path=PLAYER_CHARACTER_DATA['gif_path'],
        sprite_path=PLAYER_CHARACTER_DATA['sprite_path'],
        has_extra_limbs=False,
        max_extral_limbs_hp=0,
        level=1,
        exp=0,
        evo_points_hp=0,
        evo_points_regen=0,
        evo_points_stamina=0,
        evo_points_reserve=0,
        evo_points_strength=0,
        evo_points_dexterity=0,
        evo_points_special=0,
        evo_points_speed=0
    )
pause_menu = PauseMenu(screen_width, screen_height, player_stats) if player_stats else None
game_paused = False

# --- Music System ---

import pygame.mixer
pygame.mixer.init()
# --- Music Volume Control ---
music_volume = 0.7  # Default music volume (0.0 to 1.0)
def set_music_volume(vol):
    global music_volume
    music_volume = max(0.0, min(1.0, vol))
    pygame.mixer.music.set_volume(music_volume)
    return music_volume

# Load game settings and apply fullscreen
game_settings = load_game_settings()
screen = apply_fullscreen_setting(game_settings, screen_width, screen_height)

# Load and start music with volume from settings
try:
    pygame.mixer.music.load(r"C:\Users\franc\Desktop\Afterdeath_RPG\Musics\Boney Rattle.MP3")
    # Set music volume from loaded settings
    set_music_volume(game_settings.get('music_volume', 0.7))
    pygame.mixer.music.play(-1)  # Loop forever
    print(f"Music started: Boney Rattle.MP3 with volume {music_volume}")
except Exception as e:
    print(f"Music could not be loaded: {e}")
pygame.display.set_caption("TMX Map with Camera")
clock = pygame.time.Clock()

if pause_menu:
    pause_menu.reload_frame_png()
else:
    # If not yet created (save loaded), initialize now then load frame
    initialize_player_from_loaded_save()
    if pause_menu:
        pause_menu.reload_frame_png()

# --- Precompute vignette for ambient occlusion ---

def create_vignette(width, height, strength=120, power=1.7):
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    cx, cy = width // 2, height // 2
    max_radius = math.hypot(cx, cy)
    strength = getattr(map_config.Config_Data, 'VIGNETTE_STRENGTH', 180)
    power = getattr(map_config.Config_Data, 'VIGNETTE_POWER', 1.7)
    for y in range(height):
        for x in range(width):
            dx = x - cx
            dy = y - cy
            dist = math.hypot(dx, dy)
            alpha = int(strength * (dist / max_radius) ** power)
            if alpha > 0:
                vignette.set_at((x, y), (0, 0, 0, min(alpha, strength)))
    return vignette

# --- Precompute filter effect for map ---
def create_map_filter(width, height, opacity=80, color=(0,0,0)):
    filter_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    r, g, b = color
    filter_surface.fill((r, g, b, opacity))
    return filter_surface

# --- Import map config ---
import Map_Roadmap

# --- Set initial map config and spawnpoint ---
# Check if we have a saved current map to load
if LOADED_PLAYER_POSITION and LOADED_PLAYER_POSITION.get("current_map"):
    saved_map = LOADED_PLAYER_POSITION["current_map"]
    print(f"[Overworld] Loading saved map: {saved_map}")
    
    # Map the saved map name to the appropriate config
    map_name_to_config = {
        "foresta_dorsale_sud": Map_Roadmap.foresta_dorsale_sud_config,
        "citta_01": Map_Roadmap.citta_01_config,
        "foresta_dorsale_est": Map_Roadmap.foresta_dorsale_est_config,
        # Add more map mappings as needed
    }
    
    if saved_map in map_name_to_config:
        map_config = map_name_to_config[saved_map]
        selected_spawnpoint = "Spawnpoint_1"  # Default spawn point for loaded maps
        print(f"[Overworld] Loaded map config for: {saved_map}")
        current_map_name = saved_map
    else:
        print(f"[Overworld] Unknown saved map '{saved_map}', using default")
        map_config, selected_spawnpoint = Map_Roadmap.MAP_TRANSITIONS.get(
            "__initial__", (Map_Roadmap.foresta_dorsale_sud_config, "Spawnpoint_1")
        )
        current_map_name = getattr(map_config.Config_Data, 'MAP_NAME', 'foresta_dorsale_sud')
else:
    # Default map for new games
    map_config, selected_spawnpoint = Map_Roadmap.MAP_TRANSITIONS.get(
        "__initial__", (Map_Roadmap.foresta_dorsale_sud_config, "Spawnpoint_1")
    )
    current_map_name = getattr(map_config.Config_Data, 'MAP_NAME', 'foresta_dorsale_sud')

# Debug: Print current map name
print(f"[DEBUG] Current map name: {current_map_name}")
print(f"[DEBUG] WORLD_STATE maps: {WORLD_STATE['maps']}")

# --- Vignette from config ---

import time
# --- Load filter effect from config ---
if getattr(map_config.Config_Data, 'HAS_FILTER', False):
    filter_opacity = getattr(map_config.Config_Data, 'FILTER_OPACITY', 80)
    filter_color = getattr(map_config.Config_Data, 'FILTER_COLOR', (0,0,0))
    filter_surface = create_map_filter(screen_width, screen_height, filter_opacity, filter_color)
else:
    filter_surface = None

# --- Vignette from config ---
if getattr(map_config.Config_Data, 'HAS_VIGNETTE', False):
    vignette_surface = create_vignette(screen_width, screen_height)
else:
    vignette_surface = None

# --- TMX path from config ---
tmx_data = load_pygame(map_config.Config_Data.TMX_PATH)

# Clear any existing animated tile states from previous sessions
if hasattr(pygame, 'animated_tile_states'):
    pygame.animated_tile_states.clear()

tile_group = pygame.sprite.Group()  # Renamed for clarity
object_group = pygame.sprite.Group()  # Separate group for objects
player_group = pygame.sprite.Group()

# Calculate map dimensions
map_width = tmx_data.width * tmx_data.tilewidth
map_height = tmx_data.height * tmx_data.tileheight

# Create camera
camera = Camera(screen_width, screen_height)
camera.set_map_size(map_width, map_height)

# Find spawn point from map objects
def find_spawn_point(tmx_data, selected_spawnpoint="Spawnpoint_1"):
    """Find the spawn point from objects with 'spawnpoint' in their name"""
    
    # First pass: collect all spawn points
    spawn_points = {}
    object_count = 0
    
    for obj in tmx_data.objects:
        object_count += 1
        
        # Check if object name contains 'spawnpoint' 
        if hasattr(obj, 'name') and obj.name and 'spawnpoint' in obj.name.lower():
            spawn_points[obj.name] = (obj.x, obj.y)
            print(f"  -> Found spawn point '{obj.name}' at ({obj.x}, {obj.y})")
    
    print(f"Checked {object_count} total objects")
    print(f"Found {len(spawn_points)} spawn points: {list(spawn_points.keys())}")
    
    # Try to find the selected spawn point
    if selected_spawnpoint in spawn_points:
        print(f"Using selected spawn point '{selected_spawnpoint}' at {spawn_points[selected_spawnpoint]}")
        return spawn_points[selected_spawnpoint]
    elif spawn_points:
        # If selected spawn point not found, use the first available one
        first_spawn = list(spawn_points.keys())[0]
        print(f"Selected spawn point '{selected_spawnpoint}' not found, using '{first_spawn}' at {spawn_points[first_spawn]}")
        return spawn_points[first_spawn]
    else:
        # If no spawn points found, use default position
        print("No spawn points found, using default position (600, 400)")
        return (600, 400)

# Configuration: Select which spawn point to use
selected_spawnpoint = "Spawnpoint_1"  # Change this to use different spawn points

# Create player at dynamic spawn point or saved position
if LOADED_PLAYER_POSITION and LOADED_PLAYER_POSITION["x"] is not None and LOADED_PLAYER_POSITION["y"] is not None:
    # Use saved position
    spawn_position = (LOADED_PLAYER_POSITION["x"], LOADED_PLAYER_POSITION["y"])
    print(f"[Overworld] Using saved player position: {spawn_position}")
else:
    # Use default spawn point
    spawn_position = find_spawn_point(tmx_data, selected_spawnpoint)
    print(f"[Overworld] Using default spawn position: {spawn_position}")

player = Player(spawn_position, player_group, player_stats.sprite_path)
player.speed *= 24

# Initialize camera position centered on player
initial_camera_x = player.pos.x - (screen_width / camera.zoom_factor) / 2
initial_camera_y = player.pos.y - (screen_height / camera.zoom_factor) / 2
camera.set_position(initial_camera_x, initial_camera_y)


# --- Place enemies at map object positions ---
# Place enemies at map object positions using ENEMIES_DATA and create_npc_from_data

from Enemies_List import ENEMIES_DATA, create_npc_from_data, get_enemy_data_by_name


# Debug: Print all objects with type 'Enemy'
print("[DEBUG] Listing all map objects with type 'Enemy':")
for obj in tmx_data.objects:
    if getattr(obj, 'type', None) == 'Enemy':
        print(f"[DEBUG] Enemy object found: name='{getattr(obj, 'name', None)}', pos=({obj.x}, {obj.y})")

# Place enemies at map object positions using ENEMIES_DATA and create_npc_from_data
current_map = globals().get('current_map_name', 'unknown_map')
killed_enemies_list = WORLD_STATE["maps"].get(current_map, {}).get("killed_enemies", [])
print(f"[DEBUG] Enemy spawning check - current_map: '{current_map}'")
print(f"[DEBUG] WORLD_STATE maps: {list(WORLD_STATE['maps'].keys())}")
print(f"[DEBUG] killed_enemies_list for this map: {killed_enemies_list}")

for obj in tmx_data.objects:
    # Only place enemies for objects of class 'Enemy' and matching name
    if getattr(obj, 'type', None) == 'Enemy' and hasattr(obj, 'name'):
        enemy_name = obj.name
        spawn_x, spawn_y = obj.x, obj.y
        
        # Check if this enemy was killed at this spawn location
        is_killed = False
        killed_enemy = None
        for killed in killed_enemies_list:
            if (killed["name"] == enemy_name and 
                killed["spawn_x"] == spawn_x and 
                killed["spawn_y"] == spawn_y):
                is_killed = True
                killed_enemy = killed
                break
        
        if is_killed:
            # Spawn corpse at death location instead of live enemy
            print(f"[WorldState] Spawning corpse for killed enemy '{enemy_name}' at death coords ({killed_enemy['death_x']}, {killed_enemy['death_y']})")
            
            # Load death image
            death_image = None
            enemy_data = get_enemy_data_by_name(enemy_name)
            if enemy_data:
                death_image_path = enemy_data.get("death_image_path")
                if death_image_path:
                    try:
                        death_image = pygame.image.load(death_image_path).convert_alpha()
                    except Exception as e:
                        print(f"[WorldState] Could not load death image: {e}")
            
            if death_image is None:
                death_image = pygame.Surface((32,32), pygame.SRCALPHA)
                death_image.fill((80, 80, 80, 180))  # Gray fallback
            
            # Create corpse at death location
            try:
                corpse_obj = Corpse((killed_enemy['death_x'], killed_enemy['death_y']), death_image, enemy_name)
                # Store unique corpse ID based on death coordinates for interaction tracking (legacy)
                corpse_obj.unique_corpse_id = f"{enemy_name}_{int(killed_enemy['death_x'])}_{int(killed_enemy['death_y'])}"
                # NEW: Set interaction flag based on the killed enemy's interaction count
                corpse_interactions = killed_enemy.get('interactions', 0)
                if corpse_interactions > 0:
                    corpse_obj.corpse_interacted = True
                    print(f"[WorldState] Corpse marked as already interacted (interactions: {corpse_interactions})")
                else:
                    corpse_obj.corpse_interacted = False
                    print(f"[WorldState] Corpse ready for first interaction")
                print(f"[WorldState] Corpse spawned for {enemy_name} with ID: {corpse_obj.unique_corpse_id}")
            except Exception as e:
                print(f"[WorldState] Error creating corpse: {e}")
        else:
            # Spawn live enemy normally
            enemy_data = get_enemy_data_by_name(obj.name)
            print(f"[DEBUG] get_enemy_data_by_name('{obj.name}') returned: {enemy_data}")
            if enemy_data:
                enemy_npc = create_npc_from_data(enemy_data, (obj.x, obj.y), object_group)
                # Store spawn coordinates for future reference
                enemy_npc.spawn_x = obj.x
                enemy_npc.spawn_y = obj.y
                print(f"[DEBUG] Enemy NPC created: {enemy_npc.name} at {enemy_npc.pos}")

# Create message display system
message_display = MessageDisplay(screen_width, screen_height)

# --- Event System ---
class GameEvent:
    def __init__(self, name, x, y, width, height):
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        self.triggered = False  # Prevent retriggering if needed

# Find all event objects
event_list = []
for obj in tmx_data.objects:
    if hasattr(obj, 'name') and obj.name and 'event' in obj.name.lower():
        event_rect = pygame.Rect(obj.x, obj.y, getattr(obj, 'width', 0), getattr(obj, 'height', 0))
        event_list.append(GameEvent(obj.name, obj.x, obj.y, getattr(obj, 'width', 0), getattr(obj, 'height', 0)))
        print(f"Event found: {obj.name} at ({obj.x}, {obj.y}, {getattr(obj, 'width', 0)}, {getattr(obj, 'height', 0)})")


# Collision detection setup
collision_tiles = set()  # Set to store collision tile positions
for layer in tmx_data.layers:
    if hasattr(layer, 'data'):  # Tile layers
        # Add collision tiles from ALL layers (both visible and invisible)
        if 'collision' in layer.name.lower() or not layer.visible:
            for x, y, gid in layer:
                if gid:  # If there's a tile here
                    collision_tiles.add((x, y))
        # Only render visible layers
        if layer.visible:
            for x, y, surface in layer.tiles():
                if surface:  # Only create tiles for non-empty tiles
                    pos = (x * tmx_data.tilewidth, y * tmx_data.tileheight)
                    Tile(pos=pos, surf=surface, groups=tile_group)
            print(f"Visible layer '{layer.name}' rendered")

print(f"Total collision tiles loaded: {len(collision_tiles)}")

print(f"Map info: {tmx_data.width}x{tmx_data.height} tiles, tile size: {tmx_data.tilewidth}x{tmx_data.tileheight}")
print(f"Map pixel size: {map_width}x{map_height}")

def apply_object_transformations(obj):
    """
    Apply rotation, flipping, and scaling transformations to an object's image
    based on TMX editor properties, matching Tiled's exact behavior.
    
    Based on Tiled's source code and documentation:
    - TMX rotation is in degrees clockwise around object position (x,y)
    - Tile objects use bottom-left alignment in orthogonal orientation
    - Objects rotate around their bottom-left point (for tile objects)
    
    Args:
        obj: TMX object with image and transformation properties
        
    Returns:
        dict: {'surface': transformed_surface, 'offset_x': x_offset, 'offset_y': y_offset}
              or None if no image
    """
    if not hasattr(obj, 'image') or obj.image is None:
        return None
    
    # Start with the base image
    if hasattr(obj.image, 'convert_alpha'):
        surf = obj.image.convert_alpha()
    else:
        surf = obj.image
    
    # Get transformation properties from TMX object
    rotation = getattr(obj, 'rotation', 0)  # TMX rotation in degrees
    width = getattr(obj, 'width', surf.get_width())
    height = getattr(obj, 'height', surf.get_height())
    
    # Check for flipping flags (TMX format uses these properties)
    flipped_horizontally = getattr(obj, 'flipped_horizontally', False)
    flipped_vertically = getattr(obj, 'flipped_vertically', False)
    flipped_diagonally = getattr(obj, 'flipped_diagonally', False)
    
    # Alternative: check for flip flags in properties if they exist
    if hasattr(obj, 'properties'):
        flipped_horizontally = obj.properties.get('flipped_h', flipped_horizontally)
        flipped_vertically = obj.properties.get('flipped_v', flipped_vertically)
        flipped_diagonally = obj.properties.get('flipped_d', flipped_diagonally)
    
    # Convert rotation to degrees if it's in radians (PyTMX might return radians)
    if rotation != 0:
        # If rotation is greater than 2*pi (6.28), it's likely already in degrees
        if abs(rotation) > 6.28:
            angle_degrees = rotation  # Already in degrees
        else:
            angle_degrees = math.degrees(rotation)  # Convert from radians
    else:
        angle_degrees = 0
    
    # Store original dimensions for offset calculations
    original_width = surf.get_width()
    original_height = surf.get_height()
    
    # Apply scaling if size differs from original
    if width != original_width or height != original_height:
        surf = pygame.transform.scale(surf, (int(width), int(height)))
    
    # Apply flipping transformations
    if flipped_horizontally:
        surf = pygame.transform.flip(surf, True, False)
    
    if flipped_vertically:
        surf = pygame.transform.flip(surf, False, True)
    
    if flipped_diagonally:
        # Diagonal flip = transpose (flip along diagonal axis)
        surf = pygame.transform.rotate(surf, 90)
        surf = pygame.transform.flip(surf, True, False)
    
    # Initialize offset values
    offset_x = 0
    offset_y = 0
    
    # Apply rotation with correct offset calculation
    if angle_degrees != 0:
        # Normalize angle to 0-360 range
        normalized_angle = angle_degrees % 360
        
        # TMX uses clockwise rotation, pygame uses counter-clockwise
        # So we need to negate the angle for pygame
        pygame_angle = -normalized_angle
        
        # Get dimensions before rotation for offset calculation
        pre_rot_width = surf.get_width()
        pre_rot_height = surf.get_height()
        
        # Apply rotation
        rotated_surf = pygame.transform.rotate(surf, pygame_angle)
        
        # Calculate the offset needed to maintain bottom-left alignment
        # This is based on how Tiled handles rotation around the bottom-left point
        angle_rad = math.radians(normalized_angle)
        
        # For bottom-left alignment, we need to calculate where the bottom-left corner
        # of the original image ends up after rotation, then offset to keep it at (0,0)
        
        # Original bottom-left corner relative to image center
        orig_bottom_left_x = -pre_rot_width / 2
        orig_bottom_left_y = pre_rot_height / 2
        
        # After rotation (clockwise), where does the bottom-left corner end up?
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Rotate the bottom-left corner point around the center
        rotated_bl_x = orig_bottom_left_x * cos_a - orig_bottom_left_y * sin_a
        rotated_bl_y = orig_bottom_left_x * sin_a + orig_bottom_left_y * cos_a
        
        # The offset is the difference between where we want the bottom-left (at origin)
        # and where it actually is after rotation
        new_center_x = rotated_surf.get_width() / 2
        new_center_y = rotated_surf.get_height() / 2
        
        # Calculate final offset to align bottom-left corner
        offset_x = -(rotated_bl_x + new_center_x)
        offset_y = -(rotated_bl_y + new_center_y - rotated_surf.get_height())
        
        surf = rotated_surf
    return {
        'surface': surf,
        'offset_x': offset_x,
        'offset_y': offset_y
    }

for obj in tmx_data.objects:
    
    # Skip objects of class 'Enemy' (already handled above)
    if getattr(obj, 'type', None) == 'Enemy':
        continue
    
    # Debug: print all objects with their properties
    obj_name = getattr(obj, 'name', 'NO_NAME')
    obj_type = getattr(obj, 'type', 'NO_TYPE')
    has_image = hasattr(obj, 'image') and obj.image is not None
    
    # Check if this object was killed/removed using proximity matching
    current_map = globals().get('current_map_name', 'unknown_map')
    killed_objects_list = WORLD_STATE["maps"].get(current_map, {}).get("killed_objects", [])
    
    # Initialize used_records set if not already created
    if not hasattr(tmx_data, '_used_object_records'):
        tmx_data._used_object_records = set()
    
    killed_obj_record = is_object_killed_nearby(obj_name, obj.x, obj.y, killed_objects_list, used_records=tmx_data._used_object_records)
    
    if killed_obj_record:
        print(f"[WorldState] Skipping killed object '{obj_name}' at ({obj.x}, {obj.y}) - killed at ({killed_obj_record['x']}, {killed_obj_record['y']})")
        continue
    
    if obj.image:
        # Apply all transformations (rotation, flipping, scaling) from TMX editor
        transform_result = apply_object_transformations(obj)
        if transform_result is None:
            continue  # Skip if transformation failed
        
        # Extract surface and offsets from the transformation result
        surf = transform_result['surface']
        offset_x = transform_result['offset_x']
        offset_y = transform_result['offset_y']
        
        # Apply the calculated offset to the position to match Tiled's behavior
        pos = (obj.x + offset_x, obj.y + offset_y)
        obj_tile = Tile(pos=pos, surf=surf, groups=object_group)
        obj_tile.depth_y = obj.y + obj.height
        # Add name to the tile sprite for interaction
        obj_tile.name = obj_name
        
        # Store GID for tile objects (needed for animation)
        obj_gid = getattr(obj, 'gid', None)
        if obj_gid:
            obj_tile.gid = obj_gid
            # Check if this tile has animation frames
            tile_frames = None
            if hasattr(tmx_data, 'get_tile_frames_by_gid'):
                tile_frames = tmx_data.get_tile_frames_by_gid(obj_gid)
            elif hasattr(tmx_data, 'tile_properties') and obj_gid in tmx_data.tile_properties:
                tile_frames = tmx_data.tile_properties[obj_gid].get('frames', None)
            
            if tile_frames and isinstance(tile_frames, list) and len(tile_frames) > 0:
                obj_tile.is_animated = True
                obj_tile.animation_frames = tile_frames
                print(f"[DEBUG] Added animated tile object '{obj_name}' with {len(tile_frames)} frames")
            else:
                obj_tile.is_animated = False
        else:
            obj_tile.is_animated = False
            
        print(f"[DEBUG] Added visible object '{obj_name}' to object_group with offset ({offset_x:.1f}, {offset_y:.1f})")
    else:
        # Invisible objects are handled by the TMX object system (is_player_facing_object_center)
        # Don't create sprite objects for them to avoid double interactions
        if obj_name != 'NO_NAME':
            print(f"[DEBUG] Skipped invisible object '{obj_name}' - will be handled by TMX object system")


# --- Utility: Fast fade to black ---
def fade_to_black(screen, duration=200):
    clock = pygame.time.Clock()
    fade_surface = pygame.Surface(screen.get_size())
    fade_surface.fill((0, 0, 0))
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < duration:
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        clock.tick(120)

# --- Minimal PromptInteraction class ---
class PromptInteraction:
    def __init__(self):
        self.active = False
        self.messages = []
        self.actions = []
        self.index = 0
        self.current_object = None  # Store reference to object for actions like removal
        self.last_interaction_time = 0  # Add cooldown to prevent rapid interactions
        self.interaction_cooldown = 500  # 500ms cooldown between interactions
        self.found_loot_message = None  # Store loot result message
        self.interaction_position = None  # Store the position where interaction started
        self.object_name = None  # Store the name of the object being interacted with
    
    def can_interact(self):
        """Check if enough time has passed since last interaction"""
        current_time = pygame.time.get_ticks()
        return current_time - self.last_interaction_time >= self.interaction_cooldown
    
    def start(self, messages, actions=None, obj=None, sprite=None):
        # Check cooldown before starting new interaction
        if not self.can_interact():
            print("[SCRIPT] Interaction on cooldown, ignoring")
            return
            
        self.active = True
        self.messages = messages
        self.actions = actions if actions else [None]*len(messages)
        self.index = 0
        self.current_object = obj  # Store object reference for removal actions
        self.last_interaction_time = pygame.time.get_ticks()
        self.found_loot_message = None  # Reset loot message
        
        # Store interaction details for object removal
        if obj:  # TMX object
            self.interaction_position = (getattr(obj, 'x', 0), getattr(obj, 'y', 0))
            self.object_name = getattr(obj, 'name', None)
        elif sprite:  # Sprite object
            self.interaction_position = (sprite.rect.x, sprite.rect.y)
            self.object_name = getattr(sprite, 'name', None)
        else:
            self.interaction_position = (0, 0)
            self.object_name = None
            
        print(f"[SCRIPT] Starting interaction with '{self.object_name}' at position {self.interaction_position}")
        self.show_current()
    def show_current(self):
        if self.active and self.index < len(self.messages):
            msg = self.messages[self.index]
            action = self.actions[self.index] if self.actions and self.index < len(self.actions) else None
            if isinstance(msg, dict):
                text = msg.get('message', str(msg))
            else:
                text = str(msg)
            message_display.show_message(text, 999999)  # Show until advanced
            # Perform action for this message if present
            if action:
                if action.get('type') == 'give_item':
                    item = action.get('item')
                    print(f"[SCRIPT] Giving item to player: {item}")
                    # Add item to player inventory (implement as needed)
                elif action.get('type') == 'add_item':
                    item_name = action.get('item')
                    print(f"[SCRIPT] Adding item to player inventory: {item_name}")
                    # Try to use global Player_Items import and add the item
                    if Player_Items and hasattr(Player_Items, 'player1_items'):
                        # Look for the item in the available items
                        item_found = None
                        # Check all example item lists
                        for item_list_name in ['example_misc_items', 'example_food_items', 'example_key_items']:
                            if hasattr(Player_Items, item_list_name):
                                item_list = getattr(Player_Items, item_list_name)
                                for item in item_list:
                                    if item.name.replace(' ', '_') == item_name or item.name == item_name:
                                        item_found = item
                                        break
                                if item_found:
                                    break
                        
                        if item_found:
                            Player_Items.player1_items.add_item(item_found)
                            print(f"[SCRIPT] Successfully added item: {item_found.name}")
                        else:
                            print(f"[SCRIPT] Item '{item_name}' not found in Player_Items")
                            # Create a generic item if not found
                            generic_item = Player_Items.Item(
                                item_name.replace('_', ' '),
                                None, None, 'MISC',
                                f"A {item_name.replace('_', ' ').lower()}.",
                                f"{item_name.replace('_', ' ')}"
                            )
                            Player_Items.player1_items.add_item(generic_item)
                            print(f"[SCRIPT] Created and added generic item: {generic_item.name}")
                    else:
                        print(f"[SCRIPT] Player_Items module not available")
                elif action.get('type') == 'give_exp':
                    exp = action.get('amount', 0)
                    Get_Exp(player_stats, exp)
                    print(f"[SCRIPT] Giving {exp} EXP to player.")
                elif action.get('type') == 'add_equipment':
                    item = action.get('item')
                    print(f"[SCRIPT] Adding equipment to player: {item}")
                    # Use global Player_Equipment import
                    if Player_Equipment and hasattr(Player_Equipment, 'player1') and hasattr(Player_Equipment.player1, 'add_equipment'):
                        # Try to get the equipment object by name from Player_Equipment module
                        equipment_obj = getattr(Player_Equipment, item, None)
                        if equipment_obj and hasattr(equipment_obj, 'name'):
                            # Check current equipment count before adding
                            current_count = len(Player_Equipment.player1.equip)
                            Player_Equipment.player1.add_equipment(equipment_obj)
                            new_count = len(Player_Equipment.player1.equip)
                            print(f"[SCRIPT] Successfully added equipment: {equipment_obj.name}")
                            print(f"[SCRIPT] Equipment count: {current_count} -> {new_count}")
                            print(f"[SCRIPT] Current equipment list: {[eq.name for eq in Player_Equipment.player1.equip]}")
                        else:
                            print(f"[SCRIPT] Equipment '{item}' not found in Player_Equipment module")
                            print(f"[SCRIPT] Available equipment in module: {[attr for attr in dir(Player_Equipment) if not attr.startswith('_') and hasattr(getattr(Player_Equipment, attr, None), 'name')]}")
                    else:
                        print(f"[SCRIPT] Player_Equipment.player1.add_equipment not available")
                elif action.get('type') == 'random_loot':
                    pool_name = action.get('pool')
                    print(f"[SCRIPT] Rolling for random loot from pool: {pool_name}")
                    
                    # Get the loot from the map config
                    loot_type, loot_name, quantity = map_config.Config_Data.get_random_loot(pool_name)
                    
                    if loot_type is None:
                        print(f"[SCRIPT] Found nothing in the search...")
                        # Update the current message to show the result
                        message_display.show_message("You search around but find nothing of interest.", 3000)
                    elif loot_type == 'item':
                        print(f"[SCRIPT] Found {quantity}x {loot_name} (item)")
                        
                        # Add the item(s) to inventory
                        if Player_Items and hasattr(Player_Items, 'player1_items'):
                            # Look for the item in the available items
                            item_found = None
                            for item_list_name in ['example_misc_items', 'example_food_items', 'example_key_items']:
                                if hasattr(Player_Items, item_list_name):
                                    item_list = getattr(Player_Items, item_list_name)
                                    for item in item_list:
                                        if item.name.replace(' ', '_') == loot_name or item.name == loot_name:
                                            item_found = item
                                            break
                                    if item_found:
                                        break
                            
                            if item_found:
                                for _ in range(quantity):
                                    Player_Items.player1_items.add_item(item_found)
                                print(f"[SCRIPT] Successfully added {quantity}x {item_found.name}")
                                qty_text = f"{quantity}x " if quantity > 1 else ""
                                # Update the current message to show the result
                                message_display.show_message(f"You found {qty_text}{item_found.name}!", 3000)
                            else:
                                # Create a generic item if not found
                                generic_item = Player_Items.Item(
                                    loot_name.replace('_', ' '),
                                    None, None, 'MISC',
                                    f"A {loot_name.replace('_', ' ').lower()}.",
                                    f"{loot_name.replace('_', ' ')}"
                                )
                                for _ in range(quantity):
                                    Player_Items.player1_items.add_item(generic_item)
                                print(f"[SCRIPT] Created and added {quantity}x generic item: {generic_item.name}")
                                qty_text = f"{quantity}x " if quantity > 1 else ""
                                # Update the current message to show the result
                                message_display.show_message(f"You found {qty_text}{generic_item.name}!", 3000)
                        else:
                            print(f"[SCRIPT] Player_Items module not available")
                            message_display.show_message("You search around but find nothing of interest.", 3000)
                            
                    elif loot_type == 'equipment':
                        print(f"[SCRIPT] Found {quantity}x {loot_name} (equipment)")
                        
                        # Add the equipment to inventory
                        if Player_Equipment and hasattr(Player_Equipment, 'player1') and hasattr(Player_Equipment.player1, 'add_equipment'):
                            equipment_obj = getattr(Player_Equipment, loot_name, None)
                            if equipment_obj and hasattr(equipment_obj, 'name'):
                                for _ in range(quantity):
                                    Player_Equipment.player1.add_equipment(equipment_obj)
                                print(f"[SCRIPT] Successfully added {quantity}x {equipment_obj.name}")
                                qty_text = f"{quantity}x " if quantity > 1 else ""
                                # Update the current message to show the result
                                message_display.show_message(f"You found {qty_text}{equipment_obj.name}!", 3000)
                            else:
                                print(f"[SCRIPT] Equipment '{loot_name}' not found in Player_Equipment module")
                                # Show generic found equipment message
                                message_display.show_message("You found some equipment, but couldn't identify it.", 3000)
                        else:
                            print(f"[SCRIPT] Player_Equipment module not available")
                            message_display.show_message("You search around but find nothing of interest.", 3000)
                elif action.get('type') == 'remove_object':
                    print(f"[SCRIPT] Removing object from map")
                    if self.object_name and self.interaction_position:
                        print(f"[SCRIPT] Object info: name='{self.object_name}', pos=({self.interaction_position[0]}, {self.interaction_position[1]})")
                        
                        # Record object removal in world state
                        try:
                            current_map = globals().get('current_map_name', 'unknown_map')
                            if current_map not in WORLD_STATE["maps"]:
                                WORLD_STATE["maps"][current_map] = {"killed_enemies": [], "killed_objects": []}
                            
                            object_record = {
                                "name": self.object_name,
                                "x": self.interaction_position[0],
                                "y": self.interaction_position[1]
                            }
                            WORLD_STATE["maps"][current_map]["killed_objects"].append(object_record)
                            print(f"[SCRIPT] Recorded object removal: {object_record}")
                        except Exception as e:
                            print(f"[SCRIPT] Error recording object removal: {e}")
                        
                        # Find the nearest sprite with matching name
                        nearest_sprite = find_nearest_object_with_name(self.object_name, self.interaction_position)
                        
                        if nearest_sprite:
                            distance = math.hypot(self.interaction_position[0] - nearest_sprite.rect.x, self.interaction_position[1] - nearest_sprite.rect.y)
                            print(f"[SCRIPT] Removing sprite at rect=({nearest_sprite.rect.x}, {nearest_sprite.rect.y}) with distance {distance:.1f}px")
                            nearest_sprite.kill()  # Remove sprite from all groups
                            print(f"[SCRIPT] Successfully removed nearest object '{nearest_sprite.name}' from map")
                            
                            # Mark object as removed so it won't be removed again at the end
                            self.current_object = None
                        else:
                            print(f"[SCRIPT] Could not find any sprite with name '{self.object_name}' to remove")
                            print(f"[SCRIPT] Available sprites: {[getattr(s, 'name', 'NO_NAME') for s in object_group]}")
                    else:
                        print(f"[SCRIPT] No object name or position stored for removal")
                # Add more custom actions as needed
        else:
            self.active = False
            message_display.is_visible = False
    def advance(self):
        if self.active:
            self.index += 1
            if self.index < len(self.messages):
                self.show_current()
            else:
                # Interaction completed - check for auto-removal
                # Check if any action in this interaction was a remove_object action
                has_remove_action = False
                if self.actions:
                    for action in self.actions:
                        if action and action.get('type') == 'remove_object':
                            has_remove_action = True
                            break
                
                # Only remove automatically if there was no explicit remove_object action
                if not has_remove_action:
                    if self.object_name and self.interaction_position:
                        print(f"[SCRIPT] Auto-removal: Object info: name='{self.object_name}', pos=({self.interaction_position[0]}, {self.interaction_position[1]})")
                        print(f"[SCRIPT] All sprites with name '{self.object_name}':")
                        
                        # List all matching sprites before removal
                        matching_sprites = []
                        for sprite in object_group:
                            if hasattr(sprite, 'name') and sprite.name == self.object_name:
                                matching_sprites.append(sprite)
                                print(f"[SCRIPT]   - Sprite at rect=({sprite.rect.x}, {sprite.rect.y}), center=({sprite.rect.centerx}, {sprite.rect.centery})")
                        
                        print(f"[SCRIPT] Found {len(matching_sprites)} sprites with matching name")
                        
                        # Find the nearest sprite with matching name
                        nearest_sprite = find_nearest_object_with_name(self.object_name, self.interaction_position)
                        
                        if nearest_sprite:
                            distance = math.hypot(self.interaction_position[0] - nearest_sprite.rect.x, self.interaction_position[1] - nearest_sprite.rect.y)
                            print(f"[SCRIPT] Auto-removing sprite at rect=({nearest_sprite.rect.x}, {nearest_sprite.rect.y}) with distance {distance:.1f}px")
                            
                            # Record object removal in world state for auto-removal too
                            try:
                                current_map = globals().get('current_map_name', 'unknown_map')
                                if current_map not in WORLD_STATE["maps"]:
                                    WORLD_STATE["maps"][current_map] = {"killed_enemies": [], "killed_objects": []}
                                
                                object_record = {
                                    "name": self.object_name,
                                    "x": self.interaction_position[0],
                                    "y": self.interaction_position[1]
                                }
                                WORLD_STATE["maps"][current_map]["killed_objects"].append(object_record)
                                print(f"[SCRIPT] Recorded auto-removed object: {object_record}")
                            except Exception as e:
                                print(f"[SCRIPT] Error recording auto-removed object: {e}")
                            
                            nearest_sprite.kill()  # Remove sprite from all groups
                            print(f"[SCRIPT] Successfully auto-removed nearest object '{nearest_sprite.name}' from map")
                        else:
                            print(f"[SCRIPT] Could not find any sprite with name '{self.object_name}' to auto-remove")
                            print(f"[SCRIPT] Available sprites: {[getattr(s, 'name', 'NO_NAME') for s in object_group]}")
                    else:
                        print(f"[SCRIPT] No object name or position stored for auto-removal")
                else:
                    print(f"[SCRIPT] Interaction had explicit remove_object action, skipping auto-removal")
                
                self.active = False
                self.current_object = None  # Clear the object reference
                message_display.is_visible = False
prompt_interaction = PromptInteraction()

def find_nearest_object_with_name(object_name, reference_pos):
    """
    Find the nearest object in object_group with the given name to a reference position.
    
    Args:
        object_name (str): Name of the object to find
        reference_pos (tuple): (x, y) reference position
        
    Returns:
        pygame.sprite.Sprite or None: The nearest object, or None if not found
    """
    nearest_sprite = None
    min_distance = float('inf')
    
    for sprite in object_group:
        if hasattr(sprite, 'name') and sprite.name == object_name:
            # Calculate distance from reference position to sprite position
            distance = math.hypot(reference_pos[0] - sprite.rect.x, reference_pos[1] - sprite.rect.y)
            if distance < min_distance:
                min_distance = distance
                nearest_sprite = sprite
    
    return nearest_sprite

def find_nearest_object_with_name(object_name, reference_pos):
    """
    Find the nearest object in object_group with the given name to a reference position.
    
    Args:
        object_name (str): Name of the object to find
        reference_pos (tuple): Reference position (x, y) to measure distance from
        
    Returns:
        sprite or None: The nearest sprite with matching name, or None if not found
    """
    nearest_sprite = None
    nearest_distance = float('inf')
    
    print(f"[DEBUG] find_nearest_object_with_name: Looking for '{object_name}' near TMX position ({reference_pos[0]}, {reference_pos[1]})")
    
    candidates = []
    for sprite in object_group:
        if hasattr(sprite, 'name') and sprite.name == object_name:
            # Try multiple distance calculations to see which works best
            sprite_rect_pos = (sprite.rect.x, sprite.rect.y)
            sprite_center = sprite.rect.center
            
            # Distance to sprite rect top-left
            dist_to_rect = math.hypot(reference_pos[0] - sprite_rect_pos[0], reference_pos[1] - sprite_rect_pos[1])
            # Distance to sprite center
            dist_to_center = math.hypot(reference_pos[0] - sprite_center[0], reference_pos[1] - sprite_center[1])
            
            candidates.append({
                'sprite': sprite,
                'rect_pos': sprite_rect_pos,
                'center_pos': sprite_center,
                'dist_to_rect': dist_to_rect,
                'dist_to_center': dist_to_center
            })
            
            print(f"[DEBUG]   Candidate: rect=({sprite_rect_pos[0]}, {sprite_rect_pos[1]}), center=({sprite_center[0]}, {sprite_center[1]}), dist_rect={dist_to_rect:.1f}, dist_center={dist_to_center:.1f}")
    
    if not candidates:
        print(f"[DEBUG] No sprites found with name '{object_name}'")
        return None
    
    # Use distance to rect position (top-left) as it matches TMX object positioning better
    nearest_candidate = min(candidates, key=lambda c: c['dist_to_rect'])
    nearest_sprite = nearest_candidate['sprite']
    
    print(f"[DEBUG] Selected nearest sprite at rect=({nearest_candidate['rect_pos'][0]}, {nearest_candidate['rect_pos'][1]}), distance={nearest_candidate['dist_to_rect']:.1f}")
    
    return nearest_sprite

# Reserve logic timer
reserve_logic_timer = 0.0

# --- Auto-save system ---
AUTO_SAVE_INTERVAL_MS = 10000  # 10 seconds (for testing - was 60 seconds)
_auto_save_elapsed = 0

def create_complete_save(reason="interval"):
    """
    UNIFIED SAVE FUNCTION - Used by auto-save, manual save, map transitions, and combat.
    Creates a complete save including player stats, position, and world state.
    """
    try:
        print(f"[SaveGame] Starting complete save for reason: {reason}")
        
        # Check if we have required globals
        if 'player_stats' not in globals() or 'player' not in globals():
            print(f"[SaveGame] Missing player context (player_stats={('player_stats' in globals())}, player={('player' in globals())}), skipping save")
            return None
            
        # Get current player position
        x = 0.0
        y = 0.0
        try:
            if hasattr(player, 'pos') and player.pos is not None:
                x = float(getattr(player.pos, 'x', 0.0))
                y = float(getattr(player.pos, 'y', 0.0))
            elif hasattr(player, 'rect'):
                x = float(player.rect.centerx)
                y = float(player.rect.centery)
        except Exception as e:
            print(f"[SaveGame] Warning: Could not get player position: {e}")
            
        # Get current map name
        map_name = globals().get('current_map_name', 'foresta_dorsale_sud')
        
        # Mark current map as explored
        if map_name not in WORLD_STATE["explored_maps"]:
            WORLD_STATE["explored_maps"].append(map_name)
            print(f"[SaveGame] Added '{map_name}' to explored maps")
        
        # Create complete world data including world state
        world_data = {
            "player_position": {"x": x, "y": y, "current_map": map_name},
            "explored_maps": WORLD_STATE["explored_maps"],
            "maps": WORLD_STATE["maps"],
            # New enemy type interaction counters for limit system
            "enemy_type_interactions": enemy_type_interaction_counter,
            # Legacy fields for compatibility
            "corpse_interactions": {},  # Keep empty for compatibility but no longer used
            "enemies": {},
            "interactions": {},
            "map_events": {}
        }
        
        # Debug: Print world state summary
        print(f"[SaveGame] World state summary:")
        print(f"  - Player: {player_stats.name} (Level {player_stats.level}, EXP {player_stats.exp})")
        print(f"  - Position: ({x:.2f}, {y:.2f}) on map '{map_name}'")
        print(f"  - Explored maps: {len(WORLD_STATE['explored_maps'])} ({WORLD_STATE['explored_maps']})")
        
        total_killed_enemies = 0
        total_killed_objects = 0
        for map_key, map_data in WORLD_STATE["maps"].items():
            if map_data:
                killed_enemies_count = len(map_data.get("killed_enemies", []))
                killed_objects_count = len(map_data.get("killed_objects", []))
                total_killed_enemies += killed_enemies_count
                total_killed_objects += killed_objects_count
                if killed_enemies_count > 0 or killed_objects_count > 0:
                    print(f"  - Map '{map_key}': {killed_enemies_count} killed enemies, {killed_objects_count} killed objects")
        
        print(f"  - Total across all maps: {total_killed_enemies} killed enemies, {total_killed_objects} killed objects")
        
        # Perform the actual save
        path = save_system.create_save_file(player_stats, world_data)
        if path:
            print(f"[SaveGame] SUCCESS: Saved complete game state ({reason}) -> {path}")
            
            # No need to reload weapon proficiency after save - it should already be current in memory
            print(f"[SaveGame] Weapon proficiency preserved in memory after save")
            
            return path
        else:
            print(f"[SaveGame] ERROR: Failed to save for reason: {reason}")
            return None
            
    except Exception as e:
        print(f"[SaveGame] ERROR during save ({reason}): {e}")
        import traceback
        traceback.print_exc()
        return None

def perform_auto_save(reason="interval"):
    """Legacy wrapper for auto-save - now uses unified save function"""
    return create_complete_save(reason)

# Make create_complete_save accessible to pause menu for save and exit functionality
# This ensures the function is available in the global namespace when running as main
def get_create_complete_save_function():
    """Helper function to provide access to create_complete_save for external modules"""
    return create_complete_save

# Add global reference for pause menu access
if __name__ == "__main__" or True:  # Always make it available
    # Make the save function accessible to the pause menu
    import sys
    if hasattr(sys.modules.get('__main__'), '__dict__'):
        sys.modules['__main__'].__dict__['create_complete_save'] = create_complete_save

def Reserve_Logic(dt):
    global reserve_logic_timer
    # Safety check: if pause menu has been visible for too long without user input, reset it
    if pause_menu.visible and hasattr(pause_menu, 'last_interaction_time'):
        current_time = pygame.time.get_ticks()
        if current_time - pause_menu.last_interaction_time > 30000:  # 30 seconds
            print(f"[Reserve_Logic] SAFETY: Resetting stuck pause menu after 30 seconds")
            pause_menu.visible = False
    
    # Only block if menu is open
    if not pause_menu.visible:
        reserve_logic_timer += dt / 1000.0
        if reserve_logic_timer >= 1:
            reserve_logic_timer = 0.0
            # Check if REGENERATION is below max
            if player_stats.regen < player_stats.max_regen and player_stats.reserve > 0:
                transfer = min(int(player_stats.max_regen/10), player_stats.max_regen - player_stats.regen, player_stats.reserve)
                if transfer > 0:
                    player_stats.regen += transfer
                    player_stats.reserve -= transfer
                    print(f"[Reserve_Logic] +{transfer} REGENERATION, -{transfer} RESERVE")
    else:
        # Debug: print when regen is blocked
        if reserve_logic_timer == 0:  # Only print once to avoid spam
            print(f"[Reserve_Logic] BLOCKED - pause_menu.visible = {pause_menu.visible}")
            reserve_logic_timer = 0.1  # Small value to prevent immediate re-trigger

while True:
    # Calculate delta time in milliseconds
    dt = clock.tick(60)  # 60 FPS like in V02

    # Check for fullscreen setting changes from pause menu
    if pause_menu:
        current_fullscreen = pause_menu.game_settings.get('fullscreen', False)
        if current_fullscreen != game_settings.get('fullscreen', False):
            print(f"[Overworld] Fullscreen setting changed from {game_settings.get('fullscreen', False)} to {current_fullscreen}")
            game_settings['fullscreen'] = current_fullscreen
            screen = apply_fullscreen_setting(game_settings, screen_width, screen_height)
            # Update pause menu screen dimensions if fullscreen changed
            if current_fullscreen:
                # Get actual fullscreen resolution
                info = pygame.display.Info()
                pause_menu.update_dimensions(info.current_w, info.current_h)
            else:
                pause_menu.update_dimensions(screen_width, screen_height)
        
        # Check for music volume changes from pause menu
        current_music_volume = pause_menu.game_settings.get('music_volume', 0.7)
        if current_music_volume != game_settings.get('music_volume', 0.7):
            print(f"[Overworld] Music volume setting changed from {game_settings.get('music_volume', 0.7)} to {current_music_volume}")
            game_settings['music_volume'] = current_music_volume
            set_music_volume(current_music_volume)
            print(f"[Overworld] Music volume updated to {music_volume}")

    # --- Auto-save interval check ---
    try:
        _auto_save_elapsed += dt
        # Debug auto-save timing every 10 seconds
        if int(_auto_save_elapsed) % 10000 == 0 and int(_auto_save_elapsed) > 0:
            remaining = AUTO_SAVE_INTERVAL_MS - _auto_save_elapsed
            print(f"[AutoSave] Timer: {_auto_save_elapsed:.0f}ms elapsed, {remaining:.0f}ms remaining until next auto-save")
        
        if _auto_save_elapsed >= AUTO_SAVE_INTERVAL_MS:
            _auto_save_elapsed = 0
            perform_auto_save("interval")
    except Exception as e:
        print(f"[AutoSave] Timer error: {e}")
        pass
    
    # Check if pause menu wants to exit to main menu
    if hasattr(pause_menu, 'should_exit_to_main_menu') and pause_menu.should_exit_to_main_menu:
        print(f"[Overworld] EXIT SIGNAL DETECTED! should_exit_to_main_menu = {pause_menu.should_exit_to_main_menu}")
        print("[Overworld] Exiting to main menu...")
        
        # Ensure save is complete before exiting
        pygame.time.wait(100)  # Brief delay to ensure save operations complete
        
        # Import and launch main menu instead of closing the game
        import subprocess
        import os
        pygame.quit()
        
        # Launch main menu in new process with correct working directory
        # TEMPORARILY DISABLED TO PREVENT CONTINUOUS EXECUTION
        # main_menu_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Main_Menu.py")
        # main_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        # print(f"[Overworld] Main menu path: {main_menu_path}")
        # print(f"[Overworld] Working directory: {main_dir}")
        
        # try:
        #     subprocess.Popen([sys.executable, main_menu_path], cwd=main_dir)
        #     print("[Overworld] Main menu process started successfully")
        # except Exception as e:
        #     print(f"[Overworld] Error starting main menu: {e}")
        
        print("[Overworld] Auto-restart to Main Menu DISABLED to prevent continuous execution")
        
        sys.exit()

    # --- Update transition timer ---
    if is_transitioning:
        transition_timer += dt
        if transition_timer >= transition_duration:
            is_transitioning = False
            transition_timer = 0.0
            # Note: Keys will be re-enabled at the end of the main loop after rendering
            print(f"[DEBUG] Transition timer completed after {transition_duration}ms")
            
            # Only restart overworld music if it's not already playing
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.load(r"C:\Users\franc\Desktop\Afterdeath_RPG\Musics\Boney Rattle.MP3")
                    pygame.mixer.music.set_volume(music_volume)
                    pygame.mixer.music.play(-1)  # Loop forever
                    print(f"[MAP TRANSITION] Overworld music restarted at volume {music_volume}")
                except Exception as music_error:
                    print(f"[MAP TRANSITION] Failed to restart overworld music: {music_error}")
            else:
                print(f"[MAP TRANSITION] Overworld music is already playing, no restart needed")

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            # Skip all keyboard input during transitions
            if is_transitioning:
                continue
            # --- Pause menu toggle (ESC or Circle button) ---
            if event.key == pygame.K_ESCAPE:
                if not prompt_interaction.active:
                    # Only toggle pause if not in a submenu
                    if not game_paused or (game_paused and not pause_menu.in_system_menu and not pause_menu.in_regen_menu):
                        game_paused = not game_paused
                        continue  # Don't process other keys this frame
                # If prompt is active or in a submenu, let the menu handle it
            # --- Spacebar actions (SPACE or X button) ---
            if event.key == pygame.K_SPACE:
                if prompt_interaction.active:
                    prompt_interaction.advance()
                else:
                    handle_spacebar_facing_check(player, tmx_data)
            # --- Manual save key: S ---
            elif event.key == pygame.K_s:
                print("[DEBUG] Manual save triggered with S key")
                perform_auto_save("manual")
            # --- DEBUG: Give player 5 exp when 'E' is pressed ---
            elif event.key == pygame.K_e:
                Get_Exp(player_stats, 15)
                message_display.show_message(f"DEBUG: +15 EXP (now {player_stats.exp}/{player_stats.required_exp})", 1200)

        # --- CONTROLLER EVENT HANDLING ---
        elif event.type == pygame.JOYBUTTONDOWN:
            # Skip controller input during transitions
            if is_transitioning:
                continue
                
            # --- Pause menu toggle (Circle button) ---
            if is_controller_button_just_pressed(event, 'circle'):
                if not prompt_interaction.active:
                    # Only toggle pause if not in a submenu
                    if not game_paused or (game_paused and not pause_menu.in_system_menu and not pause_menu.in_regen_menu):
                        game_paused = not game_paused
                        continue
            
            # --- Spacebar actions (X button) ---
            elif is_controller_button_just_pressed(event, 'x'):
                if prompt_interaction.active:
                    prompt_interaction.advance()
                else:
                    handle_spacebar_facing_check(player, tmx_data)
            
            # --- Regeneration (R1 button) ---
            elif is_controller_button_just_pressed(event, 'r1'):
                if game_paused and not pause_menu.in_regen_menu:
                    pause_menu.enter_regen_menu()
        
        # --- CONTROLLER HAT (D-PAD) EVENT HANDLING ---
        elif event.type == pygame.JOYHATMOTION:
            # Skip controller input during transitions
            if is_transitioning:
                continue
            # D-pad events will be handled in menu systems

        # --- PAUSE MENU EVENT HANDLING ---
        if game_paused:
            # Only handle pause menu events while paused
            if event.type == pygame.KEYDOWN:
                if not pause_menu.in_regen_menu and event.key == pygame.K_r:
                    pause_menu.enter_regen_menu()
                elif pause_menu.in_regen_menu:
                    pause_menu.handle_regen_event(event)
                elif not pause_menu.in_regen_menu:
                    pause_menu.handle_menu_event(event)
            # Handle controller events for pause menu
            elif event.type == pygame.JOYBUTTONDOWN:
                if not pause_menu.in_regen_menu and is_controller_button_just_pressed(event, 'r1'):
                    pause_menu.enter_regen_menu()
                elif pause_menu.in_regen_menu:
                    pause_menu.handle_regen_event(event)
                elif not pause_menu.in_regen_menu:
                    pause_menu.handle_menu_event(event)
            # Handle controller D-pad for pause menu
            elif event.type == pygame.JOYHATMOTION:
                if pause_menu.in_regen_menu:
                    pause_menu.handle_regen_event(event)
                elif not pause_menu.in_regen_menu:
                    pause_menu.handle_menu_event(event)


    if game_paused:
        # Show the pause menu using the new function
        show_pause_menu(screen, pause_menu, dt)
        pygame.display.flip()
        
        # Check for exit signal again after processing pause menu
        if hasattr(pause_menu, 'should_exit_to_main_menu') and pause_menu.should_exit_to_main_menu:
            print(f"[Overworld] EXIT SIGNAL DETECTED IN PAUSE MENU! should_exit_to_main_menu = {pause_menu.should_exit_to_main_menu}")
            print("[Overworld] Exit signal detected during pause menu processing")
            # Ensure save is complete before exiting
            pygame.time.wait(100)
            
            # Import and launch main menu instead of closing the game
            import subprocess
            import os
            pygame.quit()
            
            # Launch main menu in new process with correct working directory
            main_menu_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Main_Menu.py")
            main_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            print(f"[Overworld] Main menu path: {main_menu_path}")
            print(f"[Overworld] Working directory: {main_dir}")
            
            try:
                subprocess.Popen([sys.executable, main_menu_path], cwd=main_dir)
                print("[Overworld] Main menu process started successfully")
            except Exception as e:
                print(f"[Overworld] Error starting main menu: {e}")
            
            sys.exit()
        
        continue

    # --- Prompt interaction: pause updates, but keep rendering ---
    if prompt_interaction.active:
        message_display.update(dt)
        # --- Rendering code ---
        screen.fill((0, 0, 0))
        margin = 2 * tmx_data.tilewidth
        cam_x = -camera.camera.x
        cam_y = -camera.camera.y
        cam_w = camera.width / camera.zoom_factor
        cam_h = camera.height / camera.zoom_factor
        camera_world_rect = pygame.Rect(cam_x - margin, cam_y - margin, cam_w + 2*margin, cam_h + 2*margin)
        if not hasattr(pygame, 'animated_tile_states'):
            pygame.animated_tile_states = {}
        current_time = pygame.time.get_ticks()
        for sprite in tile_group:
            if camera_world_rect.colliderect(sprite.rect):
                scaled_width = round(sprite.image.get_width() * camera.zoom_factor)
                scaled_height = round(sprite.image.get_height() * camera.zoom_factor)
                scaled_surface = pygame.transform.scale(sprite.image, (scaled_width, scaled_height))
                sprite_rect = camera.apply(sprite)
                blit_x = round(sprite_rect.x)
                blit_y = round(sprite_rect.y)
                screen.blit(scaled_surface, (blit_x, blit_y))
        render_objects = []
        current_image = player.image
        hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
            player.pos.x - current_image.get_width()//2,
            player.pos.y - current_image.get_height()//2,
            current_image, tmx_data)
        player_hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
        player_depth_y = player_hitbox_rect.bottom
        scaled_player = pygame.transform.scale(player.image,
            (int(player.image.get_width() * camera.zoom_factor),
             int(player.image.get_height() * camera.zoom_factor)))
        player_rect = camera.apply(player)
        render_objects.append({
            'type': 'player',
            'depth_y': player_depth_y,
            'surface': scaled_player,
            'rect': player_rect
        })
        for obj_sprite in object_group:
            if camera_world_rect.colliderect(obj_sprite.rect):
                if isinstance(obj_sprite, NPC):
                    obj_image = obj_sprite.image
                    obj_hitbox_x, obj_hitbox_y, obj_hitbox_width, obj_hitbox_height = get_character_hitbox(
                        obj_sprite.pos.x - obj_image.get_width()//2,
                        obj_sprite.pos.y - obj_image.get_height()//2,
                        obj_image, tmx_data)
                    obj_depth_y = obj_hitbox_y + obj_hitbox_height
                else:
                    obj_depth_y = obj_sprite.rect.bottom - 5
                scaled_surface = pygame.transform.scale(obj_sprite.image,
                    (int(obj_sprite.image.get_width() * camera.zoom_factor),
                     int(obj_sprite.image.get_height() * camera.zoom_factor)))
                sprite_rect = camera.apply(obj_sprite)
                render_objects.append({
                    'type': 'object',
                    'depth_y': obj_depth_y,
                    'surface': scaled_surface,
                    'rect': sprite_rect
                })
        render_objects.sort(key=lambda obj: obj['depth_y'])
        for obj in render_objects:
            screen.blit(obj['surface'], (obj['rect'].x, obj['rect'].y))
        draw_hp_bar(screen, player, player_stats.hp, player_stats.max_hp)
        if player_stats.stamina < player_stats.max_stamina:
            draw_stamina_bar(screen, player)
        message_display.draw(screen)
        
        # --- Draw transition status indicator ---
        if is_transitioning:
            remaining_time = (transition_duration - transition_timer) / 1000.0
            font = pygame.font.Font(None, 36)
            text = font.render(f"Loading new area... {remaining_time:.1f}s", True, (255, 255, 255))
            text_rect = text.get_rect(center=(screen_width // 2, screen_height - 50))
            pygame.draw.rect(screen, (0, 0, 0, 180), text_rect.inflate(20, 10))
            screen.blit(text, text_rect)
        
        if filter_surface is not None:
            screen.blit(filter_surface, (0, 0))
        if vignette_surface is not None:
            screen.blit(vignette_surface, (0, 0))
        pygame.display.flip()
        continue

    # --- Reserve Logic: transfer reserve points when menu is not open ---
    Reserve_Logic(dt)
    # --- Automatically trigger level up if exp >= required ---
    Level_Up(player_stats)

    # Handle player movement and animation - use safe key system during transitions
    keys = get_safe_keys()
    player.update(keys, collision_tiles, tmx_data, dt)

    # Check if any enemy touches the player
    enemy_touches_player(player, object_group, player_stats)

    # --- Bone_Grass tile detection with fixed damage ---
    on_bone_grass, is_moving, is_running = is_player_on_bone_grass(player, tmx_data)
    damage = 0.1 if on_bone_grass and is_moving else 0
    if damage > 0:
        player_stats.take_damage(damage, part='legs')
        print(f"[DEBUG] Bone grass damage dealt to legs: {damage:.3f}")
        now = time.time()
        if bone_grass_sound is not None:
            if now - last_bone_grass_sound_time >= 0.3:
                bone_grass_sound.play()
                last_bone_grass_sound_time = now
        else:
            print("[DEBUG] Bone grass sound not loaded, cannot play sound.")

    # --- Event Trigger Check ---
    # Get player hitbox (same as collision)
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    player_hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)

    for game_event in event_list:
        if not game_event.triggered and player_hitbox.colliderect(game_event.rect):
            event_scripts = getattr(map_config.Config_Data, 'EVENT_SCRIPTS', {})
            event_name = game_event.name.lower()
            if event_name in Map_Roadmap.MAP_TRANSITIONS:
                new_map_config, new_spawnpoint = Map_Roadmap.MAP_TRANSITIONS[event_name]
                print(f"[MAP TRANSITION] Event '{event_name}' triggered: switching to {new_map_config.__name__} at {new_spawnpoint}")
                
                # --- Start transition timer and disable keys ---
                is_transitioning = True
                transition_timer = 0.0
                disable_keys()
                
                fade_to_black(screen, duration=200)
                map_config = new_map_config
                try:
                    current_map_name = getattr(map_config.Config_Data, 'MAP_NAME', current_map_name)
                    print(f"[Overworld] Updated current_map_name after transition: {current_map_name}")
                except Exception as e:
                    print(f"[Overworld] Could not update current_map_name: {e}")
                # Perform autosave after completing map transition setup (position already updated later)
                try:
                    perform_auto_save("map_change")
                except Exception as e:
                    print(f"[Overworld] Autosave after map change failed: {e}")
                selected_spawnpoint = new_spawnpoint
                tmx_data = load_pygame(map_config.Config_Data.TMX_PATH)
                map_width = tmx_data.width * tmx_data.tilewidth
                map_height = tmx_data.height * tmx_data.tileheight
                camera.set_map_size(map_width, map_height)
                spawn_position = find_spawn_point(tmx_data, selected_spawnpoint)
                player.pos = pygame.math.Vector2(spawn_position)
                player.rect.center = player.pos
                if getattr(map_config.Config_Data, 'HAS_FILTER', False):
                    filter_opacity = getattr(map_config.Config_Data, 'FILTER_OPACITY', 80)
                    filter_color = getattr(map_config.Config_Data, 'FILTER_COLOR', (0,0,0))
                    filter_surface = create_map_filter(screen_width, screen_height, filter_opacity, filter_color)
                else:
                    filter_surface = None
                if getattr(map_config.Config_Data, 'HAS_VIGNETTE', False):
                    vignette_surface = create_vignette(screen_width, screen_height)
                else:
                    vignette_surface = None
                tile_group.empty()
                object_group.empty()
                player_group.empty()
                # Clear animated tile states for new map
                if hasattr(pygame, 'animated_tile_states'):
                    pygame.animated_tile_states.clear()
                # --- Clear and reload collision tiles for new map ---
                collision_tiles.clear()
                for layer in tmx_data.layers:
                    if hasattr(layer, 'data') and ( 'collision' in layer.name.lower() or not layer.visible):
                        for x, y, gid in layer:
                            if gid:
                                collision_tiles.add((x, y))
                # Only render visible layers
                for layer in tmx_data.layers:
                    if hasattr(layer, 'data') and layer.visible:
                        for x, y, surface in layer.tiles():
                            if surface:
                                pos = (x * tmx_data.tilewidth, y * tmx_data.tileheight)
                                Tile(pos=pos, surf=surface, groups=tile_group)
                
                # Load objects with full transformations and animations
                # First, place enemies at map object positions using ENEMIES_DATA and create_npc_from_data with world state checking
                killed_enemies_list = WORLD_STATE["maps"].get(current_map_name, {}).get("killed_enemies", [])
                print(f"[MAP TRANSITION] Enemy spawning check - current_map: '{current_map_name}'")
                print(f"[MAP TRANSITION] killed_enemies_list for this map: {killed_enemies_list}")
                
                for obj in tmx_data.objects:
                    # Only place enemies for objects of class 'Enemy' and matching name
                    if getattr(obj, 'type', None) == 'Enemy' and hasattr(obj, 'name'):
                        enemy_name = obj.name
                        spawn_x, spawn_y = obj.x, obj.y
                        
                        # Check if this enemy was killed at this spawn location
                        is_killed = False
                        killed_enemy = None
                        for killed in killed_enemies_list:
                            if (killed["name"] == enemy_name and 
                                killed["spawn_x"] == spawn_x and 
                                killed["spawn_y"] == spawn_y):
                                is_killed = True
                                killed_enemy = killed
                                break
                        
                        if is_killed:
                            # Spawn corpse at death location instead of live enemy
                            print(f"[MAP TRANSITION] Spawning corpse for killed enemy '{enemy_name}' at death coords ({killed_enemy['death_x']}, {killed_enemy['death_y']})")
                            
                            # Load death image
                            death_image = None
                            enemy_data = get_enemy_data_by_name(enemy_name)
                            if enemy_data:
                                death_image_path = enemy_data.get("death_image_path")
                                if death_image_path:
                                    try:
                                        death_image = pygame.image.load(death_image_path).convert_alpha()
                                    except Exception as e:
                                        print(f"[MAP TRANSITION] Could not load death image: {e}")
                            
                            if death_image is None:
                                death_image = pygame.Surface((32,32), pygame.SRCALPHA)
                                death_image.fill((80, 80, 80, 180))  # Gray fallback
                            
                            # Create corpse at death location
                            try:
                                corpse_obj = Corpse((killed_enemy['death_x'], killed_enemy['death_y']), death_image, enemy_name)
                                # Store unique corpse ID based on death coordinates for interaction tracking (legacy)
                                corpse_obj.unique_corpse_id = f"{enemy_name}_{int(killed_enemy['death_x'])}_{int(killed_enemy['death_y'])}"
                                # NEW: Set interaction flag based on the killed enemy's interaction count
                                corpse_interactions = killed_enemy.get('interactions', 0)
                                if corpse_interactions > 0:
                                    corpse_obj.corpse_interacted = True
                                    print(f"[MAP TRANSITION] Corpse marked as already interacted (interactions: {corpse_interactions})")
                                else:
                                    corpse_obj.corpse_interacted = False
                                    print(f"[MAP TRANSITION] Corpse ready for first interaction")
                                print(f"[MAP TRANSITION] Corpse spawned for {enemy_name} with ID: {corpse_obj.unique_corpse_id}")
                            except Exception as e:
                                print(f"[MAP TRANSITION] Error creating corpse: {e}")
                        else:
                            # Spawn live enemy normally
                            enemy_data = get_enemy_data_by_name(obj.name)
                            if enemy_data:
                                enemy_npc = create_npc_from_data(enemy_data, (obj.x, obj.y), object_group)
                                # Store spawn coordinates for future reference
                                enemy_npc.spawn_x = obj.x
                                enemy_npc.spawn_y = obj.y
                                print(f"[MAP TRANSITION] Enemy NPC created: {enemy_npc.name} at {enemy_npc.pos}")
                
                # Then load other objects with full transformations and animations
                killed_objects_list = WORLD_STATE["maps"].get(current_map_name, {}).get("killed_objects", [])
                print(f"[MAP TRANSITION] Object loading check - killed_objects_list: {killed_objects_list}")
                
                # Initialize used_records set for map transitions
                used_object_records = set()
                
                for obj in tmx_data.objects:
                    # Skip objects of class 'Enemy' (already handled above)
                    if getattr(obj, 'type', None) == 'Enemy':
                        continue
                    
                    # Debug: print all objects with their properties
                    obj_name = getattr(obj, 'name', 'NO_NAME')
                    obj_type = getattr(obj, 'type', 'NO_TYPE')
                    has_image = hasattr(obj, 'image') and obj.image is not None
                    
                    # Check if this object was killed/removed using proximity matching
                    killed_obj_record = is_object_killed_nearby(obj_name, obj.x, obj.y, killed_objects_list, used_records=used_object_records)
                    
                    if killed_obj_record:
                        print(f"[MAP TRANSITION] Skipping killed object '{obj_name}' at ({obj.x}, {obj.y}) - killed at ({killed_obj_record['x']}, {killed_obj_record['y']})")
                        continue
                    
                    if obj.image:
                        # Apply all transformations (rotation, flipping, scaling) from TMX editor
                        transform_result = apply_object_transformations(obj)
                        if transform_result is None:
                            continue  # Skip if transformation failed
                        
                        # Extract surface and offsets from the transformation result
                        surf = transform_result['surface']
                        offset_x = transform_result['offset_x']
                        offset_y = transform_result['offset_y']
                        
                        # Apply the calculated offset to the position to match Tiled's behavior
                        pos = (obj.x + offset_x, obj.y + offset_y)
                        obj_tile = Tile(pos=pos, surf=surf, groups=object_group)
                        obj_tile.depth_y = obj.y + obj.height
                        # Add name to the tile sprite for interaction
                        obj_tile.name = obj_name
                        
                        # Store GID for tile objects (needed for animation)
                        obj_gid = getattr(obj, 'gid', None)
                        if obj_gid:
                            obj_tile.gid = obj_gid
                            # Check if this tile has animation frames
                            tile_frames = None
                            if hasattr(tmx_data, 'get_tile_frames_by_gid'):
                                tile_frames = tmx_data.get_tile_frames_by_gid(obj_gid)
                            elif hasattr(tmx_data, 'tile_properties') and obj_gid in tmx_data.tile_properties:
                                tile_frames = tmx_data.tile_properties[obj_gid].get('frames', None)
                            
                            if tile_frames and isinstance(tile_frames, list) and len(tile_frames) > 0:
                                obj_tile.is_animated = True
                                obj_tile.animation_frames = tile_frames
                                print(f"[DEBUG] Added animated tile object '{obj_name}' with {len(tile_frames)} frames")
                            else:
                                obj_tile.is_animated = False
                        else:
                            obj_tile.is_animated = False
                            
                        print(f"[DEBUG] Added visible object '{obj_name}' to object_group with offset ({offset_x:.1f}, {offset_y:.1f})")
                    else:
                        # For invisible objects, we could add them as invisible sprites to object_group too
                        # This would allow uniform interaction handling
                        if obj_name != 'NO_NAME':  # Only add named invisible objects
                            # Create an invisible sprite with 1x1 size
                            invisible_surf = pygame.Surface((getattr(obj, 'width', 16), getattr(obj, 'height', 16)), pygame.SRCALPHA)
                            pos = (obj.x, obj.y)
                            obj_tile = Tile(pos=pos, surf=invisible_surf, groups=object_group)
                            obj_tile.depth_y = obj.y + getattr(obj, 'height', 16)
                            obj_tile.name = obj_name
                            print(f"[DEBUG] Added invisible object '{obj_name}' to object_group as transparent sprite")
                event_list.clear()
                for obj in tmx_data.objects:
                    if hasattr(obj, 'name') and obj.name and 'event' in obj.name.lower():
                        event_list.append(GameEvent(obj.name, obj.x, obj.y, getattr(obj, 'width', 0), getattr(obj, 'height', 0)))
                map_name_caps = getattr(new_map_config.Config_Data, 'NAME', new_map_config.__name__).upper()
                pygame.time.wait(500)  # Wait 0.5s before showing area name
                message_display.show_message(map_name_caps, 4500)
                game_event.triggered = True
            elif event_name in event_scripts:
                script = event_scripts[event_name]
                msg = script.get('message', '')
                duration = script.get('duration', 3500)
                message_display.show_message(msg, duration)
                game_event.triggered = True

    # Update message display
    message_display.update(dt)

    # Music volume display timer
    # Keep player within map bounds using full sprite dimensions for boundary check
    # Keep player within map bounds using hitbox position and size - skip during transitions
    if not is_transitioning:
        current_image = player.image
        hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
        # Calculate the offset from player.pos to hitbox center
        hitbox_center_x = hitbox_x + hitbox_width // 2
        hitbox_center_y = hitbox_y + hitbox_height // 2
        offset_x = player.pos.x - hitbox_center_x
        offset_y = player.pos.y - hitbox_center_y
        # Clamp hitbox center to map bounds
        min_x = hitbox_width // 2
        max_x = map_width - (hitbox_width // 2)
        min_y = hitbox_height // 2
        max_y = map_height - (hitbox_height // 2)
        new_hitbox_center_x = max(min_x, min(player.pos.x - offset_x, max_x))
        new_hitbox_center_y = max(min_y, min(player.pos.y - offset_y, max_y))
        # Update player.pos so that hitbox stays within bounds
        player.pos.x = new_hitbox_center_x + offset_x
        player.pos.y = new_hitbox_center_y + offset_y
        player.rect.center = player.pos

    # Update camera to follow player with smooth movement
    camera.update(player.pos, dt)

    # Clear screen
    screen.fill((0, 0, 0))

    # --- Dynamic Rendering: Only draw tiles/objects in camera view plus margin ---
    margin = 2 * tmx_data.tilewidth  # 2 tiles margin around camera
    # Camera world rect (unzoomed)
    cam_x = -camera.camera.x
    cam_y = -camera.camera.y
    cam_w = camera.width / camera.zoom_factor
    cam_h = camera.height / camera.zoom_factor
    camera_world_rect = pygame.Rect(cam_x - margin, cam_y - margin, cam_w + 2*margin, cam_h + 2*margin)

    # Step 1: Draw visible tile sprites, supporting animated tiles
    # --- Animated tile state tracking ---
    if not hasattr(pygame, 'animated_tile_states'):
        pygame.animated_tile_states = {}
    current_time = pygame.time.get_ticks()
    
    for sprite in tile_group:
        if camera_world_rect.colliderect(sprite.rect):
            # Detect if this tile is animated (using pytmx's tile property)
            tile_gid = None
            tile_frames = None
            # Try to get the tile GID and frames from the sprite
            # We need to find the corresponding tile in tmx_data
            # We'll use the sprite's rect position to infer tile coordinates
            tile_x = sprite.rect.x // tmx_data.tilewidth
            tile_y = sprite.rect.y // tmx_data.tileheight
            found_tile = False
            layer_name = None
            for layer in tmx_data.layers:
                if hasattr(layer, 'data'):
                    try:
                        gid = layer.data[tile_y][tile_x]
                        if gid:
                            tile = tmx_data.get_tile_image_by_gid(gid)
                            if tile == sprite.image:
                                tile_gid = gid
                                layer_name = layer.name
                                # pytmx stores animation frames in tmx_data.tile_properties
                                tile_obj = tmx_data.get_tile_properties_by_gid(gid)
                                if hasattr(tmx_data, 'get_tile_frames_by_gid'):
                                    tile_frames = tmx_data.get_tile_frames_by_gid(gid)
                                elif hasattr(tmx_data, 'tile_properties') and gid in tmx_data.tile_properties:
                                    tile_frames = tmx_data.tile_properties[gid].get('frames', None)
                                found_tile = True
                                break
                    except Exception as e:
                        continue
                if found_tile:
                    break
            # If animated tile detected, handle animation
            if tile_frames and isinstance(tile_frames, list) and len(tile_frames) > 0:
                # For Bone_Grass layer, only animate if player is within 2 tiles distance
                should_animate = True
                if layer_name and "Bone_Grass" in layer_name:
                    # Calculate distance from player center to tile center
                    tile_center_x = tile_x * tmx_data.tilewidth + tmx_data.tilewidth // 2
                    tile_center_y = tile_y * tmx_data.tileheight + tmx_data.tileheight // 2
                    player_tile_x = player.pos.x / tmx_data.tilewidth
                    player_tile_y = player.pos.y / tmx_data.tileheight
                    distance_in_tiles = max(abs(player_tile_x - tile_x), abs(player_tile_y - tile_y))
                    should_animate = distance_in_tiles <= 2
                
                if should_animate:
                    # Track animation state per tile position
                    key = (tile_x, tile_y)
                    state = pygame.animated_tile_states.get(key)
                    if not state:
                        state = {'frame': 0, 'last_time': current_time}
                        pygame.animated_tile_states[key] = state
                    
                    # Bounds checking for frame index
                    if state['frame'] >= len(tile_frames):
                        state['frame'] = 0
                    
                    frame_duration = tile_frames[state['frame']][1] if len(tile_frames[state['frame']]) > 1 else 100
                    if current_time - state['last_time'] >= frame_duration:
                        state['frame'] = (state['frame'] + 1) % len(tile_frames)
                        state['last_time'] = current_time
                    frame_gid = tile_frames[state['frame']][0]
                    frame_image = tmx_data.get_tile_image_by_gid(frame_gid)
                    if frame_image:
                        scaled_width = round(frame_image.get_width() * camera.zoom_factor)
                        scaled_height = round(frame_image.get_height() * camera.zoom_factor)
                        scaled_surface = pygame.transform.scale(frame_image, (scaled_width, scaled_height))
                        sprite_rect = camera.apply(sprite)
                        blit_x = round(sprite_rect.x)
                        blit_y = round(sprite_rect.y)
                        screen.blit(scaled_surface, (blit_x, blit_y))
                    else:
                        # Fallback: draw static image
                        scaled_width = round(sprite.image.get_width() * camera.zoom_factor)
                        scaled_height = round(sprite.image.get_height() * camera.zoom_factor)
                        scaled_surface = pygame.transform.scale(sprite.image, (scaled_width, scaled_height))
                        sprite_rect = camera.apply(sprite)
                        blit_x = round(sprite_rect.x)
                        blit_y = round(sprite_rect.y)
                        screen.blit(scaled_surface, (blit_x, blit_y))
                else:
                    # Animation disabled (e.g., Bone_Grass too far from player) - draw static image
                    scaled_width = round(sprite.image.get_width() * camera.zoom_factor)
                    scaled_height = round(sprite.image.get_height() * camera.zoom_factor)
                    scaled_surface = pygame.transform.scale(sprite.image, (scaled_width, scaled_height))
                    sprite_rect = camera.apply(sprite)
                    blit_x = round(sprite_rect.x)
                    blit_y = round(sprite_rect.y)
                    screen.blit(scaled_surface, (blit_x, blit_y))
            else:
                # Normal static tile rendering
                scaled_width = round(sprite.image.get_width() * camera.zoom_factor)
                scaled_height = round(sprite.image.get_height() * camera.zoom_factor)
                scaled_surface = pygame.transform.scale(sprite.image, (scaled_width, scaled_height))
                sprite_rect = camera.apply(sprite)
                blit_x = round(sprite_rect.x)
                blit_y = round(sprite_rect.y)
                screen.blit(scaled_surface, (blit_x, blit_y))

    # Step 2: Depth-sorted rendering for player and visible objects
    render_objects = []
    corpse_count = 0
    for obj in object_group:
        if hasattr(obj, 'name') and obj.name and obj.name.endswith('_corpse'):
            corpse_count += 1

    # Add player to render list (always use hitbox bottom)
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    player_hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    player_depth_y = player_hitbox_rect.bottom
    scaled_player = pygame.transform.scale(player.image,
        (int(player.image.get_width() * camera.zoom_factor),
         int(player.image.get_height() * camera.zoom_factor)))
    player_rect = camera.apply(player)
    render_objects.append({
        'type': 'player',
        'depth_y': player_depth_y,
        'surface': scaled_player,
        'rect': player_rect
    })

    # Add only visible objects to render list
    for obj_sprite in object_group:
        # Only draw if object is in camera view + margin
        if camera_world_rect.colliderect(obj_sprite.rect):
            if isinstance(obj_sprite, NPC):
                obj_sprite.update(player, collision_tiles, tmx_data)
                obj_image = obj_sprite.image
                obj_hitbox_x, obj_hitbox_y, obj_hitbox_width, obj_hitbox_height = get_character_hitbox(
                    obj_sprite.pos.x - obj_image.get_width()//2,
                    obj_sprite.pos.y - obj_image.get_height()//2,
                    obj_image, tmx_data)
                obj_depth_y = obj_hitbox_y + obj_hitbox_height
                
                # Use static image for NPCs (they have their own animation system)
                scaled_surface = pygame.transform.scale(obj_sprite.image,
                    (int(obj_sprite.image.get_width() * camera.zoom_factor),
                     int(obj_sprite.image.get_height() * camera.zoom_factor)))
            else:
                # Add 24 pixels to depth for non-NPC objects
                obj_depth_y = obj_sprite.rect.bottom - 5
                
                # Check if this is an animated tile object
                if hasattr(obj_sprite, 'is_animated') and obj_sprite.is_animated:
                    # Handle animated tile objects
                    key = f"obj_{id(obj_sprite)}"  # Unique key for each object instance
                    state = pygame.animated_tile_states.get(key)
                    if not state:
                        state = {'frame': 0, 'last_time': current_time}
                        pygame.animated_tile_states[key] = state
                        
                    # Get current frame duration
                    current_frame = obj_sprite.animation_frames[state['frame']]
                    frame_duration = current_frame[1] if len(current_frame) > 1 else 100
                    
                    # Check if it's time to advance to next frame
                    if current_time - state['last_time'] >= frame_duration:
                        state['frame'] = (state['frame'] + 1) % len(obj_sprite.animation_frames)
                        state['last_time'] = current_time
                        
                    # Get the current frame's GID and image
                    frame_gid = obj_sprite.animation_frames[state['frame']][0]
                    frame_image = tmx_data.get_tile_image_by_gid(frame_gid)
                    
                    if frame_image:
                        # Apply the same transformations that were applied to the original object
                        # We need to create a temporary object with the frame image to apply transformations
                        class TempObj:
                            def __init__(self, original_obj, frame_img):
                                # Copy all transformation properties from original object
                                for attr in ['rotation', 'width', 'height', 'flipped_horizontally', 
                                           'flipped_vertically', 'flipped_diagonally', 'properties']:
                                    if hasattr(original_obj, attr):
                                        setattr(self, attr, getattr(original_obj, attr))
                                self.image = frame_img
                                
                        # Find the original TMX object that created this sprite
                        temp_obj = None
                        for tmx_obj in tmx_data.objects:
                            if (getattr(tmx_obj, 'name', 'NO_NAME') == getattr(obj_sprite, 'name', 'NO_NAME') and
                                hasattr(tmx_obj, 'gid') and tmx_obj.gid == getattr(obj_sprite, 'gid', None)):
                                temp_obj = TempObj(tmx_obj, frame_image)
                                break
                                
                        if temp_obj:
                            # Apply transformations to the current frame
                            transform_result = apply_object_transformations(temp_obj)
                            if transform_result:
                                transformed_surface = transform_result['surface']
                            else:
                                transformed_surface = frame_image
                        else:
                            transformed_surface = frame_image
                            
                        scaled_surface = pygame.transform.scale(transformed_surface,
                            (int(transformed_surface.get_width() * camera.zoom_factor),
                             int(transformed_surface.get_height() * camera.zoom_factor)))
                    else:
                        # Fallback to static image if frame image not found
                        scaled_surface = pygame.transform.scale(obj_sprite.image,
                            (int(obj_sprite.image.get_width() * camera.zoom_factor),
                             int(obj_sprite.image.get_height() * camera.zoom_factor)))
                else:
                    # Static object - use original image
                    scaled_surface = pygame.transform.scale(obj_sprite.image,
                        (int(obj_sprite.image.get_width() * camera.zoom_factor),
                         int(obj_sprite.image.get_height() * camera.zoom_factor)))

            sprite_rect = camera.apply(obj_sprite)
            render_objects.append({
                'type': 'object',
                'depth_y': obj_depth_y,
                'surface': scaled_surface,
                'rect': sprite_rect
            })

    # Sort by depth_y and render
    render_objects.sort(key=lambda obj: obj['depth_y'])
    for obj in render_objects:
        screen.blit(obj['surface'], (obj['rect'].x, obj['rect'].y))

    # Step 3: Draw UI elements (message display) on top of everything
    draw_hp_bar(screen, player, player_stats.hp, player_stats.max_hp)
    if player_stats.stamina < player_stats.max_stamina:
        draw_stamina_bar(screen, player)
    message_display.draw(screen)

    # --- Draw transition status indicator ---
    if is_transitioning:
        remaining_time = (transition_duration - transition_timer) / 1000.0
        font = pygame.font.Font(None, 36)
        text = font.render(f"Loading new area... {remaining_time:.1f}s", True, (255, 255, 255))
        text_rect = text.get_rect(center=(screen_width // 2, screen_height - 50))
        pygame.draw.rect(screen, (0, 0, 0, 180), text_rect.inflate(20, 10))
        screen.blit(text, text_rect)

    # Draw player hitbox as a semitransparent red rectangle
    # (Disabled: make hitbox invisible)
    # current_image = player.image
    # hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
    #     player.pos.x - current_image.get_width()//2,
    #     player.pos.y - current_image.get_height()//2,
    #     current_image, tmx_data)
    # Convert world coordinates to screen coordinates using camera
    # hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    # screen_hitbox_rect = camera.apply_rect(hitbox_rect)
    # hitbox_surface = pygame.Surface((screen_hitbox_rect.width, screen_hitbox_rect.height), pygame.SRCALPHA)
    # hitbox_surface.fill((255, 0, 0, 120))  # Red, alpha=120
    # screen.blit(hitbox_surface, (screen_hitbox_rect.x, screen_hitbox_rect.y))

    # --- Ambient Occlusion Vignette Overlay (precomputed) ---

    # --- Map Filter Overlay (precomputed) ---
    if filter_surface is not None:
        screen.blit(filter_surface, (0, 0))
    # --- Ambient Occlusion Vignette Overlay (precomputed) ---
    if vignette_surface is not None:
        screen.blit(vignette_surface, (0, 0))

    pygame.display.flip()
    
    # --- Re-enable keys at the end of the loop after all rendering is complete ---
    # This ensures everything is loaded and displayed before allowing input
    if not is_transitioning and keys_disabled:
        enable_keys()