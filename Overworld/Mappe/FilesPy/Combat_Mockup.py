# Combat_Mockup.py
# Temporary combat simulation stub

def Combat_Mockup(player_stats, npc, Corpse, object_group):
    """
    Simulates combat: player loses 15hp to each body part, enemy is killed and replaced by corpse object.
    Requires global object_group and Tile class from main file.
    """
    print(f"[Combat_Mockup] Combat triggered between {getattr(player_stats, 'name', 'Player')} and {getattr(npc, 'name', 'Enemy')}")
    # --- Robust imports and checks ---
    try:
        import pygame
    except ImportError:
        print("[Combat_Mockup] pygame not available.")
        return
    # Use Corpse and object_group passed from main file
    # --- Damage application ---
    # Apply 15hp damage to each body part if possible
    for part in ['head', 'torso', 'left_arm', 'right_arm', 'left_leg', 'right_leg']:
        if hasattr(player_stats, 'take_damage'):
            try:
                player_stats.take_damage(5, part=part)
            except Exception as e:
                print(f"[Combat_Mockup] Error applying damage to {part}: {e}")
    npc.kill()

    # --- Record enemy death in world state ---
    try:
        print(f"[Combat_Mockup] Starting enemy death recording for {getattr(npc, 'name', 'unknown_enemy')}")
        
        # Get spawn and death coordinates - fixed to use stored spawn coords
        spawn_x = getattr(npc, 'spawn_x', 0)
        spawn_y = getattr(npc, 'spawn_y', 0)
        death_x = getattr(npc, 'pos', None).x if hasattr(getattr(npc, 'pos', None), 'x') else getattr(npc, 'rect', None).x if hasattr(npc, 'rect') else 0
        death_y = getattr(npc, 'pos', None).y if hasattr(getattr(npc, 'pos', None), 'y') else getattr(npc, 'rect', None).y if hasattr(npc, 'rect') else 0
        
        print(f"[Combat_Mockup] Enemy coords: spawn=({spawn_x}, {spawn_y}), death=({death_x}, {death_y})")
        
        # Access global world state directly from the calling module
        import sys
        
        # Try to get WORLD_STATE from the calling frame's globals
        import inspect
        frame = inspect.currentframe()
        main_globals = None
        
        # Walk up the call stack to find WORLD_STATE
        while frame is not None:
            frame_globals = frame.f_globals
            if 'WORLD_STATE' in frame_globals and 'current_map_name' in frame_globals:
                main_globals = frame_globals
                print(f"[Combat_Mockup] Found WORLD_STATE in calling frame: {frame.f_code.co_filename}")
                break
            frame = frame.f_back
        
        if main_globals and 'WORLD_STATE' in main_globals and 'current_map_name' in main_globals:
            current_map = main_globals['current_map_name']
            world_state = main_globals['WORLD_STATE']
            print(f"[Combat_Mockup] Successfully accessed WORLD_STATE from caller")
            print(f"[Combat_Mockup] Current map: {current_map}")
            
            # Ensure map is in world state
            if current_map not in world_state["maps"]:
                world_state["maps"][current_map] = {"killed_enemies": [], "killed_objects": []}
                print(f"[Combat_Mockup] Created map entry for '{current_map}'")
            
            # Add killed enemy record
            enemy_record = {
                "name": getattr(npc, 'name', 'unknown_enemy'),
                "spawn_x": spawn_x,
                "spawn_y": spawn_y,
                "death_x": death_x,
                "death_y": death_y,
                "interactions": 0  # NEW: Track individual corpse interactions
            }
            world_state["maps"][current_map]["killed_enemies"].append(enemy_record)
            print(f"[Combat_Mockup] Recorded enemy death: {enemy_record}")
            print(f"[Combat_Mockup] World state now has {len(world_state['maps'][current_map]['killed_enemies'])} killed enemies on map '{current_map}'")
        else:
            print(f"[Combat_Mockup] ERROR: Could not find WORLD_STATE in any calling frame!")
            
    except Exception as e:
        print(f"[Combat_Mockup] Error recording enemy death: {e}")
        import traceback
        traceback.print_exc()

    # --- Death image loading ---
    death_image_path = getattr(npc, "death_image_path", None)
    death_image = None
    if death_image_path:
        try:
            death_image = pygame.image.load(death_image_path).convert_alpha()
        except Exception as e:
            print(f"[Combat_Mockup] Could not load death image: {e}")
    if death_image is None:
        death_image = pygame.Surface((32,32), pygame.SRCALPHA)
        death_image.fill((80, 80, 80, 180))  # Gray fallback
    # --- Position fallback ---
    pos = None
    if hasattr(npc, 'pos') and hasattr(npc.pos, 'x') and hasattr(npc.pos, 'y'):
        pos = (npc.pos.x, npc.pos.y)
    elif hasattr(npc, 'rect'):
        pos = (npc.rect.x, npc.rect.y)
    else:
        pos = (0, 0)

    # --- Create corpse using Corpse class ---
    try:
        corpse_obj = Corpse(pos, death_image, getattr(npc, 'name', 'enemy'))
        print(f"[Combat_Mockup] Corpse object created at {pos}.")
    except Exception as e:
        print(f"[Combat_Mockup] Error creating corpse object: {e}")

    # --- Add weapon proficiency experience after combat ---
    try:
        print(f"[Combat_Mockup] *** WEAPON PROFICIENCY DEBUG START ***")
        import Player_Equipment
        print(f"[Combat_Mockup] Player_Equipment imported successfully")
        
        if hasattr(Player_Equipment, 'player1'):
            player1 = Player_Equipment.player1
            print(f"[Combat_Mockup] player1 found: {type(player1)}")
            
            if player1 and hasattr(player1, 'weapon_proficiency'):
                prof_sys = player1.weapon_proficiency
                print(f"[Combat_Mockup] weapon_proficiency system found: {type(prof_sys)}")
                
                # Show current weapon proficiencies before adding experience
                print(f"[Combat_Mockup] Current weapon proficiencies BEFORE combat exp:")
                for wpn_class, level in prof_sys.wpn_class_proficiency.items():
                    exp = prof_sys.wpn_class_exp.get(wpn_class, 0)
                    if level > 0 or exp > 0:
                        print(f"[Combat_Mockup]   {wpn_class}: Level {level}, EXP {exp}")
                
                # Add combat experience
                level_up = Player_Equipment.add_combat_experience(player1)
                print(f"[Combat_Mockup] add_combat_experience called, level_up result: {level_up}")
                
                # Show current weapon proficiencies after adding experience
                print(f"[Combat_Mockup] Current weapon proficiencies AFTER combat exp:")
                for wpn_class, level in prof_sys.wpn_class_proficiency.items():
                    exp = prof_sys.wpn_class_exp.get(wpn_class, 0)
                    if level > 0 or exp > 0:
                        print(f"[Combat_Mockup]   {wpn_class}: Level {level}, EXP {exp}")
                
                if level_up:
                    print("🎉 [Combat_Mockup] Weapon proficiency level increased after combat!")
                else:
                    print("[Combat_Mockup] Added weapon proficiency experience after combat")
            else:
                print("[Combat_Mockup] WARNING: player1 missing weapon_proficiency attribute")
        else:
            print("[Combat_Mockup] WARNING: Player_Equipment.player1 not available")
        
        print(f"[Combat_Mockup] *** WEAPON PROFICIENCY DEBUG END ***")
    except ImportError:
        print("[Combat_Mockup] WARNING: Player_Equipment module not available for experience gain")
    except Exception as e:
        print(f"[Combat_Mockup] ERROR adding weapon proficiency experience: {e}")
        import traceback
        traceback.print_exc()

    # --- Auto-save after enemy kill ---
    try:
        print(f"[Combat_Mockup] Triggering auto-save after enemy kill")
        if main_globals and 'create_complete_save' in main_globals:
            save_path = main_globals['create_complete_save']("enemy_kill")
            if save_path:
                print(f"[Combat_Mockup] Auto-save after enemy kill successful: {save_path}")
            else:
                print(f"[Combat_Mockup] Auto-save after enemy kill failed!")
        else:
            print(f"[Combat_Mockup] Warning: Cannot auto-save - main_globals missing create_complete_save function")
    except Exception as e:
        print(f"[Combat_Mockup] Error during auto-save after enemy kill: {e}")

    print("[Combat] Combat completed successfully")
