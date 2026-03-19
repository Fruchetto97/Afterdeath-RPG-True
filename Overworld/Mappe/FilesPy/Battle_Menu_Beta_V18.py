# IMPORTS AND SETUP
from pathlib import Path
from PIL import Image
import pygame
import sys
import random
import time
import traceback
import os
from pathlib import Path
from PIL import Image
import pygame
import sys

# Weapon equipping cost variables
swap_weapon_cost = 3  # Cost to swap one weapon for another
equip_unequip_cost = 2  # Cost to manually equip or unequip without swapping

# Import status effects configuration
main_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(main_dir)
from Status_Effects_Config import (
    get_effect_config, 
    calculate_debuff_level, 
    get_damage_per_turn,
    get_all_debuff_effects,
    get_effect_cost,
    get_confusion_accuracy_modifier,
    is_property_effect,
    get_property_effects,
    get_property_config,
    STATUS_EFFECTS_CONFIG
)
from Species_Config import get_species_config
from Skills_Config import calculate_elemental_damage, get_species_elemental_modifiers, MEMORY_SKILLS
import Global_SFX

# ================= MEMORY SKILLS RUNTIME SYSTEM WITH DEBUGGING =================

# Global reference to battle menu instance for event logging
battle_menu_instance = None

def process_memory_skills_start_of_turn(active, opposing):
    """Process memory skills at start of character's turn."""
    global turn_player, turn_enemy, battle_menu_instance
    total_turns = turn_player + turn_enemy
    print(f"\n[MemorySkills] === PROCESSING TURN START FOR {active.name} ===")
    print(f"[MemorySkills] Total turns: {total_turns} (P:{turn_player} + E:{turn_enemy})")
    print(f"[MemorySkills] Equipped skills: {getattr(active, 'equipped_memory_skills', 'NONE')}")
    
    if not active or not hasattr(active, 'equipped_memory_skills'):
        print(f"[MemorySkills] {active.name} has no equipped_memory_skills attribute")
        return
    
    if not active.equipped_memory_skills:
        print(f"[MemorySkills] {active.name} has empty equipped_memory_skills list")
        return
    
    # SAFETY CHECK: Ensure memory_skill_state exists
    if not hasattr(active, 'memory_skill_state'):
        print(f"[MemorySkills] WARNING: {active.name} missing memory_skill_state, initializing...")
        init_memory_skill_state(active)
    
    active.memory_turn_damage_bonus = 0
    
    for sid in active.equipped_memory_skills:
        print(f"[MemorySkills] Processing skill: {sid}")
        data = MEMORY_SKILLS.get(sid)
        if not data:
            print(f"[MemorySkills] ERROR: Skill {sid} not found in MEMORY_SKILLS")
            continue
        
        trig = data.get("trigger_type")
        params = data.get("trigger_params", {})
        state = active.memory_skill_state.get(sid, {})
        
        print(f"[MemorySkills] {sid}: trigger_type={trig}, params={params}")
        
        # PERIODIC SKILLS
        if trig == "periodic":
            period = params.get("period", 0)
            # For periodic skills, we want them to activate on turns: period, period*2, period*3, etc.
            # So for raising_speed (period=2): turns 2, 4, 6, 8, etc.
            # For fiery_presence (period=1): turns 1, 2, 3, 4, etc.
            # Use player's individual turn count since total_turns gives odd numbers for player
            player_turn_count = turn_player
            mod_result = player_turn_count % period if period > 0 else "N/A"
            should_activate = period > 0 and player_turn_count > 0 and player_turn_count % period == 0
            print(f"[MemorySkills] {sid}: Checking periodic (period={period}, player_turn={player_turn_count}, mod={mod_result}, should_activate={should_activate})")
            
            if should_activate:
                print(f"[MemorySkills] {sid}: ACTIVATING PERIODIC SKILL!")
                
                action = params.get("action", {})
                eff = action.get("effect")
                
                if eff == "BUFF_STAT":
                    stat = action.get("stat")
                    inc = action.get("amount", 0)
                    cap = action.get("max_total_bonus", 0)
                    applied = state.get("applied_bonus", 0)
                    if stat and applied < cap:
                        real_inc = min(inc, cap - applied)
                        # Use the proper buff system instead of direct stat modification
                        apply_buff_debuff(active, stat, real_inc, 999)  # Long duration for memory skills
                        state["applied_bonus"] = applied + real_inc
                        skill_name = data.get('name', sid)
                        print(f"[MemorySkills] {skill_name}: Applied +{real_inc} {stat} buff (total bonus {state['applied_bonus']}/{cap})")
                        
                        # Play sound ONLY when skill actually activates (not when max bonus reached)
                        if 'played_sound' in data:
                            sound_file = data['played_sound']
                            print(f"🎵 Playing memory skill sound for {skill_name}: {sound_file}")
                            # Use Global_SFX volume system instead of hardcoded volume
                            try:
                                import Global_SFX
                                # Play with base volume 0.6 and apply global SFX volume
                                if hasattr(battle_menu_instance, 'play_sound_effect'):
                                    # Calculate final volume using Global_SFX system
                                    base_volume = 0.6  # Base volume for memory skills
                                    global_sfx_volume = Global_SFX.get_global_sfx_volume()
                                    final_volume = base_volume * global_sfx_volume
                                    battle_menu_instance.play_sound_effect(sound_file, volume=final_volume, loops=0)
                                else:
                                    # Fallback to direct pygame with Global_SFX
                                    sound = Global_SFX.load_sound_with_global_volume(sound_file, 0.6)
                                    if sound:
                                        sound.play()
                            except Exception as e:
                                print(f"[MemorySkills] Error playing sound {sound_file}: {e}")
                        
                        # Add to event log with proper colors
                        if battle_menu_instance:
                            battle_menu_instance.add_log_entry(
                                f"{active.name}'s {skill_name} activated! +{real_inc} {stat.upper()} (Total: +{state['applied_bonus']})",
                                'effect',
                                (255, 200, 100)  # Golden color for memory skills
                            )
                    else:
                        print(f"[MemorySkills] {sid}: Stat buff capped or invalid (applied={applied}, cap={cap}) - NO SOUND PLAYED")
                        
                elif eff == "APPLY_STATUS":
                    status_name = action.get("status", "BURN")
                    skill_name = data.get('name', sid)
                    print(f"[MemorySkills] {sid}: Applying status to {opposing.name}")
                    
                    _mem_apply_status_random(
                        opposing,
                        status_name,
                        action.get("level", 1),
                        action.get("duration", 1),
                        action.get("target_mode", "RANDOM_ENEMY_PART"),
                        action.get("target_part")
                    )
                    
                    # Play sound AFTER successful status application
                    if 'played_sound' in data:
                        sound_file = data['played_sound']
                        print(f"🎵 Playing memory skill sound for {skill_name}: {sound_file}")
                        # Use Global_SFX volume system
                        try:
                            import Global_SFX
                            # Play with base volume 0.6 and apply global SFX volume
                            if hasattr(battle_menu_instance, 'play_sound_effect'):
                                base_volume = 0.6  # Base volume for memory skills
                                global_sfx_volume = Global_SFX.get_global_sfx_volume()
                                final_volume = base_volume * global_sfx_volume
                                battle_menu_instance.play_sound_effect(sound_file, volume=final_volume, loops=0)
                            else:
                                # Fallback to direct pygame with Global_SFX
                                sound = Global_SFX.load_sound_with_global_volume(sound_file, 0.6)
                                if sound:
                                    sound.play()
                        except Exception as e:
                            print(f"[MemorySkills] Error playing sound {sound_file}: {e}")
                    
                    # Add to event log with proper colors
                    if battle_menu_instance:
                        battle_menu_instance.add_log_entry(
                            f"{active.name}'s {skill_name} activated! Applied {status_name} to {opposing.name}",
                            'effect',
                            (255, 100, 100)  # Red color for damage/status effects
                        )
            else:
                print(f"[MemorySkills] {sid}: Periodic condition not met")
        
        # ENEMY STATUS THRESHOLD SKILLS
        elif trig == "enemy_status_threshold":
            status = params.get("status")
            if status:
                total = _mem_total_status_stacks(opposing, status)
                stacks_per = params.get("stacks_per_increment", 1)
                pct_per = params.get("percent_per_increment", 0)
                max_pct = params.get("max_percent", 0)
                increments = total // stacks_per if stacks_per > 0 else 0
                bonus_pct = min(max_pct, increments * pct_per)
                
                print(f"[MemorySkills] {sid}: Status threshold check - {opposing.name} has {total} {status} stacks")
                print(f"[MemorySkills] {sid}: Increments={increments}, bonus={bonus_pct}%")
                
                if bonus_pct > 0:
                    active.memory_turn_damage_bonus += bonus_pct
                    print(f"[MemorySkills] {data['name']}: +{bonus_pct}% damage (total bonus now {active.memory_turn_damage_bonus}%)")
            else:
                print(f"[MemorySkills] {sid}: No status specified for threshold")
        
        # ENEMY STATUS BUFF SKILLS - Refreshing buff based on enemy status
        elif trig == "enemy_status_buff":
            status = params.get("status")
            stat = params.get("stat")
            if status and stat:
                total = _mem_total_status_stacks(opposing, status)
                stacks_per = params.get("stacks_per_increment", 1)
                buff_per = params.get("buff_per_increment", 1)
                duration = params.get("duration", 1)
                increments = total // stacks_per if stacks_per > 0 else 0
                buff_amount = increments * buff_per
                
                print(f"[MemorySkills] {sid}: Status buff check - {opposing.name} has {total} {status} stacks")
                print(f"[MemorySkills] {sid}: Increments={increments}, buff amount={buff_amount}")
                
                skill_name = data.get('name', sid)
                
                # First remove any existing buff from this skill (to refresh)
                previous_buff = state.get("current_buff_amount", 0)
                if previous_buff > 0:
                    # Remove previous buff by applying negative amount
                    apply_buff_debuff(active, stat, -previous_buff, 1)
                    print(f"[MemorySkills] {skill_name}: Removed previous buff of {previous_buff} {stat}")
                
                # Apply new buff if condition is met
                if buff_amount > 0:
                    apply_buff_debuff(active, stat, buff_amount, duration)
                    state["current_buff_amount"] = buff_amount
                    print(f"[MemorySkills] {skill_name}: Applied +{buff_amount} {stat} buff for {duration} turn(s)")
                    
                    # Play sound AFTER successful buff application
                    if 'played_sound' in data:
                        sound_file = data['played_sound']
                        print(f"🎵 Playing memory skill sound for {skill_name}: {sound_file}")
                        # Use Global_SFX volume system
                        try:
                            import Global_SFX
                            if hasattr(battle_menu_instance, 'play_sound_effect'):
                                base_volume = 0.6
                                global_sfx_volume = Global_SFX.get_global_sfx_volume()
                                final_volume = base_volume * global_sfx_volume
                                battle_menu_instance.play_sound_effect(sound_file, volume=final_volume, loops=0)
                            else:
                                sound = Global_SFX.load_sound_with_global_volume(sound_file, 0.6)
                                if sound:
                                    sound.play()
                        except Exception as e:
                            print(f"[MemorySkills] Error playing sound {sound_file}: {e}")
                    
                    # Add to event log
                    if battle_menu_instance:
                        battle_menu_instance.add_log_entry(
                            f"{active.name}'s {skill_name} activated! +{buff_amount} {stat.upper()} (from {total} {status} stacks on {opposing.name})",
                            'effect',
                            (255, 150, 150)  # Light red color for wound exploitation
                        )
                else:
                    # No buff to apply, set current amount to 0
                    state["current_buff_amount"] = 0
                    if previous_buff > 0:
                        print(f"[MemorySkills] {skill_name}: Condition no longer met, buff removed")
                        if battle_menu_instance:
                            battle_menu_instance.add_log_entry(
                                f"{active.name}'s {skill_name} is no longer active (no qualifying {status} stacks)",
                                'effect',
                                (150, 150, 150)  # Gray color for skill deactivation
                            )
            else:
                print(f"[MemorySkills] {sid}: Missing status or stat parameter for enemy_status_buff")
        
        else:
            print(f"[MemorySkills] {sid}: Trigger type {trig} not processed at turn start")
        
        active.memory_skill_state[sid] = state
    
    print(f"[MemorySkills] Turn start processing complete for {active.name}")

def process_memory_skills_bodypart_loss(owner, opposing, lost_part_name):
    """Process memory skills when body part reaches 0 HP."""
    global battle_menu_instance
    print(f"\n[MemorySkills] === BODY PART LOSS: {owner.name} lost {lost_part_name} ===")
    
    if not owner or not hasattr(owner, 'equipped_memory_skills'):
        print(f"[MemorySkills] {owner.name} has no equipped_memory_skills")
        return
    
    # SAFETY CHECK: Ensure memory_skill_state exists
    if not hasattr(owner, 'memory_skill_state'):
        print(f"[MemorySkills] WARNING: {owner.name} missing memory_skill_state, initializing...")
        init_memory_skill_state(owner)
    
    print(f"[MemorySkills] {owner.name} equipped skills: {owner.equipped_memory_skills}")
    
    for sid in owner.equipped_memory_skills:
        data = MEMORY_SKILLS.get(sid)
        if not data or data.get("trigger_type") != "on_bodypart_loss":
            continue
        
        print(f"[MemorySkills] Processing body part loss skill: {sid}")
        params = data.get("trigger_params", {})
        state = owner.memory_skill_state.get(sid, {})
        limit = params.get("limit_per_battle", 0)
        
        if limit > 0 and state.get("activations", 0) >= limit:
            print(f"[MemorySkills] {sid} already used {limit} times this battle")
            continue
        
        action = params.get("action", {})
        eff = action.get("effect")
        
        print(f"[MemorySkills] {sid}: Executing effect {eff}")
        
        if eff == "RESTORE_PART_PERCENT":
            if _mem_restore_first_lost_part(owner, action.get("percent", 0.5)):
                state["activations"] = state.get("activations", 0) + 1
                skill_name = data.get('name', sid)
                print(f"[MemorySkills] {skill_name} activated for {owner.name}")
                
                # Play sound AFTER successful restoration
                if 'played_sound' in data:
                    sound_file = data['played_sound']
                    print(f"🎵 Playing memory skill sound for {skill_name}: {sound_file}")
                    # Use Global_SFX volume system
                    try:
                        import Global_SFX
                        if hasattr(battle_menu_instance, 'play_sound_effect'):
                            base_volume = 0.6
                            global_sfx_volume = Global_SFX.get_global_sfx_volume()
                            final_volume = base_volume * global_sfx_volume
                            battle_menu_instance.play_sound_effect(sound_file, volume=final_volume, loops=0)
                        else:
                            sound = Global_SFX.load_sound_with_global_volume(sound_file, 0.6)
                            if sound:
                                sound.play()
                    except Exception as e:
                        print(f"[MemorySkills] Error playing sound {sound_file}: {e}")
                
                # DELAYED LOGGING: Store memory skill event for later display
                if globals().get('battle_menu_instance'):
                    battle_instance = globals()['battle_menu_instance']
                    if not hasattr(battle_instance, 'pending_memory_skill_logs'):
                        battle_instance.pending_memory_skill_logs = []
                    
                    log_message = f"{owner.name}'s {skill_name} triggered! Body part restored"
                    battle_instance.pending_memory_skill_logs.append((log_message, "effect", (100, 255, 100)))
                
        elif eff == "DAMAGE_AND_STATUS":
            formula = action.get("damage_formula", "0")
            special_val = getattr(owner, 'spe', 0)
            safe_expr = formula.replace('special', str(special_val)).replace('spe', str(special_val))
            try:
                dmg = int(eval(safe_expr, {"__builtins__": {}}, {}))
                print(f"[MemorySkills] {sid}: Calculated damage = {dmg} (formula: {formula}, spe: {special_val})")
            except Exception as e:
                print(f"[MemorySkills] {sid}: Error calculating damage: {e}")
                dmg = 0
            
            target_part_name, status_applied = _mem_damage_random_enemy_part(
                opposing,
                dmg,
                status=action.get("status"),
                status_level=action.get("status_level", 1),
                status_duration=action.get("status_duration", 1)
            )
            
            state["activations"] = state.get("activations", 0) + 1
            skill_name = data.get('name', sid)
            print(f"[MemorySkills] {skill_name} explosion activated for {owner.name}")
            
            # Play sound AFTER successful damage and status application
            if 'played_sound' in data:
                sound_file = data['played_sound']
                print(f"🎵 Playing memory skill sound for {skill_name}: {sound_file}")
                # Use Global_SFX volume system
                try:
                    import Global_SFX
                    if hasattr(battle_menu_instance, 'play_sound_effect'):
                        base_volume = 0.6
                        global_sfx_volume = Global_SFX.get_global_sfx_volume()
                        final_volume = base_volume * global_sfx_volume
                        battle_menu_instance.play_sound_effect(sound_file, volume=final_volume, loops=0)
                    else:
                        sound = Global_SFX.load_sound_with_global_volume(sound_file, 0.6)
                        if sound:
                            sound.play()
                except Exception as e:
                    print(f"[MemorySkills] Error playing sound {sound_file}: {e}")
            
            # DELAYED LOGGING: Store memory skill event for later display
            if battle_menu_instance and opposing:
                if not hasattr(battle_menu_instance, 'pending_memory_skill_logs'):
                    battle_menu_instance.pending_memory_skill_logs = []
                
                if status_applied:
                    status_info = f" and applied {status_applied}"
                else:
                    status_info = ""
                log_message = f"{owner.name}'s {skill_name} triggered! Dealt {dmg} damage{status_info} to {opposing.name}'s {target_part_name}!"
                battle_menu_instance.pending_memory_skill_logs.append((log_message, 'effect', (255, 150, 0)))
        
        owner.memory_skill_state[sid] = state

def apply_memory_damage_bonus(base_damage, attacker):
    """Apply memory-based damage bonus."""
    bonus_pct = getattr(attacker, 'memory_turn_damage_bonus', 0)
    if bonus_pct > 0:
        final_damage = int(base_damage * (1 + bonus_pct / 100.0))
        print(f"[MemorySkills] {attacker.name} damage bonus: {base_damage} -> {final_damage} (+{bonus_pct}%)")
        return final_damage
    else:
        print(f"[MemorySkills] {attacker.name} no damage bonus (bonus_pct={bonus_pct})")
        return base_damage

# ...existing helper functions (_mem_total_status_stacks, _mem_apply_status_random, etc.)...

# ================= END MEMORY SKILLS RUNTIME SYSTEM =====================

# Import Enemy AI system - V3 with simple decision tree
try:
    import sys
    import os
    # Add the project root directory to the path (3 levels up from this file)
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from Enemy_AI_V3 import create_enemy_ai_v3
    ENEMY_AI_AVAILABLE = True
    AI_VERSION = 'V3'
    print("[Battle_Menu] Enemy AI V3 system loaded successfully")
except ImportError as e:
    print(f"[Battle_Menu] Warning: Could not import Enemy AI V3: {e}")
    # Try fallback to V2
    try:
        from Enemy_AI_V2 import create_enemy_ai_v2
        ENEMY_AI_AVAILABLE = True
        AI_VERSION = 'V2'
        print("[Battle_Menu] Fallback to Enemy AI V2 system loaded successfully")
    except ImportError as e2:
        print(f"[Battle_Menu] Warning: Could not import any Enemy AI: {e2}")
        ENEMY_AI_AVAILABLE = False
        AI_VERSION = None

# ================= MEMORY SKILLS RUNTIME SYSTEM =================

def init_memory_skill_state(combatant):
    """Prepare per-battle memory skill tracking for a combatant."""
    if combatant is None:
        return
    
    print(f"[MemorySkills] Initializing memory skill state for {combatant.name}")
    
    if not hasattr(combatant, 'equipped_memory_skills'):
        # Try to load equipped memory skills from actual player data
        if hasattr(combatant, 'name'):
            # Check if this is the player character by trying to access overworld player_stats
            try:
                # Import overworld module to access player_stats
                import sys
                player_loaded = False
                for module_name in sys.modules:
                    if 'Overworld_Main' in module_name:
                        overworld_module = sys.modules[module_name]
                        if hasattr(overworld_module, 'player_stats'):
                            player_stats = overworld_module.player_stats
                            if (hasattr(player_stats, 'equipped_memory_skills') and 
                                player_stats.name == combatant.name):
                                # This is the player - use their actual equipped skills
                                combatant.equipped_memory_skills = list(player_stats.equipped_memory_skills)
                                print(f"[MemorySkills] LOADED PLAYER SKILLS FROM SAVE: {combatant.equipped_memory_skills}")
                                player_loaded = True
                                break
                
                if not player_loaded:
                    # This is likely an enemy or player skills couldn't be loaded - use fallback only for players
                    if any(name in combatant.name.upper() for name in ["PLAYER", "JONNY"]):
                        combatant.equipped_memory_skills = ["raising_speed", "fiery_presence"]
                        print(f"[MemorySkills] FALLBACK PLAYER TEST SKILLS: {combatant.equipped_memory_skills}")
                    else:
                        # For enemies, don't override if they already have skills - they should come from enemy data
                        combatant.equipped_memory_skills = []
                        print(f"[MemorySkills] Enemy {combatant.name} has no equipped skills, using empty list")
                        
            except Exception as e:
                print(f"[MemorySkills] Error loading from save data: {e}")
                # Final fallback
                combatant.equipped_memory_skills = []
                print(f"[MemorySkills] Using empty skills list as final fallback")
        else:
            combatant.equipped_memory_skills = []
            print(f"[MemorySkills] No name attribute, using empty skills list")
    else:
        print(f"[MemorySkills] {combatant.name} already has equipped_memory_skills: {combatant.equipped_memory_skills}")
    
    if not hasattr(combatant, 'memory_skill_state'):
        combatant.memory_skill_state = {}
    if not hasattr(combatant, 'memory_turn_damage_bonus'):
        combatant.memory_turn_damage_bonus = 0
    
    # Initialize state entries for equipped skills
    for sid in combatant.equipped_memory_skills:
        if sid in MEMORY_SKILLS and sid not in combatant.memory_skill_state:
            combatant.memory_skill_state[sid] = {
                "activations": 0,
                "applied_bonus": 0
            }
    
    print(f"[MemorySkills] {combatant.name} initialized with {len(combatant.equipped_memory_skills)} skills")

def _mem_total_status_stacks(target, status_name):
    """Count total status effect stacks across all body parts."""
    total = 0
    if not target or not hasattr(target, 'body_parts'):
        return 0
    for bp in target.body_parts:
        if hasattr(bp, 'p_eff'):
            eff_obj = bp.p_eff
            if hasattr(eff_obj, status_name.lower()):
                eff = getattr(eff_obj, status_name.lower())
                if isinstance(eff, list) and len(eff) >= 3 and eff[1] > 0 and eff[2] > 0:
                    total += eff[1]
    return total

def _mem_apply_status_random(enemy, status, level, duration, target_mode="RANDOM_ENEMY_PART", target_part=None):
    """Apply status effect to enemy body part."""
    import random
    if not enemy or not hasattr(enemy, 'body_parts') or not enemy.body_parts:
        return
    candidates = [bp for bp in enemy.body_parts if bp.p_pvt > 0]
    if not candidates:
        candidates = enemy.body_parts
    
    if target_mode == "SPECIFIC_PART" and target_part:
        chosen = next((bp for bp in enemy.body_parts if bp.name.upper() == target_part.upper()), None)
        if not chosen:
            chosen = random.choice(candidates)
    else:
        chosen = random.choice(candidates)
    
    part_index = enemy.body_parts.index(chosen)
    try:
        apply_status_effect(enemy, part_index, status.lower(), level, duration, 0)
        print(f"[MemorySkills] Applied {status} Lv{level} Dur{duration} to {enemy.name}'s {chosen.name}")
    except Exception as e:
        print(f"[MemorySkills] Error applying status: {e}")

def _mem_restore_first_lost_part(combatant, percent):
    """Restore first lost body part to percentage HP."""
    if not combatant or not hasattr(combatant, 'body_parts'):
        return False
    for bp in combatant.body_parts:
        if bp.p_pvt <= 0 and bp.max_p_pvt > 0:
            bp.p_pvt = max(1, int(bp.max_p_pvt * percent))
            combatant.calculate_health_from_body_parts()
            print(f"[MemorySkills] Restored {combatant.name}'s {bp.name} to {bp.p_pvt} ({int(percent*100)}%)")
            return True
    return False

def _mem_damage_random_enemy_part(enemy, amount, status=None, status_level=1, status_duration=1):
    """Deal damage to random enemy body part. Returns (target_part_name, status_applied_info)"""
    import random
    if not enemy or not hasattr(enemy, 'body_parts') or not enemy.body_parts:
        return None, None
    candidates = [bp for bp in enemy.body_parts if bp.p_pvt > 0]
    if not candidates:
        candidates = enemy.body_parts
    target = random.choice(candidates)
    old = target.p_pvt
    target.p_pvt = max(0, target.p_pvt - amount)
    print(f"[MemorySkills] Explosion deals {amount} to {enemy.name}'s {target.name} ({old}->{target.p_pvt})")
    
    # Check for body part destruction and trigger explosive mindset (but pass None as opposing to avoid infinite loops)
    if old > 0 and target.p_pvt == 0:
        process_memory_skills_bodypart_loss(enemy, None, target.name)
    
    status_applied_info = None
    if status:
        part_index = enemy.body_parts.index(target)
        try:
            apply_status_effect(enemy, part_index, status.lower(), status_level, status_duration, 0)
            status_applied_info = f"{status.upper()} (Lvl {status_level}) for {status_duration} turn{'s' if status_duration != 1 else ''}"
        except Exception:
            pass
    enemy.calculate_health_from_body_parts()
    return target.name, status_applied_info

# Duplicate function removed - using the complete version above

def apply_memory_damage_bonus(base_damage, attacker):
    """Apply memory-based damage bonus."""
    bonus_pct = getattr(attacker, 'memory_turn_damage_bonus', 0)
    if bonus_pct:
        final_damage = int(base_damage * (1 + bonus_pct / 100.0))
        print(f"[MemorySkills] {attacker.name} damage bonus: {base_damage} -> {final_damage} (+{bonus_pct}%)")
        return final_damage
    return base_damage

def resolve_damage_application(attacker, defender, move, base_damage, target_part_index, ui_instance=None):
    """Consolidated damage pipeline with memory skills integration."""
    result = {
        'final_damage': 0,
        'actual_damage': 0,
        'target_was_destroyed': False,
        'effects_applied': False,
        'target_part_name': None
    }

    if defender is None or not hasattr(defender, 'body_parts') or not defender.body_parts:
        return result

    if not (0 <= target_part_index < len(defender.body_parts)):
        return result

    target_part = defender.body_parts[target_part_index]
    result['target_part_name'] = getattr(target_part, 'name', None)

    try:
        # 1) Apply memory damage bonus
        damage_after_memory = apply_memory_damage_bonus(base_damage if base_damage is not None else 0, attacker)

        # 2) Apply weapon hand penalty for One and a Half Handed weapons used with one hand
        damage_after_weapon_penalty = damage_after_memory
        if hasattr(move, 'reqs') and move.reqs:
            for requirement in move.reqs:
                if str(requirement).upper().strip() == "WEAPON":
                    # This is a weapon move, check for one-handed penalty
                    try:
                        from Player_Equipment import get_main_player_equipment
                        player_equip = get_main_player_equipment()
                        
                        if player_equip and hasattr(attacker, 'name') and ('AKU' in attacker.name.upper() or 'SELKIO' in attacker.name.upper() or 'JONNY' in attacker.name.upper()):
                            equipped_weapon = player_equip.get_equipped_by_type('weapon')
                            if equipped_weapon and equipped_weapon.get_weapon_type() == "One and a Half Handed":
                                # Count usable hands
                                usable_hands = 0
                                for body_part in attacker.body_parts:
                                    if "ARM" in body_part.name.upper() and body_part.p_pvt >= 2:
                                        usable_hands += 1
                                
                                # Apply 25% damage penalty if only one hand is usable
                                if usable_hands == 1:
                                    damage_after_weapon_penalty = int(damage_after_memory * 0.75)
                                    if ui_instance and hasattr(ui_instance, 'add_log_entry'):
                                        ui_instance.add_log_entry(
                                            f"One-handed penalty: {damage_after_memory} -> {damage_after_weapon_penalty} damage", 
                                            "effect", (255, 200, 100)
                                        )
                                    print(f"[Battle] One-handed penalty applied: {damage_after_memory} -> {damage_after_weapon_penalty}")
                    except (ImportError, AttributeError) as e:
                        print(f"[Battle] Could not check weapon hand penalty: {e}")
                    break  # Only check once for weapon requirement

        # 3) Apply elemental modifiers
        try:
            final_damage, effects_applied = apply_elemental_damage(damage_after_weapon_penalty, move, defender, ui_instance)
        except Exception:
            final_damage, effects_applied = damage_after_weapon_penalty, True

        result['final_damage'] = int(final_damage)
        result['effects_applied'] = bool(effects_applied)

        # 4) Apply damage to target part
        old_hp = getattr(target_part, 'p_pvt', 0)
        target_part.p_pvt = max(0, int(old_hp) - int(result['final_damage']))
        actual_damage = old_hp - target_part.p_pvt
        result['actual_damage'] = int(actual_damage)

        # 5) Recalculate total HP
        try:
            defender.calculate_health_from_body_parts()
        except Exception:
            pass

        # 6) Check for body part destruction and trigger memory skills
        if old_hp > 0 and target_part.p_pvt == 0:
            result['target_was_destroyed'] = True
            process_memory_skills_bodypart_loss(defender, attacker, target_part.name)

        # 7) Apply move effects
        try:
            applied_effects = apply_move_effects(move, defender, target_part_index)
            if ui_instance and hasattr(ui_instance, 'add_log_entry') and applied_effects:
                for eff in applied_effects:
                    ui_instance.add_log_entry(f"Effect: {eff[0]} L{eff[1]} Dur{eff[2]}", "effect")
        except Exception:
            pass

        # 7) Apply lifesteal
        if move and has_property_effect(move, 'lifesteal'):
            try:
                healed = apply_lifesteal_healing(attacker, result['actual_damage'])
                if healed and ui_instance and hasattr(ui_instance, 'add_log_entry'):
                    ui_instance.add_log_entry(f"{attacker.name} healed {healed} HP", "regeneration")
            except Exception:
                pass

        return result

    except Exception as e:
        print(f"[MemorySkills] Error in damage resolution: {e}")
        return result
# ================= END MEMORY SKILLS RUNTIME SYSTEM =====================

# ELEMENT CALCULATION SYSTEM
def calculate_move_element(scaling, species_name):
    """
    Automatically calculate the element of a move based on scaling and species.
    
    Args:
        scaling (dict): Dictionary with 'forz', 'des', 'spe' scaling values
        species_name (str): Name of the species (e.g., "Selkio", "Maedo", "Sapifer", "Minnago")
        
    Returns:
        str: The calculated element for the move
    """
    # Get species configuration
    species_config = get_species_config(species_name)
    if not species_config:
        # Fallback to default if species not found
        print(f"[Element Calculation] Warning: Species '{species_name}' not found, using default elements")
        return "IMPACT"  # Default fallback element
    
    # Check if move has special scaling (spe > 0)
    special_scaling = scaling.get('spe', 0)
    
    if special_scaling >= 1:
        # Move uses special scaling - use special element
        return species_config.get('special_element', 'IMPACT')
    else:
        # Move uses only physical scaling (strength/dexterity) - use normal element
        return species_config.get('normal_element', 'IMPACT')

# PROPERTY EFFECTS SYSTEM
def get_move_property_effects(move):
    """
    Extract all property effects from a move's effect list.
    
    Args:
        move: Move object with eff_appl attribute
        
    Returns:
        list: List of property effect names found in the move
    """
    property_effects = []
    
    if not hasattr(move, 'eff_appl') or not move.eff_appl:
        return property_effects
    
    for effect in move.eff_appl:
        # Effects are stored as [effect_name, level, duration, immunity_turns]
        if isinstance(effect, list) and len(effect) >= 1:
            effect_name = effect[0].lower().strip()
            if is_property_effect(effect_name):
                property_effects.append(effect_name)
    
    return property_effects

def has_property_effect(move, property_name):
    """
    Check if a move has a specific property effect.
    
    Args:
        move: Move object
        property_name (str): Name of the property to check for
        
    Returns:
        bool: True if move has the property effect
    """
    property_effects = get_move_property_effects(move)
    return property_name.lower().strip() in property_effects

def apply_rhythm_damage_bonus(base_damage, rhythm_count):
    """
    Calculate damage bonus from rhythm property effects.
    
    Args:
        base_damage (int): Base damage of the move
        rhythm_count (int): Number of consecutive rhythm moves used this turn
        
    Returns:
        int: Total damage with rhythm bonus applied (rounded down)
    """
    if rhythm_count <= 0:
        return base_damage
    
    # Get rhythm configuration
    rhythm_config = get_property_config('rhythm')
    if not rhythm_config:
        return base_damage
    
    # Calculate bonus: 10% per rhythm move (rounded down)
    bonus_percentage = rhythm_config.get('damage_bonus_per_stack', 10)
    total_bonus_percentage = bonus_percentage * rhythm_count
    bonus_damage = int((base_damage * total_bonus_percentage) / 100)
    
    print(f"[RHYTHM] Base damage: {base_damage}, Rhythm count: {rhythm_count}, Bonus: +{bonus_damage} ({total_bonus_percentage}%)")
    
    return base_damage + bonus_damage

def check_clean_cut_threshold(damage, target_part):
    """
    Check if clean cut should trigger and calculate final damage.
    
    Args:
        damage (int): Original damage to deal
        target_part: Target body part object
        
    Returns:
        tuple: (final_damage, clean_cut_triggered)
    """
    clean_cut_config = get_property_config('clean_cut')
    if not clean_cut_config:
        return damage, False
    
    threshold_percentage = clean_cut_config.get('damage_threshold', 50)
    max_hp = getattr(target_part, 'p_pvt_max', getattr(target_part, 'p_pvt', 1))
    threshold_damage = int((max_hp * threshold_percentage) / 100)
    
    if damage >= threshold_damage:
        # Clean cut triggers - deal double damage (effectively sets HP to 0)
        final_damage = max_hp  # Set HP to 0 immediately
        print(f"[CLEAN CUT] Triggered! Damage {damage} >= {threshold_percentage}% of {max_hp} HP. Dealing {final_damage} damage.")
        return final_damage, True
    
    return damage, False

def apply_lifesteal_healing(attacker, damage_dealt):
    """
    Apply lifesteal healing to the attacker.
    
    Args:
        attacker: Character object that dealt the damage
        damage_dealt (int): Amount of damage that was actually dealt
        
    Returns:
        int: Amount of HP healed
    """
    lifesteal_config = get_property_config('lifesteal')
    if not lifesteal_config:
        return 0
    
    heal_percentage = lifesteal_config.get('heal_percentage', 50)
    heal_amount = int((damage_dealt * heal_percentage) / 100)  # Rounded down
    
    if heal_amount > 0:
        # Find the most damaged body part (lowest HP percentage)
        most_damaged_part = None
        lowest_hp_percentage = 1.0
        
        for part in attacker.body_parts:
            if part.p_pvt < part.max_p_pvt:  # Only consider damaged parts
                hp_percentage = part.p_pvt / part.max_p_pvt
                if hp_percentage < lowest_hp_percentage:
                    lowest_hp_percentage = hp_percentage
                    most_damaged_part = part
        
        if most_damaged_part:
            # Heal the most damaged body part
            old_part_hp = most_damaged_part.p_pvt
            most_damaged_part.p_pvt = min(most_damaged_part.max_p_pvt, most_damaged_part.p_pvt + heal_amount)
            actual_heal = most_damaged_part.p_pvt - old_part_hp
            
            # Recalculate character's total HP
            attacker.calculate_health_from_body_parts()
            
            print(f"[LIFESTEAL] {attacker.name} healed {actual_heal} HP to {most_damaged_part.name} (from {heal_amount} calculated heal)")
            return actual_heal
        else:
            # No damaged parts, heal total HP as fallback
            old_hp = attacker.pvt
            max_hp = getattr(attacker, 'pvt_max', attacker.pvt)
            attacker.pvt = min(max_hp, attacker.pvt + heal_amount)
            actual_heal = attacker.pvt - old_hp
            
            print(f"[LIFESTEAL] {attacker.name} healed {actual_heal} HP to total HP (no damaged parts)")
            return actual_heal
    
    return 0

# Import Player_Moves system with lazy loading to avoid circular imports
PLAYER_MOVES_AVAILABLE = False
stamina_cost_per_regeneration = 3
# Dodge and Shield system configuration
DodgeShield_Stamina_Cost = 3
# Regeneration RIG cost configuration
rig_cost_per_regeneration = 5
#Swap_weapon_cost 
swap_weapon_cost = 3
#Equip/unequip cost
equip_unequip_cost = 2
# Scaling factors for buff/debuff effects on stats
STAT_SCALING_FACTORS = {
    'rig': 5.0,    # rigenerazione scaling factor
    'res': 30.0,    # Riserva scaling factor
    'sta': 1.0,    # Stamina scaling factor
    'forz': 2.0,   # Forza scaling factor
    'des': 2.0,    # Destrezza scaling factor
    'spe': 2.0,    # Speedy scaling factor
    'vel': 1.0     # Velocità scaling factor
}

# Scaling factors for move stamina cost calculations
MOVE_STAMINA_SCALING_FACTORS = {
    'eff_stm_sca_factor': 1,  # Effect stamina scaling factor (each effect multiplied by this)
    'req_stm_sca_factor': 1   # Requirement stamina scaling factor (each requirement multiplied by this) - set to 0 to disable requirement reduction
}

# Turn tracking variables
turn_player = 0     # Number of turns the player has completed
turn_enemy = 0      # Number of turns the enemy has completed
Turn = 1            # Overall turn counter (increases after both characters play)

# Speed-based turn system variables
current_round = 0   # Current round number (for "TURN X" display)
turn_queue = []     # Queue of characters in order of speed (highest first)
current_turn_index = 0  # Index of current character in turn_queue
first_turn_of_round = True  # Flag to show turn order messages

# Rhythm tracking system for property effects
rhythm_tracking = {
    'player': 0,    # Number of consecutive rhythm moves used by player this turn
    'enemy': 0      # Number of consecutive rhythm moves used by enemy this turn
}

# Music system initialization and functions
def initialize_music():
    """Initialize pygame mixer for background music"""
    try:
        pygame.mixer.init()
        print("Music system initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize music system: {e}")
        return False

def play_background_music(music_path, volume=1, loops=-1):
    """
    Play background music on loop
    
    Args:
        music_path (str): Path to the music file
        volume (float): Volume level (0.0 to 1.0)
        loops (int): Number of loops (-1 for infinite loop)
    """
    try:
        # Check if the music file exists
        import os
        if not os.path.exists(music_path):
            print(f"Music file not found: {music_path}")
            return False
            
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)
        print(f"Background music started: {music_path}")
        return True
    except Exception as e:
        print(f"Failed to play background music: {e}")
        return False

def stop_background_music():
    """Stop the background music"""
    try:
        pygame.mixer.music.stop()
        print("Background music stopped")
    except Exception as e:
        print(f"Failed to stop background music: {e}")

def set_music_volume(volume):
    """Set the music volume (0.0 to 1.0)"""
    try:
        pygame.mixer.music.set_volume(volume)
        print(f"Music volume set to: {volume}")
    except Exception as e:
        print(f"Failed to set music volume: {e}")

# Music file path - corrected to point to main directory
# Current file is in Overworld/Mappe/FilesPy, so we need to go up 3 levels to reach main directory
BACKGROUND_MUSIC_PATH = Path(__file__).resolve().parent.parent.parent.parent / "Musics" / "Battle-Walzer.MP3"

# Sound effects folder path - corrected to point to main directory  
SOUND_EFFECTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "Sound Effects"

# Dictionary to cache loaded sound effects
sound_effects_cache = {}

# Global volume settings
global_music_volume = 0.7
# global_sfx_volume removed - now using Global_SFX module

def load_sound_effect(sound_name):
    """
    Load a sound effect from the Sound Effects folder and cache it.
    
    Args:
        sound_name (str): Name of the sound file (with or without extension)
    
    Returns:
        pygame.mixer.Sound: Loaded sound object, or None if failed
    """
    # If already cached, return it
    if sound_name in sound_effects_cache:
        return sound_effects_cache[sound_name]
    
    # Common audio file extensions to try
    extensions = ['.wav', '.mp3', '.ogg', '.flac']
    sound_path = None
    
    # If sound_name already has an extension, try it first
    if '.' in sound_name:
        potential_path = SOUND_EFFECTS_PATH / sound_name
        if potential_path.exists():
            sound_path = potential_path
    
    # If not found, try adding common extensions
    if sound_path is None:
        base_name = sound_name.split('.')[0]  # Remove extension if present
        for ext in extensions:
            potential_path = SOUND_EFFECTS_PATH / f"{base_name}{ext}"
            if potential_path.exists():
                sound_path = potential_path
                break
    
    if sound_path is None:
        print(f"Sound effect not found: {sound_name} in {SOUND_EFFECTS_PATH}")
        # Debug: Try alternative path for sound effects
        import pathlib
        alt_sound_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "Sound Effects"
        print(f"Trying alternative sound effects path: {alt_sound_path}")
        if alt_sound_path.exists():
            # Try with the alternative path
            for ext in extensions:
                potential_path = alt_sound_path / f"{base_name}{ext}"
                if potential_path.exists():
                    sound_path = potential_path
                    print(f"Found sound with alternative path: {sound_path}")
                    break
        if sound_path is None:
            return None
    
    try:
        sound = pygame.mixer.Sound(str(sound_path))
        sound_effects_cache[sound_name] = sound
        print(f"Loaded sound effect: {sound_path}")
        return sound
    except Exception as e:
        print(f"Failed to load sound effect {sound_path}: {e}")
        return None

def play_sound_effect(sound_name, volume=1.0, loops=0):
    """
    Play a sound effect from the Sound Effects folder, applying global volume settings.
    
    Args:
        sound_name (str): Name of the sound file (with or without extension)
        volume (float): Volume level (0.0 to 1.0) - will be multiplied by global SFX volume
        loops (int): Number of additional loops (0 = play once, -1 = loop forever)
    
    Returns:
        bool: True if sound was played successfully, False otherwise
    """
    print(f"[DEBUG SOUND] play_sound_effect called: {sound_name}, volume={volume}, loops={loops}")
    try:
        sound = load_sound_effect(sound_name)
        if sound is None:
            print(f"[DEBUG SOUND] Sound loading failed for: {sound_name}")
            return False
        
        # Use Global_SFX module for centralized volume management
        global_sfx_volume = Global_SFX.get_global_sfx_volume()
        final_volume = min(1.0, volume * global_sfx_volume)
        sound.set_volume(final_volume)
        sound.play(loops)
        print(f"[DEBUG SOUND] Successfully playing: {sound_name} (base volume: {volume}, global SFX: {global_sfx_volume}, final: {final_volume}, loops: {loops})")
        return True
    except Exception as e:
        print(f"[DEBUG SOUND] Failed to play sound effect {sound_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def stop_all_sound_effects():
    """Stop all currently playing sound effects"""
    try:
        pygame.mixer.stop()
        print("All sound effects stopped")
    except Exception as e:
        print(f"Failed to stop sound effects: {e}")

def set_sound_effects_volume(volume):
    """
    Set the volume for all cached sound effects.
    
    Args:
        volume (float): Volume level (0.0 to 1.0)
    """
    try:
        for sound_name, sound in sound_effects_cache.items():
            sound.set_volume(volume)
        print(f"Set volume for all sound effects to: {volume}")
    except Exception as e:
        print(f"Failed to set sound effects volume: {e}")

def list_available_sound_effects():
    """
    List all available sound effect files in the Sound Effects folder.
    
    Returns:
        list: List of sound file names
    """
    sound_files = []
    if SOUND_EFFECTS_PATH.exists():
        extensions = ['.wav', '.mp3', '.ogg', '.flac']
        for file_path in SOUND_EFFECTS_PATH.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                sound_files.append(file_path.name)
    else:
        print(f"Sound Effects folder not found: {SOUND_EFFECTS_PATH}")
    
    return sound_files

def preload_sound_effects():
    """
    Preload all sound effects from the Sound Effects folder for better performance.
    Call this function at game startup to avoid loading delays during gameplay.
    """
    sound_files = list_available_sound_effects()
    loaded_count = 0
    
    print(f"Preloading {len(sound_files)} sound effects...")
    for sound_file in sound_files:
        if load_sound_effect(sound_file) is not None:
            loaded_count += 1
    
    print(f"Successfully preloaded {loaded_count}/{len(sound_files)} sound effects")
    return loaded_count

def update_character_stats(character):
    """
    Update current stats based on max stats and buffs/debuffs with scaling factors.
    Formula: current_stat = max_stat + (buf_stat_level * scaling_factor)
    Note: For stamina, we calculate the maximum possible stamina but don't override current stamina
    if it has been reduced (e.g., from move usage).
    """
    # Map of stat names to their max and current attributes and buffs attributes
    stat_mappings = {
        'rig': ('max_rig', 'rig', 'buf_rig'),
        'res': ('max_res', 'res', 'buf_res'),
        'sta': ('max_sta', 'sta', 'buf_sta'),
        'forz': ('max_for', 'forz', 'buf_forz'),
        'des': ('max_des', 'des', 'buf_des'),
        'spe': ('max_spe', 'spe', 'buf_spe'),
        'vel': ('max_vel', 'vel', 'buf_vel')
    }
    
    for stat_name, (max_attr, current_attr, buf_attr) in stat_mappings.items():
        if hasattr(character, max_attr) and hasattr(character, 'buffs') and hasattr(character, current_attr):
            max_value = getattr(character, max_attr)
            
            # Get buff level from the new buffs system
            if hasattr(character.buffs, buf_attr):
                buff_data = getattr(character.buffs, buf_attr)
                # buff_data is [name, level, duration] - we want level (index 1)
                buf_level = buff_data[1] if buff_data[2] > 0 else 0  # Only apply if duration > 0
            else:
                buf_level = 0
            
            scaling_factor = STAT_SCALING_FACTORS.get(stat_name, 1.0)
            
            # Calculate new maximum possible value: max + (buff_level * scaling_factor)
            new_max_possible = max_value + (buf_level * scaling_factor)
            new_max_possible = max(0, new_max_possible)
            
            if stat_name == 'sta':
                # For stamina, only update if current stamina is higher than the new max
                # (i.e., don't override reductions from move usage)
                current_value = getattr(character, current_attr)
                if current_value > new_max_possible:
                    setattr(character, current_attr, new_max_possible)
                # Update the character's effective max stamina for display purposes
                if not hasattr(character, 'effective_max_sta'):
                    character.effective_max_sta = new_max_possible
                else:
                    character.effective_max_sta = new_max_possible
            elif stat_name == 'rig':
                # For RIG, similar to stamina - don't override reductions from regeneration usage
                # Only update if current RIG is higher than the new max (to handle buffs/debuffs)
                current_value = getattr(character, current_attr)
                if current_value > new_max_possible:
                    setattr(character, current_attr, new_max_possible)
                # Update the character's effective max RIG for display purposes
                if not hasattr(character, 'effective_max_rig'):
                    character.effective_max_rig = new_max_possible
                else:
                    character.effective_max_rig = new_max_possible
            elif stat_name == 'res':
                # For RES, similar to RIG and STA - preserve consumption but apply buffs/debuffs
                current_value = getattr(character, current_attr)
                if current_value > new_max_possible:
                    setattr(character, current_attr, new_max_possible)
                # Update the character's effective max RES for display purposes
                if not hasattr(character, 'effective_max_res'):
                    character.effective_max_res = new_max_possible
                else:
                    character.effective_max_res = new_max_possible
            else:
                # For other stats (forz, des, spe, vel), update normally
                setattr(character, current_attr, new_max_possible)

def update_all_characters_stats():
    """
    Update stats for all characters in the game.
    This function should be called periodically to keep stats synchronized.
    """
    update_character_stats(player)
    update_character_stats(enemy)

def set_stat_scaling_factor(stat_name, scaling_factor):
    """
    Set the scaling factor for a specific stat.
    
    Args:
        stat_name (str): Name of the stat ('rig', 'res', 'sta', 'forz', 'des', 'spe', 'vel')
        scaling_factor (float): The scaling factor to apply to buff/debuff values
    """
    if stat_name in STAT_SCALING_FACTORS:
        STAT_SCALING_FACTORS[stat_name] = scaling_factor
        print(f"Set scaling factor for {stat_name} to {scaling_factor}")
        # Immediately update stats to reflect the change
        update_all_characters_stats()
    else:
        print(f"Invalid stat name '{stat_name}'. Valid stats are: {list(STAT_SCALING_FACTORS.keys())}")

def set_move_stamina_scaling_factor(factor_name, scaling_factor):
    """
    Set the scaling factor for move stamina calculations.
    
    Args:
        factor_name (str): Name of the factor ('eff_stm_sca_factor' or 'req_stm_sca_factor')
        scaling_factor (float): The scaling factor to apply
    """
    if factor_name in MOVE_STAMINA_SCALING_FACTORS:
        MOVE_STAMINA_SCALING_FACTORS[factor_name] = scaling_factor
        print(f"Set move stamina scaling factor for {factor_name} to {scaling_factor}")
    else:
        print(f"Invalid factor name '{factor_name}'. Valid factors are: {list(MOVE_STAMINA_SCALING_FACTORS.keys())}")

def display_scaling_factors():
    """
    Display all current scaling factors for stats and move stamina calculations.
    """
    print("\n" + "="*50)
    print("CURRENT SCALING FACTORS")
    print("="*50)
    
    print("\nStat Scaling Factors:")
    for stat_name, factor in STAT_SCALING_FACTORS.items():
        print(f"  {stat_name.upper()}: {factor}")
    
    print("\nMove Stamina Scaling Factors:")
    for factor_name, factor in MOVE_STAMINA_SCALING_FACTORS.items():
        print(f"  {factor_name}: {factor}")
    print("="*50)

#CALCULATE MOVE DAMAGE CALCULATION

def calculate_move_damage(character, strength_scaling, dexterity_scaling, special_scaling):
    current_strength = getattr(character, 'forz', 0)
    current_dexterity = getattr(character, 'des', 0)
    current_special = getattr(character, 'spe', 0)
    
    damage = (strength_scaling * current_strength / 5 + 
              dexterity_scaling * current_dexterity / 5 + 
              special_scaling * current_special / 5)

    return max(0, round(damage))  # Ensure damage is not negative and is an integer

def apply_elemental_damage(base_damage, move, target_character, battle_menu_instance):
    """
    Apply elemental damage calculation including resistances, weaknesses, and immunities.
    
    Args:
        base_damage: The base damage before elemental effects
        move: The move being used (with elem attribute)
        target_character: The target character receiving damage
        battle_menu_instance: The battle menu instance for logging
    
    Returns:
        tuple: (final_damage, effects_applied)
    """
    if not hasattr(move, 'elem') or not move.elem:
        # No element specified, return base damage
        return base_damage, True
    
    # Get target species
    target_species = getattr(target_character, 'species', 'Maedo')
    

    
    # Process each element in the move (moves can have multiple elements)
    final_damage = base_damage
    effects_applied = True
    
    for element in move.elem:
        # Apply elemental calculation for this element
        elemental_damage, element_effects_applied = calculate_elemental_damage(
            final_damage, element, target_species
        )
        
        # If any element grants immunity, no damage and no effects
        if elemental_damage == 0 and not element_effects_applied:
            battle_menu_instance.add_log_entry(
                f"IMMUNE to {element}! No damage or effects applied!", 
                "effect", (100, 100, 255)
            )
            return 0, False
        
        # Apply damage modifier and log if changed
        if elemental_damage != final_damage:
            damage_change = elemental_damage - final_damage
            if damage_change > 0:
                battle_menu_instance.add_log_entry(
                    f"WEAK to {element}! +{damage_change} damage!", 
                    "effect", (255, 100, 100)
                )
            else:
                battle_menu_instance.add_log_entry(
                    f"RESISTS {element}! {damage_change} damage!", 
                    "effect", (100, 255, 100)
                )
        
        final_damage = elemental_damage
        effects_applied = effects_applied and element_effects_applied
    
    return final_damage, effects_applied

def check_move_requirements(character, move, target_character=None, target_part=None):
    """
    Check if a character meets all requirements to use a move.
    
    Args:
        character: The character trying to use the move
        move: The move to check requirements for
        target_character: The target character (for target-based requirements)
        target_part: The specific target body part (for target-based requirements)
    
    Returns:
        tuple: (can_use: bool, failed_requirements: list)
    """
    global player
    def is_body_part_usable(body_part):
        """Check if a body part is usable (has >=2 HP and not paralyzed)"""
        if body_part.p_pvt < 2:
            return False
        
        # Check for paralysis effect using new status format
        if hasattr(body_part, 'p_eff') and hasattr(body_part.p_eff, 'paralysis'):
            paralysis_data = getattr(body_part.p_eff, 'paralysis')
            # Check if paralysis is active (level > 0 and duration > 0)
            # New format: ['paralysis', level, duration, immunity]
            if isinstance(paralysis_data, list) and len(paralysis_data) >= 3:
                level = paralysis_data[1] if len(paralysis_data) > 1 else 0
                duration = paralysis_data[2] if len(paralysis_data) > 2 else 0
                if level > 0 and duration > 0:
                    return False  # Body part is paralyzed
        
        return True

    def count_usable_hands(character):
        """Count the number of usable hands (arms with >=2 HP and not paralyzed)"""
        usable_hands = 0
        for body_part in character.body_parts:
            if "ARM" in body_part.name.upper() and is_body_part_usable(body_part):
                usable_hands += 1
        return usable_hands

    def check_weapon_hand_conflicts(character, move_requirements):
        """Check if equipped weapon conflicts with hand requirements"""
        try:
            # Try to import and get weapon restrictions
            import Player_Equipment
            if hasattr(Player_Equipment, 'player1'):
                player_equip = Player_Equipment.player1
                
                if player_equip:
                    # Check if weapon restricts hand usage
                    is_restricted = player_equip.check_weapon_hand_restrictions(move_requirements)
                    return is_restricted
        except (ImportError, AttributeError) as e:
            print(f"[Battle] Could not check weapon hand restrictions: {e}")
        
        return False
    
    if not hasattr(move, 'reqs') or not move.reqs:
        return True, []
    
    failed_requirements = []
    
    for i, requirement in enumerate(move.reqs):
        if not requirement:
            continue
            
        req_str = str(requirement).upper().strip()
        
        # Skip target-specific requirements if no target is provided (for pre-target-selection checks)
        if req_str.startswith("TARGET ") and target_part is None:
            continue  # These will be checked later when target is selected
        
        # Target-specific and status requirements: check TARGET format (MUST come before body part HP check)
        if req_str.startswith("TARGET "):
            target_requirement = req_str.replace("TARGET ", "").strip()
            
            # List of known body parts to distinguish from status effects
            body_parts = ["HEAD", "BODY", "RIGHT ARM", "LEFT ARM", "RIGHT LEG", "LEFT LEG", 
                         "RIGHT CLAW", "LEFT CLAW", "TENTACLES"]
            
            # Generic targeting requirements that match multiple body parts
            generic_targets = {
                "ARM": ["RIGHT ARM", "LEFT ARM"],
                "LEG": ["RIGHT LEG", "LEFT LEG"],
                "CLAW": ["RIGHT CLAW", "LEFT CLAW"],
                "TENTACLES": ["TENTACLES"]
            }
            
            if target_requirement.upper() in body_parts:
                # This is a specific body part targeting requirement
                if not target_part or target_part.name.upper() != target_requirement.upper():
                    failed_requirements.append(f"Must target {target_requirement}")
            elif target_requirement.upper() in generic_targets:
                # This is a generic targeting requirement (e.g., "ARM" matches either arm)
                valid_targets = generic_targets[target_requirement.upper()]
                if not target_part or target_part.name.upper() not in valid_targets:
                    valid_names = " or ".join(valid_targets)
                    failed_requirements.append(f"Must target {valid_names}")
            else:
                # This is a status effect requirement
                if not target_part:
                    failed_requirements.append(f"Target must have {target_requirement} status")
                else:
                    has_status = False
                    # Check the status effects in the target body part's p_eff
                    if hasattr(target_part, 'p_eff'):
                        # Check if the required status effect is active (level > 0)
                        effect_attr = getattr(target_part.p_eff, target_requirement.lower(), None)
                        if effect_attr and isinstance(effect_attr, list) and len(effect_attr) >= 2:
                            # effect_attr is [name, level, duration, immunity]
                            effect_level = effect_attr[1]
                            if effect_level > 0:
                                has_status = True
                    
                    if not has_status:
                        failed_requirements.append(f"Target must have {target_requirement} status")
        
        # Body part HP requirements: check if character has required body parts with >1 HP (NEEDS prefix)
        elif req_str.startswith("NEEDS"):
            # Handle NEEDS prefixed body part names (remove "NEEDS " prefix)
            needs_requirement = req_str.replace("NEEDS", "").strip()
            body_part_mapping = {
                "SWORD": ["RIGHT ARM", "LEFT ARM"],  # Sword requires an arm
                "TESTA": ["HEAD"],
                "2 GAMBE": ["RIGHT LEG", "LEFT LEG"],  # Both legs
                "GAMBE": ["RIGHT LEG", "LEFT LEG"],    # Either leg
                "RIGHTARM": ["RIGHT ARM"],
                "LEFTARM": ["LEFT ARM"],
                "ARM": ["RIGHT ARM", "LEFT ARM"],      # Either arm
                "HEAD": ["HEAD"],
                "BODY": ["BODY"],
                "RIGHT LEG": ["RIGHT LEG"],
                "LEFT LEG": ["LEFT LEG"],
                "LEG": ["RIGHT LEG", "LEFT LEG"],       # Either leg
                "2 ARMS": ["RIGHT ARM", "LEFT ARM"],    # Both arms
                "2 LEGS": ["RIGHT LEG", "LEFT LEG"],    # Both legs
                "TENTACLES": ["TENTACLES"], # Single unified tentacles body part
            }
            requirement_met = False
            # Check if needs_requirement matches any key in the mapping
            if needs_requirement in body_part_mapping:
                required_parts = body_part_mapping[needs_requirement]
                if "2 " in needs_requirement:  # Requires both parts
                    all_parts_healthy = True
                    for part_name in required_parts:
                        matching_part = None
                        for body_part in character.body_parts:
                            if body_part.name.upper() == part_name.upper():
                                matching_part = body_part
                                break
                        if not matching_part or not is_body_part_usable(matching_part):
                            all_parts_healthy = False
                            break
                    if all_parts_healthy:
                        requirement_met = True
                else:  # Requires at least one part
                    for part_name in required_parts:
                        for body_part in character.body_parts:
                            if body_part.name.upper() == part_name.upper() and is_body_part_usable(body_part):
                                requirement_met = True
                                break
                        if requirement_met:
                            break
            
            # DEBUG: Log ALL 2 ARMS requirement checks for enemies
            if "2 ARMS" in needs_requirement.upper() and hasattr(character, 'name') and ("SELKIO" in character.name.upper() or "MAEDO" in character.name.upper()):
                arms = [p for p in character.body_parts if "ARM" in p.name.upper()]
                print(f"[REQ DEBUG] {character.name} checking 2 ARMS requirement:")
                for arm in arms:
                    print(f"[REQ DEBUG] {arm.name}: {arm.p_pvt}/{arm.max_p_pvt} HP")
                print(f"[REQ DEBUG] Result: {requirement_met}")
            
            if not requirement_met:
                failed_requirements.append(f"Requires {needs_requirement} with ≥2 HP")
        
        # Handle special weapon requirements
        elif req_str == "WEAPON":
            # WEAPON requirement - check weapon type and hand requirements
            weapon_requirement_met = False
            usable_hands_count = count_usable_hands(character)
            
            # Try to get equipped weapon type and check specific requirements
            try:
                import Player_Equipment
                if hasattr(Player_Equipment, 'player1') and character == player:
                    player_equip = Player_Equipment.player1
                    equipped_weapon = player_equip.get_equipped_by_type('weapon')
                    if equipped_weapon:
                        weapon_type = equipped_weapon.get_weapon_type()
                        
                        if weapon_type == "One Handed":
                            # Requires at least 1 usable hand
                            if usable_hands_count >= 1:
                                weapon_requirement_met = True
                            
                        elif weapon_type == "One and a Half Handed":
                            # Can be used with 1 or 2 hands
                            if usable_hands_count >= 1:
                                weapon_requirement_met = True
                                print(f"[Battle] One and a Half Handed weapon requirement satisfied - {usable_hands_count} usable hands")
                            else:
                                print(f"[Battle] One and a Half Handed weapon requirement failed - need 1 hand, have {usable_hands_count}")
                        
                        elif weapon_type == "Two Handed":
                            # Requires exactly 2 usable hands
                            if usable_hands_count >= 2:
                                weapon_requirement_met = True
                        
                        else:
                            # Unknown weapon type, default to basic check
                            if usable_hands_count >= 1:
                                weapon_requirement_met = True
                    
                else:
                    # Fallback for non-player characters or no equipment system
                    if usable_hands_count >= 1:
                        weapon_requirement_met = True
                        print(f"[Battle] Basic WEAPON requirement satisfied - {usable_hands_count} usable hands")
            except (ImportError, AttributeError) as e:
                print(f"[Battle] Could not check weapon type, using basic check: {e}")
                # Fallback to basic weapon requirement
                if usable_hands_count >= 1:
                    weapon_requirement_met = True
                    print(f"[Battle] Fallback WEAPON requirement satisfied - {usable_hands_count} usable hands")
            
            if not weapon_requirement_met:
                failed_requirements.append("Requires sufficient hands to wield weapon")
        
        # Backward compatibility: Handle old format body parts without "NEEDS" prefix
        else:
            # Try to match as a body part requirement (for backward compatibility)
            body_part_mapping = {
                "SWORD": ["RIGHT ARM", "LEFT ARM"],  # Sword requires an arm
                "TESTA": ["HEAD"],
                "2 GAMBE": ["RIGHT LEG", "LEFT LEG"],  # Both legs
                "GAMBE": ["RIGHT LEG", "LEFT LEG"],    # Either leg
                "RIGHTARM": ["RIGHT ARM"],
                "LEFTARM": ["LEFT ARM"],
                "ARM": ["RIGHT ARM", "LEFT ARM"],      # Either arm
                "HEAD": ["HEAD"],
                "BODY": ["BODY"],
                "RIGHT LEG": ["RIGHT LEG"],
                "LEFT LEG": ["LEFT LEG"],
                "LEG": ["RIGHT LEG", "LEFT LEG"],       # Either leg
                "2 ARMS": ["RIGHT ARM", "LEFT ARM"],    # Both arms
                "2 LEGS": ["RIGHT LEG", "LEFT LEG"],    # Both legs
                "TENTACLES": ["TENTACLES"], # Single unified tentacles body part
            }
            
            requirement_met = False
            for req_key, required_parts in body_part_mapping.items():
                if req_key in req_str:
                    if "2 " in req_str:  # Requires both parts
                        all_parts_healthy = True
                        for part_name in required_parts:
                            matching_part = None
                            for body_part in character.body_parts:
                                if body_part.name.upper() == part_name.upper():
                                    matching_part = body_part
                                    break
                            if not matching_part or not is_body_part_usable(matching_part):
                                all_parts_healthy = False
                                break
                        if all_parts_healthy:
                            requirement_met = True
                    else:  # Requires at least one part
                        for part_name in required_parts:
                            for body_part in character.body_parts:
                                if body_part.name.upper() == part_name.upper() and is_body_part_usable(body_part):
                                    requirement_met = True
                                    break
                            if requirement_met:
                                break
                    break
            
            if not requirement_met:
                failed_requirements.append(f"Unknown requirement or body part not available: {requirement}")

    # Check for weapon hand conflicts (must be done after processing all requirements)
    weapon_conflicts = check_weapon_hand_conflicts(character, move.reqs)
    if weapon_conflicts:
        failed_requirements.append("Equipped weapon occupies required hands")

    can_use = len(failed_requirements) == 0
    return can_use, failed_requirements

def calculate_buf_move_stamina_cost(effects=None, requirements=None, accuracy=100):
    """
    Calculate stamina cost for BUF moves using the correct formula:
    base_cost (2) + cost_of_buff * level - requirement_reduction + 1 (always 100% accuracy)
    """
    # Base cost
    base_cost = 2
    
    # Effect cost - cost of buff multiplied by level
    effect_cost = 0
    if effects:
        for effect in effects:
            if isinstance(effect, list) and len(effect) >= 2:
                # Format: [name, level, duration, immunity] - use level (index 1) and name (index 0)
                effect_name = effect[0] if len(effect) > 0 else ""
                effect_level = effect[1] if isinstance(effect[1], (int, float)) else 1
                # Get cost per level from config and multiply by effect level
                cost_per_level = get_effect_cost(effect_name)
                effect_cost += cost_per_level * effect_level
            else:
                # Old format - treat as string effect name with level 1
                effect_name = str(effect) if effect else ""
                cost_per_level = get_effect_cost(effect_name)
                effect_cost += cost_per_level
    
    # Requirement reduction - calculate based on requirement types
    requirement_reduction = 0
    if requirements:
        for requirement in requirements:
            if not requirement:
                continue
            req_str = str(requirement).upper().strip()
            # Body part requirements with NEEDS_ prefix: -1 stamina per required body part
            if req_str.startswith("NEEDS "):
                needs_req = req_str.replace("NEEDS ", "").strip()
                # Double requirements: -2 stamina for double requirements
                if needs_req.startswith("2 "):
                    requirement_reduction += 2
                # Single requirements: -1 stamina
                else:
                    requirement_reduction += 1
    
    # Apply scaling factor to requirement reduction
    requirement_reduction *= MOVE_STAMINA_SCALING_FACTORS['req_stm_sca_factor']
    
    # BUF moves always have +1 accuracy modifier (always 100% accuracy)
    accuracy_modifier = 1
    
    total_cost = base_cost + effect_cost - requirement_reduction + accuracy_modifier

    return max(2, round(total_cost))  # Ensure minimum cost of 2 and is an integer

def calculate_atk_move_stamina_cost(strength_scaling, dexterity_scaling, special_scaling, effects=None, requirements=None, accuracy=100):
    """
    Calculate stamina cost for ATK moves using the scaling-based formula
    """
    # Base cost
    base_cost = 2
    
    # Sum of all scaling values
    scaling_sum = strength_scaling + dexterity_scaling + special_scaling
    
    # Effect cost - now based on effect levels and individual effect costs from config
    effect_cost = 0
    if effects:
        for effect in effects:
            if isinstance(effect, list) and len(effect) >= 2:
                # New format: [name, level, duration, immunity] - use level (index 1) and name (index 0)
                effect_name = effect[0] if len(effect) > 0 else ""
                effect_level = effect[1] if isinstance(effect[1], (int, float)) else 1
                # Get cost per level from config and multiply by effect level
                cost_per_level = get_effect_cost(effect_name)
                effect_cost += cost_per_level * effect_level
            else:
                # Old format - treat as string effect name with level 1
                effect_name = str(effect) if effect else ""
                cost_per_level = get_effect_cost(effect_name)
                effect_cost += cost_per_level
    
    # Enhanced requirement reduction - calculate based on requirement types
    requirement_reduction = 0
    if requirements:
        for requirement in requirements:
            if not requirement:
                continue
            req_str = str(requirement).upper().strip()
            # If requirement is target-specific, count as target-specific
            if req_str.startswith("TARGET "):
                requirement_reduction += 1  # Target requirement (bodypart or status)
            # Body part requirements with NEEDS_ prefix: -1 stamina per required body part
            elif req_str.startswith("NEEDS "):
                needs_req = req_str.replace("NEEDS ", "").strip()
                # Double requirements: -2 stamina for double requirements
                if needs_req.startswith("2 "):
                    requirement_reduction += 2
                # Single requirements: -1 stamina
                else:
                    requirement_reduction += 1
                # Special weapon requirements: additional -1 stamina
                if "SWORD" in needs_req:
                    requirement_reduction += 1
                # Status effect requirements: -1 stamina (handles both 'STATUS ' and 'STATUS_')
                if req_str.startswith("STATUS ") or req_str.startswith("STATUS_"):
                    requirement_reduction += 1
            # Also handle 'TARGET_' and 'STATUS_' legacy formats
            if req_str.startswith("TARGET_"):
                requirement_reduction += 1
            if req_str.startswith("STATUS_"):
                requirement_reduction += 1
    
    # Apply scaling factor to requirement reduction
    requirement_reduction *= MOVE_STAMINA_SCALING_FACTORS['req_stm_sca_factor']
    requirement_reduction = min(requirement_reduction, 4)  # Cap reduction to not exceed total cost
    
    # Weapon type stamina bonus for weapon moves
    weapon_bonus = 0
    if requirements:
        for requirement in requirements:
            if str(requirement).upper().strip() == "WEAPON":
                # This is a weapon move, check for weapon type bonus
                try:
                    import Player_Equipment
                    if hasattr(Player_Equipment, 'player1'):
                        player_equip = Player_Equipment.player1
                        weapon_bonus = player_equip.get_equipped_weapon_stamina_bonus()
                except (ImportError, AttributeError) as e:
                    print(f"[Battle] Could not get weapon stamina bonus: {e}")
                break  # Only check once for weapon requirement
    
    # Accuracy modifier calculation (new balanced system)
    # Based on balanced analysis: 30% = -5, 50% = -3, 90% = 0, 100% = +1
    accuracy_modifier = 0
    if accuracy == 100:
        accuracy_modifier = 1
    elif accuracy == 90:
        accuracy_modifier = 0
    elif accuracy == 50:
        accuracy_modifier = -1
    elif accuracy == 30:
        accuracy_modifier = -2
    # Only these 4 accuracy values (30, 50, 90, 100) are supported
    
    total_cost = base_cost + scaling_sum + effect_cost - requirement_reduction + accuracy_modifier + weapon_bonus

    return max(2, round(total_cost))  # Ensure minimum cost of 2 and is an integer

def calculate_move_stamina_cost(strength_scaling, dexterity_scaling, special_scaling, effects=None, requirements=None, accuracy=100, move_type=None):
    """
    Calculate stamina cost for any move type (maintains backward compatibility)
    """
    # If move type is explicitly BUF, use BUF formula
    if move_type == "BUF":
        return calculate_buf_move_stamina_cost(effects, requirements, accuracy)
    else:
        # Default to ATK formula for backward compatibility
        return calculate_atk_move_stamina_cost(strength_scaling, dexterity_scaling, special_scaling, effects, requirements, accuracy)

def recalculate_character_moves(character):
    """
    Recalculate damage and stamina cost for all moves of a character.
    This should be called when a character's stats change.
    
    Args:
        character: The character object
    """
    if not hasattr(character, 'moves') or character.moves is None:
        return
    
    char_name = getattr(character, 'name', 'Unknown')
    
    for move in character.moves:
        old_damage = move.danno
        old_stamina = move.stamina_cost
        
        # Recalculate damage and stamina cost (now including accuracy)
        move.danno = calculate_move_damage(character, move.sca_for, move.sca_des, move.sca_spe)
        move.stamina_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs, move.accuracy)
        
        if old_damage != move.danno or old_stamina != move.stamina_cost:
            print(f"  {move.name}: Damage {old_damage} -> {move.danno}, Stamina {old_stamina} -> {move.stamina_cost}")

def recalculate_all_character_moves():
    """
    Recalculate moves for all characters in the game.
    This function should be called when stat scaling factors change.
    """
    recalculate_character_moves(player)
    recalculate_character_moves(enemy)

def recalculate_all_character_health():
    """
    Recalculate health for all characters based on their body parts.
    This function should be called when body part health changes.
    """
    player.calculate_health_from_body_parts()
    enemy.calculate_health_from_body_parts()

def refill_player_rig_with_res():
    """
    Refill player RIG using RES as fuel.
    RES is consumed to restore RIG at 1:1 ratio.
    
    Returns:
        tuple: (rig_restored, res_consumed, message)
    """
    # Calculate how much RIG needs to be restored
    rig_needed = player.max_rig - player.rig
    
    if rig_needed <= 0:
        return 0, 0, f"{player.name} RIG già al massimo: {player.rig}/{player.max_rig}"
    
    # Check available RES
    available_res = player.res
    
    if available_res <= 0:
        return 0, 0, f"{player.name} non ha RES per rigenerare! RES: {player.res}/{player.max_res}"
    
    # Calculate how much we can actually restore
    rig_to_restore = min(rig_needed, available_res)
    
    # Apply the restoration
    old_rig = player.rig
    old_res = player.res
    
    player.rig += rig_to_restore
    player.res -= rig_to_restore
    
    # Update character stats to ensure RES changes are reflected properly
    update_character_stats(player)
    
    # Create message based on whether full restoration was possible
    if rig_to_restore == rig_needed:
        message = f"{player.name} RIG completamente ripristinata: {old_rig} -> {player.rig} (RES: {old_res} -> {player.res})"
    else:
        message = f"{player.name} RIG parzialmente ripristinata: {old_rig} -> {player.rig} (RES esaurita: {old_res} -> {player.res})"
    
    return rig_to_restore, rig_to_restore, message

def refill_enemy_rig_with_res():
    """
    Refill enemy RIG using RES as fuel.
    RES is consumed to restore RIG at 1:1 ratio.
    
    Returns:
        tuple: (rig_restored, res_consumed, message)
    """
    # Calculate how much RIG needs to be restored
    rig_needed = enemy.max_rig - enemy.rig
    
    if rig_needed <= 0:
        return 0, 0, f"{enemy.name} RIG già al massimo: {enemy.rig}/{enemy.max_rig}"
    
    # Check available RES
    available_res = enemy.res
    
    if available_res <= 0:
        return 0, 0, f"{enemy.name} non ha RES per rigenerare! RES: {enemy.res}/{enemy.max_res}"
    
    # Calculate how much we can actually restore
    rig_to_restore = min(rig_needed, available_res)
    
    # Apply the restoration
    old_rig = enemy.rig
    old_res = enemy.res
    
    enemy.rig += rig_to_restore
    enemy.res -= rig_to_restore
    
    # Update character stats to ensure RES changes are reflected properly
    update_character_stats(enemy)
    
    # Create message based on whether full restoration was possible
    if rig_to_restore == rig_needed:
        message = f"{enemy.name} RIG completamente ripristinata: {old_rig} -> {enemy.rig} (RES: {old_res} -> {enemy.res})"
    else:
        message = f"{enemy.name} RIG parzialmente ripristinata: {old_rig} -> {enemy.rig} (RES esaurita: {old_res} -> {enemy.res})"
    
   
    return rig_to_restore, rig_to_restore, message

def find_most_damaged_enemy_parts():
    """
    Find enemy body parts that are most damaged (lowest p_pvt).
    Returns a list of part indices sorted by damage level (most damaged first).
    
    Returns:
        list: List of (part_index, part, damage_ratio) tuples sorted by damage level
    """
    damaged_parts = []
    
    for idx, part in enumerate(enemy.body_parts):
        # Consider damaged parts, including those at 0 HP
        if part.p_pvt < part.max_p_pvt:
            damage_ratio = part.p_pvt / part.max_p_pvt if part.max_p_pvt > 0 else 0
            damaged_parts.append((idx, part, damage_ratio))
    
    # Sort by damage ratio (lowest first = most damaged)
    damaged_parts.sort(key=lambda x: x[2])
    
    print(f"DEBUG: Found {len(damaged_parts)} damaged enemy parts")
    for idx, (part_idx, part, ratio) in enumerate(damaged_parts[:3]):  # Show top 3 most damaged
        print(f"  {idx+1}. {part.name}: {part.p_pvt}/{part.max_p_pvt} ({ratio:.2%})")
    
    return damaged_parts

def enemy_auto_regenerate():
    """
    Automatically regenerate the most damaged enemy body part if resources allow.
    Uses the same regeneration logic as the player but without UI messages.
    
    Returns:
        bool: True if regeneration was performed, False otherwise
    """
    # Check if enemy has enough RIG to regenerate
    if enemy.rig < 5:
        print(f"DEBUG: {enemy.name} cannot regenerate - insufficient RIG: {enemy.rig}/5")
        return False
    
    # Check if enemy has enough stamina (uses stamina_cost_per_regeneration)
    if enemy.sta < stamina_cost_per_regeneration:
        print(f"DEBUG: {enemy.name} cannot regenerate - insufficient STA: {enemy.sta}/{stamina_cost_per_regeneration}")
        return False
    
    # Find damaged parts
    damaged_parts = find_most_damaged_enemy_parts()
    
    if not damaged_parts:
        print(f"DEBUG: {enemy.name} has no damaged parts to regenerate")
        return False
    
    # Select the most damaged part (first in the sorted list)
    part_index, part, damage_ratio = damaged_parts[0]
    
    print(f"DEBUG: {enemy.name} attempting to regenerate {part.name} (damage: {damage_ratio:.2%})")
    
    # Use the new enemy-specific regeneration function
    success = regenerate_enemy_body_part(enemy, part_index)
    
    if success:
        print(f"DEBUG: {enemy.name} successfully regenerated {part.name}")
    else:
        print(f"DEBUG: {enemy.name} failed to regenerate {part.name}")
    
    return success

# OLD REGENERATION SYSTEM REMOVED - NOW HANDLED BY Enemy_AI_V2.py
# All enemy regeneration decisions are now part of the priority point AI system
# This ensures strategic regeneration integrated with attack/buff decisions

def regenerate_enemy_body_part(character, part_index):
    """
    Regenerate a specific enemy body part if the character has enough resources.
    Similar to player regeneration but without UI messages and updates.
    
    Args:
        character: The character object (should be enemy)
        part_index: Index of the body part to regenerate
    
    Returns:
        bool: True if regeneration was successful, False otherwise
    """
    # Check if part index is valid
    if not (0 <= part_index < len(character.body_parts)):
        print(f"Invalid body part index {part_index} for character {getattr(character, 'name', 'Unknown')}")
        return False
    
    part = character.body_parts[part_index]
    
    if part.p_pvt >= part.max_p_pvt:
        print(f"DEBUG: {character.name}'s {part.name} is already at full health")
        return False

    # Check for MESS UP effect FIRST - reduces level instead of healing
    if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'mess_up'):
        mess_up_data = getattr(part.p_eff, 'mess_up')
        # Check if mess_up is active (level > 0)
        if len(mess_up_data) >= 2 and mess_up_data[1] > 0:
            # Check regeneration (rig) resource first
            if character.rig < 5:
                print(f"DEBUG: {character.name} cannot regenerate - insufficient RIG: {character.rig}/5")
                return False

            # Check stamina resource (uses stamina_cost_per_regeneration)
            if character.sta < stamina_cost_per_regeneration:
                print(f"DEBUG: {character.name} cannot regenerate - insufficient STA: {character.sta}/{stamina_cost_per_regeneration}")
                return False
            
            mess_up_level = mess_up_data[1]
            # Reduce mess_up level by 1 instead of healing
            new_level = max(0, mess_up_level - 1)
            setattr(part.p_eff, 'mess_up', [mess_up_data[0], new_level, mess_up_data[2], mess_up_data[3]])
            
            print(f"DEBUG: {character.name}'s {part.name} MESS UP reduced from level {mess_up_level} to {new_level}")
            
            # Consume resources but NO HEALING
            old_rig = character.rig
            old_sta = character.sta
            character.rig -= 5
            character.sta -= stamina_cost_per_regeneration
            
            print(f"⚡ ENEMY REGEN STAMINA: {character.name} regeneration consumed (mess up) - RIG: {old_rig} -> {character.rig}, STA: {old_sta} -> {character.sta} (-{stamina_cost_per_regeneration}) - NO HEALING")
            
            if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                globals()['battle_menu_instance'].add_log_entry(f"{character.name}'s {part.name} mess up reduced to level {new_level} - no healing", "effect", (200, 150, 100))
            
            return True  # Regeneration was "successful" but no healing occurred

    # Check for AMPUTATE effect blocking regeneration
    if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'amputate'):
        amputate_data = getattr(part.p_eff, 'amputate')
        # Check if amputate is active (level > 0 and duration > 0)
        if len(amputate_data) >= 3 and amputate_data[1] > 0 and amputate_data[2] > 0:
            print(f"DEBUG: {character.name}'s {part.name} cannot regenerate - AMPUTATED")
            return False

    # Check regeneration (rig) resource
    if character.rig < 5:
        print(f"DEBUG: {character.name} cannot regenerate - insufficient RIG: {character.rig}/5")
        return False

    # Check stamina resource (uses stamina_cost_per_regeneration)
    if character.sta < stamina_cost_per_regeneration:
        print(f"DEBUG: {character.name} cannot regenerate - insufficient STA: {character.sta}/{stamina_cost_per_regeneration}")
        return False

    # Apply regeneration
    old_pvt = part.p_pvt
    if part.p_pvt == 0:
        # Revive dead parts to 1 HP only (requires 2 heals to become usable at ≥2 HP)
        part.p_pvt = 1
        actual_healing = 1
        # Lose 5 regen if available
        if hasattr(character, 'regen') and character.regen is not None:
            character.regen = max(0, character.regen - 5)
            print(f"DEBUG: {character.name} lost 5 regen for reviving {part.name} to 1 HP. New regen: {character.regen}")
    else:
        # All other cases: heal by +5 HP normally
        part.p_pvt = min(part.p_pvt + 5, part.max_p_pvt)
        actual_healing = part.p_pvt - old_pvt

    # Nerf status effects on this part
    if 'nerf_status_effects_on_part' in globals():
        globals()['nerf_status_effects_on_part'](part)
    elif hasattr(globals().get('battle_menu_instance', None), 'nerf_status_effects_on_part'):
        globals()['battle_menu_instance'].nerf_status_effects_on_part(part)
    elif hasattr(globals().get('ui', None), 'nerf_status_effects_on_part'):
        globals()['ui'].nerf_status_effects_on_part(part)

    # Consume resources (uses stamina_cost_per_regeneration)
    old_rig = character.rig
    old_sta = character.sta
    character.rig -= 5
    character.sta -= stamina_cost_per_regeneration

    print(f"⚡ ENEMY REGEN STAMINA: {character.name} regeneration consumed - RIG: {old_rig} -> {character.rig}, STA: {old_sta} -> {character.sta} (-{stamina_cost_per_regeneration})")
    
    # Also add to combat log for visibility
    if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
        globals()['battle_menu_instance'].add_log_entry(f"⚡ {character.name} regen cost: STA {old_sta} -> {character.sta} (-2)", "debug")

    # Recalculate total health
    character.calculate_health_from_body_parts()

    # Update automatic debuffs since status effects may have been weakened
    update_automatic_debuffs(character)

    print(f"DEBUG: Regenerated {character.name}'s {part.name}: {old_pvt} -> {part.p_pvt} (+{actual_healing})")
    print(f"DEBUG: {character.name} resources after regen - RIG: {character.rig}, STA: {character.sta}")

    # Play regeneration sound effect
    if actual_healing > 0:
        try:
            import random
            import Global_SFX
            regen_sounds = [
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\cute-level-up-3-189853.mp3",
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\cute-level-up-3-189853.mp3",
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\cute-level-up-3-189853.mp3"
            ]
            sound_file = random.choice(regen_sounds)
            
            # Use battle menu instance sound system if available
            if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'play_sound_effect'):
                global_sfx_volume = Global_SFX.get_global_sfx_volume()
                final_volume = 0.6 * global_sfx_volume  # 0.6 base volume for regeneration
                globals()['battle_menu_instance'].play_sound_effect(sound_file, volume=final_volume, loops=0)
            else:
                # Fallback to direct pygame with Global_SFX
                sound = Global_SFX.load_sound_with_global_volume(sound_file, 0.6)
                if sound:
                    sound.play()
            print(f"[SOUND] Played enemy regeneration sound: {sound_file}")
        except Exception as e:
            print(f"[SOUND] Error playing enemy regeneration sound: {e}")

    # Log regeneration in event log (purple, type 'effect')
    if actual_healing > 0:
        message = f"{character.name} regenerated {part.name}: +{actual_healing}"
        # Try battle_menu_instance first, then fallback to ui global
        if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
            globals()['battle_menu_instance'].add_log_entry(message, log_type="effect", color=(255, 150, 255))
        elif hasattr(globals().get('ui', None), 'add_log_entry'):
            globals()['ui'].add_log_entry(message, log_type="effect", color=(255, 150, 255))
        else:
            # If no UI available, just print to console instead of using undefined event_log
            print(f"[REGENERATION LOG]: {message}")

    return True
#---------------------------------------------------------------

#CLASSI E INIZIALIZZAZIONE

# CLASSI

class Character:
    def __init__(self, name, max_pvt, pvt, max_rig, rig, max_res, res, max_sta, sta,
                  max_for, forz, max_des, des, max_spe, spe, max_vel, vel,
                  body_parts, image_path, moves=None, ability=None):
        self.name = name
        # Note: max_pvt and pvt will be recalculated based on body parts
        self.max_pvt = max_pvt  # Will be overwritten by calculate_health_from_body_parts()
        self.max_rig = max_rig
        self.max_res = max_res
        self.max_sta = max_sta
        self.max_for = max_for
        self.max_des = max_des
        self.max_spe = max_spe
        self.max_vel = max_vel
        self.pvt = pvt  # Will be overwritten by calculate_health_from_body_parts()
        self.rig = rig
        self.res = res
        self.sta = sta
        self.forz = forz
        self.des = des
        self.spe = spe
        self.vel = vel
        
        # Initialize the new Buffs system
        self.buffs = Buffs()
        # Initialize active buff moves system (requirement-based)
        self.active_buffs = ActiveBuffs()
        
        self.body_parts = body_parts  # List of body parts
        self.image_path = image_path  # Path to character image
        self.moves = moves if moves is not None else []  # List of moves
        self.ability = ability if ability is not None else []
        
        # Calculate health based on body parts after initialization
        self.calculate_health_from_body_parts()
    
    def calculate_health_from_body_parts(self):
        """
        Calculate max_pvt and pvt based on the sum of all body parts' health.
        max_pvt = sum of all body parts' max_p_pvt
        pvt = sum of all body parts' p_pvt
        """
        if self.body_parts:
            self.max_pvt = sum(part.max_p_pvt for part in self.body_parts)
            self.pvt = sum(part.p_pvt for part in self.body_parts)
            print(f"{self.name}: Health recalculated - max_pvt: {self.max_pvt}, current pvt: {self.pvt}")
        else:
            print(f"Warning: {self.name} has no body parts for health calculation")

class BodyPart:
    def __init__(self, name, max_p_pvt, p_pvt, p_eff, p_difese, p_elusione):
        self.name = name
        self.max_p_pvt = max_p_pvt
        self.p_pvt = p_pvt
        self.p_eff = p_eff
        self.p_difese = p_difese
        self.p_elusione = p_elusione

class Effetti:
    def __init__(self, burn=None, bleed=None, poison=None, stun=None, confusion=None, acid=None, frost=None, heal=None, regeneration=None, sleep=None, weakness=None, amputate=None, mess_up=None, paralysis=None, fry_neurons=None, fine_dust=None, custom_poison=None):
        # per ogni effetto di stato il primo elemento della lista è il nome dell'effetto, il secondo è il livello, il terzo la durata e il quarto l'immunità (0 non immune o 1 immune)
        #di base li setta tutti a zero, se vuoi settarne uno devi farlo separatamente.
        self.burn = burn if burn is not None else ["burn", 0, 0, 0]
        self.bleed = bleed if bleed is not None else ["bleed", 0, 0, 0]
        self.poison = poison if poison is not None else ["poison", 0, 0, 0]
        self.stun = stun if stun is not None else ["stun", 0, 0, 0]
        self.confusion = confusion if confusion is not None else ["confusion", 0, 0, 0]
        self.acid = acid if acid is not None else ["acid", 0, 0, 0]
        self.frost = frost if frost is not None else ["frost", 0, 0, 0]
        self.heal = heal if heal is not None else ["heal", 0, 0, 0]
        self.regeneration = regeneration if regeneration is not None else ["regeneration", 0, 0, 0]
        self.sleep = sleep if sleep is not None else ["sleep", 0, 0, 0]
        self.weakness = weakness if weakness is not None else ["weakness", 0, 0, 0]
        # New status effects
        self.amputate = amputate if amputate is not None else ["amputate", 0, 0, 0]
        self.mess_up = mess_up if mess_up is not None else ["mess_up", 0, 0, 0]
        self.paralysis = paralysis if paralysis is not None else ["paralysis", 0, 0, 0]
        self.fry_neurons = fry_neurons if fry_neurons is not None else ["fry_neurons", 0, 0, 0]
        self.fine_dust = fine_dust if fine_dust is not None else ["fine_dust", 0, 0, 0]
        self.custom_poison = custom_poison if custom_poison is not None else ["custom_poison", 0, 0, 0]

class ActiveBuffs:
    """Tracks active buff moves with their requirements (new system)"""
    def __init__(self):
        # Dictionary to track active buff moves: {move_name: {'requirements': [...], 'effects': [...]}}
        self.active_buff_moves = {}
    
    def activate_buff_move(self, move_name, requirements, effects):
        """Activate a buff move with its requirements and effects"""
        self.active_buff_moves[move_name] = {
            'requirements': requirements,
            'effects': effects,
            'active': True
        }
    
    def deactivate_buff_move(self, move_name):
        """Deactivate a specific buff move"""
        if move_name in self.active_buff_moves:
            self.active_buff_moves[move_name]['active'] = False
    
    def get_active_buff_moves(self):
        """Get all active buff moves"""
        return {name: data for name, data in self.active_buff_moves.items() if data.get('active', False)}
    
    def check_requirements_conflicts(self, new_requirements):
        """Check if new requirements conflict with existing active buffs"""
        conflicting_buffs = []
        for move_name, buff_data in self.get_active_buff_moves().items():
            existing_reqs = buff_data['requirements']
            # Check if any requirements overlap
            if any(req in existing_reqs for req in new_requirements):
                conflicting_buffs.append(move_name)
        return conflicting_buffs
    
    def deactivate_conflicting_buffs(self, new_requirements):
        """Deactivate buffs that conflict with new requirements"""
        conflicting = self.check_requirements_conflicts(new_requirements)
        for buff_name in conflicting:
            self.deactivate_buff_move(buff_name)
        return conflicting

class Buffs:
    def __init__(self, buf_rig=None, buf_res=None, buf_sta=None, buf_forz=None, buf_des=None, buf_spe=None, buf_vel=None, buf_dodge=None, buf_shield=None):
        # per ogni buff/debuff il primo elemento della lista è il nome del buff, il secondo è il livello, il terzo la durata
        # di base li setta tutti a zero, se vuoi settarne uno devi farlo separatamente.
        self.buf_rig = buf_rig if buf_rig is not None else ["buf_rig", 0, 0]
        self.buf_res = buf_res if buf_res is not None else ["buf_res", 0, 0]
        self.buf_sta = buf_sta if buf_sta is not None else ["buf_sta", 0, 0]
        self.buf_forz = buf_forz if buf_forz is not None else ["buf_forz", 0, 0]
        self.buf_des = buf_des if buf_des is not None else ["buf_des", 0, 0]
        self.buf_spe = buf_spe if buf_spe is not None else ["buf_spe", 0, 0]
        self.buf_vel = buf_vel if buf_vel is not None else ["buf_vel", 0, 0]
        # New defensive buffs
        self.buf_dodge = buf_dodge if buf_dodge is not None else ["buf_dodge", 0, 0]  # Requires 2 legs
        self.buf_shield = buf_shield if buf_shield is not None else ["buf_shield", 0, 0]  # Requires 1 arm

class Difese:
    def __init__(self, p_def_cut =1 , p_def_pierce =1 , p_def_blunt=1, p_def_fire=1, p_def_ice=1, p_def_electricity=1):
        self.p_def_cut = p_def_cut
        self.p_def_pierce = p_def_pierce
        self.p_def_blunt = p_def_blunt
        self.p_def_fire = p_def_fire
        self.p_def_ice = p_def_ice
        self.p_def_electricity = p_def_electricity

class Mossa:
    def __init__(self, name, tipo, sca_for, sca_des, sca_spe, character, eff_appl=None, reqs=None, elem=None, accuracy=100):
        self.name = name
        self.tipo = tipo  # ATK, BUF, REA
        self.sca_for = sca_for  # Strength scaling
        self.sca_des = sca_des  # Dexterity scaling  
        self.sca_spe = sca_spe  # Special scaling
        self.eff_appl = eff_appl if eff_appl is not None else []  # Up to 4 effects
        self.reqs = reqs if reqs is not None else []  # Up to 4 requirements
        self.elem = elem if elem is not None else []  # Up to 2 elements
        self.accuracy = accuracy  # Accuracy value
        
        # Calculate damage and stamina cost automatically
        self.danno = calculate_move_damage(character, sca_for, sca_des, sca_spe)
        self.stamina_cost = calculate_move_stamina_cost(sca_for, sca_des, sca_spe, eff_appl, reqs, accuracy)

class Ability:
    def __init__(self, name, punti, description, descriptionLong):
        self.name = name
        self.punti = punti  #COst in points
        self.description = description  # Short description
        self.descriptionLong = descriptionLong  # Long description for detailed view
        
#------------------------------------------------------------------------------------------------------------------

#INIT STUFF

# Example characters with custom body parts and image

player_image_path = Path(__file__).parent /"enemies_gifs" / "Selkio_NPC_2_gif.gif"

# Example enemy with custom body parts and animated gif

enemy_image_path = Path(__file__).parent / "Enemies_GIFs" / "Maedo_NPC_1_Gif.gif"

# Debug: Check if image files exist at initialization
print(f"Player image path at initialization: {player_image_path}")
print(f"Player image file exists: {player_image_path.exists()}")
if player_image_path.exists():
    print(f"Player image absolute path: {player_image_path.absolute()}")
else:
    print(f"Player image file not found at: {player_image_path.absolute()}")

# Debug: Check if enemy image file exists at initialization
enemy_image_check = Path(enemy_image_path)
print(f"Enemy image path at initialization: {enemy_image_path}")
print(f"Enemy image file exists: {enemy_image_check.exists()}")
if enemy_image_check.exists():
    print(f"Enemy image absolute path: {enemy_image_check.absolute()}")
else:
    print(f"Enemy image file not found at: {enemy_image_check.absolute()}")
    print("Available files in current directory:")
    current_dir = Path(".")
    for item in current_dir.iterdir():
        if item.is_file():
            print(f"  File: {item}")
        elif item.is_dir():
            print(f"  Directory: {item}/")

player_body_parts = [
    BodyPart("HEAD", 30, 30, Effetti(), Difese(), 0.5),  # 50% evasion for head
    BodyPart("RIGHT ARM", 15, 15, Effetti(), Difese(), 1),
    BodyPart("LEFT ARM", 15, 15, Effetti(), Difese(), 1),
    BodyPart("BODY", 100, 100, Effetti(), Difese(), 2),
    BodyPart("RIGHT LEG", 20, 20, Effetti(),Difese(), 1),
    BodyPart("LEFT LEG", 20, 20, Effetti(),Difese(), 1),
]

player = Character(
    "JONNY BUONO",
    200, 200, 20, 20, 50, 50, 12, 12, 15, 15, 14, 14, 13, 13, 11, 11,
    player_body_parts,
    str(player_image_path)  # Convert Path to string for compatibility
)

enemy_body_parts = [
    BodyPart("HEAD", 30, 30, Effetti(), Difese(), 1),
    BodyPart("BODY", 100, 100, Effetti(), Difese(), 1),
    BodyPart("RIGHT ARM", 15, 15, Effetti(), Difese(), 1),
    BodyPart("LEFT ARM", 15, 15, Effetti(), Difese(), 1),
    BodyPart("TENTACLE 1", 20, 20, Effetti(), Difese(), 1),
    BodyPart("TENTACLE 2", 20, 20, Effetti(), Difese(), 1),
    BodyPart("RIGHT LEG", 20, 20, Effetti(),Difese(), 1),
    BodyPart("LEFT LEG", 20, 20, Effetti(),Difese(), 1),
]

enemy = Character(
    "MAEDO WARRIOR",
    200, 200, 20, 20, 50, 50, 14, 14, 10, 10, 13, 13, 16, 16, 11, 11,
    enemy_body_parts,
    str(enemy_image_path)  # Convert Path to string for compatibility
)

#-------------------------------------------------------------------------------------------------------------------

# Essential utility functions that are used early in the code
def apply_status_effect(character, part_index, effect_name, level=1, duration=1, immunity=0, caster=None):
    """
    Apply a status effect to a specific body part of a character.
    If the effect already exists, it stacks: level = sum of levels, duration = previous duration + 1.
    Special handling for effects with forced targeting:
    - Sleep, fry_neurons: always target the head
    - Fine_dust: always targets the body
    - Amputate: can only be applied to destroyed body parts
    - Custom_poison: stores caster's special stat for damage calculation
    
    Args:
        character: Target character
        part_index: Index of body part to target
        effect_name: Name of the effect
        level: Level of the effect
        duration: Duration of the effect
        immunity: Immunity level
        caster: The character who cast the effect (for custom_poison damage calculation)
    
    Returns:
        bool: True if effect was successfully applied, False otherwise
    """
    """
    Apply a status effect to a specific body part of a character.
    If the effect already exists, it stacks: level = sum of levels, duration = previous duration + 1.
    Special handling for effects with forced targeting:
    - Sleep, fry_neurons: always target the head
    - Fine_dust: always targets the body
    - Amputate: can only be applied to destroyed body parts
    """
    from Status_Effects_Config import should_always_target_head, should_effect_reduce_over_time, get_effect_config
    
    # Get effect configuration for special targeting
    effect_config = get_effect_config(effect_name)
    
    # Special handling for head-targeting effects (sleep, fry_neurons)
    if should_always_target_head(effect_name):
        # Find the head part
        head_part_index = -1
        for i, part in enumerate(character.body_parts):
            if "HEAD" in part.name.upper():
                head_part_index = i
                break
        
        if head_part_index == -1:
            print(f"No head part found for {getattr(character, 'name', 'Unknown')} - cannot apply {effect_name}")
            return
        
        # Override part_index to target the head
        part_index = head_part_index
        print(f"Head-targeting effect {effect_name} automatically targeting head for {getattr(character, 'name', 'Unknown')}")
    
    # Special handling for body-targeting effects (fine_dust)
    elif effect_config and effect_config.get('always_target_body', False):
        # Find the body part
        body_part_index = -1
        for i, part in enumerate(character.body_parts):
            if "BODY" in part.name.upper():
                body_part_index = i
                break
        
        if body_part_index == -1:
            print(f"No body part found for {getattr(character, 'name', 'Unknown')} - cannot apply {effect_name}")
            return
        
        # Override part_index to target the body
        part_index = body_part_index
        print(f"Body-targeting effect {effect_name} automatically targeting body for {getattr(character, 'name', 'Unknown')}")
    
    # Special handling for amputate effect - can only be applied to destroyed parts
    elif effect_name.lower() == 'amputate':
        if not (0 <= part_index < len(character.body_parts)):
            print(f"Invalid body part index {part_index} for character {getattr(character, 'name', 'Unknown')}")
            return False
        target_part = character.body_parts[part_index]
        if target_part.p_pvt > 0:
            print(f"Amputate can only be applied to destroyed body parts. {target_part.name} has {target_part.p_pvt} HP")
            return False
        print(f"Applying amputate to destroyed part {target_part.name}")
    
    if not (0 <= part_index < len(character.body_parts)):
        print(f"Invalid body part index {part_index} for character {getattr(character, 'name', 'Unknown')}")
        return False
    part = character.body_parts[part_index]
    effetti = part.p_eff
    if not hasattr(effetti, effect_name):
        print(f"Effect '{effect_name}' not found on {part.name}")
        return False
    
    # Special duration handling for effects that don't reduce over time (like sleep)
    if not should_effect_reduce_over_time(effect_name):
        # For effects like sleep that don't reduce over time, use a special infinite duration marker
        duration = 999  # Use 999 as infinite duration marker
    
    # Get the current effect data
    current_effect = getattr(effetti, effect_name)
    
    # Check if the effect is already active (level > 0)
    if current_effect[1] > 0:  # level is at index 1
        # Special handling for amputate - cannot stack, max level 1
        if effect_name.lower() == 'amputate':
            print(f"Amputate is already active on {getattr(character, 'name', 'Unknown')} - {part.name}, cannot stack beyond level 1")
            return False
        
        # Stack the effect: sum levels, for special effects maintain infinite duration
        new_level = current_effect[1] + level
        if not should_effect_reduce_over_time(effect_name):
            new_duration = 999  # Maintain infinite duration for sleep
        else:
            new_duration = current_effect[2] + 1  # Normal duration increment
        existing_immunity = current_effect[3]  # immunity is at index 3
        
        setattr(effetti, effect_name, [effect_name, new_level, new_duration, existing_immunity])
        print(f"Stacked {effect_name} on {getattr(character, 'name', 'Unknown')} - {part.name}: Level {current_effect[1]} + {level} = {new_level}, Duration {new_duration}")
    else:
        # Apply new effect since none exists or it's inactive
        setattr(effetti, effect_name, [effect_name, level, duration, immunity])
        print(f"Applied {effect_name} to {getattr(character, 'name', 'Unknown')} - {part.name}: {[effect_name, level, duration, immunity]}")
    
    # Special handling for custom_poison: store caster's special stat for damage calculation
    if effect_name.lower() == 'custom_poison' and caster is not None:
        if hasattr(caster, 'spe'):
            # Store damage per level = caster's special / 2 (rounded down)
            damage_per_level = max(1, caster.spe // 2)  # Minimum 1 damage
            setattr(part, 'custom_poison_damage_per_level', damage_per_level)
            print(f"  Stored custom_poison damage: {damage_per_level} per level (from caster {getattr(caster, 'name', 'Unknown')}'s special {caster.spe})")
        else:
            print(f"  Warning: Caster has no 'spe' attribute for custom_poison damage calculation")
    
    return True  # Effect successfully applied

def process_effect_on_hit_buffs(attacker, defender, move, is_ranged=False):
    """
    Process Effect-on-Hit buffs for both attacker and defender when a move makes contact.
    
    Args:
        attacker: The character making the attack
        defender: The character receiving the attack
        move: The move being used
        is_ranged: Whether the move is ranged (Effect-on-Hit buffs don't trigger for ranged moves)
    """
    
    if is_ranged:
        return  # Effect-on-Hit buffs don't trigger on ranged attacks
    
    from Status_Effects_Config import get_effect_config
    
    # Check for Effect-on-Hit buffs on both attacker and defender
    for character, contact_type in [(attacker, 'hit'), (defender, 'hit_by')]:
        char_name = getattr(character, 'name', 'Unknown')
        
        # Track which Effect-on-Hit buffs have already been triggered for this character
        triggered_buffs = set()
        
        # Check all body parts for active Effect-on-Hit buffs
        for part in character.body_parts:
            if not hasattr(part, 'p_eff'):
                continue
                
            effetti = part.p_eff
            
            # Check for each possible Effect-on-Hit buff
            effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
            
            for buff_name in effect_on_hit_buffs:
                # Skip if this buff has already been triggered for this character
                if buff_name in triggered_buffs:
                    continue
                    
                if hasattr(effetti, buff_name):
                    buff_data = getattr(effetti, buff_name)
                    
                    # Check if buff is active (level > 0)
                    if buff_data[1] > 0:
                        # Mark this buff as triggered so it doesn't trigger again
                        triggered_buffs.add(buff_name)
                        buff_config = get_effect_config(buff_name)
                        
                        if buff_config:
                            buff_contact_type = buff_config.get('contact_type', 'both')
                            
                            # Check if this buff triggers for this contact type
                            if buff_contact_type == 'both' or buff_contact_type == contact_type:
                                # Trigger the effect on the opposite character
                                target = defender if character == attacker else attacker
                                
                                trigger_effect = buff_config.get('trigger_effect')
                                trigger_level = buff_config.get('trigger_level', 1)
                                trigger_body_part = buff_config.get('trigger_body_part', 'random')
                                
                                if trigger_effect:
                                    # Determine target body part
                                    if trigger_body_part == 'random':
                                        import random
                                        target_part_index = random.randint(0, len(target.body_parts) - 1)
                                    elif trigger_body_part == 'head' and len(target.body_parts) > 0:
                                        target_part_index = 0  # Assume head is first
                                    elif trigger_body_part == 'body' and len(target.body_parts) > 1:
                                        target_part_index = 1  # Assume body is second
                                    else:
                                        target_part_index = 0  # Default to first part
                                    
                                    # Apply the trigger effect
                                    target_part = target.body_parts[target_part_index]
                                    target_name = getattr(target, 'name', 'Unknown')
                                    
                                    # Apply the effect using the existing system
                                    apply_status_effect(target, target_part_index, trigger_effect, trigger_level, 1)  # 1 turn duration (as requested)
                                    
                                    print(f"🔥 {char_name}'s {buff_name} triggered: {trigger_effect} level {trigger_level} applied to {target_name}'s {target_part.name}")
                                    
                                    # Add to battle log
                                    if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                                        globals()['battle_menu_instance'].add_log_entry(
                                            f"{char_name}'s {buff_name} triggers {trigger_effect} on {target_name}'s {target_part.name}",
                                            "effect", (255, 165, 0)
                                        )

def apply_move_effects(move, target_character, target_part_index=None):
    """
    Apply all status effects from a move to the target character.
    
    Args:
        move: The move object containing effects in eff_appl
        target_character: The character to apply effects to
        target_part_index: Index of the specific body part to target (if None, applies to random parts)
    
    Returns:
        list: List of tuples containing (effect_name, level, duration) for effects that were applied
    """
    
    applied_effects = []  # Track effects that were applied
    
    print(f"[EFFECT DEBUG] apply_move_effects called: move={move.name}, target={getattr(target_character, 'name', 'Unknown')}")
    print(f"[EFFECT DEBUG] move.eff_appl = {getattr(move, 'eff_appl', 'NOT FOUND')}")
    
    if not hasattr(move, 'eff_appl') or not move.eff_appl:
        print(f"[EFFECT DEBUG] No effects to apply for move {move.name}")
        return applied_effects
    
    # Get all available effect names from the Effetti class and buff/debuff effects
    available_effects = ['burn', 'bleed', 'poison', 'stun', 'confusion', 'acid', 'frost', 'heal', 'regeneration', 'sleep', 'weakness', 'amputate', 'mess_up', 'paralysis', 'fry_neurons', 'fine_dust', 'custom_poison']
    available_buffs = ['buf_rig', 'buf_res', 'buf_sta', 'buf_forz', 'buf_des', 'buf_spe', 'buf_vel', 'buf_dodge', 'buf_shield']
    
    # Effect-on-Hit buffs (special handling needed)
    effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
    
    char_name = getattr(target_character, 'name', 'Unknown')
    print(f"\nApplying effects from move '{move.name}' to {char_name}:")
    
    for effect_data in move.eff_appl:
        # Handle both old format (single string) and new format (list with details)
        if isinstance(effect_data, str):
            # Old format: just effect name
            effect_name = effect_data.lower()
            level, duration, immunity = 1, 1, 0
        elif isinstance(effect_data, list) and len(effect_data) >= 4:
            # New format: [name, level, duration, immunity]
            effect_name = effect_data[0].lower()
            level = effect_data[1]
            duration = effect_data[2]
            immunity = effect_data[3]
        else:
            print(f"  Invalid effect format: {effect_data}")
            continue
        
        # Check if effect name is valid (status effect, buff/debuff, or Effect-on-Hit buff)
        # Skip property effects as they are handled during damage calculation, not as status effects
        property_effects = ['rhythm', 'clean_cut', 'lifesteal', 'ranged']  # Known property effects
        if effect_name in property_effects:
            print(f"  Skipping property effect '{effect_name}' (handled during damage calculation)")
            continue
            
        if effect_name not in available_effects and effect_name not in available_buffs and effect_name not in effect_on_hit_buffs:
            print(f"  Unknown effect '{effect_name}' - skipping")
            continue
        
        # Apply effect based on type (status effect or buff/debuff)
        if effect_name in available_effects:
            # Handle status effects (applied to body parts)
            if target_character.body_parts:
                if target_part_index is not None and 0 <= target_part_index < len(target_character.body_parts):
                    # Apply to specific targeted body part
                    part_index = target_part_index
                    target_part = target_character.body_parts[part_index]
                    
                    # SPECIAL CASE: Paralysis on HEAD or BODY should target a random limb instead
                    if effect_name == 'paralysis' and target_part.name.upper() in ['HEAD', 'BODY']:
                        # Find all non-HEAD/BODY parts (limbs)
                        limb_indices = []
                        for i, part in enumerate(target_character.body_parts):
                            if part.name.upper() not in ['HEAD', 'BODY']:
                                limb_indices.append(i)
                        
                        if limb_indices:
                            # Randomly select a limb to paralyze instead
                            original_part_name = target_part.name
                            part_index = random.choice(limb_indices)
                            target_part = target_character.body_parts[part_index]
                            print(f"  PARALYSIS REDIRECT: {effect_name} was targeted at {original_part_name}, redirecting to {target_part.name}")
                        else:
                            print(f"  PARALYSIS REDIRECT: No limbs available to paralyze, skipping paralysis effect")
                            continue
                    
                    print(f"  Applying {effect_name} to targeted body part: {target_part.name}")
                else:
                    # Fall back to random body part if target_part_index is invalid or None
                    if effect_name == 'paralysis':
                        # For paralysis, prefer limbs over HEAD/BODY
                        limb_indices = []
                        for i, part in enumerate(target_character.body_parts):
                            if part.name.upper() not in ['HEAD', 'BODY']:
                                limb_indices.append(i)
                        
                        if limb_indices:
                            part_index = random.choice(limb_indices)
                            target_part = target_character.body_parts[part_index]
                            print(f"  Applying {effect_name} to random limb: {target_part.name}")
                        else:
                            # No limbs available, fall back to any part
                            part_index = random.randint(0, len(target_character.body_parts) - 1)
                            target_part = target_character.body_parts[part_index]
                            print(f"  Applying {effect_name} to random body part: {target_part.name}")
                    else:
                        # Normal random selection for other effects
                        part_index = random.randint(0, len(target_character.body_parts) - 1)
                        target_part = target_character.body_parts[part_index]
                        print(f"  Applying {effect_name} to random body part: {target_part.name}")
                
                # Apply the status effect to the selected body part
                effect_applied = apply_status_effect(target_character, part_index, effect_name, level, duration, immunity)
                
                # Track the applied effect only if it was successfully applied
                if effect_applied:
                    applied_effects.append((effect_name.capitalize(), level, duration))
                    print(f"  → {effect_name.upper()} applied to {target_part.name} (Level: {level}, Duration: {duration})")
                else:
                    print(f"  → {effect_name.upper()} failed to apply to {target_part.name} (conditions not met)")
            else:
                print(f"  → No body parts available on {char_name} to apply {effect_name}")
        
        elif effect_name in effect_on_hit_buffs:
            # Handle Effect-on-Hit buffs (applied as persistent effects on body parts)
            print(f"🔥 PROCESSING EFFECT-ON-HIT BUFF: {effect_name} (level {level}) to {char_name}")
            
            # Effect-on-Hit buffs are applied to all body parts with permanent duration (999)
            if target_character.body_parts:
                for part in target_character.body_parts:
                    if hasattr(part, 'p_eff'):
                        # Apply the Effect-on-Hit buff with permanent duration and no immunity
                        setattr(part.p_eff, effect_name, [effect_name, level, 999, False])
                        print(f"  → {effect_name.upper()} applied to {part.name} (Level: {level}, Duration: 999)")
                
                # Track the applied effect
                applied_effects.append((f"{effect_name.upper()}", level, 999))
                print(f"  → Effect-on-Hit buff {effect_name.upper()} activated on {char_name}")
            else:
                print(f"  → No body parts available on {char_name} to apply Effect-on-Hit buff {effect_name}")
        
        elif effect_name in available_buffs:
            # Handle buff/debuff effects (applied to character stats)
            # For DODGE/SHIELD, keep the full buf_ name; for others, remove buf_ prefix
            if effect_name in ['buf_dodge', 'buf_shield']:
                stat_name = effect_name  # Keep full name for special buffs
            else:
                stat_name = effect_name.replace('buf_', '')  # Remove prefix for regular buffs
            print(f"🔥 PROCESSING BUFF EFFECT: {effect_name} (level {level}) to {char_name}'s {stat_name.upper()}")
            
            # Play custom sound for this buff effect based on STATUS_EFFECTS_CONFIG
            if effect_name in STATUS_EFFECTS_CONFIG and 'played_sound' in STATUS_EFFECTS_CONFIG[effect_name]:
                sound_file = STATUS_EFFECTS_CONFIG[effect_name]['played_sound']
                print(f"🎵 Playing custom sound for {effect_name}: {sound_file}")
                play_sound_effect(sound_file, volume=0.7)  # Fixed: was volume=3, now 0.7
            
            # Apply the buff/debuff using the existing function
            apply_buff_debuff(target_character, stat_name, level, duration)
            
            # Track the applied effect
            buff_type = "BUFF" if level > 0 else "DEBUFF"
            applied_effects.append((f"{stat_name.upper()} {buff_type}", level, duration))
            print(f"  → {stat_name.upper()} {buff_type} applied to {char_name} (Level: {level}, Duration: {duration})")
        
        else:
            print(f"  → Unknown effect type: {effect_name}")
    
    # Update automatic debuffs for the target character after applying status effects
    update_automatic_debuffs(target_character)
    
    return applied_effects

def decrease_status_effect_durations(character):
    """
    Check all status effects for all body parts of a character and decrease their duration by 1.
    If duration reaches 0, the effect is deactivated (level set to 0).
    
    Args:
        character: The character object to process
    
    Returns:
        list: List of messages about effects that expired or were reduced
    """
    messages = []
    char_name = getattr(character, 'name', 'Unknown')
    
    # List of all available status effects
    available_effects = ['burn', 'bleed', 'poison', 'stun', 'confusion', 'cancer', 'inhibition', 'freeze', 'regen', 'sleep', 'acid', 'amputate', 'mess_up', 'paralysis', 'fry_neurons', 'fine_dust', 'custom_poison']
    
    if not hasattr(character, 'body_parts') or not character.body_parts:
        print(f"No body parts found for {char_name}")
        return messages
    
    print(f"\nDecreasing status effect durations for {char_name}:")
    
    for part_index, part in enumerate(character.body_parts):
        if not hasattr(part, 'p_eff'):
            continue
            
        effetti = part.p_eff
        part_had_active_effects = False
        
        for effect_name in available_effects:
            if hasattr(effetti, effect_name):
                effect_data = getattr(effetti, effect_name)
                
                # Check if effect is currently active (level > 0 and duration > 0)
                if effect_data[1] > 0 and effect_data[2] > 0:  # level > 0 and duration > 0
                    part_had_active_effects = True
                    old_duration = effect_data[2]
                    new_duration = old_duration - 1
                    
                    # Update the duration
                    effect_data[2] = new_duration
                    
                    if new_duration <= 0:
                        # Effect expired, deactivate it (set level to 0)
                        effect_data[1] = 0
                        message = f"  {part.name}: {effect_name.upper()} expired (was duration {old_duration})"
                        print(message)
                        messages.append(f"{char_name} - {message}")
                    else:
                        # Effect duration reduced but still active
                        message = f"  {part.name}: {effect_name.upper()} duration {old_duration} -> {new_duration}"
                        print(message)
                        messages.append(f"{char_name} - {message}")
        
        if not part_had_active_effects:
            print(f"  {part.name}: No active status effects")
    
    if not messages:
        print(f"  {char_name} has no active status effects to reduce")
    
    return messages

def process_turn_start_effects(character):
    """
    Process turn START effects for a specific character only.
    Called at the beginning of each character's turn AFTER stamina restoration.
    
    Effects processed:
    - STUN: Reduces stamina based on total stun levels across all body parts
    - SLEEP: Similar to stun (if implemented)
    - FREEZE: Prevents certain actions (if implemented)
    
    After processing, durations are decreased by 1 for this character only.
    """
    char_name = getattr(character, 'name', 'Unknown')
    global turn_player, turn_enemy
    total_turns = turn_player + turn_enemy
    
    if not hasattr(character, 'body_parts') or not character.body_parts:
        print(f"No body parts found for {char_name}")
        return
    
    # Process STUN effects (sum all stun levels across body parts)
    total_stun = 0
    stun_parts = []
    
    for part in character.body_parts:
        if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'stun'):
            stun_data = getattr(part.p_eff, 'stun')
            # Check if stun is active (level > 0 and duration > 0)
            if stun_data[1] > 0 and stun_data[2] > 0:
                total_stun += stun_data[1]
                stun_parts.append(f"{part.name}(L{stun_data[1]})")
                print(f"  STUN: {part.name} Level {stun_data[1]}, Duration {stun_data[2]}")
    
    # Apply stun stamina reduction if any stun present
    if total_stun > 0:
        old_sta = character.sta
        character.sta = max(0, character.sta - total_stun)
        stun_message = f"{char_name} loses {total_stun} stamina due to STUN"
        print(stun_message)
        
        # Add to battle log
        if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
            globals()['battle_menu_instance'].add_log_entry(stun_message, "effect", (255, 150, 255))
    else:
        print(f"  No active stun effects for {char_name}")
    
    # Process SLEEP effects (check threshold and apply stamina loss with same timing as stun)
    from Status_Effects_Config import check_sleep_threshold, process_sleep_wake_up
    
    # Find head part for sleep processing
    head_part = None
    for part in character.body_parts:
        if "HEAD" in part.name.upper():
            head_part = part
            break
    
    if head_part and hasattr(head_part, 'p_eff') and hasattr(head_part.p_eff, 'sleep'):
        sleep_data = getattr(head_part.p_eff, 'sleep')
        # Check if sleep is active (level > 0 and duration > 0)
        if sleep_data[1] > 0 and sleep_data[2] > 0:
            sleep_level = sleep_data[1]
            print(f"  SLEEP: {head_part.name} Level {sleep_level}, Duration {sleep_data[2]}")
            
            # Check sleep threshold (level >= max_hp / 10)
            threshold_met = check_sleep_threshold(character)
            
            if threshold_met:
                # Check if character was already asleep (stamina = 0) to determine message
                was_already_asleep = (character.sta == 0)
                
                # Apply stamina loss - sleep drains ALL stamina to 0
                old_sta = character.sta
                stamina_lost = character.sta  # Track how much stamina was lost
                character.sta = 0  # Sleep effect drains ALL stamina
                
                # Show appropriate message based on sleep state
                if was_already_asleep:
                    sleep_message = f"{char_name} is still asleep..."
                else:
                    sleep_message = f"{char_name} falls asleep..."
                    
                print(sleep_message)
                
                # Add to battle log
                if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                    globals()['battle_menu_instance'].add_log_entry(sleep_message, "effect", (150, 100, 255))
                
                # Process wake-up chance (75% chance to wake up)
                woke_up = process_sleep_wake_up(character)
                if woke_up:
                    wake_message = f"{char_name} woke up!"
                    print(f"  {wake_message}")
                    
                    # Add to battle log
                    if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                        globals()['battle_menu_instance'].add_log_entry(wake_message, "success", (100, 255, 100))
            else:
                # Calculate threshold for display (same logic as in check_sleep_threshold)
                body_part = None
                for part in character.body_parts:
                    if "BODY" in part.name.upper():
                        body_part = part
                        break
                
                if body_part:
                    threshold = body_part.max_p_pvt // 10
                    print(f"  SLEEP: {head_part.name} Level {sleep_level} below threshold (need >= {threshold})")
                else:
                    print(f"  SLEEP: {head_part.name} Level {sleep_level} below threshold (body part not found)")
    else:
        print(f"  No active sleep effects for {char_name}")
    
    # Process FRY NEURONS effects (disable random skills at turn start)
    if head_part and hasattr(head_part, 'p_eff') and hasattr(head_part.p_eff, 'fry_neurons'):
        fry_data = getattr(head_part.p_eff, 'fry_neurons')
        # Check if fry_neurons is active (level > 0 and duration > 0)
        if fry_data[1] > 0 and fry_data[2] > 0:
            fry_level = fry_data[1]
            print(f"  FRY NEURONS: {head_part.name} Level {fry_level}, Duration {fry_data[2]}")
            
            # Disable random skills equal to the level
            import random
            skills_disabled = 0
            
            # Check for PLAYER memory skills system
            if hasattr(character, 'memory_skills') and character.memory_skills:
                active_skills = [skill_id for skill_id, data in character.memory_skills.items() 
                               if data.get('active', False)]
                
                if active_skills and fry_level > 0:
                    # Disable up to fry_level skills randomly
                    skills_to_disable = min(fry_level, len(active_skills))
                    skills_to_disable_list = random.sample(active_skills, skills_to_disable)
                    
                    for skill_id in skills_to_disable_list:
                        character.memory_skills[skill_id]['active'] = False
                        print(f"    Disabled player skill: {skill_id}")
                        skills_disabled += 1
            
            # Check for ENEMY memory skills system (equipped_memory_skills + memory_skill_state)
            elif hasattr(character, 'equipped_memory_skills') and character.equipped_memory_skills:
                # Initialize memory_skill_state if it doesn't exist
                if not hasattr(character, 'memory_skill_state'):
                    character.memory_skill_state = {}
                    for skill_id in character.equipped_memory_skills:
                        character.memory_skill_state[skill_id] = {'active': True}
                    print(f"    Initialized memory_skill_state for {char_name}")
                
                # Get currently active skills
                active_skills = []
                for skill_id in character.equipped_memory_skills:
                    if skill_id in character.memory_skill_state:
                        skill_state = character.memory_skill_state[skill_id]
                        if skill_state.get('active', True):  # Default to True if not specified
                            active_skills.append(skill_id)
                
                if active_skills and fry_level > 0:
                    # Disable up to fry_level skills randomly
                    skills_to_disable = min(fry_level, len(active_skills))
                    skills_to_disable_list = random.sample(active_skills, skills_to_disable)
                    
                    for skill_id in skills_to_disable_list:
                        if skill_id in character.memory_skill_state:
                            character.memory_skill_state[skill_id]['active'] = False
                        else:
                            character.memory_skill_state[skill_id] = {'active': False}
                        print(f"    Disabled enemy skill: {skill_id}")
                        skills_disabled += 1
            
            # Report results
            if skills_disabled > 0:
                fry_message = f"{char_name}'s neurons are fried! {skills_disabled} skill(s) disabled"
                print(fry_message)
                
                # Add to battle log
                if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                    globals()['battle_menu_instance'].add_log_entry(fry_message, "effect", (255, 200, 100))
            else:
                print(f"    No active skills to disable for {char_name}")
    else:
        print(f"  No active fry_neurons effects for {char_name}")
    
    # Process memory skills for this character's turn start
    try:
        global player, enemy
        if character == player:
            opposing = enemy
        elif character == enemy:
            opposing = player
        else:
            opposing = None
        
        if opposing:
            print(f"  Processing memory skills for {char_name}...")
            process_memory_skills_start_of_turn(character, opposing)
        else:
            print(f"  Could not determine opposing character for memory skills")
    except Exception as e:
        print(f"  Memory skills error for {char_name}: {e}")
    
    # Decrease durations for turn-start effects ONLY for this character
    decrease_turn_start_effect_durations(character)

def process_turn_end_effects(character):
    """
    Process turn END effects for a specific character only.
    Called at the end of each character's turn.
    
    Effects processed:
    - BURN: Deals damage over time
    - BLEED: Deals damage over time  
    - POISON: Deals damage over time
    - REGEN: Heals over time
    - Other damage/healing effects
    
    After processing, durations are decreased by 1 for this character only.
    """
    char_name = getattr(character, 'name', 'Unknown')
    print(f"\n💥 === TURN END EFFECTS FOR {char_name.upper()} === [CALL TRACE]")
    import traceback
    traceback.print_stack(limit=5)  # Show last 5 stack frames
    print(f"💥 === END CALL TRACE ===")
    
    if not hasattr(character, 'body_parts') or not character.body_parts:
        print(f"No body parts found for {char_name}")
        return
    
    # Get list of turn-end effects from configuration
    from Status_Effects_Config import get_effects_by_timing, get_damage_per_turn
    turn_end_effects = get_effects_by_timing('end_turn')
    print(f"  Turn-end effects to check: {turn_end_effects}")

    # Process damage/healing effects for each body part
    for part_index, part in enumerate(character.body_parts):
        if not hasattr(part, 'p_eff'):
            print(f"  {part.name}: No p_eff attribute")
            continue
        
        effetti = part.p_eff
        part_had_effects = False
        
        # Process each turn-end effect
        for effect_name in turn_end_effects:
            if hasattr(effetti, effect_name):
                effect_data = getattr(effetti, effect_name)
                print(f"  {part.name}: {effect_name} = {effect_data}")
                
                # Check if effect is active (level >= 1 and duration >= 1)
                if len(effect_data) >= 3 and effect_data[1] >= 1 and effect_data[2] >= 1:
                    part_had_effects = True
                    effect_level = effect_data[1]
                    
                    # Use configuration to get damage per turn
                    damage = get_damage_per_turn(effect_name, effect_level)
                    
                    # Special handling for custom_poison - damage based on caster's special stat
                    if effect_name.lower() == 'custom_poison':
                        # For custom_poison, we need access to the caster's special stat
                        # Since we don't have direct access to the caster during turn processing,
                        # we'll store the damage value when the effect is applied
                        # For now, use a default calculation if no stored value exists
                        # TODO: Modify apply_status_effect to store caster info for custom_poison
                        if hasattr(part, 'custom_poison_damage_per_level'):
                            damage = getattr(part, 'custom_poison_damage_per_level') * effect_level
                            print(f"    {effect_name} using stored damage calculation: {damage} per level * {effect_level} = {damage}")
                        else:
                            # Fallback: assume 10 damage per level (special stat / 2 = 20 / 2 = 10)
                            damage = 10 * effect_level
                            print(f"    {effect_name} using fallback damage calculation: {damage}")
                    else:
                        print(f"    {effect_name} level {effect_level} should deal {damage} damage")
                    
                    if damage != 0:  # Only process if there's damage/healing
                        old_pvt = part.p_pvt
                        if damage > 0:
                            # Damage effect
                            part.p_pvt = max(0, part.p_pvt - damage)
                            actual_damage = old_pvt - part.p_pvt
                            message = f"{effect_name.upper()} dealt {actual_damage} damage to {char_name}'s {part.name}"
                            
                            # Check for body part destruction and trigger explosive mindset
                            if old_pvt > 0 and part.p_pvt == 0:
                                # For status effects, there's no direct attacker, so we pass None
                                process_memory_skills_bodypart_loss(character, None, part.name)
                        else:
                            # Healing effect
                            part.p_pvt = min(part.max_p_pvt, part.p_pvt - damage)  # damage is negative for healing
                            actual_healing = part.p_pvt - old_pvt
                            message = f"{effect_name.upper()} healed {actual_healing} HP to {char_name}'s {part.name}"
                        
                        print(f"  {message}")
                        
                        # Add to battle log
                        if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                            globals()['battle_menu_instance'].add_log_entry(message, "effect", (255, 150, 255))
                else:
                    print(f"    {effect_name} is inactive: level={effect_data[1] if len(effect_data) > 1 else 'N/A'}, duration={effect_data[2] if len(effect_data) > 2 else 'N/A'}")
            else:
                print(f"  {part.name}: No {effect_name} attribute")
        
        if not part_had_effects:
            print(f"  {part.name}: No active turn-end effects")
    
    # Recalculate character's total health after applying effects
    character.calculate_health_from_body_parts()
    
    # Check for and deactivate buffs that require body parts at 1 or less HP
    deactivate_buffs_for_damaged_body_parts(character)
    
    # ALSO check for weapon unequipping if body parts are damaged (status effect damage)
    if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'check_buffs_on_body_part_damage'):
        globals()['battle_menu_instance'].check_buffs_on_body_part_damage(character)
    
    # Recalculate character stats after potential buff deactivation
    update_character_stats(character)
    
    # Decrease durations for turn-end effects ONLY for this character
    decrease_turn_end_effect_durations(character)
    
    print(f"💥 === TURN END EFFECTS COMPLETE FOR {char_name.upper()} ===\n")

def deactivate_buffs_for_damaged_body_parts(character):
    """
    Check for buffs that require body parts that are at 1 or less HP and deactivate them.
    This includes both specific buffs (dodge, shield) and general active buff moves.
    """
    char_name = getattr(character, 'name', 'Unknown')
    print(f"🔍 Checking buff deactivation for {char_name} due to body part damage")
    
    if not hasattr(character, 'body_parts'):
        return
    
    # Check specific buffs first (legacy system)
    if hasattr(character, 'buffs'):
        # Check DODGE buff (requires 2 legs)
        if hasattr(character.buffs, 'buf_dodge'):
            dodge_data = character.buffs.buf_dodge
            if dodge_data[1] > 0 and dodge_data[2] > 0:  # Active dodge buff
                functional_legs = sum(1 for part in character.body_parts 
                                    if "LEG" in part.name.upper() and part.p_pvt >= 2)
                if functional_legs < 2:
                    dodge_data[1] = 0  # Deactivate by setting level to 0
                    dodge_data[2] = 0  # Also set duration to 0
                    message = f"{char_name}: BUF_DODGE deactivated - insufficient legs ({functional_legs}/2)"
                    print(f"  ⚠️ {message}")
                    
                    # Add to battle log
                    if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                        globals()['battle_menu_instance'].add_log_entry(message, "effect", (255, 100, 100))
                else:
                    print(f"  ✅ BUF_DODGE remains active - functional legs: {functional_legs}/2")
        
        # Check SHIELD buff (requires 1 arm)  
        if hasattr(character.buffs, 'buf_shield'):
            shield_data = character.buffs.buf_shield
            if shield_data[1] > 0 and shield_data[2] > 0:  # Active shield buff
                functional_arms = sum(1 for part in character.body_parts 
                                    if "ARM" in part.name.upper() and part.p_pvt > 1)
                if functional_arms < 1:
                    shield_data[1] = 0  # Deactivate by setting level to 0
                    shield_data[2] = 0  # Also set duration to 0
                    message = f"{char_name}: BUF_SHIELD deactivated - insufficient arms ({functional_arms}/1)"
                    print(f"  ⚠️ {message}")
                    
                    # Add to battle log
                    if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                        globals()['battle_menu_instance'].add_log_entry(message, "effect", (255, 100, 100))
                else:
                    print(f"  ✅ BUF_SHIELD remains active - functional arms: {functional_arms}/1")
    
    # Check general active buff moves (new system) - simplified approach
    if hasattr(character, 'active_buffs') and hasattr(character.active_buffs, 'active_buff_moves'):
        buffs_to_deactivate = []
        
        for move_name, buff_data in character.active_buffs.active_buff_moves.items():
            if not buff_data.get('active', False):
                continue  # Skip already inactive buffs
                
            requirements = buff_data.get('requirements', [])
            if not requirements:
                continue  # Skip buffs without body part requirements
            
            # Simple body part damage check - if any required body part is at 0 HP, deactivate
            can_maintain_buff = True
            failed_parts = []
            
            for requirement in requirements:
                req_upper = requirement.upper()
                
                # Check for damaged parts matching requirement
                for part in character.body_parts:
                    part_name_upper = part.name.upper()
                    
                    # Simple matching logic - if requirement contains any part name or vice versa
                    if (req_upper in part_name_upper or part_name_upper in req_upper or 
                        any(keyword in part_name_upper for keyword in req_upper.split()) or
                        any(keyword in req_upper for keyword in part_name_upper.split())):
                        
                        if part.p_pvt <= 1:  # Body part is at 1 HP or less
                            can_maintain_buff = False
                            failed_parts.append(part.name)
            
            if not can_maintain_buff:
                buffs_to_deactivate.append((move_name, failed_parts))
        
        # Deactivate buffs that can't be maintained
        for move_name, failed_parts in buffs_to_deactivate:
            character.active_buffs.deactivate_buff_move(move_name)
            
            # Also deactivate corresponding buff effects
            effects = character.active_buffs.active_buff_moves[move_name].get('effects', [])
            # Use the same list defined elsewhere to ensure consistency
            effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
            
            for effect in effects:
                if len(effect) >= 2:
                    effect_name = effect[0]
                    
                    # Handle regular buff/debuff effects
                    if hasattr(character, 'buffs') and hasattr(character.buffs, effect_name):
                        buff_effect_data = getattr(character.buffs, effect_name)
                        buff_effect_data[1] = 0  # Set level to 0
                        buff_effect_data[2] = 0  # Set duration to 0
                        print(f"  🔹 Deactivated regular buff effect: {effect_name}")
                    
                    # Handle Effect-on-Hit buffs (remove from all body parts) 
                    elif effect_name in effect_on_hit_buffs:
                        print(f"  🔥 Deactivating Effect-on-Hit buff: {effect_name}")
                        removed_count = 0
                        for part in character.body_parts:
                            if hasattr(part, 'p_eff') and hasattr(part.p_eff, effect_name):
                                # Get current effect data 
                                effect_data = getattr(part.p_eff, effect_name)
                                if len(effect_data) >= 3 and effect_data[2] > 0:  # Check if actually active
                                    effect_data[1] = 0  # Set level to 0
                                    effect_data[2] = 0  # Set duration to 0
                                    print(f"    → Removed {effect_name} from {part.name}")
                                    removed_count += 1
                        if removed_count > 0:
                            print(f"  ✅ Effect-on-Hit buff {effect_name} deactivated from {removed_count} body parts")
                        else:
                            print(f"  ℹ️  Effect-on-Hit buff {effect_name} was already inactive")
            
            message = f"{char_name}: {move_name} deactivated - damaged parts: {', '.join(failed_parts)}"
            print(f"  ⚠️ {message}")
            
            # Add to battle log
            if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                globals()['battle_menu_instance'].add_log_entry(message, "effect", (255, 100, 100))

def decrease_turn_start_effect_durations(character):
    """
    Decrease durations for turn-start effects (stun, sleep, freeze) for a specific character only.
    Also processes upkeep costs for Effect-on-Hit buffs.
    """
    char_name = getattr(character, 'name', 'Unknown')
    print(f"⏰ Processing turn-start effects and upkeep costs for {char_name}")
    
    # Get list of turn-start effects from configuration
    from Status_Effects_Config import get_effects_by_timing, get_effect_config
    turn_start_effects = get_effects_by_timing('start_turn')
    
    # Track which Effect-on-Hit buffs have already been processed for upkeep
    processed_upkeep_buffs = set()
    
    for part in character.body_parts:
        if not hasattr(part, 'p_eff'):
            continue
            
        effetti = part.p_eff
        
        for effect_name in turn_start_effects:
            if hasattr(effetti, effect_name):
                effect_data = getattr(effetti, effect_name)
                effect_config = get_effect_config(effect_name)
                
                # Check if effect is currently active (level > 0 and duration > 0)
                if effect_data[1] > 0 and effect_data[2] > 0:
                    
                    # Handle upkeep costs for Effect-on-Hit buffs
                    if effect_config and effect_config.get('buff_type') == 'effect_on_hit':
                        # Skip if we've already processed upkeep for this Effect-on-Hit buff
                        if effect_name in processed_upkeep_buffs:
                            continue
                        
                        processed_upkeep_buffs.add(effect_name)
                        
                        upkeep_cost = effect_config.get('upkeep_cost', 0)
                        upkeep_type = effect_config.get('upkeep_type', 'stamina')
                        
                        if upkeep_cost > 0:
                            # Check if character has enough resources for upkeep
                            if upkeep_type == 'stamina':
                                current_resource = character.sta
                                can_afford = current_resource >= upkeep_cost
                                if can_afford:
                                    character.sta -= upkeep_cost
                                    print(f"  {char_name}: {effect_name.upper()} upkeep cost {upkeep_cost} stamina (STA: {current_resource} → {character.sta})")
                            elif upkeep_type == 'reserve':
                                current_resource = character.res
                                can_afford = current_resource >= upkeep_cost
                                if can_afford:
                                    character.res -= upkeep_cost
                                    print(f"  {char_name}: {effect_name.upper()} upkeep cost {upkeep_cost} reserve (RES: {current_resource} → {character.res})")
                            else:
                                can_afford = True  # Unknown upkeep type, skip cost
                            
                            # If can't afford upkeep, deactivate the buff
                            if not can_afford:
                                effect_data[1] = 0  # Deactivate
                                effect_data[2] = 0  # Set duration to 0
                                print(f"  {char_name}: {effect_name.upper()} deactivated - insufficient {upkeep_type} for upkeep cost {upkeep_cost}")
                                
                                # Add to battle log
                                if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                                    globals()['battle_menu_instance'].add_log_entry(f"{char_name}: {effect_name.upper()} deactivated - insufficient {upkeep_type}", "effect", (255, 100, 100))
                                continue  # Skip duration processing since buff is deactivated
                    
                    # Process duration for regular effects (not Effect-on-Hit buffs which have permanent duration)
                    if not (effect_config and effect_config.get('buff_type') == 'effect_on_hit'):
                        # Check if this effect should have its duration reduced over time
                        from Status_Effects_Config import should_effect_reduce_over_time
                        
                        if should_effect_reduce_over_time(effect_name):
                            old_duration = effect_data[2]
                            new_duration = old_duration - 1
                            
                            # Update the duration
                            effect_data[2] = new_duration
                            
                            if new_duration <= 0:
                                # Effect expired, deactivate it (set level to 0)
                                effect_data[1] = 0
                                print(f"  {part.name}: {effect_name.upper()} expired")
                                
                                # Add to battle log
                                if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                                    globals()['battle_menu_instance'].add_log_entry(f"{char_name}'s {part.name}: {effect_name.upper()} expired", "effect", (150, 150, 150))
                            else:
                                # Effect duration reduced but still active
                                print(f"  {part.name}: {effect_name.upper()} duration {old_duration} -> {new_duration}")
                        else:
                            # Effect has infinite duration (like sleep), skip duration reduction
                            print(f"  {part.name}: {effect_name.upper()} has infinite duration - skipping reduction")

def decrease_turn_end_effect_durations(character):
    """
    Decrease durations for turn-end effects (damage/healing over time) for a specific character only.
    """
    char_name = getattr(character, 'name', 'Unknown')
    print(f"⏰ Decreasing turn-end effect durations for {char_name}")
    
    # Get list of turn-end effects from configuration  
    from Status_Effects_Config import get_effects_by_timing, should_effect_reduce_over_time
    turn_end_effects = get_effects_by_timing('end_turn')
    
    for part in character.body_parts:
        if not hasattr(part, 'p_eff'):
            continue
            
        effetti = part.p_eff
        
        for effect_name in turn_end_effects:
            if hasattr(effetti, effect_name):
                effect_data = getattr(effetti, effect_name)
                
                # Check if effect is currently active (level > 0 and duration > 0)
                if effect_data[1] > 0 and effect_data[2] > 0:
                    
                    # Check if this effect should have its duration reduced over time
                    if should_effect_reduce_over_time(effect_name):
                        old_duration = effect_data[2]
                        new_duration = old_duration - 1
                        
                        # Update the duration
                        effect_data[2] = new_duration
                        
                        if new_duration <= 0:
                            # Effect expired, deactivate it (set level to 0)
                            effect_data[1] = 0
                            print(f"  {part.name}: {effect_name.upper()} expired")
                            
                            # Add to battle log
                            if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                                globals()['battle_menu_instance'].add_log_entry(f"{char_name}'s {part.name}: {effect_name.upper()} expired", "effect", (150, 150, 150))
                        else:
                            # Effect duration reduced but still active
                            print(f"  {part.name}: {effect_name.upper()} duration {old_duration} -> {new_duration}")
                    else:
                        # Effect has infinite duration (like acid, sleep), skip duration reduction
                        print(f"  {part.name}: {effect_name.upper()} has infinite duration - skipping reduction")

def activate_effects():
    """
    DEPRECATED: This function is disabled and should not be called.
    Status effects are now processed per-character during their turns.
    
    Returns:
        list: Empty list (function disabled)
    """
    # Function completely disabled - return immediately
    return []
    
    # OLD CODE BELOW - DISABLED
    messages = []
    global event_log
    if 'event_log' not in globals():
        event_log = []
    
    print("\n" + "="*50)
    print("ACTIVATING STATUS EFFECTS FOR ALL CHARACTERS")
    print("="*50)
    
    # Process all characters
    for character in [player, enemy]:
        char_name = getattr(character, 'name', 'Unknown')
        print(f"\nProcessing status effects for {char_name}:")
        
        if not hasattr(character, 'body_parts') or not character.body_parts:
            print(f"  No body parts found for {char_name}")
            continue
        
        # Process damage-over-time effects for each body part using configuration
        for part_index, part in enumerate(character.body_parts):
            if not hasattr(part, 'p_eff'):
                continue
            
            effetti = part.p_eff
            part_had_effects = False
            
            # Get list of all possible status effects
            possible_effects = ['bleed', 'poison', 'burn', 'acid', 'frost', 'heal', 'regeneration']
            
            # Process each possible effect using configuration
            for effect_name in possible_effects:
                if hasattr(effetti, effect_name):
                    effect_data = getattr(effetti, effect_name)
                    # Check if effect is active (level >= 1 and duration >= 1)
                    if len(effect_data) >= 3 and effect_data[1] >= 1 and effect_data[2] >= 1:
                        part_had_effects = True
                        effect_level = effect_data[1]
                        
                        # Use configuration to get damage per turn
                        damage = get_damage_per_turn(effect_name, effect_level)
                        
                        if damage != 0:  # Only process if there's damage/healing
                            old_pvt = part.p_pvt
                            if damage > 0:
                                # Damage effect
                                part.p_pvt = max(0, part.p_pvt - damage)
                                actual_damage = old_pvt - part.p_pvt
                                message = f"{effect_name.upper()} dealt {actual_damage} damage to {char_name}'s {part.name}"
                                
                                # Check for body part destruction and trigger explosive mindset
                                if old_pvt > 0 and part.p_pvt == 0:
                                    # For status effects, there's no direct attacker, so we pass None
                                    process_memory_skills_bodypart_loss(character, None, part.name)
                            else:
                                # Healing effect - BUT CHECK FOR MESS_UP FIRST!
                                if effect_name == 'regeneration' and hasattr(part.p_eff, 'mess_up') and len(part.p_eff.mess_up) >= 3 and part.p_eff.mess_up[1] >= 1 and part.p_eff.mess_up[2] >= 1:
                                    # MESS_UP PREVENTS HEALING! Only reduce mess_up level by 1
                                    part.p_eff.mess_up[1] = max(0, part.p_eff.mess_up[1] - 1)
                                    if part.p_eff.mess_up[1] == 0:
                                        part.p_eff.mess_up[2] = 0  # Clear duration too
                                    message = f"REGENERATION blocked by MESS_UP on {char_name}'s {part.name} (mess_up reduced by 1 level)"
                                else:
                                    # Normal healing
                                    part.p_pvt = min(part.max_p_pvt, part.p_pvt - damage)  # damage is negative for healing
                                    actual_healing = part.p_pvt - old_pvt
                                    message = f"{effect_name.upper()} healed {actual_healing} HP to {char_name}'s {part.name}"
                            
                            messages.append(message)
                            if globals().get('battle_menu_instance') and hasattr(globals()['battle_menu_instance'], 'add_log_entry'):
                                globals()['battle_menu_instance'].add_log_entry(message, log_type="effect", color=(255, 150, 255))
                            elif hasattr(globals().get('ui', None), 'add_log_entry'):
                                globals()['ui'].add_log_entry(message, log_type="effect", color=(255, 150, 255))
                            else:
                                print(f"[{effect_name.upper()} LOG]: {message}")
            
            if not part_had_effects:
                print(f"  {part.name}: No active status effects")
        
        # Recalculate character's total health after applying effects
        character.calculate_health_from_body_parts()
        
        # Check for buffs that need deactivation due to body part damage
        deactivate_buffs_for_damaged_body_parts(character)
    
    print("="*50)
    
    if not messages:
        print("No active status effects found on any characters")
    
    return messages

def check_dodge_shield_evasion(defender, attacker_move, move_stamina_cost):
    """
    Check if the defender can evade the attack using DODGE or SHIELD buffs.
    Now supports unblockable and undodgable property effects.
    
    Args:
        defender: The character being attacked
        attacker_move: The move being used to attack
        move_stamina_cost: The stamina cost of the attacking move (no longer used for evasion cost)
    
    Returns:
        tuple: (can_evade, evasion_type, stamina_consumed)
            - can_evade: bool, True if attack was evaded
            - evasion_type: str, "DODGE", "SHIELD", or None
            - stamina_consumed: int, amount of stamina consumed by evasion (always DodgeShield_Stamina_Cost)
    """
    
    print(f"\n🛡️ === EVASION CHECK START ===")
    print(f"🛡️ Defender: {defender.name}")
    print(f"🛡️ Attacker move: {getattr(attacker_move, 'name', attacker_move)}")
    print(f"🛡️ Evasion stamina cost: {DodgeShield_Stamina_Cost}")
    print(f"🛡️ Defender current stamina: {defender.sta}")
    
    # Check for property effects that bypass evasion
    is_undodgable = has_property_effect(attacker_move, 'undodgable')
    is_unblockable = has_property_effect(attacker_move, 'unblockable')
    
    if is_undodgable:
        print(f"🛡️ ⚠️  UNDODGABLE MOVE: Dodge attempts will fail but still consume stamina")
    if is_unblockable:
        print(f"🛡️ ⚠️  UNBLOCKABLE MOVE: Shield attempts will fail but still consume stamina")
    
    # Check for DODGE buff (requires 2 legs)
    dodge_data = getattr(defender.buffs, 'buf_dodge', ["buf_dodge", 0, 0])
    print(f"🛡️ DODGE buff data: {dodge_data}")
    
    if dodge_data[1] > 0 and dodge_data[2] > 0:  # Active dodge buff
        print(f"🛡️ DODGE buff is ACTIVE (level={dodge_data[1]}, duration={dodge_data[2]})")
        # Check if defender has 2 functional legs
        legs = []
        for part in defender.body_parts:
            if "LEG" in part.name.upper() and part.p_pvt > 1:
                legs.append(part)
        
        print(f"🛡️ Checking legs: found {len(legs)} functional legs")
        for leg in legs:
            print(f"🛡️ - {leg.name}: HP={leg.p_pvt}")
        
        if len(legs) >= 2:  # Has 2 functional legs
            print(f"🛡️ Has enough legs for DODGE")
            # Check if defender has enough stamina to dodge - using fixed stamina cost
            if defender.sta >= DodgeShield_Stamina_Cost:
                # Always consume stamina and reduce dodge level (even for undodgable moves)
                defender.sta -= DodgeShield_Stamina_Cost
                dodge_data[1] -= 1  # Reduce dodge level by 1
                if dodge_data[1] <= 0:  # If level reaches 0, duration also becomes 0
                    dodge_data[2] = 0
                    print(f"🛡️ 🚫 DODGE buff depleted and deactivated!")
                
                # Update the buff data back to the character
                setattr(defender.buffs, 'buf_dodge', dodge_data)
                
                if is_undodgable:
                    print(f"🛡️ ❌ DODGE FAILED (UNDODGABLE)! Still consuming {DodgeShield_Stamina_Cost} stamina")
                    print(f"DEBUG: {defender.name} attempted to dodge but failed (undodgable)! Stamina: {defender.sta + DodgeShield_Stamina_Cost} -> {defender.sta}, Dodge level: {dodge_data[1] + 1} -> {dodge_data[1]}")
                    # Continue to check shield - don't return here
                else:
                    print(f"🛡️ ✅ DODGE SUCCESS! Consuming {DodgeShield_Stamina_Cost} stamina")
                    print(f"DEBUG: {defender.name} successfully dodged attack! Stamina: {defender.sta + DodgeShield_Stamina_Cost} -> {defender.sta}, Dodge level: {dodge_data[1] + 1} -> {dodge_data[1]}")
                    return True, "DODGE", DodgeShield_Stamina_Cost
            else:
                print(f"🛡️ ❌ Not enough stamina for DODGE ({defender.sta} < {DodgeShield_Stamina_Cost}) - NO ATTEMPT MADE")
        else:
            print(f"🛡️ ❌ Not enough functional legs for DODGE (need 2, have {len(legs)})")
    else:
        print(f"🛡️ DODGE buff is INACTIVE")
    
    # Check for SHIELD buff (requires 1 arm)
    shield_data = getattr(defender.buffs, 'buf_shield', ["buf_shield", 0, 0])
    print(f"🛡️ SHIELD buff data: {shield_data}")
    
    if shield_data[1] > 0 and shield_data[2] > 0:  # Active shield buff
        print(f"🛡️ SHIELD buff is ACTIVE (level={shield_data[1]}, duration={shield_data[2]})")
        # Check if defender has at least 1 functional arm
        arms = []
        for part in defender.body_parts:
            if "ARM" in part.name.upper() and part.p_pvt > 1:
                arms.append(part)
        
        print(f"🛡️ Checking arms: found {len(arms)} functional arms")
        for arm in arms:
            print(f"🛡️ - {arm.name}: HP={arm.p_pvt}")
        
        if len(arms) >= 1:  # Has at least 1 functional arm
            print(f"🛡️ Has enough arms for SHIELD")
            # Check if defender has enough stamina to shield - using fixed stamina cost
            if defender.sta >= DodgeShield_Stamina_Cost:
                # Always consume stamina and reduce shield level (even for unblockable moves)
                defender.sta -= DodgeShield_Stamina_Cost
                shield_data[1] -= 1  # Reduce shield level by 1
                if shield_data[1] <= 0:  # If level reaches 0, duration also becomes 0
                    shield_data[2] = 0
                    print(f"🛡️ 🚫 SHIELD buff depleted and deactivated!")
                
                # Update the buff data back to the character
                setattr(defender.buffs, 'buf_shield', shield_data)
                
                if is_unblockable:
                    print(f"🛡️ ❌ SHIELD FAILED (UNBLOCKABLE)! Still consuming {DodgeShield_Stamina_Cost} stamina")
                    print(f"DEBUG: {defender.name} attempted to shield but failed (unblockable)! Stamina: {defender.sta + DodgeShield_Stamina_Cost} -> {defender.sta}, Shield level: {shield_data[1] + 1} -> {shield_data[1]}")
                    # Attack hits despite shield attempt
                else:
                    print(f"🛡️ ✅ SHIELD SUCCESS! Consuming {DodgeShield_Stamina_Cost} stamina")
                    print(f"DEBUG: {defender.name} successfully blocked attack with shield! Stamina: {defender.sta + DodgeShield_Stamina_Cost} -> {defender.sta}, Shield level: {shield_data[1] + 1} -> {shield_data[1]}")
                    return True, "SHIELD", DodgeShield_Stamina_Cost
            else:
                print(f"🛡️ ❌ Not enough stamina for SHIELD ({defender.sta} < {DodgeShield_Stamina_Cost}) - NO ATTEMPT MADE")
        else:
            print(f"🛡️ ❌ Not enough functional arms for SHIELD (need 1, have {len(arms)})")
    else:
        print(f"🛡️ SHIELD buff is INACTIVE")
    
    # No evasion possible
    print(f"🛡️ === EVASION CHECK RESULT: NO EVASION ===\n")
    return False, None, 0

def decrease_all_characters_status_durations():
    """
    Decrease status effect durations for all characters in the game.
    This function should be called at the end of each turn.
    
    Returns:
        list: Combined list of all status effect messages
    """
    all_messages = []
    
    print("\n" + "="*50)
    print("DECREASING STATUS EFFECT DURATIONS FOR ALL CHARACTERS")
    print("="*50)
    
    # Process player
    player_messages = decrease_status_effect_durations(player)
    all_messages.extend(player_messages)
    
    # Process enemy
    enemy_messages = decrease_status_effect_durations(enemy)
    all_messages.extend(enemy_messages)
    
    # Update automatic debuffs after duration changes (some effects may have expired)
    update_all_automatic_debuffs()
    
    print("="*50)
    
    return all_messages

def calculate_total_effect_levels(character, effect_name):
    """
    Calculate total levels of a specific status effect across all body parts of a character.
    
    Args:
        character: Character object with body_parts
        effect_name (str): Name of the effect to count
        
    Returns:
        int: Total accumulated levels of the effect
    """
    total_levels = 0
    
    if not hasattr(character, 'body_parts') or not character.body_parts:
        return 0
        
    for part in character.body_parts:
        if not hasattr(part, 'p_eff'):
            continue
            
        effetti = part.p_eff
        if hasattr(effetti, effect_name.lower()):
            effect_data = getattr(effetti, effect_name.lower())
            # Check if effect is active (level >= 1 and duration >= 1)
            if len(effect_data) >= 3 and effect_data[1] >= 1 and effect_data[2] >= 1:
                total_levels += effect_data[1]
                
    return total_levels

def set_automatic_debuff(character, stat_name, level):
    """
    SET (not stack) an automatic debuff to a specific level.
    This overwrites any existing automatic debuff.
    
    Args:
        character: Character object
        stat_name: Stat to debuff ('forz', 'des', 'spe', etc.)
        level: Debuff level (positive number, will be applied as negative)
    """
    stat_mapping = {
        'rig': 'buf_rig',
        'res': 'buf_res', 
        'sta': 'buf_sta',
        'forz': 'buf_forz',
        'des': 'buf_des',
        'spe': 'buf_spe',
        'vel': 'buf_vel'
    }
    
    if stat_name not in stat_mapping:
        return
        
    buf_attr = stat_mapping[stat_name]
    
    if not hasattr(character, 'buffs') or not hasattr(character.buffs, buf_attr):
        return
    
    char_name = getattr(character, 'name', 'Unknown')
    
    if level > 0:
        # SET debuff to specific level (duration 999 marks it as automatic)
        setattr(character.buffs, buf_attr, [buf_attr, -level, 999])
        print(f"SET automatic debuff on {char_name} - {stat_name}: Level -{level}, Duration 999")
    else:
        # REMOVE debuff (set to inactive)
        setattr(character.buffs, buf_attr, [buf_attr, 0, 0])
        print(f"REMOVED automatic debuff from {char_name} - {stat_name}")
    
    # Update character stats
    update_character_stats(character)

def update_automatic_debuffs(character):
    """
    Update automatic debuffs based on current status effect levels.
    This should be called whenever status effects change.
    
    Args:
        character: Character object to update debuffs for
    """
    char_name = getattr(character, 'name', 'Unknown')
    print(f"\nUpdating automatic debuffs for {char_name}:")
    
    # Get all effects that can apply debuffs
    debuff_effects = get_all_debuff_effects()
    
    # Group effects by the stat they debuff to handle multiple effects affecting the same stat
    stat_debuffs = {}  # {stat_name: total_debuff_level}
    
    for effect_name in debuff_effects:
        config = get_effect_config(effect_name)
        if not config or config['debuff_type'] != 'auto':
            continue
            
        # Calculate total effect levels
        total_levels = calculate_total_effect_levels(character, effect_name)
        
        # Calculate required debuff level for this effect
        required_debuff = calculate_debuff_level(effect_name, total_levels)
        
        stat_name = config['debuff_stat']
        
        print(f"  {effect_name.upper()}: {total_levels} levels -> {required_debuff} {stat_name} debuff")
        
        # Add this effect's debuff to the total for this stat
        if stat_name not in stat_debuffs:
            stat_debuffs[stat_name] = 0
        stat_debuffs[stat_name] += required_debuff
    
    # Apply the combined debuffs for each stat
    for stat_name, total_debuff in stat_debuffs.items():
        # Get current automatic debuff level 
        current_debuff = 0
        if hasattr(character, 'buffs') and hasattr(character.buffs, f'buf_{stat_name}'):
            buff_data = getattr(character.buffs, f'buf_{stat_name}')
            # Check if this is an automatic debuff (duration 999)
            if len(buff_data) >= 3 and buff_data[2] == 999:
                try:
                    level_value = int(buff_data[1]) if isinstance(buff_data[1], str) else buff_data[1]
                    if level_value < 0:
                        current_debuff = abs(level_value)  # Current debuff level (absolute value)
                except (ValueError, TypeError):
                    current_debuff = 0
        
        print(f"  → TOTAL {stat_name.upper()} debuff: {total_debuff} (current: {current_debuff})")
        
        # SET debuff to correct level (only if it changed)
        if total_debuff != current_debuff:
            set_automatic_debuff(character, stat_name, total_debuff)
            if total_debuff > 0:
                print(f"    SET {stat_name} debuff to: -{total_debuff}")
            else:
                print(f"    REMOVED {stat_name} debuff")

def update_all_automatic_debuffs():
    """
    Update automatic debuffs for all characters based on their current status effects.
    This should be called after any status effect changes.
    """
    print("\n" + "="*50)
    print("UPDATING AUTOMATIC DEBUFFS FOR ALL CHARACTERS")
    print("="*50)
    
    # Update debuffs for all characters
    for character in [player, enemy]:
        update_automatic_debuffs(character)
        # Update character stats to reflect new debuffs
        update_character_stats(character)
    
    print("="*50)

def end_player_turn():
    """
    End the player's turn and advance to the next character in speed-based queue.
    This function should be called when the player completes their turn.
    """
    global turn_player, Turn, battle_menu_instance, rhythm_tracking
    
    # Process turn-end effects for PLAYER before ending their turn
    process_turn_end_effects(player)
    
    turn_player += 1
    old_turn = Turn
    Turn = (turn_player + turn_enemy) // 2  # Integer division (rounded down)
    
    # Reset rhythm tracking for player
    rhythm_tracking['player'] = 0
    print(f"[RHYTHM] Player rhythm count reset")
    
    print(f"\n--- PLAYER TURN ENDED ---")
    print(f"Player turns completed: {turn_player}")
    print(f"Enemy turns completed: {turn_enemy}")
    print(f"Overall Turn: {old_turn} -> {Turn}")
    
    # Advance the speed-based turn queue
    if battle_menu_instance and hasattr(battle_menu_instance, 'advance_turn_queue'):
        battle_menu_instance.advance_turn_queue()
    
    if Turn > old_turn:
        print(f"*** ROUND {Turn} COMPLETED ***")
        end_of_round_processing()
    
    return Turn

def end_enemy_turn():
    """
    End the enemy's turn and advance to the next character in speed-based queue.
    This function should be called when the enemy completes their turn.
    """
    global turn_enemy, Turn, battle_menu_instance, rhythm_tracking
    
    # Process turn-end effects for ENEMY before ending their turn
    process_turn_end_effects(enemy)
    
    turn_enemy += 1
    old_turn = Turn
    Turn = (turn_player + turn_enemy) // 2  # Integer division (rounded down)
    
    # Reset rhythm tracking for enemy
    rhythm_tracking['enemy'] = 0
    print(f"[RHYTHM] Enemy rhythm count reset")
    
    print(f"\n--- ENEMY TURN ENDED ---")
    print(f"Player turns completed: {turn_player}")
    print(f"Enemy turns completed: {turn_enemy}")
    print(f"Overall Turn: {old_turn} -> {Turn}")
    
    # Advance the speed-based turn queue
    if battle_menu_instance and hasattr(battle_menu_instance, 'advance_turn_queue'):
        battle_menu_instance.advance_turn_queue()
    
    if Turn > old_turn:
        print(f"*** ROUND {Turn} COMPLETED ***")
        end_of_round_processing()
    
    return Turn

def end_of_round_processing():
    """
    Handles all logic that should occur at the very end of a combat round.
    NOTE: Status effects are now processed per-character during their turns.
    This function is kept for backward compatibility but no longer processes effects.
    """
    global battle_menu_instance, player, enemy, turn_player, turn_enemy

    # Status effects are now processed per-character during their turns - no processing here

    if battle_menu_instance:
        battle_menu_instance.check_and_update_active_buffs()

    # Duration decreases are now handled at turn start/end, not here
    print("Round completed - effects are processed per character during their turns.")

def get_turn_info():
    """
    Get current turn information.
    
    Returns:
        dict: Dictionary containing turn information
    """
    return {
        'player_turns': turn_player,
        'enemy_turns': turn_enemy,
        'overall_turn': Turn,
        'whose_turn_next': 'player' if turn_player <= turn_enemy else 'enemy'
    }

def display_turn_info():
    """
    Display current turn information in a formatted way.
    """
    info = get_turn_info()
    
    print(f"\n{'='*30}")
    print(f"TURN INFORMATION")
    print(f"{'='*30}")
    print(f"Player turns completed: {info['player_turns']}")
    print(f"Enemy turns completed: {info['enemy_turns']}")
    print(f"Overall Turn (Round): {info['overall_turn']}")
    print(f"Next turn: {info['whose_turn_next'].upper()}")
    print(f"{'='*30}")

def reset_turn_counters():
    """
    Reset all turn counters to 0. Use this to start a new battle.
    """
    global turn_player, turn_enemy, Turn, current_round, turn_queue, current_turn_index, first_turn_of_round
    
    turn_player = 0
    turn_enemy = 0
    Turn = 0
    current_round = 0
    turn_queue = []
    current_turn_index = 0
    first_turn_of_round = True
    
    print("Turn counters reset to 0")
    # update_turn_display()  # Update the visual display
    display_turn_info()

def initialize_speed_based_turns():
    """Initialize the speed-based turn system by creating a turn queue ordered by speed"""
    global turn_queue, current_turn_index, first_turn_of_round, current_round
    
    # Get character speeds
    player_speed = getattr(player, 'vel', 0)
    enemy_speed = getattr(enemy, 'vel', 0)
    
    # Create list of (character, name, speed) tuples
    characters = [
        (player, player.name, player_speed),
        (enemy, enemy.name, enemy_speed)
    ]
    
    # Sort by speed (highest first)
    characters.sort(key=lambda x: x[2], reverse=True)
    
    # Create turn queue with character objects
    turn_queue = [char[0] for char in characters]
    
    # Reset turn tracking
    current_turn_index = 0
    first_turn_of_round = True
    current_round = 0
    
    return turn_queue

def get_current_character():
    """Get the character whose turn it currently is"""
    global turn_queue, current_turn_index
    
    if not turn_queue or current_turn_index >= len(turn_queue):
        return None
    
    current_char = turn_queue[current_turn_index]
    return current_char

def advance_turn_queue():
    """Advance to the next character in the turn queue"""
    global current_turn_index, first_turn_of_round, current_round
    
    old_index = current_turn_index
    old_char = turn_queue[current_turn_index] if turn_queue and current_turn_index < len(turn_queue) else None
    
    current_turn_index += 1
    
    # If we've gone through all characters, start a new round
    if current_turn_index >= len(turn_queue):
        current_turn_index = 0
        current_round += 1
        first_turn_of_round = True
        return True  # New round started
    
    return False  # Same round continues

def get_turn_order_message():
    """Get the turn order message showing who attacks first in this round"""
    global turn_queue, first_turn_of_round, current_turn_index
    
    if not first_turn_of_round or not turn_queue:
        return None
        
    # Always show who attacks first in this round
    first_char = turn_queue[0]
    message = f"{first_char.name} attacks first!"
    
    return message

def get_current_turn_message():
    """Get message for the current character's turn (first/second)"""
    global turn_queue, current_turn_index
    
    if not turn_queue or current_turn_index >= len(turn_queue):
        return None
    
    current_char = turn_queue[current_turn_index]
    
    if current_turn_index == 0:
        return f"{current_char.name} attacks first!"
    elif current_turn_index == 1:
        return f"{current_char.name} attacks second!"
    
    return None

def apply_buff_debuff(character, stat_name, level=1, duration=1):
    """
    Apply a buff or debuff to a character's stat using the new buffs system.
    If the buff already exists, it stacks: level = sum of levels, duration = previous duration + 1.
    
    Args:
        character: The character object
        stat_name (str): Name of the stat ('rig', 'res', 'sta', 'forz', 'des', 'spe', 'vel', 'buf_dodge', 'buf_shield')
        level (int): Level of the buff/debuff (positive for buff, negative for debuff)
        duration (int): Duration in turns (default 1)
    """
    # Map stat names to their corresponding buf_ attributes
    stat_mapping = {
        'rig': 'buf_rig',
        'res': 'buf_res', 
        'sta': 'buf_sta',
        'forz': 'buf_forz',
        'des': 'buf_des',
        'spe': 'buf_spe',
        'vel': 'buf_vel',
        'buf_dodge': 'buf_dodge',
        'buf_shield': 'buf_shield'
    }
    
    print(f"💊 === BUFF APPLICATION START ===")
    print(f"💊 Character: {getattr(character, 'name', 'Unknown')}")
    print(f"💊 Stat name: {stat_name}")
    print(f"💊 Level: {level}")
    print(f"💊 Duration: {duration}")
    
    if stat_name not in stat_mapping:
        print(f"💊 ❌ Invalid stat name '{stat_name}'. Valid stats are: {list(stat_mapping.keys())}")
        return
    
    buf_attr = stat_mapping[stat_name]
    print(f"💊 Buff attribute: {buf_attr}")
    
    if not hasattr(character, 'buffs') or not hasattr(character.buffs, buf_attr):
        print(f"💊 ❌ Character {getattr(character, 'name', 'Unknown')} does not have buffs system or attribute '{buf_attr}'")
        return
    
    # Get current buff data
    current_buff = getattr(character.buffs, buf_attr)
    print(f"💊 Current buff data: {current_buff}")
    
    # Check if the buff is already active (level != 0 and duration > 0)
    if current_buff[1] != 0 and current_buff[2] > 0:
        # Stack the buff: sum levels, add 1 to duration
        new_level = current_buff[1] + level
        new_duration = current_buff[2] + 1
        
        setattr(character.buffs, buf_attr, [buf_attr, new_level, new_duration])
        print(f"💊 ✅ Stacked buff/debuff on {getattr(character, 'name', 'Unknown')} - {stat_name}: Level {current_buff[1]} + {level} = {new_level}, Duration {current_buff[2]} + 1 = {new_duration}")
    else:
        # Apply new buff since none exists or it's inactive
        setattr(character.buffs, buf_attr, [buf_attr, level, duration])
        print(f"💊 ✅ Applied NEW buff/debuff to {getattr(character, 'name', 'Unknown')} - {stat_name}: Level {level}, Duration {duration}")
    
    # Verify the buff was applied
    final_buff = getattr(character.buffs, buf_attr)
    print(f"💊 Final buff data: {final_buff}")
    
    # Update the character's current stats based on the new buff values (skip for DODGE/SHIELD)
    if stat_name not in ['buf_dodge', 'buf_shield']:
        update_character_stats(character)
    
    buff_type = "buff" if level > 0 else "debuff"
    print(f"💊 ✅ Applied {buff_type} to {getattr(character, 'name', 'Unknown')} - {stat_name} successfully")
    print(f"💊 === BUFF APPLICATION END ===\n")

def get_character_buff_level(character, stat_name):
    """
    Get the current buff level for a specific stat from the new buffs system.
    This function is for compatibility with UI code that expects numeric buff values.
    
    Args:
        character: The character object
        stat_name (str): Name of the stat ('rig', 'res', 'sta', 'forz', 'des', 'spe', 'vel', 'buf_dodge', 'buf_shield')
    
    Returns:
        int: The current buff level (positive for buff, negative for debuff, 0 for no buff)
    """
    # Map stat names to their corresponding buf_ attributes
    stat_mapping = {
        'rig': 'buf_rig',
        'res': 'buf_res', 
        'sta': 'buf_sta',
        'forz': 'buf_forz',
        'des': 'buf_des',
        'spe': 'buf_spe',
        'vel': 'buf_vel',
        'buf_dodge': 'buf_dodge',
        'buf_shield': 'buf_shield'
    }
    
    if stat_name not in stat_mapping:
        return 0
    
    buf_attr = stat_mapping[stat_name]
    
    if not hasattr(character, 'buffs') or not hasattr(character.buffs, buf_attr):
        return 0
    
    # Get current buff data
    buff_data = getattr(character.buffs, buf_attr)
    
    # Return level if duration > 0, otherwise return 0
    return buff_data[1] if buff_data[2] > 0 else 0

def add_move_to_character(character, move_name, move_type, strength_scaling, dexterity_scaling, 
                         special_scaling, effects=None, requirements=None, elements=None, accuracy=100):
    """
    Add a move to a character's move list.
    
    Args:
        character: The character object to add the move to
        move_name (str): Name of the move
        move_type (str): Type of move ('ATK', 'BUF', 'REA')
        strength_scaling (float): Strength scaling factor
        dexterity_scaling (float): Dexterity scaling factor
        special_scaling (float): Special scaling factor
        effects (list): Up to 4 different effects (optional)
        requirements (list): Up to 4 different requirements (optional)
        elements (list): Up to 2 different elements (optional)
        accuracy (int): Accuracy value (default 100)
    """
    # Validate move type
    valid_types = ['ATK', 'BUF', 'REA']
    if move_type not in valid_types:
        print(f"Invalid move type '{move_type}'. Valid types are: {valid_types}")
        return False
    
    # Validate effects list (max 4)
    if effects is not None and len(effects) > 4:
        print(f"Too many effects specified ({len(effects)}). Maximum is 4.")
        return False
    
    # Validate requirements list (max 4)
    if requirements is not None and len(requirements) > 4:
        print(f"Too many requirements specified ({len(requirements)}). Maximum is 4.")
        return False
    
    # Validate elements list (max 2)
    if elements is not None and len(elements) > 2:
        print(f"Too many elements specified ({len(elements)}). Maximum is 2.")
        return False
    
    # Auto-calculate elements if not provided
    if elements is None:
        scaling_dict = {'forz': strength_scaling, 'des': dexterity_scaling, 'spe': special_scaling}
        species_name = getattr(character, 'species', 'Maedo')  # Default to Maedo if no species
        calculated_element = calculate_move_element(scaling_dict, species_name)
        elements = [calculated_element]
        print(f"[Element Auto-Calculation] Species: {species_name}, Scaling: {scaling_dict}, Calculated Element: {calculated_element}")
    
    # Check if character already has a move with the same name
    if hasattr(character, 'moves'):
        for existing_move in character.moves:
            if existing_move.name == move_name:
                print(f"Character {getattr(character, 'name', 'Unknown')} already has a move named '{move_name}'")
                return False
    
    # Create the new move (damage and stamina cost calculated automatically)
    new_move = Mossa(
        name=move_name,
        tipo=move_type,
        sca_for=strength_scaling,
        sca_des=dexterity_scaling,
        sca_spe=special_scaling,
        character=character,
        eff_appl=effects,
        reqs=requirements,
        elem=elements,
        accuracy=accuracy
    )
    
    # Add move to character
    if not hasattr(character, 'moves') or character.moves is None:
        character.moves = []
    
    character.moves.append(new_move)
    
    print(f"Added move '{move_name}' to {getattr(character, 'name', 'Unknown')}")
    print(f"  Type: {move_type}, Calculated Damage: {new_move.danno}, Calculated Stamina Cost: {new_move.stamina_cost}, Accuracy: {accuracy}%")
    print(f"  Scaling - STR: {strength_scaling}, DEX: {dexterity_scaling}, SPE: {special_scaling}")
    if effects:
        print(f"  Effects: {effects}")
    if requirements:
        print(f"  Requirements: {requirements}")
    if elements:
        print(f"  Elements: {elements}")
    
    return True

def add_ability_to_character(character, ability_name, punti, description, descriptionLong):
    """
    Add an ability to a character's ability list.
    """
    # Check if character already has an ability with the same name
    if hasattr(character, 'ability') and character.ability:
        for existing_ability in character.ability:
            if existing_ability.name == ability_name:
                print(f"Character {getattr(character, 'name', 'Unknown')} already has an ability named '{ability_name}'")
                return False
    
    # Create the new ability
    new_ability = Ability(
        name=ability_name,
        punti=punti,
        description=description,
        descriptionLong=descriptionLong,
    )
    
    # Add ability to character
    if not hasattr(character, 'ability') or character.ability is None:
        character.ability = []
    
    character.ability.append(new_ability)
    
    return True

def display_character_moves(character):
    """
    Display all moves for a character in a formatted way.
    
    Args:
        character: The character object
    """
    char_name = getattr(character, 'name', 'Unknown')
    
    if not hasattr(character, 'moves') or character.moves is None or len(character.moves) == 0:
        print(f"{char_name} has no moves.")
        return
    
    print(f"\n=== {char_name}'s Moves ===")
    for i, move in enumerate(character.moves, 1):
        print(f"{i}. {move.name} ({move.tipo})")
        print(f"   Damage: {move.danno} | Stamina Cost: {move.stamina_cost} | Accuracy: {move.accuracy}%")
        print(f"   Scaling - STR: {move.sca_for}, DEX: {move.sca_des}, SPE: {move.sca_spe}")
        if move.eff_appl:
            print(f"   Effects:")
            for effect in move.eff_appl:
                if isinstance(effect, str):
                    print(f"     {effect}")
                    print(f"       (Details: Basic)")
                elif isinstance(effect, list) and len(effect) >= 4:
                    # Format: [name, level, duration, immunity]
                    print(f"     {effect[0]}")
                    print(f"       (Level: {effect[1]}, Duration: {effect[2]}, Immunity: {effect[3]})")
                else:
                    print(f"     {str(effect)}")
                    print(f"       (Unknown format)")
        if move.reqs:
            print(f"   Requirements: {', '.join(move.reqs)}")
        if move.elem:
            print(f"   Elements: {', '.join(move.elem)}")
        print()  # Empty line for readability

def display_character_ability(character):
    """
    Display all ability for a character in a formatted way.
    
    Args:
        character: The character object
    """
    char_name = getattr(character, 'name', 'Unknown')
    
    if not hasattr(character, 'ability') or character.ability is None or len(character.ability) == 0:
        print(f"{char_name} has no ability.")
        return
    
    print(f"\n=== {char_name}'s Ability ===")
    for i, ability in enumerate(character.ability, 1):
        print(f"{i}. {ability.name}")
        print(f"   Punti: {ability.punti} | Descrizione: {ability.description}")
        print(f"   Descrizione Completa: {ability.descriptionLong}")
        print()  # Empty line for readability


# Initialize character data and apply initial effects
def initialize_game_data():
    """Initialize character data after all functions and objects are defined"""
    print("Initializing character data...")

    # Ensure player starts with full RIG and RES
    player.rig = player.max_rig
    player.res = player.max_res
    print(f"Player RIG initialized to full: {player.rig}/{player.max_rig}")
    print(f"Player RES initialized to full: {player.res}/{player.max_res}")

    # Ensure enemy also starts with full RIG and RES
    enemy.rig = enemy.max_rig
    enemy.res = enemy.max_res
    print(f"Enemy RIG initialized to full: {enemy.rig}/{enemy.max_rig}")
    print(f"Enemy RES initialized to full: {enemy.res}/{enemy.max_res}")

    # Apply initial stat updates after characters are created
    update_all_characters_stats()
    
    # Initialize memory skill state for both characters
    init_memory_skill_state(player)
    init_memory_skill_state(enemy)
    print("[MemorySkills] Memory skill system initialized")
    
    add_ability_to_character(player, "Chanche!", 1, "se CONFUSE/STUN, +1 FORZ", 
                         "I suoi attacchi fanno danni extra contro gli obbiettivi con lo status CONFUSE o STUN, come se il tuo personaggio avesse +1 STR")

    add_ability_to_character(player, "Dentistretti", 1, "se BURN/POISON, +1 FORZ",  
                         "I suoi attacchi fanno danni extra contro gli obbiettivi con lo status BURN o POISON, come se il tuo personaggio avesse +1 FORZ")

    # Display all moves for both characters
    print("\n" + "="*50)
    print("CHARACTER MOVES SUMMARY")
    print("="*50)
    display_character_moves(player)
    display_character_moves(enemy)

    display_character_ability(player)

    # Display current scaling factors
    display_scaling_factors()

# Character object definitions completed - functions will be called later after all definitions are loaded
#------------------------------------------------------------------------------------------------------------------

# Define  layout

import pygame
import sys
import random
import time
import traceback
import os
from PIL import Image, ImageTk
from pathlib import Path

# Initialize pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1000
FPS = 60

# Reference (design) resolution used for proportional scaling
REF_WIDTH = 1600
REF_HEIGHT = 1000

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (60, 179, 113)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# ...existing scaling factors and constants...
STAT_SCALING_FACTORS = {
    'rig': 5.0,
    'res': 30.0,
    'sta': 1.0,
    'forz': 2.0,
    'des': 2.0,
    'spe': 2.0,
    'vel': 1.0
}


class PygameUI:
    def check_win_loss(self):
        # Check BODY HP for both player and enemy
        player_body = next((p for p in player.body_parts if p.name.upper() == "BODY"), None)
        enemy_body = next((p for p in enemy.body_parts if p.name.upper() == "BODY"), None)
        if player_body and player_body.p_pvt <= 0:
            self.show_end_message(f"{enemy.name} defeated You!")
            return True
        if enemy_body and enemy_body.p_pvt <= 0:
            self.show_end_message(f"You defeated {enemy.name}")
            return True
        return False

    def show_end_message(self, message):
        # Draw big centered message
        self.screen.fill((0,0,0))
        big_font = pygame.font.Font(str(self._font_path), 120)
        text_rect = big_font.render(message, True, (255,255,0)).get_rect(center=(self.current_width//2, self.current_height//2))
        self.screen.blit(big_font.render(message, True, (255,255,0)), text_rect)
        pygame.display.flip()
        pygame.time.wait(2000)

        if self.return_to_overworld:
            if "You defeated" in message:
                self.combat_result = 'player_win'
            else:
                self.combat_result = 'enemy_win'
            self.running = False
        else:
            pygame.quit()
            sys.exit()

    def _deprecated_process_turn_start_effects(self, character):
        """DEPRECATED: older implementation kept for reference; not used. Use the later process_turn_start_effects."""
        char_name = getattr(character, 'name', 'Unknown')
        print(f"Processing turn-start effects for {char_name}")
        
        # Check for STUN on all body parts
        for part in character.body_parts:
            if not hasattr(part, 'p_eff'):
                continue
            
            effetti = part.p_eff
            if hasattr(effetti, 'stun'):
                stun_data = getattr(effetti, 'stun')
                # stun_data is [name, level, duration, immunity]
                if stun_data[1] > 0 and stun_data[2] > 0: # if stun is active
                    stun_level = stun_data[1]
                    stamina_reduction = 10 * stun_level # Example: 10 stamina per stun level
                    
                    old_stamina = character.sta
                    character.sta = max(0, character.sta - stamina_reduction)
                    actual_reduction = old_stamina - character.sta
                    
                    if actual_reduction > 0:
                        message = f"{char_name}'s STUN on {part.name} reduced stamina by {actual_reduction}!"
                        print(message)
                        self.add_log_entry(message, "effect", (255, 100, 255))

    def nerf_status_effects_on_part(self, part):
        """Reduce all status effects on a body part by 1 level and 1 duration (minimum 0). If duration reaches 0, also reset level to 0."""
        if not hasattr(part, 'p_eff'):
            return
        effetti = part.p_eff
        
        from Status_Effects_Config import should_effect_heal_on_regen, STATUS_EFFECTS_CONFIG
        
        # Use all status effects from the config instead of hardcoded list
        status_effects = list(STATUS_EFFECTS_CONFIG.keys())
        
        for status_name in status_effects:
            if hasattr(effetti, status_name):
                effect_data = getattr(effetti, status_name)
                
                # Skip mess_up - it has special handling and should not be reduced here
                if status_name == 'mess_up':
                    print(f"  Regeneration skipped {status_name} on {part.name} (special handling)")
                    continue
                
                # Check if this effect should be healed during regeneration
                if should_effect_heal_on_regen(status_name):
                    # effect_data: [name, level, duration, immunity]
                    # Reduce level and duration by 1, minimum 0
                    new_level = max(0, effect_data[1] - 1)
                    new_duration = max(0, effect_data[2] - 1)
                    # If duration reaches 0, reset level to 0
                    if new_duration == 0:
                        new_level = 0
                    # Update effect_data
                    effect_data[1] = new_level
                    effect_data[2] = new_duration
                    setattr(effetti, status_name, effect_data)
                    print(f"  Regeneration reduced {status_name} on {part.name}")
                else:
                    # Effect is not healed by regeneration (like sleep, acid)
                    print(f"  Regeneration skipped {status_name} on {part.name} (not healed by regen)")
        # No return needed

    def __init__(self, player_stats=None, enemy_npc=None, return_to_overworld=False):
        global battle_menu_instance
        battle_menu_instance = self
        # Handle pygame display initialization based on context
        if return_to_overworld:
            # When called from overworld, reuse existing display
            existing_surface = pygame.display.get_surface()
            if existing_surface is not None:
                self.screen = existing_surface
                print("Battle system reusing existing pygame display from overworld")
            else:
                # Fallback: create new display if none exists
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                pygame.display.set_caption("RPG FIGHTING SYSTEM")
                print("Battle system created new display (no existing display found)")
        else:
            # Standalone mode: create new display
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            pygame.display.set_caption("RPG FIGHTING SYSTEM")
            
        self.clock = pygame.time.Clock()
        
        # Initialize joystick support
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller detected: {self.joystick.get_name()}")
        else:
            print("No controller detected - keyboard only")
        
        # Font path needs to go up to the main project directory
        font_path = Path(__file__).parent.parent.parent.parent / "Pixellari.ttf"
        # Store base font sizes (design-space) and create initial fonts
        self._font_path = font_path
        self._base_font_sizes = {
            'big': 28,      # normal size
            'large': 24,    # normal size
            'medium': 20,   # normal size
            'small': 16     # normal size
        }
        # Create EQUIP menu fonts (increased by 10% from previous 40% reduction)
        self._equip_font_sizes = {
            'big': 37,      # 34 * 1.1 = 37.4 ≈ 37
            'large': 32,    # 29 * 1.1 = 31.9 ≈ 32
            'medium': 26,   # 24 * 1.1 = 26.4 ≈ 26
            'small': 21     # 19 * 1.1 = 20.9 ≈ 21
        }
        self.font_big = pygame.font.Font(str(font_path), self._base_font_sizes['big'])
        self.font_large = pygame.font.Font(str(font_path), self._base_font_sizes['large'])
        self.font_medium = pygame.font.Font(str(font_path), self._base_font_sizes['medium'])
        self.font_small = pygame.font.Font(str(font_path), self._base_font_sizes['small'])
        
        # Create doubled fonts for EQUIP menu
        self.equip_font_big = pygame.font.Font(str(font_path), self._equip_font_sizes['big'])
        self.equip_font_large = pygame.font.Font(str(font_path), self._equip_font_sizes['large'])
        self.equip_font_medium = pygame.font.Font(str(font_path), self._equip_font_sizes['medium'])
        self.equip_font_small = pygame.font.Font(str(font_path), self._equip_font_sizes['small'])

        # Track current window size
        self.current_width, self.current_height = self.screen.get_size()
        
        # Load and apply volume settings from game configuration
        if return_to_overworld:
            # When called from overworld, apply volume settings
            try:
                music_volume, sfx_volume = load_and_apply_volume_settings()
                print(f"[Combat] Volume settings applied - Music: {music_volume}, SFX: {sfx_volume}")
            except Exception as e:
                print(f"[Combat] Failed to apply volume settings: {e}")
        else:
            print("[Combat] Standalone mode - using default volume settings")
        self.ref_width = REF_WIDTH
        self.ref_height = REF_HEIGHT

        # Integration with overworld
        self.return_to_overworld = return_to_overworld
        self.combat_result = None  # Will be 'player_win', 'enemy_win', or None
        self.original_player_stats = player_stats  # Store reference to overworld player stats
        self.enemy_npc = enemy_npc  # Store reference to enemy NPC

        # Base (design reference) positions/sizes for elements to be scaled
        # Event log (from original fixed coordinates at 1600x1000)
        self.base_log_x = SCREEN_WIDTH // 2 + 300  # 1100
        self.base_log_y = SCREEN_HEIGHT - 480      # 480
        self.base_log_width = SCREEN_WIDTH // 2 - 175  # 625
        self.base_log_height = 460

        # UI state
        self.menu_selection_index = 0
        self.enemy_parts_index = 0
        self.moves_selection_index = 0
        self.running = True
        self.player_has_control = True
        self.regeneration_mode_active = False
        self.player_turn_start_active = False  # For showing player turn start indicator

        # Initialize regeneration system attributes
        self.regeneration_selection_index = 0
        self.in_regeneration_navigation = False

        # Initialize ability system attributes
        self.ability_selection_index = 0
        self.pass_selection = 0

        # Initialize blink states
        self.player_blink_state = {'active': False}
        self.enemy_blink_state = {'active': False}
        
        # Add enemy turn state
        self.enemy_turn_active = False
        self.auto_start_enemy_turn = False

        # Victory sequence state
        self.victory = {
            'active': False,
            'winner': None,
            'phase': None,
            'phase_end': 0,
            'blink_started': False,
            'fade_start': 0,
            'fade_duration': 300,
            'alpha': 255,
            'message_shown': False
        }

        # Control to pause only enemy animation frames (for freeze)
        self.enemy_animation_paused_until = 0

        # Menu items
        self.menu_labels = ["ENEMY", "MOVES", "EQUIP", "ABILITIES", "ITEMS", "PASS"]
        
        # Equipment panel variables
        self.equipment_selection_index = 0
        self.equipment_scroll_offset = 0

        # GIF animation variables
        self.player_frames = []
        self.enemy_frames = []
        self.player_frame_index = 0
        self.enemy_frame_index = 0
        self.frame_duration = 100  # Default duration in milliseconds
        self.last_frame_time = 0

        # Load images and GIFs
        self.load_images()

        # EVENT LOG SYSTEM - REPLACING MESSAGE SYSTEM (scaled layout)
        self.event_log = []  # List to store all log entries
        self.log_scroll_offset = 0  # Current scroll position
        self.max_log_entries = 100  # Maximum entries to keep in memory
        self.log_visible_lines = 8  # How many lines are visible at once
        # Runtime (scaled) log geometry will be computed in _recompute_layout()
        self.log_x = self.base_log_x
        self.log_y = self.base_log_y
        self.log_width = self.base_log_width
        self.log_height = self.base_log_height
        
        # Periodic log update timer
        self.last_log_update = 0
        
        # Initialize target selection state
        self.target_selection_active = False
        self.target_selection_index = 0
        self.selected_move = None
        
        # Initialize move execution lock to prevent multiple executions during animations
        self.move_execution_locked = False

        # Initialize Enemy AI system (will be set up after character loading)
        self.enemy_ai = None

        # Perform initial layout & font scaling pass
        self._recompute_layout()

    def is_controller_connected(self):
        """Check if a controller is connected and working"""
        return self.joystick is not None and self.joystick.get_init()
    
    def check_controller_input(self, event):
        """
        Check for controller input and return equivalent keyboard event type
        Returns: tuple (event_type, key_equivalent) or None if no match
        """
        if not self.is_controller_connected():
            return None
            
        # Handle joystick button events
        if event.type == pygame.JOYBUTTONDOWN:
            # PlayStation controller mapping (common values)
            if event.button == 0:  # X button
                return ('keydown', pygame.K_SPACE)
            elif event.button == 1:  # Circle button  
                return ('keydown', pygame.K_ESCAPE)
            elif event.button == 5:  # R1 button
                return ('keydown', pygame.K_r)
            elif event.button == 3:  # Triangle button
                return ('keydown', pygame.K_p)
                
        # Handle D-pad events
        elif event.type == pygame.JOYHATMOTION:
            if event.value == (0, 1):  # Up
                return ('keydown', pygame.K_UP)
            elif event.value == (0, -1):  # Down
                return ('keydown', pygame.K_DOWN)
            elif event.value == (-1, 0):  # Left
                return ('keydown', pygame.K_LEFT)
            elif event.value == (1, 0):  # Right
                return ('keydown', pygame.K_RIGHT)
                
        # Handle analog stick events (left stick) with deadzone and debouncing
        elif event.type == pygame.JOYAXISMOTION:
            # Initialize analog stick state tracking if not exists
            if not hasattr(self, '_analog_stick_state'):
                self._analog_stick_state = {'x_triggered': False, 'y_triggered': False}
            
            deadzone = 0.6  # Require stronger input to register
            
            # Left stick X-axis (axis 0)
            if event.axis == 0:
                if event.value < -deadzone and not self._analog_stick_state['x_triggered']:  # Left
                    self._analog_stick_state['x_triggered'] = True
                    return ('keydown', pygame.K_LEFT)
                elif event.value > deadzone and not self._analog_stick_state['x_triggered']:  # Right
                    self._analog_stick_state['x_triggered'] = True
                    return ('keydown', pygame.K_RIGHT)
                elif abs(event.value) < 0.3:  # Reset when stick returns to center
                    self._analog_stick_state['x_triggered'] = False
                    
            # Left stick Y-axis (axis 1) 
            elif event.axis == 1:
                if event.value < -deadzone and not self._analog_stick_state['y_triggered']:  # Up (negative is up in pygame)
                    self._analog_stick_state['y_triggered'] = True
                    return ('keydown', pygame.K_UP)
                elif event.value > deadzone and not self._analog_stick_state['y_triggered']:  # Down
                    self._analog_stick_state['y_triggered'] = True
                    return ('keydown', pygame.K_DOWN)
                elif abs(event.value) < 0.3:  # Reset when stick returns to center
                    self._analog_stick_state['y_triggered'] = False
        
        return None
    
    def process_controller_input(self, event):
        """
        Process controller input and execute the equivalent keyboard action
        Returns True if controller input was handled, False otherwise
        """
        controller_input = self.check_controller_input(event)
        if controller_input is None:
            return False
            
        event_type, key_equivalent = controller_input
        
        # Create a fake keyboard event to reuse existing keyboard logic
        if event_type == 'keydown':
            fake_event = type('obj', (object,), {
                'type': pygame.KEYDOWN,
                'key': key_equivalent
            })
            
            # Process the fake keyboard event using existing logic
            return self.process_keyboard_input(fake_event)
        
        return False

    def process_keyboard_input(self, event):
        """
        Extract keyboard processing logic to be reusable for both keyboard and controller
        Returns True if input was handled, False otherwise
        """
        # Handle debug keys first
        if event.key == pygame.K_F1:
            self.debug_stamina_info()
            return True
        elif event.key == pygame.K_F2:
            player.sta = max(0, player.sta - 2)
            pygame.display.flip()
            return True
        elif event.key == pygame.K_F3:
            self.restore_stamina(player, 2)
            return True
        elif event.key == pygame.K_F4:  # Clear log hotkey
            self.clear_log()
            return True
        
        # NEW: Keyboard log scrolling controls
        elif event.key == pygame.K_z:  # Scroll log UP
            self.scroll_log(-2)  # Negative value scrolls up
            return True
        elif event.key == pygame.K_x:  # Scroll log DOWN
            self.scroll_log(2)   # Positive value scrolls down
            return True
        
        # Don't allow most navigation during enemy turn
        if not self.player_has_control:
            if event.key == pygame.K_r:
                self.add_log_entry("Cannot use regeneration during enemy turn", "warning")
            return True
        
        # PASS shortcut - P key or Triangle to go directly to PASS menu
        if event.key == pygame.K_p:
            self.menu_selection_index = 5  # PASS menu is index 5
            return True
        
        # TARGET SELECTION has HIGHEST PRIORITY
        if hasattr(self, 'target_selection_active') and self.target_selection_active:
            if event.key in [pygame.K_UP, pygame.K_w]:
                old_index = getattr(self, 'target_selection_index', 0)
                new_index = self.find_next_valid_target(old_index - 1, -1)
                self.target_selection_index = new_index
                return True
                
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                old_index = getattr(self, 'target_selection_index', 0)
                new_index = self.find_next_valid_target(old_index + 1, 1)
                self.target_selection_index = new_index
                return True
                
            elif event.key == pygame.K_SPACE:
                # Check if move execution is locked (prevents multiple executions during animations)
                if getattr(self, 'move_execution_locked', False):
                    print("DEBUG: SPACE pressed but move execution is locked - ignoring input")
                    return True
                    
                # Double-check target validity before execution
                target_part = enemy.body_parts[self.target_selection_index]
                if self.is_valid_target_for_move(self.selected_move, target_part):
                    self.execute_selected_move()
                else:
                    self.show_error_message("Target non valido per questa mossa!", 2000)
                return True
                
            elif event.key == pygame.K_ESCAPE:
                self.cancel_target_selection()
                return True
        
        # Regeneration mode navigation
        elif hasattr(self, 'regeneration_mode_active') and self.regeneration_mode_active:
            if event.key in [pygame.K_UP, pygame.K_w]:
                self.regeneration_selection_index = (self.regeneration_selection_index - 1) % len(player.body_parts)
                return True
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.regeneration_selection_index = (self.regeneration_selection_index + 1) % len(player.body_parts)
                return True
            elif event.key == pygame.K_SPACE:
                success = self.regenerate_body_part_pygame(player, self.regeneration_selection_index)
                return True
            elif event.key == pygame.K_r or event.key == pygame.K_ESCAPE:
                self.toggle_regeneration_mode()
                return True
        
        # Normal navigation
        else:
            if event.key in [pygame.K_LEFT, pygame.K_a]:
                self.menu_selection_index = (self.menu_selection_index - 1) % len(self.menu_labels)
                return True
            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                self.menu_selection_index = (self.menu_selection_index + 1) % len(self.menu_labels)
                return True           
            elif event.key in [pygame.K_UP, pygame.K_w]:
                if self.menu_selection_index == 0:  # ENEMY menu
                    self.enemy_parts_index = (self.enemy_parts_index - 1) % len(enemy.body_parts)
                elif self.menu_selection_index == 1:  # MOVES menu
                    if hasattr(player, 'moves') and player.moves:
                        self.moves_selection_index = (self.moves_selection_index - 1) % len(player.moves)
                elif self.menu_selection_index == 2:  # EQUIP menu
                    try:
                        import Player_Equipment
                        player_equip = Player_Equipment.player1
                        if player_equip:
                            weapons = [item for item in player_equip.equip if hasattr(item, 'type') and item.type == 'weapon']
                            if weapons:
                                self.equipment_selection_index = (self.equipment_selection_index - 1) % len(weapons)
                    except:
                        pass
                elif self.menu_selection_index == 3:  # ABILITIES menu
                    if hasattr(player, 'ability') and player.ability:
                        self.ability_selection_index = (getattr(self, 'ability_selection_index', 0) - 1) % len(player.ability)
                        ability = player.ability[self.ability_selection_index]
                elif self.menu_selection_index == 5:  # PASS menu
                    self.pass_selection = (getattr(self, 'pass_selection', 0) - 1) % 2
                    pass_options = ["YES", "NO"]
                return True
            
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                if self.menu_selection_index == 0:  # ENEMY menu
                    self.enemy_parts_index = (self.enemy_parts_index + 1) % len(enemy.body_parts)
                elif self.menu_selection_index == 1:  # MOVES menu
                    if hasattr(player, 'moves') and player.moves:
                        self.moves_selection_index = (self.moves_selection_index + 1) % len(player.moves)
                elif self.menu_selection_index == 2:  # EQUIP menu
                    try:
                        import Player_Equipment
                        player_equip = Player_Equipment.player1
                        if player_equip:
                            weapons = [item for item in player_equip.equip if hasattr(item, 'type') and item.type == 'weapon']
                            if weapons:
                                self.equipment_selection_index = (self.equipment_selection_index + 1) % len(weapons)
                    except:
                        pass
                elif self.menu_selection_index == 3:  # ABILITIES menu
                    if hasattr(player, 'ability') and player.ability:
                        self.ability_selection_index = (getattr(self, 'ability_selection_index', 0) + 1) % len(player.ability)
                        ability = player.ability[self.ability_selection_index]
                        self.add_log_entry(f"Ability: {ability.name}", "info")
                elif self.menu_selection_index == 5:  # PASS menu
                    self.pass_selection = (getattr(self, 'pass_selection', 0) + 1) % 2
                    pass_options = ["YES", "NO"]
                    self.add_log_entry(f"Pass turn: {pass_options[self.pass_selection]}", "system")
                return True
            
            elif event.key == pygame.K_SPACE:
                if self.menu_selection_index == 1:  # Use move
                    self.use_selected_move()
                elif self.menu_selection_index == 2:  # EQUIP menu - weapon swapping
                    self.handle_weapon_selection()
                elif self.menu_selection_index == 3:  # Show ability details
                    self.show_ability_details_pygame()
                elif self.menu_selection_index == 5:  # PASS menu
                    if getattr(self, 'pass_selection', 0) == 0:  # YES selected
                        # End player turn (which will process turn-end effects)
                        self.start_enemy_turn()
                return True
            
            elif event.key == pygame.K_r:  # Toggle regeneration
                self.toggle_regeneration_mode()
                return True
            
            elif event.key == pygame.K_ESCAPE:
                if hasattr(self, 'target_selection_active') and self.target_selection_active:
                    self.cancel_target_selection()
                elif hasattr(self, 'regeneration_mode_active') and self.regeneration_mode_active:
                    self.toggle_regeneration_mode()
                return True
        
        return False

    def initialize_enemy_ai(self):
        """Initialize the Enemy AI system after characters are loaded"""
        global player, enemy
        
        if ENEMY_AI_AVAILABLE:
            try:
                # Initialize AI based on which version is available
                if AI_VERSION == 'V3':
                    # V3 has simpler initialization (no configuration parameters)
                    self.enemy_ai = create_enemy_ai_v3(enemy, player, self)
                    print("Enemy AI V3 system initialized successfully")
                    self.add_log_entry("AI V3 system activated (simple decision tree)", "info")
                elif AI_VERSION == 'V2':
                    # Fallback to V2 with configuration parameters
                    self.enemy_ai = create_enemy_ai_v2(
                        enemy, player, 
                        debug_mode=True,
                        stamina_regen_cost=stamina_cost_per_regeneration,
                        dodge_shield_cost=DodgeShield_Stamina_Cost,
                        rig_regen_cost=rig_cost_per_regeneration
                    )
                    print("Enemy AI V2 system initialized successfully (fallback)")
                    self.add_log_entry("AI V2 system activated (fallback)", "info")
                else:
                    raise Exception("No valid AI version available")
            except Exception as e:
                print(f"Warning: Could not initialize Enemy AI: {e}")
                self.add_log_entry(f"AI initialization failed: {e}", "warning")
                self.enemy_ai = None
        else:
            print("Enemy AI not available")
            self.enemy_ai = None

    def initialize_speed_based_turns(self):
        """Initialize speed-based turn system using global function"""
        initialize_speed_based_turns()

    def get_current_character(self):
        """Get current character from turn queue using global function"""
        return get_current_character()

    def advance_turn_queue(self):
        """Advance turn queue using global function"""
        return advance_turn_queue()

    def get_turn_order_message(self):
        """Get turn order message using global function"""
        return get_turn_order_message()

    def start_first_enemy_turn(self):
        """Start enemy turn at the very beginning of battle (when enemy is faster)"""
        print(f"🤖 STARTING FIRST ENEMY TURN")
        
        # Show initial battle messages
        self.add_log_entry("TURN 0", "combat", (255, 255, 100))
        first_turn_message = self.get_turn_order_message()
        if first_turn_message:
            self.add_log_entry(first_turn_message, "combat", (100, 255, 255))
        
        # Set enemy turn state (already set in run(), but make sure)
        self.enemy_turn_active = True
        self.player_has_control = False
        self.menu_selection_index = 0
        
        # Restore enemy stamina at beginning of enemy turn (BEFORE effect processing)
        old_enemy_stamina = enemy.sta
        enemy.sta = enemy.max_sta
        stamina_restored = enemy.sta - old_enemy_stamina
        
        if stamina_restored > 0:
            self.add_log_entry(f"{enemy.name} stamina restored: +{stamina_restored}", "success")
            print(f"⚡ ENEMY STAMINA RESTORED: {enemy.name} {old_enemy_stamina} -> {enemy.sta} (+{stamina_restored})")
        
        # Process turn-start effects for ENEMY ONLY
        process_turn_start_effects(enemy)
        
        # Refill enemy RIG with RES
        rig_restored, res_consumed, refill_message = refill_enemy_rig_with_res()
        if rig_restored > 0:
            self.add_log_entry(f"{enemy.name}: {refill_message}", "info")
        
        # Debug: Check enemy resources before AI actions
        print(f"DEBUG: Enemy resources after turn start - RIG: {enemy.rig}/{enemy.max_rig}, RES: {enemy.res}/{enemy.max_res}, STA: {enemy.sta}/{enemy.max_sta}")
        
        # Start enemy AI actions
        pygame.time.set_timer(pygame.USEREVENT + 2, 1500)

    def check_and_show_new_round_messages(self):
        """Check if a new round started and show appropriate messages"""
        global first_turn_of_round, current_round, current_turn_index
        
        # Check if we're at the start of a new round
        if first_turn_of_round:
            
            # Show TURN X message for all rounds (including round 0 if this is the very first time)
            if current_round == 0:
                # Only show TURN 0 at the very beginning of combat
                if not hasattr(self, '_turn_0_shown'):
                    self.add_log_entry(f"TURN {current_round}", "combat", (255, 255, 100))
                    self._turn_0_shown = True
            else:
                # Always show TURN X for rounds > 0
                self.add_log_entry(f"TURN {current_round}", "combat", (255, 255, 100))
            
            # Reset the flag after checking
            first_turn_of_round = False

    # ---------------------- SCALING HELPERS & LAYOUT ----------------------
    def sx(self, x):
        """Scale an x-dimension from design space to current window width."""
        return int(x * self.current_width / self.ref_width)

    def sy(self, y):
        """Scale a y-dimension from design space to current window height."""
        return int(y * self.current_height / self.ref_height)

    def _scale_fonts(self):
        """Recreate fonts proportionally to current window height with clamping."""
        scale = self.current_height / self.ref_height
        clamp = lambda v: max(10, min(96, int(v * scale)))
        # Normal fonts
        self.font_big = pygame.font.Font(str(self._font_path), clamp(self._base_font_sizes['big']))
        self.font_large = pygame.font.Font(str(self._font_path), clamp(self._base_font_sizes['large']))
        self.font_medium = pygame.font.Font(str(self._font_path), clamp(self._base_font_sizes['medium']))
        self.font_small = pygame.font.Font(str(self._font_path), clamp(self._base_font_sizes['small']))
        # EQUIP menu fonts (doubled)
        self.equip_font_big = pygame.font.Font(str(self._font_path), clamp(self._equip_font_sizes['big']))
        self.equip_font_large = pygame.font.Font(str(self._font_path), clamp(self._equip_font_sizes['large']))
        self.equip_font_medium = pygame.font.Font(str(self._font_path), clamp(self._equip_font_sizes['medium']))
        self.equip_font_small = pygame.font.Font(str(self._font_path), clamp(self._equip_font_sizes['small']))

    def _recompute_layout(self):
        """Recalculate all geometry dependent on window size."""
        # Update current size
        self.current_width, self.current_height = self.screen.get_size()

        # Calculate EVENT LOG coordinates relative to enemy body parts layout
        # Get the same coordinates as used in enemy panel and detail box
        panel_x = self.sx(310)  # Main panel x
        panel_width = self.sx(760)  # Main panel width
        parts_x = panel_x + panel_width + self.sx(20)  # Body parts list x (where text starts)
        parts_bg_width = self.sx(180)  # Body parts background width
        detail_panel_x = parts_x + parts_bg_width + self.sx(20)  # Detail box x
        detail_panel_width = self.sx(275)  # Detail box width
        detail_panel_end_x = detail_panel_x + detail_panel_width  # Where detail box ends
        
        # Set log coordinates: from body parts text start to detail box end
        # Keep original positioning since buff matrix and stamina bar now share the space above it properly
        self.log_x = parts_x
        self.log_y = self.sy(self.base_log_y)  # Keep original Y positioning
        self.log_width = detail_panel_end_x - parts_x  # Span from parts start to detail end
        self.log_height = max(120, self.sy(self.base_log_height))  # Restore original height calculation

        # Update fonts after size change
        self._scale_fonts()

        # Ensure log scrolls to bottom after layout change
        self.scroll_log_to_bottom()

        # (Future) Add other panel geometry scaling here
        # Placeholder attributes for future proportional panels can be added safely
        # print(f"DEBUG: Layout recomputed -> size=({self.current_width},{self.current_height}) log=({self.log_x},{self.log_y},{self.log_width},{self.log_height})")

    def add_log_entry(self, message, log_type="info", color=None):
        """
        Add an entry to the event log (FILTERED - only combat-relevant events)
        
        Args:
            message (str): The message to log
            log_type (str): Type of log entry ('info', 'error', 'success', 'warning', 'combat')
            color (tuple): Custom color override (R, G, B)
        """
        import time
        
        # FILTER: Only log combat-relevant events
        allowed_log_types = {
            'combat',      # Player/enemy moves and damage
            'regeneration', # Regeneration actions
            'damage',      # Damage dealt
            'effect',      # Status effects applied
            'evasion'      # Dodge/Shield evasion events
            # 'turn' removed - no turn start/end logging
        }
        
        # Skip logging if not a combat-relevant type
        if log_type not in allowed_log_types:
            return
        
        # Define colors for different log types
        type_colors = {
            'combat': (255, 255, 100),      # Yellow
            'regeneration': (0, 255, 200),  # Cyan
            'damage': (255, 100, 100),      # Light red
            'effect': (255, 150, 255),      # Light purple
            'evasion': (100, 255, 100)      # Green for dodge/shield evasion
        }
        
        # Use custom color or default for type
        entry_color = color if color else type_colors.get(log_type, (255, 255, 255))
        
        # Create log entry (no timestamp)
        log_entry = {
            'message': message,
            'type': log_type,
            'color': entry_color
        }
        
        # Add to log
        self.event_log.append(log_entry)
        
        # Trim log if it gets too long
        if len(self.event_log) > self.max_log_entries:
            self.event_log = self.event_log[-self.max_log_entries:]
        
        # Auto-scroll to bottom for new entries (but don't force immediate redraw)
        self.scroll_log_to_bottom()

        print(f"LOG [{log_type.upper()}]: {message}")

    def scroll_log_to_bottom(self):
        """Scroll the log to show the most recent entries"""
        if not self.event_log:
            self.log_scroll_offset = 0
            return
            
        # Ensure log_visible_lines is set (in case called before draw_event_log)
        if not hasattr(self, 'log_visible_lines') or self.log_visible_lines is None:
            # Calculate based on current log dimensions
            text_area_height = self.log_height - 75  # Account for title and margins
            line_height = 20
            self.log_visible_lines = max(1, (text_area_height - 10) // line_height)
        
        # Calculate total wrapped lines
        total_wrapped_lines = 0
        available_text_width = self.log_width - 35  # Account for margins and scrollbar
        
        for entry in self.event_log:
            wrapped_lines = self.wrap_text(entry['message'], self.font_medium, available_text_width)
            total_wrapped_lines += len(wrapped_lines)
        
        # Set scroll offset to show the most recent lines
        if total_wrapped_lines > self.log_visible_lines:
            self.log_scroll_offset = total_wrapped_lines - self.log_visible_lines
        else:
            self.log_scroll_offset = 0

    def scroll_log(self, direction):
        """
        Scroll the log up or down
        
        Args:
            direction (int): Positive to scroll down, negative to scroll up
        """
        if not self.event_log:
            return
            
        # Calculate total wrapped lines
        total_wrapped_lines = 0
        available_text_width = self.log_width - 35  # Account for margins and scrollbar
        
        for entry in self.event_log:
            wrapped_lines = self.wrap_text(entry['message'], self.font_medium, available_text_width)
            total_wrapped_lines += len(wrapped_lines)
        
        # Calculate max scroll based on wrapped lines
        max_scroll = max(0, total_wrapped_lines - self.log_visible_lines)
        
        self.log_scroll_offset = max(0, min(max_scroll, self.log_scroll_offset + direction))

    def handle_log_scroll(self, event):
        """Handle mouse wheel scrolling for the log"""
        if event.type == pygame.MOUSEWHEEL:
            # Check if mouse is over the log area
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            if (self.log_x <= mouse_x <= self.log_x + self.log_width and
                self.log_y <= mouse_y <= self.log_y + self.log_height):
                
                # Scroll the log (negative y means scroll up, positive means scroll down)
                self.scroll_log(-event.y * 2)  # Multiply by 2 for faster scrolling
                return True
        return False

    def draw_event_log(self):
        """Draw the event log window"""
        # Draw log background
        pygame.draw.rect(self.screen, BLACK, (self.log_x, self.log_y, self.log_width, self.log_height))
        pygame.draw.rect(self.screen, WHITE, (self.log_x, self.log_y, self.log_width, self.log_height), 2)
        
        offset = 15  # Reduced offset for title and separator to make more room
        # Draw log title
        title_y = self.log_y + offset
        self.draw_text("EVENT LOG", self.font_medium, WHITE, self.log_x + self.log_width // 2, title_y, center=True)  # Changed back to font_medium and reduced spacing
        
        # Draw separator line
        separator_y = title_y + 18  # Reduced spacing after title
        pygame.draw.line(self.screen, WHITE, 
                        (self.log_x + 10, separator_y), 
                        (self.log_x + self.log_width - 10, separator_y), 1)
        
        # Calculate text area more precisely
        text_start_y = separator_y + 8  # Reduced spacing after separator
        text_area_height = self.log_height - (text_start_y - self.log_y) - 15  # Reduced bottom margin
        line_height = 20
        
        # Text wrapping parameters - use almost full width with margins
        left_margin = 10
        right_margin = 10
        available_text_width = self.log_width - left_margin - right_margin - 15  # Extra space for scrollbar
        
        # Calculate how many lines we can show (be more conservative)
        max_visible_lines = max(1, (text_area_height - 10) // line_height)  # Extra safety margin
        self.log_visible_lines = max_visible_lines
        
        # Calculate total wrapped lines for all entries
        total_wrapped_lines = 0
        entry_line_counts = []
        
        for entry in self.event_log:
            wrapped_lines = self.wrap_text(entry['message'], self.font_medium, available_text_width)
            line_count = len(wrapped_lines)
            entry_line_counts.append(line_count)
            total_wrapped_lines += line_count
        
        # Ensure scroll offset is within valid bounds
        max_scroll = max(0, total_wrapped_lines - max_visible_lines)
        self.log_scroll_offset = max(0, min(self.log_scroll_offset, max_scroll))
        
        # Draw log entries
        if self.event_log:
            current_display_line = 0
            lines_skipped = 0
            
            for entry_idx, entry in enumerate(self.event_log):
                if current_display_line >= max_visible_lines:
                    break
                    
                # Get wrapped lines for this entry
                wrapped_lines = self.wrap_text(entry['message'], self.font_medium, available_text_width)
                
                # Skip lines based on scroll offset
                for line_idx, line in enumerate(wrapped_lines):
                    if lines_skipped < self.log_scroll_offset:
                        lines_skipped += 1
                        continue
                        
                    if current_display_line >= max_visible_lines:
                        break
                        
                    # Calculate Y position for this line
                    line_y = text_start_y + current_display_line * line_height
                    
                    # Make sure we don't draw outside the log area
                    if line_y + line_height > self.log_y + self.log_height - 10:
                        break
                        
                    # Indent continuation lines (lines after the first one)
                    indent = 0 if line_idx == 0 else 20
                    
                    self.draw_text(line, self.font_medium, entry['color'],
                                self.log_x + left_margin + indent, line_y)
                    
                    current_display_line += 1
        else:
            # No log entries
            no_entries_y = text_start_y + 20
            self.draw_text("No events logged yet", self.font_medium, GRAY,
                        self.log_x + self.log_width // 2, no_entries_y, center=True)
        
        # Draw scrollbar if needed
        if total_wrapped_lines > max_visible_lines:
            self.draw_log_scrollbar(total_wrapped_lines, max_visible_lines)

    def wrap_text(self, text, font, max_width):
        """
        Wrap text to fit within the specified width
        
        Args:
            text (str): Text to wrap
            font: Pygame font object
            max_width (int): Maximum width in pixels
        
        Returns:
            list: List of wrapped lines
        """
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            # Test if adding this word would exceed the width
            test_line = current_line + word + " " if current_line else word + " "
            test_surface = font.render(test_line.strip(), True, WHITE)
            
            if test_surface.get_width() <= max_width:
                # Word fits, add it to current line
                current_line = test_line
            else:
                # Word doesn't fit
                if current_line:
                    # Save current line and start new one with this word
                    lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    # Single word is too long, we need to break it
                    # For now, just add it as is (you could implement character-level breaking here)
                    lines.append(word)
                    current_line = ""
        
        # Add the last line if there's content
        if current_line.strip():
            lines.append(current_line.strip())
        
        return lines if lines else [""]
    
    def draw_log_scrollbar(self, total_wrapped_lines, visible_lines):
        """Draw a scrollbar for the log based on wrapped lines"""
        scrollbar_x = self.log_x + self.log_width - 15
        scrollbar_y = self.log_y + 65  # Start below title
        scrollbar_width = 10
        scrollbar_height = self.log_height - 75  # Leave space for title
        
        # Draw scrollbar background
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
        
        # Calculate scrollbar thumb size and position based on wrapped lines
        if total_wrapped_lines > visible_lines:
            thumb_height = max(20, int(scrollbar_height * (visible_lines / total_wrapped_lines)))
            max_thumb_y = scrollbar_height - thumb_height
            thumb_y = scrollbar_y + int(max_thumb_y * (self.log_scroll_offset / (total_wrapped_lines - visible_lines)))
            
            # Draw scrollbar thumb
            pygame.draw.rect(self.screen, WHITE, 
                            (scrollbar_x + 1, thumb_y, scrollbar_width - 2, thumb_height))

    def clear_log(self):
        """Clear all log entries"""
        self.event_log.clear()
        self.log_scroll_offset = 0
        self.add_log_entry("Event log cleared", "system")

    def blink_character_gif(self, character_type, blink_color=(255, 0, 0), blink_duration=300, blink_count=3):
        """
        Make a character's GIF blink by setting a blink state that will be handled during rendering
        
        Args:
            character_type (str): "player" or "enemy" to specify which character
            blink_color (tuple): RGB color of the blink overlay (default red)
            blink_duration (int): Duration of each blink in milliseconds
            blink_count (int): Number of blinks
        """
        current_time = pygame.time.get_ticks()
        
        if character_type.lower() == "player":
            self.player_blink_state = {
                'active': True,
                'color': blink_color,
                'duration': blink_duration,
                'count': blink_count,
                'current_blink': 0,
                'start_time': current_time,
                'visible': True  # Whether overlay is currently visible
            }
            print(f"Started player blink: {blink_count} blinks, {blink_duration}ms each")
        
        elif character_type.lower() == "enemy":
            self.enemy_blink_state = {
                'active': True,
                'color': blink_color,
                'duration': blink_duration,
                'count': blink_count,
                'current_blink': 0,
                'start_time': current_time,
                'visible': True  # Whether overlay is currently visible
            }
            print(f"Started enemy blink: {blink_count} blinks, {blink_duration}ms each")
        
        else:
            print(f"Warning: Unknown character type '{character_type}' for blinking")

    def update_blink_states(self):
        """Update blink states for all characters - call this in your main update loop"""
        current_time = pygame.time.get_ticks()
        
        # Update player blink state
        if hasattr(self, 'player_blink_state') and self.player_blink_state['active']:
            blink_state = self.player_blink_state
            elapsed = current_time - blink_state['start_time']
            half_duration = blink_state['duration'] // 2
            full_duration = blink_state['duration']
            
            # Calculate which blink we're on and whether overlay should be visible
            current_blink = elapsed // full_duration
            blink_progress = elapsed % full_duration
            
            if current_blink < blink_state['count']:
                # Still blinking
                blink_state['visible'] = blink_progress < half_duration
                blink_state['current_blink'] = current_blink
            else:
                # Blinking complete
                blink_state['active'] = False
                blink_state['visible'] = False
                print("Player blink sequence completed")
        
        # Update enemy blink state
        if hasattr(self, 'enemy_blink_state') and self.enemy_blink_state['active']:
            blink_state = self.enemy_blink_state
            elapsed = current_time - blink_state['start_time']
            half_duration = blink_state['duration'] // 2
            full_duration = blink_state['duration']
            
            # Calculate which blink we're on and whether overlay should be visible
            current_blink = elapsed // full_duration
            blink_progress = elapsed % full_duration
            
            if current_blink < blink_state['count']:
                # Still blinking
                blink_state['visible'] = blink_progress < half_duration
                blink_state['current_blink'] = current_blink
            else:
                # Blinking complete
                blink_state['active'] = False
                blink_state['visible'] = False
                print("Enemy blink sequence completed")

    def draw_blink_overlay(self, surface, x, y, width, height, color, alpha=128):
        """Draw a blink overlay on the specified surface area"""
        overlay = pygame.Surface((width, height))
        overlay.set_alpha(alpha)
        overlay.fill(color)
        surface.blit(overlay, (x, y))

    def setup_regeneration_navigation(self):
        """Set up navigation for regeneration mode (pygame version)"""
        # In pygame, navigation is handled in the main handle_events method
        # This function now just ensures regeneration mode is properly initialized
        
        if not hasattr(self, 'regeneration_selection_index'):
            self.regeneration_selection_index = 0
        
        if not hasattr(self, 'in_regeneration_navigation'):
            self.in_regeneration_navigation = False
        
        print("Regeneration navigation setup completed (pygame)")

#PLAYER REGENERATION SYSTEM (PYGAME VERSION)
    def regenerate_body_part_pygame(self, character, part_index):
        
        """Regenerate a specific body part (pygame version)"""
        print("DEBUG: Using FIRST regenerate_body_part_pygame function (line ~4950) - HAS mess_up AND amputate checks")
        # Check if part index is valid
        if not (0 <= part_index < len(character.body_parts)):
            self.set_message(f"Indice parte del corpo non valido: {part_index}", 1500)  # ← FIXED
            return False
        
        part = character.body_parts[part_index]
        
        # Check if the body part is already at full health
        if part.p_pvt >= part.max_p_pvt:
            self.set_message("Questa parte del corpo è già completamente guarita!", 1500)  # ← FIXED
            return False

        # Check for MESS UP effect FIRST - reduces level instead of healing
        if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'mess_up'):
            mess_up_data = getattr(part.p_eff, 'mess_up')
            # Check if mess_up is active (level > 0)
            if len(mess_up_data) >= 2 and mess_up_data[1] > 0:
                # Check regeneration (rig) resource first
                if character.rig < 5:
                    self.set_message("Non puoi più rigenerarti!", 1500)
                    return False
                
                # Check stamina resource
                if character.sta < stamina_cost_per_regeneration:
                    self.set_message("Non hai abbastanza stamina!", 1500)
                    return False
                
                mess_up_level = mess_up_data[1]
                # Reduce mess_up level by 1 instead of healing
                new_level = max(0, mess_up_level - 1)
                setattr(part.p_eff, 'mess_up', [mess_up_data[0], new_level, mess_up_data[2], mess_up_data[3]])
                
                # Consume resources but NO HEALING
                character.rig -= 5
                character.sta -= stamina_cost_per_regeneration
                
                self.set_message(f"{part.name} mess up ridotto a livello {new_level}! Nessuna guarigione.", 2000)
                self.add_log_entry(f"{character.name}'s {part.name} mess up reduced to level {new_level} - no healing", "effect", (200, 150, 100))
                
                return True  # Regeneration was "successful" but no healing occurred

        # Check for AMPUTATE effect blocking regeneration
        if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'amputate'):
            amputate_data = getattr(part.p_eff, 'amputate')
            # Check if amputate is active (level > 0 and duration > 0)
            if len(amputate_data) >= 3 and amputate_data[1] > 0 and amputate_data[2] > 0:
                self.set_message(f"{part.name} è amputata e non può rigenerarsi!", 2000)
                return False
        
        # Check regeneration (rig) resource
        if character.rig < 5:
            self.set_message("Non puoi più rigenerarti!", 1500)  # ← FIXED
            return False
        
        # Check stamina resource
        if character.sta < stamina_cost_per_regeneration:
            self.set_message("Non hai abbastanza stamina!", 1500)  # ← FIXED
            return False
        
        # Warning if player has low RES
        if hasattr(character, 'res') and character.res < 5:
            self.set_message("ATTENZIONE: RES insufficiente per ripristinare RIG nel prossimo turno!", 2000)  # ← FIXED
        
        # Apply regeneration
        old_pvt = part.p_pvt
        part.p_pvt = min(part.p_pvt + 5, part.max_p_pvt)
        actual_healing = part.p_pvt - old_pvt
        
        # Consume resources
        character.rig -= 5
        character.sta -= stamina_cost_per_regeneration
        
        # Recalculate total health
        character.calculate_health_from_body_parts()
        
        # Update automatic debuffs (in case status effects were weakened by regeneration)
        update_automatic_debuffs(character)
        
        # Show success message
        self.set_message(f"Rigenerato {part.name}: +{actual_healing} HP\nRIG: -{rig_cost_per_regeneration}, STA: -{stamina_cost_per_regeneration}", 2000)  # ← FIXED

        print(f"Regenerated {character.name}'s {part.name}: {old_pvt} -> {part.p_pvt} (+{actual_healing})")
        
        # Play regeneration sound effect
        if actual_healing > 0:
            try:
                import random
                import Global_SFX
                regen_sounds = [
                    r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\cute-level-up-3-189853.mp3",
                    r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\cute-level-up-3-189853.mp3",
                    r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\cute-level-up-3-189853.mp3",
                ]
                sound_file = random.choice(regen_sounds)
                
                # Use battle menu instance sound system
                if hasattr(self, 'play_sound_effect'):
                    global_sfx_volume = Global_SFX.get_global_sfx_volume()
                    final_volume = 0.6 * global_sfx_volume  # 0.6 base volume for regeneration
                    self.play_sound_effect(sound_file, volume=final_volume, loops=0)
                else:
                    # Fallback to direct pygame with Global_SFX
                    sound = Global_SFX.load_sound_with_global_volume(sound_file, 0.6)
                    if sound:
                        sound.play()
                print(f"[SOUND] Played player regeneration sound: {sound_file}")
            except Exception as e:
                print(f"[SOUND] Error playing player regeneration sound: {e}")
        
        return True

    def show_ability_details_pygame(self):
        """Show detailed information about the selected ability (pygame version)"""
        if self.menu_selection_index != 3:  # Not in ability menu
            return
        
        if not hasattr(player, 'ability') or not player.ability or len(player.ability) == 0:
            self.set_message("Nessuna abilità disponibile", 1500)  # ← FIXED: use set_message
            return
        
        ability_index = getattr(self, 'ability_selection_index', 0)
        if ability_index < 0 or ability_index >= len(player.ability):
            return
        
        selected_ability = player.ability[ability_index]
        
        # Show detailed ability information
        detail_text = f"{selected_ability.name}\nCosto: {selected_ability.punti} punti\n\n{selected_ability.descriptionLong}"
        self.set_message(detail_text, 4000)  # ← FIXED: use set_message instead of draw_message
        
        print(f"Showing details for ability: {selected_ability.name}")

    def restore_stamina(self, character, amount):
        """
        Restore stamina to a character, ensuring it doesn't exceed the effective maximum (pygame version).
        
        Args:
            character: The character object
            amount (int): Amount of stamina to restore
        """
        if not hasattr(character, 'sta'):
            print(f"Character {getattr(character, 'name', 'Unknown')} does not have stamina attribute")
            return
        
        # Get the effective maximum stamina
        effective_max = getattr(character, 'effective_max_sta', character.max_sta)
        
        old_stamina = character.sta
        character.sta = min(character.sta + amount, effective_max)
        
        actual_restored = character.sta - old_stamina
        self.set_message(f"Stamina ripristinata: +{actual_restored}\n{character.sta}/{effective_max}", 1500)  # ← FIXED
        
        print(f"Restored {actual_restored} stamina to {getattr(character, 'name', 'Unknown')}. Current: {character.sta}/{effective_max}")

    def debug_stamina_info(self):
        """Debug function to print current stamina information (pygame version)"""
        print("\n=== STAMINA DEBUG INFO ===")
        print(f"Player base max_sta: {player.max_sta}")
        print(f"Player buf_sta: {get_character_buff_level(player, 'sta')}")
        print(f"Player current sta: {player.sta}")
        print(f"Player effective_max_sta: {getattr(player, 'effective_max_sta', 'Not set')}")
        print(f"Stamina scaling factor: {STAT_SCALING_FACTORS['sta']}")
        calculated_max = player.max_sta + (get_character_buff_level(player, 'sta') * STAT_SCALING_FACTORS['sta'])
        print(f"Calculated max stamina: {calculated_max}")
        print("========================\n")
        
        # Also show on screen
        debug_text = f"STAMINA DEBUG\nMax: {player.max_sta} | Current: {player.sta}\nEffective Max: {getattr(player, 'effective_max_sta', 'Not set')}\nBuff Level: {get_character_buff_level(player, 'sta')}"
        self.set_message(debug_text, 3000)  # ← FIXED

    def draw_enemy_stamina_bar(self):
        """Draw enemy stamina bar between buff matrix and event log"""
        global enemy
        if self.menu_selection_index == 0 and enemy:  # Only show when enemy panel is active
            # Calculate same positioning as buff matrix to ensure proper alignment
            panel_x = self.sx(310)  # Main panel x
            panel_width = self.sx(760)  # Main panel width
            parts_x = panel_x + panel_width + self.sx(20)  # Body parts list x
            parts_bg_width = self.sx(180)  # Body parts background width
            detail_panel_x = parts_x + parts_bg_width + self.sx(20)  # Detail box x
            detail_panel_width = self.sx(275)  # Detail box width
            detail_panel_y = self.sy(80)   # Detail box y position
            detail_panel_height = self.sy(350)  # Detail box height
            
            # Calculate total available space and split it 50/50
            detail_box_bottom = detail_panel_y + detail_panel_height
            log_top = self.log_y
            total_available_space = log_top - detail_box_bottom
            padding = self.sy(5)  # Reduced padding to match buff matrix
            
            # Split available space 50/50 between buff matrix and stamina bar
            usable_space = total_available_space - (3 * padding)  # 3 paddings: top, middle, bottom
            half_space = usable_space // 2
            
            # Position stamina bar in the second half of available space
            stamina_bar_x = self.log_x  # Align with event log horizontally
            stamina_bar_y = detail_box_bottom + padding + half_space + padding  # After buff matrix + middle padding
            stamina_bar_width = self.log_width  # Same width as event log
            stamina_bar_height = half_space  # Use second half of available space
            
            # Draw background box for stamina bar
            pygame.draw.rect(self.screen, BLACK, (stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height))
            pygame.draw.rect(self.screen, WHITE, (stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height), 2)
            
            # Draw stamina text to the left
            stamina_text = f"ENEMY STA: {int(enemy.sta)}/{int(enemy.max_sta)}"
            text_x = stamina_bar_x + self.sx(10)
            text_y = stamina_bar_y + (stamina_bar_height // 2) - (self.font_small.get_height() // 2)  # Vertically centered
            self.draw_text(stamina_text, self.font_small, WHITE, text_x, text_y)
            
            # Calculate bar position to the right of text
            text_width = self.font_small.size(stamina_text)[0]
            bar_x = text_x + text_width + self.sx(15)  # Bar starts after text with some spacing
            bar_y = stamina_bar_y + (stamina_bar_height // 2) - self.sy(6)  # Vertically centered
            bar_width = stamina_bar_x + stamina_bar_width - bar_x - self.sx(10)  # Fill remaining width
            bar_height = self.sy(12)  # Increased bar height
            
            # Draw background bar (dark gray)
            pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
            
            # Draw fill bar (green, same as player stamina)
            if enemy.max_sta > 0:
                fill_width = int(bar_width * enemy.sta / enemy.max_sta)
                pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, fill_width, bar_height))

    def draw_enemy_buffs_matrix(self):
        """Draw enemy buff/debuff display as horizontal line (STR +/-X | DEX +/-X | SPE +/-X | SPD +/-X)"""
        global enemy  # Access the global enemy variable
        if self.menu_selection_index == 0:  # Only show when enemy panel is active
            # Position aligned with event log box
            # Calculate coordinates using same logic as log positioning
            panel_x = self.sx(310)  # Main panel x
            panel_width = self.sx(760)  # Main panel width
            parts_x = panel_x + panel_width + self.sx(20)  # Body parts list x
            parts_bg_width = self.sx(180)  # Body parts background width
            detail_panel_x = parts_x + parts_bg_width + self.sx(20)  # Detail box x
            detail_panel_width = self.sx(275)  # Detail box width
            detail_panel_y = self.sy(80)   # Detail box y position
            detail_panel_height = self.sy(350)  # Detail box height
            
            # Calculate total available space between detail box and event log
            detail_box_bottom = detail_panel_y + detail_panel_height
            log_top = self.log_y
            total_available_space = log_top - detail_box_bottom
            padding = self.sy(5)  # Reduced padding
            
            # Split available space 50/50 between buff matrix and stamina bar
            usable_space = total_available_space - (3 * padding)  # 3 paddings: top, middle, bottom
            half_space = usable_space // 2
            
            # Position the buff display in the first half of available space
            matrix_x = self.log_x  # Align with event log horizontally
            matrix_y = detail_box_bottom + padding  # Just below detail box with padding  
            matrix_width = self.log_width  # Same width as event log
            matrix_height = half_space  # Use first half of available space
            
            # Draw background box
            pygame.draw.rect(self.screen, BLACK, (matrix_x, matrix_y, matrix_width, matrix_height))
            pygame.draw.rect(self.screen, WHITE, (matrix_x, matrix_y, matrix_width, matrix_height), 2)
            
            # Get enemy buff levels for the main stats + dodge/shield
            buff_stats = ['forz', 'des', 'spe', 'vel']
            stat_names = ['STR', 'DEX', 'SPE', 'SPD'] 
            buff_values = []
            
            for stat in buff_stats:
                value = 0
                if hasattr(enemy, 'buffs') and hasattr(enemy.buffs, f'buf_{stat}'):
                    buff_data = getattr(enemy.buffs, f'buf_{stat}')
                    if len(buff_data) >= 2 and buff_data[2] > 0:  # Active buff/debuff
                        try:
                            value = int(buff_data[1]) if isinstance(buff_data[1], str) else buff_data[1]
                        except (ValueError, TypeError):
                            value = 0
                buff_values.append(value)
            
            # Get DODGE and SHIELD values
            dodge_value = 0
            shield_value = 0
            
            if hasattr(enemy, 'buffs'):
                if hasattr(enemy.buffs, 'buf_dodge'):
                    dodge_data = getattr(enemy.buffs, 'buf_dodge')
                    if len(dodge_data) >= 2 and dodge_data[2] > 0:  # Active buff
                        try:
                            dodge_value = int(dodge_data[1]) if isinstance(dodge_data[1], str) else dodge_data[1]
                        except (ValueError, TypeError):
                            dodge_value = 0
                
                if hasattr(enemy.buffs, 'buf_shield'):
                    shield_data = getattr(enemy.buffs, 'buf_shield')
                    if len(shield_data) >= 2 and shield_data[2] > 0:  # Active buff
                        try:
                            shield_value = int(shield_data[1]) if isinstance(shield_data[1], str) else shield_data[1]
                        except (ValueError, TypeError):
                            shield_value = 0
            
            # Create horizontal text format: "STR +/-X | DEX +/-X | SPE +/-X | SPD +/-X | DOG X | SHI X"
            text_parts = []
            for stat_name, value in zip(stat_names, buff_values):
                value_text = f"{value:+d}" if value != 0 else "0"
                text_parts.append(f"{stat_name} {value_text}")
            
            # Add DODGE and SHIELD
            text_parts.append(f"DODGE {dodge_value}" if dodge_value > 0 else "DODGE 0")
            text_parts.append(f"SHIELD {shield_value}" if shield_value > 0 else "SHIELD 0")

            # Join with separator
            full_text = " | ".join(text_parts)
            
            # Calculate text position (centered in box)
            text_x = matrix_x + matrix_width // 2
            text_y = matrix_y + matrix_height // 2
            
            # Draw the text centered
            self.draw_text(full_text, self.font_medium, WHITE, text_x, text_y, center=True)

    def get_body_part_buff_involvement(self, part, character):
        """
        Check if the selected body part is involved in any active buffs/debuffs.
        Returns a list of involvement descriptions based on actual move requirements.
        """
        involvement_list = []
        
        # Check if character has active buffs system
        if not hasattr(character, 'active_buffs'):
            return involvement_list
            
        # Get all active buff moves with their requirements
        active_buff_moves = character.active_buffs.get_active_buff_moves()
        
        for move_name, buff_data in active_buff_moves.items():
            requirements = buff_data.get('requirements', [])
            
            # Check if this body part is required for this buff move
            if self.is_part_required_for_move(part.name, requirements):
                # Find the buff effects to get level and type
                effects = buff_data.get('effects', [])
                for effect in effects:
                    if len(effect) >= 2:
                        effect_name = effect[0]
                        effect_level = effect[1]
                        
                        # Map effect names to display names
                        effect_display_map = {
                            'buf_forz': 'Strength',
                            'buf_des': 'Dexterity',
                            'buf_spe': 'Special',
                            'buf_vel': 'Speed',
                            'buf_rig': 'Regen',
                            'buf_res': 'Reserve',
                            'buf_sta': 'Stamina',
                            'buf_dodge': 'Dodge',
                            'buf_shield': 'Shield'
                        }
                        
                        display_name = effect_display_map.get(effect_name, effect_name)
                        
                        # Check if the buff is actually active in character.buffs
                        actual_buff_active = False
                        if hasattr(character, 'buffs') and hasattr(character.buffs, effect_name):
                            buff_data_actual = getattr(character.buffs, effect_name)
                            # Check if buff is truly active (level > 0 and duration > 0)
                            actual_buff_active = (buff_data_actual[1] > 0 and buff_data_actual[2] > 0)
                        
                        # Show simple involvement message without status indicators
                        buff_type = "Buff" if effect_level > 0 else "Debuff"
                        involvement_text = f"Involved in {buff_type}: {display_name}"
                        involvement_list.append(involvement_text)
        
        return involvement_list
    
    def is_part_required_for_move(self, part_name, requirements):
        """
        Check if a specific body part is required based on move requirements.
        Handles all body part names elastically and distinguishes singulars from plurals.
        """
        part_upper = part_name.upper()
        
        # Complete body part mapping for all possible requirements
        # This system is elastic and can handle any body part name pattern
        body_part_mapping = {
            # Basic body parts (singular - matches either/any)
            "ARM": ["RIGHT ARM", "LEFT ARM"],
            "LEG": ["RIGHT LEG", "LEFT LEG"],
            "CLAW": ["RIGHT CLAW", "LEFT CLAW"],
            "TENTACLES": ["TENTACLES"], # Single unified tentacles body part
            "HEAD": ["HEAD"],
            "BODY": ["BODY"],
            "HORN": ["HORN", "LEFT HORN", "RIGHT HORN"],
            "WING": ["LEFT WING", "RIGHT WING"],
            "TAIL": ["TAIL"],
            "EYE": ["LEFT EYE", "RIGHT EYE"],
            "HAND": ["LEFT HAND", "RIGHT HAND"],
            "FOOT": ["LEFT FOOT", "RIGHT FOOT"],
            
            # Plural requirements (require ALL of that type)
            "2 ARMS": ["RIGHT ARM", "LEFT ARM"],
            "2 LEGS": ["RIGHT LEG", "LEFT LEG"],
            "2 CLAWS": ["RIGHT CLAW", "LEFT CLAW"],
            "2 WINGS": ["LEFT WING", "RIGHT WING"],
            "2 HORNS": ["LEFT HORN", "RIGHT HORN"],
            "2 EYES": ["LEFT EYE", "RIGHT EYE"],
            "2 HANDS": ["LEFT HAND", "RIGHT HAND"],
            "2 FEET": ["LEFT FOOT", "RIGHT FOOT"],
            
            # Specific body parts (exact matches)
            "RIGHT ARM": ["RIGHT ARM"],
            "LEFT ARM": ["LEFT ARM"],
            "RIGHT LEG": ["RIGHT LEG"],
            "LEFT LEG": ["LEFT LEG"],
            "RIGHT CLAW": ["RIGHT CLAW"],
            "LEFT CLAW": ["LEFT CLAW"],

            "LEFT WING": ["LEFT WING"],
            "RIGHT WING": ["RIGHT WING"],
            "LEFT HORN": ["LEFT HORN"],
            "RIGHT HORN": ["RIGHT HORN"],
            "LEFT EYE": ["LEFT EYE"],
            "RIGHT EYE": ["RIGHT EYE"],
            "LEFT HAND": ["LEFT HAND"],
            "RIGHT HAND": ["RIGHT HAND"],
            "LEFT FOOT": ["LEFT FOOT"],
            "RIGHT FOOT": ["RIGHT FOOT"],
            
            # Equipment/weapon requirements that use body parts
            "SWORD": ["RIGHT ARM", "LEFT ARM"],
            "BOW": ["RIGHT ARM", "LEFT ARM"],
            "SHIELD": ["LEFT ARM"],
            "DAGGER": ["RIGHT ARM", "LEFT ARM"],
            "STAFF": ["RIGHT ARM", "LEFT ARM"],
            "WAND": ["RIGHT ARM", "LEFT ARM"],
            
        }
        
        for requirement in requirements:
            if not requirement:
                continue
                
            req_str = str(requirement).upper().strip()
            
            # Skip target-specific requirements
            if req_str.startswith("TARGET "):
                continue
                
            # Handle NEEDS prefixed requirements
            if req_str.startswith("NEEDS"):
                needs_requirement = req_str.replace("NEEDS", "").strip()
                
                # Check if this requirement involves our body part
                if needs_requirement in body_part_mapping:
                    required_parts = body_part_mapping[needs_requirement]
                    
                    # Check if our part is in the required parts list
                    if part_upper in [rp.upper() for rp in required_parts]:
                        return True
            
            # Handle backward compatibility (no NEEDS prefix)
            else:
                if req_str in body_part_mapping:
                    required_parts = body_part_mapping[req_str]
                    
                    # Check if our part is in the required parts list
                    if part_upper in [rp.upper() for rp in required_parts]:
                        return True
        
        return False

    def draw_enemy_part_attributes(self):
        """Draw attributes panel for the selected enemy part (pygame version) (SCALED)"""
        if self.menu_selection_index == 0:
            # Determine which part index to use based on current mode
            is_target_selection = hasattr(self, 'target_selection_active') and self.target_selection_active
            
            if is_target_selection:
                # During target selection, show the currently targeted part
                part_index = getattr(self, 'target_selection_index', 0)
            else:
                # During normal navigation, show the currently examined part
                part_index = self.enemy_parts_index
            
            # Ensure the index is valid
            if 0 <= part_index < len(enemy.body_parts):
                part = enemy.body_parts[part_index]
                
                # Position the detail box to the right of the body parts list (scaled)
                # Get the body parts list position first
                panel_x = self.sx(310)  # Main panel x
                panel_width = self.sx(760)  # Main panel width
                parts_x = panel_x + panel_width + self.sx(20)  # Body parts list x
                parts_bg_width = self.sx(180)  # Body parts background width
                
                # Position detail box to the right of body parts list
                detail_panel_x = parts_x + parts_bg_width + self.sx(20)  # 20px gap after body parts list
                detail_panel_y = self.sy(80)   # Vertically positioned
                detail_panel_width = self.sx(275)
                detail_panel_height = self.sy(350)
                
                # Draw panel background (scaled)
                pygame.draw.rect(self.screen, BLACK, (detail_panel_x, detail_panel_y, detail_panel_width, detail_panel_height))
                pygame.draw.rect(self.screen, WHITE, (detail_panel_x, detail_panel_y, detail_panel_width, detail_panel_height), 2)
                
                # Title - Part name (scaled) - Color it differently during target selection
                title_color = (255, 100, 100) if is_target_selection else WHITE  # Red during targeting
                self.draw_text(part.name, self.font_large, title_color, detail_panel_x + self.sx(10), detail_panel_y + self.sy(15))
                
                # PVT Bar section (scaled)
                pvt_y = detail_panel_y + self.sy(60)
                pvt_label_color = (255, 150, 150) if is_target_selection else GREEN  # Light red during targeting
                self.draw_text("PVT", self.font_medium, pvt_label_color, detail_panel_x + self.sx(10), pvt_y)
                
                # Draw PVT bar (scaled)
                bar_x = detail_panel_x + self.sx(60)
                bar_y = pvt_y + self.sy(5)
                bar_width = self.sx(200)
                bar_height = self.sy(18)
                
                # Background bar (scaled)
                pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
                
                # Health fill (scaled) - Red tinted during target selection
                if part.max_p_pvt > 0:
                    fill_width = int(bar_width * part.p_pvt / part.max_p_pvt)
                    bar_color = (255, 50, 50) if is_target_selection else GREEN  # Red during targeting
                    pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, fill_width, bar_height))
                
                # HP text on bar (scaled)
                hp_text = f"{part.p_pvt}/{part.max_p_pvt}"
                hp_text_color = (255, 200, 200) if is_target_selection else WHITE  # Light red during targeting
                self.draw_text(hp_text, self.font_small, hp_text_color, bar_x + bar_width//2, bar_y + bar_height//2, center=True)
                
                # Effects section (scaled)
                effects_y = detail_panel_y + self.sy(120)
                effects_label_color = (255, 150, 150) if is_target_selection else WHITE  # Light red during targeting
                self.draw_text("Effetti:", self.font_medium, effects_label_color, detail_panel_x + self.sx(10), effects_y)
                
                # Draw individual effects (scaled)
                effect_y_offset = effects_y + self.sy(30)
                effects_found = False
                
                if hasattr(part, 'p_eff'):
                    effetti = part.p_eff
                    
                    # Check each effect type
                    effect_names = ['burn', 'bleed', 'poison', 'stun', 'confusion', 'acid', 'frost', 'heal', 'regeneration', 'sleep', 'weakness', 'amputate', 'mess_up', 'paralysis', 'fry_neurons', 'fine_dust', 'custom_poison']
                    
                    for eff_name in effect_names:
                        if hasattr(effetti, eff_name):
                            eff_val = getattr(effetti, eff_name)
                            
                            # Check if effect is active (level != 0)
                            if isinstance(eff_val, list) and len(eff_val) >= 4 and eff_val[1] != 0:
                                effects_found = True
                                
                                # Format effect info: [name, level, duration, immunity]
                                from Status_Effects_Config import should_show_effect_duration
                                
                                effect_text = f"{eff_name.upper()}:"
                                
                                # Check if this effect should show duration (effects with reduces_over_time=False show "---" instead of 999)
                                from Status_Effects_Config import should_effect_reduce_over_time
                                if should_effect_reduce_over_time(eff_name):
                                    duration_text = str(eff_val[2])
                                else:
                                    duration_text = "---"  # Show "---" for effects with infinite duration (reduces_over_time=False)
                                
                                effect_details = f"Lv.{eff_val[1]}, Dur.{duration_text}, Imm.{eff_val[3]}"
                                
                                # Draw effect name (scaled) - Tinted during target selection
                                effect_color = (255, 180, 180) if is_target_selection else (0, 224, 224)  # Light red vs cyan
                                self.draw_text(effect_text, self.font_small, effect_color, detail_panel_x + self.sx(20), effect_y_offset)
                                
                                # Draw effect details on next line (scaled)
                                self.draw_text(effect_details, self.font_small, effect_color, detail_panel_x + self.sx(25), effect_y_offset + self.sy(18))
                                
                                effect_y_offset += self.sy(45)  # Space for next effect
                
                # If no active effects found (scaled)
                if not effects_found:
                    no_effects_color = (200, 150, 150) if is_target_selection else GRAY  # Light red during targeting
                    self.draw_text("Nessun effetto attivo", self.font_small, no_effects_color, detail_panel_x + self.sx(20), effect_y_offset)
                
                # Check for buff involvement - position it just above the bottom of the detail panel
                buff_involvement = self.get_body_part_buff_involvement(part, enemy)
                
                if buff_involvement:
                    # Position at bottom of detail panel, working upwards for multiple lines
                    panel_bottom = detail_panel_y + detail_panel_height - self.sy(20)  # Small margin from bottom
                    buff_involvement_y = panel_bottom - (len(buff_involvement) * self.sy(18))  # Calculate starting Y based on number of lines
                    
                    for involvement_text in buff_involvement:
                        involvement_color = (255, 200, 100) if is_target_selection else (255, 215, 0)  # Gold color
                        self.draw_text(involvement_text, self.font_small, involvement_color, detail_panel_x + self.sx(15), buff_involvement_y)
                        buff_involvement_y += self.sy(18)

    def show_target_selection(self, move):
        """Show target selection mode (FIXED)"""
        print(f"DEBUG: show_target_selection called for move: {move.name}")
        
        # Initialize target selection state
        self.target_selection_active = True
        self.selected_move = move
        
        # Find first valid target
        self.target_selection_index = self.find_next_valid_target(0, 1)
        
        # Force switch to enemy panel to show target selection
        self.menu_selection_index = 0
        
        print(f"DEBUG: Target selection activated")
        print(f"DEBUG: Switched to enemy panel (menu_selection_index = {self.menu_selection_index})")
        print(f"DEBUG: Target selection index: {self.target_selection_index}")
        print(f"DEBUG: Selected move: {self.selected_move.name}")
    
    def draw_target_selection(self):
        """Draw target selection interface integrated into enemy panel"""
        # Target selection is now integrated into show_enemy_panel()
        # This method is kept for compatibility but doesn't need to do anything
        # since the enemy panel handles both normal navigation and target selection
        pass

    def cancel_target_selection(self):
        """Cancel target selection and return to moves menu (UPDATED)"""
        print("DEBUG: Cancelling target selection")
        
        # Clear any pending animation timers
        pygame.time.set_timer(pygame.USEREVENT + 3, 0)
        
        # Unlock move execution in case it was locked
        self.move_execution_locked = False
        
        self.target_selection_active = False
        self.selected_move = None
        self.target_selection_index = 0
        
        # Return to moves menu
        self.menu_selection_index = 1
        
        print("Target selection cancelled - returned to moves menu")

    def execute_selected_move(self):
        """Execute the selected move on the selected target (FIXED with memory skills)"""
        global Turn
        
        # Check if move execution is already locked (prevents multiple executions during animations)
        if getattr(self, 'move_execution_locked', False):
            print("DEBUG: execute_selected_move - Move execution is locked, ignoring input")
            return
            
        if not self.target_selection_active or not hasattr(self, 'selected_move') or not self.selected_move:
            print("DEBUG: execute_selected_move - No active target selection or move")
            return
        
        # Check if player has head for attacking (must have > 1 HP)
        player_head = None
        for part in player.body_parts:
            if part.name.upper() == "HEAD":
                player_head = part
                break
        
        if player_head is None or player_head.p_pvt <= 1:
            self.add_log_entry(f"{player.name} cannot aim without head", "combat", (255, 100, 100))
            print(f"DEBUG: {player.name} cannot aim without head")
            return
        
        # Lock move execution to prevent multiple calls during animation
        self.move_execution_locked = True
        print("DEBUG: Move execution locked - preventing multiple executions")
        
        target_part = enemy.body_parts[self.target_selection_index]
        move = self.selected_move
        
        print(f"DEBUG: Executing {move.name} on {target_part.name}")
        
        # CRITICAL: Add requirement validation that was missing!
        # Calculate actual stamina cost with requirement reductions AND weapon bonus (already included)
        actual_stamina_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs, move.accuracy)
        actual_stamina_cost = max(1, actual_stamina_cost)  # Minimum 1 stamina
        print(f"DEBUG: Final stamina cost (with all bonuses): {actual_stamina_cost}")

        # Check if player still has enough stamina
        if player.sta < actual_stamina_cost:
            self.show_error_message("Non hai abbastanza stamina!", 1500)
            # Unlock move execution and return
            self.move_execution_locked = False
            return

        # Check target-specific and status requirements
        can_use, failed_reqs = check_move_requirements(player, move, enemy, target_part)
        if not can_use:
            # Show requirement failure message
            req_message = f"Non puoi usare {move.name}: {', '.join(failed_reqs)}"
            self.show_error_message(req_message, 2000)
            print(f"DEBUG: Target requirements not met: {failed_reqs}")
            # Unlock move execution and return
            self.move_execution_locked = False
            return

        # Subtract stamina cost from player ONLY after validation passes
        old_stamina = player.sta
        player.sta -= actual_stamina_cost
        if player.sta < 0:
            player.sta = 0
        print(f"STAMINA DEBUG: Player stamina {old_stamina} -> {player.sta} (reduced by {actual_stamina_cost})")
        
        # Check for FINE DUST effect blocking FIRE/ELECTRIC moves
        if move.elem and ("FIRE" in move.elem or "ELECTRIC" in move.elem):
            # Check if player has fine_dust on body
            body_part = None
            for part in player.body_parts:
                if "BODY" in part.name.upper():
                    body_part = part
                    break
            
            if body_part and hasattr(body_part, 'p_eff') and hasattr(body_part.p_eff, 'fine_dust'):
                dust_data = getattr(body_part.p_eff, 'fine_dust')
                # Check if fine_dust is active (level > 0 and duration > 0)
                if dust_data[1] > 0 and dust_data[2] > 0:
                    dust_level = dust_data[1]
                    print(f"FINE DUST: Blocking {move.name} due to fine dust level {dust_level}")
                    
                    # Move does not hit - deal self-damage to used body parts
                    self_damage = player.spe  # Damage equal to player's special stat
                    damaged_parts = []
                    
                    # Deal damage to body parts used by the move based on requirements
                    used_body_parts = []
                    for req in move.reqs:
                        req_str = str(req).upper().strip()
                        
                        # Parse NEEDS requirements to find actual body parts used
                        if req_str.startswith("NEEDS"):
                            needs_requirement = req_str.replace("NEEDS", "").strip()
                            
                            # Map requirements to actual body parts
                            if needs_requirement == "2 ARMS":
                                used_body_parts.extend(["RIGHT ARM", "LEFT ARM"])
                            elif needs_requirement == "ARM":
                                # For single arm requirements, use any available arm
                                for part in player.body_parts:
                                    if "ARM" in part.name.upper() and part.p_pvt >= 2:
                                        used_body_parts.append(part.name)
                                        break
                            elif needs_requirement == "2 LEGS":
                                used_body_parts.extend(["RIGHT LEG", "LEFT LEG"])
                            elif needs_requirement == "LEG":
                                # For single leg requirements, use any available leg
                                for part in player.body_parts:
                                    if "LEG" in part.name.upper() and part.p_pvt >= 2:
                                        used_body_parts.append(part.name)
                                        break
                            elif needs_requirement == "TENTACLE":
                                used_body_parts.extend(["TENTACLE 1", "TENTACLE 2"])
                            elif "TENTACLE" in needs_requirement:
                                # Find any tentacle parts
                                for part in player.body_parts:
                                    if "TENTACLE" in part.name.upper():
                                        used_body_parts.append(part.name)
                    
                    # Apply damage to identified body parts
                    for part_name in used_body_parts:
                        for part in player.body_parts:
                            if part.name.upper() == part_name.upper():
                                old_hp = part.p_pvt
                                part.p_pvt = max(0, part.p_pvt - self_damage)
                                actual_damage = old_hp - part.p_pvt
                                if actual_damage > 0:
                                    damaged_parts.append(f"{part.name}({actual_damage})")
                                break
                    
                    dust_message = f"Fine dust explosion! {player.name} takes {self_damage} damage to used parts: {', '.join(damaged_parts) if damaged_parts else 'none'}"
                    self.add_log_entry(dust_message, "effect", (200, 100, 50))
                    print(dust_message)
                    
                    # Play explosion sound effect
                    play_sound_effect("explosion-1.mp3", volume=0.8)
                    
                    # Clear all fine dust from player's body after explosion
                    if hasattr(body_part.p_eff, 'fine_dust'):
                        setattr(body_part.p_eff, 'fine_dust', ['fine_dust', 0, 0, False])
                        print(f"FINE DUST: Cleared all fine dust from {player.name}'s body after explosion")
                    
                    # Update player health and unlock execution
                    player.calculate_health_from_body_parts()
                    self.move_execution_locked = False
                    self.target_selection_active = False
                    return
        
        # Step 2: Calculate accuracy roll with evasion system and confusion modifier
        import random
        # Apply confusion modifier to attacker
        confusion_modifier = get_confusion_accuracy_modifier(player)
        # Apply target body part evasion to move accuracy
        final_accuracy = move.accuracy * target_part.p_elusione * confusion_modifier
        accuracy_roll = random.randint(1, 100)
        print(f"Accuracy roll: {accuracy_roll}, Move accuracy: {move.accuracy}, Target evasion: {target_part.p_elusione}, Confusion modifier: {confusion_modifier}, Final accuracy: {final_accuracy}")
        
        if accuracy_roll > final_accuracy:
            # Miss - show miss message and play miss sound
            miss_message = f"{player.name} ha fallito l'attacco!"
            self.show_warning_message(miss_message, 1500)
            print(f"Attack missed! {miss_message}")
            
            # LOG: Player move missed (blue color)
            self.add_log_entry(f"{player.name} used {move.name} on {target_part.name} - MISSED!", "combat", (100, 150, 255))
            self.draw_event_log()
            pygame.display.flip()
            
            # Track player move for AI Priority +16 (even if missed)
            if hasattr(self, 'enemy_ai') and self.enemy_ai:
                player_body_part = self.extract_player_body_part_from_move(move)
                target_name = target_part.name if target_part else "UNKNOWN"
                self.enemy_ai.track_player_move(move.name, player_body_part, target_name, Turn)
                print(f"[BATTLE] Tracked player move (MISSED): {move.name} using {player_body_part} -> {target_name} (Turn {Turn})")
            
            # Play miss sound effect
            play_sound_effect("mixkit-punch-through-air-2141.mp3", volume=0.6)
            
            # Make enemy blink blue to indicate miss
            self.blink_character_gif("enemy", (100, 150, 255), 200, 2)
            
            # SET DELAY FOR MISS ANIMATION - Wait for blink animation to complete
            animation_delay = 2 * 200 + 500  # 2 blinks * 200ms each + 500ms buffer = 900ms
            pygame.time.set_timer(pygame.USEREVENT + 3, animation_delay)  # Custom event for returning to moves menu
            
        else:
            # Hit - but check for dodge/shield evasion first
            print(f"\n🎯 === PLAYER ATTACKING ENEMY ===")
            print(f"🎯 Player move: {move.name}")
            print(f"🎯 Target: {enemy.name}")
            print(f"🎯 Move stamina cost: {actual_stamina_cost}")
            can_evade, evasion_type, stamina_consumed = check_dodge_shield_evasion(enemy, move, actual_stamina_cost)
            
            if can_evade:
                # Attack was evaded!
                evasion_action = "DODGED" if evasion_type == "DODGE" else "BLOCKED"
                evade_message = f"{enemy.name} {evasion_action} the attack!"
                self.show_warning_message(evade_message, 2000)
                print(f"Attack evaded! {evade_message} (Used {evasion_type})")
                
                # LOG: Attack evaded
                self.add_log_entry(f"{player.name} used {move.name} on {target_part.name}", "combat")
                self.draw_event_log()
                pygame.display.flip()
                
                # Track player move for AI Priority +16 (even if evaded)
                if hasattr(self, 'enemy_ai') and self.enemy_ai:
                    player_body_part = self.extract_player_body_part_from_move(move)
                    target_name = target_part.name if target_part else "UNKNOWN"
                    self.enemy_ai.track_player_move(move.name, player_body_part, target_name, Turn)
                    print(f"[BATTLE] Tracked player move (EVADED): {move.name} using {player_body_part} -> {target_name} (Turn {Turn})")
                
                self.add_log_entry(f"{enemy.name} {evasion_action} the attack! (Consumed {stamina_consumed} stamina)", "evasion", (100, 255, 100))
                self.draw_event_log()
                pygame.display.flip()
                
                # Play dodge/shield sound effect
                if evasion_type == "DODGE":
                    play_sound_effect("mixkit-punch-through-air-2141.mp3", volume=0.6)  # Whoosh sound for dodge
                else:  # SHIELD
                    play_sound_effect("Shield_Sound.mp3", volume=0.6)  # Shield sound for blocking
                
                # Make enemy blink green to show successful evasion
                self.blink_character_gif("enemy", (100, 255, 100), 200, 2)
                
                # SET DELAY FOR EVASION ANIMATION
                animation_delay = 2 * 200 + 500  # 2 blinks * 200ms each + 500ms buffer
                pygame.time.set_timer(pygame.USEREVENT + 3, animation_delay)
                
            else:
                # Normal hit - show hit message, play hit sound, and apply damage
                hit_message = f"{player.name} ha colpito {target_part.name} del {enemy.name}!"
                self.show_success_message(hit_message, 2000)
                
                # Apply damage with property effects
                old_hp = target_part.p_pvt
                base_damage = move.danno
                
                # Check for rhythm damage bonus
                has_rhythm = has_property_effect(move, 'rhythm')
                if has_rhythm:
                    rhythm_tracking['player'] += 1
                    damage_to_deal = apply_rhythm_damage_bonus(base_damage, rhythm_tracking['player'] - 1)  # -1 because current move counts as first
                    self.add_log_entry(f"Rhythm x{rhythm_tracking['player']}: +{damage_to_deal - base_damage} damage!", "effect", (255, 255, 100))
                else:
                    # Reset rhythm count if not a rhythm move
                    rhythm_tracking['player'] = 0
                    damage_to_deal = base_damage
                
                # Check for clean cut property
                has_clean_cut = has_property_effect(move, 'clean_cut')
                if has_clean_cut:
                    damage_to_deal, clean_cut_triggered = check_clean_cut_threshold(damage_to_deal, target_part)
                    if clean_cut_triggered:
                        self.add_log_entry(f"CLEAN CUT! Devastating blow!", "effect", (255, 200, 0))
                        self.draw_event_log()
                        pygame.display.flip()
                
                # LOG: Player move hit first
                self.add_log_entry(f"{player.name} used {move.name} on {target_part.name}", "combat")
                
                # Apply elemental damage modifiers
                damage_to_deal, effects_will_apply = apply_elemental_damage(damage_to_deal, move, enemy, self)
                
                # Apply final damage
                target_part.p_pvt = max(0, target_part.p_pvt - damage_to_deal)
                actual_damage = old_hp - target_part.p_pvt
                    
                print(f"Damage applied to {enemy.name}'s {target_part.name}: {old_hp} -> {target_part.p_pvt} (Damage: {actual_damage})")
                
                # Gain weapon proficiency if player successfully hit with an ATK move using a weapon
                if hasattr(move, 'type') and move.type == 'ATK' and actual_damage > 0:
                    try:
                        from Player_Equipment import get_main_player_equipment
                        player_equip = get_main_player_equipment()
                        if player_equip:
                            equipped_weapon = player_equip.get_equipped_by_type('weapon')
                            if equipped_weapon:
                                weapon_class = equipped_weapon.get_weapon_class()
                                if weapon_class:
                                    old_proficiency = player_equip.get_weapon_proficiency(weapon_class)
                                    player_equip.weapon_proficiency.add_experience(weapon_class, 1)  # Add 1 hit experience
                                    new_proficiency = player_equip.get_weapon_proficiency(weapon_class)
                                    
                                    if new_proficiency > old_proficiency:
                                        self.add_log_entry(f"Weapon proficiency increased! {weapon_class} is now level {new_proficiency}!", "level_up", (255, 255, 0))
                                        print(f"[Battle] Weapon proficiency level up: {weapon_class} {old_proficiency} -> {new_proficiency}")
                                    else:
                                        print(f"[Battle] Gained weapon experience: {weapon_class} (+1 hit)")
                    except Exception as e:
                        print(f"[Battle] Error gaining weapon proficiency: {e}")
                
                # Check for body part destruction and trigger explosive mindset
                if old_hp > 0 and target_part.p_pvt == 0:
                    process_memory_skills_bodypart_loss(enemy, player, target_part.name)
                
                # Check for buff deactivation immediately after damage
                if actual_damage > 0:
                    deactivate_buffs_for_damaged_body_parts(enemy)
                    update_character_stats(enemy)
                
                # Apply lifesteal healing if move has lifesteal property
                has_lifesteal = has_property_effect(move, 'lifesteal')
                if has_lifesteal and actual_damage > 0:
                    heal_amount = apply_lifesteal_healing(player, actual_damage)
                    if heal_amount > 0:
                        self.add_log_entry(f"{player.name} healed {heal_amount} HP from lifesteal!", "heal", (100, 255, 100))
                        self.draw_event_log()
                        pygame.display.flip()
                
                # ALWAYS show damage dealt - this was missing in some cases
                self.add_log_entry(f"Damage dealt: {actual_damage} HP", "damage")
                self.draw_event_log()
                pygame.display.flip()

                # Recalculate enemy health
                enemy.calculate_health_from_body_parts()
                
                # Check if enemy buffs should be deactivated due to body part damage
                self.check_buffs_on_body_part_damage(enemy)

                # Apply status effects from the move to the targeted body part (only if effects not blocked by immunity)
                if effects_will_apply:
                    effects_applied = apply_move_effects(move, enemy, self.target_selection_index)
                else:
                    effects_applied = []  # No effects applied due to elemental immunity
                
                # Process Effect-on-Hit buffs for contact moves
                is_ranged_move = has_property_effect(move, 'ranged') if hasattr(move, 'eff_prop') else False
                process_effect_on_hit_buffs(player, enemy, move, is_ranged_move)
                
                # Update enemy stats if buffs/debuffs were applied
                if effects_applied:
                    # Check if any buff/debuff effects were applied
                    has_buff_debuff = any("BUFF" in effect[0] or "DEBUFF" in effect[0] for effect in effects_applied)
                    if has_buff_debuff:
                        update_character_stats(enemy)
                        recalculate_character_moves(enemy)
                        print(f"DEBUG: Recalculated enemy moves after debuff application")
                
                # LOG: Status effects applied
                if effects_applied:
                    for effect_name, effect_level, effect_duration in effects_applied:
                        self.add_log_entry(f"Applied {effect_name} (Lvl {effect_level}) for {effect_duration} turns", "effect")
                        self.draw_event_log()
                        pygame.display.flip()

                # Display delayed memory skills logs AFTER all main effects
                if hasattr(self, 'pending_memory_skill_logs') and self.pending_memory_skill_logs:
                    for log_message, log_type, log_color in self.pending_memory_skill_logs:
                        self.add_log_entry(log_message, log_type, log_color)
                        self.draw_event_log()
                        pygame.display.flip()
                    # Clear pending logs
                    self.pending_memory_skill_logs = []

                # Make enemy blink to show damage
                self.blink_character_gif("enemy", (255, 0, 0), 300, 3)

            # Track player move for AI Priority +16
            if hasattr(self, 'enemy_ai') and self.enemy_ai:
                player_body_part = self.extract_player_body_part_from_move(move)
                target_name = target_part.name if target_part else "UNKNOWN"
                self.enemy_ai.track_player_move(move.name, player_body_part, target_name, Turn)
                print(f"[BATTLE] Tracked player move: {move.name} using {player_body_part} -> {target_name} (Turn {Turn})")

            # Play appropriate sound effect based on move type first, then element
            # Note: Buff moves now play custom sounds when effects are applied in apply_move_effects()
            if hasattr(move, 'type') and move.type == 'BUF':
                # Buff moves: custom sounds are now played in apply_move_effects based on Status_Effects_Config
                print(f"[SOUND] Buff move {move.name} - custom sound will be played when effect is applied")
            elif "BUFF" in getattr(move, 'elem', ''):
                # Alternative check if BUFF is in element field - also uses custom sounds
                print(f"[SOUND] BUFF move {move.name} - custom sound will be played when effect is applied")
            elif "CUT" in move.elem:
                play_sound_effect("mixkit-quick-knife-slice-cutting-2152.wav", volume=0.6)
            elif "IMPACT" in move.elem:
                play_sound_effect("mixkit-sword-strikes-armor-2765", volume=0.6)
            elif "SPRAY" in move.elem:
                play_sound_effect("acid_spell_cast_squish_ball_impact_01-286782", volume=0.6)
            elif "POISON" in move.elem:
                play_sound_effect("Poison_Hits.mp3", volume=0.6)
            elif "ROAR" in move.elem:
                play_sound_effect("tiger-roar-loudly-193229", volume=0.6)
            elif "ELECTRIC" in move.elem:
                play_sound_effect("electrical-shock-zap-106412.mp3", volume=0.6)
            else:
                # Default attack sound for unrecognized move types
                play_sound_effect("mixkit-impact-of-a-strong-punch-2155", volume=0.6)
            
            # SET DELAY FOR HIT ANIMATION - Wait for blink animation to complete
            animation_delay = 3 * 300 + 500  # 3 blinks * 300ms each + 500ms buffer = 1400ms
            pygame.time.set_timer(pygame.USEREVENT + 3, animation_delay)  # Custom event for returning to moves menu
        
        # DON'T immediately end target selection - let the timer handle it
        print("DEBUG: Attack executed, waiting for animation to complete before returning to moves menu")

        # Unlock move execution after successful completion
        self.move_execution_locked = False

    def extract_player_body_part_from_move(self, move):
        """Extract which body part the player used to perform a move"""
        if not hasattr(move, 'reqs') or not move.reqs:
            return "UNKNOWN"
        
        # Look through move requirements to find body part requirements
        body_parts = ["HEAD", "BODY", "RIGHT ARM", "LEFT ARM", "RIGHT LEG", "LEFT LEG", 
                     "RIGHT CLAW", "LEFT CLAW", "TENTACLE 1", "TENTACLE 2"]
        
        for req in move.reqs:
            if not req:
                continue
                
            req_str = str(req).upper().strip()
            
            # Skip target requirements - we want the player's body part requirements
            if req_str.startswith("TARGET "):
                continue
                
            # Check if requirement matches a body part (player's limb requirement)
            for body_part in body_parts:
                if body_part in req_str:
                    # Handle "2 ARMS" type requirements - extract the limb type
                    if req_str.startswith("2 ") and "ARM" in req_str:
                        return "RIGHT ARM"  # For 2 ARMS requirement, assume primary is RIGHT ARM
                    elif req_str.startswith("2 ") and "LEG" in req_str:
                        return "RIGHT LEG"  # For 2 LEGS requirement, assume primary is RIGHT LEG
                    else:
                        return body_part
        
        # If no specific body part requirement found, assume it uses arms (most common)
        return "RIGHT ARM"

    def finish_player_attack_sequence(self):
        """Complete the player attack sequence - DOES NOT end player turn, just finishes the move"""
        print("DEBUG: Animation sequence completed, returning control to player")
        
        # Clear the timer
        pygame.time.set_timer(pygame.USEREVENT + 3, 0)
        
        # Unlock move execution (allows player to attack again)
        self.move_execution_locked = False
        print("DEBUG: Move execution unlocked - player can perform actions again")
        
        # Now end target selection and return to moves menu - player can continue their turn
        self.cancel_target_selection()
        
        # DO NOT START ENEMY TURN HERE - player's turn continues until they pass!

    def is_valid_target_for_move(self, move, target_part):
        """Check if a target body part is valid for a specific move"""
        if not move or not hasattr(move, 'reqs') or not move.reqs:
            return True  # No target-specific requirements
        
        for req in move.reqs:
            if req.startswith("target:") and req != f"target:{target_part.name.lower()}":
                return False
            elif req.startswith("target_status:"):
                # Check if target has required status effect
                required_status = req.split(":", 1)[1]
                if not hasattr(target_part, 'effetti') or not target_part.effetti or required_status not in target_part.effetti:
                    return False
        
        return True

    def find_next_valid_target(self, start_index, direction=1):
        """Find the next valid target for the current move, starting from start_index"""
        if not hasattr(self, 'selected_move') or not self.selected_move:
            return start_index  # No move selected, any target is valid
        
        move = self.selected_move
        total_parts = len(enemy.body_parts)
        
        # Check all targets to see if any are valid
        for i in range(total_parts):
            index = (start_index + i * direction) % total_parts
            target_part = enemy.body_parts[index]
            
            if self.is_valid_target_for_move(move, target_part):
                return index
        
        # If no valid targets found, return original index
        return start_index

    def use_selected_move(self):
        """Use the currently selected move (FIXED for pygame with requirements check)"""
        print("DEBUG: use_selected_move called")
        
        if not hasattr(player, 'moves') or not player.moves:
            print("DEBUG: Player has no moves")
            return
        
        if not hasattr(self, 'moves_selection_index') or self.moves_selection_index < 0 or self.moves_selection_index >= len(player.moves):
            print(f"DEBUG: Invalid move selection index: {getattr(self, 'moves_selection_index', 'None')}")
            return
        
        selected_move = player.moves[self.moves_selection_index]
        print(f"DEBUG: Selected move: {selected_move.name}, base cost: {selected_move.stamina_cost}")
        
        # Calculate actual stamina cost with requirement reductions
        actual_stamina_cost = calculate_move_stamina_cost(selected_move.sca_for, selected_move.sca_des, selected_move.sca_spe, selected_move.eff_appl, selected_move.reqs, selected_move.accuracy)
        print(f"DEBUG: Actual stamina cost with requirements: {actual_stamina_cost}")
        
        # Check if player has enough stamina
        if player.sta < actual_stamina_cost:
            self.show_error_message("Non hai abbastanza stamina!", 1500)
            print(f"DEBUG: Not enough stamina! Required: {actual_stamina_cost}, Current: {player.sta}")
            return
        
        # Check body part requirements (before target selection)
        can_use, failed_reqs = check_move_requirements(player, selected_move)
        if not can_use:
            # Show requirement failure message
            req_message = f"Non puoi usare {selected_move.name}: {', '.join(failed_reqs)}"
            self.show_error_message(req_message, 2000)
            print(f"DEBUG: Requirements not met: {failed_reqs}")
            return
        
        print("DEBUG: Player has enough stamina and meets requirements")
        
        # Check if this is a BUF move (self-buff) - these auto-target the player
        if selected_move.tipo == 'BUF':
            print(f"DEBUG: BUF move detected - auto-targeting player")
            # Execute BUF move directly on the player
            self.execute_buff_move(selected_move)
        else:
            print("DEBUG: ATK/REA move - starting target selection")
            # Player meets all requirements - start target selection
            self.show_target_selection(selected_move)

    def execute_buff_move(self, move):
        """Execute a BUF move (self-buff) with new requirement-based system"""
        print(f"DEBUG: Executing BUF move: {move.name}")
        
        # Check if this is a deactivation (move already active) or activation
        if move.name in player.active_buffs.get_active_buff_moves():
            # Deactivate the buff
            player.active_buffs.deactivate_buff_move(move.name)
            self.show_success_message(f"{move.name} deactivated!", 2000)
            self.add_log_entry(f"{player.name} deactivated {move.name}", "combat")
            
            # Remove the buff effects
            self.remove_buff_effects(move, player)
            
        else:
            # Check requirements are met
            if not self.check_move_requirements(move, player):
                self.show_error_message("Requirements not met for this buff!")
                return
            
            # Calculate actual stamina cost (weapon bonus already included in calculate_move_stamina_cost)
            actual_stamina_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs, move.accuracy)
            actual_stamina_cost = max(1, actual_stamina_cost)  # Minimum 1 stamina
            print(f"DEBUG: Buff final stamina cost (with all bonuses): {actual_stamina_cost}")
            
            # Check if player has enough stamina
            if player.sta < actual_stamina_cost:
                self.show_error_message("Not enough stamina!")
                return
            
            # Deactivate conflicting buffs first
            conflicting_buffs = player.active_buffs.deactivate_conflicting_buffs(move.reqs)
            if conflicting_buffs:
                for buff_name in conflicting_buffs:
                    # Find the conflicting move to remove its effects
                    for player_move in player.moves:
                        if player_move.name == buff_name:
                            self.remove_buff_effects(player_move, player)
                            print(f"DEBUG: Removed effects for conflicting buff: {buff_name}")
                            break
                    self.add_log_entry(f"Deactivated conflicting buff: {buff_name}", "effect")
                
                # Update stats after removing conflicting buff effects
                update_character_stats(player)
                recalculate_character_moves(player)
            
            # Subtract stamina from player
            old_stamina = player.sta
            player.sta -= actual_stamina_cost
            if player.sta < 0:
                player.sta = 0
            
            print(f"STAMINA DEBUG: Player stamina {old_stamina} -> {player.sta} (reduced by {actual_stamina_cost})")
            
            # Activate the new buff
            player.active_buffs.activate_buff_move(move.name, move.reqs, move.eff_appl)
            
            print(f"[BUF DEBUG] About to apply effects for BUF move: {move.name}")
            print(f"[BUF DEBUG] Move effects: {move.eff_appl}")
            
            # Apply effects (buffs) to the player
            effects_applied = apply_move_effects(move, player, None)
            
            print(f"[BUF DEBUG] Effects applied result: {effects_applied}")
            
            # Success message
            hit_message = f"{player.name} activated {move.name}!"
            self.show_success_message(hit_message, 2000)
            
            # LOG: Player used buff move
            self.add_log_entry(f"{player.name} activated {move.name}", "combat")
            
            # LOG: Buff effects applied
            if effects_applied:
                for effect_name, effect_level, effect_duration in effects_applied:
                    # Map stat abbreviations to full names
                    stat_mapping = {
                        'RIG BUFF': 'Rigidity buff',
                        'RES BUFF': 'Resistance buff', 
                        'STA BUFF': 'Stamina buff',
                        'FORZ BUFF': 'Strength buff',
                        'DES BUFF': 'Dexterity buff',
                        'SPE BUFF': 'Special buff',
                        'VEL BUFF': 'Velocity buff',
                        'RIG DEBUFF': 'Rigidity debuff',
                        'RES DEBUFF': 'Resistance debuff', 
                        'STA DEBUFF': 'Stamina debuff',
                        'FORZ DEBUFF': 'Strength debuff',
                        'DES DEBUFF': 'Dexterity debuff',
                        'SPE DEBUFF': 'Special debuff',
                        'VEL DEBUFF': 'Velocity debuff'
                    }
                    
                    # Get proper name or fallback to original
                    proper_name = stat_mapping.get(effect_name.upper(), effect_name.lower())
                    self.add_log_entry(f"Applied {proper_name} Lv {abs(effect_level)}", "effect")
        
        # Update player stats to reflect new buffs
        update_character_stats(player)
        
        # Recalculate all move damage based on new buffed stats
        recalculate_character_moves(player)
        
        # Custom buff sounds are now played in apply_move_effects based on Status_Effects_Config
        print(f"[SOUND] Player buff move {move.name} - custom sound played when effect was applied")
        
        # Make player blink to show buff applied/removed
        color = (0, 255, 0) if move.name in player.active_buffs.get_active_buff_moves() else (255, 255, 0)
        self.blink_character_gif("player", color, 300, 3)
        
        # Set delay for animation, then return to moves menu
        animation_delay = 3 * 300 + 500  # 3 blinks * 300ms each + 500ms buffer
        pygame.time.set_timer(pygame.USEREVENT + 3, animation_delay)
        
        print("DEBUG: BUF move executed, waiting for animation to complete")

    def check_move_requirements(self, move, character):
        """Check if a character meets the requirements for a move"""
        # Use the global requirement checking function
        can_use, failed_reqs = check_move_requirements(character, move)
        return can_use
    
    def remove_buff_effects(self, move, character):
        """Remove the buff effects of a move from a character"""
        if not hasattr(move, 'eff_appl') or not move.eff_appl:
            return
        
        # Effect-on-Hit buffs that need special handling
        effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
        
        # Remove each effect
        for effect in move.eff_appl:
            effect_name = effect[0]
            effect_level = effect[1]
            
            # Handle Effect-on-Hit buffs (remove from body parts)
            if effect_name in effect_on_hit_buffs:
                if character.body_parts:
                    for part in character.body_parts:
                        if hasattr(part, 'p_eff') and hasattr(part.p_eff, effect_name):
                            # Deactivate the Effect-on-Hit buff
                            setattr(part.p_eff, effect_name, [effect_name, 0, 0, False])
                            print(f"DEBUG: Removed {effect_name} Effect-on-Hit buff from {character.name}'s {part.name}")
            else:
                # Remove regular buffs by setting them back to default
                if hasattr(character.buffs, effect_name):
                    buff_attr = getattr(character.buffs, effect_name)
                    buff_attr[1] = 0  # Reset level to 0
                    buff_attr[2] = 0  # Reset duration to 0
                    print(f"DEBUG: Removed {effect_name} buff from {character.name}")

    def check_and_update_active_buffs(self):
        """Check active buffs for both player and enemy and deactivate those with unmet requirements"""
        print("DEBUG: Checking active buffs at round end...")
        
        # Check player buffs
        player_active = player.active_buffs.get_active_buff_moves()
        print(f"DEBUG: Player has {len(player_active)} active buffs: {list(player_active.keys())}")
        self.check_character_active_buffs(player, "Player")
        
        # Check enemy buffs if enemy exists
        if hasattr(self, 'current_enemy') and self.current_enemy:
            enemy_active = self.current_enemy.active_buffs.get_active_buff_moves()
            print(f"DEBUG: Enemy has {len(enemy_active)} active buffs: {list(enemy_active.keys())}")
            self.check_character_active_buffs(self.current_enemy, "Enemy")
    
    def check_character_active_buffs(self, character, character_name):
        """Check and update active buffs for a specific character"""
        active_buffs = character.active_buffs.get_active_buff_moves()
        deactivated_buffs = []
        
        for move_name, buff_data in active_buffs.items():
            requirements = buff_data['requirements']
            
            # Create a temporary move object with requirements for checking
            class TempMove:
                def __init__(self, reqs):
                    self.reqs = reqs
            
            temp_move = TempMove(requirements)
            
            # Use the proper requirement checking function
            requirements_met, failed_reqs = check_move_requirements(character, temp_move)
            
            if not requirements_met:
                print(f"DEBUG: Requirements failed for {move_name}: {failed_reqs}")
                # Deactivate the buff
                character.active_buffs.deactivate_buff_move(move_name)
                
                # Find the move to remove its effects
                for move in character.moves:
                    if move.name == move_name:
                        self.remove_buff_effects(move, character)
                        break
                
                deactivated_buffs.append(move_name)
        
        # Log deactivated buffs
        if deactivated_buffs:
            self.add_log_entry(f"{character_name} lost buffs: {', '.join(deactivated_buffs)}", "warning", (255, 150, 50))
            print(f"DEBUG: Deactivated {len(deactivated_buffs)} buffs for {character_name}: {deactivated_buffs}")

    def check_weapon_requirements_after_damage(self, character):
        """Check if currently equipped weapon can still be used after body part damage"""
        print(f"[DEBUG WEAPON] check_weapon_requirements_after_damage called for {character.name}")
        
        # Only check for player character
        if character != player:
            print(f"[DEBUG WEAPON] {character.name} is not player - skipping weapon check")
            return
        
        try:
            # Import Player_Equipment to access the player1 object
            sys.path.append(r'c:\Users\franc\Desktop\Afterdeath_RPG')
            from Player_Equipment import player1
            
            print(f"[DEBUG WEAPON] Checking equipped weapons for {character.name}")
            
            # Check all equipped items
            equipped_weapons = []
            for item in player1.equip:
                if hasattr(item, 'type') and item.type == 'weapon':
                    equipped_weapons.append(item)
                    print(f"[DEBUG WEAPON] Found equipped weapon: {item.name} (Type: {getattr(item, 'weapon_type', 'Unknown')})")
            
            if not equipped_weapons:
                print(f"[DEBUG WEAPON] No weapons equipped for {character.name}")
                return
            
            # Check each equipped weapon
            for weapon in equipped_weapons:
                weapon_type = getattr(weapon, 'weapon_type', 'Unknown')
                print(f"[DEBUG WEAPON] Checking weapon: {weapon.name} (Type: {weapon_type})")
                
                # Count functional arms (HP >= 2 as per user requirements)
                functional_arms = []
                for part in character.body_parts:
                    if "ARM" in part.name.upper() and part.p_pvt >= 2:
                        functional_arms.append(part.name)
                        print(f"[DEBUG WEAPON] Functional arm found: {part.name} ({part.p_pvt}/{part.max_p_pvt} HP)")
                
                functional_arm_count = len(functional_arms)
                print(f"[DEBUG WEAPON] Total functional arms (≥2 HP): {functional_arm_count}")
                
                # Check weapon requirements
                should_unequip = False
                unequip_reason = ""
                
                if weapon_type == "Two Handed":
                    if functional_arm_count < 2:
                        should_unequip = True
                        unequip_reason = f"Two Handed weapon requires 2 arms, but only {functional_arm_count} functional arms available"
                elif weapon_type in ["One Handed", "One and a Half Handed"]:
                    if functional_arm_count < 1:
                        should_unequip = True
                        unequip_reason = f"{weapon_type} weapon requires 1 arm, but only {functional_arm_count} functional arms available"
                
                # Auto-unequip if requirements not met
                if should_unequip:
                    print(f"[DEBUG WEAPON] AUTO-UNEQUIPPING: {weapon.name}")
                    print(f"[DEBUG WEAPON] Reason: {unequip_reason}")
                    
                    # Unequip the weapon
                    weapon.unequip()
                    
                    # Add battle log message
                    unequip_message = f"{character.name}'s {weapon.name} was automatically unequipped - {unequip_reason}"
                    self.add_log_entry(unequip_message, "warning", (255, 150, 50))
                    print(f"LOG [WEAPON]: {unequip_message}")
                    
                    # Show temporary message on screen
                    if hasattr(self, 'set_temporary_message'):
                        self.set_temporary_message(f"{weapon.name} automatically unequipped!", 3000, (255, 150, 50))
                else:
                    print(f"[DEBUG WEAPON] {weapon.name} can still be used with {functional_arm_count} functional arms")
                    
        except Exception as e:
            print(f"[DEBUG WEAPON] Error in check_weapon_requirements_after_damage: {e}")
            import traceback
            traceback.print_exc()

    def check_buffs_on_body_part_damage(self, character):
        """Check and deactivate buffs when body parts are damaged below the threshold"""
        print(f"[DEBUG WEAPON] check_buffs_on_body_part_damage called for {character.name}")
        
        # FIRST: Check weapon requirements and auto-unequip if needed
        self.check_weapon_requirements_after_damage(character)
        
        if not hasattr(character, 'active_buffs'):
            print(f"[DEBUG WEAPON] {character.name} has no active_buffs attribute")
            return
        
        active_buffs = character.active_buffs.get_active_buff_moves()
        if not active_buffs:
            return
        
        deactivated_buffs = []
        
        for move_name, buff_data in active_buffs.items():
            requirements = buff_data['requirements']
            
            # Create a temporary move object with requirements for checking
            class TempMove:
                def __init__(self, reqs):
                    self.reqs = reqs
            
            temp_move = TempMove(requirements)
            
            # Check if buff requirements are still met after damage
            requirements_met, failed_reqs = check_move_requirements(character, temp_move)
            
            if not requirements_met:
                print(f"DEBUG: Buff {move_name} requirements no longer met after body part damage: {failed_reqs}")
                # Deactivate the buff
                character.active_buffs.deactivate_buff_move(move_name)
                
                # Find the move to remove its effects
                for move in character.moves:
                    if move.name == move_name:
                        self.remove_buff_effects(move, character)
                        break
                
                deactivated_buffs.append(move_name)
        
        # Also check DODGE and SHIELD buffs for their specific requirements
        dodge_deactivated = False
        shield_deactivated = False
        
        # Check DODGE buff (requires 2 legs)
        if hasattr(character.buffs, 'buf_dodge'):
            dodge_data = character.buffs.buf_dodge
            if dodge_data[1] > 0 and dodge_data[2] > 0:  # Active dodge buff
                functional_legs = sum(1 for part in character.body_parts 
                                    if "LEG" in part.name.upper() and part.p_pvt >= 2)
                if functional_legs < 2:
                    dodge_data[1] = 0  # Deactivate by setting level to 0
                    dodge_data[2] = 0  # Also set duration to 0
                    dodge_deactivated = True
                    deactivated_buffs.append("DODGE")
                    print(f"DEBUG: {character.name}'s DODGE buff deactivated - insufficient legs ({functional_legs}/2)")
        
        # Check SHIELD buff (requires 1 arm)  
        if hasattr(character.buffs, 'buf_shield'):
            shield_data = character.buffs.buf_shield
            if shield_data[1] > 0 and shield_data[2] > 0:  # Active shield buff
                functional_arms = sum(1 for part in character.body_parts 
                                    if "ARM" in part.name.upper() and part.p_pvt >= 2)
                if functional_arms < 1:
                    shield_data[1] = 0  # Deactivate by setting level to 0
                    shield_data[2] = 0  # Also set duration to 0
                    shield_deactivated = True
                    deactivated_buffs.append("SHIELD")
                    print(f"DEBUG: {character.name}'s SHIELD buff deactivated - insufficient arms ({functional_arms}/1)")
        
        # Log and show message if buffs were deactivated
        if deactivated_buffs:
            character_name = getattr(character, 'name', 'Character')
            message = f"{character_name} lost buffs due to body part damage: {', '.join(deactivated_buffs)}"
            self.add_log_entry(message, "warning", (255, 150, 50))
            self.set_message(message, 2000)
            print(f"DEBUG: {len(deactivated_buffs)} buffs deactivated for {character_name} due to body part damage")

            for move_name in deactivated_buffs:
                self.add_log_entry(f"{character_name}'s {move_name} deactivated (requirements no longer met)", "effect")
            
            # Update character stats after removing buffs
            update_character_stats(character)
            # Recalculate moves after stat changes
        
        # CHECK WEAPON REQUIREMENTS AND AUTO-UNEQUIP IF NEEDED
        print(f"[DEBUG WEAPON] Starting weapon check for {character.name}")
        try:
            import Player_Equipment
            print(f"[DEBUG WEAPON] Player_Equipment imported successfully")
            # Check for player character (compare with global player object directly)
            print(f"[DEBUG WEAPON] Checking if character == player: {character == player}")
            print(f"[DEBUG WEAPON] Character: {character}, Player: {player}")
            print(f"[DEBUG WEAPON] Character name: {character.name}, Player name: {player.name}")
            
            if hasattr(Player_Equipment, 'player1') and character == player:
                print(f"[DEBUG WEAPON] Character is player, checking equipment...")
                player_equip = Player_Equipment.player1
                equipped_weapon = player_equip.get_equipped_by_type('weapon')
                print(f"[DEBUG WEAPON] Equipped weapon: {equipped_weapon}")
                
                if equipped_weapon:
                    print(f"[DEBUG WEAPON] Weapon found: {getattr(equipped_weapon, 'name', 'Unknown')}")
                    # Check if weapon requirements are still met
                    weapon_requirements = getattr(equipped_weapon, 'requirements', [])
                    print(f"[DEBUG WEAPON] Weapon requirements: {weapon_requirements}")
                    
                    if weapon_requirements:
                        print(f"[DEBUG WEAPON] Checking weapon requirements...")
                        # Create a temporary move object with weapon requirements for checking
                        class TempWeaponMove:
                            def __init__(self, reqs):
                                self.reqs = reqs
                        
                        temp_weapon_move = TempWeaponMove(weapon_requirements)
                        weapon_reqs_met, failed_weapon_reqs = check_move_requirements(character, temp_weapon_move)
                        print(f"[DEBUG WEAPON] Requirements met: {weapon_reqs_met}, Failed: {failed_weapon_reqs}")
                        
                        if not weapon_reqs_met:
                            weapon_name = getattr(equipped_weapon, 'name', 'Unknown Weapon')
                            print(f"[DEBUG WEAPON] *** WEAPON AUTO-UNEQUIPPING: {weapon_name} ***")
                            print(f"[DEBUG WEAPON] Weapon {weapon_name} requirements no longer met: {failed_weapon_reqs}")
                            
                            # Unequip the weapon
                            equipped_weapon.unequip()
                            print(f"[DEBUG WEAPON] Weapon {weapon_name} has been unequipped!")
                            
                            # Add event log messages with appropriate colors
                            self.add_log_entry(f"Weapon auto-unequipped: {weapon_name}", "warning", (255, 100, 100))
                            self.add_log_entry(f"Requirements no longer met: {', '.join(failed_weapon_reqs)}", "info", (200, 200, 200))
                            
                            # Show temporary message
                            self.set_message(f"Weapon unequipped: {weapon_name} (requirements not met)", 3000)
                            
                            print(f"[DEBUG WEAPON] Auto-unequipped weapon {weapon_name} due to failed requirements")
                        else:
                            print(f"[DEBUG WEAPON] Weapon requirements still met, no unequipping needed")
                    else:
                        print(f"[DEBUG WEAPON] Weapon has no requirements")
                else:
                    print(f"[DEBUG WEAPON] No weapon equipped for {character.name}")
            else:
                print(f"[DEBUG WEAPON] Character is not player or Player_Equipment.player1 not found")
                print(f"[DEBUG WEAPON] hasattr(Player_Equipment, 'player1'): {hasattr(Player_Equipment, 'player1') if 'Player_Equipment' in locals() else 'Player_Equipment not imported'}")
        except Exception as e:
            print(f"[DEBUG WEAPON] ERROR in weapon checking: {e}")
            import traceback
            traceback.print_exc()
            recalculate_character_moves(character)
            print(f"[DEBUG WEAPON] {character.name} buffs deactivated: {deactivated_buffs}")

    def show_error_message(self, message, duration=None):
        """Show an error message in the log (duration parameter kept for compatibility)"""
        self.add_log_entry(message, "error")

    def show_success_message(self, message, duration=None):
        """Show a success message in the log (duration parameter kept for compatibility)"""
        self.add_log_entry(message, "success")

    def show_warning_message(self, message, duration=None):
        """Show a warning message in the log (duration parameter kept for compatibility)"""
        self.add_log_entry(message, "warning")

    def show_info_message(self, message, duration=None):
        """Show an info message in the log (duration parameter kept for compatibility)"""
        self.add_log_entry(message, "info")

    def set_message(self, message, duration=None, priority=None, border_color=None):
        """Legacy method for compatibility - redirects to log system"""
        # Determine log type based on border_color if provided
        log_type = "info"
        if border_color:
            if border_color == (255, 0, 0):
                log_type = "error"
            elif border_color == (0, 255, 0):
                log_type = "success"
            elif border_color == (255, 165, 0):
                log_type = "warning"
            elif border_color == (0, 191, 255):
                log_type = "info"
        
        self.add_log_entry(message, log_type)
        self.draw_event_log()
        pygame.display.flip()

    def handle_events(self):
        """Handle pygame events (UPDATED with log scrolling support)"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.return_to_overworld:
                    # During battle integration, closing window should close entire game
                    print("[Combat] Player closed window during battle - closing entire game")
                    pygame.quit()
                    import sys
                    sys.exit(0)
                else:
                    # Standalone battle mode, just exit battle
                    self.running = False
            elif event.type == pygame.VIDEORESIZE:
                # Update screen surface to new size and recompute layout
                if not self.return_to_overworld:
                    # Only recreate display in standalone mode
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                # Always recompute layout for size changes
                self._recompute_layout()
                continue
            
            # Handle log scrolling FIRST (highest priority)
            elif self.handle_log_scroll(event):
                continue  # Log scroll was handled, skip other event processing
                
            # Handle controller input (joystick events)
            elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION, pygame.JOYAXISMOTION]:
                if self.process_controller_input(event):
                    continue  # Controller input was handled
            
            # Handle keyboard input
            elif event.type == pygame.KEYDOWN:
                self.process_keyboard_input(event)
            
            # Handle custom events for enemy AI and animation delays
            elif event.type == pygame.USEREVENT + 1:
                self.end_enemy_turn()
            elif event.type == pygame.USEREVENT + 2:
                self.execute_enemy_move()
            elif event.type == pygame.USEREVENT + 3:  # Animation completion event
                self.finish_player_attack_sequence()
            elif event.type == pygame.USEREVENT + 4:  # Player turn start indicator timer
                self.player_turn_start_active = False
                pygame.time.set_timer(pygame.USEREVENT + 4, 0)  # Clear timer

    def draw_player_turn_start_indicator(self):
        """Draw player turn start indicator with semi-transparent background in enemy panel area (SCALED)"""
        # Use EXACT same coordinates as in show_enemy_panel method
        menu_bar_width = self.sx(760)
        menu_bar_x = self.sx(310)
        menu_bar_y = self.sy(1000 - 265)  # SCREEN_HEIGHT - 265
        
        # Define enemy panel area aligned with menu bar (scaled) - EXACT COPY
        panel_x = menu_bar_x
        panel_y = self.sy(35)
        panel_width = menu_bar_width
        
        # Position at top of enemy panel area (same as enemy turn indicator)
        turn_indicator_y = panel_y + self.sy(10)
        turn_text = f"{player.name}'S TURN"  # Clean text, no symbols
        
        # Calculate text dimensions for background box
        text_surface = self.font_large.render(turn_text, True, (255, 255, 100))  # Yellow
        text_width = text_surface.get_width()
        text_height = text_surface.get_height()
        
        # Add padding around text
        padding = self.sx(20)
        bg_width = text_width + 2 * padding
        bg_height = text_height + 2 * padding
        bg_x = panel_x + panel_width//2 - bg_width//2
        bg_y = turn_indicator_y - padding
        
        # Create semi-transparent background
        bg_surface = pygame.Surface((bg_width, bg_height))
        bg_surface.set_alpha(150)  # Semi-transparent
        bg_surface.fill((0, 0, 0))  # Black background
        
        # Draw the semi-transparent background
        self.screen.blit(bg_surface, (bg_x, bg_y))
        
        # Draw border for better visibility
        pygame.draw.rect(self.screen, (255, 255, 100), (bg_x, bg_y, bg_width, bg_height), 2)  # Yellow border
        
        # Draw the turn text (centered both horizontally and vertically)
        self.draw_text(turn_text, self.font_large, (255, 255, 100),  # Yellow text
                    bg_x + bg_width//2, bg_y + bg_height//2, center=True)

    def calculate_message_size(self, lines):
        """Calculate the optimal size for the message box based on content"""
        if not lines:
            return 400, 100
        
        # Calculate width based on longest line
        max_width = 0
        total_height = 0
        line_height = 30
        
        for line in lines:
            text_surface = self.font_medium.render(line, True, WHITE)
            line_width = text_surface.get_width()
            max_width = max(max_width, line_width)
        
        # Add padding and ensure minimum/maximum sizes
        message_width = max(400, min(800, max_width + 80))  # Min 400, max 800
        message_height = max(100, len(lines) * line_height + 60)  # Min 100 + padding
        
        return message_width, message_height

    def clear_message(self):
        """Immediately clear the current message"""
        self.message_text = None
        self.message_timer = 0
        self.message_priority = 0
        print("Message cleared")

    def show_enemy_panel(self):
        """Draw enemy panel when ENEMY is selected with animated GIF and background (pygame version) - SCALED"""
        # Show enemy panel when ENEMY menu is selected OR during enemy turn OR during target selection
        should_show_enemy_panel = (
            self.menu_selection_index == 0 or  # ENEMY menu selected
            (hasattr(self, 'enemy_turn_active') and self.enemy_turn_active) or  # During enemy turn
            (hasattr(self, 'target_selection_active') and self.target_selection_active)  # During target selection
        )
        
        if should_show_enemy_panel:
            # Calculate menu bar dimensions and position (scaled)
            menu_bar_width = self.sx(760)
            menu_bar_x = self.sx(310)
            menu_bar_y = self.sy(1000 - 265)  # SCREEN_HEIGHT - 265
            
            # Define enemy panel area aligned with menu bar (scaled)
            panel_x = menu_bar_x
            panel_y = self.sy(35)
            panel_width = menu_bar_width
            panel_height = menu_bar_y - panel_y - self.sy(20)

            # Display enemy name - ALIGNED WITH BODY PARTS LIST (scaled)
            enemy_name_text = f"{enemy.name}"

            # Calculate the positions of the body parts list (scaled)
            parts_x = panel_x + panel_width + self.sx(20)  # Body parts list position
            attributes_panel_x = self.sx(1450)  # Enemy part attributes box position

            # Draw the enemy name aligned with the body parts list (scaled) - using larger font
            enemy_name_y = panel_y + self.sy(10)  # Position above body parts list
            self.draw_text(enemy_name_text, self.font_large, WHITE, parts_x, enemy_name_y)
        
            # Draw enemy background if available (scaled)
            if hasattr(self, 'enemy_background') and self.enemy_background is not None:
                # Scale the background to fit the panel
                scaled_bg = pygame.transform.scale(self.enemy_background, (panel_width, panel_height))
                self.screen.blit(scaled_bg, (panel_x, panel_y))
                
                # Optional: Add a semi-transparent overlay to make text more readable
                overlay = pygame.Surface((panel_width, panel_height))
                overlay.set_alpha(30)
                overlay.fill(BLACK)
                self.screen.blit(overlay, (panel_x, panel_y))
            else:
                # Fallback: Draw a simple background rectangle
                pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_width, panel_height))
                pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
            
            # Get current animated enemy frame and scale it proportionally
            current_enemy_frame = self.get_current_enemy_frame()
            
            # Scale enemy GIF to fit panel (max 90% of panel size, maintain aspect ratio)
            max_gif_width = int(panel_width * 0.9)
            max_gif_height = int(panel_height * 0.9)
            
            # Calculate scale factor to maintain aspect ratio
            original_width, original_height = current_enemy_frame.get_size()
            scale_x = max_gif_width / original_width
            scale_y = max_gif_height / original_height
            scale_factor = min(scale_x, scale_y)
            
            new_gif_width = int(original_width * scale_factor)
            new_gif_height = int(original_height * scale_factor)
            
            # Scale the GIF frame
            scaled_enemy_frame = pygame.transform.scale(current_enemy_frame, (new_gif_width, new_gif_height))
            
            # Calculate centered position for the scaled GIF aligned to bottom of background
            centered_gif_x = panel_x + (panel_width - new_gif_width) // 2
            # Align GIF to bottom of the background panel (with small margin)
            centered_gif_y = panel_y + panel_height - new_gif_height
            
            # Draw the scaled enemy GIF centered horizontally and aligned to bottom
            self.screen.blit(scaled_enemy_frame, (centered_gif_x, centered_gif_y))
            
            # FIXED: Draw enemy blink overlay to cover the entire background area instead of just the GIF (scaled)
            if hasattr(self, 'enemy_blink_state') and self.enemy_blink_state['active'] and self.enemy_blink_state['visible']:
                # Apply blink overlay to the entire background panel dimensions
                self.draw_blink_overlay(self.screen, panel_x, panel_y, panel_width, panel_height,
                                    self.enemy_blink_state['color'], alpha=128)
            
            # Show enemy turn indicator during enemy turn (scaled) with semi-transparent background
            if hasattr(self, 'enemy_turn_active') and self.enemy_turn_active:
                turn_indicator_y = panel_y + self.sy(10)
                turn_text = f"{enemy.name}'S TURN"  # Removed >>> and <<<
                
                # Calculate text dimensions for background box
                text_surface = self.font_large.render(turn_text, True, (255, 255, 100))  # Changed to yellow
                text_width = text_surface.get_width()
                text_height = text_surface.get_height()
                
                # Add padding around text
                padding = self.sx(20)
                bg_width = text_width + 2 * padding
                bg_height = text_height + 2 * padding
                bg_x = panel_x + panel_width//2 - bg_width//2
                bg_y = turn_indicator_y - padding
                
                # Create semi-transparent background
                bg_surface = pygame.Surface((bg_width, bg_height))
                bg_surface.set_alpha(150)  # Semi-transparent
                bg_surface.fill((0, 0, 0))  # Black background
                
                # Draw the semi-transparent background
                self.screen.blit(bg_surface, (bg_x, bg_y))
                
                # Draw border for better visibility
                pygame.draw.rect(self.screen, (255, 255, 100), (bg_x, bg_y, bg_width, bg_height), 2)  # Yellow border
                
                # Draw the turn text (centered both horizontally and vertically)
                self.draw_text(turn_text, self.font_large, (255, 255, 100),  # Yellow text
                            bg_x + bg_width//2, bg_y + bg_height//2, center=True)
            
            # Show move info during target selection (scaled)
            if hasattr(self, 'target_selection_active') and self.target_selection_active and hasattr(self, 'selected_move') and self.selected_move:
                move_info_y = panel_y + self.sy(10)
                move = self.selected_move
                
                # Format effects for display
                effects_display = []
                if hasattr(move, 'eff_appl') and move.eff_appl:
                    for effect_data in move.eff_appl:
                        if isinstance(effect_data, str):
                            effects_display.append(effect_data)
                        elif isinstance(effect_data, list) and len(effect_data) >= 4:
                            effect_name = effect_data[0]
                            level = effect_data[1]
                            duration = effect_data[2]
                            effects_display.append(f"{effect_name}(L{level},D{duration})")
                        else:
                            effects_display.append(str(effect_data))
                
                # Move information - compact display (scaled)
                move_info_text = f"MOVE: {move.name} | DMG: {move.danno} | STA: {move.stamina_cost} | ACC: {move.accuracy}%"
                self.draw_text(move_info_text, self.font_medium, WHITE, panel_x + self.sx(10), move_info_y)
                
                if effects_display:
                    effects_text = f"EFFECTS: {', '.join(effects_display)}"
                    self.draw_text(effects_text, self.font_medium, WHITE, panel_x + self.sx(10), move_info_y + self.sy(25))
                
            # Enemy body parts list positioned to the right of the main panel (scaled)
            parts_x = panel_x + panel_width + self.sx(20)
            parts_y = panel_y + self.sy(50)
            
            # Semi-transparent background for body parts list (scaled)
            parts_bg_height = len(enemy.body_parts) * self.sy(40) + self.sy(20)
            parts_bg_width = self.sx(180)  # Reduced width since no HP bars
            parts_bg_rect = pygame.Rect(parts_x - self.sx(10), parts_y - self.sy(10), parts_bg_width, parts_bg_height)
            parts_bg = pygame.Surface((parts_bg_rect.width, parts_bg_rect.height))
            parts_bg.set_alpha(128)
            parts_bg.fill(BLACK)
            self.screen.blit(parts_bg, (parts_bg_rect.x, parts_bg_rect.y))

            # Body parts list with enhanced highlighting for target selection (scaled)
            for i, part in enumerate(enemy.body_parts):
                y = parts_y + i * self.sy(40)
                
                # Determine colors and selection state
                is_target_selection = hasattr(self, 'target_selection_active') and self.target_selection_active
                is_normal_enemy_nav = (self.menu_selection_index == 0 and not is_target_selection and self.player_has_control)
                
                if is_target_selection:
                    # TARGET SELECTION MODE - Check if this target is valid for the selected move
                    move = getattr(self, 'selected_move', None)
                    target_valid = True
                    
                    if move and hasattr(move, 'reqs') and move.reqs:
                        # Check target-specific requirements
                        for req in move.reqs:
                            if req.startswith("target:") and req != f"target:{part.name.lower()}":
                                target_valid = False
                                break
                            elif req.startswith("target_status:"):
                                # Check if target has required status effect
                                required_status = req.split(":", 1)[1]
                                if not hasattr(part, 'effetti') or not part.effetti or required_status not in part.effetti:
                                    target_valid = False
                                    break
                    
                    if not target_valid:
                        # Invalid target - very dark gray
                        part_name_color = (80, 80, 80)
                    elif i == getattr(self, 'target_selection_index', 0):
                        # Selected valid target - bright red
                        part_name_color = (255, 100, 100)  # Light red text
                    else:
                        # Non-selected valid targets - normal color
                        part_name_color = (200, 200, 200)  # Light gray
                        
                elif is_normal_enemy_nav and i == self.enemy_parts_index:
                    # NORMAL ENEMY NAVIGATION MODE - Green highlighting
                    part_name_color = GREEN
                    
                else:
                    # Normal state
                    part_name_color = WHITE
                
                # Draw part name with appropriate color (scaled)
                self.draw_text(part.name, self.font_medium, part_name_color, parts_x, y)

    def load_images(self):
        """Load character GIFs and background images"""
        # ...existing background loading code...
        
        # Load status effect GIFs - GENERALIZED SYSTEM  
        try:
            # Use the main Statuses_Gifs folder
            status_gifs_folder = Path(__file__).parent.parent.parent.parent / "Statuses_Gifs"
            print(f"Loading status effect GIFs from: {status_gifs_folder}")
            
            # Initialize status frames dictionary
            self.status_frames = {}
            
            # Load all status effects from STATUS_EFFECTS_CONFIG using new naming convention
            if status_gifs_folder.exists():
                # Get all possible status effects from the config
                all_status_effects = list(STATUS_EFFECTS_CONFIG.keys())
                
                for status_name in all_status_effects:
                    # Use new naming convention: StatusName_gif.gif (capitalize first letter)
                    gif_filename = f"{status_name.capitalize()}_gif.gif"
                    gif_path = status_gifs_folder / gif_filename
                    
                    if gif_path.exists():
                        try:
                            # Load frames for this status effect (50x50 size - no scaling needed)
                            frames = self.load_gif_frames(str(gif_path), (50, 50), crop_face=False)
                            self.status_frames[status_name] = frames
                            print(f"Loaded {len(frames)} frames for {status_name} status from {gif_filename}")
                        except Exception as e:
                            print(f"Error loading {status_name} GIF: {e}")
                            # Don't load fallback here - let it be handled during display
                            continue
                    else:
                        print(f"Status GIF not found: {gif_path} - will use original GIF at runtime if available")
                        # Don't load fallback here - only load actual status GIFs
            else:
                print(f"Statuses_Gifs folder not found: {status_gifs_folder}")
                # Create minimal fallback
                self.status_frames = {}
                    
        except Exception as e:
            print(f"Error loading status effect GIFs: {e}")
            # Create minimal fallback
            self.status_frames = {}
        
        """Load character GIFs and background images"""
        # Load enemy background image randomly from Backgrounds folder
        try:
            backgrounds_folder = Path(__file__).parent / "Backgrounds"
            print(f"Looking for backgrounds in: {backgrounds_folder}")
            
            if backgrounds_folder.exists() and backgrounds_folder.is_dir():
                # Find all PNG files in the Backgrounds folder
                png_files = list(backgrounds_folder.glob("*.png"))
                
                if png_files:
                    # Randomly select one PNG file
                    import random
                    selected_background = random.choice(png_files)
                    print(f"Randomly selected background: {selected_background.name}")
                    
                    # Load the selected background
                    original_bg = pygame.image.load(str(selected_background))
                    
                    # Calculate target dimensions (aligned with menu bar)
                    menu_bar_width = 760
                    menu_bar_y = SCREEN_HEIGHT - 265
                    panel_y = 35
                    target_width = menu_bar_width
                    target_height = menu_bar_y - panel_y - 20
                    
                    # Get original dimensions
                    original_width, original_height = original_bg.get_size()
                    
                    # Calculate scale factor to maintain aspect ratio while filling the area
                    scale_x = target_width / original_width
                    scale_y = target_height / original_height
                    scale_factor = max(scale_x, scale_y)  # Use max to ensure full coverage
                    
                    # Calculate scaled dimensions
                    scaled_width = int(original_width * scale_factor)
                    scaled_height = int(original_height * scale_factor)
                    
                    # Scale the image
                    scaled_bg = pygame.transform.scale(original_bg, (scaled_width, scaled_height))
                    
                    # Calculate crop area to center the image
                    crop_x = max(0, (scaled_width - target_width) // 2)
                    crop_y = max(0, (scaled_height - target_height) // 2)
                    
                    # Crop the image to final dimensions
                    if scaled_width > target_width or scaled_height > target_height:
                        self.enemy_background = scaled_bg.subsurface(
                            pygame.Rect(crop_x, crop_y, target_width, target_height)
                        ).copy()  # Copy to create independent surface
                    else:
                        self.enemy_background = scaled_bg
                    
                    print(f"Enemy background processed: original {original_width}x{original_height} -> final {target_width}x{target_height}")
                    
                else:
                    print(f"No PNG files found in: {backgrounds_folder}")
                    self.enemy_background = None
            else:
                print(f"Backgrounds folder not found: {backgrounds_folder}")
                self.enemy_background = None
                
        except Exception as e:
            print(f"Error loading enemy background: {e}")
            self.enemy_background = None
        
        # Load player GIF frames (zoomed on head)
        try:
            self.player_frames = self.load_gif_frames(str(player.image_path), (295, 295), crop_face=True)
            print(f"Loaded {len(self.player_frames)} player GIF frames (zoomed on head)")
        except Exception as e:
            print(f"Error loading player GIF: {e}")
            # Create fallback surface
            fallback_surface = pygame.Surface((295, 295))
            fallback_surface.fill(GRAY)
            self.player_frames = [fallback_surface]
        
        # Load enemy GIF frames
        try:
            self.enemy_frames = self.load_gif_frames(str(enemy.image_path), (600, 600), crop_face=False)
            print(f"Loaded {len(self.enemy_frames)} enemy GIF frames")
        except Exception as e:
            print(f"Error loading enemy GIF: {e}")
            # Create fallback surface
            fallback_surface = pygame.Surface((400, 400))
            fallback_surface.fill(GRAY)
            self.enemy_frames = [fallback_surface]

    def load_burn_fallback(self, status_gifs_folder):
        """Load Burn_gif.gif as fallback for missing status effects"""
        burn_gif_path = status_gifs_folder / "Burn_gif.gif"
        if burn_gif_path.exists():
            try:
                frames = self.load_gif_frames(str(burn_gif_path), (50, 50), crop_face=False)
                print(f"Loaded Burn_gif.gif as fallback ({len(frames)} frames)")
                return frames
            except Exception as e:
                print(f"Error loading Burn_gif.gif fallback: {e}")
        
        # Ultimate fallback: create a simple colored rectangle at battle menu size
        surface = pygame.Surface((40, 30))
        surface.fill((255, 100, 0))  # Orange-red color like burn
        return [surface]

    def create_status_fallback(self, status_name):
        """Create a fallback surface for status effects with unique colors - DEPRECATED, should not be used anymore"""
        surface = pygame.Surface((40, 30))  # Keep original container size for battle menu
        
        # Define unique colors for each status effect
        status_colors = {   
            'burn': (255, 100, 0),           # Orange-red
            'bleed': (200, 0, 0),            # Dark red
            'poison': (100, 255, 100),       # Light green
            'stun': (150, 150, 255),         # Light blue
            'confusion': (255, 100, 255),    # Magenta
            'freeze': (100, 200, 255),       # Ice blue
            'regen': (0, 255, 0),            # Green
            'cancer': (200, 200, 200),       # Silver
            'sleep': (255, 255, 255),        # White
            'inhibition': (128, 128, 0),     # Olive
            'acid': (0, 200, 0)              # Medium green
        }
        
        color = status_colors.get(status_name, (128, 128, 128))  # Default gray
        surface.fill(color)
        return surface

    def get_current_status_frame(self, status_name):
        """Get the current animation frame for a specific status effect - ONLY return actual GIF frames"""
        if hasattr(self, 'status_frames') and status_name in self.status_frames:
            frames = self.status_frames[status_name]
            if frames:
                # Use modulo to cycle properly within available frames
                frame_index = self.player_frame_index % len(frames)
                return frames[frame_index]
        
        # If no specific GIF is found, return None - do NOT use fallbacks here
        return None

    def check_status_active(self, part, status_name):
        """Check if a specific status effect is active on a body part"""
        if not hasattr(part, 'p_eff'):
            return False
        
        effetti = part.p_eff

        status_mapping = {
        'cancer': 'cancer',
        'burn': 'burn',
        'bleed': 'bleed',
        'poison': 'poison',
        'stun': 'stun',
        'confusion': 'confusion',
        'inhibition': 'inhibition',
        'freeze': 'freeze',
        'regen': 'regen',
        'sleep': 'sleep'
        }
        
        effect_attr = status_mapping.get(status_name, status_name)
        
        if hasattr(effetti, effect_attr):
            effect_data = getattr(effetti, effect_attr)
            # Check if effect is active (level > 0 and duration > 0)
            return effect_data[1] > 0 and effect_data[2] > 0
        
        return False

    def get_active_statuses(self, part):
        """Get all active status effects for a body part"""
        active_statuses = []
        
        if not hasattr(part, 'p_eff'):
            return active_statuses
        
        effetti = part.p_eff
        
        # Get all possible status effects from STATUS_EFFECTS_CONFIG
        all_status_effects = list(STATUS_EFFECTS_CONFIG.keys())
        
        for status_name in all_status_effects:
            if hasattr(effetti, status_name):
                effect_data = getattr(effetti, status_name)
                # Check if effect is active (level > 0 and duration > 0)
                if effect_data[1] > 0 and effect_data[2] > 0:
                    # Filter out effects that shouldn't be displayed in UI
                    config = STATUS_EFFECTS_CONFIG.get(status_name, {})
                    
                    # Hide "effect_on_hit" buffs (passive abilities like sleep_spores, poison_spores)
                    if config.get('buff_type') == 'effect_on_hit':
                        continue
                    
                    # Hide property effects (instant effects like ranged, unblockable)
                    if config.get('turn_timing') == 'instant':
                        continue
                    
                    active_statuses.append({
                        'name': status_name,
                        'level': effect_data[1],
                        'duration': effect_data[2],
                        'immunity': effect_data[3]
                    })
        
        return active_statuses

    def draw_status_indicators(self, part, status_x, status_y, max_indicators_per_row=3):
        """Draw status indicators for a body part with multiple statuses support"""
        active_statuses = self.get_active_statuses(part)
        
        if not active_statuses:
            return status_y  # Return original Y position if no statuses
        
        indicator_width = 40   # Keep original container size
        indicator_height = 30  # Keep original container size
        indicator_spacing = 5
        number_width = 20  # Space for level and duration numbers on the right
        row_height = indicator_height + 20  # Space for GIF + label
        
        # Calculate how many rows we need
        rows_needed = (len(active_statuses) + max_indicators_per_row - 1) // max_indicators_per_row
        
        for row in range(rows_needed):
            for col in range(max_indicators_per_row):
                status_index = row * max_indicators_per_row + col
                
                if status_index >= len(active_statuses):
                    break
                
                status = active_statuses[status_index]
                status_name = status['name']
                
                # Calculate position for this indicator
                indicator_x = status_x + col * (indicator_width + indicator_spacing + number_width)
                indicator_y = status_y + row * row_height
                
                # Get current frame for this status - ONLY get actual GIF frames
                current_frame = self.get_current_status_frame(status_name)
                
                # Only draw if we have an actual GIF frame (no fallbacks!)
                if current_frame is not None:
                    # Create a 40x30 surface with black padding to maintain square aspect ratio
                    display_surface = pygame.Surface((indicator_width, indicator_height))
                    display_surface.fill((0, 0, 0))  # Black background
                    
                    # Calculate how to fit the 50x50 GIF into 40x30 without distortion
                    # Scale the GIF to fit the height (30 pixels) and center it horizontally
                    target_size = indicator_height  # Use height as the constraint (30 pixels)
                    scaled_gif = pygame.transform.scale(current_frame, (target_size, target_size))
                    
                    # Center the scaled GIF horizontally in the 40x30 surface
                    center_x = (indicator_width - target_size) // 2  # (40 - 30) // 2 = 5 pixels padding on each side
                    display_surface.blit(scaled_gif, (center_x, 0))
                    
                    # Draw the final surface
                    self.screen.blit(display_surface, (indicator_x, indicator_y))
                    
                    # Draw status level indicator to the RIGHT of the container (top number)
                    level_text = str(status['level'])
                    level_surface = self.font_small.render(level_text, True, WHITE)
                    level_surface.set_alpha(200)  # Semi-transparent
                    # Position level indicator to the right of the container (top)
                    level_x = indicator_x + indicator_width + 2  # 2 pixels spacing from container
                    level_y = indicator_y + 2  # Top position
                    self.screen.blit(level_surface, (level_x, level_y))
                    
                    # Draw status duration indicator to the RIGHT of the container (bottom number)
                    from Status_Effects_Config import should_show_effect_duration
                    
                    # Check if this effect should show duration (sleep effects show "-" instead of 999)
                    if should_show_effect_duration(status_name):
                        duration_text = str(status['duration'])
                    else:
                        duration_text = "-"  # Show "-" for effects with infinite/hidden duration like sleep
                    
                    duration_surface = self.font_small.render(duration_text, True, (255, 255, 100))  # Yellow for duration
                    duration_surface.set_alpha(200)  # Semi-transparent
                    # Position duration indicator to the right of the container (bottom)
                    duration_x = indicator_x + indicator_width + 2  # 2 pixels spacing from container
                    duration_y = indicator_y + indicator_height - 12  # Bottom position (12 pixels from bottom)
                    self.screen.blit(duration_surface, (duration_x, duration_y))
                
                # Draw small label under the status GIF
                label_y = indicator_y + indicator_height + 2
                label_text = status_name[:4].upper()  # First 4 characters
                label_color = WHITE
                
                # Color-code labels based on status type
                if status_name in ['burn', 'bleed', 'poison', 'toxin', 'cancer', 'acid', 'custom_poison']:
                    label_color = (255, 100, 100)  # Light red for damage effects
                elif status_name in ['heal', 'regeneration']:
                    label_color = (100, 255, 100)  # Light green for healing effects
                elif status_name in ['inhibition', 'freeze', 'frost', 'stun', 'confusion', 'sleep', 'paralysis', 'weakness']:
                    label_color = (100, 255, 255)  # Cyan for control/debuff effects
                elif status_name in ['fine_dust', 'fry_neurons', 'amputate', 'mess_up']:
                    label_color = (255, 200, 100)  # Orange for special/unique effects
                elif status_name.startswith('buf_'):
                    label_color = (255, 255, 100)  # Yellow for buff effects
                else:
                    label_color = WHITE  # Default white for any new/unknown effects
                
                # self.draw_text(label_text, self.font_small, label_color, 
                            # indicator_x + indicator_width // 2, label_y, center=True)
        
        # Return new Y position after all status indicators
        return status_y + rows_needed * row_height

    def draw_inactive_status_preview(self, part, status_x, status_y):
        """Draw greyed out preview of potential status effects (optional feature)"""
        # This could show what status effects could potentially affect this body part
        # For now, just show a simple "no effects" indicator
        
        active_statuses = self.get_active_statuses(part)
        if active_statuses:
            return status_y  # Don't show preview if there are active statuses
        
        # Show a simple "no effects" indicator
        no_effects_surface = pygame.Surface((40, 30))
        no_effects_surface.fill((64, 64, 64))  # Dark gray
        no_effects_surface.set_alpha(100)  # Very transparent
        
        self.screen.blit(no_effects_surface, (status_x, status_y))
        self.draw_text("---", self.font_small, GRAY, status_x + 20, status_y + 35, center=True)
        
        return status_y + 50

    def crop_face_area(self, pil_image):
        """
        Crop the image to focus on the head/face area (middle-top portion).
        Zooms in by 2x and focuses on the top-middle area.
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            PIL Image object cropped to face area
        """
        width, height = pil_image.size
        
        # Calculate crop area to zoom in by 2x on the middle-top portion
        # We want to crop a region that's 50% of original size (2x zoom)
        crop_width = width // 2
        crop_height = height // 2
        
        # Position the crop area in the middle horizontally and from the very top vertically
        # Start from 25% from left (to center horizontally)
        left = width // 4
        # Start from the very top (no padding)
        top = 0
        
        # Calculate right and bottom bounds
        right = left + crop_width
        bottom = top + crop_height
        
        # Ensure bounds don't exceed image dimensions
        right = min(right, width)
        bottom = min(bottom, height)
        
        # Crop the image
        cropped = pil_image.crop((left, top, right, bottom))
        
        print(f"Cropped player image from {width}x{height} to {right-left}x{bottom-top} (head focus)")
        
        return cropped

    def load_gif_frames(self, gif_path, target_size, crop_face=False):
        """
        Load all frames from a GIF file and convert them to pygame surfaces
        
        Args:
            gif_path (str): Path to the GIF file
            target_size (tuple): Target size (width, height) for resizing
            crop_face (bool): If True, crop to focus on the upper portion (face area)
        
        Returns:
            list: List of pygame.Surface objects
        """
        frames = []
        
        try:
            # Open the GIF using PIL
            with Image.open(gif_path) as img:
                # Get the frame duration (in milliseconds)
                self.frame_duration = img.info.get('duration', 100)
                
                # Extract all frames
                frame_count = 0
                while True:
                    try:
                        # Convert frame to RGBA mode for better compatibility
                        frame = img.copy().convert("RGBA")
                        
                        # Crop to face area if requested
                        if crop_face:
                            frame = self.crop_face_area(frame)
                        
                        # Resize frame to target size
                        frame = frame.resize(target_size, Image.BICUBIC)

                        # Convert PIL image to pygame surface
                        frame_data = frame.tobytes()
                        pygame_surface = pygame.image.fromstring(frame_data, target_size, "RGBA")
                        
                        frames.append(pygame_surface)
                        frame_count += 1
                        
                        # Move to next frame
                        img.seek(frame_count)
                        
                    except EOFError:
                        # End of GIF reached
                        break
                
                print(f"Successfully loaded {len(frames)} frames from {gif_path}")
                
        except Exception as e:
            print(f"Error loading GIF frames from {gif_path}: {e}")
            # Create a single fallback frame
            fallback_surface = pygame.Surface(target_size)
            fallback_surface.fill(GRAY)
            frames = [fallback_surface]
        
        return frames if frames else [pygame.Surface(target_size)]

    def update_animation_frames(self):
        """Update GIF animation frames based on time"""
        current_time = pygame.time.get_ticks()
        
        if current_time - self.last_frame_time >= self.frame_duration:
            # Update player frame
            if len(self.player_frames) > 1:
                self.player_frame_index = (self.player_frame_index + 1) % len(self.player_frames)
            
            # Update enemy frame
            if len(self.enemy_frames) > 1:
                if current_time >= getattr(self, 'enemy_animation_paused_until', 0):
                    self.enemy_frame_index = (self.enemy_frame_index + 1) % len(self.enemy_frames)
            
            self.last_frame_time = current_time

    def get_current_player_frame(self):
        """Get the current player animation frame"""
        if self.player_frames and 0 <= self.player_frame_index < len(self.player_frames):
            return self.player_frames[self.player_frame_index]
        else:
            # Fallback
            surface = pygame.Surface((295, 295))
            surface.fill(GRAY)
            return surface

    def get_current_enemy_frame(self):
        """Get the current enemy animation frame"""
        if self.enemy_frames and 0 <= self.enemy_frame_index < len(self.enemy_frames):
            return self.enemy_frames[self.enemy_frame_index]
        else:
            # Fallback
            surface = pygame.Surface((400, 400))
            surface.fill(GRAY)
            return surface

    def calculate_message_size(self, lines):
        """Calculate the optimal size for the message box based on content"""
        if not lines:
            return 400, 100
        
        # Calculate width based on longest line
        max_width = 0
        line_height = 30
        
        for line in lines:
            text_surface = self.font_medium.render(line, True, WHITE)
            line_width = text_surface.get_width()
            max_width = max(max_width, line_width)
        
        # Add padding and ensure minimum/maximum sizes
        message_width = max(400, min(800, max_width + 80))  # Min 400, max 800
        message_height = max(100, len(lines) * line_height + 60)  # Min 100 + padding
        
        return message_width, message_height

    def set_message(self, message, duration=3000, priority=1, border_color=None):
        """Set a temporary message with enhanced styling and priority system"""
        current_time = pygame.time.get_ticks()
        
        # Check if this message should override the current one
        if hasattr(self, 'message_priority') and priority < self.message_priority:
            print(f"Message blocked: priority {priority} < current {self.message_priority}")
            return
        
        # Set message properties
        self.message_text = message
        self.message_timer = current_time + duration
        self.message_priority = priority
        
        # Set fade timing (start fading in the last 500ms)
        if not hasattr(self, 'message_fade_duration'):
            self.message_fade_duration = 500
        self.message_fade_start = self.message_timer - self.message_fade_duration
        
        # Set styling
        self.message_border_color = border_color if border_color else YELLOW
        self.message_background_color = BLACK
        
        print(f"Message set: '{message}' (priority: {priority}, duration: {duration}ms)")

    def show_error_message(self, message, duration=3000):
        """Show an error message with red styling"""
        self.set_message(message, duration, priority=5, border_color=(255, 0, 0))

    def show_success_message(self, message, duration=2000):
        """Show a success message with green styling"""
        self.set_message(message, duration, priority=3, border_color=(0, 255, 0))

    def show_warning_message(self, message, duration=2500):
        """Show a warning message with orange styling"""
        self.set_message(message, duration, priority=4, border_color=(255, 165, 0))

    def show_info_message(self, message, duration=1500):
        """Show an info message with blue styling"""
        self.set_message(message, duration, priority=2, border_color=(0, 191, 255))

    def draw_text(self, text, font, color, x, y, center=False):
        """Helper function to draw text"""
        text_surface = font.render(text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, (x, y))
        return text_surface.get_rect()
    
    def draw_body_panel(self):
        """Draw the left body panel with HP bars and animated player image at bottom (SCALED)"""
        panel_x = self.sx(10)
        panel_y = self.sy(10)
        panel_width = self.sx(280)
        panel_height = self.current_height - self.sy(20)
        
        # Draw panel background (scaled)
        pygame.draw.rect(self.screen, BLACK, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Calculate space needed for body parts (scaled)
        body_parts_count = len(player.body_parts)
        part_height = self.sy(90)  # Increased from 75 to accommodate multiple status rows
        total_parts_height = body_parts_count * part_height + self.sy(30)  # +30 for top padding
        
        # Calculate remaining space for player image (scaled)
        available_image_height = panel_height - total_parts_height - self.sy(20)  # -20 for bottom padding
        
        # Get current animated frame
        current_player_frame = self.get_current_player_frame()
        original_img_width, original_img_height = current_player_frame.get_size()
        max_img_width = panel_width - self.sx(30)  # Leave 15px margin on each side
        max_img_height = max(self.sy(100), available_image_height)  # Minimum 100px height
        
        # Calculate scaled dimensions maintaining aspect ratio
        scale_factor = min(max_img_width / original_img_width, max_img_height / original_img_height)
        img_width = int(original_img_width * scale_factor)
        img_height = int(original_img_height * scale_factor)
        
        # Scale the current player frame
        scaled_player_frame = pygame.transform.scale(current_player_frame, (img_width, img_height))
        
        # Draw body parts with regeneration highlighting and generalized status indicators (scaled)
        y_offset = self.sy(15)
        for idx, part in enumerate(player.body_parts):
            # Determine text color based on regeneration mode
            if getattr(self, 'regeneration_mode_active', False):
                if idx == getattr(self, 'regeneration_selection_index', 0):
                    part_name_color = GREEN  # Highlight selected part in regeneration mode
                else:
                    part_name_color = WHITE  # Normal color for non-selected parts
            else:
                part_name_color = WHITE  # Normal color when not in regeneration mode
            
            # Part name with appropriate color (scaled)
            self.draw_text(part.name, self.font_large, part_name_color, panel_x + panel_width // 2, panel_y + y_offset + self.sy(10), center=True)
            
            # HP bar (scaled)
            bar_y = panel_y + y_offset + self.sy(25)
            bar_width = self.sx(250)
            bar_height = self.sy(20)
            
            # Background bar (scaled)
            pygame.draw.rect(self.screen, DARK_GRAY, (panel_x + self.sx(15), bar_y, bar_width, bar_height))
            
            # Health fill (scaled)
            if part.max_p_pvt > 0:
                fill_width = int(bar_width * part.p_pvt / part.max_p_pvt)
                pygame.draw.rect(self.screen, GREEN, (panel_x + self.sx(15), bar_y, fill_width, bar_height))
            
            # HP text - centered with bar and using / format (scaled)
            hp_text = f"{part.p_pvt}/{part.max_p_pvt}"
            bar_center_x = panel_x + self.sx(15) + bar_width // 2  # Center of the HP bar
            bar_center_y = bar_y + bar_height // 2  # Center of the HP bar
            self.draw_text(hp_text, self.font_small, WHITE, bar_center_x, bar_center_y, center=True)
            
            # Status indicators: Multiple status effects below HP bar (scaled)
            status_y = bar_y + self.sy(25)  # Position below HP bar
            status_x = panel_x + self.sx(20)  # Left-aligned with some margin
            
            # Draw all active status indicators for this body part
            final_y = self.draw_status_indicators(part, status_x, status_y, max_indicators_per_row=3)
            
            # If no active statuses, optionally show preview (commented out by default)
            # if final_y == status_y:
               # final_y = self.draw_inactive_status_preview(part, status_x, status_y)
            
            y_offset += part_height  # Use increased part height
        
        # Draw animated player image at the bottom of the panel (scaled)
        img_x = panel_x + (panel_width - img_width) // 2  # Center horizontally
        img_y = panel_y + panel_height - img_height - self.sy(10)  # Position at bottom with scaled margin
        
        # Draw a background for the image (scaled)
        pygame.draw.rect(self.screen, DARK_GRAY, (img_x - self.sx(5), img_y - self.sy(5), img_width + self.sx(10), img_height + self.sy(10)))
        pygame.draw.rect(self.screen, WHITE, (img_x - self.sx(5), img_y - self.sy(5), img_width + self.sx(10), img_height + self.sy(10)), 1)
        
        # Draw the current animated player frame
        self.screen.blit(scaled_player_frame, (img_x, img_y))

        # Draw player blink overlay if active
        if hasattr(self, 'player_blink_state') and self.player_blink_state['active'] and self.player_blink_state['visible']:
            self.draw_blink_overlay(self.screen, img_x, img_y, img_width, img_height, 
                                self.player_blink_state['color'], alpha=128)

        # Draw player name and turn info above the image (scaled)
        name_y = img_y - self.sy(25)
        turn_y = name_y - self.sy(25)
        self.draw_text(player.name, self.font_big, WHITE, panel_x + panel_width // 2, name_y, center=True)
        turn_text = f"TURN: {Turn}"
        self.draw_text(turn_text, self.font_big, YELLOW, panel_x + panel_width // 2, turn_y, center=True)

    def draw_enemy_panel(self):
        """Draw enemy panel when ENEMY is selected with animated GIF and background"""
        if self.menu_selection_index == 0:
            # Define enemy panel area
            enemy_x = 410
            enemy_y = 35
            panel_width = 900
            panel_height = 900
            target_height = SCREEN_HEIGHT - 250 - enemy_y

            # Draw enemy background if available
            if self.enemy_background is not None:
                # Draw background image
                bg_rect = pygame.Rect(enemy_x - 100, enemy_y, panel_width, panel_height)
                self.screen.blit(self.enemy_background, bg_rect)
                
                # Optional: Add a semi-transparent overlay to make text more readable
                overlay = pygame.Surface((panel_width, panel_height))
                overlay.set_alpha(50)  # Adjust transparency (0-255)
                overlay.fill(BLACK)
                self.screen.blit(overlay, (enemy_x - 100, enemy_y))
            else:
                # Fallback: Draw a simple background rectangle
                pygame.draw.rect(self.screen, DARK_GRAY, (enemy_x - 100, enemy_y, panel_width, panel_height))
                pygame.draw.rect(self.screen, WHITE, (enemy_x - 100, enemy_y, panel_width, panel_height), 2)
            
            # Get current animated enemy frame
            current_enemy_frame = self.get_current_enemy_frame()
            enemy_gif_width, enemy_gif_height = current_enemy_frame.get_size()
            
            bg_x = enemy_x - 100
            bg_y = enemy_y
            bg_width = panel_width
            bg_height = panel_height

            centered_gif_x = bg_x + (bg_width - enemy_gif_width) // 2
            centered_gif_y = target_height - enemy_gif_height  # Position above bottom edge

            # Draw the enemy GIF
            self.screen.blit(current_enemy_frame, (centered_gif_x - 80, centered_gif_y))

            # Draw enemy blink overlay if active
            if hasattr(self, 'enemy_blink_state') and self.enemy_blink_state['active'] and self.enemy_blink_state['visible']:
                self.draw_blink_overlay(self.screen, centered_gif_x - 80, centered_gif_y, enemy_gif_width, enemy_gif_height,
                                       self.enemy_blink_state['color'], alpha=128)

            # Center the enemy name with the GIF
            # Calculate the center X position of the GIF
            # gif_center_x = centered_gif_x + (enemy_gif_width // 2)

            # Position the name below the GIF, centered with it
            # name_y = centered_gif_y + enemy_gif_height + 10  # 10px gap below GIF

            # Draw enemy name centered with the GIF
            # self.draw_text(enemy.name, self.font_big, WHITE, gif_center_x, name_y, center=True)
            
            # Enemy body parts list with background
            parts_x = enemy_x + 700
            parts_y = enemy_y + 150
            
            # Semi-transparent background for body parts list
            parts_bg_rect = pygame.Rect(parts_x - 10, parts_y - 10, 200, len(enemy.body_parts) * 40 + 20)
            parts_bg = pygame.Surface((parts_bg_rect.width, parts_bg_rect.height))
            parts_bg.set_alpha(128)
            parts_bg.fill(BLACK)
            self.screen.blit(parts_bg, (parts_bg_rect.x, parts_bg_rect.y))
            
            for i, part in enumerate(enemy.body_parts):
                y = parts_y + i * 40
                color = GREEN if i == self.enemy_parts_index else WHITE
                self.draw_text(part.name, self.font_big, color, parts_x, y)
                
                # Draw selection triangle
                if i == self.enemy_parts_index:
                    triangle_points = [(parts_x - 20, y), (parts_x - 20, y + 20), (parts_x - 5, y + 10)]
                    pygame.draw.polygon(self.screen, WHITE, triangle_points)

    def blink_player(self, blink_color=(255, 0, 0), blink_duration=100, blink_count=3):
        """Convenience function to blink the player character (pygame version)"""
        self.blink_character_gif("player", blink_color, blink_duration, blink_count)

    def blink_enemy(self, blink_color=(255, 0, 0), blink_duration=300, blink_count=3):
        """Convenience function to blink the enemy character (pygame version)"""
        self.blink_character_gif("enemy", blink_color, blink_duration, blink_count)

    def check_win_loss(self):
        # Check BODY HP for both player and enemy
        player_body = next((p for p in player.body_parts if p.name.upper() == "BODY"), None)
        enemy_body = next((p for p in enemy.body_parts if p.name.upper() == "BODY"), None)
        if player_body and player_body.p_pvt <= 0:
            if self.return_to_overworld:
                self.combat_result = 'enemy_win'
                self.show_end_message(f"{enemy.name} defeated You!")
                self.running = False
            else:
                self.show_end_message(f"{enemy.name} defeated You!")
            return True
        if enemy_body and enemy_body.p_pvt <= 0:
            # Start non-blocking victory sequence
            now = pygame.time.get_ticks()
            self.victory['active'] = True
            self.victory['winner'] = 'player'
            self.victory['phase'] = 'freeze'
            self.victory['phase_end'] = now + 500  # 0.5s
            self.victory['blink_started'] = False
            self.victory['fade_start'] = 0
            self.victory['alpha'] = 255
            # Pause enemy animation until end of freeze
            self.enemy_animation_paused_until = self.victory['phase_end']
            
            # CRITICAL: Set combat result immediately for overworld integration
            if self.return_to_overworld:
                self.combat_result = 'player_win'
                print(f"[Victory] Combat result set to 'player_win' for overworld return")
            
            return True
        return False

    def show_end_message(self, message):
        # Draw big centered message 
        self.screen.fill((0,0,0))
        big_font = pygame.font.Font(str(self._font_path), 60)
        rendered = big_font.render(message, True, (255,255,0))
        text_rect = rendered.get_rect(center=(self.current_width//2, self.current_height//2))
        self.screen.blit(rendered, text_rect)
        pygame.display.flip()
        
        # Only wait and quit if not returning to overworld
        if not self.return_to_overworld:
            pygame.time.wait(2000)
            pygame.quit()
            sys.exit()
        else:
            pygame.time.wait(1500)  # Shorter wait for overworld integration

    def update(self):
        """Update game state"""
        # Handle auto-starting enemy turn if enemy goes first
        if hasattr(self, 'auto_start_enemy_turn') and self.auto_start_enemy_turn:
            self.auto_start_enemy_turn = False
            print(f"🤖 AUTO-STARTING ENEMY TURN (enemy is faster)")
            # Start the full enemy turn sequence - but skip the player turn end part
            self.start_first_enemy_turn()
        
        # Update animation frames
        self.update_animation_frames()
        # Update blink states
        self.update_blink_states()
        # Update character stats
        update_all_characters_stats()
        # Check win/loss condition
        if not self.victory['active']:
            self.check_win_loss()
        else:
            # Progress victory phases
            now = pygame.time.get_ticks()
            if self.victory['phase'] == 'freeze' and now >= self.victory['phase_end']:
                # Start blink for 1s @ 2Hz
                self.victory['phase'] = 'blink'
                self.victory['phase_end'] = now + 1000
                self.blink_character_gif('enemy', (255, 255, 255), 500, 2)
            elif self.victory['phase'] == 'blink' and now >= self.victory['phase_end']:
                # Start fade
                self.victory['phase'] = 'fade'
                self.victory['fade_start'] = now
            elif self.victory['phase'] == 'fade':
                elapsed = now - self.victory['fade_start']
                if elapsed >= self.victory['fade_duration']:
                    # Fade completed -> wait extra 0.7s then show message
                    self.victory['phase'] = 'post_fade_wait'
                    self.victory['phase_end'] = now + 700
                else:
                    # Compute alpha for drawing overlay in draw()
                    self.victory['alpha'] = max(0, int(255 * (1 - elapsed / self.victory['fade_duration'])))
            elif self.victory['phase'] == 'post_fade_wait' and now >= self.victory['phase_end']:
                if not self.victory['message_shown']:
                    self.victory['message_shown'] = True
                    self.show_end_message(f"You defeated {enemy.name}")
                    # After message, ensure battle ends properly
                    if self.return_to_overworld:
                        print(f"[Victory] Ending battle with result: {self.combat_result}")
                        self.running = False
        
        # Periodic event log update every 0.5 seconds
        current_time = pygame.time.get_ticks()
        if current_time - self.last_log_update > 500:
            self.draw_event_log()
            pygame.display.flip()
            self.last_log_update = current_time

    def draw_stats_panel(self):
        """Draw the stats panel with character stats (SCALED)"""
        stats_x = self.sx(310)
        stats_y = self.sy(840)
        stats_width = self.sx(760)
        stats_height = self.sy(140)
        
        # Draw stats panel background (scaled)
        pygame.draw.rect(self.screen, BLACK, (stats_x, stats_y, stats_width, stats_height))
        pygame.draw.rect(self.screen, WHITE, (stats_x, stats_y, stats_width, stats_height), 2)
        
        # Player stats section (scaled)
        player_section_x = stats_x + self.sx(10)
        player_section_y = stats_y + self.sy(10)
        
        # Player name (scaled)
        self.draw_text(f"{player.name} STATS", self.font_medium, WHITE, player_section_x - self.sx(25) + stats_width/2, player_section_y+self.sy(10), center=True)

        # Player stats in columns (scaled)
        col1_x = player_section_x
        col2_x = player_section_x + self.sx(400)
        col3_x = col2_x + self.sx(100)
        col4_x = col3_x + self.sx(50)
        col5_x = col4_x + self.sx(80)  # New column for DODGE/SHIELD
        stat_y = player_section_y + self.sy(30)

        forz_buff = get_character_buff_level(player, 'forz')
        des_buff = get_character_buff_level(player, 'des')
        spe_buff = get_character_buff_level(player, 'spe')
        vel_buff = get_character_buff_level(player, 'vel')
        
        # Get DODGE and SHIELD buff levels
        dodge_level = 0
        shield_level = 0
        
        if hasattr(player, 'buffs'):
            if hasattr(player.buffs, 'buf_dodge'):
                dodge_data = getattr(player.buffs, 'buf_dodge')
                if len(dodge_data) >= 2 and dodge_data[2] > 0:  # Active buff
                    try:
                        dodge_level = int(dodge_data[1]) if isinstance(dodge_data[1], str) else dodge_data[1]
                    except (ValueError, TypeError):
                        dodge_level = 0
            
            if hasattr(player.buffs, 'buf_shield'):
                shield_data = getattr(player.buffs, 'buf_shield')
                if len(shield_data) >= 2 and shield_data[2] > 0:  # Active buff
                    try:
                        shield_level = int(shield_data[1]) if isinstance(shield_data[1], str) else shield_data[1]
                    except (ValueError, TypeError):
                        shield_level = 0
        
        # Health bar dimensions (scaled)
        bar_width = self.sx(180)
        bar_height = self.sy(12)
        bar_offset_x = self.sx(50)  # Space between text and bar
        
        # Column 1: HPS, REG, RES with health bars (scaled)
        # HPS (Health Points)
        hps_text = f"HPS: {int(player.pvt)}/{int(player.max_pvt)}"
        self.draw_text(hps_text, self.font_small, WHITE, col1_x, stat_y)

        # HPS health bar (scaled)
        hps_bar_x = col1_x + bar_offset_x + self.sx(80)
        hps_bar_y = stat_y + self.sy(2)
        pygame.draw.rect(self.screen, DARK_GRAY, (hps_bar_x, hps_bar_y, bar_width, bar_height))
        if player.max_pvt > 0:
            hps_fill_width = int(bar_width * player.pvt / player.max_pvt)
            pygame.draw.rect(self.screen, RED, (hps_bar_x, hps_bar_y, hps_fill_width, bar_height))
        
        # REG (Regeneration) (scaled)
        reg_text = f"REG: {int(player.rig)}/{int(player.max_rig)}"
        self.draw_text(reg_text, self.font_small, WHITE, col1_x, stat_y + self.sy(25))
        
        # REG health bar (scaled)
        reg_bar_x = col1_x + bar_offset_x + self.sx(80)
        reg_bar_y = stat_y + self.sy(25) + self.sy(2)
        pygame.draw.rect(self.screen, DARK_GRAY, (reg_bar_x, reg_bar_y, bar_width, bar_height))
        if player.max_rig > 0:
            reg_fill_width = int(bar_width * player.rig / player.max_rig)
            pygame.draw.rect(self.screen, (0, 191, 255), (reg_bar_x, reg_bar_y, reg_fill_width, bar_height))  # Light blue color

        # RES (Resistance/Resources) (scaled)
        res_text = f"RES: {int(player.res)}/{int(player.max_res)}"
        self.draw_text(res_text, self.font_small, WHITE, col1_x, stat_y + self.sy(50))
        
        # RES health bar (scaled)
        res_bar_x = col1_x + bar_offset_x + self.sx(80)
        res_bar_y = stat_y + self.sy(50) + self.sy(2)
        pygame.draw.rect(self.screen, DARK_GRAY, (res_bar_x, res_bar_y, bar_width, bar_height))
        if player.max_res > 0:
            res_fill_width = int(bar_width * player.res / player.max_res)
            pygame.draw.rect(self.screen, (255, 200, 0), (res_bar_x, res_bar_y, res_fill_width, bar_height))  # Orange color

        # STA (Stamina) (scaled)
        sta_text = f"STA: {int(player.sta)}/{int(player.max_sta)}"
        self.draw_text(sta_text, self.font_small, WHITE, col1_x, stat_y + self.sy(75))
        
        # STA health bar (scaled)
        sta_bar_x = col1_x + bar_offset_x + self.sx(80)
        sta_bar_y = stat_y + self.sy(75) + self.sy(2)
        pygame.draw.rect(self.screen, DARK_GRAY, (sta_bar_x, sta_bar_y, bar_width, bar_height))
        if player.max_sta > 0:
            sta_fill_width = int(bar_width * player.sta / player.max_sta)
            pygame.draw.rect(self.screen, GREEN, (sta_bar_x, sta_bar_y, sta_fill_width, bar_height))  # Green color

        # Column 2: STR, DEX, SPE, VEL (no bars needed for these stats) (scaled)
        self.draw_text(f"STR: {int(player.forz)}", self.font_small, WHITE, col2_x, stat_y)
        self.draw_text(f"DEX: {int(player.des)}", self.font_small, WHITE, col2_x, stat_y + self.sy(25))
        self.draw_text(f"SPE: {int(player.spe)}", self.font_small, WHITE, col2_x, stat_y + self.sy(50))
        self.draw_text(f"VEL: {int(player.vel)}", self.font_small, WHITE, col2_x, stat_y + self.sy(75))

        # Color buffs/debuffs (green for positive, red for negative, gray for zero)
        def get_buff_color(buff_level):
            if buff_level > 0:
                return GREEN
            elif buff_level < 0:
                return RED
            else:
                return GRAY

        # Display buff levels with appropriate colors (scaled)
        self.draw_text(f"{forz_buff:+d}" if forz_buff != 0 else "0", self.font_small, get_buff_color(forz_buff), col3_x, stat_y)
        self.draw_text(f"{des_buff:+d}" if des_buff != 0 else "0", self.font_small, get_buff_color(des_buff), col3_x, stat_y + self.sy(25))
        self.draw_text(f"{spe_buff:+d}" if spe_buff != 0 else "0", self.font_small, get_buff_color(spe_buff), col3_x, stat_y + self.sy(50))
        self.draw_text(f"{vel_buff:+d}" if vel_buff != 0 else "0", self.font_small, get_buff_color(vel_buff), col3_x, stat_y + self.sy(75))
    
        final_forz = player.max_for + (forz_buff * STAT_SCALING_FACTORS['forz'])
        final_des = player.max_des + (des_buff * STAT_SCALING_FACTORS['des'])
        final_spe = player.max_spe + (spe_buff * STAT_SCALING_FACTORS['spe'])
        final_vel = player.max_vel + (vel_buff * STAT_SCALING_FACTORS['vel'])

        self.draw_text(f"{int(final_forz)}", self.font_small, YELLOW, col4_x, stat_y)
        self.draw_text(f"{int(final_des)}", self.font_small, YELLOW, col4_x, stat_y + self.sy(25))
        self.draw_text(f"{int(final_spe)}", self.font_small, YELLOW, col4_x, stat_y + self.sy(50))
        self.draw_text(f"{int(final_vel)}", self.font_small, YELLOW, col4_x, stat_y + self.sy(75))
        
        # Column 5: DODGE and SHIELD buffs
        def get_defensive_buff_color(buff_level):
            if buff_level > 0:
                return (100, 255, 255)  # Light cyan for active defensive buffs
            else:
                return GRAY
        
        self.draw_text("DODGE:", self.font_small, WHITE, col5_x, stat_y)
        self.draw_text(f"{dodge_level}" if dodge_level > 0 else "0", self.font_small, get_defensive_buff_color(dodge_level), col5_x + self.sx(55), stat_y)

        self.draw_text("SHIELD:", self.font_small, WHITE, col5_x, stat_y + self.sy(25))
        self.draw_text(f"{shield_level}" if shield_level > 0 else "0", self.font_small, get_defensive_buff_color(shield_level), col5_x + self.sx(55), stat_y + self.sy(25))

    def draw_menu_bar(self):
        """Draw the main menu bar (SCALED)"""
        menu_x = self.sx(310)
        menu_y = self.sy(1000 - 265)  # SCREEN_HEIGHT - 265
        menu_width = self.sx(760)
        menu_height = self.sy(80)
        
        # Draw menu background (scaled)
        pygame.draw.rect(self.screen, BLACK, (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, WHITE, (menu_x, menu_y, menu_width, menu_height), 2)
        
        # Calculate menu item positions (scaled)
        item_width = menu_width // len(self.menu_labels)
        
        for i, label in enumerate(self.menu_labels):
            item_x = menu_x + i * item_width
            item_center_x = item_x + item_width // 2
            item_center_y = menu_y + menu_height // 2
            
            # Highlight selected menu item (scaled)
            if i == self.menu_selection_index:
                # Draw selection background
                pygame.draw.rect(self.screen, DARK_GRAY, (item_x + self.sx(5), menu_y + self.sy(5), item_width - self.sx(10), menu_height - self.sy(10)))
                color = YELLOW
            else:
                color = WHITE
            
            # Draw menu label
            self.draw_text(label, self.font_large, color, item_center_x, item_center_y, center=True)

    def draw_moves_panel(self):
        """Draw moves panel when MOVES is selected (SCALED) - FINAL VISUALS"""
        if self.menu_selection_index == 1:
            # Align with menu bar
            menu_x = self.sx(310)
            menu_y = self.sy(1000 - 265)
            menu_width = self.sx(760)
            menu_height = self.sy(80)

            # Panel bounds: start at same y as body panel, end just above menu bar
            panel_x = menu_x
            panel_width = menu_width
            top_margin = self.sy(10)
            bottom_margin = self.sy(15)
            panel_y = top_margin
            panel_height = menu_y - top_margin - bottom_margin

            # Draw white border box
            pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
            pygame.draw.rect(self.screen, BLACK, (panel_x + 2, panel_y + 2, panel_width - 4, panel_height - 4))

            # Title positioning (aligned with menu bar)
            title_x = panel_x + self.sx(20)
            title_y = panel_y + self.sy(15)
            self.draw_text(f"{player.name}'s Moves", self.font_large, WHITE, title_x, title_y)

            if hasattr(player, 'moves') and player.moves:
                # Calculate scrolling parameters with proper height management
                move_height = self.sy(80)  # Total height for each move entry including all lines
                move_spacing = self.sy(15)  # Increased spacing between moves for better readability
                content_start_y = title_y + self.sy(45)
                content_height = panel_height - (content_start_y - panel_y) - self.sy(20)
                
                # Calculate how many moves can fit properly (each move needs 6 lines of text)
                single_line_height = self.sy(20)  # Increased line height for better spacing
                lines_per_move = 6  # 6 lines per move (name, scaling, requirements, effects, elements, spacing)
                total_move_height = lines_per_move * single_line_height
                max_visible_moves = max(1, int(content_height // total_move_height))

                # Initialize scroll offset if not exists
                if not hasattr(self, 'moves_scroll_offset'):
                    self.moves_scroll_offset = 0

                # Adjust scroll offset based on current selection
                if self.moves_selection_index < self.moves_scroll_offset:
                    self.moves_scroll_offset = self.moves_selection_index
                elif self.moves_selection_index >= self.moves_scroll_offset + max_visible_moves:
                    self.moves_scroll_offset = self.moves_selection_index - max_visible_moves + 1

                # Clamp scroll offset
                max_scroll = max(0, len(player.moves) - max_visible_moves)
                self.moves_scroll_offset = max(0, min(self.moves_scroll_offset, max_scroll))

                # Draw visible moves
                for i in range(max_visible_moves):
                    move_index = i + self.moves_scroll_offset
                    if move_index >= len(player.moves):
                        break

                    move = player.moves[move_index]
                    # Position calculation for this move
                    y = content_start_y + i * total_move_height

                    # Check if move requirements are met
                    can_use, failed_requirements = check_move_requirements(player, move)
                    is_selected = move_index == self.moves_selection_index

                    # Color selection: selected move is red, others white/gray
                    base_color = RED if is_selected else (WHITE if can_use else GRAY)

                    # Calculate actual stamina cost with requirement reductions
                    actual_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs, move.accuracy)

                    # Move name and basic info (line 1)
                    if move.tipo == "BUF":
                        # For BUF moves: only show Type, name, stamina cost, element (no damage, accuracy, scaling, duration)
                        move_text = f"{move.name} ({move.tipo}) - STA: {actual_cost}"
                    else:
                        # For ATK/REA moves: show all info as before
                        move_text = f"{move.name} ({move.tipo}) - DMG: {move.danno}, STA: {actual_cost}, ACC: {move.accuracy}%"
                    self.draw_text(move_text, self.font_large, base_color, title_x, y)

                    # For BUF moves, show ACTIVE/INACTIVE status instead of scaling
                    if move.tipo == "BUF":
                        # Check if the buff effects are actually active in the character
                        buff_actually_active = False
                        effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
                        
                        # FIRST: Check the new active_buff_moves system for this specific move
                        if hasattr(player, 'active_buffs') and hasattr(player.active_buffs, 'active_buff_moves'):
                            move_buff_data = player.active_buffs.active_buff_moves.get(move.name)
                            if move_buff_data and move_buff_data.get('active', False):
                                buff_actually_active = True
                        
                        # SECOND: Check legacy buff systems if not found in active_buff_moves
                        if not buff_actually_active and hasattr(move, 'eff_appl') and move.eff_appl:
                            for effect in move.eff_appl:
                                if len(effect) >= 2:
                                    effect_name = effect[0]
                                    
                                    # Check for Effect-on-Hit buffs in body parts
                                    if effect_name in effect_on_hit_buffs:
                                        if hasattr(player, 'body_parts') and player.body_parts:
                                            for part in player.body_parts:
                                                if hasattr(part, 'p_eff') and hasattr(part.p_eff, effect_name):
                                                    buff_data = getattr(part.p_eff, effect_name)
                                                    # Effect-on-Hit buffs are active if level > 0
                                                    if isinstance(buff_data, list) and len(buff_data) >= 2 and buff_data[1] > 0:
                                                        buff_actually_active = True
                                                        break
                                            if buff_actually_active:
                                                break
                                    
                                    # Check for regular buffs in character.buffs
                                    elif hasattr(player, 'buffs') and hasattr(player.buffs, effect_name):
                                        buff_data = getattr(player.buffs, effect_name)
                                        # Check if level > 0 and duration > 0
                                        if isinstance(buff_data, list) and len(buff_data) >= 3 and buff_data[1] > 0 and buff_data[2] > 0:
                                            buff_actually_active = True
                                            break
                        
                        # Determine status text and color
                        if buff_actually_active:
                            status_text = "STATUS: ACTIVE"
                            status_color = GREEN
                        else:
                            status_text = "STATUS: INACTIVE"
                            status_color = RED
                        
                        self.draw_text(status_text, self.font_medium, status_color, title_x, y + single_line_height)
                    else:
                        # Scaling info (line 2) for non-BUF moves
                        scaling_text = f"Scaling - STR: {move.sca_for}, DEX: {move.sca_des}, SPE: {move.sca_spe}"
                        self.draw_text(scaling_text, self.font_medium, base_color, title_x, y + single_line_height)

                    # Format requirements (body parts, weapons) and effects (line 3)
                    req_lines = []
                    if move.reqs:
                        for req in move.reqs:
                            req_eng = req.replace('GAMBE', 'LEGS').replace('SPADA', 'SWORD').replace('TESTA', 'HEAD').replace('BRACCIO', 'ARM').replace('CORPO', 'BODY').replace('SANGUE', 'BLEED')
                            req_lines.append(req_eng.upper())
                    req_text = "Requirements: "
                    if req_lines:
                        req_text += f"{' | '.join(req_lines)}"
                    else:
                        req_text += "NONE"
                    req_color = base_color if can_use else RED
                    self.draw_text(req_text, self.font_medium, req_color, title_x, y + 2 * single_line_height)

                    # Format effects (line 4)
                    effect_lines = []
                    if move.eff_appl:
                        for eff in move.eff_appl:
                            if isinstance(eff, dict):
                                name = eff.get('name', '').upper()
                                lvl = eff.get('level', '')
                                turns = eff.get('turns', '')
                                if move.tipo == "BUF":
                                    # For BUF moves: only show effect name and level (no duration)
                                    effect_lines.append(f"{name} - Lv. {lvl}")
                                else:
                                    # For other moves: show full effect info including turns
                                    effect_lines.append(f"{name} - Lv. {lvl} - Tr. {turns}")
                            elif isinstance(eff, list) and len(eff) >= 3:
                                name = str(eff[0]).upper()
                                lvl = eff[1]
                                turns = eff[2]
                                if move.tipo == "BUF":
                                    # For BUF moves: only show effect name and level (no duration)
                                    effect_lines.append(f"{name} - Lv. {lvl}")
                                else:
                                    # For other moves: show full effect info including turns
                                    effect_lines.append(f"{name} - Lv. {lvl} - Tr. {turns}")
                            else:
                                eff_str = str(eff).replace('[[', '').replace(']]', '').replace('IMMUNITY', '').replace('immunity', '').upper()
                                effect_lines.append(eff_str)
                    effects_text = "Effects: "
                    if effect_lines:
                        effects_text += f"[{' - '.join(effect_lines)}]"
                    else:
                        effects_text += "NONE"
                    self.draw_text(effects_text, self.font_medium, base_color, title_x, y + 3 * single_line_height)

                    # Format elements (line 5) - Skip for BUF moves
                    if move.elem and move.tipo != "BUF":
                        element_line = ' '.join([str(e).replace("'", "") for e in move.elem]).replace('[','').replace(']','').replace(',','').upper()
                        self.draw_text(f"Elements: {element_line}", self.font_medium, base_color, title_x, y + 4 * single_line_height)

                # Draw scroll bar if needed (same as log)
                if len(player.moves) > max_visible_moves:
                    total_entries = len(player.moves)
                    visible_lines = max_visible_moves
                    # Use log menu's scroll bar style
                    scrollbar_x = panel_x + panel_width - 15
                    scrollbar_y = panel_y + self.sy(65)
                    scrollbar_width = 10
                    scrollbar_height = panel_height - self.sy(75)
                    pygame.draw.rect(self.screen, DARK_GRAY, (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
                    thumb_height = max(20, int(scrollbar_height * (visible_lines / total_entries)))
                    max_thumb_y = scrollbar_height - thumb_height
                    thumb_y = scrollbar_y + int(max_thumb_y * (self.moves_scroll_offset / (total_entries - visible_lines)))
                    pygame.draw.rect(self.screen, WHITE, (scrollbar_x + 1, thumb_y, scrollbar_width - 2, thumb_height))

            else:
                # No moves available
                content_start_y = title_y + self.sy(45)
                no_moves_x = title_x
                no_moves_y = content_start_y + self.sy(20)
                self.draw_text("No moves available", self.font_large, GRAY, no_moves_x, no_moves_y)

    def start_enemy_turn(self):
        """Start enemy turn with speed-based turn system"""
        # End player turn and update counters
        end_player_turn()
        
        # Check if it's actually the enemy's turn based on speed queue
        current_char = self.get_current_character()
        if current_char != enemy:
            # If it's not enemy's turn, give control back to player
            self.enemy_turn_active = False
            self.player_has_control = True
            return
        
        # It is the enemy's turn - proceed with enemy turn logic
        
        # Set enemy turn state
        self.enemy_turn_active = True
        self.player_has_control = False
        self.menu_selection_index = 0
        
        # Check and show new round messages if appropriate (TURN X messages)
        self.check_and_show_new_round_messages()
        
        # Show current turn message (e.g., "Enemy attacks first!")
        current_turn_msg = get_current_turn_message()
        if current_turn_msg:
            self.add_log_entry(current_turn_msg, "combat", (100, 255, 255))
        
        # Restore enemy stamina at beginning of enemy turn (BEFORE effect processing)
        old_enemy_stamina = enemy.sta
        enemy.sta = enemy.max_sta
        stamina_restored = enemy.sta - old_enemy_stamina
        
        if stamina_restored > 0:
            self.add_log_entry(f"{enemy.name} stamina restored: +{stamina_restored}", "success")
            print(f"⚡ ENEMY STAMINA RESTORED: {enemy.name} {old_enemy_stamina} -> {enemy.sta} (+{stamina_restored})")
        
        # Process turn-start effects for ENEMY ONLY
        process_turn_start_effects(enemy)
        
        # Refill enemy RIG with RES
        rig_restored, res_consumed, refill_message = refill_enemy_rig_with_res()
        if rig_restored > 0:
            self.add_log_entry(f"{enemy.name}: {refill_message}", "info")
        
        # Debug: Check enemy resources before regeneration
        print(f"DEBUG: Enemy resources before regeneration - RIG: {enemy.rig}/{enemy.max_rig}, RES: {enemy.res}/{enemy.max_res}, STA: {enemy.sta}/{enemy.max_sta}")
        
        # Enemy regeneration - NOW HANDLED BY AI SYSTEM
        # Regeneration is now a strategic decision made by the Enemy AI, not automatic
        print(f"DEBUG: Regeneration is now handled by AI system - skipping automatic regeneration")
        total_regenerations = 0
        regeneration_messages = []
        
        # Stun processing completed - turn can now begin
        
        self.add_log_entry(f"=== {enemy.name.upper()}'S TURN STARTED ===", "turn")
        
        # Start enemy moves
        pygame.time.set_timer(pygame.USEREVENT + 2, 1500)

    def execute_enemy_move(self):
        """Execute enemy move using AI-driven decision making"""
        print("DEBUG: execute_enemy_move called (AI-driven)")
        
        if not self.enemy_turn_active:
            print("DEBUG: Enemy turn not active, exiting")
            return
        
        # Use AI system if available, otherwise fall back to basic behavior
        if self.enemy_ai and ENEMY_AI_AVAILABLE:
            try:
                # Get AI decision - let AI decide what to do even without head
                global Turn
                ai_action = self.enemy_ai.decide_action(Turn)
                
                if ai_action is None:
                    print("DEBUG: AI returned no valid action, ending turn")
                    self.add_log_entry(f"{enemy.name} has no valid actions - ending turn", "warning")
                    pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
                    return
                
                # Execute the AI-selected action
                self.execute_ai_action(ai_action)
                return
                
            except Exception as e:
                print(f"ERROR: AI system failed: {e}")
                self.add_log_entry(f"AI system error, falling back to basic behavior", "warning")
                # Fall through to basic behavior
        
        # Fallback to basic enemy behavior (simplified version)
        self.execute_basic_enemy_behavior()
    
    def execute_ai_action(self, ai_action):
        """Execute an action selected by the AI system"""
        move_name = ai_action.move.name if ai_action.move else "None"
        print(f"DEBUG: Executing AI action: {ai_action.action_type} - {move_name}")
        
        if ai_action.action_type == "pass":
            # AI has decided to pass this turn
            print("DEBUG: AI chose to pass - ending turn")
            pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
            
        elif ai_action.action_type == "buff":
            # Execute buff move on enemy
            if self.perform_enemy_buff_move(ai_action.move):
                self.schedule_next_enemy_action()
            else:
                print("DEBUG: AI buff move failed, ending turn")
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
        
        elif ai_action.action_type == "regenerate":
            # Execute strategic regeneration on enemy part
            target_part_index = ai_action.target_part
            
            if target_part_index is not None and 0 <= target_part_index < len(enemy.body_parts):
                regeneration_success = regenerate_enemy_body_part(enemy, target_part_index)
                if regeneration_success:
                    part_name = enemy.body_parts[target_part_index].name
                    print(f"DEBUG: AI regeneration successful on {part_name}")
                else:
                    print(f"DEBUG: AI regeneration failed on part index {target_part_index}")
                
                self.schedule_next_enemy_action()
            else:
                print(f"DEBUG: Invalid regeneration target part index: {target_part_index}, ending turn")
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
        
        elif ai_action.action_type in ["attack", "reaction"]:
            # Check if enemy has head for attacking (but allow regeneration without head)
            enemy_head = None
            for part in enemy.body_parts:
                if part.name.upper() == "HEAD":
                    enemy_head = part
                    break
            
            if enemy_head is None or enemy_head.p_pvt <= 1:
                self.add_log_entry(f"{enemy.name} cannot aim without head", "combat", (255, 100, 100))
                print(f"DEBUG: {enemy.name} cannot aim without head")
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)  # End turn after 1 second
                return
                
            # Execute attack/reaction move on target
            target_part_index = ai_action.target_part
            
            if target_part_index is not None and 0 <= target_part_index < len(player.body_parts):
                target_part = player.body_parts[target_part_index]
                print(f"DEBUG: AI targeting player's {target_part.name}")
                self.perform_enemy_move(ai_action.move, target_part, target_part_index)
                self.schedule_next_enemy_action()
            else:
                print(f"DEBUG: Invalid target part index: {target_part_index}, ending turn")
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
        
        else:
            print(f"DEBUG: Unknown AI action type: {ai_action.action_type}")
            pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
    
    def schedule_next_enemy_action(self):
        """Schedule the next enemy action or end turn based on remaining stamina"""
        # Check if enemy can make another move
        remaining_moves = False
        
        for move in enemy.moves:
            actual_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs, move.accuracy)
            if actual_cost <= enemy.sta:
                can_use, _ = check_move_requirements(enemy, move)
                if can_use:
                    remaining_moves = True
                    break
        
        if remaining_moves:
            print("DEBUG: Enemy can make another move, scheduling in 2 seconds")
            pygame.time.set_timer(pygame.USEREVENT + 2, 2000)  # 2 second delay
        else:
            print("DEBUG: Enemy out of moves, ending turn in 3 seconds")
            pygame.time.set_timer(pygame.USEREVENT + 1, 3000)  # End turn after 3 seconds
    
    def execute_basic_enemy_behavior(self):
        """Fallback basic enemy behavior when AI is not available"""
        import random
        
        print("DEBUG: Using basic enemy behavior (AI fallback)")
        
        # Find affordable moves
        affordable_moves = []
        for i, move in enumerate(enemy.moves):
            actual_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs, move.accuracy)
            if actual_cost <= enemy.sta:
                can_use, _ = check_move_requirements(enemy, move)
                if can_use:
                    affordable_moves.append((i, move))
        
        if not affordable_moves:
            print("DEBUG: No affordable moves, ending turn")
            pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
            return
        
        # Simple selection: prefer buffs that aren't active, then random attack
        buff_moves = [(i, move) for i, move in affordable_moves 
                      if move.tipo == 'BUF' and move.name not in enemy.active_buffs.get_active_buff_moves()]
        attack_moves = [(i, move) for i, move in affordable_moves if move.tipo != 'BUF']
        
        if buff_moves:
            move_index, selected_move = random.choice(buff_moves)
            if self.perform_enemy_buff_move(selected_move):
                self.schedule_next_enemy_action()
                return
        
        if attack_moves:
            move_index, selected_move = random.choice(attack_moves)
            # Find valid targets
            valid_targets = []
            for i, target_part in enumerate(player.body_parts):
                if target_part.p_pvt > 0:
                    can_use, _ = check_move_requirements(enemy, selected_move, player, target_part)
                    if can_use:
                        valid_targets.append((i, target_part))
            
            if valid_targets:
                target_part_index, target_part = random.choice(valid_targets)
                self.perform_enemy_move(selected_move, target_part, target_part_index)
                self.schedule_next_enemy_action()
                return
        
        # No valid moves or targets
        print("DEBUG: No valid moves or targets, ending turn")
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000)

    def perform_enemy_move(self, move, target_part, target_part_index):
        """Perform an enemy move on a player body part (pygame version - FIXED)"""
        import random
        
        print(f"DEBUG: Performing enemy move {move.name} on {target_part.name}")
        
        # Calculate actual stamina cost with requirement reductions
        actual_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs, move.accuracy)
        
        # ⚠️ CRITICAL: Check stamina BEFORE deducting to prevent negative stamina
        if enemy.sta < actual_cost:
            print(f"⚠️ ENEMY STAMINA CHECK FAILED: {enemy.name} has {enemy.sta} stamina but {move.name} costs {actual_cost}")
            print(f"DEBUG: Move cancelled - enemy cannot afford this move")
            return  # Cancel the move execution
        
        # Subtract stamina cost from enemy (only if check passed)
        old_enemy_stamina = enemy.sta
        enemy.sta -= actual_cost
        print(f"⚡ ENEMY STAMINA USAGE: {enemy.name} used {move.name} - Stamina: {old_enemy_stamina} -> {enemy.sta} (-{actual_cost})")
        self.add_log_entry(f"⚡ {enemy.name} stamina: {old_enemy_stamina} -> {enemy.sta} (-{actual_cost})", "debug")
        
        # Check for FINE DUST effect blocking FIRE/ELECTRIC moves
        if move.elem and ("FIRE" in move.elem or "ELECTRIC" in move.elem):
            # Check if enemy has fine_dust on body
            body_part = None
            for part in enemy.body_parts:
                if "BODY" in part.name.upper():
                    body_part = part
                    break
            
            if body_part and hasattr(body_part, 'p_eff') and hasattr(body_part.p_eff, 'fine_dust'):
                dust_data = getattr(body_part.p_eff, 'fine_dust')
                # Check if fine_dust is active (level > 0 and duration > 0)
                if dust_data[1] > 0 and dust_data[2] > 0:
                    dust_level = dust_data[1]
                    print(f"FINE DUST: Blocking {move.name} due to fine dust level {dust_level}")
                    
                    # Move does not hit - deal self-damage to used body parts
                    self_damage = enemy.spe  # Damage equal to enemy's special stat
                    damaged_parts = []
                    
                    # Deal damage to body parts used by the move based on requirements
                    used_body_parts = []
                    for req in move.reqs:
                        req_str = str(req).upper().strip()
                        
                        # Parse NEEDS requirements to find actual body parts used
                        if req_str.startswith("NEEDS"):
                            needs_requirement = req_str.replace("NEEDS", "").strip()
                            
                            # Map requirements to actual body parts
                            if needs_requirement == "2 ARMS":
                                used_body_parts.extend(["RIGHT ARM", "LEFT ARM"])
                            elif needs_requirement == "ARM":
                                # For single arm requirements, use any available arm
                                for part in enemy.body_parts:
                                    if "ARM" in part.name.upper() and part.p_pvt >= 2:
                                        used_body_parts.append(part.name)
                                        break
                            elif needs_requirement == "2 LEGS":
                                used_body_parts.extend(["RIGHT LEG", "LEFT LEG"])
                            elif needs_requirement == "LEG":
                                # For single leg requirements, use any available leg
                                for part in enemy.body_parts:
                                    if "LEG" in part.name.upper() and part.p_pvt >= 2:
                                        used_body_parts.append(part.name)
                                        break
                            elif needs_requirement == "TENTACLE":
                                used_body_parts.extend(["TENTACLE 1", "TENTACLE 2"])
                            elif "TENTACLE" in needs_requirement:
                                # Find any tentacle parts
                                for part in enemy.body_parts:
                                    if "TENTACLE" in part.name.upper():
                                        used_body_parts.append(part.name)
                    
                    # Apply damage to identified body parts
                    for part_name in used_body_parts:
                        for part in enemy.body_parts:
                            if part.name.upper() == part_name.upper():
                                old_hp = part.p_pvt
                                part.p_pvt = max(0, part.p_pvt - self_damage)
                                actual_damage = old_hp - part.p_pvt
                                if actual_damage > 0:
                                    damaged_parts.append(f"{part.name}({actual_damage})")
                                break
                    
                    dust_message = f"Fine dust explosion! {enemy.name} takes {self_damage} damage to used parts: {', '.join(damaged_parts) if damaged_parts else 'none'}"
                    self.add_log_entry(dust_message, "effect", (200, 100, 50))
                    print(dust_message)
                    
                    # Play explosion sound effect
                    play_sound_effect("explosion-1.mp3", volume=0.8)
                    
                    # Clear all fine dust from enemy's body after explosion
                    if hasattr(body_part.p_eff, 'fine_dust'):
                        setattr(body_part.p_eff, 'fine_dust', ['fine_dust', 0, 0, False])
                        print(f"FINE DUST: Cleared all fine dust from {enemy.name}'s body after explosion")
                    
                    # Update enemy health
                    enemy.calculate_health_from_body_parts()
                    return
        
        # Calculate accuracy roll with evasion system and confusion modifier
        accuracy_roll = random.randint(1, 100)
        # Apply confusion modifier to attacker (enemy)
        confusion_modifier = get_confusion_accuracy_modifier(enemy)
        # Apply target body part evasion to move accuracy
        final_accuracy = move.accuracy * target_part.p_elusione * confusion_modifier
        print(f"DEBUG: Accuracy roll: {accuracy_roll} vs move accuracy: {move.accuracy}, Target evasion: {target_part.p_elusione}, Confusion modifier: {confusion_modifier}, Final accuracy: {final_accuracy}")
        
        if accuracy_roll > final_accuracy:
            # Move missed - play miss sound and show message
            miss_message = f"{enemy.name} ha mancato {move.name} su {target_part.name}!"
            self.show_warning_message(miss_message, 1500)
            print(f"DEBUG: Enemy attack missed! {miss_message}")
            
            # LOG: Enemy move missed (blue color)
            self.add_log_entry(f"{enemy.name} used {move.name} on {target_part.name} - MISSED!", "combat", (100, 150, 255))
            
            # Play miss sound effect
            play_sound_effect("mixkit-punch-through-air-2141.mp3", volume=0.4)
            
            # Make player blink blue to show miss
            self.blink_character_gif("player", (100, 150, 255), 200, 2)  # Blue blink for miss
            
            return
        
        # Move hit - but check for dodge/shield evasion first
        print(f"\n🎯 === ENEMY ATTACKING PLAYER ===")
        print(f"🎯 Enemy move: {move.name}")
        print(f"🎯 Target: {player.name}")
        print(f"🎯 Move stamina cost: {actual_cost}")
        can_evade, evasion_type, stamina_consumed = check_dodge_shield_evasion(player, move, actual_cost)
        
        if can_evade:
            # Attack was evaded by player!
            evasion_action = "DODGED" if evasion_type == "DODGE" else "BLOCKED"
            evade_message = f"{player.name} {evasion_action} the attack!"
            self.show_success_message(evade_message, 2000)
            print(f"Player evaded attack! {evade_message} (Used {evasion_type})")
            
            # LOG: Attack evaded
            self.add_log_entry(f"{enemy.name} used {move.name} on {target_part.name}", "combat")
            self.draw_event_log()
            pygame.display.flip()
            self.add_log_entry(f"{player.name} {evasion_action} the attack! (Consumed {stamina_consumed} stamina)", "evasion", (100, 255, 100))
            self.draw_event_log()
            pygame.display.flip()
            
            # Play dodge/shield sound effect
            if evasion_type == "DODGE":
                play_sound_effect("mixkit-punch-through-air-2141.mp3", volume=0.4)  # Whoosh sound for dodge
            else:  # SHIELD
                play_sound_effect("mixkit-sword-strikes-armor-2765", volume=0.4)  # Clang sound for shield
            
            # Make player blink green to show successful evasion
            self.blink_character_gif("player", (100, 255, 100), 200, 2)
            
            return  # Attack evaded, no damage or effects applied
        
        # Normal hit - apply damage with property effects
        old_hp = target_part.p_pvt
        base_damage = move.danno
        
        # Check for rhythm damage bonus (enemy)
        has_rhythm = has_property_effect(move, 'rhythm')
        if has_rhythm:
            rhythm_tracking['enemy'] += 1
            damage_to_deal = apply_rhythm_damage_bonus(base_damage, rhythm_tracking['enemy'] - 1)  # -1 because current move counts as first
            self.add_log_entry(f"Enemy Rhythm x{rhythm_tracking['enemy']}: +{damage_to_deal - base_damage} damage!", "effect", (255, 100, 100))
        else:
            # Reset rhythm count if not a rhythm move
            rhythm_tracking['enemy'] = 0
            damage_to_deal = base_damage
        
        # Check for clean cut property (enemy)
        has_clean_cut = has_property_effect(move, 'clean_cut')
        if has_clean_cut:
            damage_to_deal, clean_cut_triggered = check_clean_cut_threshold(damage_to_deal, target_part)
            if clean_cut_triggered:
                self.add_log_entry(f"Enemy CLEAN CUT! Devastating blow!", "effect", (255, 150, 0))
                self.draw_event_log()
                pygame.display.flip()
        
        # LOG: Enemy move hit first
        self.add_log_entry(f"{enemy.name} used {move.name} on {target_part.name}", "combat")
        
        # Apply elemental damage modifiers
        damage_to_deal, effects_will_apply = apply_elemental_damage(damage_to_deal, move, player, self)
        
        # Apply final damage
        target_part.p_pvt = max(0, target_part.p_pvt - damage_to_deal)
        actual_damage = old_hp - target_part.p_pvt
        
        print(f"DEBUG: Damage applied to {player.name}'s {target_part.name}: {old_hp} -> {target_part.p_pvt} (-{actual_damage})")
        
        # Play appropriate sound effect based on move element (same as player moves)
        print(f"[DEBUG SOUND] Playing enemy attack sound for {move.name}")
        print(f"[DEBUG SOUND] Move elements: {getattr(move, 'elem', 'None')}")
        
        if hasattr(move, 'elem') and move.elem:
            print(f"[DEBUG SOUND] Move has elements: {move.elem}")
            if "CUT" in move.elem:
                print(f"[DEBUG SOUND] Playing CUT sound")
                play_sound_effect("mixkit-quick-knife-slice-cutting-2152.wav", volume=0.6)
            elif "IMPACT" in move.elem:
                print(f"[DEBUG SOUND] Playing IMPACT sound")
                play_sound_effect("mixkit-sword-strikes-armor-2765", volume=0.6)
            elif "SPRAY" in move.elem:
                print(f"[DEBUG SOUND] Playing SPRAY sound")
                play_sound_effect("acid_spell_cast_squish_ball_impact_01-286782", volume=0.6)
            elif "POISON" in move.elem:
                print(f"[DEBUG SOUND] Playing POISON sound")
                play_sound_effect("Poison_Hits.mp3", volume=0.6)
            elif "ROAR" in move.elem:
                print(f"[DEBUG SOUND] Playing ROAR sound")
                play_sound_effect("tiger-roar-loudly-193229", volume=0.6)
            elif "ELECTRIC" in move.elem:
                print(f"[DEBUG SOUND] Playing ELECTRIC sound")
                play_sound_effect("electrical-shock-zap-106412.mp3", volume=0.6)
            elif "FIRE" in move.elem:
                print(f"[DEBUG SOUND] Playing FIRE sound")
                play_sound_effect("fire-sound.wav", volume=0.6)
            else:
                # Default attack sound for unrecognized move types
                print(f"[DEBUG SOUND] Playing default sound for unrecognized element")
                play_sound_effect("mixkit-impact-of-a-strong-punch-2155", volume=0.6)
        else:
            # Default sound if no element specified
            print(f"[DEBUG SOUND] No elements found, playing default sound")
            play_sound_effect("mixkit-impact-of-a-strong-punch-2155", volume=0.6)
        print(f"[DEBUG SOUND] Played enemy attack sound for {move.name} with element: {getattr(move, 'elem', 'None')}")
        
        # Check for body part destruction and trigger explosive mindset
        if old_hp > 0 and target_part.p_pvt == 0:
            process_memory_skills_bodypart_loss(player, enemy, target_part.name)
        
        # Check for buff deactivation immediately after damage
        if actual_damage > 0:
            deactivate_buffs_for_damaged_body_parts(player)
            update_character_stats(player)
        
        # Apply lifesteal healing if enemy move has lifesteal property
        has_lifesteal = has_property_effect(move, 'lifesteal')
        if has_lifesteal and actual_damage > 0:
            heal_amount = apply_lifesteal_healing(enemy, actual_damage)
            if heal_amount > 0:
                self.add_log_entry(f"{enemy.name} healed {heal_amount} HP from lifesteal!", "heal", (255, 100, 100))
                self.draw_event_log()
                pygame.display.flip()
        
        # ALWAYS show damage dealt - this was missing in some cases
        self.add_log_entry(f"Damage dealt: {actual_damage} HP", "damage")
        self.draw_event_log()
        pygame.display.flip()
        
        # Recalculate player health
        player.calculate_health_from_body_parts()
        
        # Check if player buffs should be deactivated due to body part damage
        self.check_buffs_on_body_part_damage(player)
        
        # Apply status effects from the move to the targeted body part (only if effects not blocked by immunity)
        if effects_will_apply:
            effects_applied = apply_move_effects(move, player, target_part_index)
        else:
            effects_applied = []  # No effects applied due to elemental immunity
        
        # Process Effect-on-Hit buffs for contact moves
        is_ranged_move = has_property_effect(move, 'ranged') if hasattr(move, 'eff_prop') else False
        process_effect_on_hit_buffs(enemy, player, move, is_ranged_move)
        
        # Update player stats if buffs/debuffs were applied
        if effects_applied:
            # Check if any buff/debuff effects were applied
            has_buff_debuff = any("BUFF" in effect[0] or "DEBUFF" in effect[0] for effect in effects_applied)
            if has_buff_debuff:
                update_character_stats(player)
                recalculate_character_moves(player)
                print(f"DEBUG: Recalculated player moves after debuff application")
        
        # LOG: Status effects applied
        if effects_applied:
            for effect_name, effect_level, effect_duration in effects_applied:
                self.add_log_entry(f"Applied {effect_name} (Lvl {effect_level}) for {effect_duration} turns", "effect")
                self.draw_event_log()
                pygame.display.flip()

        # Display delayed memory skills logs AFTER all main effects
        if hasattr(self, 'pending_memory_skill_logs') and self.pending_memory_skill_logs:
            for log_message, log_type, log_color in self.pending_memory_skill_logs:
                self.add_log_entry(log_message, log_type, log_color)
                self.draw_event_log()
                pygame.display.flip()
            # Clear pending logs
            self.pending_memory_skill_logs = []


        # Make player blink red to show damage taken
        self.blink_character_gif("player", (255, 0, 0), 300, 3)
        
        # Show hit message
        hit_message = f"{enemy.name} ha usato {move.name}\nsu {target_part.name} di {player.name}\nDanno: {actual_damage}"
        self.show_error_message(hit_message, 2000)
        
        # Play appropriate sound effect based on move element
        if hasattr(move, 'elem') and move.elem:
            if "CUT" in move.elem:
                play_sound_effect("mixkit-quick-knife-slice-cutting-2152.wav", volume=0.4)
            elif "IMPACT" in move.elem:
                play_sound_effect("mixkit-sword-strikes-armor-2765", volume=0.4)
            elif "SPRAY" in move.elem:
                play_sound_effect("acid_spell_cast_squish_ball_impact_01-286782", volume=0.4)
            elif "POISON" in move.elem:
                play_sound_effect("Poison_Hits.mp3", volume=0.4)
            elif "ROAR" in move.elem:
                play_sound_effect("tiger-roar-loudly-193229", volume=0.4)
            elif "ELECTRIC" in move.elem:
                play_sound_effect("electrical-shock-zap-106412.mp3", volume=0.4)
            else:
                play_sound_effect("mixkit-impact-of-a-strong-punch-2155", volume=0.4)
        else:
            # Default hit sound
            play_sound_effect("mixkit-impact-of-a-strong-punch-2155", volume=0.4)
        
        print(f"DEBUG: Enemy move completed - {move.name} hit {target_part.name} for {actual_damage} damage")

    def perform_enemy_buff_move(self, move):
        """Perform an enemy BUF move with new requirement-based system"""
        print(f"DEBUG: Performing enemy BUF move: {move.name}")
        
        # NEVER deactivate active buffs - AI should not do this
        if move.name in enemy.active_buffs.get_active_buff_moves():
            print(f"DEBUG: Enemy buff {move.name} already active - should not have been selected")
            return False
            
        else:
            # Check requirements are met
            if not self.check_move_requirements(move, enemy):
                print(f"DEBUG: Enemy {move.name} requirements not met")
                return False  # Enemy AI should pick a different move
            
            # Calculate actual stamina cost
            actual_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs, move.accuracy)
            
            # Check if enemy has enough stamina
            if enemy.sta < actual_cost:
                print(f"DEBUG: Enemy not enough stamina for {move.name}")
                return False  # Enemy AI should pick a different move
            
            # Deactivate conflicting buffs first
            conflicting_buffs = enemy.active_buffs.deactivate_conflicting_buffs(move.reqs)
            if conflicting_buffs:
                for buff_name in conflicting_buffs:
                    # Find the conflicting move to remove its effects
                    for enemy_move in enemy.moves:
                        if enemy_move.name == buff_name:
                            self.remove_buff_effects(enemy_move, enemy)
                            print(f"DEBUG: Removed effects for conflicting enemy buff: {buff_name}")
                            break
                    self.add_log_entry(f"{enemy.name} deactivated conflicting buff: {buff_name}", "effect")
                
                # Update stats after removing conflicting buff effects
                update_character_stats(enemy)
                recalculate_character_moves(enemy)
            
            # Subtract stamina from enemy
            old_enemy_stamina = enemy.sta
            enemy.sta -= actual_cost
            print(f"⚡ ENEMY STAMINA USAGE: {enemy.name} used {move.name} - Stamina: {old_enemy_stamina} -> {enemy.sta} (-{actual_cost})")
            self.add_log_entry(f"⚡ {enemy.name} stamina: {old_enemy_stamina} -> {enemy.sta} (-{actual_cost})", "debug")
            
            # Activate the new buff
            enemy.active_buffs.activate_buff_move(move.name, move.reqs, move.eff_appl)
            
            # Apply effects (buffs) to the enemy
            effects_applied = apply_move_effects(move, enemy, None)
            
            # Success message
            hit_message = f"{enemy.name} activated {move.name}!"
            self.show_success_message(hit_message, 2000)
            print(f"DEBUG: Enemy used buff move: {hit_message}")
            
            # LOG: Enemy used buff move
            self.add_log_entry(f"{enemy.name} activated {move.name}", "combat")
            
            # LOG: Buff effects applied to enemy
            if effects_applied:
                for effect_name, effect_level, effect_duration in effects_applied:
                    # Map stat abbreviations to full names
                    stat_mapping = {
                        'RIG BUFF': 'Rigidity buff',
                        'RES BUFF': 'Resistance buff', 
                        'STA BUFF': 'Stamina buff',
                        'FORZ BUFF': 'Strength buff',
                        'DES BUFF': 'Dexterity buff',
                        'SPE BUFF': 'Special buff',
                        'VEL BUFF': 'Velocity buff',
                        'RIG DEBUFF': 'Rigidity debuff',
                        'RES DEBUFF': 'Resistance debuff', 
                        'STA DEBUFF': 'Stamina debuff',
                        'FORZ DEBUFF': 'Strength debuff',
                        'DES DEBUFF': 'Dexterity debuff',
                        'SPE DEBUFF': 'Special debuff',
                        'VEL DEBUFF': 'Velocity debuff'
                    }
                    
                    # Get proper name or fallback to original
                    proper_name = stat_mapping.get(effect_name.upper(), effect_name.lower())
                    self.add_log_entry(f"Applied {proper_name} Lv {abs(effect_level)}", "effect")
        
        # Update enemy stats to reflect new buffs
        update_character_stats(enemy)
        
        # Recalculate all move damage based on new buffed stats
        recalculate_character_moves(enemy)
        
        # Custom buff sounds are now played in apply_move_effects based on Status_Effects_Config
        print(f"[SOUND] Enemy buff move {move.name} - custom sound played when effect was applied")
        
        # Make enemy blink to show buff applied
        self.blink_character_gif("enemy", (0, 255, 0), 300, 3)  # Green blink for buffs
        
        # Calculate remaining moves for scheduling
        remaining_stamina = enemy.sta
        remaining_affordable_moves = []
        for i, check_move in enumerate(enemy.moves):
            actual_move_cost = calculate_move_stamina_cost(check_move.sca_for, check_move.sca_des, check_move.sca_spe, check_move.eff_appl, check_move.reqs, check_move.accuracy)
            if actual_move_cost <= remaining_stamina:
                can_use, _ = check_move_requirements(check_move, enemy)
                if can_use:
                    remaining_affordable_moves.append((i, check_move))
        
        print(f"DEBUG: Enemy will have {remaining_stamina} stamina after buff")
        print(f"DEBUG: Enemy will have {len(remaining_affordable_moves)} moves available after this buff")
        
        if remaining_affordable_moves:
            # Schedule next move after animation delay
            animation_delay = 3 * 300 + 500  # 3 blinks * 300ms + 500ms buffer
            print(f"DEBUG: Scheduling next enemy move in {animation_delay}ms")
            pygame.time.set_timer(pygame.USEREVENT + 2, animation_delay)
        else:
            # Enemy will be out of stamina after this move, end turn
            animation_delay = 3 * 300 + 1000  # Animation + extra time to see the effect
            print("DEBUG: Enemy will be out of stamina, scheduling turn end")
            pygame.time.set_timer(pygame.USEREVENT + 1, animation_delay)
        
        return True  # BUF move was successful

    def draw(self):
        """Draw everything (UPDATED to use event log instead of temporary messages)"""
        self.screen.fill(BLACK)
            
        # Draw UI components
        self.draw_body_panel()
        self.draw_stats_panel()
        self.draw_menu_bar()
        
        # Always draw the enemy panel
        self.show_enemy_panel()

        # If victory fade is active, overlay fade on enemy panel area
        if self.victory['active'] and self.victory['phase'] in ('fade', 'post_fade_wait'):
            # Mirror the enemy panel rect used in show_enemy_panel (scaled)
            menu_bar_width = self.sx(760)
            menu_bar_x = self.sx(310)
            menu_bar_y = self.sy(1000 - 265)
            panel_x = menu_bar_x
            panel_y = self.sy(35)
            panel_width = menu_bar_width
            panel_height = menu_bar_y - panel_y - self.sy(20)
            overlay = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            fade_alpha = 255 - self.victory.get('alpha', 0)
            overlay.fill((0, 0, 0, fade_alpha))
            self.screen.blit(overlay, (panel_x, panel_y))
        
        # Draw other panels based on conditions
        if not (hasattr(self, 'target_selection_active') and self.target_selection_active):
            if self.player_has_control:
                self.draw_moves_panel()
                self.draw_equipment_panel()
                self.draw_abilities_panel()
                self.draw_items_panel()
                self.draw_pass_panel()
        
        # Draw enemy part attributes when appropriate
        if self.menu_selection_index == 0 and self.player_has_control:
            self.draw_enemy_part_attributes()
        
        # ALWAYS show enemy buffs/debuffs matrix and stamina bar during combat for player understanding
        # This allows players to see enemy status during both player and enemy turns, regardless of menu selection
        # Draw enemy buffs/debuffs matrix
        self.draw_enemy_buffs_matrix()
        # Draw enemy stamina bar between buff matrix and event log
        self.draw_enemy_stamina_bar()
        
        # Draw player turn start indicator (if active)
        if hasattr(self, 'player_turn_start_active') and self.player_turn_start_active:
            self.draw_player_turn_start_indicator()
        
        # Draw event log (replaces draw_message)
        self.draw_event_log()
        
        pygame.display.flip()
    
    def regenerate_body_part_pygame(self, character, part_index):
        """Regenerate a specific body part (updated with log integration)"""
        if not (0 <= part_index < len(character.body_parts)):
            self.add_log_entry(f"Invalid body part index: {part_index}", "error")
            return False
        
        part = character.body_parts[part_index]

        if part.p_pvt >= part.max_p_pvt:
            self.add_log_entry(f"{part.name} is already at full health!", "warning")
            return False

        if character.rig < 5:
            self.add_log_entry("Cannot regenerate - insufficient RIG!", "error")
            return False

        if character.sta < stamina_cost_per_regeneration:
            self.add_log_entry("Cannot regenerate - insufficient stamina!", "error")
            return False

        if hasattr(character, 'res') and character.res < 5:
            self.add_log_entry("WARNING: Low RES - cannot restore RIG next turn!", "warning")

        # Check for MESS UP effect FIRST - reduces level instead of healing
        if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'mess_up'):
            mess_up_data = getattr(part.p_eff, 'mess_up')
            # Check if mess_up is active (level > 0)
            if len(mess_up_data) >= 2 and mess_up_data[1] > 0:
                mess_up_level = mess_up_data[1]
                # Reduce mess_up level by 1 instead of healing
                new_level = max(0, mess_up_level - 1)
                setattr(part.p_eff, 'mess_up', [mess_up_data[0], new_level, mess_up_data[2], mess_up_data[3]])
                
                # Consume resources but NO HEALING
                character.rig -= 5
                character.sta -= stamina_cost_per_regeneration
                
                self.add_log_entry(f"{character.name}'s {part.name} mess up reduced to level {new_level} - no healing", "effect", (200, 150, 100))
                
                return True  # Regeneration was "successful" but no healing occurred

        # Check for AMPUTATE effect blocking regeneration
        if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'amputate'):
            amputate_data = getattr(part.p_eff, 'amputate')
            # Check if amputate is active (level > 0 and duration > 0)
            if len(amputate_data) >= 3 and amputate_data[1] > 0 and amputate_data[2] > 0:
                self.add_log_entry(f"{part.name} is amputated and cannot regenerate!", "error")
                return False

        # Apply regeneration
        old_pvt = part.p_pvt
        if part.p_pvt == 0:
            part.p_pvt = 1
            actual_healing = 1
            # Lose 5 regen if available
            if hasattr(character, 'regen') and character.regen is not None:
                character.regen = max(0, character.regen - 5)
                self.add_log_entry(f"{character.name} lost 5 regen for reviving {part.name}. New regen: {character.regen}", "regeneration")
        else:
            part.p_pvt = min(part.p_pvt + 5, part.max_p_pvt)
            actual_healing = part.p_pvt - old_pvt

        character.rig -= 5
        character.sta -= stamina_cost_per_regeneration
        character.calculate_health_from_body_parts()

        # Nerf status effects on this part
        self.nerf_status_effects_on_part(part)
        
        # Update automatic debuffs since status effects may have been weakened
        update_automatic_debuffs(character)

        # Log success - only show HP recovered
        self.add_log_entry(f"Regenerated {part.name}: +{actual_healing} HP", "regeneration")

        return True

    def update_body_part_highlighting(self):
        """Update the highlighting of body parts based on regeneration selection (pygame version)"""
        if not self.regeneration_mode_active:
            return
        
        # Store the regeneration selection state for use in draw_body_panel
        self.regeneration_selection_index = getattr(self, 'regeneration_selection_index', 0)
        
        # The actual highlighting will be handled in draw_body_panel method
        # No need to modify widgets directly since pygame redraws everything each frame

    def toggle_regeneration_mode(self):
        """Toggle regeneration mode on/off (updated with log integration)"""
        if not self.player_has_control:
            return
        
        self.regeneration_mode_active = not self.regeneration_mode_active
        
        if not hasattr(self, 'regeneration_selection_index'):
            self.regeneration_selection_index = 0
        else:
            self.regeneration_selection_index = 0
        
        if self.regeneration_mode_active:
            # Removed regeneration mode activation message from event log
            self.in_regeneration_navigation = True
        else:
            # Removed regeneration mode deactivation message from event log
            self.in_regeneration_navigation = False

    def end_enemy_turn(self):
        """End enemy turn with speed-based turn system"""
        # Turn-end effects are processed in the global end_enemy_turn() function
        
        # Clear timers
        pygame.time.set_timer(pygame.USEREVENT + 1, 0)
        pygame.time.set_timer(pygame.USEREVENT + 2, 0)
        
        # Call global function to advance turn queue (which processes turn-end effects)
        end_enemy_turn()
        
        # Check who has the next turn based on speed queue
        current_char = self.get_current_character()
        
        if current_char == player:
            # Next turn is player's - give control to player
            self.enemy_turn_active = False
            self.player_has_control = True
            
            # Ensure move execution is unlocked when player gets control
            self.move_execution_locked = False
            
            # Check and show new round messages if appropriate (TURN X messages)
            self.check_and_show_new_round_messages()
            
            # Show current turn message (e.g., "Player attacks second!")
            current_turn_msg = get_current_turn_message()
            if current_turn_msg:
                self.add_log_entry(current_turn_msg, "combat", (100, 255, 255))
            
            # Set player turn start indicator (show for 2 seconds)
            self.player_turn_start_active = True
            pygame.time.set_timer(pygame.USEREVENT + 4, 2000)
            
            # Restore player stamina at beginning of player turn (BEFORE effect processing)
            old_player_stamina = player.sta
            player.sta = player.max_sta
            stamina_restored = player.sta - old_player_stamina
            
            if stamina_restored > 0:
                self.add_log_entry(f"{player.name} stamina restored: +{stamina_restored}", "success")
                print(f"⚡ PLAYER STAMINA RESTORED: {player.name} {old_player_stamina} -> {player.sta} (+{stamina_restored})")
            
            # Process turn-start effects for PLAYER ONLY
            process_turn_start_effects(player)
            
            # Check for weapon unequipping after turn start effects (status effects may have damaged arms)
            self.check_buffs_on_body_part_damage(player)
            
            # Refill player RIG
            rig_restored, res_consumed, refill_message = refill_player_rig_with_res()
            if rig_restored > 0:
                self.add_log_entry(f"{player.name}: {refill_message}", "info")
                
        else:
            # Next turn is enemy's - start the next enemy turn properly
            self.start_enemy_turn()
            
            # Restore enemy stamina at beginning of enemy turn
            old_enemy_stamina = enemy.sta
            enemy.sta = enemy.max_sta
            stamina_restored = enemy.sta - old_enemy_stamina
            
            if stamina_restored > 0:
                self.add_log_entry(f"{enemy.name} stamina restored: +{stamina_restored}", "success")
                print(f"⚡ ENEMY STAMINA RESTORED: {enemy.name} {old_enemy_stamina} -> {enemy.sta} (+{stamina_restored})")
            
            # Process turn-start effects for ENEMY ONLY
            process_turn_start_effects(enemy)
            
            # Refill enemy RIG with RES
            rig_restored, res_consumed, refill_message = refill_enemy_rig_with_res()
            if rig_restored > 0:
                self.add_log_entry(f"{enemy.name}: {refill_message}", "info")

    def process_stun_stamina_reduction(self, character):
        """Process STUN stamina reduction: sum ALL stun levels across body parts and subtract from stamina
        
        CRITICAL: This is called at the START of each character's turn AFTER stamina restoration.
        Sequence: 1. Stamina restored → 2. Stun effects processed → 3. Duration decreases → 4. Turn begins
        This ensures stuns work correctly and durations decrease immediately after being processed.
        """
        char_name = getattr(character, 'name', 'Unknown')
        
        if not hasattr(character, 'body_parts') or not character.body_parts:
            return
        
        print(f"DEBUG: Processing stun effects for {char_name}")
        
        # STUN effect: sum ALL stun levels across ALL body parts
        total_stun = 0
        stun_parts = []
        
        for part in character.body_parts:
            if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'stun'):
                stun_data = getattr(part.p_eff, 'stun')
                # Check if stun is active (level > 0 and duration > 0)
                print(f"DEBUG: {char_name} {part.name} stun data: Level={stun_data[1]}, Duration={stun_data[2]}")
                
                # A stun effect is active if it has both level > 0 AND duration > 0
                if stun_data[1] > 0 and stun_data[2] > 0:
                    total_stun += stun_data[1]
                    stun_parts.append(f"{part.name}(L{stun_data[1]})")
                    print(f"DEBUG: Added {stun_data[1]} stun from {part.name}, total now: {total_stun}")
                else:
                    print(f"DEBUG: {part.name} stun not active - Level={stun_data[1]}, Duration={stun_data[2]}")

        # If any stun present, subtract total stun levels from stamina
        if total_stun > 0:
            old_sta = character.sta
            character.sta = max(0, character.sta - total_stun)
            stun_message = f"{char_name} loses {total_stun} stamina due to STUN from {', '.join(stun_parts)} (STA: {old_sta} → {character.sta})"
            print(stun_message)
            self.add_log_entry(stun_message, "warning")
        else:
            print(f"DEBUG: {char_name} has no active stun effects")

    def draw_equipment_panel(self):
        """Draw equipment panel when EQUIP is selected (SCALED) - matches moves panel dimensions"""
        if self.menu_selection_index == 2:
            # Align with menu bar - EXACT SAME AS MOVES PANEL
            menu_x = self.sx(310)
            menu_y = self.sy(1000 - 265)
            menu_width = self.sx(760)
            menu_height = self.sy(80)

            # Panel bounds: start at same y as body panel, end just above menu bar
            panel_x = menu_x
            panel_width = menu_width
            top_margin = self.sy(10)
            bottom_margin = self.sy(15)
            panel_y = top_margin
            panel_height = menu_y - top_margin - bottom_margin

            # Draw white border box for equipment list
            pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
            pygame.draw.rect(self.screen, BLACK, (panel_x + 2, panel_y + 2, panel_width - 4, panel_height - 4))

            # Title positioning (aligned with menu bar) - USE EQUIP FONTS (DOUBLED)
            title_x = panel_x + self.sx(20)
            title_y = panel_y + self.sy(15)
            self.draw_text(f"{player.name}'s Equipment", self.equip_font_large, WHITE, title_x, title_y)
            
            # Import Player_Equipment to get weapon list
            try:
                import Player_Equipment
                player_equip = Player_Equipment.player1
                
                if not player_equip:
                    self.draw_text("Equipment system not available", self.equip_font_medium, RED, title_x, title_y + self.sy(50))
                    return
                
                # Current weapon info
                current_weapon = player_equip.get_equipped_by_type('weapon')
                current_y = title_y + self.sy(45)
                
                if current_weapon:
                    current_text = f"Current: {current_weapon.name} ({current_weapon.get_weapon_type()})"
                    self.draw_text(current_text, self.equip_font_medium, GREEN, title_x, current_y)
                else:
                    self.draw_text("Current: None (Unarmed)", self.equip_font_medium, YELLOW, title_x, current_y)
                
                # STM cost info
                cost_y = current_y + self.sy(25)
                self.draw_text(f"Swap weapon: {swap_weapon_cost} STM | Equip/Unequip: {equip_unequip_cost} STM", 
                             self.equip_font_small, GRAY, title_x, cost_y)
                
                # Get all weapons from player's equipment
                weapons = [item for item in player_equip.equip if hasattr(item, 'type') and item.type == 'weapon']
                
                if weapons:
                    # Calculate scrolling parameters with proper height management for doubled fonts
                    content_start_y = cost_y + self.sy(35)
                    content_height = panel_height - (content_start_y - panel_y) - self.sy(20)
                    
                    # Calculate how many weapons can fit with reduced spacing for smaller fonts
                    line_spacing = self.sy(22)  # Reduced spacing for smaller fonts
                    lines_per_weapon = 4  # 4 lines: name, class, type, status (spacing = 1 row height)
                    total_weapon_height = lines_per_weapon * line_spacing
                    max_visible_weapons = max(1, int(content_height // total_weapon_height))

                    # Initialize scroll offset if not exists
                    if not hasattr(self, 'equipment_scroll_offset'):
                        self.equipment_scroll_offset = 0

                    # Adjust scroll offset based on current selection
                    if self.equipment_selection_index < self.equipment_scroll_offset:
                        self.equipment_scroll_offset = self.equipment_selection_index
                    elif self.equipment_selection_index >= self.equipment_scroll_offset + max_visible_weapons:
                        self.equipment_scroll_offset = self.equipment_selection_index - max_visible_weapons + 1

                    # Display weapons with proper spacing
                    for i in range(max_visible_weapons):
                        weapon_index = self.equipment_scroll_offset + i
                        if weapon_index >= len(weapons):
                            break
                        
                        weapon = weapons[weapon_index]
                        y_pos = content_start_y + i * total_weapon_height
                        
                        # Weapon name - check if weapon can be equipped to determine color
                        if weapon.equipped:
                            name_color = GREEN if weapon_index == self.equipment_selection_index else GREEN
                        elif not self.can_player_equip_weapon(weapon)[0]:  # Can't equip - gray out
                            name_color = DARK_GRAY if weapon_index == self.equipment_selection_index else GRAY
                        else:
                            name_color = RED if weapon_index == self.equipment_selection_index else WHITE
                        
                        self.draw_text(weapon.name, self.equip_font_medium, name_color, title_x, y_pos)
                        
                        # Weapon class on separate line with proper spacing
                        class_text = f"Class: {getattr(weapon, 'weapon_class', 'Unknown')}"
                        self.draw_text(class_text, self.equip_font_small, GRAY, title_x, y_pos + line_spacing)
                        
                        # Weapon type on separate line with proper spacing
                        type_text = f"Type: {getattr(weapon, 'get_weapon_type', lambda: 'Unknown')()}"
                        self.draw_text(type_text, self.equip_font_small, GRAY, title_x, y_pos + line_spacing * 2)
                        
                        # Equipment status with proper spacing
                        status_text = ""
                        status_color = WHITE
                        
                        if weapon.equipped:
                            status_text = "[EQUIPPED]"
                            status_color = GREEN
                        else:
                            can_equip, reason = self.can_player_equip_weapon(weapon)
                            if not can_equip:
                                status_text = f"[CANNOT EQUIP]"
                                status_color = RED
                        
                        if status_text:
                            self.draw_text(status_text, self.equip_font_small, status_color, title_x, y_pos + line_spacing * 3)
                    
                    # Draw large weapon image panel - FIXED POSITIONING TO MATCH EVENT LOG BOUNDARIES
                    if weapons and 0 <= self.equipment_selection_index < len(weapons):
                        selected_weapon = weapons[self.equipment_selection_index]
                        
                        # Calculate weapon image positioning to align with EVENT LOG boundaries exactly
                        # Use same x position as event log (self.log_x)
                        weapon_image_x = self.log_x  # Align left edge with event log
                        weapon_image_y = panel_y  # Start at same level as equipment panel
                        
                        # Calculate proper dimensions - use exact EVENT LOG boundaries
                        # Width: same as event log width (self.log_width)
                        # Height: stop exactly at event log top position with small gap
                        weapon_image_width = self.log_width  # Exact same width as event log
                        weapon_image_height = self.log_y - weapon_image_y - self.sy(10)  # Small gap before event log
                        
                        # Draw weapon image panel border
                        pygame.draw.rect(self.screen, WHITE, (weapon_image_x, weapon_image_y, weapon_image_width, weapon_image_height), 2)
                        pygame.draw.rect(self.screen, BLACK, (weapon_image_x + 2, weapon_image_y + 2, weapon_image_width - 4, weapon_image_height - 4))
                        
                        # Try to load and display weapon image - FULL PANEL USAGE
                        try:
                            if hasattr(selected_weapon, 'image_path') and selected_weapon.image_path:
                                # Load weapon image
                                weapon_img = pygame.image.load(selected_weapon.image_path)
                                
                                # Use maximum available space with small margins for borders
                                available_width = weapon_image_width - self.sx(10)
                                available_height = weapon_image_height - self.sy(10)
                                
                                # Calculate scaling to fit within bounds while maintaining aspect ratio
                                img_width, img_height = weapon_img.get_size()
                                scale_x = available_width / img_width
                                scale_y = available_height / img_height
                                scale = min(scale_x, scale_y)
                                
                                new_width = int(img_width * scale)
                                new_height = int(img_height * scale)
                                
                                # Scale the image
                                scaled_weapon_img = pygame.transform.scale(weapon_img, (new_width, new_height))
                                
                                # Center the image perfectly in the available space
                                img_x = weapon_image_x + (weapon_image_width - new_width) // 2
                                img_y = weapon_image_y + (weapon_image_height - new_height) // 2
                                
                                self.screen.blit(scaled_weapon_img, (img_x, img_y))
                                
                        except Exception as e:
                            # Error loading image - show error in center
                            error_x = weapon_image_x + weapon_image_width // 2 - self.sx(40)
                            error_y = weapon_image_y + weapon_image_height // 2
                            self.draw_text("No Image", self.equip_font_medium, RED, error_x, error_y)
                    
                    # Scroll indicators
                    if self.equipment_scroll_offset > 0:
                        self.draw_text("↑ More above", self.equip_font_small, YELLOW, 
                                     panel_x + panel_width - self.sx(120), content_start_y - self.sy(15))
                    
                    if self.equipment_scroll_offset + max_visible_weapons < len(weapons):
                        self.draw_text("↓ More below", self.equip_font_small, YELLOW,
                                     panel_x + panel_width - self.sx(120), 
                                     content_start_y + content_height - self.sy(15))
                
                else:
                    self.draw_text("No weapons available", self.equip_font_medium, GRAY, title_x, cost_y + self.sy(40))
                    
            except Exception as e:
                error_text = f"Error loading equipment: {e}"
                self.draw_text(error_text, self.equip_font_medium, RED, title_x, title_y + self.sy(50))

    def can_player_equip_weapon(self, weapon):
        """Check if player has enough usable arms to equip a weapon"""
        weapon_type = getattr(weapon, 'weapon_type', 'One Handed')
        
        # Count functional arms (≥2 HP as per user requirements)
        functional_arms = 0
        for part in player.body_parts:
            if "ARM" in part.name.upper() and part.p_pvt >= 2:
                functional_arms += 1
        
        # Check requirements based on weapon type
        if weapon_type == "Two Handed":
            if functional_arms < 2:
                return False, f"Two Handed weapon requires 2 arms with ≥2 HP, but only {functional_arms} available"
        elif weapon_type in ["One Handed", "One and a Half Handed"]:
            if functional_arms < 1:
                return False, f"{weapon_type} weapon requires 1 arm with ≥2 HP, but only {functional_arms} available"
        
        return True, "Requirements met"

    def check_weapon_drop_on_injury(self, injured_part_name):
        """Check if player should drop weapon due to arm injury"""
        try:
            import Player_Equipment
            player_equip = Player_Equipment.player1
            
            if not player_equip:
                return
            
            current_weapon = player_equip.get_equipped_by_type('weapon')
            if not current_weapon:
                return
            
            # Only check if an arm was injured
            if "ARM" not in injured_part_name.upper():
                return
            
            # Check if player can still use the weapon
            can_equip, reason = self.can_player_equip_weapon(current_weapon)
            
            if not can_equip:
                # Drop the weapon
                current_weapon.unequip()
                drop_message = f"{player.name} dropped {current_weapon.name} when losing {injured_part_name}"
                self.add_log_entry(drop_message, "warning", YELLOW)
                print(f"[Weapon Drop] {drop_message}")
                
                # Reload moves to get bare-handed moves back
                load_player_moves_from_system()
                
        except Exception as e:
            print(f"[Weapon Drop] Error checking weapon drop: {e}")

    def handle_weapon_selection(self):
        """Handle weapon selection and swapping with STM costs"""
        try:
            # Get weapons from Player_Equipment
            import Player_Equipment
            player_equip = Player_Equipment.player1
            if not player_equip:
                self.add_log_entry("Equipment system not available", "error")
                return
            
            weapons = [item for item in player_equip.equip if hasattr(item, 'type') and item.type == 'weapon']
            if not weapons:
                self.add_log_entry("No weapons available", "info")
                return
            
            selected_weapon = weapons[self.equipment_selection_index]
            
            # Check if weapon is already equipped
            if selected_weapon.equipped:
                # Unequip weapon
                if player.sta < equip_unequip_cost:
                    self.add_log_entry(f"Not enough STM to unequip! Need {equip_unequip_cost}, have {player.sta}", "error")
                    return
                
                selected_weapon.unequip()
                player.sta -= equip_unequip_cost
                self.add_log_entry(f"Unequipped {selected_weapon.name} (STM -{equip_unequip_cost})", "success")
                
                # Reload moves to get bare-handed moves back
                load_player_moves_from_system()
                
            else:
                # Try to equip weapon - check requirements first
                can_equip, reason = self.can_player_equip_weapon(selected_weapon)
                if not can_equip:
                    self.add_log_entry(f"Cannot equip {selected_weapon.name}: {reason}", "error")
                    return  # Don't consume stamina for invalid equip attempts
                
                # Check if we need to swap (another weapon equipped)
                current_equipped_weapon = None
                for weapon in weapons:
                    if weapon.equipped:
                        current_equipped_weapon = weapon
                        break
                
                if current_equipped_weapon:
                    # Weapon swap
                    if player.sta < swap_weapon_cost:
                        self.add_log_entry(f"Not enough STM to swap! Need {swap_weapon_cost}, have {player.sta}", "error")
                        return
                    
                    current_equipped_weapon.unequip()
                    selected_weapon.equip()
                    player.sta -= swap_weapon_cost
                    self.add_log_entry(f"Swapped {current_equipped_weapon.name} for {selected_weapon.name} (STM -{swap_weapon_cost})", "success")
                    
                else:
                    # Simple equip (no weapon currently equipped)
                    if player.sta < equip_unequip_cost:
                        self.add_log_entry(f"Not enough STM to equip! Need {equip_unequip_cost}, have {player.sta}", "error")
                        return
                    
                    selected_weapon.equip()
                    player.sta -= equip_unequip_cost
                    self.add_log_entry(f"Equipped {selected_weapon.name} (STM -{equip_unequip_cost})", "success")
                
                # Reload moves to update with weapon moves
                load_player_moves_from_system()
        
        except Exception as e:
            import traceback
            print(f"[Weapon Selection] Full traceback:")
            traceback.print_exc()
            self.add_log_entry(f"Error handling weapon selection: {e}", "error")
            print(f"[Weapon Selection] Error: {e}")

    def draw_abilities_panel(self):
        """Draw abilities panel when ABILITIES is selected"""
        if self.menu_selection_index == 3:
            abilities_x = 400
            abilities_y = 100
            
            self.draw_text(f"{player.name}'s Abilities", self.font_large, WHITE, abilities_x, abilities_y)
            
            if hasattr(player, 'ability') and player.ability:
                for i, ability in enumerate(player.ability):
                    y = abilities_y + 40 + i * 60
                    color = RED if i == getattr(self, 'ability_selection_index', 0) else WHITE
                    
                    # Ability name and info
                    ability_text = f"{ability.name} - Cost: {ability.punti} points"
                    self.draw_text(ability_text, self.font_medium, color, abilities_x, y)
                    
                    # Description
                    self.draw_text(ability.description, self.font_small, color, abilities_x, y + 20)
                    
            else:
                self.draw_text("No abilities available", self.font_medium, GRAY, abilities_x, abilities_y + 60)

    def draw_items_panel(self):
        """Draw items panel when ITEMS is selected"""
        if self.menu_selection_index == 4:
            items_x = 400
            items_y = 100
            
            self.draw_text("Items Panel", self.font_large, WHITE, items_x, items_y)
            self.draw_text("Items system in development", self.font_medium, GRAY, items_x, items_y + 50)

    def draw_pass_panel(self):
        """Draw pass panel when PASS is selected (SCALED)"""
        if self.menu_selection_index == 5:
            pass_x = self.sx(500)
            pass_y = self.sy(200)
            
            self.draw_text("Pass Turn?", self.font_large, WHITE, pass_x, pass_y)
            
            # YES option (scaled)
            yes_color = RED if getattr(self, 'pass_selection', 0) == 0 else WHITE
            self.draw_text("YES", self.font_large, yes_color, pass_x, pass_y + self.sy(60))
            
            # NO option (scaled)
            no_color = RED if getattr(self, 'pass_selection', 0) == 1 else WHITE
            self.draw_text("NO", self.font_large, no_color, pass_x, pass_y + self.sy(120))
    
    def run(self):
        """Main game loop"""
        # Initialize AI system now that characters are loaded
        self.initialize_enemy_ai()
        
        # Initialize speed-based turn system
        self.initialize_speed_based_turns()
        
        # Set initial control based on who goes first in speed queue
        first_character = self.get_current_character()
        if first_character == player:
            self.player_has_control = True
            self.enemy_turn_active = False
            # Show initial battle messages
            self.check_and_show_new_round_messages()
            current_turn_msg = get_current_turn_message()
            if current_turn_msg:
                self.add_log_entry(current_turn_msg, "combat", (100, 255, 255))
        elif first_character == enemy:
            self.player_has_control = False
            self.enemy_turn_active = True
            # Messages will be shown when enemy turn actually starts
        
        # If enemy goes first, set flag to auto-start their turn
        if first_character == enemy:
            self.auto_start_enemy_turn = True
        else:
            self.auto_start_enemy_turn = False
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        # If returning to overworld, don't quit pygame
        if not self.return_to_overworld:
            pygame.quit()
            sys.exit()
        
        return self.combat_result

# Module-level initialization moved to function to prevent import hanging
def initialize_battle_system():
    """Initialize the battle system - call this before using combat functions"""
    # Initialize global event log
    global event_log
    if 'event_log' not in globals():
        event_log = []
    
    # Initialize game data
    initialize_game_data()

    # Initialize music system (but don't start music yet - will be handled by music switching)
    if initialize_music():
        # Preload sound effects for better performance
        preload_sound_effects()
    else:
        print("Game will continue without background music")

def load_weapon_moves_for_battle(character_name=None):
    """Load weapon moves from equipped weapon based on proficiency level for battle system"""
    weapon_moves = []
    
    try:
        # Try to import Player_Equipment
        from Player_Equipment import get_main_player_equipment
        
        # Get the main player equipment object
        player_equip = get_main_player_equipment()
        if not player_equip:
            print("[Battle] No player equipment found for weapon moves")
            return weapon_moves
        
        # Get equipped weapon
        equipped_weapon = player_equip.get_equipped_by_type('weapon')
        if not equipped_weapon:
            print("[Battle] No weapon equipped - no weapon moves")
            return weapon_moves
        
        # Get weapon class and proficiency
        weapon_class = equipped_weapon.get_weapon_class()
        if not weapon_class:
            print(f"[Battle] No weapon class for {equipped_weapon.name}")
            return weapon_moves
        
        proficiency_level = player_equip.get_weapon_proficiency(weapon_class)
        print(f"[Battle] Loading weapon moves for {equipped_weapon.name} (Class: {weapon_class}, Proficiency: {proficiency_level})")
        
        # Get available moves for current proficiency level
        weapon_move_objects = equipped_weapon.get_available_moves(proficiency_level)
        print(f"[Battle] Equipment returned {len(weapon_move_objects)} weapon move objects")
        
        # Debug: show what we got from equipment
        for i, move_obj in enumerate(weapon_move_objects):
            print(f"[Battle] Move {i}: {type(move_obj)} - {getattr(move_obj, 'name', 'NO_NAME')}")
        
        # Convert to battle system format
        for move_obj in weapon_move_objects:
            try:
                # Handle Mossa objects from Battle_Menu_Beta_V18 (Italian attribute names)
                if hasattr(move_obj, 'name'):
                    weapon_move_dict = {
                        'name': move_obj.name,
                        'type': getattr(move_obj, 'tipo', getattr(move_obj, 'type', 'ATK')),  # Italian: tipo
                        'scaling': {
                            'forz': getattr(move_obj, 'sca_for', getattr(move_obj, 'forz_scaling', 1)),  # Italian: sca_for
                            'des': getattr(move_obj, 'sca_des', getattr(move_obj, 'des_scaling', 0)),   # Italian: sca_des
                            'spe': getattr(move_obj, 'sca_spe', getattr(move_obj, 'spe_scaling', 0))   # Italian: sca_spe
                        },
                        'effects': getattr(move_obj, 'eff_appl', getattr(move_obj, 'effects', [])),     # Italian: eff_appl
                        'requirements': getattr(move_obj, 'reqs', getattr(move_obj, 'requirements', [])), # Italian: reqs
                        'elements': getattr(move_obj, 'elem', getattr(move_obj, 'elements', [])),       # Italian: elem
                        'accuracy': getattr(move_obj, 'accuracy', getattr(move_obj, 'prec', 90)),      # accuracy or prec
                        'WPN': True  # Mark as weapon move
                    }
                    weapon_moves.append(weapon_move_dict)
                    print(f"[Battle] Added weapon move: {weapon_move_dict['name']} (type: {weapon_move_dict['type']})")
                else:
                    print(f"[Battle] Skipping invalid weapon move object: {type(move_obj)}")
            except Exception as move_error:
                print(f"[Battle] Error converting weapon move {getattr(move_obj, 'name', 'Unknown')}: {move_error}")
                import traceback
                traceback.print_exc()
        
        print(f"[Battle] Total weapon moves loaded: {len(weapon_moves)}")
        
    except ImportError:
        print("[Battle] Player_Equipment not available - no weapon moves")
    except Exception as e:
        print(f"[Battle] Error loading weapon moves: {e}")
        import traceback
        traceback.print_exc()
    
    return weapon_moves

def load_custom_moves_for_battle(character_name=None):
    """Load custom moves from character's save file using Save System for battle system"""
    try:
        # Get character name - try multiple sources
        if not character_name:
            # Try to get from global player variable
            if 'player' in globals() and hasattr(globals()['player'], 'name'):
                character_name = globals()['player'].name
            else:
                # Fallback: try character_data.json
                import json
                import os
                char_data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                            "character_data.json")
                if os.path.exists(char_data_file):
                    with open(char_data_file, 'r') as f:
                        char_data = json.load(f)
                        character_name = char_data.get('name')
        
        if not character_name:
            print("[Battle] Cannot load moves: no character name available")
            return None
        
        # Import and use Save System
        from Save_System import SaveSystem
        save_system = SaveSystem()
        
        # Load character's save data
        save_data = save_system.load_save(character_name)
        if save_data and 'player' in save_data and 'custom_moves' in save_data['player']:
            custom_moves = save_data['player']['custom_moves']
            if custom_moves:  # Has moves
                print(f"[Battle] Loaded {len(custom_moves)} custom moves for {character_name} from save file")
                return custom_moves
            else:  # Empty moves array - this is valid, don't fall back to legacy
                print(f"[Battle] {character_name} has no custom moves in save file")
                return None
        
        # Fallback: try legacy character_data.json
        try:
            import json
            import os
            save_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                    "character_data.json")
            
            if os.path.exists(save_file):
                with open(save_file, 'r') as f:
                    save_data = json.load(f)
                
                if 'custom_moves' in save_data:
                    print(f"[Battle] Loaded {len(save_data['custom_moves'])} custom moves from legacy character_data.json")
                    return save_data['custom_moves']
        except Exception as e:
            print(f"[Battle] Error loading from legacy file: {e}")
        
        print(f"[Battle] No custom moves found for {character_name}")
        return None  # No custom moves found
        
    except Exception as e:
        print(f"[Battle] Error loading custom moves: {e}")
        return None

def load_player_moves_from_system():
    """Load player moves from the Player_Moves system, prioritizing custom moves"""
    global player
    
    # First try to load custom moves with character name
    character_name = player.name if hasattr(player, 'name') else None
    custom_moves = load_custom_moves_for_battle(character_name)
    weapon_moves = load_weapon_moves_for_battle(character_name)

    # Simple approach: If custom moves exist, use them. Otherwise use default Player_Moves.
    if custom_moves:
        # Use custom moves + weapon moves
        all_moves = []
        all_moves.extend(custom_moves)
        if weapon_moves:
            all_moves.extend(weapon_moves)
        print(f"[Battle] Using {len(all_moves)} total moves ({len(custom_moves)} custom + {len(weapon_moves) if weapon_moves else 0} weapon)")
        
        # Clear existing player moves
        player.moves = []
        
        # Convert moves to battle system format and add them
        for move_data in all_moves:
            # Handle both 'effects' and 'buffs' fields for BUF moves
            effects_list = move_data.get('effects', [])
            
            # For BUF moves, also check for 'buffs' field and merge with effects
            if move_data['type'] == 'BUF' and 'buffs' in move_data:
                buffs_list = move_data.get('buffs', [])
                print(f"[Battle] BUF move '{move_data['name']}' has buffs field: {buffs_list}")
                # Merge buffs into effects list (buffs have priority)
                for buff in buffs_list:
                    if isinstance(buff, list) and len(buff) >= 2 and buff[1] > 0:
                        # Convert buff format [name, level] to effect format [name, level, duration, immunity]
                        buff_name, level = buff[0], buff[1]
                        # Effect-on-Hit buffs get permanent duration (999), others get shorter duration
                        effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
                        if buff_name in effect_on_hit_buffs:
                            effects_list.append([buff_name, level, 999, 0])
                            print(f"  → Added Effect-on-Hit buff: {buff_name} level {level}")
                        else:
                            # Regular buffs need 'buf_' prefix and shorter duration
                            buff_with_prefix = f"buf_{buff_name}" if not buff_name.startswith('buf_') else buff_name
                            effects_list.append([buff_with_prefix, level, 10, 0])
                            print(f"  → Added regular buff: {buff_with_prefix} level {level}")
            
            add_move_to_character(
                player, 
                move_data['name'], 
                move_data['type'],
                move_data['scaling']['forz'],
                move_data['scaling']['des'], 
                move_data['scaling']['spe'],
                effects=effects_list,
                requirements=move_data.get('requirements', []),
                elements=move_data.get('elements', []),
                accuracy=move_data.get('accuracy', 100)
            )
        
        print(f"[Combat] Loaded {len(all_moves)} total moves for battle ({len(custom_moves)} custom + {len(weapon_moves) if weapon_moves else 0} weapon)")
        return

    # No custom moves found - use default Player_Moves + weapon moves for new character
    
    # Lazy import to avoid circular dependencies
    global PLAYER_MOVES_AVAILABLE
    
    if not PLAYER_MOVES_AVAILABLE:
        try:
            global get_player_moves
            from Player_Moves import get_player_moves
            PLAYER_MOVES_AVAILABLE = True
        except ImportError as e:
            print(f"[Battle] Player_Moves system not available: {e}")
            setup_example_moves_with_requirements()
            return

    try:
        # Get player moves from the system
        player_moves_obj = get_player_moves()
        
        moves_list = player_moves_obj.get_all_moves()
        
        # Combine default moves with weapon moves
        all_moves = []
        if moves_list:
            all_moves.extend(moves_list)
        if weapon_moves:
            all_moves.extend(weapon_moves)
        
        # Clear existing player moves
        player.moves = []
        
        # Convert moves to battle system format and add them
        for move_data in all_moves:
            add_move_to_character(
                player, 
                move_data['name'], 
                move_data['type'],
                move_data['scaling']['forz'],
                move_data['scaling']['des'], 
                move_data['scaling']['spe'],
                effects=move_data.get('effects', []),
                requirements=move_data.get('requirements', []),
                elements=move_data.get('elements', []),
                accuracy=move_data.get('accuracy', 100)
            )
        
        print(f"[Combat] Loaded {len(moves_list)} default moves + {len(weapon_moves) if weapon_moves else 0} weapon moves from Player_Moves system")
        
    except Exception as e:
        print(f"[Battle] Error loading player moves: {e}")
        setup_example_moves_with_requirements()

def setup_example_moves_with_requirements():
    """Set up example moves demonstrating the new requirements system"""
    # Clear existing moves first
    player.moves = []
    enemy.moves = []
    
    # Player moves with different requirement types
    
    # Body part requirement move - requires both legs to have >1 HP
    add_move_to_character(
        player, "Devastating Dropkick", "ATK", 3, 2, 0,
        effects=[["stun", 2, 1, 0]], 
        requirements=["2 LEGS"], 
        elements=["IMPACT"], 
        accuracy=70
    )
    
    # Target-specific requirement move - must target head
    add_move_to_character(
        player, "Precise Headshot", "ATK", 2, 4, 0,
        effects=[["stun", 1, 1, 0]], 
        requirements=["TARGET HEAD","ARM"], 
        elements=["IMPACT"], 
        accuracy=100
    )
    
    # Status requirement move - target must be bleeding
    add_move_to_character(
        player, "Salt the Wound", "ATK", 0, 3, 3,
        effects=[["bleed", 2, 1, 0]], 
        requirements=["TARGET bleed","2 ARMS"], 
        elements=["CUT"], 
        accuracy=100
    )
    
    # Multiple requirements move - requires sword arm + target must be head + target must be stunned
    add_move_to_character(
        player, "Execution Strike", "ATK", 3, 5, 0,
        effects=[["stun", 3, 1, 0]], 
        requirements=["SWORD", "TARGET HEAD", "TARGET stun"], 
        elements=["CUT"], 
        accuracy=90
    )
    
    # Basic move with no requirements for comparison
    add_move_to_character(
        player, "Blade Hands", "ATK", 0, 1, 1,
        effects=[["bleed", 1, 1, 0]], 
        requirements=["2 ARMS"], 
        elements=["CUT"], 
        accuracy=90
    )
    
    # Sword requirement only
    add_move_to_character(
        player, "Sword Slash", "ATK", 3, 5, 0,
        effects=[], 
        requirements=["SWORD", "2 LEGS"], 
        elements=["CUT"], 
        accuracy= 90
    )

    # BUFF MOVES for testing new requirement-based system
    add_move_to_character(
        player, "Power Surge", "BUF", 0, 0, 0,
        effects=[["buf_dex", 3, 0, 0]], 
        requirements=["ARM"], 
        elements=["NONE"], 
        accuracy=100
    )
    
    add_move_to_character(
        player, "Adrenaline Rush", "BUF", 0, 0, 0,
        effects=[["buf_spe", 2, 0, 0]], 
        requirements=["HEAD"], 
        elements=["NONE"], 
        accuracy=100
    )
    
    add_move_to_character(
        player, "Defensive Stance", "BUF", 0, 0, 0,
        effects=[["buf_res", 4, 0, 0]], 
        requirements=["2 LEGS"], 
        elements=["NONE"], 
        accuracy=100
    )
    
    # DODGE BUFF - Requires 2 legs, allows evasion of attacks
    add_move_to_character(
        player, "Evasive Stance", "BUF", 0, 0, 0,
        effects=[["buf_dodge", 3, 0, 0]],  # Level 3 dodge for 3 successful evasions
        requirements=["2 LEGS"], 
        elements=["NONE"], 
        accuracy=100
    )
    
    # SHIELD BUFF - Requires 1 arm, allows blocking of attacks  
    add_move_to_character(
        player, "Defensive Guard", "BUF", 0, 0, 0,
        effects=[["buf_shield", 2, 0, 0]],  # Level 2 shield for 2 successful blocks
        requirements=["ARM"], 
        elements=["NONE"], 
        accuracy=100
    )

    # EXAMPLE Enemy moves with requirements
    
    # Basic enemy moves
    add_move_to_character(
        enemy, "Small Zap", "ATK", 0, 0, 1,
        effects=[["stun", 1, 1, 0]], 
        requirements=["TENTACLE"], 
        elements=["ELECTRIC"], 
        accuracy=90
    )

    # Basic enemy moves
    add_move_to_character(
        enemy, "Scratch", "ATK", 2, 1, 0,
        effects=[["bleed", 1, 1, 0]], 
        requirements=["ARM"], 
        elements=["CUT"], 
        accuracy=90
    )

    # Enemy move requiring tentacles
    add_move_to_character(
        enemy, "Electroshock", "ATK", 0, 1, 3,
        effects=[["stun", 2, 1, 0]], 
        requirements=["TENTACLE"], 
        elements=["ELECTRIC"], 
        accuracy=90
    )
    
    # Enemy move targeting stunned body part
    add_move_to_character(
        enemy, "Total Discharge", "ATK", 0, 1, 5,
        effects=[["stun", 2, 1, 0]], 
        requirements=["2 TENTACLES", "TARGET STUN"], 
        elements=["ELECTRIC"], 
        accuracy=90
    )
    
    # Enemy BUF moves for testing
    add_move_to_character(
        enemy, "Battle Fury", "BUF", 0, 0, 0,
        effects=[["buf_forz", 3, 0, 0]], 
        requirements=["HEAD"], 
        elements=["NONE"], 
        accuracy=100
    )
    
    add_move_to_character(
        enemy, "Electric Charge", "BUF", 0, 0, 0,
        effects=[["buf_spe", 2, 0, 0]], 
        requirements=["TENTACLE"], 
        elements=["ELECTRIC"], 
        accuracy=100
    )
    
    # Enemy DODGE BUFF - Requires 2 tentacles (or legs if enemy has legs)
    add_move_to_character(
        enemy, "Swift Evasion", "BUF", 0, 0, 0,
        effects=[["buf_dodge", 2, 0, 0]],  # Level 2 dodge for 2 successful evasions
        requirements=["2 TENTACLES"], 
        elements=["NONE"], 
        accuracy=100
    )
    
    # Enemy SHIELD BUFF - Requires 1 tentacle (or arm if enemy has arms)
    add_move_to_character(
        enemy, "Protective Shell", "BUF", 0, 0, 0,
        effects=[["buf_shield", 1, 0, 0]],  # Level 1 shield for 1 successful block
        requirements=["TENTACLE"], 
        elements=["NONE"], 
        accuracy=100
    )
    
    print("Example moves with requirements set up!")
    print("\nPlayer moves:")
    for i, move in enumerate(player.moves):
        print(f"  {i+1}. {move.name} - Cost: {move.stamina_cost}, Reqs: {move.reqs}")
    
    print("\nEnemy moves:")
    for i, move in enumerate(enemy.moves):
        print(f"  {i+1}. {move.name} - Cost: {move.stamina_cost}, Reqs: {move.reqs}")

def convert_battle_to_overworld_player(battle_player, overworld_player_stats):
    """
    Sync battle results back to overworld player stats.
    
    Args:
        battle_player: Character object from battle system
        overworld_player_stats: PlayerStats object from overworld
    """
    print(f"[Battle Integration] Syncing battle results back to overworld...")
    
    # Sync current body part HP values from battle back to overworld
    if len(battle_player.body_parts) >= 6:  # Ensure we have all standard body parts
        overworld_player_stats.head_hp = max(0, battle_player.body_parts[0].p_pvt)
        overworld_player_stats.right_arm_hp = max(0, battle_player.body_parts[1].p_pvt)
        overworld_player_stats.left_arm_hp = max(0, battle_player.body_parts[2].p_pvt)
        overworld_player_stats.body_hp = max(0, battle_player.body_parts[3].p_pvt)
        overworld_player_stats.right_leg_hp = max(0, battle_player.body_parts[4].p_pvt)
        overworld_player_stats.left_leg_hp = max(0, battle_player.body_parts[5].p_pvt)
        
        # Handle extra limbs if present
        if len(battle_player.body_parts) > 6 and overworld_player_stats.has_extra_limbs:
            overworld_player_stats.extral_limbs_hp = max(0, battle_player.body_parts[6].p_pvt)
    
    # Sync current stamina, regen, and reserve
    overworld_player_stats.stamina = max(0, battle_player.sta)
    overworld_player_stats.regen = max(0, battle_player.rig)
    overworld_player_stats.reserve = max(0, battle_player.res)
    
    # Recalculate total HP based on current body part values
    overworld_player_stats.hp = overworld_player_stats.calc_hp()
    
    # Sync weapon proficiency data from battle back to equipment system
    try:
        from Player_Equipment import get_main_player_equipment
        player_equip = get_main_player_equipment()
        if player_equip:
            # Weapon proficiency is already stored in the equipment system during battle
            # Just trigger a save to ensure it persists
            from Save_System import SaveSystem
            save_system = SaveSystem()
            character_name = overworld_player_stats.name if hasattr(overworld_player_stats, 'name') else None
            if character_name:
                # Load current save data
                save_data = save_system.load_save(character_name)
                if save_data:
                    # Update weapon proficiencies in save data
                    if 'weapon_proficiencies' not in save_data:
                        save_data['weapon_proficiencies'] = {}
                    
                    # Sync from equipment system to save data
                    for weapon_class in player_equip.weapon_proficiency.wpn_class_proficiency:
                        save_data['weapon_proficiencies'][weapon_class] = {
                            'proficiency': player_equip.weapon_proficiency.wpn_class_proficiency[weapon_class],
                            'experience': player_equip.weapon_proficiency.wpn_class_exp[weapon_class]
                        }
                    
                    # Save updated data
                    save_system.save_game(save_data, character_name)
                    print(f"[Battle Integration] Weapon proficiency data saved for {character_name}")
    except Exception as e:
        print(f"[Battle Integration] Error syncing weapon proficiency: {e}")
    
    print(f"[Battle Integration] Overworld stats updated after battle:")
    print(f"  Total HP: {overworld_player_stats.hp}/{overworld_player_stats.max_hp}")
    print(f"  Head HP: {overworld_player_stats.head_hp}/{overworld_player_stats.max_head_hp}")
    print(f"  Body HP: {overworld_player_stats.body_hp}/{overworld_player_stats.max_body_hp}")
    print(f"  Right Arm HP: {overworld_player_stats.right_arm_hp}/{overworld_player_stats.max_right_arm_hp}")
    print(f"  Left Arm HP: {overworld_player_stats.left_arm_hp}/{overworld_player_stats.max_left_arm_hp}")
    print(f"  Right Leg HP: {overworld_player_stats.right_leg_hp}/{overworld_player_stats.max_right_leg_hp}")
    print(f"  Left Leg HP: {overworld_player_stats.left_leg_hp}/{overworld_player_stats.max_left_leg_hp}")
    if overworld_player_stats.has_extra_limbs:
        # Get species-specific limb name
        species_config = get_species_config(overworld_player_stats.species)
        limb_name = species_config["body_parts"]["extra_limbs_name"] if species_config else "Extra Limbs"
        print(f"  {limb_name} HP: {overworld_player_stats.extral_limbs_hp}/{overworld_player_stats.max_extral_limbs_hp}")
    print(f"  Stamina: {overworld_player_stats.stamina}/{overworld_player_stats.max_stamina}")
    print(f"  Regen: {overworld_player_stats.regen}/{overworld_player_stats.max_regen}")
    print(f"  Reserve: {overworld_player_stats.reserve}/{overworld_player_stats.max_reserve}")

def convert_overworld_to_battle_player(player_stats):
    """
    Convert overworld PlayerStats to battle Character object.
    
    Args:
        player_stats: PlayerStats object from overworld
        
    Returns:
        Character: Converted battle character with actual current stats
    """
    print(f"[Battle Integration] Converting overworld player to battle character...")
    print(f"[Battle Integration] Player: {player_stats.name}")
    
    # Find the player GIF path for battle character image
    import os
    from pathlib import Path
    
    # Try to find player image in various locations
    gif_path = Path(player_stats.gif_path)
    if gif_path.exists():
        player_image_path = gif_path
    else:
        # Try relative to current working directory
        cwd_path = Path.cwd() / gif_path.name
        if cwd_path.exists():
            player_image_path = cwd_path
        else:
            # Fallback to a default path
            player_image_path = Path(__file__).parent.parent.parent.parent / "Player_GIFs" / "Maedo_Player_GIF.gif"
    
    print(f"[Battle Integration] Player image path: {player_image_path}")
    
    # Map overworld stats to battle stats:
    # total_hp -> max_pvt/pvt
    # max_regen -> max_rig/rig  
    # max_reserve -> max_res/res
    # max_stamina -> max_sta/sta
    # strength -> max_forz/forz
    # dexterity -> max_des/des
    # special -> max_spe/spe
    # speed -> max_vel/vel
    
    # Current values (use actual overworld current values, ensure they're refreshed)
    # Force recalculation of current stats to get latest values (important after level-ups)
    if hasattr(player_stats, 'update_main_stats'):
        player_stats.update_main_stats()
    
    current_regen = getattr(player_stats, 'regen', player_stats.max_regen)
    current_reserve = getattr(player_stats, 'reserve', player_stats.max_reserve) 
    current_stamina = getattr(player_stats, 'stamina', player_stats.max_stamina)
    
    print(f"[Battle Integration] Using current stats from overworld:")
    print(f"  Current stamina: {current_stamina}/{player_stats.max_stamina}")
    print(f"  Current regen: {current_regen}/{player_stats.max_regen}")
    print(f"  Current reserve: {current_reserve}/{player_stats.max_reserve}")
    print(f"  Strength: {player_stats.strength}")
    print(f"  Dexterity: {player_stats.dexterity}")
    print(f"  Special: {player_stats.special}")
    print(f"  Speed: {player_stats.speed}")
    print(f"  Current HP values:")
    print(f"    Head: {player_stats.head_hp}/{player_stats.max_head_hp}")
    print(f"    Body: {player_stats.body_hp}/{player_stats.max_body_hp}")
    print(f"    Right Arm: {player_stats.right_arm_hp}/{player_stats.max_right_arm_hp}")
    print(f"    Left Arm: {player_stats.left_arm_hp}/{player_stats.max_left_arm_hp}")
    print(f"    Right Leg: {player_stats.right_leg_hp}/{player_stats.max_right_leg_hp}")
    print(f"    Left Leg: {player_stats.left_leg_hp}/{player_stats.max_left_leg_hp}")
    if getattr(player_stats, 'has_extra_limbs', False):
        # Get species-specific limb name
        species_config = get_species_config(player_stats.species)
        limb_name = species_config["body_parts"]["extra_limbs_name"] if species_config else "Extra Limbs"
        print(f"    {limb_name}: {player_stats.extral_limbs_hp}/{player_stats.max_extral_limbs_hp}")
    
    # Create body parts from overworld data using CURRENT HP values from body parts
    battle_body_parts = [
        BodyPart("HEAD", int(player_stats.max_head_hp), int(player_stats.head_hp), Effetti(), Difese(), 0.5),  # 50% evasion for head
        BodyPart("RIGHT ARM", int(player_stats.max_right_arm_hp), int(player_stats.right_arm_hp), Effetti(), Difese(), 1),
        BodyPart("LEFT ARM", int(player_stats.max_left_arm_hp), int(player_stats.left_arm_hp), Effetti(), Difese(), 1),
        BodyPart("BODY", int(player_stats.max_body_hp), int(player_stats.body_hp), Effetti(), Difese(), 1),  # Fixed body evasion to 1 (100% hit chance)
        BodyPart("RIGHT LEG", int(player_stats.max_right_leg_hp), int(player_stats.right_leg_hp), Effetti(), Difese(), 1),
        BodyPart("LEFT LEG", int(player_stats.max_left_leg_hp), int(player_stats.left_leg_hp), Effetti(), Difese(), 1),
    ]
    
    # Add extra limbs if player has them
    if getattr(player_stats, 'has_extra_limbs', False) and getattr(player_stats, 'max_extral_limbs_hp', 0) > 0:
        # Get species-specific limb name
        species_config = get_species_config(player_stats.species)
        limb_name = species_config["body_parts"]["extra_limbs_name"] if species_config else "EXTRA LIMBS"
        extra_limbs_current_hp = player_stats.extral_limbs_hp  # Use actual current HP
        battle_body_parts.append(
            BodyPart(limb_name, int(player_stats.max_extral_limbs_hp), int(extra_limbs_current_hp), Effetti(), Difese(), 1)
        )
    
    # Create battle character using current HP values
    battle_player = Character(
        name=player_stats.name,
        max_pvt=int(player_stats.max_hp),    # Use actual max HP from calculated value
        pvt=int(player_stats.hp),            # Use current HP from calculated value
        max_rig=int(player_stats.max_regen),
        rig=int(current_regen),
        max_res=int(player_stats.max_reserve), 
        res=int(current_reserve),
        max_sta=int(player_stats.max_stamina),
        sta=int(current_stamina),
        max_for=int(player_stats.strength),
        forz=int(player_stats.strength),     # Current equals max for combat stats
        max_des=int(player_stats.dexterity),
        des=int(player_stats.dexterity),
        max_spe=int(player_stats.special),
        spe=int(player_stats.special),
        max_vel=int(player_stats.speed),
        vel=int(player_stats.speed),
        body_parts=battle_body_parts,
        image_path=str(player_image_path)
    )
    
    # Let Character.calculate_health_from_body_parts() recalculate total HP correctly
    battle_player.calculate_health_from_body_parts()
    
    # Set species from player_stats (essential for elemental resistance calculations)
    battle_player.species = player_stats.species
    print(f"[Battle Integration] Set species '{battle_player.species}' for battle player '{battle_player.name}'")
    
    print(f"[Battle Integration] Player conversion complete:")
    print(f"  Name: {battle_player.name}")
    print(f"  Species: {battle_player.species}")
    print(f"  Total HP: {battle_player.pvt}/{battle_player.max_pvt}")
    print(f"  RIG: {battle_player.rig}/{battle_player.max_rig}")
    print(f"  RES: {battle_player.res}/{battle_player.max_res}")
    print(f"  STA: {battle_player.sta}/{battle_player.max_sta}")
    print(f"  FORZ: {battle_player.forz}")
    print(f"  DES: {battle_player.des}")
    print(f"  SPE: {battle_player.spe}")
    print(f"  VEL: {battle_player.vel}")
    print(f"  Body parts: {len(battle_player.body_parts)}")
    
    return battle_player

# Create and run the pygame UI
def load_and_apply_volume_settings():
    """Load volume settings from game_settings.json and apply them to battle system"""
    global global_music_volume
    import json
    import os
    try:
        # Construct path to game_settings.json (4 levels up from current file)
        settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "game_settings.json")
        print(f"[Combat] Loading volume settings from: {settings_file}")
        
        # Default settings
        default_music_volume = 0.7
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                global_music_volume = settings.get('music_volume', default_music_volume)
                
                # Apply music volume
                pygame.mixer.music.set_volume(global_music_volume)
                print(f"[Combat] Applied music volume: {global_music_volume}")
                
                # Load SFX volume through Global_SFX module
                Global_SFX.load_global_sfx_volume()
                sfx_volume = Global_SFX.get_global_sfx_volume()
                print(f"[Combat] Loaded global SFX volume: {sfx_volume}")
                
                return global_music_volume, sfx_volume
        else:
            print(f"[Combat] Settings file not found, using defaults")
            global_music_volume = default_music_volume
            pygame.mixer.music.set_volume(global_music_volume)
            Global_SFX.load_global_sfx_volume()
            sfx_volume = Global_SFX.get_global_sfx_volume()
            return global_music_volume, sfx_volume
            
    except Exception as e:
        print(f"[Combat] Error loading volume settings: {e}")
        # Fallback to defaults
        global_music_volume = 0.7
        pygame.mixer.music.set_volume(global_music_volume)
        Global_SFX.load_global_sfx_volume()
        sfx_volume = Global_SFX.get_global_sfx_volume()
        return global_music_volume, sfx_volume

def start_combat_from_overworld(player_stats, enemy_npc, screenshot=None):
    """
    Start combat from overworld, return result
    
    Args:
        player_stats: PlayerStats object from overworld
        enemy_npc: Enemy NPC object from overworld
        screenshot: Screenshot surface for background (optional)
        
    Returns:
        'player_win', 'enemy_win', or None if escaped/cancelled
    """
    global enemy, player  # We need to modify the global enemy and player variables
    
    print(f"[Combat] start_combat_from_overworld called")
    print(f"[Combat] Player: {player_stats.name}, Enemy: {enemy_npc.name}")
    print(f"[Combat] Initializing battle system...")
    
    # Convert overworld player stats to battle character
    player = convert_overworld_to_battle_player(player_stats)
    
    # Initialize battle system if not already done
    if not hasattr(start_combat_from_overworld, 'initialized'):
        initialize_battle_system()
        start_combat_from_overworld.initialized = True
    
    # Load and apply volume settings from game configuration
    music_volume, sfx_volume = load_and_apply_volume_settings()
    
    # Stop overworld music and start battle music
    print(f"[Combat] Switching to battle music...")
    try:
        pygame.mixer.music.stop()  # Stop current music
        import time
        time.sleep(0.1)  # Small delay to ensure music stops
        
        # Start battle music with loaded volume
        battle_music_path = str(BACKGROUND_MUSIC_PATH)
        # Debug: print the resolved path
        print(f"[Combat] Battle music path resolved to: {battle_music_path}")
        if os.path.exists(battle_music_path):
            music_started = play_background_music(battle_music_path, volume=global_music_volume, loops=-1)
            if music_started:
                print(f"[Combat] Battle music started successfully with volume {global_music_volume}")
            else:
                print(f"[Combat] Failed to start battle music")
        else:
            print(f"[Combat] Battle music file not found: {battle_music_path}")
            # Try alternative path construction
            import pathlib
            alt_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "Musics" / "Battle-Walzer.MP3"
            print(f"[Combat] Trying alternative path: {alt_path}")
            if alt_path.exists():
                music_started = play_background_music(str(alt_path), volume=global_music_volume, loops=-1)
                if music_started:
                    print(f"[Combat] Battle music started with alternative path and volume {global_music_volume}")
                else:
                    print(f"[Combat] Failed to start battle music with alternative path")
            else:
                print(f"[Combat] Alternative path also not found")
    except Exception as e:
        print(f"[Combat] Error switching music: {e}")
    
    # Use the enemy's battle character if available
    if hasattr(enemy_npc, 'battle_character') and enemy_npc.battle_character is not None:
        print(f"[Combat] Using enemy battle character: {enemy_npc.battle_character.name}")
        enemy = enemy_npc.battle_character
    else:
        print(f"[Combat] Warning: No battle character found for {enemy_npc.name}, using default enemy")
        # Keep the default enemy if no battle character is defined
    
    print(f"[Combat] Battle system initialized")
    print(f"[Combat] Creating PygameUI instance...")
    
    # Initialize combat UI with overworld integration
    ui = PygameUI(player_stats=player_stats, enemy_npc=enemy_npc, return_to_overworld=True)
    
    print(f"[Combat] PygameUI instance created")
    print(f"[Combat] Setting up moves...")
    
    # Load player moves from the Player_Moves system
    load_player_moves_from_system()
    
    print(f"[Combat] Moves set up")
    print(f"[Combat] Starting UI run...")
    
    # TODO: Battle entry animation with screenshot will be implemented later
    # For now, just start the battle directly
    
    # Run combat and return result
    result = ui.run()
    
    print(f"[Combat] Battle ended with result: {result}")
    
    # Sync battle results back to overworld player stats
    if result in ['player_win', 'enemy_win']:  # Only sync if battle actually completed
        print(f"[Combat] Syncing battle results back to overworld...")
        convert_battle_to_overworld_player(player, player_stats)
    else:
        print(f"[Combat] No sync needed - battle did not complete normally")
    
    # After battle ends, stop battle music (overworld will restart its own music)
    print(f"[Combat] Battle ended, stopping battle music...")
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"[Combat] Error stopping battle music: {e}")
    
    return result

if __name__ == "__main__":
    # Initialize battle system for standalone execution
    initialize_battle_system()
    
    # Set up example moves with requirements to test the new system
    setup_example_moves_with_requirements()
    
    ui = PygameUI()
    ui.run()
#------------------------------------------------------------------------------------------------------------------

print("GUI main loop ended.")