"""
Comprehensive Save System for Afterdeath RPG
Handles saving and loading all game state including:
- Player stats, position, inventory, equipment
- Map states, enemy states, interaction states
- Game settings and progress
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import tempfile

class SaveSystem:
    def __init__(self):
        # Create saves directory if it doesn't exist
        # Use absolute path to ensure it works from any working directory
        script_dir = Path(__file__).parent
        self.saves_dir = script_dir / "saves"
        self.saves_dir.mkdir(exist_ok=True)
        
        # Save file template
        self.save_template = {
            # Increment version when save structure changes
            "version": "1.2",
            "created_at": "",
            "last_saved": "",
            "play_time_seconds": 0,
            "player": {
                "name": "",
                "species": "",
                "level": 1,
                "exp": 0,
                "gif_path": "",
                "sprite_path": "",
                "stats": {
                    "hp": 100,
                    "max_hp": 100,
                    "regen": 50,
                    "max_regen": 50,
                    "reserve": 30,
                    "max_reserve": 30,
                    "stamina": 100,
                    "max_stamina": 100,
                    "head_hp": 20,
                    "max_head_hp": 20,
                    "body_hp": 40,
                    "max_body_hp": 40,
                    "right_arm_hp": 15,
                    "max_right_arm_hp": 15,
                    "left_arm_hp": 15,
                    "max_left_arm_hp": 15,
                    "right_leg_hp": 20,
                    "max_right_leg_hp": 20,
                    "left_leg_hp": 20,
                    "max_left_leg_hp": 20,
                    "extral_limbs_hp": 0,
                    "max_extral_limbs_hp": 0,
                    "evo_points_hp": 0,
                    "evo_points_regen": 0,
                    "evo_points_stamina": 0,
                    "evo_points_reserve": 0,
                    "evo_points_strength": 0,
                    "evo_points_dexterity": 0,
                    "evo_points_special": 0,
                    "evo_points_speed": 0
                },
                "position": {
                    "x": 0,
                    "y": 0,
                    "current_map": "foresta_dorsale_sud"
                },
                "equipment": {},
                "items": {},  # Usable items (MISC/FOOD/KEY)
                "weapon_proficiencies": {},
                "custom_moves": [],  # Character-specific custom moves
                "memory_skills": {
                    "equipped": [],  # List of equipped memory skill IDs
                    "available_memory_points": 10,  # Total memory points available
                    "skill_states": {}  # Individual skill states/progress
                }
            },
            "world_state": {
                "explored_maps": [],  # List of explored map names
                "maps": {}  # map_name: { "killed_enemies": [{name, spawn_x, spawn_y, death_x, death_y}], "killed_objects": [{name, x, y}] }
            },
            "game_settings": {
                "music_volume": 0.7,
                "sfx_volume": 0.8,
                "fullscreen": False
            }
        }
    
    def find_existing_save(self, character_name):
        """Find existing save file for a character"""
        try:
            # Collect all save files for this character
            candidate_files = list(self.saves_dir.glob(f"save_{character_name}_*.json"))
            if not candidate_files:
                return None
            # Pick the most recently modified file (not arbitrary first)
            latest = max(candidate_files, key=lambda p: p.stat().st_mtime)
            print(f"[SaveSystem] Located existing save candidates: {[p.name for p in candidate_files]}")
            print(f"[SaveSystem] Using latest existing save: {latest.name}")
            return str(latest)
        except Exception as e:
            print(f"[SaveSystem] Error finding existing save: {e}")
            return None
    
    def create_save_file(self, player_stats, world_data=None, game_start_time=None):
        """Create or update save file with current game state"""
        try:
            # Look for existing save file for this character
            existing_save = self.find_existing_save(player_stats.name)
            # Also gather all existing saves for cleanup AFTER writing
            all_existing = list(self.saves_dir.glob(f"save_{player_stats.name}_*.json"))
            
            if existing_save:
                # Overwrite existing save
                save_filename = os.path.basename(existing_save)
                save_path = Path(existing_save)
                print(f"[SaveSystem] Overwriting existing save: {save_filename}")
            else:
                # Create new save file with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_filename = f"save_{player_stats.name}_{timestamp}.json"
                save_path = self.saves_dir / save_filename
                print(f"[SaveSystem] Creating new save: {save_filename}")
            
            # Create save data - ALWAYS create fresh data, don't load old data
            # This prevents any chance of reverting to old save data
            # Use a DEEP copy so nested dicts are not shared between saves
            import copy
            save_data = copy.deepcopy(self.save_template)
            
            if existing_save:
                print("[SaveSystem] Overwriting existing save with FRESH data (not merging)")
                # Keep the original creation date AND custom_moves if available
                try:
                    # Load from existing main save file for creation date
                    with open(save_path, 'r') as f:
                        old_data = json.load(f)
                    if "created_at" in old_data:
                        save_data["created_at"] = old_data["created_at"]
                        print(f"[SaveSystem] Preserved creation date: {old_data['created_at']}")
                    
                    # For custom_moves, check autosave first (most up-to-date), then main save
                    custom_moves_to_preserve = []
                    
                    # Check autosave file first
                    autosave_path = self.saves_dir / f"autosave_{player_stats.name}.json"
                    if autosave_path.exists():
                        try:
                            with open(autosave_path, 'r') as f:
                                autosave_data = json.load(f)
                            if "player" in autosave_data and "custom_moves" in autosave_data["player"]:
                                custom_moves_to_preserve = autosave_data["player"]["custom_moves"]
                                print(f"[SaveSystem] Found {len(custom_moves_to_preserve)} custom moves in autosave")
                        except Exception as e:
                            print(f"[SaveSystem] Could not read autosave for custom_moves: {e}")
                    
                    # If no custom_moves in autosave, check main save file
                    if not custom_moves_to_preserve and "player" in old_data and "custom_moves" in old_data["player"]:
                        custom_moves_to_preserve = old_data["player"]["custom_moves"]
                        print(f"[SaveSystem] Found {len(custom_moves_to_preserve)} custom moves in main save")
                    
                    # Preserve the custom_moves we found
                    if custom_moves_to_preserve:
                        save_data["player"]["custom_moves"] = custom_moves_to_preserve
                        print(f"[SaveSystem] Preserved {len(custom_moves_to_preserve)} custom moves")
                    else:
                        print(f"[SaveSystem] No custom moves found to preserve")
                    
                except Exception as e:
                    print(f"[SaveSystem] Could not read old save data: {e}")
                    save_data["created_at"] = datetime.now().isoformat()
            else:
                print("[SaveSystem] Creating completely new save file")
                save_data["created_at"] = datetime.now().isoformat()
            
            # Always update the last saved timestamp
            save_data["last_saved"] = datetime.now().isoformat()
            
            # Calculate play time
            if game_start_time:
                save_data["play_time_seconds"] = time.time() - game_start_time
            
            # Save player data
            self._save_player_data(save_data, player_stats)
            
            # Save world data if provided
            if world_data:
                self._save_world_data(save_data, world_data)
            
            # Write save file
            # Atomic write: write to temp then replace to avoid partial writes
            try:
                with tempfile.NamedTemporaryFile('w', delete=False, dir=self.saves_dir, prefix='.tmp_save_', suffix='.json') as tmp:
                    json.dump(save_data, tmp, indent=2)
                    tmp_path = Path(tmp.name)
                # Replace
                tmp_path.replace(save_path)
            except Exception as e:
                print(f"[SaveSystem] Atomic write failed, falling back to direct write: {e}")
                with open(save_path, 'w') as f:
                    json.dump(save_data, f, indent=2)

            # Verification: read back and confirm critical fields
            try:
                with open(save_path, 'r') as vf:
                    verify_data = json.load(vf)
                v_player = verify_data.get('player', {})
                print(f"[SaveSystem] Game saved to: {save_filename} (level={v_player.get('level')}, exp={v_player.get('exp')}, hp={v_player.get('stats', {}).get('hp')})")
            except Exception as e:
                print(f"[SaveSystem] Verification read failed: {e}")

            # Cleanup: remove any other stale save files for this character
            try:
                for other in all_existing:
                    if other != save_path and other.exists():
                        print(f"[SaveSystem] Removing stale duplicate save: {other.name}")
                        other.unlink()
            except Exception as e:
                print(f"[SaveSystem] Error cleaning up old saves: {e}")
            return str(save_path)
            
        except Exception as e:
            print(f"[SaveSystem] Error creating save file: {e}")
            return None
    
    def load_save_file(self, save_path):
        """Load game state from save file"""
        try:
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            print(f"[SaveSystem] Loaded save file: {os.path.basename(save_path)}")
            return save_data
            
        except Exception as e:
            print(f"[SaveSystem] Error loading save file {save_path}: {e}")
            return None
    
    def get_save_files(self):
        """Get list of all available save files with metadata"""
        save_files = []
        
        try:
            for save_file in self.saves_dir.glob("save_*.json"):
                try:
                    with open(save_file, 'r') as f:
                        save_data = json.load(f)
                    
                    # Handle both "player" and "character" keys for backward compatibility
                    player_data = save_data.get("player", save_data.get("character", {}))
                    
                    # Extract metadata for save file list
                    metadata = {
                        "filename": save_file.name,
                        "path": str(save_file),
                        "character": {
                            "name": player_data.get("name", "Unknown"),
                            "species": player_data.get("species", "Unknown"),
                            "level": player_data.get("level", 1)
                        },
                        "metadata": {
                            "playtime": save_data.get("metadata", {}).get("playtime", "00:00:00"),
                            "save_date": save_data.get("metadata", {}).get("save_date", save_data.get("last_saved", "")),
                        },
                        "world_state": save_data.get("world_state", {})
                    }
                    
                    save_files.append(metadata)
                    
                except Exception as e:
                    print(f"[SaveSystem] Error reading save file {save_file}: {e}")
                    continue
        
        except Exception as e:
            print(f"[SaveSystem] Error scanning save directory: {e}")
        
        # Sort by save date (most recent first)
        save_files.sort(key=lambda x: x["metadata"]["save_date"], reverse=True)
        return save_files
    
    def _save_player_data(self, save_data, player_stats):
        """Save player stats and data"""
        player_data = save_data["player"]
        
        print(f"[SaveSystem] SAVING PLAYER DATA:")
        print(f"  - Input player_stats.name: {getattr(player_stats, 'name', 'N/A')}")
        print(f"  - Input player_stats.level: {getattr(player_stats, 'level', 'N/A')}")
        print(f"  - Input player_stats.exp: {getattr(player_stats, 'exp', 'N/A')}")
        print(f"  - Input player_stats.hp: {getattr(player_stats, 'hp', 'N/A')}")
        
        # Basic info
        player_data["name"] = getattr(player_stats, 'name', '')
        player_data["species"] = getattr(player_stats, 'species', '')
        player_data["level"] = getattr(player_stats, 'level', 1)
        player_data["exp"] = getattr(player_stats, 'exp', 0)
        
        # Handle gif_path and sprite_path - generate proper paths if empty or missing
        gif_path = getattr(player_stats, 'gif_path', '')
        sprite_path = getattr(player_stats, 'sprite_path', '')
        species = getattr(player_stats, 'species', '')
        
        # Generate proper paths based on species if they're empty or missing
        if not gif_path and species:
            gif_path = f"C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Player_GIFs\\{species}_Player_GIF.gif"
            print(f"[SaveSystem] Generated gif_path: {gif_path}")
        
        if not sprite_path and species:
            sprite_path = f"C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\characters\\{species}_32p.png"
            print(f"[SaveSystem] Generated sprite_path: {sprite_path}")
        
        player_data["gif_path"] = gif_path
        player_data["sprite_path"] = sprite_path
        
        print(f"[SaveSystem] SAVED TO FILE:")
        print(f"  - Saved name: {player_data['name']}")
        print(f"  - Saved level: {player_data['level']}")
        print(f"  - Saved exp: {player_data['exp']}")
        
        # Stats
        stats = player_data["stats"]
        for stat_name in stats.keys():
            if hasattr(player_stats, stat_name):
                stats[stat_name] = getattr(player_stats, stat_name)
        
    # --- Equipment Serialization ---
        # Attempt to pull data from Player_Equipment system if available
        try:
            from Player_Equipment import get_main_player_equipment
            equip_obj = get_main_player_equipment()
            if equip_obj:
                equipment_list = equip_obj.get_equipment_list()
                equipment_serialized = {}
                for eq in equipment_list:
                    try:
                        equipment_serialized[eq.name] = {
                            "type": getattr(eq, 'type', None),
                            "equipped": getattr(eq, 'equipped', False),
                            "weapon_class": getattr(eq, 'weapon_class', None),
                            "weapon_type": getattr(eq, 'weapon_type', None),  # Add weapon_type to save data
                            "icon_path": getattr(eq, 'icon_path', None),
                            "image_path": getattr(eq, 'image_path', None),
                            # Just save move names for now (reconstruction of moves can be added later)
                            "moves": [getattr(m, 'name', 'Unknown') for m in getattr(eq, 'moves', [])]
                        }
                    except Exception as e:
                        print(f"[SaveSystem] Error serializing equipment '{getattr(eq,'name','?')}': {e}")
                player_data["equipment"] = equipment_serialized
                print(f"[SaveSystem] Saved {len(equipment_serialized)} equipment entries")
            else:
                print("[SaveSystem] No equipment object returned; skipping equipment save")
        except ImportError:
            print("[SaveSystem] Player_Equipment module not available; skipping equipment save")
        except Exception as e:
            print(f"[SaveSystem] Unexpected error saving equipment: {e}")

        # --- Items Serialization ---
        try:
            from Player_Items import get_main_player_items
            items_obj = get_main_player_items()
            if items_obj and hasattr(items_obj, 'items'):
                items_serialized = {}
                # Access the internal dictionary structure directly
                for item_name, item_data in items_obj.items.items():
                    try:
                        item = item_data['item']
                        count = item_data['count']
                        items_serialized[item_name] = {
                            "type": getattr(item, 'type', None),
                            "count": count,
                            "icon_path": getattr(item, 'icon_path', None),
                            "image_path": getattr(item, 'image_path', None),
                        }
                    except Exception as e:
                        print(f"[SaveSystem] Error serializing item '{item_name}': {e}")
                player_data["items"] = items_serialized
                print(f"[SaveSystem] Saved {len(items_serialized)} items")
            else:
                print("[SaveSystem] No items object or no items to save")
        except ImportError:
            print("[SaveSystem] Player_Items module not available; skipping items save")
        except Exception as e:
            print(f"[SaveSystem] Unexpected error saving items: {e}")

        # --- Weapon Proficiencies ---
        try:
            print(f"[Save_System] *** WEAPON PROFICIENCY SAVE DEBUG START ***")
            from Player_Equipment import get_main_player_equipment
            equip_obj = get_main_player_equipment()
            print(f"[Save_System] Equipment object retrieved: {type(equip_obj)}")
            print(f"[Save_System] Equipment object ID: {id(equip_obj)}")
            
            if equip_obj and hasattr(equip_obj, 'weapon_proficiency'):
                prof_system = equip_obj.weapon_proficiency
                print(f"[Save_System] weapon_proficiency system found: {type(prof_system)}")
                print(f"[Save_System] WeaponProficiency object ID: {id(prof_system)}")
                
                wpns = {}
                # Access internal dicts directly for exact values
                print(f"[Save_System] Saving weapon proficiencies:")
                total_nonzero = 0
                for wpn_class, level in prof_system.wpn_class_proficiency.items():
                    try:
                        exp = prof_system.wpn_class_exp.get(wpn_class, 0)
                        wpns[wpn_class] = {
                            "proficiency": level,
                            "experience": exp
                        }
                        if level > 0 or exp > 0:
                            print(f"[Save_System]   Saving {wpn_class}: Level {level}, EXP {exp}")
                            total_nonzero += 1
                    except Exception as e:
                        print(f"[Save_System] Error serializing proficiency '{wpn_class}': {e}")
                        
                player_data["weapon_proficiencies"] = wpns
                print(f"[Save_System] Saved weapon proficiencies for {len(wpns)} classes ({total_nonzero} with progress)")
                print(f"[Save_System] Final weapon_proficiencies data sample: {dict(list(wpns.items())[:3])}")
            else:
                print("[Save_System] WARNING: No equipment object or weapon_proficiency found for saving proficiencies")
                
            print(f"[Save_System] *** WEAPON PROFICIENCY SAVE DEBUG END ***")
        except ImportError:
            print("[Save_System] Player_Equipment module not available; skipping weapon proficiencies save")
        except Exception as e:
            print(f"[Save_System] Error saving weapon proficiencies: {e}")
            import traceback
            traceback.print_exc()

        # --- Memory Skills Serialization ---
        try:
            print(f"[SaveSystem] *** MEMORY SKILLS SAVE DEBUG START ***")
            
            memory_skills_data = player_data["memory_skills"]
            
            # First try to get equipped skills directly from the player_stats parameter
            if hasattr(player_stats, 'equipped_memory_skills'):
                memory_skills_data["equipped"] = list(player_stats.equipped_memory_skills)
                print(f"[SaveSystem] Saved equipped memory skills from player_stats: {memory_skills_data['equipped']}")
            else:
                # Try to access global player_stats object as fallback
                global_player_stats = None
                try:
                    # Look for player_stats in the overworld module
                    import sys
                    for module_name in sys.modules:
                        if 'Overworld_Main' in module_name:
                            overworld_module = sys.modules[module_name]
                            if hasattr(overworld_module, 'player_stats'):
                                global_player_stats = overworld_module.player_stats
                                break
                    
                    if global_player_stats and hasattr(global_player_stats, 'equipped_memory_skills'):
                        memory_skills_data["equipped"] = list(global_player_stats.equipped_memory_skills)
                        print(f"[SaveSystem] Saved equipped memory skills from global player_stats: {memory_skills_data['equipped']}")
                    else:
                        print(f"[SaveSystem] No equipped memory skills found on any player object")
                        
                except Exception as e:
                    print(f"[SaveSystem] Error finding global player_stats: {e}")
                
            # Save memory skill states if available
            if hasattr(player_stats, 'memory_skill_state'):
                memory_skills_data["skill_states"] = dict(player_stats.memory_skill_state)
                print(f"[SaveSystem] Saved memory skill states from player_stats: {memory_skills_data['skill_states']}")
            elif global_player_stats and hasattr(global_player_stats, 'memory_skill_state'):
                memory_skills_data["skill_states"] = dict(global_player_stats.memory_skill_state)
                print(f"[SaveSystem] Saved memory skill states from global player_stats: {memory_skills_data['skill_states']}")
            else:
                print(f"[SaveSystem] No memory skill states found on any player object")
                
            # TODO: Save available memory points if that system exists
            # For now, keep default value from template
            
            print(f"[SaveSystem] *** MEMORY SKILLS SAVE DEBUG END ***")
        except Exception as e:
            print(f"[SaveSystem] Error saving memory skills: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_world_data(self, save_data, world_data):
        """Save world state data"""
        if not world_data:
            return
            
        world_state = save_data["world_state"]
        
        # Save player position if provided in world_data
        if "player_position" in world_data:
            save_data["player"]["position"].update(world_data["player_position"])
            print(f"[SaveSystem] Saved player position: {world_data['player_position']}")
            # Extra debug: show final position stored in save_data
            print(f"[SaveSystem] save_data.player.position now: {save_data['player']['position']}")
        
        # Save enemy states
        if "enemies" in world_data:
            world_state["enemies"] = world_data["enemies"]
        
        # Save interaction states
        if "interactions" in world_data:
            world_state["interactions"] = world_data["interactions"]
        
        # Save enemy type interaction counters (new system)
        if "enemy_type_interactions" in world_data:
            world_state["enemy_type_interactions"] = world_data["enemy_type_interactions"]
        
        # Save legacy corpse interaction counters for backward compatibility
        if "corpse_interactions" in world_data:
            world_state["corpse_interactions"] = world_data["corpse_interactions"]
        
        # Save map events
        if "map_events" in world_data:
            world_state["map_events"] = world_data["map_events"]
        
        # Save explored maps
        if "explored_maps" in world_data:
            world_state["explored_maps"] = world_data["explored_maps"]
            
        # Save per-map data
        if "maps" in world_data:
            world_state["maps"] = world_data["maps"]
    
    def auto_save(self, player_stats, world_data=None, game_start_time=None):
        """Auto-save by updating the main save file (same as normal save)"""
        print(f"[SaveSystem] Auto-saving game (updating main save file)")
        # Auto-save now works exactly the same as create_save_file
        return self.create_save_file(player_stats, world_data, game_start_time)
    
    def format_play_time(self, seconds):
        """Format play time seconds into readable string"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def load_save(self, character_name):
        """Load save data for a character by name from the main save file"""
        try:
            # Load from the main save file (autosave now updates this same file)
            existing_save = self.find_existing_save(character_name)
            if existing_save:
                print(f"[SaveSystem] Loading save file for {character_name}")
                return self.load_save_file(existing_save)
            
            print(f"[SaveSystem] No save found for character {character_name}")
            return None
        except Exception as e:
            print(f"[SaveSystem] Error loading save for {character_name}: {e}")
            return None
            return None
    
    def save_game(self, save_data, character_name=None):
        """Save game data to character's autosave file"""
        try:
            # Get character name from save data if not provided
            if not character_name and 'player' in save_data and 'name' in save_data['player']:
                character_name = save_data['player']['name']
            
            if not character_name:
                print("[SaveSystem] Cannot save: no character name provided")
                return False
            
            # Update timestamps
            save_data['last_saved'] = datetime.now().isoformat()
            
            # Save to autosave file
            autosave_path = self.saves_dir / f"autosave_{character_name}.json"
            with open(autosave_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            print(f"[SaveSystem] Game saved to {autosave_path}")
            return True
            
        except Exception as e:
            print(f"[SaveSystem] Error saving game: {e}")
            return False

# Global save system instance
save_system = SaveSystem()



