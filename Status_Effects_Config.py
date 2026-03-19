"""
Status Effects Configuration File
This file defines the behavior of all status effects including:
- Damage per turn for damaging effects
- Stat debuffs applied based on effect levels
- Stack requirements for debuff application
"""

# Status Effects Configuration Dictionary
STATUS_EFFECTS_CONFIG = {
    
    # DAMAGING EFFECTS WITH DEBUFFS
    'bleed': {
        'damage_per_turn': 5,           # Base damage per level per turn
        'debuff_stat': 'forz',          # Stat to debuff (strength)
        'stacks_per_debuff': 2,         # Every 2 levels = -1 strength
        'debuff_type': 'auto',          # Automatically applied based on levels
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Bleeding wounds that weaken strength'
    },
    
    'burn': {
        'damage_per_turn': 5,           # Base damage per level per turn  
        'debuff_stat': 'des',           # Stat to debuff (dexterity)
        'stacks_per_debuff': 2,         # Every 2 levels = -1 dexterity
        'debuff_type': 'auto',          # Automatically applied based on levels
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Burns that impair dexterity'
    },
    
    'poison': {
        'damage_per_turn': 5,           # Base damage per level per turn
        'debuff_stat': 'spe',           # Stat to debuff (special)  
        'stacks_per_debuff': 2,         # Every 2 levels = -1 special
        'debuff_type': 'auto',          # Automatically applied based on levels
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Poison that clouds the mind, reducing the special stat'
    },
    
    'toxin': {
        'damage_per_turn': 7,           # Base damage per level per turn
        'debuff_stat': 'spe',           # Stat to debuff (special)  
        'stacks_per_debuff': 2,         # Every 2 levels = -1 special
        'debuff_type': 'auto',          # Automatically applied based on levels
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Toxins that cloud the mind, reducing the special stat'
    },

    'acid': {
        'damage_per_turn': 2,           # Base damage per level per turn
        'debuff_stat': 'forz',           # Stat to debuff (strength)
        'stacks_per_debuff': 2,         # Every 2 levels = -1 strength
        'debuff_type': 'auto',          # Automatically applied based on levels
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Corrosive acid that cannot be healed during battle and reduces strength',
        'healed_on_regen': False,       # Not healed by regeneration
        'reduces_over_time': False,     # Duration never depletes naturally
    },
    
    'frost': {
        'damage_per_turn': 2,           # Base damage per level per turn
        'debuff_stat': 'vel',           # Stat to debuff (velocity)
        'stacks_per_debuff': 1,         # Every 1 level = -1 velocity
        'debuff_type': 'auto',          # Automatically applied based on levels  
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Freezing cold that slows movement'
    },
    
    # NON-DAMAGING EFFECTS
    'stun': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No automatic debuff
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs applied
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect (higher cost)
        'description': 'Stunning effect that reduces stamina'
    },
    
    'sleep': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No automatic debuff  
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs applied
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect
        'special_mechanic': True,       # Has special sleep mechanics
        'always_target_head': True,     # Sleep effects always target the head
        'sleep_threshold_divisor': 10,  # Sleep triggers when level >= max_hp / 10
        'wake_up_chance': 0.75,         # 75% chance to wake up after sleeping 1 turn
        'stay_asleep_chance': 0.25,     # 25% chance to stay asleep
        'healed_on_regen': False,       # Not healed by regeneration
        'reduces_over_time': False,     # Duration never depletes naturally
        'show_duration': False,         # Never show duration in UI
        'description': 'Sleep effect that causes unconsciousness when accumulated'
    },
    
    'confusion': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': 'des',           # Debuff dexterity
        'stacks_per_debuff': 2,         # Every 2 levels = -1 dexterity
        'debuff_type': 'auto',          # Automatically applied
        'turn_timing': 'end_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'accuracy_modifier': True,      # Affects accuracy calculation
        'accuracy_base': 1.0,           # Base accuracy multiplier
        'accuracy_reduction': 0.1,      # Accuracy reduction per level (0.1 = 10% per level)
        'description': 'Mental confusion that impairs precision and accuracy'
    },
    
    'weakness': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': 'forz',          # Debuff strength
        'stacks_per_debuff': 1,         # Every 1 level = -1 strength
        'debuff_type': 'auto',          # Automatically applied
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Physical weakness that reduces power'
    },
    
    # BENEFICIAL EFFECTS (for completeness)
    'heal': {
        'damage_per_turn': -5,          # Negative = healing
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Regenerative healing over time'
    },
    
    'regeneration': {
        'damage_per_turn': -3,          # Negative = healing
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A  
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect
        'description': 'Slow regeneration of health'
    },
    
    # NEW NORMAL EFFECTS
    'amputate': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 4,                      # Stamina cost for moves with this effect
        'healed_on_regen': False,       # Not healed by regeneration
        'reduces_over_time': True,      # Duration depletes naturally
        'show_duration': True,          # Show duration in UI
        'description': 'Prevents body part regeneration for 1 turn'
    },
    
    'mess_up': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect
        'healed_on_regen': False,       # Not healed by regeneration - instead reduced by 1 level
        'reduces_over_time': False,     # Duration never depletes naturally
        'show_duration': False,         # Never show duration in UI
        'special_mechanic': True,       # Has special heal prevention mechanics
        'description': 'When healed, reduces level by 1 instead of healing'
    },
    
    'paralysis': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs (but affects requirements)
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 3,                      # Stamina cost for moves with this effect
        'healed_on_regen': False,       # Not healed by regeneration
        'reduces_over_time': True,      # Duration depletes naturally
        'show_duration': True,          # Show duration in UI
        'special_mechanic': True,       # Has special requirement blocking mechanics
        'description': 'Makes body part unusable for move requirements if used on limbs, disables random limb if used on body or head. Depletes naturally, but cannot be healed by regeneration'
    },
    
    'fry_neurons': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # Process at start of turn to disable skills
        'cost': 3,                      # Stamina cost for moves with this effect
        'always_target_head': True,     # Always targets the head
        'healed_on_regen': True,        # Can be healed by regeneration
        'reduces_over_time': False,      # Duration depletes naturally
        'show_duration': False,          # Show duration in UI
        'special_mechanic': True,       # Has special skill disabling mechanics
        'description': 'Disables random skills equal to effect level at turn start. Does not deplete naturally, must be healed.'
    },
    
    'fine_dust': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 3,                      # Stamina cost for moves with this effect
        'always_target_body': True,     # Always targets the body
        'healed_on_regen': False,       # Not healed by regeneration
        'reduces_over_time': True,      # Duration depletes naturally
        'show_duration': True,          # Show duration in UI
        'special_mechanic': True,       # Has special fire/electric move blocking mechanics
        'description': 'Blocks FIRE/ELECTRIC moves and deals self-damage to used body parts'
    },
    
    'custom_poison': {
        'damage_per_turn': 0,           # Custom damage calculation (special / 2 per level)
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'end_turn',      # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect
        'healed_on_regen': True,        # Can be healed by regeneration
        'reduces_over_time': True,      # Duration depletes naturally
        'show_duration': True,          # Show duration in UI
        'special_mechanic': True,       # Has custom damage calculation
        'description': 'Deals damage equal to caster special / 2 per level each turn'
    },
    
    # BUFF EFFECTS
    'buf_rig': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'Buff-1.mp3',  # Custom sound for this buff
        'description': 'Increases regeneration stat'
    },
    
    'buf_res': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'Buff-1.mp3',  # Custom sound for this buff
        'description': 'Increases resistance stat'
    },
    
    'buf_sta': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'Buff-1.mp3',  # Custom sound for this buff
        'description': 'Increases stamina stat'
    },
    
    'buf_forz': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'Buff-1.mp3',  # Custom sound for this buff
        'description': 'Increases strength stat'
    },
    
    'buf_des': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'Buff-1.mp3',  # Custom sound for this buff
        'description': 'Increases dexterity stat'
    },
    
    'buf_spe': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'Buff-1.mp3',  # Custom sound for this buff
        'description': 'Increases special stat'
    },
    
    'buf_vel': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 2,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'mixkit-quick-knife-slice-cutting-2152.mp3',  # Custom sound for this buff
        'description': 'Increases speed stat'
    },
    
    'buf_dodge': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'Buff-1.mp3',  # Custom sound for this buff
        'description': 'Allows dodging attacks with legs'
    },
    
    'buf_shield': {
        'damage_per_turn': 0,           # No damage
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # When to process: 'start_turn' or 'end_turn'
        'cost': 1,                      # Stamina cost for moves with this effect (higher cost)
        'played_sound': 'mixkit-sword-strikes-armor-2765.wav',  # Custom sound for this buff
        'description': 'Allows blocking attacks with an arm'
    },
    
    # PROPERTY EFFECTS - Instant effects that modify move behavior during execution
    'ranged': {
        'damage_per_turn': 0,           # No damage over time
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'instant',       # Instant effect, no turn processing
        'cost': 2,                      # Stamina cost for moves with this property
        'property': 'ranged',           # Property name for move behavior
        'description': 'Moves can hit from a distance, unaffected by on-Hit effects'
    },
    
    'unblockable': {
        'damage_per_turn': 0,           # No damage over time
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'instant',       # Instant effect, no turn processing
        'cost': 2,                      # Stamina cost for moves with this property
        'property': 'unblockable',      # Property name for move behavior
        'description': 'Moves hit even if enemy has shield, enemy still loses stamina for blocking'
    },
    
    'undodgable': {
        'damage_per_turn': 0,           # No damage over time
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'instant',       # Instant effect, no turn processing
        'cost': 2,                      # Stamina cost for moves with this property
        'property': 'undodgable',       # Property name for move behavior
        'description': 'Moves hit even if enemy tries to dodge, enemy still loses stamina for dodging'
    },
    
    'lifesteal': {
        'damage_per_turn': 0,           # No damage over time
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'instant',       # Instant effect, no turn processing
        'cost': 3,                      # Stamina cost for moves with this property
        'property': 'lifesteal',        # Property name for move behavior
        'heal_percentage': 50,          # Percentage of damage dealt that heals the attacker
        'description': 'Upon hit, heals 50% of damage dealt to enemy (rounded down)'
    },
    
    'clean_cut': {
        'damage_per_turn': 0,           # No damage over time
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'instant',       # Instant effect, no turn processing
        'cost': 4,                      # Stamina cost for moves with this property
        'property': 'clean_cut',        # Property name for move behavior
        'damage_threshold': 50,         # Percentage of total HP needed to trigger (50%)
        'description': 'If move deals ≥50% of body part total HP, deals double damage instead (sets HP to 0)'
    },
    
    'rhythm': {
        'damage_per_turn': 0,           # No damage over time
        'debuff_stat': None,            # No debuffs
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'instant',       # Instant effect, no turn processing
        'cost': 3,                      # Stamina cost for moves with this property
        'property': 'rhythm',           # Property name for move behavior
        'damage_bonus_per_stack': 10,   # Percentage damage bonus per consecutive rhythm move
        'description': 'Deals 10% more damage (rounded down) for each consecutive rhythm move used that turn'
    },
    
    # EFFECT ON HIT BUFFS
    # These are special buffs that trigger status effects when the user hits or is hit by non-ranged moves
    
    'poison_spores': {
        'damage_per_turn': 0,           # No damage over time (this is a buff, not a damaging effect)
        'debuff_stat': None,            # No debuffs from the buff itself
        'stacks_per_debuff': None,      # N/A
        'debuff_type': 'none',          # No debuffs
        'turn_timing': 'start_turn',    # Process at start of turn for upkeep cost
        'cost': 3,                      # Stamina cost to activate the buff
        'buff_type': 'effect_on_hit',   # Special buff type
        'upkeep_cost': 3,               # Stamina cost per turn to maintain
        'upkeep_type': 'stamina',       # Cost type: 'stamina' or 'reserve'
        'trigger_effect': 'poison',     # Effect applied on contact
        'trigger_level': 1,             # Level of effect applied
        'trigger_body_part': 'random',    # Body part targeted (head/body/random)
        'contact_type': 'hit_by',       # Triggers on: 'hit' (when hitting), 'hit_by' (when being hit), 'both'
        'description': 'When being hit by non-ranged moves, inflicts poison level 1 to a random body part'
    },
    
    'confusion_spores': {
        'damage_per_turn': 0,           
        'debuff_stat': None,            
        'stacks_per_debuff': None,      
        'debuff_type': 'none',          
        'turn_timing': 'start_turn',    
        'cost': 2,                      # Stamina cost to activate
        'buff_type': 'effect_on_hit',   
        'upkeep_cost': 2,               # Stamina cost per turn to maintain
        'upkeep_type': 'stamina',       
        'trigger_effect': 'stun',       # Inflicts stun instead of confusion (since confusion might not be implemented)
        'trigger_level': 1,             
        'trigger_body_part': 'head',    
        'contact_type': 'hit_by',       
        'description': 'When being hit by non-ranged moves, inflicts stun level 1 to enemy head'
    },
    
    'sleep_spores': {
        'damage_per_turn': 0,           
        'debuff_stat': None,            
        'stacks_per_debuff': None,      
        'debuff_type': 'none',          
        'turn_timing': 'start_turn',    
        'cost': 4,                      # Stamina cost to activate
        'buff_type': 'effect_on_hit',   
        'upkeep_cost': 4,               # Stamina cost per turn to maintain
        'upkeep_type': 'stamina',       
        'trigger_effect': 'sleep',      # Sleep effect (needs to be implemented in status effects)
        'trigger_level': 1,             
        'trigger_body_part': 'head',    
        'contact_type': 'hit_by',       
        'description': 'When being hit by non-ranged moves, inflicts sleep level 1 to enemy head'
    },
    
    'burning_flesh': {
        'damage_per_turn': 0,           
        'debuff_stat': None,            
        'stacks_per_debuff': None,      
        'debuff_type': 'none',          
        'turn_timing': 'start_turn',    
        'cost': 2,                      # Stamina cost to activate
        'buff_type': 'effect_on_hit',   
        'upkeep_cost': 10,              # Reserve cost per turn to maintain
        'upkeep_type': 'reserve',       # Uses reserve instead of stamina
        'trigger_effect': 'burn',       
        'trigger_level': 1,             
        'trigger_body_part': 'body',    # Always targets body
        'contact_type': 'hit_by',       
        'description': 'When being hit by non-ranged moves, inflicts burn level 1 to enemy body'
    },
    
    'moving_blades': {
        'damage_per_turn': 0,           
        'debuff_stat': None,            
        'stacks_per_debuff': None,      
        'debuff_type': 'none',          
        'turn_timing': 'start_turn',    
        'cost': 3,                      # Stamina cost to activate
        'buff_type': 'effect_on_hit',   
        'upkeep_cost': 3,               # Stamina cost per turn to maintain
        'upkeep_type': 'stamina',       
        'trigger_effect': 'bleed',      
        'trigger_level': 1,             
        'trigger_body_part': 'random',  # Random body part
        'contact_type': 'hit_by',       
        'description': 'When being hit by non-ranged moves, inflicts bleed level 1 to random enemy body part'
    }
}


def get_effect_config(effect_name):
    """
    Get configuration for a specific status effect with default values.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        dict: Configuration dictionary for the effect with defaults, or None if not found
    """
    effect_name = effect_name.lower().strip()
    config = STATUS_EFFECTS_CONFIG.get(effect_name)
    if not config:
        return None
    
    # Add default values for new attributes if not specified
    defaults = {
        'healed_on_regen': True,       # Most effects are healed by regeneration
        'reduces_over_time': True,     # Most effects reduce duration over time
        'show_duration': True,         # Most effects show duration in UI
        'special_mechanic': False,     # Most effects don't have special mechanics
        'always_target_head': False    # Most effects don't force head targeting
    }
    
    # Merge defaults with actual config
    result = defaults.copy()
    result.update(config)
    return result


def calculate_debuff_level(effect_name, total_effect_levels):
    """
    Calculate how much debuff should be applied based on total effect levels.
    
    Args:
        effect_name (str): Name of the effect
        total_effect_levels (int): Total accumulated levels of the effect
        
    Returns:
        int: Debuff level to apply (0 if no debuff should be applied)
    """
    config = get_effect_config(effect_name)
    if not config or config['debuff_type'] != 'auto' or not config['stacks_per_debuff']:
        return 0
    
    return total_effect_levels // config['stacks_per_debuff']


def get_damage_per_turn(effect_name, effect_level):
    """
    Calculate damage per turn for an effect.
    
    Args:
        effect_name (str): Name of the effect
        effect_level (int): Level of the effect
        
    Returns:
        int: Damage per turn (negative for healing effects)
    """
    config = get_effect_config(effect_name)
    if not config:
        return 0
    
    return config['damage_per_turn'] * effect_level


def get_all_debuff_effects():
    """
    Get list of all effects that apply automatic debuffs.
    
    Returns:
        list: Names of effects that apply automatic debuffs
    """
    return [name for name, config in STATUS_EFFECTS_CONFIG.items() 
            if config['debuff_type'] == 'auto']


def get_effects_by_debuff_stat(stat_name):
    """
    Get all effects that debuff a specific stat.
    
    Args:
        stat_name (str): Name of the stat ('forz', 'des', 'spe', etc.)
        
    Returns:
        list: Names of effects that debuff the specified stat
    """
    return [name for name, config in STATUS_EFFECTS_CONFIG.items()
            if config.get('debuff_stat') == stat_name.lower()]


def get_effect_cost(effect_name):
    """
    Get the stamina cost for a specific effect.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        int: Stamina cost for the effect (1 if not found)
    """
    config = get_effect_config(effect_name)
    if config and 'cost' in config:
        return config['cost']
    return 1  # Default cost if effect not found or cost not specified


def is_property_effect(effect_name):
    """
    Check if an effect is a property effect (instant, no lasting status).
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        bool: True if it's a property effect
    """
    config = get_effect_config(effect_name)
    return config and config.get('turn_timing') == 'instant'


def get_property_effects():
    """
    Get list of all property effects.
    
    Returns:
        list: Names of all property effects
    """
    return [name for name, config in STATUS_EFFECTS_CONFIG.items()
            if config.get('turn_timing') == 'instant']


def get_property_config(property_name):
    """
    Get configuration for a specific property effect.
    
    Args:
        property_name (str): Name of the property (case insensitive)
        
    Returns:
        dict: Configuration dictionary for the property, or None if not found
    """
    return get_effect_config(property_name) if is_property_effect(property_name) else None


def get_confusion_accuracy_modifier(character):
    """
    Calculate accuracy modifier based on character's confusion level.
    Base = 1.0, decreases by 0.1 per confusion level.
    
    Args:
        character: Character object with body_parts containing effects
        
    Returns:
        float: Accuracy multiplier (1.0 = no penalty, 0.7 = 30% accuracy reduction)
    """
    # Get confusion config
    confusion_config = get_effect_config('confusion')
    if not confusion_config or not confusion_config.get('accuracy_modifier', False):
        return 1.0  # No confusion accuracy system
    
    # Find highest confusion level across all body parts
    max_confusion_level = 0
    for part in character.body_parts:
        if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'confusion'):
            confusion_data = part.p_eff.confusion
            # FIXED: Check if duration > 0 to ensure effect is active
            if len(confusion_data) >= 3 and confusion_data[2] > 0:  # Check if duration > 0 (active)
                confusion_level = confusion_data[1]  # [name, level, duration, immunity]
                max_confusion_level = max(max_confusion_level, confusion_level)
    
    # Calculate modifier: base - (level * reduction_per_level)
    base = confusion_config.get('accuracy_base', 1.0)
    reduction_per_level = confusion_config.get('accuracy_reduction', 0.1)
    modifier = base - (max_confusion_level * reduction_per_level)
    
    # Ensure modifier doesn't go below 0.1 (10% minimum accuracy)
    modifier = max(modifier, 0.1)
    
    return modifier


def get_effects_by_timing(timing):
    """
    Get all effects that should be processed at a specific timing.
    
    Args:
        timing (str): 'start_turn' or 'end_turn'
        
    Returns:
        list: Names of effects that should be processed at the specified timing
    """
    return [name for name, config in STATUS_EFFECTS_CONFIG.items()
            if config.get('turn_timing') == timing]


def get_effect_timing(effect_name):
    """
    Get the turn timing for a specific effect.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        str: 'start_turn', 'end_turn', or 'end_turn' (default)
    """
    config = get_effect_config(effect_name)
    if config and 'turn_timing' in config:
        return config['turn_timing']
    return 'end_turn'  # Default to end_turn if not specified


def should_process_at_turn_start(effect_name):
    """
    Check if an effect should be processed at turn start.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        bool: True if effect should be processed at turn start
    """
    return get_effect_timing(effect_name) == 'start_turn'


def should_process_at_turn_end(effect_name):
    """
    Check if an effect should be processed at turn end.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        bool: True if effect should be processed at turn end
    """
    return get_effect_timing(effect_name) == 'end_turn'


def check_sleep_threshold(character):
    """
    Check if a character should fall asleep based on sleep level vs body HP.
    
    Args:
        character: Character object to check
        
    Returns:
        bool: True if character should fall asleep
    """
    # Find head part and get sleep level
    head_part = None
    for part in character.body_parts:
        if "HEAD" in part.name.upper():
            head_part = part
            break
    
    if not head_part or not hasattr(head_part, 'p_eff') or not hasattr(head_part.p_eff, 'sleep'):
        return False
    
    sleep_data = head_part.p_eff.sleep
    if len(sleep_data) < 2:
        return False
    
    sleep_level = sleep_data[1]
    if sleep_level <= 0:
        return False
    
    # Calculate sleep threshold: max body HP / 10
    body_part = None
    for part in character.body_parts:
        if "BODY" in part.name.upper():
            body_part = part
            break
    
    if not body_part:
        return False
    
    sleep_config = get_effect_config('sleep')
    threshold_divisor = sleep_config.get('sleep_threshold_divisor', 10)
    sleep_threshold = body_part.max_p_pvt / threshold_divisor
    
    return sleep_level >= sleep_threshold


def process_sleep_wake_up(character):
    """
    Process wake up chances for a sleeping character.
    
    Args:
        character: Character object to process
        
    Returns:
        bool: True if character woke up, False if still sleeping
    """
    import random
    
    sleep_config = get_effect_config('sleep')
    wake_up_chance = sleep_config.get('wake_up_chance', 0.75)
    
    if random.random() < wake_up_chance:
        # Wake up - remove all sleep tokens from head
        head_part = None
        for part in character.body_parts:
            if "HEAD" in part.name.upper():
                head_part = part
                break
        
        if head_part and hasattr(head_part, 'p_eff') and hasattr(head_part.p_eff, 'sleep'):
            head_part.p_eff.sleep = ["sleep", 0, 0, 0]  # Reset sleep effect
        
        return True  # Woke up
    else:
        return False  # Still sleeping


def should_effect_reduce_over_time(effect_name):
    """
    Check if an effect should reduce its duration over time.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        bool: True if effect should reduce over time
    """
    config = get_effect_config(effect_name)
    return config.get('reduces_over_time', True) if config else True


def should_effect_heal_on_regen(effect_name):
    """
    Check if an effect should be healed during regeneration.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        bool: True if effect should be healed on regeneration
    """
    config = get_effect_config(effect_name)
    return config.get('healed_on_regen', True) if config else True


def should_show_effect_duration(effect_name):
    """
    Check if an effect's duration should be shown in UI.
    Effects with reduces_over_time=False show '---' instead of their actual duration.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        bool: True if duration should be shown as a number, False if it should show '---'
    """
    return should_effect_reduce_over_time(effect_name)


def should_always_target_head(effect_name):
    """
    Check if an effect should always target the head regardless of hit location.
    
    Args:
        effect_name (str): Name of the effect (case insensitive)
        
    Returns:
        bool: True if effect should always target head
    """
    config = get_effect_config(effect_name)
    return config.get('always_target_head', False) if config else False


# Example usage and testing functions
if __name__ == "__main__":
    print("Status Effects Configuration Loaded")
    print("=====================================")
    
    # Test examples
    print(f"Bleed with 5 levels: {calculate_debuff_level('bleed', 5)} strength debuff")
    print(f"Burn with 3 levels: {calculate_debuff_level('burn', 3)} dexterity debuff") 
    print(f"Poison with 6 levels: {calculate_debuff_level('poison', 6)} special debuff")
    
    print(f"\nBleed level 2 damage per turn: {get_damage_per_turn('bleed', 2)}")
    print(f"Burn level 3 damage per turn: {get_damage_per_turn('burn', 3)}")
    
    print(f"\nEffects that apply automatic debuffs: {get_all_debuff_effects()}")
    print(f"Effects that debuff strength: {get_effects_by_debuff_stat('forz')}")
    
    print(f"\nTurn timing examples:")
    print(f"Start turn effects: {get_effects_by_timing('start_turn')}")
    print(f"End turn effects: {get_effects_by_timing('end_turn')}")
    print(f"Stun timing: {get_effect_timing('stun')}")
    print(f"Burn timing: {get_effect_timing('burn')}")
    print(f"Should process stun at turn start: {should_process_at_turn_start('stun')}")
    print(f"Should process burn at turn end: {should_process_at_turn_end('burn')}")
    
    print(f"\nEffect costs:")
    print(f"Bleed cost: {get_effect_cost('bleed')}")
    print(f"Stun cost: {get_effect_cost('stun')}")
    print(f"buf_forz cost: {get_effect_cost('buf_forz')}")
    print(f"buf_dodge cost: {get_effect_cost('buf_dodge')}")
    print(f"Unknown effect cost: {get_effect_cost('unknown_effect')}")