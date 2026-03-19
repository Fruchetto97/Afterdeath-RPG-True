#FUNZIONI
import tkinter as tk
import random
import time
import traceback
from PIL import Image, ImageTk
from pathlib import Path

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
    'req_stm_sca_factor': 1   # Requirement stamina scaling factor (each requirement multiplied by this)
}

def update_character_stats(character):
    """
    Update current stats based on max stats and buffs/debuffs with scaling factors.
    Formula: current_stat = max_stat + (buf_stat * scaling_factor)
    Note: For stamina, we calculate the maximum possible stamina but don't override current stamina
    if it has been reduced (e.g., from move usage).
    """
    # Map of stat names to their max and buf attributes
    stat_mappings = {
        'rig': ('max_rig', 'rig', 'buf_rig'),
        'res': ('max_res', 'res', 'buf_res'),  # Note: buf_reg in Character class
        'sta': ('max_sta', 'sta', 'buf_sta'),
        'forz': ('max_for', 'forz', 'buf_forz'),
        'des': ('max_des', 'des', 'buf_des'),
        'spe': ('max_spe', 'spe', 'buf_spe'),
        'vel': ('max_vel', 'vel', 'buf_vel')
    }
    
    for stat_name, (max_attr, current_attr, buf_attr) in stat_mappings.items():
        if hasattr(character, max_attr) and hasattr(character, buf_attr) and hasattr(character, current_attr):
            max_value = getattr(character, max_attr)
            buf_value = getattr(character, buf_attr)
            scaling_factor = STAT_SCALING_FACTORS.get(stat_name, 1.0)
            
            # Calculate new maximum possible value: max + (buff * scaling_factor)
            new_max_possible = max_value + (buf_value * scaling_factor)
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
            else:
                # For other stats, update normally
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

def calculate_move_damage(character, strength_scaling, dexterity_scaling, special_scaling):
    current_strength = getattr(character, 'forz', 0)
    current_dexterity = getattr(character, 'des', 0)
    current_special = getattr(character, 'spe', 0)
    
    damage = (strength_scaling * current_strength + 
              dexterity_scaling * current_dexterity + 
              special_scaling * current_special)
    
    return max(0, round(damage))  # Ensure damage is not negative and is an integer

def calculate_move_stamina_cost(strength_scaling, dexterity_scaling, special_scaling, effects=None, requirements=None):
    # Base cost
    base_cost = 2
    
    # Sum of all scaling values
    scaling_sum = strength_scaling + dexterity_scaling + special_scaling
    
    # Effect cost
    num_effects = len(effects) if effects else 0
    effect_cost = num_effects * MOVE_STAMINA_SCALING_FACTORS['eff_stm_sca_factor']
    
    # Requirement reduction
    num_requirements = len(requirements) if requirements else 0
    requirement_reduction = num_requirements * MOVE_STAMINA_SCALING_FACTORS['req_stm_sca_factor']
    
    total_cost = base_cost + scaling_sum + effect_cost - requirement_reduction
    
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
        
        # Recalculate damage and stamina cost
        move.danno = calculate_move_damage(character, move.sca_for, move.sca_des, move.sca_spe)
        move.stamina_cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, move.eff_appl, move.reqs)
        
        if old_damage != move.danno or old_stamina != move.stamina_cost:
            print(f"  {move.name}: Damage {old_damage} -> {move.danno}, Stamina {old_stamina} -> {move.stamina_cost}")

def recalculate_all_character_moves():
    """
    Recalculate moves for all characters in the game.
    This function should be called when stat scaling factors change.
    """
    recalculate_character_moves(player)
    recalculate_character_moves(enemy)

def display_scaling_factors():
    """
    Display all current scaling factors for easy reference and modification.
    """
    print("\n" + "="*50)
    print("CURRENT SCALING FACTORS")
    print("="*50)
    
    print("\nStat Scaling Factors (for character stats):")
    for stat, factor in STAT_SCALING_FACTORS.items():
        print(f"  {stat}: {factor}")
    
    print("\nMove Stamina Scaling Factors:")
    for factor_name, factor_value in MOVE_STAMINA_SCALING_FACTORS.items():
        print(f"  {factor_name}: {factor_value}")
    
    print("\nDamage Formula: STR_scaling * Current_STR + DEX_scaling * Current_DEX + SPE_scaling * Current_SPE")
    print("Stamina Formula: 2 + (sum of scaling values) + (effects * eff_stm_sca_factor) - (requirements * req_stm_sca_factor)")
    print("="*50)
#---------------------------------------------------------------

#CLASSI E INIZIALIZZAZIONE

# CLASSI

class Character:
    def __init__(self, name, max_pvt, pvt, max_rig, rig, buf_rig, max_res, res, buf_res, max_sta, sta, buf_sta,
                  max_for, forz, buf_forz, max_des, des, buf_des, max_spe, spe, buf_spe, max_vel, vel, buf_vel,
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
        self.buf_rig = buf_rig  # Buffs
        self.buf_res = buf_res  
        self.buf_sta = buf_sta
        self.buf_forz = buf_forz    
        self.buf_des = buf_des
        self.buf_spe = buf_spe
        self.buf_vel = buf_vel  
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
    def __init__(self, burn=None, bleeding=None, poison=None, stun=None, confusion=None):
        # per ogni effetto di stato il primo elemento della lista è il nome dell'effetto, il secondo è il livello, il terzo la durata e il quarto l'immunità (0 non immune o 1 immune)
        #di base li setta tutti a zero, se vuoi settarne uno devi farlo separatamente.
        self.burn = burn if burn is not None else ["burn", 0, 0, 0]
        self.bleeding = bleeding if bleeding is not None else ["bleeding", 0, 0, 0]
        self.poison = poison if poison is not None else ["poison", 0, 0, 0]
        self.stun = stun if stun is not None else ["stun", 0, 0, 0]
        self.confusion = confusion if confusion is not None else ["confusion", 0, 0, 0]

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
        self.stamina_cost = calculate_move_stamina_cost(sca_for, sca_des, sca_spe, eff_appl, reqs)

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

enemy_image_path = Path(__file__).parent / "Enemies_GIFs" / "Selkio_NPC_2_gif.gif"

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
    BodyPart("Testa", 20, 20, Effetti(), Difese(), 1),
    BodyPart("Br. Dx", 10, 10, Effetti(), Difese(), 1),
    BodyPart("Br. Sx", 10, 10, Effetti(), Difese(), 1),
    BodyPart("Corpo", 30, 30, Effetti(), Difese(), 2),
    BodyPart("Ga. Dx", 15, 15, Effetti(),Difese(), 1),
    BodyPart("Ga. Sx", 15, 15, Effetti(),Difese(), 1),
]

player = Character(
    "Jonny Buono",
    100, 80, 20, 20,0, 50, 40,0, 12, 12,0, 15, 15,0, 14, 14, 0,13, 13, 0,11, 11,0,
    player_body_parts,
    str(player_image_path)  # Convert Path to string for compatibility
)

enemy_body_parts = [
    BodyPart("Testa", 1000, 1000, Effetti(), Difese(), 2),
    BodyPart("Occhio", 300, 250, Effetti(), Difese(), 1),
    BodyPart("Artiglio Dx", 25, 25, Effetti(), Difese(), 1),
    BodyPart("Artiglio Sx", 25, 25, Effetti(), Difese(), 1),
    BodyPart("Tentacoli (1)", 12, 12, Effetti(), Difese(), 1),
    BodyPart("Tentacoli (2)", 12, 8, Effetti(), Difese(), 1),
    BodyPart("Tentacoli (3)", 12, 12, Effetti(), Difese(), 1),
    BodyPart("Tentacoli (4)", 12, 12, Effetti(), Difese(), 1),
    BodyPart("Tentacoli (5)", 12, 5, Effetti(), Difese(), 1),
]

enemy = Character(
    "BLUBBERTONE",
    100, 80, 20, 20,0, 50, 40,0, 12, 12,0, 15, 15, 0,14, 14,0, 13, 13,0, 11, 11,0,
    enemy_body_parts,
    str(enemy_image_path)  # Convert Path to string for compatibility
)

#-------------------------------------------------------------------------------------------------------------------

# Essential utility functions that are used early in the code
def apply_status_effect(character, part_index, effect_name, level=1, duration=1, immunity=0):
    """
    Apply a status effect to a specific body part of a character.
    Overwrites the effect list to avoid reference issues.
    """
    if not (0 <= part_index < len(character.body_parts)):
        print(f"Invalid body part index {part_index} for character {getattr(character, 'name', 'Unknown')}")
        return
    part = character.body_parts[part_index]
    effetti = part.p_eff
    if not hasattr(effetti, effect_name):
        print(f"Effect '{effect_name}' not found on {part.name}")
        return
    # This always overwrites the previous effect for this body part and effect name
    setattr(effetti, effect_name, [effect_name, level, duration, immunity])
    print(f"Applied {effect_name} to {getattr(character, 'name', 'Unknown')} - {part.name}: {[effect_name, level, duration, immunity]}")

def apply_buff_debuff(character, stat_name, amount):
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
    
    if not hasattr(character, buf_attr):
        print(f"Character {getattr(character, 'name', 'Unknown')} does not have attribute '{buf_attr}'")
        return
    
    # Apply the buff/debuff
    current_value = getattr(character, buf_attr)
    new_value = current_value + amount
    setattr(character, buf_attr, new_value)
    
    # Update the character's current stats based on the new buff values
    update_character_stats(character)
    
    buff_type = "buff" if amount > 0 else "debuff"
    print(f"Applied {buff_type} to {getattr(character, 'name', 'Unknown')} - {stat_name}: {current_value} -> {new_value} ({amount:+d})")

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
            print(f"   Effects: {', '.join(move.eff_appl)}")
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

    # Reset and apply status effects after characters are created
    apply_status_effect(enemy, 3, 'burn', level=3, duration=4, immunity=0)

    apply_buff_debuff(player, 'forz', 5)  # Example buff to player's forz stat (will be scaled by 2.0)
    apply_buff_debuff(player, 'vel', 3)   # Example buff to player's vel stat (will be scaled by 1.0)

    # Apply initial stat updates after characters are created
    update_all_characters_stats()

    # Example of adding moves to characters
    # Add some example moves to the player
    add_move_to_character(player, "Fendente", "ATK", 1.2, 0.8, 0.0, 
                         effects=["SNG"], requirements=["SPADA"], 
                         elements=["CUT"], accuracy=85)

    add_move_to_character(player, "Grido di  Battaglia", "BUF", 0.0, 0.0, 1.0, 
                         effects=["FOR+1"], requirements=["TESTA"], 
                         elements=[], accuracy=100)

    add_move_to_character(player, "Schivata", "REA", 0.0, 1.5, 0.0, 
                         effects=["DOG"], requirements=["2 GAMBE"], 
                         elements=[], accuracy=95)
    
    add_ability_to_character(player, "Chanche!", 1, "se CONFUSE/STUN, +1 FORZ", 
                         "I suoi attacchi fanno danni extra contro gli obbiettivi con lo status CONFUSE o STUN, come se il tuo personaggio avesse +1 STR")

    add_ability_to_character(player, "Dentistretti", 1, "se BURN/POISON, +1 FORZ",  
                         "I suoi attacchi fanno danni extra contro gli obbiettivi con lo status BURN o POISON, come se il tuo personaggio avesse +1 FORZ")
    # Add some example moves to the enemy
    add_move_to_character(enemy, "Tentacle Slam", "ATK", 1.0, 0.5, 0.0, 
                         effects=["stun"], requirements=[], 
                         elements=["physical"], accuracy=75)

    add_move_to_character(enemy, "Toxic Spray", "ATK", 0.3, 0.0, 1.2, 
                         effects=["poison"], requirements=[], 
                         elements=["poison"], accuracy=90)

    # Add 3 additional moves to the enemy for testing
    add_move_to_character(enemy, "Crushing Bite", "ATK", 1.5, 0.2, 0.0, 
                         effects=["bleeding"], requirements=[], 
                         elements=["physical"], accuracy=80)

    add_move_to_character(enemy, "Acid Spit", "ATK", 0.5, 0.8, 1.0, 
                         effects=["burn"], requirements=[], 
                         elements=["acid"], accuracy=75)

    add_move_to_character(enemy, "Intimidating Roar", "BUF", 0.0, 0.0, 0.5, 
                         effects=["fear"], requirements=[], 
                         elements=[], accuracy=95)

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

#COSE FISSE NEL MENU' (CHE SONO SMEPRE A SCHERMO)

root = tk.Tk()
root.title("RPG Fighting System")
root.configure(bg="black")

image_size = 295  # You can adjust this value for your layout

# Constants for fixed positions
LEFT_PANEL_WIDTH = image_size  # 295
MENU_TOP_Y = 540               # Y position for the menu separator line
MENU_WIDTH = 1200              # Adjust to your menu's actual width
MENU_HEIGHT = 2
MENU_SECTION_HEIGHT = 60

# Configure grid for layout
for i in range(12):
    if i == 6:
        root.grid_rowconfigure(i, weight=0, minsize=1)  # Name frame row
    elif 7 <= i <= 11:
        root.grid_rowconfigure(i, weight=0, minsize=1)   # Stat bar rows: minimal height
    else:
        root.grid_rowconfigure(i, weight=1)
for i in range(1, 7):  # Only columns 1-6 stretch
    root.grid_columnconfigure(i, weight=1)
root.grid_columnconfigure(0, weight=0, minsize=1)

# Left panel (body parts)
body_panel_width = 280  # Adjust as needed
body_panel_height = 1000  # Adjust as needed
body_panel = tk.Frame(root, bg="black", width=body_panel_width, height=body_panel_height)
body_panel.place(x=0, y=0)

body_part_bar_width = body_panel_width
body_part_bar_height = 20
body_part_spacing = 60  # Space between each part (name + bar)

# Global list to store body part HP canvases for updates
body_part_hp_canvases = []

for idx, part in enumerate(player.body_parts):
    # Centered name label
    name_label = tk.Label(
        body_panel,
        text=part.name,
        fg="white",
        bg="black",
        font=("Times", 16),
        anchor="center",
        width=14
    )
    name_label.place(x=(body_panel_width - body_part_bar_width)//2, y=10 + idx*body_part_spacing, width=body_part_bar_width)

    # HP bar below name
    bar_y = 10 + idx*body_part_spacing + 28
    hp_canvas = tk.Canvas(body_panel, width=body_part_bar_width, height=body_part_bar_height, bg="black", highlightthickness=0)
    hp_canvas.place(x=(body_panel_width - body_part_bar_width)//2, y=bar_y)
    hp_canvas.create_rectangle(15, 0, body_part_bar_width, body_part_bar_height, fill="#222", outline="")
    fill_width = int(body_part_bar_width * part.p_pvt / part.max_p_pvt) if part.max_p_pvt > 0 else 0
    hp_canvas.create_rectangle(15, 0, fill_width, body_part_bar_height, fill="green", outline="")
    hp_canvas.create_text(body_part_bar_width // 2, body_part_bar_height // 2, text=f"{part.p_pvt}/{part.max_p_pvt}", fill="white", font=("Times", 10))
    
    # Store canvas reference for updates
    body_part_hp_canvases.append(hp_canvas)

# Character name (middle-left rectangle, under body parts)
name_frame = tk.Frame(
    root,
    bg="black",
    highlightbackground="white",
    highlightthickness=1,
    height=50
)
name_frame.grid(row=9, column=0, padx=0, pady=0)
tk.Label(name_frame, width=22, text=player.name, fg="white", bg="black", font=("Times", 18)).pack(expand=True, fill="both")
name_frame.grid_propagate(False)  # Prevent frame from resizing to content

# Character image (bottom-left square)

image_frame = tk.Frame(
    root,
    bg="black",
    highlightbackground="white",
    highlightthickness=1,
    width=image_size,
    height=image_size
)
image_frame.grid(row=10, column=0, rowspan=5, padx=0, pady=0)
image_frame.grid_propagate(False)  # Prevent frame from resizing to content

try:
    img = Image.open(player.image_path)
    img = img.resize((image_size -10, image_size - 10), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    img_label = tk.Label(image_frame, image=photo, bg="black")
    img_label.image = photo  # Keep a reference!
    img_label.place(relx=0.5, rely=0.5, anchor="center")  # Center the image
except Exception as e:
    print(f"Error loading player image: {e}")
    tk.Label(image_frame, text="No Image", fg="white", bg="black").place(relx=0.5, rely=0.5, anchor="center")


# Bottom left (PVT, RIG, RES, STA)
stats_frame = tk.Frame(root, bg="black")
stats_frame.grid(row=12, column=1, rowspan=4, sticky="nw", padx=2, pady=0)

# Global variables to store stat bar widgets for updates
stat_bars = {}

def draw_stat_bar(parent, label, current, maximum, bar_width=400, bar_height=20):
    row_frame = tk.Frame(parent, bg="black")
    row_frame.pack(anchor="w", pady=1)
    tk.Label(row_frame, text=label, fg="green", bg="black", font=("Times", 20)).pack(side="left")
    canvas = tk.Canvas(row_frame, width=bar_width, height=bar_height, bg="black", highlightthickness=0)
    canvas.pack(side="left", padx=(5, 0))
    canvas.create_rectangle(0, 0, bar_width, bar_height, fill="#222", outline="")
    fill_width = int(bar_width * current / maximum) if maximum > 0 else 0
    canvas.create_rectangle(0, 0, fill_width, bar_height, fill="green", outline="")
    canvas.create_text(bar_width // 2, bar_height // 2, text=f"{current}/{maximum}", fill="white", font=("Times", 9))
    return canvas

def update_stat_bar(canvas, current, maximum, bar_width=400, bar_height=20):
    """Update an existing stat bar with new values"""
    canvas.delete("all")
    canvas.create_rectangle(0, 0, bar_width, bar_height, fill="#222", outline="")
    fill_width = int(bar_width * current / maximum) if maximum > 0 else 0
    canvas.create_rectangle(0, 0, fill_width, bar_height, fill="green", outline="")
    canvas.create_text(bar_width // 2, bar_height // 2, text=f"{current}/{maximum}", fill="white", font=("Times", 9))

def update_body_part_hp_bars():
    """Update all body part HP bars with current values"""
    global body_part_hp_canvases
    
    if len(body_part_hp_canvases) == len(player.body_parts):
        for idx, (canvas, part) in enumerate(zip(body_part_hp_canvases, player.body_parts)):
            try:
                canvas.delete("all")
                canvas.create_rectangle(15, 0, body_part_bar_width, body_part_bar_height, fill="#222", outline="")
                fill_width = int(body_part_bar_width * part.p_pvt / part.max_p_pvt) if part.max_p_pvt > 0 else 0
                canvas.create_rectangle(15, 0, fill_width, body_part_bar_height, fill="green", outline="")
                canvas.create_text(body_part_bar_width // 2, body_part_bar_height // 2, text=f"{part.p_pvt}/{part.max_p_pvt}", fill="white", font=("Times", 10))
            except Exception as e:
                print(f"Error updating body part HP bar {idx}: {e}")

stat_bars['pvt'] = draw_stat_bar(stats_frame, "PVT", player.pvt, player.max_pvt)
stat_bars['rig'] = draw_stat_bar(stats_frame, "RIG", player.rig, player.max_rig)
stat_bars['res'] = draw_stat_bar(stats_frame, "RES", player.res, player.max_res)
stat_bars['sta'] = draw_stat_bar(stats_frame, "STA", player.sta, player.max_sta)

# Bottom right (FOR, DES, SPE, VEL)
stats_right_frame = tk.Frame(root, bg="black", width=600, height=120)
stats_right_frame.place(x=LEFT_PANEL_WIDTH + 400 + 200, y=MENU_TOP_Y + 285)

stat_font = ("Times", 20)
number_font = ("Times", 18)

# Global variables to store right stat labels for updates
right_stat_labels = {}

def draw_right_stat_row(parent, label, current, maximum, buf_value):
    row_frame = tk.Frame(parent, bg="black")
    row_frame.pack(anchor="e", pady=1)
    
    # Label for the stat name
    tk.Label(row_frame, text=label, fg="green", bg="black", font=stat_font, width=4, anchor="w").pack(side="left")
    
    # Stats section with vertical lines
    stats_section = tk.Frame(row_frame, bg="black")
    stats_section.pack(side="left", padx=(10, 0))
    
    # Max value (fixed width column for up to 4 digits, centered)
    max_label = tk.Label(stats_section, text=str(maximum), fg="white", bg="black", font=number_font, width=4, anchor="center")
    max_label.pack(side="left")
    
    # First vertical line
    line1 = tk.Frame(stats_section, bg="white", width=1, height=22)
    line1.pack(side="left", padx=(5, 5))
    
    # Buffer value (fixed width column for up to 4 digits, centered)
    buf_label = tk.Label(stats_section, text=str(buf_value), fg="yellow", bg="black", font=number_font, width=4, anchor="center")
    buf_label.pack(side="left")
    
    # Second vertical line
    line2 = tk.Frame(stats_section, bg="white", width=1, height=22)
    line2.pack(side="left", padx=(5, 5))
    
    # Current value (fixed width column for up to 4 digits, centered)
    current_label = tk.Label(stats_section, text=str(current), fg="cyan", bg="black", font=number_font, width=4, anchor="center")
    current_label.pack(side="left")
    
    return {'max': max_label, 'buf': buf_label, 'current': current_label}

# Draw the right stats with the new format and store references
right_stat_labels['forz'] = draw_right_stat_row(stats_right_frame, "FOR", player.forz, player.max_for, player.buf_forz)
right_stat_labels['des'] = draw_right_stat_row(stats_right_frame, "DES", player.des, player.max_des, player.buf_des)
right_stat_labels['spe'] = draw_right_stat_row(stats_right_frame, "SPE", player.spe, player.max_spe, player.buf_spe)
right_stat_labels['vel'] = draw_right_stat_row(stats_right_frame, "VEL", player.vel, player.max_vel, player.buf_vel)

# Bottom menu
menu_labels = ["NEMICO", "MOSSE", "EFFETTI", "ABILITÀ", "OGGETTI", "PASSA"]

# Create a fixed frame for the menu bar
menu_bar_width = 1200
menu_bar_height = 40
menu_bar_x = LEFT_PANEL_WIDTH + 30
menu_bar_y = MENU_TOP_Y + 245

menu_bar = tk.Frame(root, bg="black", width=menu_bar_width, height=menu_bar_height)
menu_bar.place(x=menu_bar_x, y=menu_bar_y)

menu_label_widgets = []
menu_spacing = [10, 180, 320, 475, 633, 790]  # Same as MENU_ITEM_SPACING

for idx, label in enumerate(menu_labels):
    # Color the PASSA menu in yellow
    color = "yellow" if label == "PASSA" else "white"
    lbl = tk.Label(menu_bar, text=label, fg=color, bg="black", font=("Times", 18))
    lbl.place(x=menu_spacing[idx], y=0)
    menu_label_widgets.append(lbl)

#LINES SECTION

# Vertical line between left panel and stats
separator_left = tk.Frame(root, bg="white", width=2, height=1800)
separator_left.place(x=LEFT_PANEL_WIDTH, y=0)

# Horizontal line above bottom menu
separator_menu = tk.Frame(root, bg="white", height=MENU_HEIGHT, width=MENU_WIDTH+100)
separator_menu.place(x=LEFT_PANEL_WIDTH, y=MENU_TOP_Y+242)

# Horizontal line under bottom menu
separator_menu = tk.Frame(root, bg="white", height=MENU_HEIGHT, width=MENU_WIDTH+100)
separator_menu.place(x=LEFT_PANEL_WIDTH, y=MENU_TOP_Y+278)

root.geometry("1600x1000")
root.resizable(False, False)

# Periodic stat update routine (runs every 100ms)
# Counter for move recalculation (less frequent)
move_recalc_counter = 0

def periodic_stat_update():
    """
    Periodic function that updates all character stats and refreshes UI.
    This ensures stats stay synchronized with buffs/debuffs and body part health.
    """
    global move_recalc_counter
    
    # First recalculate health from body parts
    recalculate_all_character_health()
    
    # Then update all other stats
    update_all_characters_stats()
    
    # Recalculate moves every 10 cycles (1 second) to avoid performance issues
    move_recalc_counter += 1
    if move_recalc_counter >= 10:
        recalculate_all_character_moves()
        move_recalc_counter = 0
    
    # Update left stat bars
    if 'pvt' in stat_bars:
        update_stat_bar(stat_bars['pvt'], player.pvt, player.max_pvt)
    if 'rig' in stat_bars:
        update_stat_bar(stat_bars['rig'], player.rig, player.max_rig)
    if 'res' in stat_bars:
        update_stat_bar(stat_bars['res'], player.res, player.max_res)
    if 'sta' in stat_bars:
        # Use effective_max_sta if available, otherwise fall back to max_sta
        max_sta_display = getattr(player, 'effective_max_sta', player.max_sta)
        update_stat_bar(stat_bars['sta'], player.sta, max_sta_display)
    
    # Update right stat labels
    if 'forz' in right_stat_labels:
        labels = right_stat_labels['forz']
        labels['max'].config(text=str(player.max_for))
        labels['buf'].config(text=str(player.buf_forz))
        labels['current'].config(text=str(player.forz))
    
    if 'des' in right_stat_labels:
        labels = right_stat_labels['des']
        labels['max'].config(text=str(player.max_des))
        labels['buf'].config(text=str(player.buf_des))
        labels['current'].config(text=str(player.des))
    
    if 'spe' in right_stat_labels:
        labels = right_stat_labels['spe']
        labels['max'].config(text=str(player.max_spe))
        labels['buf'].config(text=str(player.buf_spe))
        labels['current'].config(text=str(player.spe))
    
    if 'vel' in right_stat_labels:
        labels = right_stat_labels['vel']
        labels['max'].config(text=str(player.max_vel))
        labels['buf'].config(text=str(player.buf_vel))
        labels['current'].config(text=str(player.vel))
    
    # Update body part HP bars
    update_body_part_hp_bars()
    
    # Schedule the next update
    root.after(100, periodic_stat_update)

# Start the periodic update routine
root.after(100, periodic_stat_update)

# Initialize game data before starting the main loop
initialize_game_data()

#------------------------------------------------------------------------------------------------------------------

# --- NAVIGAZIONE MENU' principale ---

TRIANGLE_SIZE = 24
MENU_ITEM_SPACING = [10, 180, 320, 475, 633, 790]  # Spacing between menu items
MENU_START_X = LEFT_PANEL_WIDTH + 520
MENU_Y = MENU_TOP_Y + 23

menu_selection_index = 0  # Start with first menu item selected

triangle_canvas = tk.Canvas(root, width=TRIANGLE_SIZE, height=TRIANGLE_SIZE, bg="black", highlightthickness=0, bd=0)
triangle_canvas.place(x=MENU_START_X - TRIANGLE_SIZE//2, y=MENU_Y - TRIANGLE_SIZE)

def draw_triangle(index):
    x = TRIANGLE_SIZE // 2
    y = 0
    triangle_canvas.delete("all")
    triangle_canvas.create_polygon(
        x - TRIANGLE_SIZE // 2, y,
        x - TRIANGLE_SIZE // 2, y + TRIANGLE_SIZE,
        x + TRIANGLE_SIZE // 2, y + TRIANGLE_SIZE // 2,
        fill="white"
    )
    # Place triangle relative to menu_bar
    triangle_canvas.place(
        x=menu_bar_x + menu_spacing[index] -15 - TRIANGLE_SIZE // 2,
        y=menu_bar_y - TRIANGLE_SIZE + 28
    )

draw_triangle(menu_selection_index)

# --- NAVIGAZIONE MENU' : NEMICO ---

enemy_image_frame = None  # To keep reference
enemy_name_label = None   # To keep reference
enemy_parts_frame = None  # To keep reference
enemy_parts_triangle = None  # To keep reference
enemy_parts_index = 0    # Current selection in enemy body parts
enemy_part_attr_frame = None  # Frame for showing enemy part attributes
# Global variables for enemy parts positioning
enemy_parts_x = 0
enemy_parts_y = 0

def draw_enemy_parts_triangle():
    """Draw the triangle indicator for enemy parts selection"""
    global enemy_parts_triangle, enemy_parts_x, enemy_parts_y
    if enemy_parts_triangle is not None:
        enemy_parts_triangle.destroy()
    triangle_size = 20
    y_offset = enemy_parts_index * 40 + 6
    enemy_parts_triangle = tk.Canvas(root, width=triangle_size, height=triangle_size, bg="black", highlightthickness=0)
    enemy_parts_triangle.place(x=enemy_parts_x + 2, y=enemy_parts_y + y_offset)
    enemy_parts_triangle.create_polygon(
        0, 0,
        triangle_size, triangle_size / 2,
        0, triangle_size,
        fill="white"
    )

def show_enemy_part_attributes():
    """Show attributes for the selected enemy part"""
    global enemy_part_attr_frame, enemy_parts_x, enemy_parts_y
    # Remove previous attribute frame if it exists
    if enemy_part_attr_frame is not None:
        enemy_part_attr_frame.destroy()
        enemy_part_attr_frame = None
    # Show for any selected enemy part if enemy menu is active
    if menu_selection_index == 0 and 0 <= enemy_parts_index < len(enemy.body_parts):
        part = enemy.body_parts[enemy_parts_index]
        enemy_part_attr_frame = tk.Frame(root, bg="black", width=350, height=350, highlightbackground="white", highlightthickness=1)
        attr_x = enemy_parts_x + 250
        attr_y = enemy_parts_y
        enemy_part_attr_frame.place(x=attr_x, y=attr_y)
        enemy_part_attr_frame.propagate(False)
        # Title
        tk.Label(enemy_part_attr_frame, text=part.name, fg="white", bg="black", font=("Times", 22, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        # PVT bar
        bar_frame = tk.Frame(enemy_part_attr_frame, bg="black")
        bar_frame.pack(anchor="w", padx=10, pady=(10, 0))
        tk.Label(bar_frame, text="PVT", fg="green", bg="black", font=("Times", 16)).pack(side="left")
        bar_width = 200
        bar_height = 18
        canvas = tk.Canvas(bar_frame, width=bar_width, height=bar_height, bg="black", highlightthickness=0)
        canvas.pack(side="left", padx=(5, 0))
        canvas.create_rectangle(0, 0, bar_width, bar_height, fill="#222", outline="")
        fill_width = int(bar_width * part.p_pvt / part.max_p_pvt) if part.max_p_pvt > 0 else 0
        canvas.create_rectangle(0, 0, fill_width, bar_height, fill="green", outline="")
        canvas.create_text(bar_width // 2, bar_height // 2, text=f"{part.p_pvt}/{part.max_p_pvt}", fill="white", font=("Times", 10))
        # Effetti attributes
        effetti = part.p_eff
        tk.Label(enemy_part_attr_frame, text="Effetti:", fg="white", bg="black", font=("Times", 16, "underline")).pack(anchor="w", padx=10, pady=(15, 0))
        effetti_dict = vars(effetti)
        for eff_name, eff_val in effetti_dict.items():
            # eff_val is a list: [name, level, duration, immunity]
            if isinstance(eff_val, list) and len(eff_val) >= 4 and eff_val[1] != 0:
                # Only show if level != 0, and only show level, duration, immunity
                eff_str = f"{eff_name}:\nLv.={eff_val[1]}, Dur.={eff_val[2]}, Imm.={eff_val[3]}"
                tk.Label(enemy_part_attr_frame, text=eff_str, fg="#00e0e0", bg="black", font=("Times", 14), justify="left", anchor="w").pack(anchor="w", padx=20)

def show_enemy_panel():
    global enemy_image_frame, enemy_name_label, enemy_parts_frame, enemy_parts_triangle, enemy_parts_index, enemy_part_attr_frame
    
    print(f"DEBUG: show_enemy_panel called, menu_selection_index = {menu_selection_index}")
    
    # Remove previous enemy frame if it exists
    if enemy_image_frame is not None:
        try:
            enemy_image_frame.destroy()
        except tk.TclError:
            pass  # Widget already destroyed
        enemy_image_frame = None
    
    # Remove previous enemy name label if it exists
    if enemy_name_label is not None:
        try:
            enemy_name_label.destroy()
        except tk.TclError:
            pass
        enemy_name_label = None
    
    # Remove previous enemy parts frame if it exists
    if enemy_parts_frame is not None:
        try:
            enemy_parts_frame.destroy()
        except tk.TclError:
            pass
        enemy_parts_frame = None
    
    # Remove previous triangle if it exists
    if enemy_parts_triangle is not None:
        try:
            enemy_parts_triangle.destroy()
        except tk.TclError:
            pass
        enemy_parts_triangle = None
    
    # Remove previous attribute frame if it exists
    if enemy_part_attr_frame is not None:
        try:
            enemy_part_attr_frame.destroy()
        except tk.TclError:
            pass
        enemy_part_attr_frame = None
    
    enemy_parts_index = 0  # Reset selection when menu is shown

    # Only show if "NEMICO" is selected (index 0)
    if menu_selection_index == 0:
        print("DEBUG: Creating enemy panel...")
        
        enemy_image_frame = tk.Frame(
            root,
            bg="black",
            highlightbackground="white",
            highlightthickness=1,
            width=700,
            height=700
        )
        enemy_image_frame.place(x=LEFT_PANEL_WIDTH + 10, y=MENU_TOP_Y - 550)
        enemy_image_frame.propagate(False)
        
        # Force the frame to update before loading image
        enemy_image_frame.update_idletasks()
        
        try:
            # Use Path for better cross-platform compatibility and ensure file exists
            image_path = Path(enemy.image_path)
            
            print(f"DEBUG: Attempting to load image from: {image_path}")
            print(f"DEBUG: File exists: {image_path.exists()}")
            
            # Check if file exists
            if not image_path.exists():
                print(f"Enemy image file not found: {image_path}")
                error_label = tk.Label(enemy_image_frame, text="Image File Not Found", fg="red", bg="black", font=("Times", 16))
                error_label.place(relx=0.5, rely=0.5, anchor="center")
            else:
                print(f"Loading enemy image from: {image_path}")
                
                # Open image - use the same approach as V1
                img = Image.open(enemy.image_path)
                frames = []
                
                print(f"DEBUG: Image opened, format: {img.format}, mode: {img.mode}, size: {img.size}")
                
                try:
                    while True:
                        frame = img.copy().convert("P")
                        frame = frame.resize((700, 700), Image.LANCZOS)
                        frames.append(ImageTk.PhotoImage(frame))
                        img.seek(len(frames))
                except EOFError:
                    pass
                
                print(f"Successfully loaded {len(frames)} frames from enemy GIF")
                
                if frames:
                    img_label = tk.Label(enemy_image_frame, bg="black")
                    img_label.place(relx=0.5, rely=0.5, anchor="center")
                    
                    def animate(index=0):
                        img_label.config(image=frames[index])
                        img_label.image = frames[index]
                        enemy_image_frame.after(img.info.get('duration', 100), animate, (index + 1) % len(frames))
                    
                    print("DEBUG: Starting GIF animation")
                    animate()
                else:
                    error_label = tk.Label(enemy_image_frame, text="No Frames Found", fg="red", bg="black", font=("Times", 16))
                    error_label.place(relx=0.5, rely=0.5, anchor="center")
                    
        except Exception as e:
            print(f"Error loading enemy image: {e}")
            print(f"Attempted to load: {enemy.image_path}")
            traceback.print_exc()
            error_label = tk.Label(enemy_image_frame, text=f"Error: {str(e)}", fg="red", bg="black", wraplength=600, font=("Times", 14))
            error_label.place(relx=0.5, rely=0.5, anchor="center")
        # Show enemy name label under the image
        enemy_name_label = tk.Label(
            root,
            text=enemy.name,
            fg="white",
            bg="black",
            font=("Times", 20)
        )
        enemy_name_label.place(
            x=LEFT_PANEL_WIDTH + 22,
            y=MENU_TOP_Y - 550 + 680,
            width=700,
            height=40
        )
        # Show enemy body parts in a new vertical menu
        enemy_parts_frame = tk.Frame(root, bg="black", width=220, height=700)
        enemy_parts_x = LEFT_PANEL_WIDTH + 740
        enemy_parts_y = MENU_TOP_Y - 520 + 40
        enemy_parts_frame.place(x=enemy_parts_x, y=enemy_parts_y)
        enemy_parts_frame.propagate(False)  # Prevent frame from shrinking to fit contents
        part_labels = []
        for idx, part in enumerate(enemy.body_parts):
            lbl = tk.Label(
                enemy_parts_frame,
                text=part.name,
                fg="white",
                bg="black",
                font=("Times", 21),
                anchor="w"
            )
            lbl.place(x=30, y=idx*40, width=220, height=32)
            part_labels.append(lbl)

        # Update global position variables for the triangle and attributes
        globals()['enemy_parts_x'] = enemy_parts_x
        globals()['enemy_parts_y'] = enemy_parts_y

        # Initial display update
        draw_enemy_parts_triangle()
        show_enemy_part_attributes()

# --- NAVIGAZIONE MENU' : MOSSE ---

moves_table_frame = None  # To keep reference
moves_selection_index = 0  # Current move selection index
moves_triangle_cursor = None  # Triangle cursor for move selection
move_row_frames = []  # To store move row frames for highlighting

# --- NAVIGAZIONE MENU' : ABILITÀ ---

ability_table_frame = None  # To keep reference
ability_selection_index = 0  # Current ability selection index
ability_row_frames = []  # To store ability row frames for highlighting

# --- NAVIGAZIONE MENU' : EFFETTI ---

effects_table_frame = None  # To keep reference
effects_selection_index = 0  # Current effects selection index

# --- NAVIGAZIONE MENU' : PASSA ---

passa_table_frame = None  # To keep reference
passa_selection_index = 0  # Current passa selection index (0=YES, 1=NO)

# --- ENEMY TURN SYSTEM ---

enemy_turn_active = False  # Flag to indicate if enemy turn is in progress
player_has_control = True  # Flag to indicate if player has menu control

# --- MOVE USAGE SYSTEM ---

# Global variables for move usage
move_usage_active = False
target_selection_frame = None
target_selection_index = 0
target_triangle_cursor = None
selected_move = None
message_label = None

def show_message(text, duration=500):
    """Display a temporary message that disappears after the specified duration (in milliseconds)"""
    global message_label
    
    # Remove any existing message
    if message_label is not None:
        message_label.destroy()
    
    # Create new message label
    message_label = tk.Label(
        root,
        text=text,
        fg="yellow",
        bg="black",
        font=("Times", 24, "bold"),
        relief="solid",
        borderwidth=2,
        padx=20,
        pady=10
    )
    
    # Center the message on screen
    message_label.place(relx=0.6, rely=0.3, anchor="center")
    
    # Schedule message removal
    def remove_message():
        global message_label
        if message_label is not None:
            message_label.destroy()
            message_label = None
    
    root.after(duration, remove_message)

def show_target_selection():
    """Show enemy body parts selection menu for targeting"""
    global target_selection_frame, target_selection_index, target_triangle_cursor
    
    # Clear any existing target selection
    if target_selection_frame is not None:
        target_selection_frame.destroy()
        target_selection_frame = None
    if target_triangle_cursor is not None:
        target_triangle_cursor.destroy()
        target_triangle_cursor = None
    
    target_selection_index = 0
    
    # Create target selection frame (similar to enemy panel but for targeting)
    target_selection_frame = tk.Frame(
        root,
        bg="black",
        highlightbackground="white",
        highlightthickness=2,
        width=1200,
        height=750
    )
    target_selection_frame.place(x=LEFT_PANEL_WIDTH + 50, y=15)
    target_selection_frame.propagate(False)

    attack_info = (
        f"{selected_move.name}\n"
        f"Tipo: {selected_move.tipo} | "
        f"Danno: {selected_move.danno} | "
        f"Stamina: {selected_move.stamina_cost} | "
        f"Accuratezza: {selected_move.accuracy}%\n"
        f"Effetti: {', '.join(selected_move.eff_appl) if selected_move.eff_appl else 'Nessuno'}\n"
        f"Requisiti: {', '.join(selected_move.reqs) if selected_move.reqs else 'Nessuno'}\n"
        f"Tipologia: {', '.join(selected_move.elem) if selected_move.elem else 'Nessuno'}"
    )
    attack_info_label = tk.Label(
        target_selection_frame,
        text=attack_info,
        fg="#FFFFFF",
        bg="black",
        font=("Times", 16, "bold"),
        justify="left"
    )
    attack_info_label.pack(pady=5)

    # Enemy name
    enemy_name_label = tk.Label(
        target_selection_frame,
        text=f"Bersaglio: {enemy.name}",
        fg="white",
        bg="black",
        font=("Times", 18)
    )
    enemy_name_label.pack(pady=5)

    # --- Enemy GIF (now placed after enemy name) ---
    enemy_gif_frame = tk.Frame(target_selection_frame, bg="black", width=180, height=180)
    enemy_gif_frame.pack(pady=10)
    try:
        img = Image.open(enemy.image_path)
        frames = []
        while True:
            frame = img.copy().convert("RGBA")
            frame = frame.resize((160, 160), Image.LANCZOS)
            frames.append(ImageTk.PhotoImage(frame))
            img.seek(len(frames))
    except EOFError:
        pass
    except Exception as e:
        print(f"Error loading enemy GIF: {e}")
        frames = []
    if frames:
        img_label = tk.Label(enemy_gif_frame, bg="black")
        img_label.place(relx=0.5, rely=0.5, anchor="center")
        def animate(index=0):
            img_label.config(image=frames[index])
            img_label.image = frames[index]
            enemy_gif_frame.after(img.info.get('duration', 100), animate, (index + 1) % len(frames))
        animate()
    else:
        tk.Label(enemy_gif_frame, text="No GIF", fg="white", bg="black").place(relx=0.5, rely=0.5, anchor="center")

    # Body parts list (now appears after GIF)
    parts_frame = tk.Frame(target_selection_frame, bg="black")
    parts_frame.pack(pady=(20, 20))  # Adjust as needed

    part_labels = []
    hp_bars = []
    for idx, part in enumerate(enemy.body_parts):
        row_frame = tk.Frame(parts_frame, bg="black")
        row_frame.pack(anchor="w", pady=3, padx=50)
        part_label = tk.Label(
            row_frame,
            text=f"{part.name}",
            fg="white",
            bg="black",
            font=("Times", 16),
            anchor="w",
            width=18
        )
        part_label.pack(side="left")
        # HP bar next to part name
        bar_width = 120
        bar_height = 16
        hp_canvas = tk.Canvas(row_frame, width=bar_width, height=bar_height, bg="black", highlightthickness=0)
        hp_canvas.pack(side="left", padx=(10, 0))
        hp_canvas.create_rectangle(0, 0, bar_width, bar_height, fill="#222", outline="")
        fill_width = int(bar_width * part.p_pvt / part.max_p_pvt) if part.max_p_pvt > 0 else 0
        hp_canvas.create_rectangle(0, 0, fill_width, bar_height, fill="green", outline="")
        hp_canvas.create_text(bar_width // 2, bar_height // 2, text=f"{part.p_pvt}/{part.max_p_pvt}", fill="white", font=("Times", 9))
        part_labels.append(part_label)
        hp_bars.append(hp_canvas)

    
    # Instructions
    instructions = tk.Label(
        target_selection_frame,
        text="Usa ↑↓ per selezionare, ENTER per confermare, ESC per annullare",
        fg="gray",
        bg="black",
        font=("Times", 14)
    )
    instructions.pack(side="bottom", pady=10)
    
    def draw_target_triangle():
        global target_triangle_cursor
        if target_triangle_cursor is not None:
            target_triangle_cursor.destroy()

        triangle_size = 16
        # cursor_x = LEFT_PANEL_WIDTH + 240  # Adjust as needed

        # Get the y position of the selected label relative to root
        selected_label = part_labels[target_selection_index]
        # Get y position of label within its parent frame
        label_y = selected_label.winfo_rooty()
        label_x = selected_label.winfo_rootx()
        # Get y position of root window
        root_y = root.winfo_rooty()
        root_x = root.winfo_rootx()
        # Calculate x and y position relative to root window
        cursor_y = label_y - root_y + 5
        cursor_x = label_x - root_x - 20 

        target_triangle_cursor = tk.Canvas(root, width=triangle_size, height=triangle_size, bg="black", highlightthickness=0)
        target_triangle_cursor.place(x=cursor_x, y=cursor_y)
        target_triangle_cursor.create_polygon(
            0, 0,
            0, triangle_size,
            triangle_size, triangle_size // 2,
            fill="red"
        )
    
    root.update_idletasks()
    draw_target_triangle()
    
    def on_target_nav(event):
        global target_selection_index
        if not move_usage_active:
            return

        if event.keysym == "Down":
            target_selection_index = (target_selection_index + 1) % len(enemy.body_parts)
        elif event.keysym == "Up":
            target_selection_index = (target_selection_index - 1) % len(enemy.body_parts)
        elif event.keysym == "Return":  # ENTER key
            execute_move()
            return
        elif event.keysym in ("Escape", "Canc", "Left", "Right"):  # ESC, Canc, Left, Right
            cancel_move_usage()
            return

        draw_target_triangle()

    # Bind navigation keys for target selection
    root.bind("<Up>", on_target_nav)
    root.bind("<Down>", on_target_nav)
    root.bind("<Return>", on_target_nav)
    root.bind("<Escape>", on_target_nav)
    root.bind("<Left>", on_target_nav)
    root.bind("<Right>", on_target_nav)

def execute_move():
    """Execute the selected move on the selected target"""
    global move_usage_active, selected_move, target_selection_index
    
    if not move_usage_active or selected_move is None:
        return
    
    target_part = enemy.body_parts[target_selection_index]
    
    # Step 1: Subtract stamina cost from player
    old_stamina = player.sta
    player.sta -= selected_move.stamina_cost
    
    # Ensure stamina doesn't go below 0
    if player.sta < 0:
        player.sta = 0
    
    print(f"STAMINA DEBUG: Player stamina {old_stamina} -> {player.sta} (reduced by {selected_move.stamina_cost})")
    print(f"STAMINA DEBUG: Player effective max stamina: {getattr(player, 'effective_max_sta', player.max_sta)}")
    
    # Step 2: Calculate accuracy roll
    accuracy_roll = random.randint(1, 100)
    print(f"Accuracy roll: {accuracy_roll}, Move accuracy: {selected_move.accuracy}")
    
    if accuracy_roll > selected_move.accuracy:
        # Miss - show miss message
        miss_message = f"{player.name} ha fallito l'attacco!"
        show_message(miss_message, 500)
        print(f"Attack missed! {miss_message}")
        
        # Return to moves menu after message
        def return_to_moves():
            cancel_move_usage()
        root.after(500, return_to_moves)
        
    else:
        # Hit - show hit message and apply damage
        hit_message = f"{player.name} ha colpito {target_part.name} del {enemy.name}!"
        show_message(hit_message, 1000)
        
        # Apply damage
        old_hp = target_part.p_pvt
        damage_to_deal = selected_move.danno
        target_part.p_pvt -= damage_to_deal
        if target_part.p_pvt < 0:
            target_part.p_pvt = 0
            
        print(f"Damage applied to {enemy.name}'s {target_part.name}: {old_hp} -> {target_part.p_pvt} (Damage: {damage_to_deal})")

        # Recalculate enemy health
        enemy.calculate_health_from_body_parts()

        # Return to moves menu after message
        def return_to_moves():
            cancel_move_usage()
        root.after(1000, return_to_moves)

def cancel_move_usage():
    global move_usage_active, target_selection_frame, target_triangle_cursor, selected_move

    move_usage_active = False
    selected_move = None

    # Clean up target selection UI
    if target_selection_frame is not None:
        target_selection_frame.destroy()
        target_selection_frame = None
    if target_triangle_cursor is not None:
        target_triangle_cursor.destroy()
        target_triangle_cursor = None

    # Restore moves menu navigation
    setup_moves_navigation()

    # Restore global menu navigation for left/right arrows
    root.unbind("<Left>")
    root.unbind("<Right>")
    root.bind("<Left>", move_selection)
    root.bind("<Right>", move_selection)
    
    # Restore moves menu navigation
    setup_moves_navigation()

def use_selected_move():
    """Attempt to use the currently selected move"""
    global move_usage_active, selected_move
    
    if menu_selection_index != 1:  # Not in moves menu
        return
    
    if not hasattr(player, 'moves') or not player.moves or len(player.moves) == 0:
        return
    
    if moves_selection_index < 0 or moves_selection_index >= len(player.moves):
        return
    
    selected_move = player.moves[moves_selection_index]
    
    # Check if player has enough stamina
    if player.sta < selected_move.stamina_cost:
        show_message("Non hai abbastanza stamina!", 500)
        print(f"Not enough stamina! Required: {selected_move.stamina_cost}, Current: {player.sta}")
        return
    
    # Player has enough stamina - start target selection
    move_usage_active = True
    show_target_selection()

def show_ability_details():
    """Show detailed information about the selected ability"""
    if menu_selection_index != 3:  # Not in ability menu
        return
    
    if not hasattr(player, 'ability') or not player.ability or len(player.ability) == 0:
        return
    
    if ability_selection_index < 0 or ability_selection_index >= len(player.ability):
        return
    
    selected_ability = player.ability[ability_selection_index]
    
    # Show detailed ability information in a popup or message
    detail_text = f"{selected_ability.name}\nCosto: {selected_ability.punti} punti\n\n{selected_ability.descriptionLong}"
    show_message(detail_text, 3000)  # Show for 3 seconds

def show_abilities_panel():
    """Show or hide the abilities panel based on menu selection"""
    global ability_table_frame, ability_selection_index, ability_row_frames
    
    print(f"DEBUG: show_abilities_panel called, menu_selection_index = {menu_selection_index}")
    
    # Remove previous ability frame if it exists
    if ability_table_frame is not None:
        try:
            ability_table_frame.destroy()
        except tk.TclError:
            pass  # Widget already destroyed
        ability_table_frame = None
    
    # Clear ability row frames when panel is being destroyed
    ability_row_frames.clear()
    
    ability_selection_index = 0  # Reset selection when menu is shown

    # Only show if "ABILITÀ" is selected (index 3)
    if menu_selection_index == 3:
        print("DEBUG: Creating abilities panel...")
        
        available_width = 1000  # Set a fixed width for the panel
        available_height = MENU_TOP_Y + 240 - 150  # 730 pixels

        center_x = (root.winfo_width() - available_width) // 2

        # Create main frame for the abilities table
        ability_table_frame = tk.Frame(
            root,
            bg="black",
            highlightbackground="white",
            highlightthickness=1,
            width=available_width,
            height=available_height
        )
        ability_table_frame.place(x=center_x + 150, y=75)  # Centered horizontally
        ability_table_frame.propagate(False)
        
        # Title
        title_label = tk.Label(
            ability_table_frame,
            text=f"{player.name}'s Abilities",
            fg="white",
                       bg="black",
            font=("Times", 20, "bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Add instructions
        instructions_label = tk.Label(
            ability_table_frame,
            text="Usa ↑↓ per navigare, ENTER per dettagli abilità",
            fg="white",
            bg="black",
            font=("Times", 14)
        )
        instructions_label.pack(pady=(0, 10))

        # Container for table and potential scrollbar
        table_container = tk.Frame(ability_table_frame, bg="black")
        table_container.pack(fill="both", expand=True, padx=50, pady=(0, 10))
        
        # Calculate if scrollbar is needed
        estimated_row_height = 35
        header_height = 40
        content_height = available_height - 140  # Space for title, instructions and padding
        
        ability_count = len(player.ability) if hasattr(player, 'ability') and player.ability else 0
        total_content_height = header_height + (ability_count * estimated_row_height)
        needs_scrollbar = total_content_height > content_height
        
        # Adjust canvas width based on scrollbar need
        canvas_width = available_width - 40  # Base padding
        if needs_scrollbar:
            canvas_width -= 20  # Additional space for scrollbar
        
        # Create scrollable frame for the table
        canvas = tk.Canvas(table_container, bg="black", width=canvas_width, height=content_height, highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg="black")
        
        if needs_scrollbar:
            scrollbar = tk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Table headers
        headers = ["NOME ABILITÀ", "PUNTI", "DESCRIZIONE"]
        col_widths_pixels = [200, 80, 400]
        
        # Header row
        header_frame = tk.Frame(scrollable_frame, bg="black")
        header_frame.pack(fill="x", padx=5, pady=(3, 8))

        for i, (header, width_px) in enumerate(zip(headers, col_widths_pixels)):
            header_label = tk.Label(
                header_frame,
                text=header,
                fg="#FFD700",  # Gold color for headers
                bg="#1a1a1a",  # Slightly lighter background
                font=("Times", 11, "bold"),
                height=2,
                anchor="center",
                relief="raised",
                borderwidth=1
            )
            header_label.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
            
        # Configure column weights for proper spacing
        for i in range(len(headers)):
            header_frame.grid_columnconfigure(i, weight=1, minsize=col_widths_pixels[i])
      
        # Data rows
        if hasattr(player, 'ability') and player.ability:
            ability_row_frames.clear()

            for row_idx, ability in enumerate(player.ability):
                row_frame = tk.Frame(scrollable_frame, bg="black")
                row_frame.pack(fill="x", padx=5, pady=2)
                ability_row_frames.append(row_frame)  # Store reference
                
                # Prepare data for each column
                ability_data = [
                    ability.name,                     # NOME
                    str(ability.punti),              # PUNTI
                    ability.description,             # DESCRIZIONE
                ]
                
                # Create cells for each data column
                for col_idx, (data, width_px) in enumerate(zip(ability_data, col_widths_pixels)):
                    # Color coding for different data types
                    if col_idx == 0:  # NOME
                        color = "#FF6B6B"  # Red for name
                    elif col_idx == 1:  # PUNTI
                        color = "#90EE90"  # Light green for points
                    else:
                        color = "white"
                    
                    # Alternate row background for better readability
                    bg_color = "#0d0d0d" if row_idx % 2 == 0 else "black"
                    
                    cell_label = tk.Label(
                        row_frame,
                        text=data,
                        fg=color,
                        bg=bg_color,
                        font=("Times", 10),
                        height=2,
                        anchor="center",
                        relief="solid",
                        borderwidth=1,
                        wraplength=width_px-5
                    )
                    cell_label.grid(row=0, column=col_idx, padx=1, pady=1, sticky="ew")
                
                # Configure column weights for proper spacing
                for i in range(len(headers)):
                    row_frame.grid_columnconfigure(i, weight=1, minsize=col_widths_pixels[i])
        
        else:
            # No abilities message
            no_ability_label = tk.Label(
                scrollable_frame,
                text="Nessuna abilità disponibile",
                fg="gray",
                bg="black",
                font=("Times", 18),
                pady=40
            )
            no_ability_label.pack()
        
        # Pack canvas and scrollbar only if needed
        canvas.pack(side="left", fill="both", expand=True)
        if needs_scrollbar:
            scrollbar.pack(side="right", fill="y")

        def highlight_selected_ability_row_local():
            """Local highlight function for abilities panel"""
            for i, row in enumerate(ability_row_frames):
                bg = "#880000" if i == ability_selection_index else ("#0d0d0d" if i % 2 == 0 else "black")
                for widget in row.winfo_children():
                    widget.config(bg=bg)
        
        # Set up ability navigation
        setup_ability_navigation()

        # Highlight selected row
        highlight_selected_ability_row_local()

def highlight_selected_move_row():
    global move_row_frames, moves_selection_index
    if not move_row_frames:
        return
    for i, row in enumerate(move_row_frames):
        bg = "#880000" if i == moves_selection_index else ("#0d0d0d" if i % 2 == 0 else "black")
        for widget in row.winfo_children():
            widget.config(bg=bg)

def highlight_selected_ability_row():
    global ability_row_frames, ability_selection_index
    if not ability_row_frames:
        return
    for i, row in enumerate(ability_row_frames):
        bg = "#880000" if i == ability_selection_index else ("#0d0d0d" if i % 2 == 0 else "black")
        for widget in row.winfo_children():
            widget.config(bg=bg)

def setup_moves_navigation():
    def on_moves_nav(event):
        global moves_selection_index
        if menu_selection_index != 1:  # Only work in MOSSE menu
            return
        if move_usage_active:  # Don't interfere with target selection
            return
        if not hasattr(player, 'moves') or not player.moves or len(player.moves) == 0:
            return
        
        old_index = moves_selection_index
        if event.keysym == "Down":
            moves_selection_index = (moves_selection_index + 1) % len(player.moves)
        elif event.keysym == "Up":
            moves_selection_index = (moves_selection_index - 1) % len(player.moves)
        elif event.keysym == "Return":  # ENTER key to use move
            highlight_selected_move_row()  # Highlight on ENTER
            use_selected_move()
            return
        
        # draw_moves_triangle_cursor()
        highlight_selected_move_row()  # Highlight on navigation

    root.bind("<Up>", on_moves_nav)
    root.bind("<Down>", on_moves_nav)
    root.bind("<Return>", on_moves_nav)

def setup_ability_navigation():
    def on_ability_nav(event):
        global ability_selection_index
        if menu_selection_index != 3:  # Only work in ABILITÀ menu
            return
        if not hasattr(player, 'ability') or not player.ability or len(player.ability) == 0:
            return
        
        old_index = ability_selection_index
        if event.keysym == "Down":
            ability_selection_index = (ability_selection_index + 1) % len(player.ability)
        elif event.keysym == "Up":
            ability_selection_index = (ability_selection_index - 1) % len(player.ability)
        elif event.keysym == "Return":  # ENTER key to see ability details
            show_ability_details()
            return
        
        highlight_selected_ability_row()  # Highlight on navigation

    root.bind("<Up>", on_ability_nav)
    root.bind("<Down>", on_ability_nav)
    root.bind("<Return>", on_ability_nav)

def draw_moves_triangle_cursor():
    """Draw the triangle cursor for move selection"""
    global moves_triangle_cursor, moves_selection_index
    
    # Force clear and destroy any existing cursor
    try:
        if moves_triangle_cursor is not None:
            moves_triangle_cursor.destroy()
    except:
        pass
    finally:
        moves_triangle_cursor = None
    
    # Force update display before creating new cursor
    root.update_idletasks()
    
    if hasattr(player, 'moves') and player.moves and len(player.moves) > 0:
        # Calculate cursor position with exact measurements
        triangle_size = 16
        row_height = 40
        current_index = moves_selection_index
        cursor_y = 215 + (current_index * row_height)  # Adjusted for instructions
        
        # Enhanced debug: Print all relevant values
        print(f"DEBUG ENHANCED: current_index = {current_index}, cursor_y = {cursor_y}, row_height = {row_height}")
        
        # X position - inside the table frame, left margin
        cursor_x = LEFT_PANEL_WIDTH + 60  # Table position + left margin inside table
        
        # Create new cursor with forced positioning
        moves_triangle_cursor = tk.Canvas(root, width=triangle_size, height=triangle_size, bg="black", highlightthickness=0)
        
        # Force immediate placement
        moves_triangle_cursor.place(x=cursor_x, y=cursor_y)
        print(f"DEBUG PLACEMENT: Cursor placed at x={cursor_x}, y={cursor_y}")
        
        # Triangle pointing right (corrected direction)
        moves_triangle_cursor.create_polygon(
            0, 0,
            0, triangle_size,
            triangle_size, triangle_size // 2,
            fill="white"
        )
        
        # Force immediate display update
        moves_triangle_cursor.update()

def show_moves_panel():
    global moves_table_frame, moves_selection_index, moves_triangle_cursor, move_row_frames, ability_row_frames

    # Force clear all variables and UI elements first
    print(f"SHOW_MOVES_PANEL: Starting cleanup, current moves_selection_index = {moves_selection_index}")
    
    # Remove previous moves frame if it exists
    try:
        if moves_table_frame is not None:
            moves_table_frame.destroy()
    except:
        pass
    finally:
        moves_table_frame = None
    
    # Remove previous triangle cursor if it exists  
    try:
        if moves_triangle_cursor is not None:
            moves_triangle_cursor.destroy()
    except:
        pass
    finally:
        moves_triangle_cursor = None
    
    # Clear move row frames when not in moves menu
    if menu_selection_index != 1:
        move_row_frames.clear()
    
    # Reset move selection when entering moves menu
    moves_selection_index = 0
    print(f"SHOW_MOVES_PANEL: Reset moves_selection_index to {moves_selection_index}")
    
    # Force display update before continuing
    root.update_idletasks()

    # Only show if "MOSSE" is selected (index 1)
    if menu_selection_index == 1:
        # Calculate available space for the moves table
        # Available width: from left panel to right edge, minus padding
        available_width = 1000  # Set a fixed width for the panel
        available_height = MENU_TOP_Y + 240 - 150  # 730 pixels

        center_x = (root.winfo_width() - available_width) // 2

        # Create main frame for the moves table
        moves_table_frame = tk.Frame(
            root,
            bg="black",
            highlightbackground="white",
            highlightthickness=1,
            width=available_width,
            height=available_height
        )
        moves_table_frame.place(x=center_x + 150, y=75)  # Centered horizontally
        moves_table_frame.propagate(False)
        
        # Title
        title_label = tk.Label(
            moves_table_frame,
            text=f"{player.name}'s Moves",
            fg="white",
            bg="black",
            font=("Times", 20, "bold")  # Reduced title font size
        )
        title_label.pack(pady=(10, 15))
        
        # Add instructions for move usage
        instructions_label = tk.Label(
            moves_table_frame,
            text="Usa ↑↓ per navigare, ENTER per usare la mossa",
            fg="white",
            bg="black",
            font=("Times", 14)
        )
        instructions_label.pack(pady=(0, 10))
        
        # Container for table and potential scrollbar
        table_container = tk.Frame(moves_table_frame, bg="black")
        table_container.pack(fill="both", expand=True, padx=50, pady=(0, 10))
        
        # Calculate if scrollbar is needed
        estimated_row_height = 35  # Reduced row height for smaller font
        header_height = 40  # Reduced header height
        content_height = available_height - 140  # Space for title, instructions and padding
        
        moves_count = len(player.moves) if hasattr(player, 'moves') and player.moves else 0
        total_content_height = header_height + (moves_count * estimated_row_height)
        needs_scrollbar = total_content_height > content_height
        
        # Adjust canvas width based on scrollbar need
        canvas_width = available_width - 40  # Base padding
        if needs_scrollbar:
            canvas_width -= 20  # Additional space for scrollbar
        
        # Create scrollable frame for the table
        canvas = tk.Canvas(table_container, bg="black", width=canvas_width, height=content_height, highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg="black")
        
        if needs_scrollbar:
            scrollbar = tk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Table headers with shorter names and more columns
        headers = ["NOME", "TYP", "DAN", "STM", "ACC", "FOR", "DES", "SPE", "EFF1", "EFF2", "EFF3", "EFF4", "REQ1", "REQ2", "REQ3", "REQ4", "EL1", "EL2"]
        # Adjusted column widths for all the new columns
        col_widths_pixels = [100, 40, 40, 40, 45, 40, 40, 40, 50, 50, 50, 50, 50, 50, 50, 50, 40, 40]
        
        # Header row with improved styling
        header_frame = tk.Frame(scrollable_frame, bg="black")
        header_frame.pack(fill="x", padx=5, pady=(3, 8))

        for i, (header, width_px) in enumerate(zip(headers, col_widths_pixels)):
            header_label = tk.Label(
                header_frame,
                text=header,
                fg="#FFD700",  # Gold color for headers
                bg="#1a1a1a",  # Slightly lighter background
                font=("Times", 11, "bold"),  # Smaller header font to fit more columns
                # width=width_px//7,  # Convert pixels to approximate character width
                height=2,  # Header height
                anchor="center",
                relief="raised",
                borderwidth=1
            )
            header_label.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
            
        # Configure column weights for proper spacing
        for i in range(len(headers)):
            header_frame.grid_columnconfigure(i, weight=1, minsize=col_widths_pixels[i])
      
        
        # Data rows with improved formatting
        if hasattr(player, 'moves') and player.moves:
            move_row_frames.clear()

            for row_idx, move in enumerate(player.moves):
                row_frame = tk.Frame(scrollable_frame, bg="black")
                row_frame.pack(fill="x", padx=5, pady=2)
                move_row_frames.append(row_frame)  # Store reference
                
                # Prepare individual effects, requirements, and elements
                effects = move.eff_appl if move.eff_appl else []
                requirements = move.reqs if move.reqs else []
                elements = move.elem if move.elem else []
                
                # Pad lists to ensure we have 4 effects, 4 requirements, and 2 elements
                effects_padded = (effects + ["-"] * 4)[:4]
                requirements_padded = (requirements + ["-"] * 4)[:4]
                elements_padded = (elements + ["-"] * 2)[:2]
                
                # Prepare data for each column
                move_data = [
                    move.name,                           # NOME
                    move.tipo,                          # TYP
                    str(move.danno),                    # DAN
                    str(move.stamina_cost),             # STM
                    f"{move.accuracy}%",                # ACC
                    f"{move.sca_for:.1f}",             # FOR
                    f"{move.sca_des:.1f}",             # DES
                    f"{move.sca_spe:.1f}",             # SPE
                    effects_padded[0],                  # EFF1
                    effects_padded[1],                  # EFF2
                    effects_padded[2],                  # EFF3
                    effects_padded[3],                  # EFF4
                    requirements_padded[0],             # REQ1
                    requirements_padded[1],             # REQ2
                    requirements_padded[2],             # REQ3
                    requirements_padded[3],             # REQ4
                    elements_padded[0],                 # EL1
                    elements_padded[1]                  # EL2
                ]
                
                # Create cells for each data column
                for col_idx, (data, width_px) in enumerate(zip(move_data, col_widths_pixels)):
                    # Enhanced color coding for different data types
                    if col_idx == 1:  # TYP
                        if data == "ATK":
                            color = "#FF6B6B"  # Red for attack
                        elif data == "BUF":
                            color = "#90EE90"  # Light green for buff
                        else:
                            color = "#87CEEB"  # Sky blue for reaction
                    elif col_idx in [2, 3]:  # DAN, STM
                        color = "#FFA500"  # Orange for damage/stamina
                    elif col_idx == 4:  # ACC
                        color = "#98FB98"  # Pale green for accuracy
                    elif col_idx in [5, 6, 7]:  # FOR, DES, SPE
                        color = "#DDA0DD"  # Plum for scaling
                    elif col_idx in [8, 9, 10, 11]:  # EFF1-4
                        color = "#00CED1" if data != "-" else "#333333"  # Dark turquoise for effects, dark gray for empty
                    elif col_idx in [12, 13, 14, 15]:  # REQ1-4
                        color = "#F0E68C" if data != "-" else "#333333"  # Khaki for requirements, dark gray for empty
                    elif col_idx in [16, 17]:  # EL1-2
                        color = "#FFA07A" if data != "-" else "#333333"  # Light salmon for elements, dark gray for empty
                    else:
                        color = "white"
                    
                    # Alternate row background for better readability
                    bg_color = "#0d0d0d" if row_idx % 2 == 0 else "black"
                    
                    cell_label = tk.Label(
                        row_frame,
                        text=data,
                        fg=color,
                        bg=bg_color,
                        font=("Times", 10),
                        height=2,
                        anchor="center",
                        relief="solid",
                        borderwidth=1,
                        wraplength=width_px-5
                    )
                    cell_label.grid(row=0, column=col_idx, padx=1, pady=1, sticky="ew")
                
                # Configure column weights for proper spacing
                for i in range(len(headers)):
                    row_frame.grid_columnconfigure(i, weight=1, minsize=col_widths_pixels[i])
        
        else:
            # No moves message
            no_moves_label = tk.Label(
                scrollable_frame,
                text="Nessuna mossa disponibile",
                fg="gray",
                bg="black",
                font=("Times", 18),  # Adjusted font for no moves message
                pady=40  # Padding
            )
            no_moves_label.pack()
        
        # Pack canvas and scrollbar only if needed
        canvas.pack(side="left", fill="both", expand=True)
        if needs_scrollbar:
            scrollbar.pack(side="right", fill="y")

        def highlight_selected_move_row_local():
            """Local highlight function for moves panel"""
            for i, row in enumerate(move_row_frames):
                bg = "#880000" if i == moves_selection_index else ("#0d0d0d" if i % 2 == 0 else "black")
                for widget in row.winfo_children():
                    widget.config(bg=bg)

        # Set up moves navigation
        setup_moves_navigation()

        # Highlight selected move row
        highlight_selected_move_row_local()

    elif menu_selection_index == 2:  # EFFETTI menu
        # Calculate available space for the effects table
        available_width = 1000  # Set a fixed width for the panel
        available_height = MENU_TOP_Y + 240 - 150  # 730 pixels

        center_x = (root.winfo_width() - available_width) // 2

        # Create main frame for the effects table
        moves_table_frame = tk.Frame(
            root,
            bg="black",
            highlightbackground="white",
            highlightthickness=1,
            width=available_width,
            height=available_height
        )
        moves_table_frame.place(x=center_x + 150, y=75)  # Centered horizontally
        moves_table_frame.propagate(False)
        
        # Title
        title_label = tk.Label(
            moves_table_frame,
            text=f"{player.name}'s Effects",
            fg="white",
            bg="black",
            font=("Times", 20, "bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Add instructions for effect details
        instructions_label = tk.Label(
            moves_table_frame,
            text="Usa ↑↓ per navigare, ENTER per dettagli effetti",
            fg="white",
            bg="black",
            font=("Times", 14)
        )
        instructions_label.pack(pady=(0, 10))

        # Effects content (placeholder for now)
        effects_content = tk.Label(
            moves_table_frame,
            text="Sistema effetti in sviluppo",
            fg="gray",
            bg="black",
            font=("Times", 16)
        )
        effects_content.pack(pady=50)

    elif menu_selection_index == 4:  # OGGETTI menu
        # Calculate available space for the items table
        available_width = 1000  # Set a fixed width for the panel
        available_height = MENU_TOP_Y + 240 - 150  # 730 pixels

        center_x = (root.winfo_width() - available_width) // 2

        # Create main frame for the items table
        moves_table_frame = tk.Frame(
            root,
            bg="black",
            highlightbackground="white",
            highlightthickness=1,
            width=available_width,
            height=available_height
        )
        moves_table_frame.place(x=center_x + 150, y=75)  # Centered horizontally
        moves_table_frame.propagate(False)
        
        # Title
        title_label = tk.Label(
            moves_table_frame,
            text=f"{player.name}'s Items",
            fg="white",
            bg="black",
            font=("Times", 20, "bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Add instructions for item usage
        instructions_label = tk.Label(
            moves_table_frame,
            text="Usa ↑↓ per navigare, ENTER per usare oggetto",
            fg="white",
            bg="black",
            font=("Times", 14)
        )
        instructions_label.pack(pady=(0, 10))

        # Items content (placeholder for now)
        items_content = tk.Label(
            moves_table_frame,
            text="Sistema oggetti in sviluppo",
            fg="gray",
            bg="black",
            font=("Times", 16)
        )
        items_content.pack(pady=50)

    # ABILITÀ menu is now handled by show_abilities_panel()

def show_passa_panel():
    """Show or hide the PASSA panel based on menu selection"""
    global passa_table_frame, passa_selection_index
    
    print(f"DEBUG: show_passa_panel called, menu_selection_index = {menu_selection_index}")
    
    # Remove previous passa frame if it exists
    if passa_table_frame is not None:
        try:
            passa_table_frame.destroy()
        except tk.TclError:
            pass  # Widget already destroyed
        passa_table_frame = None
    
    passa_selection_index = 0  # Reset selection when menu is shown (0=YES, 1=NO)

    # Only show if "PASSA" is selected (index 5)
    if menu_selection_index == 5:
        print("DEBUG: Creating passa panel...")
        
        available_width = 600  # Smaller width for simple menu
        available_height = 400  # Smaller height

        center_x = (root.winfo_width() - available_width) // 2

        # Create main frame for the passa menu
        passa_table_frame = tk.Frame(
            root,
            bg="black",
            highlightbackground="white",
            highlightthickness=1,
            width=available_width,
            height=available_height
        )
        passa_table_frame.place(x=center_x + 150, y=200)  # Centered
        passa_table_frame.propagate(False)
        
        # Title question
        title_label = tk.Label(
            passa_table_frame,
            text="Vuoi passare il turno?",
            fg="white",
            bg="black",
            font=("Times", 24, "bold")
        )
        title_label.pack(pady=(50, 50))
        
        # Container for YES/NO options
        options_frame = tk.Frame(passa_table_frame, bg="black")
        options_frame.pack(expand=True)
        
        # YES option
        yes_label = tk.Label(
            options_frame,
            text="SI",
            fg="white",
            bg="black",
            font=("Times", 20),
            pady=10
        )
        yes_label.pack(pady=10)
        
        # NO option
        no_label = tk.Label(
            options_frame,
            text="NO",
            fg="white",
            bg="black",
            font=("Times", 20),
            pady=10
        )
        no_label.pack(pady=10)
        
        def highlight_selected_passa_option():
            """Highlight the currently selected option"""
            if passa_selection_index == 0:  # YES selected
                yes_label.config(bg="#880000")
                no_label.config(bg="black")
            else:  # NO selected
                yes_label.config(bg="black")
                no_label.config(bg="#880000")
        
        # Highlight selected option
        highlight_selected_passa_option()

def setup_passa_navigation():
    """Set up navigation for the PASSA menu"""
    def on_passa_nav(event):
        global passa_selection_index, player_has_control
        if menu_selection_index != 5:  # Only work in PASSA menu (index 5)
            return
        if not player_has_control:  # Don't allow navigation during enemy turn
            return
        
        if event.keysym == "Down":
            passa_selection_index = (passa_selection_index + 1) % 2
        elif event.keysym == "Up":
            passa_selection_index = (passa_selection_index - 1) % 2
        elif event.keysym == "Return":  # ENTER key
            if passa_selection_index == 0:  # YES selected
                start_enemy_turn()
            # If NO selected, do nothing
            return
        
        # Update highlighting
        show_passa_panel()  # Refresh the panel to update highlighting

    root.bind("<Up>", on_passa_nav)
    root.bind("<Down>", on_passa_nav)
    root.bind("<Return>", on_passa_nav)

def start_enemy_turn():
    """Start the enemy turn sequence"""
    global enemy_turn_active, player_has_control, menu_selection_index
    
    # Restore player stamina to full at the end of their turn
    old_stamina = player.sta
    player.sta = player.max_sta
    stamina_restored = player.sta - old_stamina
    
    enemy_turn_active = True
    player_has_control = False
    
    # Display the enemy turn message
    show_message(f"È il turno di {enemy.name}", 2000)
    
    # Switch to NEMICO menu
    menu_selection_index = 0
    draw_triangle(menu_selection_index)
    
    # Clear current panels and show enemy panel
    show_enemy_panel()
    show_moves_panel()
    show_abilities_panel()
    show_passa_panel()
    
    # Start enemy turn after a short delay
    root.after(2500, execute_enemy_turn)

def execute_enemy_turn():
    """Execute the enemy's turn - perform random moves until out of stamina"""
    global enemy_turn_active, player_has_control
    
    import random
    
    if not enemy_turn_active:
        return
    
    # Check if enemy has any moves they can afford
    affordable_moves = []
    for i, move in enumerate(enemy.moves):
        if move.stamina_cost <= enemy.sta:
            affordable_moves.append((i, move))
    
    if not affordable_moves:
        # Enemy is out of stamina, end turn
        end_enemy_turn()
        return
    
    # Select a random affordable move
    move_index, selected_move = random.choice(affordable_moves)
    
    # Select a random player body part to target
    target_part_index = random.randint(0, len(player.body_parts) - 1)
    target_part = player.body_parts[target_part_index]
    
    # Execute the move
    perform_enemy_move(selected_move, target_part)
    
    # Schedule next move after a delay
    root.after(2000, execute_enemy_turn)

def perform_enemy_move(move, target_part):
    """Perform an enemy move on a player body part"""
    import random
    
    # Subtract stamina cost from enemy
    enemy.sta -= move.stamina_cost
    
    # Calculate accuracy roll
    accuracy_roll = random.randint(1, 100)
    
    if accuracy_roll > move.accuracy:
        # Move missed
        show_message(f"{enemy.name} ha mancato {move.name}!", 1500)
        return
    
    # Move hit - apply damage
    damage = move.danno
    target_part.p_pvt = max(0, target_part.p_pvt - damage)
    
    # Create multi-line message
    message = f"{enemy.name} ha usato {move.name}\nsu {target_part.name} di {player.name}\nDanno: {damage}"
    show_message(message, 1500)
    
    print(f"Enemy used {move.name} on {player.name}'s {target_part.name} for {damage} damage")

def end_enemy_turn():
    """End the enemy turn and give control back to the player"""
    global enemy_turn_active, player_has_control
    
    # Restore enemy stamina to full at the end of their turn
    old_stamina = enemy.sta
    enemy.sta = enemy.max_sta
    stamina_restored = enemy.sta - old_stamina
    
    enemy_turn_active = False
    player_has_control = True
    
    # Display player turn message with stamina info
    show_message(f"È il turno di {player.name}\n{enemy.name} stamina ripristinata: {enemy.sta}/{enemy.max_sta} (+{stamina_restored})", 2000)
    
    print("Enemy turn ended, control returned to player")

def move_selection(event):
    global menu_selection_index, player_has_control
    
    # Don't allow menu navigation during enemy turn
    if not player_has_control:
        return
        
    if event.keysym == "Right":
        menu_selection_index = (menu_selection_index + 1) % (len(menu_labels))
    elif event.keysym == "Left":
        menu_selection_index = (menu_selection_index - 1) % (len(menu_labels))
    draw_triangle(menu_selection_index)
    
    show_enemy_panel()  # Update enemy panel based on selection
    show_moves_panel()  # Update moves panel based on selection (handles MOSSE, EFFETTI, OGGETTI)
    show_abilities_panel()  # Update abilities panel based on selection (handles ABILITÀ)
    show_passa_panel()  # Update passa panel based on selection
    
    # Setup menu-specific navigation based on current selection AFTER panels are shown
    setup_menu_navigation()

def setup_menu_navigation():
    """Centralized navigation setup based on current menu selection"""
    # Clear any existing vertical navigation bindings
    root.unbind("<Up>")
    root.unbind("<Down>")
    root.unbind("<Return>")
    root.unbind("<Escape>")
    
    # Set up navigation based on current menu
    if menu_selection_index == 0:  # NEMICO menu
        setup_enemy_navigation()
    elif menu_selection_index == 1:  # MOSSE menu
        setup_moves_navigation()
    elif menu_selection_index == 3:  # ABILITÀ menu
        setup_ability_navigation()
    elif menu_selection_index == 5:  # PASSA menu
        setup_passa_navigation()
    # No special navigation needed for EFFETTI (2) and OGGETTI (4) yet

def setup_enemy_navigation():
    """Set up navigation for the enemy menu"""
    def on_enemy_parts_nav(event):
        global enemy_parts_index
        if menu_selection_index != 0:  # Only work in NEMICO menu
            return
        if event.keysym == "Down":
            enemy_parts_index = (enemy_parts_index + 1) % len(enemy.body_parts)
        elif event.keysym == "Up":
            enemy_parts_index = (enemy_parts_index - 1) % len(enemy.body_parts)
        # Update enemy display
        draw_enemy_parts_triangle()
        show_enemy_part_attributes()

    root.bind("<Up>", on_enemy_parts_nav)
    root.bind("<Down>", on_enemy_parts_nav)

def restore_stamina(character, amount):
    """
    Restore stamina to a character, ensuring it doesn't exceed the effective maximum.
    
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
    
    print(f"Restored {character.sta - old_stamina} stamina to {getattr(character, 'name', 'Unknown')}. Current: {character.sta}/{effective_max}")

def set_stamina(character, amount):
    """
    Set stamina to a specific amount, ensuring it doesn't exceed the effective maximum.
    
    Args:
        character: The character object
        amount (int): Amount to set stamina to
    """
    if not hasattr(character, 'sta'):
        print(f"Character {getattr(character, 'name', 'Unknown')} does not have stamina attribute")
        return
    
    # Get the effective maximum stamina
    effective_max = getattr(character, 'effective_max_sta', character.max_sta)
    
    old_stamina = character.sta
    character.sta = max(0, min(amount, effective_max))
    
    print(f"Set {getattr(character, 'name', 'Unknown')} stamina from {old_stamina} to {character.sta}/{effective_max}")

def debug_stamina_info():
    """Debug function to print current stamina information"""
    print("\n=== STAMINA DEBUG INFO ===")
    print(f"Player base max_sta: {player.max_sta}")
    print(f"Player buf_sta: {player.buf_sta}")
    print(f"Player current sta: {player.sta}")
    print(f"Player effective_max_sta: {getattr(player, 'effective_max_sta', 'Not set')}")
    print(f"Stamina scaling factor: {STAT_SCALING_FACTORS['sta']}")
    calculated_max = player.max_sta + (player.buf_sta * STAT_SCALING_FACTORS['sta'])
    print(f"Calculated max stamina: {calculated_max}")
    print("========================\n")

def on_closing():
    """Handle window closing event - clean up properly"""
    global enemy_image_frame, enemy_name_label, enemy_parts_frame, enemy_parts_triangle, enemy_part_attr_frame
    global moves_table_frame, moves_triangle_cursor, target_selection_frame, target_triangle_cursor, message_label
    
    print("DEBUG: Window closing - cleaning up...")
    
    # Clean up all global UI elements
    ui_elements = [
        enemy_image_frame, enemy_name_label, enemy_parts_frame, enemy_parts_triangle, enemy_part_attr_frame,
        moves_table_frame, moves_triangle_cursor, target_selection_frame, target_triangle_cursor, message_label
    ]
    
    for element in ui_elements:
        if element is not None:
            try:
                element.destroy()
            except (tk.TclError, AttributeError):
                pass  # Element already destroyed or doesn't exist
    
    # Destroy the root window
    try:
        root.quit()
        root.destroy()
    except tk.TclError:
        pass
    
    print("DEBUG: Window cleanup completed")

def on_debug_key(event):
    """Handle debug key presses"""
    if event.keysym == 'F1':
        debug_stamina_info()
    elif event.keysym == 'F2':
        # Reduce player stamina by 2 for testing
        player.sta = max(0, player.sta - 2)
        print(f"DEBUG: Manually reduced player stamina to {player.sta}")
    elif event.keysym == 'F3':
        # Restore player stamina by 2 for testing
        restore_stamina(player, 2)

# Set up proper window close handling
root.protocol("WM_DELETE_WINDOW", on_closing)

root.bind("<Left>", move_selection)
root.bind("<Right>", move_selection)

# Bind debug keys
root.bind("<F1>", on_debug_key)
root.bind("<F2>", on_debug_key)
root.bind("<F3>", on_debug_key)

# Show panels at startup if needed
show_enemy_panel()
show_moves_panel()
show_abilities_panel()
show_passa_panel()

# Set up initial navigation for the default menu (NEMICO)
setup_menu_navigation()

print("Starting GUI main loop...")
try:
    root.mainloop()
except KeyboardInterrupt:
    print("DEBUG: Interrupted by user")
    on_closing()
except Exception as e:
    print(f"DEBUG: Error in main loop: {e}")
    import traceback
    traceback.print_exc()
    on_closing()

print("GUI main loop ended.")
def recalculate_all_character_health():
    """
    Recalculate health for all characters based on their body parts.
    This function should be called when body part health changes.
    """
    player.calculate_health_from_body_parts()
    enemy.calculate_health_from_body_parts()