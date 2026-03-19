"""
Global SFX Volume Manager for Afterdeath RPG
This module provides centralized management of SFX volume across all game components.
"""

import pygame
import json
import os
from pathlib import Path

# Global SFX volume variable
_global_sfx_volume = 0.8  # Default SFX volume

def load_global_sfx_volume():
    """Load the global SFX volume from game settings"""
    global _global_sfx_volume
    try:
        settings_file = Path("game_settings.json")
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                _global_sfx_volume = settings.get('sfx_volume', 0.8)
        else:
            _global_sfx_volume = 0.8
    except Exception as e:
        print(f"[Global_SFX] Error loading SFX volume: {e}")
        _global_sfx_volume = 0.8
    
    return _global_sfx_volume

def get_global_sfx_volume():
    """Get the current global SFX volume"""
    return _global_sfx_volume

def set_global_sfx_volume(volume):
    """Set the global SFX volume (0.0 to 1.0) and save to settings"""
    global _global_sfx_volume
    _global_sfx_volume = max(0.0, min(1.0, volume))
    
    # Save to game settings immediately
    try:
        settings_file = Path("game_settings.json")
        settings = {}
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        
        settings['sfx_volume'] = _global_sfx_volume
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
            
    except Exception as e:
        print(f"[Global_SFX] Error saving SFX volume: {e}")
    
    return _global_sfx_volume

# Global sound tracking for volume updates
_loaded_sounds = []  # List to track all loaded sounds for volume updates

def _track_sound(sound, base_volume):
    """Internal function to track loaded sounds for volume updates"""
    global _loaded_sounds
    _loaded_sounds.append({'sound': sound, 'base_volume': base_volume})

def load_sound_with_global_volume(sound_path, base_volume=1.0):
    """
    Load a sound effect with the global SFX volume applied
    
    Args:
        sound_path (str): Path to the sound file
        base_volume (float): Base volume for this specific sound (0.0 to 1.0)
    
    Returns:
        pygame.mixer.Sound or None: Loaded sound with volume applied
    """
    try:
        sound = pygame.mixer.Sound(sound_path)
        # Apply both the base volume and global SFX volume
        final_volume = base_volume * _global_sfx_volume
        sound.set_volume(final_volume)
        
        # Track this sound for future volume updates
        _track_sound(sound, base_volume)
        
        return sound
    except Exception as e:
        print(f"[Global_SFX] Error loading sound {sound_path}: {e}")
        return None

def apply_global_volume_to_sound(sound, base_volume=1.0):
    """
    Apply the global SFX volume to an existing sound object
    
    Args:
        sound (pygame.mixer.Sound): The sound object
        base_volume (float): Base volume for this specific sound (0.0 to 1.0)
    """
    if sound:
        final_volume = base_volume * _global_sfx_volume
        sound.set_volume(final_volume)

def update_all_tracked_sounds():
    """Update volume for all tracked sounds to current global SFX volume"""
    global _loaded_sounds
    # Clean up references to deleted sounds and update remaining ones
    active_sounds = []
    for sound_data in _loaded_sounds:
        sound = sound_data['sound']
        base_volume = sound_data['base_volume']
        try:
            # Test if sound is still valid
            sound.get_volume()
            # Update volume
            final_volume = base_volume * _global_sfx_volume
            sound.set_volume(final_volume)
            active_sounds.append(sound_data)
        except:
            # Sound has been garbage collected, don't track it anymore
            pass
    _loaded_sounds = active_sounds

def update_all_sounds_volume(sound_dict, base_volumes=None):
    """
    Update volume for multiple sound objects
    
    Args:
        sound_dict (dict): Dictionary of sound objects {name: sound}
        base_volumes (dict): Dictionary of base volumes {name: volume}. If None, uses 1.0 for all
    """
    if base_volumes is None:
        base_volumes = {}
    
    for name, sound in sound_dict.items():
        if sound:
            base_vol = base_volumes.get(name, 1.0)
            apply_global_volume_to_sound(sound, base_vol)

# Sound effect paths - commonly used across the game
COMMON_SFX_PATHS = {
    'menu_selection': r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\menu-selection-102220.mp3",
    'button_click': r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\casual-click-pop-ui-3-262120.mp3",
    'cancel_discard': r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\discard-sound-effect-221455.mp3",
    'level_up': r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\cute-level-up-3-189853.mp3"
}

# Common base volumes for different types of sounds
COMMON_BASE_VOLUMES = {
    'menu_selection': 0.4,
    'button_click': 0.45,
    'cancel_discard': 1.0,
    'level_up': 0.7
}

def load_common_sfx():
    """Load commonly used sound effects with global volume applied"""
    sounds = {}
    for name, path in COMMON_SFX_PATHS.items():
        base_vol = COMMON_BASE_VOLUMES.get(name, 1.0)
        sounds[name] = load_sound_with_global_volume(path, base_vol)
    return sounds

# Initialize global SFX volume on module import
load_global_sfx_volume()
