#FUNZIONI
import random
import time
import traceback
import os
from pathlib import Path
from PIL import Image
import pygame
import sys

# Scaling factors for buff/debuff effects on stats
STAT_SCALING_FACTORS = {
    'rig': 5.0,    # rigenerazione scaling factor
    'res': 30.0,    # Resistenza scaling factor  
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
Turn = 0            # Overall turn counter (increases after both characters play)

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

# Music file path
BACKGROUND_MUSIC_PATH = Path(__file__).parent/ "Musics\Battle-Walzer.MP3"

# Sound effects folder path
SOUND_EFFECTS_PATH = Path(__file__).parent / "Sound Effects"

# Dictionary to cache loaded sound effects
sound_effects_cache = {}

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
    Play a sound effect from the Sound Effects folder.
    
    Args:
        sound_name (str): Name of the sound file (with or without extension)
        volume (float): Volume level (0.0 to 1.0)
        loops (int): Number of additional loops (0 = play once, -1 = loop forever)
    
    Returns:
        bool: True if sound was played successfully, False otherwise
    """
    try:
        sound = load_sound_effect(sound_name)
        if sound is None:
            return False
        
        # Set volume and play
        sound.set_volume(volume)
        sound.play(loops)
        print(f"Playing sound effect: {sound_name} (volume: {volume}, loops: {loops})")
        return True
    except Exception as e:
        print(f"Failed to play sound effect {sound_name}: {e}")
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

def calculate_move_damage(character, strength_scaling, dexterity_scaling, special_scaling):
    current_strength = getattr(character, 'forz', 0)
    current_dexterity = getattr(character, 'des', 0)
    current_special = getattr(character, 'spe', 0)
    
    damage = (strength_scaling * current_strength + 
              dexterity_scaling * current_dexterity + 
              special_scaling * current_special)
    
    return max(0, round(damage))  # Ensure damage is not negative and is an integer

def calculate_move_stamina_cost(strength_scaling, dexterity_scaling, special_scaling, effects=None, requirements=None, accuracy=100):
    # Base cost
    base_cost = 2
    
    # Sum of all scaling values
    scaling_sum = strength_scaling + dexterity_scaling + special_scaling
    
    # Effect cost - now based on the sum of effect levels
    effect_cost = 0
    if effects:
        for effect in effects:
            if isinstance(effect, list) and len(effect) >= 2:
                # New format: [name, level, duration, immunity] - use level (index 1)
                effect_level = effect[1] if isinstance(effect[1], (int, float)) else 1
                effect_cost += effect_level
            else:
                # Old format or invalid format - default to level 1
                effect_cost += 1
    
    # Requirement reduction
    num_requirements = len(requirements) if requirements else 0
    requirement_reduction = num_requirements * MOVE_STAMINA_SCALING_FACTORS['req_stm_sca_factor']
    
    # Accuracy bonus calculation
    # -1 stamina for every 10% under 90% accuracy
    # +1 stamina if accuracy is 100% or above
    accuracy_bonus = 0
    if accuracy < 90:
        # Calculate how many 10% increments below 90%
        accuracy_reduction = 90 - accuracy
        accuracy_bonus = -(accuracy_reduction // 10)  # Negative for cost reduction
    elif accuracy >= 100:
        accuracy_bonus = 1  # Penalty for perfect accuracy
    # If accuracy is 90-99%, bonus remains 0
    
    total_cost = base_cost + scaling_sum + effect_cost - requirement_reduction + accuracy_bonus
    
    return max(1, round(total_cost))  # Ensure minimum cost of 1 and is an integer

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
        if part.p_pvt < part.max_p_pvt:  # Only consider damaged parts
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
    
    # Check if enemy has enough stamina (though enemy stamina is usually full)
    if enemy.sta < 1:
        print(f"DEBUG: {enemy.name} cannot regenerate - insufficient STA: {enemy.sta}/1")
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

def enemy_auto_regenerate_multiple():
    """
    Automatically regenerate enemy body parts multiple times in the same turn.
    Continues regenerating as long as the enemy has enough RIG (>=5) and there are damaged parts.
    
    Returns:
        tuple: (total_regenerations_performed, regeneration_messages)
    """
    total_regenerations = 0
    regeneration_messages = []
    max_regenerations = 10  # Safety limit to prevent infinite loops
    rig_cost_per_regeneration = 5  # Cost of each regeneration
    stamina_cost_per_regeneration = 1  # Stamina cost of each regeneration
    
    print(f"DEBUG: Starting multiple regeneration cycle for {enemy.name}")
    print(f"DEBUG: Initial RIG: {enemy.rig}, Initial STA: {enemy.sta}")
    
    while total_regenerations < max_regenerations:
        # Check if enemy still has enough resources
        if enemy.rig < rig_cost_per_regeneration:
            print(f"DEBUG: {enemy.name} regeneration cycle ended - insufficient RIG: {enemy.rig}/{rig_cost_per_regeneration}")
            break
            
        if enemy.sta < stamina_cost_per_regeneration:
            print(f"DEBUG: {enemy.name} regeneration cycle ended - insufficient STA: {enemy.sta}/{stamina_cost_per_regeneration}")
            break
        
        # Find damaged parts
        damaged_parts = find_most_damaged_enemy_parts()
        
        if not damaged_parts:
            print(f"DEBUG: {enemy.name} regeneration cycle ended - no damaged parts to regenerate")
            break
        
        # Store the part name before regeneration (in case regeneration changes the order)
        part_to_regenerate = damaged_parts[0][1].name
        
        # Attempt regeneration
        regeneration_success = enemy_auto_regenerate()
        
        if regeneration_success:
            total_regenerations += 1
            regeneration_messages.append(f"{enemy.name} ha rigenerato {part_to_regenerate}!")
            print(f"DEBUG: Regeneration #{total_regenerations} completed. Current RIG: {enemy.rig}, STA: {enemy.sta}")
        else:
            print(f"DEBUG: {enemy.name} regeneration failed, ending cycle")
            break
    
    if total_regenerations > 0:
        print(f"DEBUG: {enemy.name} completed {total_regenerations} regenerations in this turn")
        print(f"DEBUG: Final RIG: {enemy.rig}, Final STA: {enemy.sta}")
    
    return total_regenerations, regeneration_messages

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
    
    # Check if the body part is already at full health
    if part.p_pvt >= part.max_p_pvt:
        print(f"DEBUG: {character.name}'s {part.name} is already at full health")
        return False
    
    # Check regeneration (rig) resource
    if character.rig < 5:
        print(f"DEBUG: {character.name} cannot regenerate - insufficient RIG: {character.rig}/5")
        return False
    
    # Check stamina resource
    if character.sta < 1:
        print(f"DEBUG: {character.name} cannot regenerate - insufficient STA: {character.sta}/1")
        return False
    
    # Apply regeneration
    old_pvt = part.p_pvt
    part.p_pvt = min(part.p_pvt + 5, part.max_p_pvt)  # Don't exceed max health
    actual_healing = part.p_pvt - old_pvt
    
    # Consume resources
    old_rig = character.rig
    character.rig -= 5
    character.sta -= 1
    
    print(f"DEBUG: {character.name} regeneration consumed resources - RIG: {old_rig} -> {character.rig}, STA: {character.sta + 1} -> {character.sta}")
    
    # Recalculate total health
    character.calculate_health_from_body_parts()
    
    print(f"DEBUG: Regenerated {character.name}'s {part.name}: {old_pvt} -> {part.p_pvt} (+{actual_healing})")
    print(f"DEBUG: {character.name} resources after regen - RIG: {character.rig}, STA: {character.sta}")
    
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
        # if self.body_parts:
          #   self.max_pvt = sum(part.max_p_pvt for part in self.body_parts)
          #   self.pvt = sum(part.p_pvt for part in self.body_parts)
            # print(f"{self.name}: Health recalculated - max_pvt: {self.max_pvt}, current pvt: {self.pvt}")
        # else:
            # print(f"Warning: {self.name} has no body parts for health calculation")

class BodyPart:
    def __init__(self, name, max_p_pvt, p_pvt, p_eff, p_difese, p_elusione):
        self.name = name
        self.max_p_pvt = max_p_pvt
        self.p_pvt = p_pvt
        self.p_eff = p_eff
        self.p_difese = p_difese
        self.p_elusione = p_elusione

class Effetti:
    def __init__(self, burn=None, bleed=None, poison=None, stun=None, confusion=None):
        # per ogni effetto di stato il primo elemento della lista è il nome dell'effetto, il secondo è il livello, il terzo la durata e il quarto l'immunità (0 non immune o 1 immune)
        #di base li setta tutti a zero, se vuoi settarne uno devi farlo separatamente.
        self.burn = burn if burn is not None else ["burn", 0, 0, 0]
        self.bleed = bleed if bleed is not None else ["bleed", 0, 0, 0]
        self.poison = poison if poison is not None else ["poison", 0, 0, 0]
        self.stun = stun if stun is not None else ["stun", 0, 0, 0]
        self.confusion = confusion if confusion is not None else ["confusion", 0, 0, 0]

class Buffs:
    def __init__(self, buf_rig=None, buf_res=None, buf_sta=None, buf_forz=None, buf_des=None, buf_spe=None, buf_vel=None):
        # per ogni buff/debuff il primo elemento della lista è il nome del buff, il secondo è il livello, il terzo la durata
        # di base li setta tutti a zero, se vuoi settarne uno devi farlo separatamente.
        self.buf_rig = buf_rig if buf_rig is not None else ["buf_rig", 0, 0]
        self.buf_res = buf_res if buf_res is not None else ["buf_res", 0, 0]
        self.buf_sta = buf_sta if buf_sta is not None else ["buf_sta", 0, 0]
        self.buf_forz = buf_forz if buf_forz is not None else ["buf_forz", 0, 0]
        self.buf_des = buf_des if buf_des is not None else ["buf_des", 0, 0]
        self.buf_spe = buf_spe if buf_spe is not None else ["buf_spe", 0, 0]
        self.buf_vel = buf_vel if buf_vel is not None else ["buf_vel", 0, 0]

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

player_image_path = Path(__file__).parent /"enemies_gifs" / "Selkio_NPC_1_gif.gif"

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
    BodyPart("HEAD", 20, 20, Effetti(), Difese(), 1),
    BodyPart("RIGHT ARM", 10, 10, Effetti(), Difese(), 1),
    BodyPart("LEFT ARM", 10, 10, Effetti(), Difese(), 1),
    BodyPart("BODY", 30, 30, Effetti(), Difese(), 2),
    BodyPart("RIGHT LEG", 15, 15, Effetti(),Difese(), 1),
    BodyPart("LEFT LEG", 15, 15, Effetti(),Difese(), 1),
]

player = Character(
    "JONNY BUONO",
    100, 80, 20, 20, 50, 40, 12, 12, 15, 15, 14, 14, 13, 13, 11, 11,
    player_body_parts,
    str(player_image_path)  # Convert Path to string for compatibility
)

enemy_body_parts = [
    BodyPart("HEAD", 1000, 1000, Effetti(), Difese(), 2),
    BodyPart("EYE", 300, 250, Effetti(), Difese(), 1),
    BodyPart("RIGHT CLAW", 25, 25, Effetti(), Difese(), 1),
    BodyPart("LEFT CLAW", 25, 25, Effetti(), Difese(), 1),
    BodyPart("TENTACLE (1)", 12, 12, Effetti(), Difese(), 1),
    BodyPart("TENTACLE (2)", 12, 8, Effetti(), Difese(), 1),
    BodyPart("TENTACLE (3)", 12, 12, Effetti(), Difese(), 1),
    BodyPart("TENTACLE (4)", 12, 12, Effetti(), Difese(), 1),
    BodyPart("TENTACLE (5)", 12, 5, Effetti(), Difese(), 1),
]

enemy = Character(
    "BLUBBERTONE",
    100, 80, 20, 20, 50, 40, 12, 12, 15, 15, 14, 14, 13, 13, 11, 11,
    enemy_body_parts,
    str(enemy_image_path)  # Convert Path to string for compatibility
)

#-------------------------------------------------------------------------------------------------------------------

# Essential utility functions that are used early in the code
def apply_status_effect(character, part_index, effect_name, level=1, duration=1, immunity=0):
    """
    Apply a status effect to a specific body part of a character.
    If the effect already exists, it stacks: level = sum of levels, duration = previous duration + 1.
    """
    if not (0 <= part_index < len(character.body_parts)):
        print(f"Invalid body part index {part_index} for character {getattr(character, 'name', 'Unknown')}")
        return
    part = character.body_parts[part_index]
    effetti = part.p_eff
    if not hasattr(effetti, effect_name):
        print(f"Effect '{effect_name}' not found on {part.name}")
        return
    
    # Get the current effect data
    current_effect = getattr(effetti, effect_name)
    
    # Check if the effect is already active (level > 0)
    if current_effect[1] > 0:  # level is at index 1
        # Stack the effect: sum levels, add 1 to duration, keep same immunity
        new_level = current_effect[1] + level
        new_duration = current_effect[2] + 1  # duration is at index 2
        existing_immunity = current_effect[3]  # immunity is at index 3
        
        setattr(effetti, effect_name, [effect_name, new_level, new_duration, existing_immunity])
        print(f"Stacked {effect_name} on {getattr(character, 'name', 'Unknown')} - {part.name}: Level {current_effect[1]} + {level} = {new_level}, Duration {current_effect[2]} + 1 = {new_duration}")
    else:
        # Apply new effect since none exists or it's inactive
        setattr(effetti, effect_name, [effect_name, level, duration, immunity])
        print(f"Applied {effect_name} to {getattr(character, 'name', 'Unknown')} - {part.name}: {[effect_name, level, duration, immunity]}")

def apply_move_effects(move, target_character, target_part_index=None):
    """
    Apply all status effects from a move to the target character.
    
    Args:
        move: The move object containing effects in eff_appl
        target_character: The character to apply effects to
        target_part_index: Index of the specific body part to target (if None, applies to random parts)
    """
    import random
    
    if not hasattr(move, 'eff_appl') or not move.eff_appl:
        return
    
    # Get all available effect names from the Effetti class
    available_effects = ['burn', 'bleed', 'poison', 'stun', 'confusion']
    
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
        
        # Check if effect name is valid
        if effect_name not in available_effects:
            print(f"  Unknown effect '{effect_name}' - skipping")
            continue
        
        # Select target body part
        if target_character.body_parts:
            if target_part_index is not None and 0 <= target_part_index < len(target_character.body_parts):
                # Apply to specific targeted body part
                part_index = target_part_index
                target_part = target_character.body_parts[part_index]
                print(f"  Applying {effect_name} to targeted body part: {target_part.name}")
            else:
                # Fall back to random body part if target_part_index is invalid or None
                part_index = random.randint(0, len(target_character.body_parts) - 1)
                target_part = target_character.body_parts[part_index]
                print(f"  Applying {effect_name} to random body part: {target_part.name}")
            
            # Apply the effect using the existing function
            # Apply the status effect to the selected body part
            apply_status_effect(target_character, part_index, effect_name, level, duration, immunity)
            print(f"  → {effect_name.upper()} applied to {target_part.name} (Level: {level}, Duration: {duration})")
        else:
            print(f"  → No body parts available on {char_name} to apply {effect_name}")

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
    available_effects = ['burn', 'bleed', 'poison', 'stun', 'confusion']
    
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

def activate_effects():
    """
    Apply the effects of all active status effects to all characters.
    This function should be called to process status effect damage/effects.
    
    Returns:
        list: List of messages about effects that were applied
    """
    messages = []
    
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
        
        # Check each body part for active status effects
        for part_index, part in enumerate(character.body_parts):
            if not hasattr(part, 'p_eff'):
                continue
            
            effetti = part.p_eff
            part_had_effects = False
            
            # Check for BLEED effect
            if hasattr(effetti, 'bleed'):
                bleed_data = getattr(effetti, 'bleed')
                
                # Check if bleed is active (level >= 1 and duration >= 1)
                if bleed_data[1] >= 1 and bleed_data[2] >= 1:
                    part_had_effects = True
                    
                    # Apply bleed damage (5 damage per level)
                    bleed_level = bleed_data[1]
                    damage = 5 * bleed_level
                    
                    old_pvt = part.p_pvt
                    part.p_pvt = max(0, part.p_pvt - damage)  # Don't go below 0
                    actual_damage = old_pvt - part.p_pvt
                    
                    message = f"{char_name}'s {part.name} takes {actual_damage} bleed damage (Level {bleed_level}): {old_pvt} -> {part.p_pvt}"
                    messages.append(message)
                    print(f"  → {message}")
            
            # Check for POISON effect
            if hasattr(effetti, 'poison'):
                poison_data = getattr(effetti, 'poison')
                
                # Check if poison is active (level >= 1 and duration >= 1)
                if poison_data[1] >= 1 and poison_data[2] >= 1:
                    part_had_effects = True
                    
                    # Apply poison damage (5 damage per level)
                    poison_level = poison_data[1]
                    damage = 5 * poison_level
                    
                    old_pvt = part.p_pvt
                    part.p_pvt = max(0, part.p_pvt - damage)  # Don't go below 0
                    actual_damage = old_pvt - part.p_pvt
                    
                    message = f"{char_name}'s {part.name} takes {actual_damage} poison damage (Level {poison_level}): {old_pvt} -> {part.p_pvt}"
                    messages.append(message)
                    print(f"  → {message}")
            
            # Check for BURN effect
            if hasattr(effetti, 'burn'):
                burn_data = getattr(effetti, 'burn')
                
                # Check if burn is active (level >= 1 and duration >= 1)
                if burn_data[1] >= 1 and burn_data[2] >= 1:
                    part_had_effects = True
                    
                    # Apply burn damage (5 damage per level)
                    burn_level = burn_data[1]
                    damage = 5 * burn_level
                    
                    old_pvt = part.p_pvt
                    part.p_pvt = max(0, part.p_pvt - damage)  # Don't go below 0
                    actual_damage = old_pvt - part.p_pvt
                    
                    message = f"{char_name}'s {part.name} takes {actual_damage} burn damage (Level {burn_level}): {old_pvt} -> {part.p_pvt}"
                    messages.append(message)
                    print(f"  → {message}")
            
            if not part_had_effects:
                print(f"  {part.name}: No active status effects")
        
        # Recalculate character's total health after applying effects
        character.calculate_health_from_body_parts()
    
    print("="*50)
    
    if not messages:
        print("No active status effects found on any characters")
    
    return messages

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
    
    print("="*50)
    
    return all_messages

def end_player_turn():
    """
    End the player's turn and update turn counters.
    This function should be called when the player completes their turn.
    """
    global turn_player, Turn
    
    turn_player += 1
    old_turn = Turn
    Turn = (turn_player + turn_enemy) // 2  # Integer division (rounded down)
    
    print(f"\n--- PLAYER TURN ENDED ---")
    print(f"Player turns completed: {turn_player}")
    print(f"Enemy turns completed: {turn_enemy}")
    print(f"Overall Turn: {old_turn} -> {Turn}")
    
    # Update the visual turn display
    #  draw_turn_display()
    
    if Turn > old_turn:
        print(f"*** ROUND {Turn} COMPLETED ***")
        # Process status effects when a full round is completed
        activate_effects()
        status_messages = decrease_all_characters_status_durations()
        if status_messages:
            print("Status effects processed at end of round.")
    
    return Turn

def end_enemy_turn():
    """
    End the enemy's turn and update turn counters.
    This function should be called when the enemy completes their turn.
    """
    global turn_enemy, Turn
    
    turn_enemy += 1
    old_turn = Turn
    Turn = (turn_player + turn_enemy) // 2  # Integer division (rounded down)
    
    print(f"\n--- ENEMY TURN ENDED ---")
    print(f"Player turns completed: {turn_player}")
    print(f"Enemy turns completed: {turn_enemy}")
    print(f"Overall Turn: {old_turn} -> {Turn}")
    
    # Update the visual turn display
    # update_turn_display()
    
    if Turn > old_turn:
        print(f"*** ROUND {Turn} COMPLETED ***")
        # Process status effects when a full round is completed
        activate_effects()
        status_messages = decrease_all_characters_status_durations()
        if status_messages:
            print("Status effects processed at end of round.")
    
    return Turn

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
    global turn_player, turn_enemy, Turn
    
    turn_player = 0
    turn_enemy = 0
    Turn = 0
    
    print("Turn counters reset to 0")
    # update_turn_display()  # Update the visual display
    display_turn_info()

def apply_buff_debuff(character, stat_name, level=1, duration=1):
    """
    Apply a buff or debuff to a character's stat using the new buffs system.
    If the buff already exists, it stacks: level = sum of levels, duration = previous duration + 1.
    
    Args:
        character: The character object
        stat_name (str): Name of the stat ('rig', 'res', 'sta', 'forz', 'des', 'spe', 'vel')
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
        'vel': 'buf_vel'
    }
    
    if stat_name not in stat_mapping:
        print(f"Invalid stat name '{stat_name}'. Valid stats are: {list(stat_mapping.keys())}")
        return
    
    buf_attr = stat_mapping[stat_name]
    
    if not hasattr(character, 'buffs') or not hasattr(character.buffs, buf_attr):
        print(f"Character {getattr(character, 'name', 'Unknown')} does not have buffs system or attribute '{buf_attr}'")
        return
    
    # Get current buff data
    current_buff = getattr(character.buffs, buf_attr)
    
    # Check if the buff is already active (level != 0 and duration > 0)
    if current_buff[1] != 0 and current_buff[2] > 0:
        # Stack the buff: sum levels, add 1 to duration
        new_level = current_buff[1] + level
        new_duration = current_buff[2] + 1
        
        setattr(character.buffs, buf_attr, [buf_attr, new_level, new_duration])
        print(f"Stacked buff/debuff on {getattr(character, 'name', 'Unknown')} - {stat_name}: Level {current_buff[1]} + {level} = {new_level}, Duration {current_buff[2]} + 1 = {new_duration}")
    else:
        # Apply new buff since none exists or it's inactive
        setattr(character.buffs, buf_attr, [buf_attr, level, duration])
        print(f"Applied buff/debuff to {getattr(character, 'name', 'Unknown')} - {stat_name}: Level {level}, Duration {duration}")
    
    # Update the character's current stats based on the new buff values
    update_character_stats(character)
    
    buff_type = "buff" if level > 0 else "debuff"
    print(f"Applied {buff_type} to {getattr(character, 'name', 'Unknown')} - {stat_name} successfully")

def get_character_buff_level(character, stat_name):
    """
    Get the current buff level for a specific stat from the new buffs system.
    This function is for compatibility with UI code that expects numeric buff values.
    
    Args:
        character: The character object
        stat_name (str): Name of the stat ('rig', 'res', 'sta', 'forz', 'des', 'spe', 'vel')
    
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
        'vel': 'buf_vel'
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

    # Reset and apply status effects after characters are created
    apply_status_effect(enemy, 3, 'burn', level=3, duration=4, immunity=0)

    # Apply initial stat updates after characters are created
    update_all_characters_stats()

    # Example of adding moves to characters
    add_move_to_character(player, "Fendente", "ATK", 1, 1, 0, 
                         effects=[["Bleed", 1, 1, 0], ["Stun", 1,2,0]], requirements=["SPADA"], 
                         elements=["CUT"], accuracy=90)

    add_move_to_character(player, "Grido di  Battaglia", "BUF", 0.0, 0.0, 1.0, 
                         effects=[["Burn", 1, 1, 0]], requirements=["TESTA"], 
                         elements=["ROAR"], accuracy=100)

    add_move_to_character(player, "Schivata", "REA", 0.0, 1.5, 0.0, 
                         effects=[["Stun", 1, 1, 0]], requirements=["2 GAMBE"], 
                         elements=["IMPACT"], accuracy=80)
    
    add_ability_to_character(player, "Chanche!", 1, "se CONFUSE/STUN, +1 FORZ", 
                         "I suoi attacchi fanno danni extra contro gli obbiettivi con lo status CONFUSE o STUN, come se il tuo personaggio avesse +1 STR")

    add_ability_to_character(player, "Dentistretti", 1, "se BURN/POISON, +1 FORZ",  
                         "I suoi attacchi fanno danni extra contro gli obbiettivi con lo status BURN o POISON, come se il tuo personaggio avesse +1 FORZ")
    # Add some example moves to the enemy
    add_move_to_character(enemy, "Tentacle Slam", "ATK", 1.0, 0.5, 0.0, 
                         effects=[["Stun", 1, 1, 0]], requirements=[], 
                         elements=["IMPACT"], accuracy=75)

    add_move_to_character(enemy, "Toxic Spray", "ATK", 0.3, 0.0, 1.2, 
                         effects=[["Stun", 1, 1, 0]], requirements=[], 
                         elements=["SPRAY"], accuracy=90)

    # Add 3 additional moves to the enemy for testing
    add_move_to_character(enemy, "Crushing Bite", "ATK", 1.5, 0.2, 0.0, 
                         effects=[["Stun", 1, 1, 0]], requirements=[], 
                         elements=["CUT"], accuracy=80)

    add_move_to_character(enemy, "Acid Spit", "ATK", 0.5, 0.8, 1.0, 
                         effects=[["burn", 2, 2, 0]], requirements=[], 
                         elements=["SPRAY"], accuracy=75)

    add_move_to_character(enemy, "Intimidating Roar", "BUF", 0.0, 0.0, 0.5, 
                         effects=[["stun", 1, 1, 0]], requirements=[], 
                         elements=["ROAR"], accuracy=95)

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

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),pygame.RESIZABLE)
        pygame.display.set_caption("RPG FIGHTING SYSTEM")
        self.clock = pygame.time.Clock()
        font_path = Path(__file__).parent / "Pixellari.ttf"
        # Store base font sizes (design-space) and create initial fonts
        self._font_path = font_path
        self._base_font_sizes = {
            'big': 28,
            'large': 24,
            'medium': 20,
            'small': 16
        }
        self.font_big = pygame.font.Font(str(font_path), self._base_font_sizes['big'])
        self.font_large = pygame.font.Font(str(font_path), self._base_font_sizes['large'])
        self.font_medium = pygame.font.Font(str(font_path), self._base_font_sizes['medium'])
        self.font_small = pygame.font.Font(str(font_path), self._base_font_sizes['small'])

        # Track current window size
        self.current_width, self.current_height = self.screen.get_size()
        self.ref_width = REF_WIDTH
        self.ref_height = REF_HEIGHT

        # Base (design reference) positions/sizes for elements to be scaled
        # Event log (from original fixed coordinates at 1600x1000)
        self.base_log_x = SCREEN_WIDTH // 2 + 300  # 1100
        self.base_log_y = SCREEN_HEIGHT - 500      # 500
        self.base_log_width = SCREEN_WIDTH // 2 - 175  # 625
        self.base_log_height = 480

        # UI state
        self.menu_selection_index = 0
        self.enemy_parts_index = 0
        self.moves_selection_index = 0
        self.running = True
        self.player_has_control = True
        self.regeneration_mode_active = False

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

        # Menu items
        self.menu_labels = ["ENEMY", "MOVES", "EFFECTS", "ABILITIES", "ITEMS", "PASS"]

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
        
        # Initialize target selection state
        self.target_selection_active = False
        self.target_selection_index = 0
        self.selected_move = None

        # Perform initial layout & font scaling pass
        self._recompute_layout()

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
        self.font_big = pygame.font.Font(str(self._font_path), clamp(self._base_font_sizes['big']))
        self.font_large = pygame.font.Font(str(self._font_path), clamp(self._base_font_sizes['large']))
        self.font_medium = pygame.font.Font(str(self._font_path), clamp(self._base_font_sizes['medium']))
        self.font_small = pygame.font.Font(str(self._font_path), clamp(self._base_font_sizes['small']))

    def _recompute_layout(self):
        """Recalculate all geometry dependent on window size."""
        # Update current size
        self.current_width, self.current_height = self.screen.get_size()

        # Scale log geometry
        self.log_x = self.sx(self.base_log_x)
        self.log_y = self.sy(self.base_log_y)
        self.log_width = max(150, self.sx(self.base_log_width))
        self.log_height = max(120, self.sy(self.base_log_height))

        # Update fonts after size change
        self._scale_fonts()

        # (Future) Add other panel geometry scaling here
        # Placeholder attributes for future proportional panels can be added safely
        # print(f"DEBUG: Layout recomputed -> size=({self.current_width},{self.current_height}) log=({self.log_x},{self.log_y},{self.log_width},{self.log_height})")

    def add_log_entry(self, message, log_type="info", color=None):
        """
        Add an entry to the event log
        
        Args:
            message (str): The message to log
            log_type (str): Type of log entry ('info', 'error', 'success', 'warning', 'combat')
            color (tuple): Custom color override (R, G, B)
        """
        import time
        
        # Define colors for different log types
        type_colors = {
            'info': (255, 255, 255),        # White
            'error': (255, 100, 100),       # Light red
            'success': (100, 255, 100),     # Light green
            'warning': (255, 200, 100),     # Orange/yellow
            'combat': (255, 255, 100),      # Yellow
            'system': (100, 200, 255),      # Light blue
            'regeneration': (0, 255, 200),  # Cyan
            'turn': (200, 200, 255)         # Light purple
        }
        
        # Use custom color or default for type
        entry_color = color if color else type_colors.get(log_type, (255, 255, 255))
        
        # Get current time for timestamp
        timestamp = time.strftime("%H:%M:%S")
        
        # Create log entry
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'type': log_type,
            'color': entry_color
        }
        
        # Add to log
        self.event_log.append(log_entry)
        
        # Trim log if it gets too long
        if len(self.event_log) > self.max_log_entries:
            self.event_log = self.event_log[-self.max_log_entries:]
            # Adjust scroll offset if needed
            if self.log_scroll_offset > 0:
                self.log_scroll_offset = max(0, self.log_scroll_offset - 1)
        
        # Auto-scroll to bottom when new entries are added
        self.scroll_log_to_bottom()
        
        print(f"LOG [{log_type.upper()}]: {message}")

    def scroll_log_to_bottom(self):
        """Scroll the log to show the most recent entries"""
        total_lines = len(self.event_log)
        if total_lines > self.log_visible_lines:
            self.log_scroll_offset = total_lines - self.log_visible_lines
        else:
            self.log_scroll_offset = 0

    def scroll_log(self, direction):
        """
        Scroll the log up or down
        
        Args:
            direction (int): Positive to scroll down, negative to scroll up
        """
        total_lines = len(self.event_log)
        max_scroll = max(0, total_lines - self.log_visible_lines)
        
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
        
        offset = 25  # Offset for title and separator
        # Draw log title
        title_y = self.log_y + offset + 5
        self.draw_text("EVENT LOG", self.font_medium, WHITE, self.log_x + self.log_width // 2, title_y, center=True)
        
        # Draw separator line
        separator_y = title_y + offset
        pygame.draw.line(self.screen, WHITE, 
                        (self.log_x + 10, separator_y), 
                        (self.log_x + self.log_width - 10, separator_y), 1)
        
        # Calculate text area
        text_start_y = separator_y + 10
        text_area_height = self.log_height - (text_start_y - self.log_y) - 10
        line_height = 20
        
        # Text wrapping parameters - use almost full width with margins
        left_margin = 10
        right_margin = 10
        available_text_width = self.log_width - left_margin - right_margin - 15  # Extra space for scrollbar
        
        # Calculate how many lines we can show
        max_visible_lines = text_area_height // line_height
        self.log_visible_lines = max_visible_lines
        
        # Draw log entries
        if self.event_log:
            # Determine which entries to show based on scroll offset
            start_index = self.log_scroll_offset
            end_index = min(start_index + max_visible_lines, len(self.event_log))
            
            current_line = 0  # Track current line for display
            
            for i in range(start_index, end_index):
                if i < len(self.event_log) and current_line < max_visible_lines:
                    entry = self.event_log[i]
                    
                    # Create full message with timestamp
                    full_message = f"[{entry['timestamp']}] {entry['message']}"
                    
                    # Word wrap the message to fit the available width
                    wrapped_lines = self.wrap_text(full_message, self.font_small, available_text_width)
                    
                    # Draw each wrapped line
                    for line_idx, line in enumerate(wrapped_lines):
                        if current_line >= max_visible_lines:
                            break
                        
                        line_y = text_start_y + current_line * line_height
                        
                        # Indent continuation lines (lines after the first one)
                        indent = 0 if line_idx == 0 else 20
                        
                        self.draw_text(line, self.font_small, entry['color'], 
                                    self.log_x + left_margin + indent, line_y)
                        
                        current_line += 1
        else:
            # No log entries
            no_entries_y = text_start_y + 20
            self.draw_text("No events logged yet", self.font_small, GRAY, 
                        self.log_x + self.log_width // 2, no_entries_y, center=True)
        
        # Draw scrollbar if needed
        total_entries = len(self.event_log)
        if total_entries > max_visible_lines:
            self.draw_log_scrollbar(total_entries, max_visible_lines)

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
    
    def draw_log_scrollbar(self, total_entries, visible_lines):
        """Draw a scrollbar for the log"""
        scrollbar_x = self.log_x + self.log_width - 15
        scrollbar_y = self.log_y + 65  # Start below title
        scrollbar_width = 10
        scrollbar_height = self.log_height - 75  # Leave space for title
        
        # Draw scrollbar background
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
        
        # Calculate scrollbar thumb size and position
        if total_entries > visible_lines:
            thumb_height = max(20, int(scrollbar_height * (visible_lines / total_entries)))
            max_thumb_y = scrollbar_height - thumb_height
            thumb_y = scrollbar_y + int(max_thumb_y * (self.log_scroll_offset / (total_entries - visible_lines)))
            
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

    def regenerate_body_part_pygame(self, character, part_index):
        """Regenerate a specific body part (pygame version)"""
        # Check if part index is valid
        if not (0 <= part_index < len(character.body_parts)):
            self.set_message(f"Indice parte del corpo non valido: {part_index}", 1500)  # ← FIXED
            return False
        
        part = character.body_parts[part_index]
        
        # Check if the body part is already at full health
        if part.p_pvt >= part.max_p_pvt:
            self.set_message("Questa parte del corpo è già completamente guarita!", 1500)  # ← FIXED
            return False
        
        # Check regeneration (rig) resource
        if character.rig < 5:
            self.set_message("Non puoi più rigenerarti!", 1500)  # ← FIXED
            return False
        
        # Check stamina resource
        if character.sta < 1:
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
        character.sta -= 1
        
        # Recalculate total health
        character.calculate_health_from_body_parts()
        
        # Show success message
        self.set_message(f"Rigenerato {part.name}: +{actual_healing} HP\nRIG: -{5}, STA: -{1}", 2000)  # ← FIXED
        
        print(f"Regenerated {character.name}'s {part.name}: {old_pvt} -> {part.p_pvt} (+{actual_healing})")
        
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

    def draw_enemy_part_attributes(self):
        """Draw attributes panel for the selected enemy part (pygame version)"""
        if self.menu_selection_index == 0 and 0 <= self.enemy_parts_index < len(enemy.body_parts):
            part = enemy.body_parts[self.enemy_parts_index]
            
            # Calculate position for the attributes panel (to the right of enemy parts list)
            panel_x = 1450  # Right side of screen
            panel_y = 80   # Vertically centered
            panel_width = 275
            panel_height = 350
            
            # Draw panel background
            pygame.draw.rect(self.screen, BLACK, (panel_x, panel_y, panel_width, panel_height))
            pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
            
            # Title - Part name
            self.draw_text(part.name, self.font_large, WHITE, panel_x + 10, panel_y + 15)
            
            # PVT Bar section
            pvt_y = panel_y + 60
            self.draw_text("PVT", self.font_medium, GREEN, panel_x + 10, pvt_y)
            
            # Draw PVT bar
            bar_x = panel_x + 60
            bar_y = pvt_y + 5
            bar_width = 200
            bar_height = 18
            
            # Background bar
            pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
            
            # Health fill
            if part.max_p_pvt > 0:
                fill_width = int(bar_width * part.p_pvt / part.max_p_pvt)
                pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, fill_width, bar_height))
            
            # HP text on bar
            hp_text = f"{part.p_pvt}/{part.max_p_pvt}"
            self.draw_text(hp_text, self.font_small, WHITE, bar_x + bar_width//2, bar_y + bar_height//2, center=True)
            
            # Effects section
            effects_y = panel_y + 120
            self.draw_text("Effetti:", self.font_medium, WHITE, panel_x + 10, effects_y)
            
            # Draw individual effects
            effect_y_offset = effects_y + 30
            effects_found = False
            
            if hasattr(part, 'p_eff'):
                effetti = part.p_eff
                
                # Check each effect type
                effect_names = ['burn', 'bleed', 'poison', 'stun', 'confusion']
                
                for eff_name in effect_names:
                    if hasattr(effetti, eff_name):
                        eff_val = getattr(effetti, eff_name)
                        
                        # Check if effect is active (level != 0)
                        if isinstance(eff_val, list) and len(eff_val) >= 4 and eff_val[1] != 0:
                            effects_found = True
                            
                            # Format effect info: [name, level, duration, immunity]
                            effect_text = f"{eff_name.upper()}:"
                            effect_details = f"Lv.{eff_val[1]}, Dur.{eff_val[2]}, Imm.{eff_val[3]}"
                            
                            # Draw effect name
                            self.draw_text(effect_text, self.font_small, (0, 224, 224), panel_x + 20, effect_y_offset)  # Cyan color
                            
                            # Draw effect details on next line
                            self.draw_text(effect_details, self.font_small, (0, 224, 224), panel_x + 25, effect_y_offset + 18)
                            
                            effect_y_offset += 45  # Space for next effect
            
            # If no active effects found
            if not effects_found:
                self.draw_text("Nessun effetto attivo", self.font_small, GRAY, panel_x + 20, effect_y_offset)

    def show_target_selection(self, move):
        """Show target selection mode (FIXED)"""
        print(f"DEBUG: show_target_selection called for move: {move.name}")
        
        # Initialize target selection state
        self.target_selection_active = True
        self.target_selection_index = 0
        self.selected_move = move
        
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
        
        self.target_selection_active = False
        self.selected_move = None
        self.target_selection_index = 0
        
        # Return to moves menu
        self.menu_selection_index = 1
        
        print("Target selection cancelled - returned to moves menu")

    def execute_selected_move(self):
        """Execute the selected move on the selected target (FIXED with animation delay)"""
        if not self.target_selection_active or not hasattr(self, 'selected_move') or not self.selected_move:
            print("DEBUG: execute_selected_move - No active target selection or move")
            return
        
        target_part = enemy.body_parts[self.target_selection_index]
        move = self.selected_move
        
        print(f"DEBUG: Executing {move.name} on {target_part.name}")
        
        # Check if player still has enough stamina
        if player.sta < move.stamina_cost:
            self.show_error_message("Non hai abbastanza stamina!", 1500)
            return
        
        # Step 1: Subtract stamina cost from player
        old_stamina = player.sta
        player.sta -= move.stamina_cost
        
        # Ensure stamina doesn't go below 0
        if player.sta < 0:
            player.sta = 0
        
        print(f"STAMINA DEBUG: Player stamina {old_stamina} -> {player.sta} (reduced by {move.stamina_cost})")
        
        # Step 2: Calculate accuracy roll
        import random
        accuracy_roll = random.randint(1, 100)
        print(f"Accuracy roll: {accuracy_roll}, Move accuracy: {move.accuracy}")
        
        if accuracy_roll > move.accuracy:
            # Miss - show miss message and play miss sound
            miss_message = f"{player.name} ha fallito l'attacco!"
            self.show_warning_message(miss_message, 1500)
            print(f"Attack missed! {miss_message}")
            
            # Play miss sound effect
            play_sound_effect("mixkit-punch-through-air-2141.mp3", volume=4)
            
            # Make player blink red to indicate miss
            self.blink_character_gif("player", (255, 100, 100), 200, 2)
            
            # SET DELAY FOR MISS ANIMATION - Wait for blink animation to complete
            animation_delay = 2 * 200 + 500  # 2 blinks * 200ms each + 500ms buffer = 900ms
            pygame.time.set_timer(pygame.USEREVENT + 3, animation_delay)  # Custom event for returning to moves menu
            
        else:
            # Hit - show hit message, play hit sound, and apply damage
            hit_message = f"{player.name} ha colpito {target_part.name} del {enemy.name}!"
            self.show_success_message(hit_message, 2000)
            
            # Apply damage
            old_hp = target_part.p_pvt
            damage_to_deal = move.danno
            target_part.p_pvt = max(0, target_part.p_pvt - damage_to_deal)
            actual_damage = old_hp - target_part.p_pvt
                
            print(f"Damage applied to {enemy.name}'s {target_part.name}: {old_hp} -> {target_part.p_pvt} (Damage: {actual_damage})")

            # Recalculate enemy health
            enemy.calculate_health_from_body_parts()

            # Apply status effects from the move to the targeted body part
            apply_move_effects(move, enemy, self.target_selection_index)

            # Make enemy blink to show damage
            self.blink_character_gif("enemy", (255, 0, 0), 300, 3)

            # Play appropriate sound effect based on move element
            if "CUT" in move.elem:
                play_sound_effect("mixkit-quick-knife-slice-cutting-2152.wav", volume=4)
            elif "IMPACT" in move.elem:
                play_sound_effect("mixkit-sword-strikes-armor-2765", volume=4)
            elif "SPRAY" in move.elem:
                play_sound_effect("acid_spell_cast_squish_ball_impact_01-286782", volume=4)
            elif "ROAR" in move.elem:
                play_sound_effect("tiger-roar-loudly-193229", volume=4)
            else:
                play_sound_effect("mixkit-impact-of-a-strong-punch-2155", volume=4)
            
            # SET DELAY FOR HIT ANIMATION - Wait for blink animation to complete
            animation_delay = 3 * 300 + 500  # 3 blinks * 300ms each + 500ms buffer = 1400ms
            pygame.time.set_timer(pygame.USEREVENT + 3, animation_delay)  # Custom event for returning to moves menu
        
        # DON'T immediately end target selection - let the timer handle it
        print("DEBUG: Attack executed, waiting for animation to complete before returning to moves menu")

    def finish_player_attack_sequence(self):
        """Complete the player attack sequence and return to moves menu (NEW METHOD)"""
        print("DEBUG: Animation sequence completed, returning to moves menu")
        
        # Clear the timer
        pygame.time.set_timer(pygame.USEREVENT + 3, 0)
        
        # Now end target selection and return to moves menu
        self.cancel_target_selection()

    def use_selected_move(self):
        """Use the currently selected move (FIXED for pygame)"""
        print("DEBUG: use_selected_move called")
        
        if not hasattr(player, 'moves') or not player.moves:
            print("DEBUG: Player has no moves")
            return
        
        if not hasattr(self, 'moves_selection_index') or self.moves_selection_index < 0 or self.moves_selection_index >= len(player.moves):
            print(f"DEBUG: Invalid move selection index: {getattr(self, 'moves_selection_index', 'None')}")
            return
        
        selected_move = player.moves[self.moves_selection_index]
        print(f"DEBUG: Selected move: {selected_move.name}, cost: {selected_move.stamina_cost}")
        
        # Check if player has enough stamina
        if player.sta < selected_move.stamina_cost:
            self.show_error_message("Non hai abbastanza stamina!", 1500)
            print(f"DEBUG: Not enough stamina! Required: {selected_move.stamina_cost}, Current: {player.sta}")
            return
        
        print("DEBUG: Player has enough stamina, starting target selection")
        # Player has enough stamina - start target selection
        self.show_target_selection(selected_move)

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

    def handle_events(self):
        """Handle pygame events (UPDATED with log scrolling support)"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                # Update screen surface to new size and recompute layout
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self._recompute_layout()
                continue
            
            # Handle log scrolling FIRST (highest priority)
            elif self.handle_log_scroll(event):
                continue  # Log scroll was handled, skip other event processing
            
            elif event.type == pygame.KEYDOWN:
                # Handle debug keys first
                if event.key == pygame.K_F1:
                    self.debug_stamina_info()
                elif event.key == pygame.K_F2:
                    player.sta = max(0, player.sta - 2)
                    self.add_log_entry(f"DEBUG: Player stamina reduced to {player.sta}", "system")
                elif event.key == pygame.K_F3:
                    self.restore_stamina(player, 2)
                elif event.key == pygame.K_F4:  # Clear log hotkey
                    self.clear_log()
                
                # NEW: Keyboard log scrolling controls
                elif event.key == pygame.K_z:  # Scroll log UP
                    self.scroll_log(-2)  # Negative value scrolls up
                    continue  # Skip other event processing
                elif event.key == pygame.K_x:  # Scroll log DOWN
                    self.scroll_log(2)   # Positive value scrolls down
                    continue  # Skip other event processing
                
                # Don't allow most navigation during enemy turn
                if not self.player_has_control:
                    if event.key == pygame.K_r:
                        self.add_log_entry("Cannot use regeneration during enemy turn", "warning")
                    continue
                
                # TARGET SELECTION has HIGHEST PRIORITY
                if hasattr(self, 'target_selection_active') and self.target_selection_active:
                    if event.key == pygame.K_UP:
                        old_index = getattr(self, 'target_selection_index', 0)
                        self.target_selection_index = (old_index - 1) % len(enemy.body_parts)
                        self.add_log_entry(f"Target: {enemy.body_parts[self.target_selection_index].name}", "combat")
                        
                    elif event.key == pygame.K_DOWN:
                        old_index = getattr(self, 'target_selection_index', 0)
                        self.target_selection_index = (old_index + 1) % len(enemy.body_parts)
                        self.add_log_entry(f"Target: {enemy.body_parts[self.target_selection_index].name}", "combat")
                        
                    elif event.key == pygame.K_SPACE:
                        self.execute_selected_move()
                        
                    elif event.key == pygame.K_ESCAPE:
                        self.cancel_target_selection()
                    
                    continue  # Skip other navigation when in target selection
                
                # Regeneration mode navigation
                elif hasattr(self, 'regeneration_mode_active') and self.regeneration_mode_active:
                    if event.key == pygame.K_UP:
                        self.regeneration_selection_index = (self.regeneration_selection_index - 1) % len(player.body_parts)
                        self.add_log_entry(f"Regeneration target: {player.body_parts[self.regeneration_selection_index].name}", "regeneration")
                    elif event.key == pygame.K_DOWN:
                        self.regeneration_selection_index = (self.regeneration_selection_index + 1) % len(player.body_parts)
                        self.add_log_entry(f"Regeneration target: {player.body_parts[self.regeneration_selection_index].name}", "regeneration")
                    elif event.key == pygame.K_SPACE:
                        success = self.regenerate_body_part_pygame(player, self.regeneration_selection_index)
                    elif event.key == pygame.K_r or event.key == pygame.K_ESCAPE:
                        self.toggle_regeneration_mode()
                    continue
                
                # Normal navigation
                else:
                    if event.key == pygame.K_LEFT:
                        self.menu_selection_index = (self.menu_selection_index - 1) % len(self.menu_labels)
                        self.add_log_entry(f"Menu: {self.menu_labels[self.menu_selection_index]}", "system")
                    elif event.key == pygame.K_RIGHT:
                        self.menu_selection_index = (self.menu_selection_index + 1) % len(self.menu_labels)
                        self.add_log_entry(f"Menu: {self.menu_labels[self.menu_selection_index]}", "system")
                    
                    elif event.key == pygame.K_UP:
                        if self.menu_selection_index == 0:  # ENEMY menu
                            self.enemy_parts_index = (self.enemy_parts_index - 1) % len(enemy.body_parts)
                            self.add_log_entry(f"Examining: {enemy.body_parts[self.enemy_parts_index].name}", "info")
                        elif self.menu_selection_index == 1:  # MOVES menu
                            if hasattr(player, 'moves') and player.moves:
                                self.moves_selection_index = (self.moves_selection_index - 1) % len(player.moves)
                                move = player.moves[self.moves_selection_index]
                                self.add_log_entry(f"Move: {move.name} (DMG: {move.danno}, STA: {move.stamina_cost})", "combat")
                        elif self.menu_selection_index == 3:  # ABILITIES menu
                            if hasattr(player, 'ability') and player.ability:
                                self.ability_selection_index = (getattr(self, 'ability_selection_index', 0) - 1) % len(player.ability)
                                ability = player.ability[self.ability_selection_index]
                                self.add_log_entry(f"Ability: {ability.name}", "info")
                        elif self.menu_selection_index == 5:  # PASS menu
                            self.pass_selection = (getattr(self, 'pass_selection', 0) - 1) % 2
                            pass_options = ["YES", "NO"]
                            self.add_log_entry(f"Pass turn: {pass_options[self.pass_selection]}", "system")
                    
                    elif event.key == pygame.K_DOWN:
                        if self.menu_selection_index == 0:  # ENEMY menu
                            self.enemy_parts_index = (self.enemy_parts_index + 1) % len(enemy.body_parts)
                            self.add_log_entry(f"Examining: {enemy.body_parts[self.enemy_parts_index].name}", "info")
                        elif self.menu_selection_index == 1:  # MOVES menu
                            if hasattr(player, 'moves') and player.moves:
                                self.moves_selection_index = (self.moves_selection_index + 1) % len(player.moves)
                                move = player.moves[self.moves_selection_index]
                                self.add_log_entry(f"Move: {move.name} (DMG: {move.danno}, STA: {move.stamina_cost})", "combat")
                        elif self.menu_selection_index == 3:  # ABILITIES menu
                            if hasattr(player, 'ability') and player.ability:
                                self.ability_selection_index = (getattr(self, 'ability_selection_index', 0) + 1) % len(player.ability)
                                ability = player.ability[self.ability_selection_index]
                                self.add_log_entry(f"Ability: {ability.name}", "info")
                        elif self.menu_selection_index == 5:  # PASS menu
                            self.pass_selection = (getattr(self, 'pass_selection', 0) + 1) % 2
                            pass_options = ["YES", "NO"]
                            self.add_log_entry(f"Pass turn: {pass_options[self.pass_selection]}", "system")
                    
                    elif event.key == pygame.K_SPACE:
                        if self.menu_selection_index == 1:  # Use move
                            self.use_selected_move()
                        elif self.menu_selection_index == 3:  # Show ability details
                            self.show_ability_details_pygame()
                        elif self.menu_selection_index == 5:  # PASS menu
                            if getattr(self, 'pass_selection', 0) == 0:  # YES selected
                                self.start_enemy_turn()
                    
                    elif event.key == pygame.K_r:  # Toggle regeneration
                        self.toggle_regeneration_mode()
                    
                    elif event.key == pygame.K_ESCAPE:
                        if hasattr(self, 'target_selection_active') and self.target_selection_active:
                            self.cancel_target_selection()
                        elif hasattr(self, 'regeneration_mode_active') and self.regeneration_mode_active:
                            self.toggle_regeneration_mode()
            
            # Handle custom events for enemy AI and animation delays
            elif event.type == pygame.USEREVENT + 1:
                self.end_enemy_turn()
            elif event.type == pygame.USEREVENT + 2:
                self.execute_enemy_move()
            elif event.type == pygame.USEREVENT + 3:  # Animation completion event
                self.finish_player_attack_sequence()

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
            print(f"DEBUG: Showing enemy panel - menu_index: {self.menu_selection_index}, enemy_turn: {getattr(self, 'enemy_turn_active', False)}, target_selection: {getattr(self, 'target_selection_active', False)}")
            
            # Calculate menu bar dimensions and position (scaled)
            menu_bar_width = self.sx(760)
            menu_bar_x = self.sx(310)
            menu_bar_y = self.sy(1000 - 265)  # SCREEN_HEIGHT - 265
            
            # Define enemy panel area aligned with menu bar (scaled)
            panel_x = menu_bar_x
            panel_y = self.sy(35)
            panel_width = menu_bar_width
            panel_height = menu_bar_y - panel_y - self.sy(20)

            # Display enemy name - AUTOMATICALLY CENTERED (scaled)
            enemy_name_text = f"{enemy.name}"

            # Calculate the positions of the body parts list and attributes box (scaled)
            parts_x = panel_x + panel_width + self.sx(20)  # Body parts list position
            attributes_panel_x = self.sx(1450)  # Enemy part attributes box position

            # Calculate the center point between the two panels (scaled)
            center_x = (parts_x + self.sx(350) + attributes_panel_x) // 2  # +350 for body parts list width

            # Draw the enemy name centered between the two panels (scaled)
            self.draw_text(enemy_name_text, self.font_medium, WHITE, center_x, panel_y + self.sy(25), center=True)
        
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
            
            # Show enemy turn indicator during enemy turn (scaled)
            if hasattr(self, 'enemy_turn_active') and self.enemy_turn_active:
                turn_indicator_y = panel_y + self.sy(10)
                self.draw_text(f">>> {enemy.name}'S TURN <<<", self.font_large, (255, 100, 100), 
                            panel_x + panel_width//2, turn_indicator_y, center=True)
            
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
                move_info_text = f"MOSSA: {move.name} | DMG: {move.danno} | STA: {move.stamina_cost} | ACC: {move.accuracy}%"
                self.draw_text(move_info_text, self.font_medium, WHITE, panel_x + self.sx(10), move_info_y)
                
                if effects_display:
                    effects_text = f"EFFETTI: {', '.join(effects_display)}"
                    self.draw_text(effects_text, self.font_medium, WHITE, panel_x + self.sx(10), move_info_y + self.sy(25))
                
            # Enemy body parts list positioned to the right of the main panel (scaled)
            parts_x = panel_x + panel_width + self.sx(20)
            parts_y = panel_y + self.sy(50)
            
            # Semi-transparent background for body parts list (scaled)
            parts_bg_height = len(enemy.body_parts) * self.sy(40) + self.sy(20)
            parts_bg_width = self.sx(200)
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
                    # TARGET SELECTION MODE - Red highlighting
                    if i == getattr(self, 'target_selection_index', 0):
                        # Selected target - bright red
                        part_name_color = (255, 100, 100)  # Light red text
                    else:
                        # Non-selected targets - dimmed
                        part_name_color = (150, 150, 150)  # Gray
                        
                elif is_normal_enemy_nav and i == self.enemy_parts_index:
                    # NORMAL ENEMY NAVIGATION MODE - Green highlighting
                    part_name_color = GREEN
                    
                else:
                    # Normal state
                    part_name_color = WHITE
                
                # Draw part name with appropriate color (scaled)
                self.draw_text(part.name, self.font_medium, part_name_color, parts_x, y)
                
                # HP bar next to part name (scaled)
                bar_x = parts_x + self.sx(180)
                bar_width = self.sx(150)
                bar_height = self.sy(15)
                
                # Background bar (scaled)
                pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, y, bar_width, bar_height))
                
                # Health fill - red tint during target selection (scaled)
                if part.max_p_pvt > 0:
                    fill_width = int(bar_width * part.p_pvt / part.max_p_pvt)
                    
                    if is_target_selection and i == getattr(self, 'target_selection_index', 0):
                        # Selected target - red-tinted HP bar
                        bar_color = (255, 50, 50)  # Red-tinted bar
                    else:
                        # Normal green HP bar
                        bar_color = GREEN
                    
                    pygame.draw.rect(self.screen, bar_color, (bar_x, y, fill_width, bar_height))
                
                # HP text (scaled)
                hp_text = f"{part.p_pvt}/{part.max_p_pvt}"
                hp_text_color = WHITE
                if is_target_selection and i == getattr(self, 'target_selection_index', 0):
                    hp_text_color = (255, 200, 200)  # Light red
                
                self.draw_text(hp_text, self.font_small, hp_text_color, bar_x + bar_width//2, y+self.sy(8), center=True)
        else:
            print(f"DEBUG: NOT showing enemy panel - conditions not met")

    def draw_turn_display(self):
        """Draw the turn display panel at the top of the body panel (SCALED)"""
        # Turn display dimensions and position (scaled)
        turn_x = self.sx(10)
        turn_y = self.sy(10)
        turn_width = self.sx(280)
        turn_height = self.sy(40)
        
        # Draw turn display background (scaled)
        pygame.draw.rect(self.screen, BLACK, (turn_x, turn_y, turn_width, turn_height))
        pygame.draw.rect(self.screen, WHITE, (turn_x, turn_y, turn_width, turn_height), 2)
        
        # Create turn display text
        turn_text = f"Turn: {Turn} | P: {turn_player} | E: {turn_enemy}"
        
        # Draw turn text centered in the display (scaled)
        self.draw_text(
            turn_text, 
            self.font_medium, 
            YELLOW, 
            turn_x + turn_width // 2, 
            turn_y + turn_height // 2, 
            center=True
        )
    
    def load_images(self):
        """Load character GIFs and background images"""
        # ...existing background loading code...
        
        # Load status effect GIFs - GENERALIZED SYSTEM
        try:
            status_gifs_folder = Path(__file__).parent / "SymbolGIF"
            print(f"Loading status effect GIFs from: {status_gifs_folder}")
            
            # Initialize status frames dictionary
            self.status_frames = {}
            
            # Define all possible status effects and their corresponding file names
            status_effects = {
                'stun': 'stun.mp4',
                'burn': 'fire.gif',
                'bleed': 'blood.gif', 
                'poison': 'poison.gif',
                'inhibition': 'inhibition.gif',
                'confusion': 'confusion.gif',
                'freeze': 'ice.gif',
                'regen': 'heal.gif',
                'cancer': 'cancer.gif',
                'sleep': 'sleep.gif'
                # Add more status effects as needed
            }
            
            if status_gifs_folder.exists():
                for status_name, filename in status_effects.items():
                    gif_path = status_gifs_folder / filename
                    
                    if gif_path.exists():
                        try:
                            # Load frames for this status effect (40x30 size for consistency)
                            frames = self.load_gif_frames(str(gif_path), (40, 30), crop_face=False)
                            self.status_frames[status_name] = frames
                            print(f"Loaded {len(frames)} frames for {status_name} status")
                        except Exception as e:
                            print(f"Error loading {status_name} GIF: {e}")
                            # Create fallback surface with unique color for each status
                            fallback_surface = self.create_status_fallback(status_name)
                            self.status_frames[status_name] = [fallback_surface]
                    else:
                        print(f"Status GIF not found: {gif_path}")
                        # Create fallback surface
                        fallback_surface = self.create_status_fallback(status_name)
                        self.status_frames[status_name] = [fallback_surface]
            else:
                print(f"SymbolGIF folder not found: {status_gifs_folder}")
                # Create fallback surfaces for all status effects
                for status_name in status_effects.keys():
                    fallback_surface = self.create_status_fallback(status_name)
                    self.status_frames[status_name] = [fallback_surface]
                    
        except Exception as e:
            print(f"Error loading status effect GIFs: {e}")
            # Create fallback surfaces for all status effects
            self.status_frames = {}
            for status_name in ['electricity', 'burn', 'bleed', 'poison', 'stun', 'confusion']:
                fallback_surface = self.create_status_fallback(status_name)
                self.status_frames[status_name] = [fallback_surface]
        
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
        
        # Load player GIF frames
        try:
            self.player_frames = self.load_gif_frames(str(player.image_path), (295, 295), crop_face=False)
            print(f"Loaded {len(self.player_frames)} player GIF frames")
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

    def create_status_fallback(self, status_name):
        """Create a fallback surface for status effects with unique colors"""
        surface = pygame.Surface((40, 30))
        
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
            'inhibition': (128, 128, 0)      # Olive
        }
        
        color = status_colors.get(status_name, (128, 128, 128))  # Default gray
        surface.fill(color)
        return surface

    def get_current_status_frame(self, status_name):
        """Get the current animation frame for a specific status effect"""
        if hasattr(self, 'status_frames') and status_name in self.status_frames:
            frames = self.status_frames[status_name]
            if frames and 0 <= self.player_frame_index < len(frames):
                return frames[self.player_frame_index]
        
        # Fallback
        return self.create_status_fallback(status_name)

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
        
        # Check all possible status effects
        status_effects = ['burn', 'bleed', 'poison', 'stun', 'confusion', 'cancer', 'inhibition', 'freeze', 'regen', 'sleep']
        
        for status_name in status_effects:
            if hasattr(effetti, status_name):
                effect_data = getattr(effetti, status_name)
                # Check if effect is active (level > 0 and duration > 0)
                if effect_data[1] > 0 and effect_data[2] > 0:
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
        
        indicator_width = 40
        indicator_height = 30
        indicator_spacing = 5
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
                indicator_x = status_x + col * (indicator_width + indicator_spacing)
                indicator_y = status_y + row * row_height
                
                # Get current frame for this status
                current_frame = self.get_current_status_frame(status_name)
                
                # Draw the status GIF (full color when active)
                self.screen.blit(current_frame, (indicator_x, indicator_y))
                
                # Draw status level indicator if level > 1
                if status['level'] > 1:
                    level_text = str(status['level'])
                    level_surface = self.font_small.render(level_text, True, WHITE)
                    level_surface.set_alpha(200)  # Semi-transparent
                    # Position level indicator in top-right corner of the GIF
                    level_x = indicator_x + indicator_width - 12
                    level_y = indicator_y + 2
                    self.screen.blit(level_surface, (level_x, level_y))
                
                # Draw small label under the status GIF
                label_y = indicator_y + indicator_height + 2
                label_text = status_name[:4].upper()  # First 4 characters
                label_color = WHITE
                
                # Color-code labels based on status type
                if status_name in ['burn', 'bleed', 'poison', 'cancer']:
                    label_color = (255, 100, 100)  # Light red for damage effects
                elif status_name == 'regen':
                    label_color = (255, 255, 100)  # Yellow for regen
                elif status_name in ['inhibition', 'freeze', 'stun', 'confusion' , 'sleep']:
                    label_color = (100, 255, 255)  # Cyan for control effects
                
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
            
            # HP text
            hp_text = f"{part.p_pvt}-{part.max_p_pvt}"
            self.draw_text(hp_text, self.font_small, WHITE, panel_x + 140, bar_y + 10, center=True)
            
            # Status indicators: Multiple status effects below HP bar
            status_y = bar_y + 25  # Position below HP bar
            status_x = panel_x + 20  # Left-aligned with some margin
            
            # Draw all active status indicators for this body part
            final_y = self.draw_status_indicators(part, status_x, status_y, max_indicators_per_row=3)
            
            # If no active statuses, optionally show preview (commented out by default)
            # if final_y == status_y:
               # final_y = self.draw_inactive_status_preview(part, status_x, status_y)
            
            y_offset += part_height  # Use increased part height
        
        # Draw animated player image at the bottom of the panel
        img_x = panel_x + (panel_width - img_width) // 2  # Center horizontally
        img_y = panel_y + panel_height - img_height - 10  # Position at bottom with 10px margin
        
        # Draw a background for the image
        pygame.draw.rect(self.screen, DARK_GRAY, (img_x - 5, img_y - 5, img_width + 10, img_height + 10))
        pygame.draw.rect(self.screen, WHITE, (img_x - 5, img_y - 5, img_width + 10, img_height + 10), 1)
        
        # Draw the current animated player frame
        self.screen.blit(scaled_player_frame, (img_x, img_y))

        # Draw player blink overlay if active
        if hasattr(self, 'player_blink_state') and self.player_blink_state['active'] and self.player_blink_state['visible']:
            self.draw_blink_overlay(self.screen, img_x, img_y, img_width, img_height, 
                                self.player_blink_state['color'], alpha=128)

        # Draw player name and turn info above the image
        name_y = img_y - 25
        turn_y = name_y - 25
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

    def update(self):
        """Update game state"""
        # Update animation frames
        self.update_animation_frames()
        
        # Update blink states
        self.update_blink_states()
        
        # Update character stats
        update_all_characters_stats()

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
        stat_y = player_section_y + self.sy(30)

        forz_buff = get_character_buff_level(player, 'forz')
        des_buff = get_character_buff_level(player, 'des')
        spe_buff = get_character_buff_level(player, 'spe')
        vel_buff = get_character_buff_level(player, 'vel')
        
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
        
        # RES health bar
        res_bar_x = col1_x + bar_offset_x + 80
        res_bar_y = stat_y + 50 + 2
        pygame.draw.rect(self.screen, DARK_GRAY, (res_bar_x, res_bar_y, bar_width, bar_height))
        if player.max_res > 0:
            res_fill_width = int(bar_width * player.res / player.max_res)
            pygame.draw.rect(self.screen, (255, 200, 0), (res_bar_x, res_bar_y, res_fill_width, bar_height))  # Light blue color

        # STA (Stamina)
        sta_text = f"STA: {int(player.sta)}/{int(player.max_sta)}"
        self.draw_text(sta_text, self.font_small, WHITE, col1_x, stat_y + 75)
        
        # STA health bar
        sta_bar_x = col1_x + bar_offset_x + 80
        sta_bar_y = stat_y + 75 + 2
        pygame.draw.rect(self.screen, DARK_GRAY, (sta_bar_x, sta_bar_y, bar_width, bar_height))
        if player.max_sta > 0:
            sta_fill_width = int(bar_width * player.sta / player.max_sta)
            pygame.draw.rect(self.screen, GREEN, (sta_bar_x, sta_bar_y, sta_fill_width, bar_height))  # Yellow color

        # Column 2: STR, DEX, SPE, VEL (no bars needed for these stats)
        self.draw_text(f"STR: {int(player.forz)}", self.font_small, WHITE, col2_x, stat_y)
        self.draw_text(f"DEX: {int(player.des)}", self.font_small, WHITE, col2_x, stat_y + 25)
        self.draw_text(f"SPE: {int(player.spe)}", self.font_small, WHITE, col2_x, stat_y + 50)
        self.draw_text(f"VEL: {int(player.vel)}", self.font_small, WHITE, col2_x, stat_y + 75)

        # Color buffs/debuffs (green for positive, red for negative, gray for zero)
        def get_buff_color(buff_level):
            if buff_level > 0:
                return GREEN
            elif buff_level < 0:
                return RED
            else:
                return GRAY

        # Display buff levels with appropriate colors
        self.draw_text(f"{forz_buff:+d}" if forz_buff != 0 else "0", self.font_small, get_buff_color(forz_buff), col3_x, stat_y)
        self.draw_text(f"{des_buff:+d}" if des_buff != 0 else "0", self.font_small, get_buff_color(des_buff), col3_x, stat_y + 25)
        self.draw_text(f"{spe_buff:+d}" if spe_buff != 0 else "0", self.font_small, get_buff_color(spe_buff), col3_x, stat_y + 50)
        self.draw_text(f"{vel_buff:+d}" if vel_buff != 0 else "0", self.font_small, get_buff_color(vel_buff), col3_x, stat_y + 75)
    
        final_forz = player.max_for + (forz_buff * STAT_SCALING_FACTORS['forz'])
        final_des = player.max_des + (des_buff * STAT_SCALING_FACTORS['des'])
        final_spe = player.max_spe + (spe_buff * STAT_SCALING_FACTORS['spe'])
        final_vel = player.max_vel + (vel_buff * STAT_SCALING_FACTORS['vel'])

        self.draw_text(f"{int(final_forz)}", self.font_small, YELLOW, col4_x, stat_y)
        self.draw_text(f"{int(final_des)}", self.font_small, YELLOW, col4_x, stat_y + 25)
        self.draw_text(f"{int(final_spe)}", self.font_small, YELLOW, col4_x, stat_y + 50)
        self.draw_text(f"{int(final_vel)}", self.font_small, YELLOW, col4_x, stat_y + 75)

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
        """Draw moves panel when MOVES is selected (SCALED)"""
        if self.menu_selection_index == 1:
            moves_x = self.sx(400)
            moves_y = self.sy(140)
            
            self.draw_text(f"{player.name}'s Moves", self.font_large, WHITE, moves_x, moves_y)
            
            if hasattr(player, 'moves') and player.moves:
                for i, move in enumerate(player.moves):
                    y = moves_y + self.sy(40) + i * self.sy(80)
                    color = RED if i == self.moves_selection_index else WHITE
                    
                    # Move name and basic info (scaled)
                    move_text = f"{move.name} ({move.tipo}) - DMG: {move.danno}, STA: {move.stamina_cost}, ACC: {move.accuracy}%"
                    self.draw_text(move_text, self.font_medium, color, moves_x, y)
                    
                    # Scaling info (scaled)
                    scaling_text = f"Scaling - STR: {move.sca_for}, DEX: {move.sca_des}, SPE: {move.sca_spe}"
                    self.draw_text(scaling_text, self.font_small, color, moves_x, y + 20)
                    
                    # Effects and elements
                    if move.eff_appl or move.elem:
                        effects_text = f"Effects: {move.eff_appl} | Elements: {move.elem}"
                        self.draw_text(effects_text, self.font_small, color, moves_x, y + 40)
            else:
                self.draw_text("No moves available", self.font_medium, GRAY, moves_x, moves_y + 60)

    def start_enemy_turn(self):
        """Start enemy turn (updated with log integration)"""
        self.add_log_entry("=== PLAYER TURN ENDED ===", "turn")
        
        # End player turn and update counters
        end_player_turn()
        
        # Set enemy turn state
        self.enemy_turn_active = True
        self.player_has_control = False
        self.menu_selection_index = 0
        
        # Restore player stamina
        old_player_stamina = player.sta
        player.sta = player.max_sta
        stamina_restored = player.sta - old_player_stamina
        
        if stamina_restored > 0:
            self.add_log_entry(f"{player.name} stamina restored: +{stamina_restored}", "success")
        
        # Refill enemy RIG
        rig_restored, res_consumed, refill_message = refill_enemy_rig_with_res()
        if rig_restored > 0:
            self.add_log_entry(f"{enemy.name}: {refill_message}", "info")
        
        # Enemy regeneration
        total_regenerations, regeneration_messages = enemy_auto_regenerate_multiple()
        for msg in regeneration_messages:
            self.add_log_entry(msg, "success")
        
        self.add_log_entry(f"=== {enemy.name.upper()}'S TURN STARTED ===", "turn")
        
        # Start enemy moves
        pygame.time.set_timer(pygame.USEREVENT + 2, 1500)

    def execute_enemy_move(self):
        """Execute a random enemy move on a random player body part (pygame version - FIXED)"""
        import random
        
        print("DEBUG: execute_enemy_move called")
        
        if not self.enemy_turn_active:
            print("DEBUG: Enemy turn not active, exiting")
            return
        
        # Check if enemy has any moves they can afford
        affordable_moves = []
        for i, move in enumerate(enemy.moves):
            if move.stamina_cost <= enemy.sta:
                affordable_moves.append((i, move))
        
        print(f"DEBUG: Enemy stamina: {enemy.sta}")
        print(f"DEBUG: Enemy has {len(affordable_moves)} affordable moves")
        for i, (idx, move) in enumerate(affordable_moves):
            print(f"  Move {i+1}: {move.name} (cost: {move.stamina_cost})")
        
        if not affordable_moves:
            # Enemy is out of stamina, end turn
            print("DEBUG: Enemy out of stamina, ending turn")
            pygame.time.set_timer(pygame.USEREVENT + 1, 1000)  # End turn after 1 second
            return
        
        # Select a random affordable move
        move_index, selected_move = random.choice(affordable_moves)
        print(f"DEBUG: Enemy selected move: {selected_move.name}")
        
        # Select a random player body part to target
        target_part_index = random.randint(0, len(player.body_parts) - 1)
        target_part = player.body_parts[target_part_index]
        
        print(f"DEBUG: Enemy targeting player's {target_part.name}")
        
        # Execute the move
        self.perform_enemy_move(selected_move, target_part, target_part_index)
        
        # Check if enemy has more stamina for another move after this one executes
        remaining_stamina = enemy.sta - selected_move.stamina_cost
        print(f"DEBUG: Enemy will have {remaining_stamina} stamina after this move")
        
        remaining_affordable_moves = []
        for i, move in enumerate(enemy.moves):
            if move.stamina_cost <= remaining_stamina:
                remaining_affordable_moves.append((i, move))
        
        print(f"DEBUG: Enemy will have {len(remaining_affordable_moves)} moves available after this one")
        
        if remaining_affordable_moves:
            # Schedule next move after a delay
            print("DEBUG: Scheduling next enemy move in 2 seconds")
            pygame.time.set_timer(pygame.USEREVENT + 2, 2000)  # 2 second delay
        else:
            # Enemy will be out of stamina after this move, end turn
            print("DEBUG: Enemy will be out of stamina, scheduling turn end in 3 seconds")
            pygame.time.set_timer(pygame.USEREVENT + 1, 3000)  # End turn after 3 seconds

    def perform_enemy_move(self, move, target_part, target_part_index):
        """Perform an enemy move on a player body part (pygame version - FIXED)"""
        import random
        
        print(f"DEBUG: Performing enemy move {move.name} on {target_part.name}")
        
        # Subtract stamina cost from enemy
        old_enemy_stamina = enemy.sta
        enemy.sta -= move.stamina_cost
        print(f"DEBUG: Enemy stamina: {old_enemy_stamina} -> {enemy.sta} (-{move.stamina_cost})")
        
        # Calculate accuracy roll
        accuracy_roll = random.randint(1, 100)
        print(f"DEBUG: Accuracy roll: {accuracy_roll} vs move accuracy: {move.accuracy}")
        
        if accuracy_roll > move.accuracy:
            # Move missed - play miss sound and show message
            miss_message = f"{enemy.name} ha mancato {move.name} su {target_part.name}!"
            self.show_warning_message(miss_message, 1500)
            print(f"DEBUG: Enemy attack missed! {miss_message}")
            
            # Play miss sound effect
            play_sound_effect("mixkit-punch-through-air-2141.mp3", volume=0.4)
            
            # Make enemy blink to show miss
            self.blink_character_gif("enemy", (100, 100, 255), 200, 2)  # Blue blink for miss
            
            return
        
        # Move hit - apply damage
        damage = move.danno
        old_hp = target_part.p_pvt
        target_part.p_pvt = max(0, target_part.p_pvt - damage)
        actual_damage = old_hp - target_part.p_pvt
        
        print(f"DEBUG: Damage applied to {player.name}'s {target_part.name}: {old_hp} -> {target_part.p_pvt} (-{actual_damage})")
        
        # Recalculate player health
        player.calculate_health_from_body_parts()
        
        # Apply status effects from the move to the targeted body part
        apply_move_effects(move, player, target_part_index)
        
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
            elif "ROAR" in move.elem:
                play_sound_effect("tiger-roar-loudly-193229", volume=0.4)
            else:
                play_sound_effect("mixkit-impact-of-a-strong-punch-2155", volume=0.4)
        else:
            # Default hit sound
            play_sound_effect("mixkit-impact-of-a-strong-punch-2155", volume=0.4)
        
        print(f"DEBUG: Enemy move completed - {move.name} hit {target_part.name} for {actual_damage} damage")

    def draw(self):
        """Draw everything (UPDATED to use event log instead of temporary messages)"""
        self.screen.fill(BLACK)
            
        # Draw UI components
        self.draw_turn_display()
        self.draw_body_panel()
        self.draw_stats_panel()
        self.draw_menu_bar()
        
        # Always draw the enemy panel
        self.show_enemy_panel()
        
        # Draw other panels based on conditions
        if not (hasattr(self, 'target_selection_active') and self.target_selection_active):
            if self.player_has_control:
                self.draw_moves_panel()
                self.draw_effects_panel()
                self.draw_abilities_panel()
                self.draw_items_panel()
                self.draw_pass_panel()
        
        # Draw enemy part attributes when appropriate
        if self.menu_selection_index == 0 and self.player_has_control:
            self.draw_enemy_part_attributes()
        
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
        
        if character.sta < 1:
            self.add_log_entry("Cannot regenerate - insufficient stamina!", "error")
            return False
        
        if hasattr(character, 'res') and character.res < 5:
            self.add_log_entry("WARNING: Low RES - cannot restore RIG next turn!", "warning")
        
        # Apply regeneration
        old_pvt = part.p_pvt
        part.p_pvt = min(part.p_pvt + 5, part.max_p_pvt)
        actual_healing = part.p_pvt - old_pvt
        
        character.rig -= 5
        character.sta -= 1
        character.calculate_health_from_body_parts()
        
        # Log success
        self.add_log_entry(f"Regenerated {part.name}: +{actual_healing} HP (RIG: -{5}, STA: -{1})", "success")
        
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
            self.add_log_entry("Regeneration mode ACTIVATED (↑↓ select, SPACE regenerate, R exit)", "regeneration")
            self.in_regeneration_navigation = True
        else:
            self.add_log_entry("Regeneration mode DEACTIVATED", "regeneration")
            self.in_regeneration_navigation = False

    def end_enemy_turn(self):
        """End enemy turn (updated with log integration)"""
        self.add_log_entry("=== ENEMY TURN ENDED ===", "turn")
        
        # Clear timers
        pygame.time.set_timer(pygame.USEREVENT + 1, 0)
        pygame.time.set_timer(pygame.USEREVENT + 2, 0)
        
        # Call global function
        end_enemy_turn()
        
        # Update UI state
        self.enemy_turn_active = False
        self.player_has_control = True
        
        # Restore enemy stamina
        old_enemy_stamina = enemy.sta
        enemy.sta = enemy.max_sta
        stamina_restored = enemy.sta - old_enemy_stamina
        
        if stamina_restored > 0:
            self.add_log_entry(f"{enemy.name} stamina restored: +{stamina_restored}", "success")
        
        # Refill player RIG
        rig_restored, res_consumed, refill_message = refill_player_rig_with_res()
        if rig_restored > 0:
            self.add_log_entry(f"{player.name}: {refill_message}", "info")
        
        self.add_log_entry(f"=== {player.name.upper()}'S TURN STARTED ===", "turn")

    def draw_effects_panel(self):
        """Draw effects panel when EFFECTS is selected"""
        if self.menu_selection_index == 2:
            effects_x = 400
            effects_y = 100
            
            self.draw_text("Effects Panel", self.font_large, WHITE, effects_x, effects_y)
            self.draw_text("Effects system in development", self.font_medium, GRAY, effects_x, effects_y + 50)

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
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# Initialize game data
initialize_game_data()

# Initialize and play background music at startup
if initialize_music():
    music_started = play_background_music(BACKGROUND_MUSIC_PATH, volume=0.3, loops=-1)
    if not music_started:
        print("Failed to start background music")
    
    # Preload sound effects for better performance
    preload_sound_effects()
else:
    print("Game will continue without background music")

# Create and run the pygame UI
if __name__ == "__main__":
    ui = PygameUI()
    ui.run()
#------------------------------------------------------------------------------------------------------------------

print("GUI main loop ended.")