# Skills Configuration File
# This file defines all skills in the game, divided into Normal Skills and Memory Skills

# =============================================================================
# NORMAL SKILLS
# These skills are passive or active abilities that do NOT require ability points
# and are ALWAYS active once obtained
# =============================================================================

# --- FLATTENED INBORN SKILL DEFINITIONS (no species keys here) ---
INBORN_SKILLS = {
    "bare_bones": {
        "name": "Bare Bones",
        "short_description": "Skeletal protection against cuts",
        "long_description": "Skeletal structure provides natural protection against cutting attacks but is vulnerable to precise strikes. The exposed bone structure acts as natural armor against slashing weapons, but joints and connection points remain weak to piercing attacks.",
        "description": "Skeletal structure provides natural protection against cutting attacks but is vulnerable to precise strikes.",
        "type": "passive",
        "effects": {
            "resistances": {"CUT": 0.75},
            "weaknesses": {"PIERCE": 1.25}
        },
        "always_active": True
    },
    "fluffy_coverage": {
        "name": "Fluffy Coverage",
        "short_description": "Dense fur provides protection",
        "long_description": "Dense fur cushions blunt impacts and filters spores but is highly flammable and retains cold; its vegetal/fur mass becomes a liability against fire and freezing attacks.",
        "description": "Dense fur protects vs impact & spores, weak to fire & cold.",
        "type": "passive",
        "effects": {
            "resistances": {"IMPACT": 0.75, "SPORES": 0.75},
            "weaknesses": {"FIRE": 1.25, "COLD": 1.25}
        },
        "always_active": True
    },
    "insulating_membrane": {
        "name": "Insulating Membrane",
        "short_description": "Membrane protects from elements",
        "long_description": "Specialized insulating membrane nullifies electricity and dampens temperature extremes, but its soft tissue is vulnerable to cutting force.",
        "description": "Insulation vs electric/temperature, weak to cutting.",
        "type": "passive",
        "effects": {
            "immunities": ["ELECTRIC"],
            "resistances": {"HOT": 0.75, "COLD": 0.75},
            "weaknesses": {"CUT": 1.25}
        },
        "always_active": True
    },

    "snake_hide": {
        "name": "Snake Hide",
        "short_description": "Natural resistance to poison and cuts, weakness to elements",
        "long_description": "Thick, leathery skin provides natural resistance to poisons and cutting attacks. However, the presence of sacs full of toxins and other liquids underneath their skin generates a vulnerability to elemental attacks such as fire, cold and electricity.",
        "description": "Thick skin provides natural resistance to poisons and cuts, weakness to elements.",
        "type": "passive",
        "effects": {
            "resistances": {"POISON": 0.75, "CUT": 0.75},
            "weaknesses": {"FIRE": 1.25, "COLD": 1.25, "ELECTRIC": 1.25, "HOT": 1.25}
        },
        "always_active": True
    }
}

# Proficiency Skills - Learned through gameplay, unlock additional features
PROFICIENCY_SKILLS = {
    "Special_Proficiency": {
        "name": "Special Proficiency",
        "short_description": "Allows the use of Moves that have only special scaling",
        "long_description": "Allows the use of Moves that have only special scaling (no required physical scaling on strength or dexterity).",
        "type": "proficiency",
        "level": 1,
        "effects": {
            "Special_proficiency": 1  # 10% combat effectiveness increase
        }
    }
}

# =============================================================================
# MEMORY SKILLS
# These are passive skills that require Ability Points to equip
# They have effects only inside battle
# =============================================================================

MEMORY_SKILLS = {
    # 1. PERIODIC (every N total battle turns)
    "raising_speed": {
        "name": "Raising Speed",
        "short_description": "Gain Special every 2 turns",
        "long_description": "Every 2 total turns, grants +1 Special (buff) up to a maximum of +3 Special.",
        "type": "passive",
        "memory_cost": 1,
        "trigger_type": "periodic",
        "played_sound": "chainsaw-fast.mp3",  # Custom sound for this skill
        "trigger_params": {
            "period": 2,
            "action": {
                "effect": "BUFF_STAT",
                "stat": "spe",          # Attribute name to buff
                "amount": 1,
                "max_total_bonus": 3    # Cap for cumulative applications
            }
        }
    },
    "raising_voltage": {
        "name": "Raising Voltage",
        "short_description": "Gain Special every 2 turns",
        "long_description": "Every 2 total turns, grants +1 Special (buff) up to a maximum of +3 Special.",
        "type": "passive",
        "memory_cost": 1,
        "trigger_type": "periodic",
        "played_sound": "electrical-shock-zap-106412.mp3",  # Custom sound for this skill
        "trigger_params": {
            "period": 2,
            "action": {
                "effect": "BUFF_STAT",
                "stat": "spe",          # Attribute name to buff
                "amount": 1,
                "max_total_bonus": 3    # Cap for cumulative applications
            }
        }
    },
    "fiery_presence": {
        "name": "Fiery Presence",
        "short_description": "Burn nearby foes",
        "long_description": "Every turn applies Burn Lv1 (Dur 1) to a random enemy body part.",
        "type": "passive",
        "memory_cost": 1,
        "trigger_type": "periodic",
        "played_sound": "fire-sound.mp3",  # Custom sound for this skill
        "trigger_params": {
            "period": 1,
            "action": {
                "effect": "APPLY_STATUS",
                "status": "BURN",
                "level": 1,
                "duration": 1,
                "target_mode": "RANDOM_ENEMY_PART",  # or SPECIFIC_PART
                "target_part": None                  # If SPECIFIC_PART set HEAD/BODY etc.
            }
        }
    },

    # 2. ON BODY PART LOSS
    "snap_back": {
        "name": "Snap Back",
        "short_description": "Recover lost body part",
        "long_description": "The first time one of your body parts reaches 0 HP, it is restored to 50% HP.",
        "type": "passive",
        "memory_cost": 1,
        "trigger_type": "on_bodypart_loss",
        "played_sound": "whip-123738.mp3",  # Custom sound for this skill
        "trigger_params": {
            "limit_per_battle": 1,
            "action": {
                "effect": "RESTORE_PART_PERCENT",
                "percent": 0.50
            }
        }
    },
    "explosive_mindset": {
        "name": "Explosive Mindset",
        "short_description": "Explode when hurt",
        "long_description": "When one of your body parts is lost, deal damage equal to the your Special stat to a random enemy body part and inflict Burn Lv1 Dur1.",
        "type": "passive",
        "memory_cost": 1,
        "trigger_type": "on_bodypart_loss",
        "played_sound": "explosion-1.mp3",  # Custom sound for this skill
        "trigger_params": {
            "limit_per_battle": 0,  # 0 = unlimited
            "action": {
                "effect": "DAMAGE_AND_STATUS",
                "damage_formula": "1 * special",  # Parsed simply
                "status": "BURN",
                "status_level": 1,
                "status_duration": 1,
                "target_mode": "RANDOM_ENEMY_PART"
            }
        }
    },

    # 3. CONDITIONAL ENEMY STATUS THRESHOLD - BUFF BASED
    "exploit_wounds": {
        "name": "Exploit Wounds",
        "short_description": "Gain dexterity vs bleeding foes",
        "long_description": "At the start of your turn, gain +1 Dexterity for every 2 total Bleed stacks on the enemy. The buff refreshes each turn and is removed if the condition is no longer met.",
        "type": "passive",
        "memory_cost": 1,
        "trigger_type": "enemy_status_buff",
        "played_sound": "chainsaw-fast.mp3",  # Custom sound for this skill
        "trigger_params": {
            "status": "BLEED",
            "stacks_per_increment": 2,
            "buff_per_increment": 1,
            "stat": "des",                     # Dexterity stat
            "duration": 1                     # Lasts only this turn (refreshed each turn)
        }
    },

    "exploit_acid": {
        "name": "Exploit Acid",
        "short_description": "Gain strength vs foes with acid",
        "long_description": "At the start of your turn, gain +1 Strength for every 2 total Acid stacks on the enemy. The buff refreshes each turn and is removed if the condition is no longer met.",
        "type": "passive",
        "memory_cost": 1,
        "trigger_type": "enemy_status_buff",
        "played_sound": "Buff-1.mp3",  # Custom sound for this skill
        "trigger_params": {
            "status": "ACID",
            "stacks_per_increment": 2,
            "buff_per_increment": 1,
            "stat": "forz",                     # Strength stat
            "duration": 1                     # Lasts only this turn (refreshed each turn)
        }
    },

    "exploit_stun": {
        "name": "Exploit Stun",
        "short_description": "Gain strength vs stunned foes",
        "long_description": "At the start of your turn, gain +1 Strength for every 2 total Stun stacks on the enemy. The buff refreshes each turn and is removed if the condition is no longer met.",
        "type": "passive",
        "memory_cost": 1,
        "trigger_type": "enemy_status_buff",
        "played_sound": "Buff-1.mp3",  # Custom sound for this skill
        "trigger_params": {
            "status": "STUN",
            "stacks_per_increment": 2,
            "buff_per_increment": 1,
            "stat": "forz",                    # Strength stat (internal name)
            "duration": 1                     # Lasts only this turn (refreshed each turn)
        }
    }
    
}

# --- ACCESSORS (kept for existing imports) ---
def get_proficiency_skills():
    """Get all available proficiency skills"""
    return PROFICIENCY_SKILLS

def get_memory_skills():
    """Get all available memory skills"""
    return MEMORY_SKILLS

def get_inborn_skill_by_id(skill_id):
    return INBORN_SKILLS.get(skill_id)

# --- SPECIES ASSOCIATION RESOLUTION ---
def get_inborn_skills_for_species(species_name: str):
    """
    Return dict {skill_id: skill_def} for the given species.
    Source of species→skill association = Species_Config.SPECIES_INBORN_SKILLS.
    """
    try:
        from Species_Config import SPECIES_INBORN_SKILLS
        skill_ids = SPECIES_INBORN_SKILLS.get(species_name, [])
    except Exception:
        # Fallback hardcoded mapping if Species_Config missing
        fallback = {
            "Selkio": ["bare_bones"],
            "Sapifer": ["fluffy_coverage"],
            "Maedo": ["insulating_membrane"]
        }
        skill_ids = fallback.get(species_name, [])
    result = {}
    for sid in skill_ids:
        data = INBORN_SKILLS.get(sid)
        if data:
            result[sid] = data
    return result

# --- BACKWARD COMPAT LEGACY FUNCTION NAME ---
def get_inborn_skills(species_name):
    return get_inborn_skills_for_species(species_name)

# --- ELEMENTAL CALC FUNCTIONS (keep unchanged / or ensure present) ---
def calculate_elemental_damage(base_damage, element, target_species, target_skills=None):
    final_damage = base_damage
    effects_applied = True
    inborn = get_inborn_skills_for_species(target_species)
    for skill in inborn.values():
        if not skill.get("always_active"):
            continue
        eff = skill.get("effects", {})
        if element in eff.get("immunities", []):
            return 0, False
        if element in eff.get("resistances", {}):
            final_damage = int(final_damage * eff["resistances"][element])
        if element in eff.get("weaknesses", {}):
            final_damage = int(final_damage * eff["weaknesses"][element])
    return final_damage, effects_applied

def get_species_elemental_modifiers(species):
    mods = {"resistances": {}, "weaknesses": {}, "immunities": []}
    inborn = get_inborn_skills_for_species(species)
    for skill in inborn.values():
        if not skill.get("always_active"):
            continue
        eff = skill.get("effects", {})
        mods["resistances"].update(eff.get("resistances", {}))
        mods["weaknesses"].update(eff.get("weaknesses", {}))
        mods["immunities"].extend(eff.get("immunities", []))
    return mods