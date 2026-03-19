"""
Species Configuration System
===========================

This file defines the characteristics of different species in the game.
Each species has its own body parts distribution, HP ratios, and available effects/buffs.

Usage: Import this file and use get_species_config(species_name) to get configuration data.
"""

# Species configuration data
SPECIES_CONFIG = {
    "Maedo": {
        "body_parts": {
            "has_extra_limbs": True,
            "extra_limbs_name": "TENTACLES",
            "extra_limbs_count": 1
        },
        "hp_distribution": {
            # Electric species with tentacles - ratios out of 200
            "head": 30,      # 15% of total HP
            "body": 80,      # 40% of total HP (reduced from 100 to accommodate tentacles)
            "left_arm": 15,  # 7.5% of total HP
            "right_arm": 15, # 7.5% of total HP
            "left_leg": 20,  # 10% of total HP
            "right_leg": 20, # 10% of total HP
            "extra_limbs": 20 # 10% of total HP (tentacles)
        },
        "available_effects": {
            # Format: [effect_name, available, unlocked]
            # available: 1 if species can learn this effect, 0 if not
            # unlocked: 1 if available at start, 0 if needs to be unlocked
            "bleed": [0, 0],
            "burn": [0, 0],
            "poison": [0, 0],
            "stun": [1, 1],
            "confusion": [0, 0],
            "regeneration": [1, 1],
            "paralysis": [1, 1],  # Paralysis effect from electric-based abilities
            "fry_neurons": [1, 1]  # Fry Neurons effect from electric-based abilities
        },
        "available_buffs": {
            # Format: [buff_name, available, unlocked]
            "buf_forz": [1, 1],    # Strength buff
            "buf_des": [1, 1],     # Dexterity buff
            "buf_spe": [1, 1],     # Special buff
            "buf_vel": [1, 1],     # Velocity buff
            "buf_res": [0, 0],     # Resistance buff
            "buf_dodge": [1, 1],   # Dodge buff
            "buf_shield": [0, 0],  # Shield buff
            # Effect on Hit buffs - Maedo's electric-based abilities
            "burning_flesh": [1, 1] # Burn on contact (electric burn)
        },
        "available_properties": {
            # Format: [property_name, available, unlocked]
            # Property effects that modify move behavior during execution
            "ranged": [1, 0],      # Special interactions with future mechanics
            "unblockable": [1, 1], # Bypasses shields, enemy still loses stamina
            "undodgable": [0, 0],  # Bypasses dodge, enemy still loses stamina
            "lifesteal": [0, 0],   # Heals 50% of damage dealt
            "clean_cut": [0, 0],   # Double damage if ≥50% of body part HP
            "rhythm": [0, 0]       # +10% damage per consecutive rhythm move
        },
        "normal_element": "IMPACT",
        "special_element": "ELECTRIC",
        "starting_moves": [
            # Electric tentacle-based moves reflecting Maedo's nature
            {
                "name": "Zapping Tentacles", 
                "type": "ATK", 
                "scaling": {"forz": 0, "des": 1, "spe": 2}, 
                "effects": [["stun", 1, 1, 0]], 
                "requirements": ["NEEDS TENTACLES"], 
                "elements": ["ELECTRIC"], 
                "accuracy": 90
            },
            {
                "name": "Electrical Charge", 
                "type": "BUF", 
                "scaling": {"forz": 0, "des": 0, "spe": 0}, 
                "effects": [["buf_spe", 2, 2, 0]], 
                "requirements": [], 
                "elements": ["ELECTRIC"], 
                "accuracy": 90
            },
            {
                "name": "Punch", 
                "type": "ATK", 
                "scaling": {"forz": 2, "des": 1, "spe": 1}, 
                "effects": [], 
                "requirements": ["NEEDS ARM"], 
                "elements": ["IMPACT"], 
                "accuracy": 90
            }
        ]
    },
    
#----------------------------------------------------------------------------

    "Selkio": {
        "body_parts": {
            "has_extra_limbs": False,
            "extra_limbs_name": None,
            "extra_limbs_count": 0
        },
        "hp_distribution": {
            # Standard humanoid distribution - ratios out of 200
            "head": 30,      # 15% of total HP
            "body": 100,     # 50% of total HP (standard proportion)
            "left_arm": 15,  # 7.5% of total HP
            "right_arm": 15, # 7.5% of total HP
            "left_leg": 20,  # 10% of total HP
            "right_leg": 20  # 10% of total HP
            # No extra_limbs for standard humanoid
        },
        "available_effects": {
            "bleed": [1, 1],
            "regeneration": [1, 1],
            "amputate": [1, 1],  # Amputate effect from blade-based abilities
            "mess_up" : [1, 1]  # Mess Up effect from blade-based abilities
        },
        "available_buffs": {
            "buf_forz": [1, 1],    # Strength buff
            "buf_des": [1, 1],     # Dexterity buff
            "buf_spe": [1, 1],     # Special buff
            "buf_vel": [1, 1],     # Velocity buff
            "buf_res": [0, 0],     # Resistance buff
            "buf_dodge": [1, 1],   # Dodge buff
            "buf_shield": [0, 0],  # Shield buff
            # Effect on Hit buffs - Selkio's blade-based abilities
            "moving_blades": [1, 1] # Bleed on contact
        },
        "available_properties": {
            # Format: [property_name, available, unlocked]  
            # Selkio has ALL property effects unlocked for testing
            "ranged": [1, 0],      # Special interactions with future mechanics
            "unblockable": [0, 0], # Bypasses shields, enemy still loses stamina
            "undodgable": [0, 0],  # Bypasses dodge, enemy still loses stamina  
            "lifesteal": [0, 0],   # Heals 50% of damage dealt
            "clean_cut": [1, 1],   # Double damage if ≥50% of body part HP
            "rhythm": [1, 1]       # +10% damage per consecutive rhythm move
        },
        "normal_element": "IMPACT",
        "special_element": "CUT",
        "starting_moves": [
            # Rotating muscles skeletal moves reflecting Selkio's nature
            {
                "name": "Sawblade Hands", 
                "type": "ATK", 
                "scaling": {"forz": 0, "des": 1, "spe": 2}, 
                "effects": [["bleed", 1, 1, 0]], 
                "requirements": ["NEEDS 2 ARMS"], 
                "elements": ["CUT"], 
                "accuracy": 90
            },
            {
                "name": "Moving Muscles", 
                "type": "BUF", 
                "scaling": {"forz": 0, "des": 0, "spe": 0}, 
                "effects": [["regeneration", 1, 3, 0]], 
                "requirements": [], 
                "elements": ["CUT"], 
                "accuracy": 90
            },
            {
                "name": "Kick", 
                "type": "ATK", 
                "scaling": {"forz": 2, "des": 2, "spe": 0}, 
                "effects": [], 
                "requirements": ["NEEDS ARM"], 
                "elements": ["Impact"], 
                "accuracy": 90
            }
        ]
    },
    
#----------------------------------------------------------------------------

    "Minnago": {
        "body_parts": {
            "has_extra_limbs": False,
            "extra_limbs_name": None,
            "extra_limbs_count": 0
        },
        "hp_distribution": {
            # Standard humanoid distribution - ratios out of 200
            "head": 30,      # 15% of total HP
            "body": 100,     # 50% of total HP (standard proportion)
            "left_arm": 15,  # 7.5% of total HP
            "right_arm": 15, # 7.5% of total HP
            "left_leg": 20,  # 10% of total HP
            "right_leg": 20  # 10% of total HP
            # No extra_limbs for standard humanoid
        },
        "available_effects": {
            "poison": [1, 1],
            "custom_poison": [1, 1],  # Custom poison effect from poison-based abilities
            "paralysis": [1, 1],  # Paralysis effect from poison-based abilities
            "regeneration": [1, 1],
            "acid": [1, 1],  # Acid effect from poison-based abilities
            "toxin": [1, 1]  # Toxin effect from poison-based abilities
        },
        "available_buffs": {
            "buf_forz": [1, 1],    # Strength buff
            "buf_des": [1, 1],     # Dexterity buff
            "buf_spe": [1, 1],     # Special buff
            "buf_vel": [0, 0],     # Velocity buff
            "buf_res": [0, 0],     # Resistance buff
            "buf_dodge": [0, 0],   # Dodge buff
            "buf_shield": [0, 0],  # Shield buff
            # Effect on Hit buffs - Minnago's poison-based abilities

        },
        "available_properties": {
            # Format: [property_name, available, unlocked]  
            # Selkio has ALL property effects unlocked for testing
            "ranged": [1, 0],      # Special interactions with future mechanics
            "unblockable": [0, 0], # Bypasses shields, enemy still loses stamina
            "undodgable": [0, 0],  # Bypasses dodge, enemy still loses stamina  
            "lifesteal": [0, 0],   # Heals 50% of damage dealt
            "clean_cut": [0, 0],   # Double damage if ≥50% of body part HP
            "rhythm": [0, 0]       # +10% damage per consecutive rhythm move
        },
        "normal_element": "IMPACT",
        "special_element": "POISON",
        "starting_moves": [
            # Modified poison based moves reflecting Minnago's nature
            {
                "name": "Poisonous Claws", 
                "type": "ATK", 
                "scaling": {"forz": 1, "des": 0, "spe": 2}, 
                "effects": [["Poison", 1, 1, 0]], 
                "requirements": ["NEEDS 2 ARMS"], 
                "elements": ["POISON"], 
                "accuracy": 90
            },
            {
                "name": "Toxic Boost", 
                "type": "BUF", 
                "scaling": {"forz": 0, "des": 0, "spe": 0}, 
                "effects": [["buf_spe", 2, 2, 0]], 
                "requirements": [], 
                "elements": ["POISON"], 
                "accuracy": 90
            },
            {
                "name": "Acid Spit", 
                "type": "ATK", 
                "scaling": {"forz": 0, "des": 1, "spe": 1}, 
                "effects": [["Acid", 1, 1, 0]], 
                "requirements": [], 
                "elements": ["POISON"], 
                "accuracy": 90
            }
        ]
    },
    
#----------------------------------------------------------------------------

    "Sapifer": {
        "body_parts": {
            "has_extra_limbs": False,
            "extra_limbs_name": None,
            "extra_limbs_count": 0
        },
        "hp_distribution": {
            # Faun with bushes on top - ratios out of 200
            "head": 40,      # 12.5% of total HP 
            "body": 90,      # 45% of total HP 
            "left_arm": 15,  # 7.5% of total HP
            "right_arm": 15, # 7.5% of total HP
            "left_leg": 20,  # 10% of total HP 
            "right_leg": 20, # 10% of total HP
        },
        "available_effects": {
            "bleed": [0, 0],
            "burn": [0, 0],
            "poison": [1, 1],
            "stun": [0, 0],
            "confusion": [1, 1],
            "regeneration": [1, 1],
            "fine_dust": [1, 1],  # Fine Dust effect from spore abilities
            "sleep": [1, 1]  # Sleep effect from spore abilities
        },
        "available_buffs": {
            "buf_forz": [1, 1],    # Strength buff
            "buf_des": [1, 1],     # Dexterity buff
            "buf_spe": [1, 1],     # Special buff
            "buf_vel": [1, 1],     # Velocity buff
            "buf_res": [0, 0],     # Resistance buff
            "buf_dodge": [1, 1],   # Dodge buff
            "buf_shield": [0, 0],  # Shield buff
            # Effect on Hit buffs - Sapifer's spore-based abilities
            "poison_spores": [1, 1],    # Poison on contact
            "confusion_spores": [1, 1], # Stun on contact  
            "sleep_spores": [1, 1]      # Sleep on contact
        },
        "available_properties": {
            # Format: [property_name, available, unlocked]
            # Sapifer has nature-themed property effects
            "ranged": [1, 1],      # Spore clouds and nature attacks
            "unblockable": [0, 0], # Not available for plant-based species
            "undodgable": [1, 1],  # Spore clouds are hard to avoid
            "lifesteal": [1, 1],   # Plant parasitism and nutrient drain
            "clean_cut": [0, 0],   # Not available for nature-based species
            "rhythm": [0, 0]       # Not available for deliberate plant species
        },
        "normal_element": "CUT",
        "special_element": "SPORE",
        "starting_moves": [
            # Plant-based moves reflecting Sapifer's faun-like nature with bush growth abilities
            {
                "name": "Thorn Claw",
                "type": "ATK",
                "scaling": {"forz": 2, "des": 2, "spe": 0},
                "effects": [],
                "requirements": ["NEEDS ARM"],
                "elements": ["CUT"],
                "accuracy": 90
            },
            {
                "name": "Nutrient Boost",
                "type": "BUF",
                "scaling": {"forz": 0, "des": 0, "spe": 0},
                "effects": [["regeneration", 1, 3, 0]],
                "requirements": [],
                "elements": ["SPORE"],
                "accuracy": 90
            },
            {
                "name": "Spore Cloud",
                "type": "ATK",
                "scaling": {"forz": 0, "des": 0, "spe": 2},
                "effects": [["confusion", 1, 1, 0]],
                "requirements": ["NEEDS ARM"],
                "elements": ["SPORE"],
                "accuracy": 90
            }
        ]
    }
}

# CENTRAL species → inborn skill id mapping (skill ids defined in Skills_Config.INBORN_SKILLS)
SPECIES_INBORN_SKILLS = {
    "Selkio": ["bare_bones"],
    "Sapifer": ["fluffy_coverage"],
    "Maedo": ["insulating_membrane"],
    "Minnago": ["tough_skin"]
}

def get_species_inborn_skills(species_name: str):
    """Return list of inborn skill ids for a species."""
    return SPECIES_INBORN_SKILLS.get(species_name, [])

# =============================================================================
# SKILLS SECTION
# =============================================================================

# Add SKILLS section to each species configuration
for species_name in SPECIES_CONFIG.keys():
    SPECIES_CONFIG[species_name]["skills"] = {
        "inborn": [],      # Inborn skills (species-specific, always active)
        "unlockable": []   # Unlockable proficiency skills (to be implemented)
    }

# Define inborn skills for each species
SPECIES_CONFIG["Selkio"]["skills"]["inborn"] = ["bare_bones"]
SPECIES_CONFIG["Sapifer"]["skills"]["inborn"] = ["fluffy_coverage"] 
SPECIES_CONFIG["Maedo"]["skills"]["inborn"] = ["insulating_membrane"]
SPECIES_CONFIG["Minnago"]["skills"]["inborn"] = ["tough_skin"] 

# Unlockable skills will be added later as proficiency skills are implemented
# These will be skills learned through gameplay that provide additional abilities

def get_species_config(species_name):
    """
    Get configuration data for a specific species.
    
    Args:
        species_name (str): Name of the species (e.g., "Selkio", "Maedo", "Sapifer")
        
    Returns:
        dict: Configuration dictionary for the species, or None if not found
    """
    return SPECIES_CONFIG.get(species_name)

def get_hp_ratios(species_name):
    """
    Get HP distribution ratios for a species (out of 200).
    
    Args:
        species_name (str): Name of the species
        
    Returns:
        dict: Dictionary with HP ratios for each body part
    """
    config = get_species_config(species_name)
    if not config:
        # Fallback to Maedo (standard humanoid) if species not found
        config = get_species_config("Maedo")
    
    return config["hp_distribution"]

def get_hp_distribution(species_name, total_hp):
    """
    Calculate HP distribution for body parts based on species and total HP.
    Ensures the sum of all body parts exactly equals total_hp by allocating any 
    rounding remainders to the body part.
    
    Args:
        species_name (str): Name of the species
        total_hp (int): Total HP to distribute
        
    Returns:
        dict: Dictionary with max HP values for each body part
    """
    hp_ratios = get_hp_ratios(species_name)
    config = get_species_config(species_name)
    
    # Calculate HP for each part based on ratios (out of 200) using integer division
    distribution = {
        "max_head_hp": int(total_hp * hp_ratios["head"] / 200),
        "max_left_arm_hp": int(total_hp * hp_ratios["left_arm"] / 200),
        "max_right_arm_hp": int(total_hp * hp_ratios["right_arm"] / 200),
        "max_left_leg_hp": int(total_hp * hp_ratios["left_leg"] / 200),
        "max_right_leg_hp": int(total_hp * hp_ratios["right_leg"] / 200)
    }
    
    # Handle extra limbs if the species has them
    if config and config["body_parts"]["has_extra_limbs"] and "extra_limbs" in hp_ratios:
        distribution["max_extral_limbs_hp"] = int(total_hp * hp_ratios["extra_limbs"] / 200)
    else:
        distribution["max_extral_limbs_hp"] = 0
    
    # Calculate body HP initially
    body_hp = int(total_hp * hp_ratios["body"] / 200)
    
    # Calculate the sum of all parts except body
    other_parts_total = (
        distribution["max_head_hp"] + 
        distribution["max_left_arm_hp"] + 
        distribution["max_right_arm_hp"] + 
        distribution["max_left_leg_hp"] + 
        distribution["max_right_leg_hp"] + 
        distribution["max_extral_limbs_hp"]
    )
    
    # Allocate remaining HP to body to ensure exact total
    distribution["max_body_hp"] = total_hp - other_parts_total
    
    return distribution

def get_available_effects(species_name):
    """
    Get available effects for a species.
    
    Args:
        species_name (str): Name of the species
        
    Returns:
        dict: Dictionary of effects with [available, unlocked] status
    """
    config = get_species_config(species_name)
    if not config:
        # Fallback to Maedo if species not found
        config = get_species_config("Maedo")
    
    return config["available_effects"]

def get_available_buffs(species_name):
    """
    Get available buffs for a species.
    
    Args:
        species_name (str): Name of the species
        
    Returns:
        dict: Dictionary of buffs with [available, unlocked] status
    """
    config = get_species_config(species_name)
    if not config:
        # Fallback to Maedo if species not found
        config = get_species_config("Maedo")
    
    return config["available_buffs"]

def get_available_properties(species_name):
    """
    Get available property effects for a species.
    
    Args:
        species_name (str): Name of the species
        
    Returns:
        dict: Dictionary of properties with [available, unlocked] status
    """
    config = get_species_config(species_name)
    if not config:
        # Fallback to Maedo if species not found
        config = get_species_config("Maedo")
    
    return config.get("available_properties", {})

def get_body_parts_info(species_name):
    """
    Get body parts information for a species.
    
    Args:
        species_name (str): Name of the species
        
    Returns:
        dict: Body parts configuration
    """
    config = get_species_config(species_name)
    if not config:
        # Fallback to Maedo if species not found
        config = get_species_config("Maedo")
    
    return config["body_parts"]

def get_starting_moves(species_name):
    """
    Get starting moves for a species.
    
    Args:
        species_name (str): Name of the species
        
    Returns:
        list: List of starting moves for the species
    """
    config = get_species_config(species_name)
    if not config:
        # Fallback to Maedo if species not found
        config = get_species_config("Maedo")
    
    return config.get("starting_moves", [])

# Export available species list
AVAILABLE_SPECIES = list(SPECIES_CONFIG.keys())

def get_available_species():
    """
    Get list of all available species.
    
    Returns:
        list: List of species names
    """
    return AVAILABLE_SPECIES

# Validation function
def validate_species_config():
    """
    Validate that all species configurations are properly formatted.
    
    Returns:
        bool: True if all configurations are valid
    """
    required_keys = ["body_parts", "hp_distribution", "available_effects", "available_buffs"]
    required_body_keys = ["has_extra_limbs", "extra_limbs_name", "extra_limbs_count"]
    required_hp_keys = ["head", "body", "left_arm", "right_arm", "left_leg", "right_leg", "extra_limbs"]
    
    for species_name, config in SPECIES_CONFIG.items():
        # Check main structure
        for key in required_keys:
            if key not in config:
                print(f"Species {species_name} missing required key: {key}")
                return False
        
        # Check body parts structure
        for key in required_body_keys:
            if key not in config["body_parts"]:
                print(f"Species {species_name} missing body part key: {key}")
                return False
        
        # Check HP distribution structure
        for key in required_hp_keys:
            if key not in config["hp_distribution"]:
                print(f"Species {species_name} missing HP distribution key: {key}")
                return False
        
        # Check HP ratios sum to 200 (for species with extra limbs) or 200 minus extra limbs ratio
        hp_sum = sum(config["hp_distribution"].values())
        if config["body_parts"]["has_extra_limbs"]:
            if hp_sum != 200:
                print(f"Species {species_name} HP ratios sum to {hp_sum}, should be 200")
                return False
        else:
            if hp_sum != 200:  # Still should sum to 200, extra_limbs should be 0
                print(f"Species {species_name} HP ratios sum to {hp_sum}, should be 200")
                return False
    
    return True

if __name__ == "__main__":
    # Test the configuration
    print("Species Config Validation:")
    if validate_species_config():
        print("✓ All species configurations are valid")
    else:
        print("✗ Some species configurations have errors")
    
    # Test HP distribution calculation
    print("\nTesting HP distribution for total_hp = 100:")
    for species in AVAILABLE_SPECIES:
        print(f"\n{species}:")
        hp_dist = get_hp_distribution(species, 100)
        total_distributed = sum(hp_dist.values())
        print(f"  Total distributed: {total_distributed}/100")
        for part, hp in hp_dist.items():
            if hp > 0:
                print(f"  {part}: {hp}")