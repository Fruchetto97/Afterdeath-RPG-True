# Player_Moves.py
# Player moves system similar to Player_Equipment and Player_Items
import sys
import os

# Add the parent directory to sys.path to import from the main directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Lazy import for Player_Equipment to avoid circular imports
PLAYER_EQUIPMENT_AVAILABLE = False

# Import Species_Config for species-specific starting moves
try:
    from Species_Config import get_starting_moves
    SPECIES_CONFIG_AVAILABLE = True
except ImportError:
    SPECIES_CONFIG_AVAILABLE = False
    print("[PlayerMoves] Warning: Species_Config not available, using default moves")

# Import element calculation from Battle_Menu_Beta_V18
try:
    from Battle_Menu_Beta_V18 import calculate_move_element
    ELEMENT_CALCULATION_AVAILABLE = True
except ImportError:
    ELEMENT_CALCULATION_AVAILABLE = False
    print("[PlayerMoves] Warning: Element calculation not available, using manual elements")

class PlayerMoves:
    """Manages player moves for combat"""
    
    def __init__(self, character_name="Default Player"):
        self.character_name = character_name
        self.moves = []
        print(f"[PlayerMoves] *** CREATING PlayerMoves object for '{character_name}' ***")
        
    def add_move(self, name, move_type, forz_scaling, des_scaling, spe_scaling, 
                effects=None, requirements=None, elements=None, accuracy=100, species_name="Maedo"):
        """Add a move to the player's move list with automatic element calculation"""
        if effects is None:
            effects = []
        if requirements is None:
            requirements = []
        if elements is None or len(elements) == 0:
            # Auto-calculate elements if not provided
            if ELEMENT_CALCULATION_AVAILABLE:
                scaling_dict = {'forz': forz_scaling, 'des': des_scaling, 'spe': spe_scaling}
                calculated_element = calculate_move_element(scaling_dict, species_name)
                elements = [calculated_element]
                print(f"[PlayerMoves] Auto-calculated element: {calculated_element} for move '{name}' (species: {species_name})")
            else:
                elements = ['IMPACT']  # Fallback default
                
        move = {
            'name': name,
            'type': move_type,
            'scaling': {
                'forz': forz_scaling,
                'des': des_scaling, 
                'spe': spe_scaling
            },
            'effects': effects,
            'requirements': requirements,
            'elements': elements,
            'accuracy': accuracy
        }
        
        self.moves.append(move)
        print(f"[PlayerMoves] Added move '{name}' to {self.character_name}")
        return move
        
    def remove_move(self, move_name):
        """Remove a move by name"""
        for i, move in enumerate(self.moves):
            if move['name'] == move_name:
                removed = self.moves.pop(i)
                print(f"[PlayerMoves] Removed move '{move_name}' from {self.character_name}")
                return removed
        print(f"[PlayerMoves] Move '{move_name}' not found in {self.character_name}'s moves")
        return None
        
    def get_move(self, move_name):
        """Get a move by name"""
        for move in self.moves:
            if move['name'] == move_name:
                return move
        return None
        
    def clear_all_moves(self):
        """Clear all moves"""
        count = len(self.moves)
        self.moves = []
        print(f"[PlayerMoves] Cleared {count} moves for {self.character_name}")
        
    def get_all_moves(self):
        """Get all moves (basic moves + weapon moves based on proficiency)"""
        all_moves = self.moves.copy()
        
        # Add weapon moves if available
        try:
            weapon_moves = self.get_weapon_moves()
            all_moves.extend(weapon_moves)
        except Exception as e:
            print(f"[Player_Moves] Could not get weapon moves: {e}")
        
        return all_moves
    
    def get_weapon_moves(self):
        """Get moves from currently equipped weapons based on proficiency level"""
        weapon_moves = []
        
        # Lazy import to avoid circular dependencies
        global PLAYER_EQUIPMENT_AVAILABLE
        if not PLAYER_EQUIPMENT_AVAILABLE:
            try:
                global get_main_player_equipment
                from Player_Equipment import get_main_player_equipment
                PLAYER_EQUIPMENT_AVAILABLE = True
                print("[Player_Moves] Player_Equipment imported successfully (lazy)")
            except ImportError as e:
                print(f"[Player_Moves] Could not import Player_Equipment: {e}")
                return weapon_moves
            
        try:
            player_equipment = get_main_player_equipment()
            if not player_equipment:
                return weapon_moves
                
            # Get equipped weapon
            equipped_weapon = None
            for equipment in player_equipment.equip:
                if equipment.equipped and hasattr(equipment, 'type') and equipment.type == 'weapon':
                    equipped_weapon = equipment
                    break
                    
            if not equipped_weapon:
                print("[Player_Moves] No weapon equipped")
                return weapon_moves
                
            # Get weapon class and proficiency
            weapon_class = getattr(equipped_weapon, 'weapon_class', '')
            if not weapon_class:
                print(f"[Player_Moves] Weapon '{equipped_weapon.name}' has no weapon_class")
                return weapon_moves
                
            # Get proficiency level
            proficiency_level = 0
            if hasattr(player_equipment, 'weapon_proficiency'):
                proficiency_level = player_equipment.weapon_proficiency.get_proficiency(weapon_class)
                print(f"[Player_Moves] {weapon_class} proficiency level: {proficiency_level}")
            
            # Instead of custom moves, get the weapon's actual moves based on proficiency
            if hasattr(equipped_weapon, 'get_available_moves'):
                available_moves = equipped_weapon.get_available_moves(proficiency_level)
                print(f"[Player_Moves] Found {len(available_moves)} weapon moves for {weapon_class} at level {proficiency_level}")
                
                # Convert Mossa objects to dictionary format for consistency
                for move in available_moves:
                    weapon_moves.append({
                        'name': move.name,
                        'type': move.tipo,
                        'scaling': {'forz': move.sca_for, 'des': move.sca_des, 'spe': move.sca_spe},
                        'effects': move.eff_appl,
                        'requirements': move.reqs,
                        'elements': move.elem,
                        'accuracy': move.accuracy
                    })
            else:
                # Fallback: get moves based on proficiency level (placeholder system)
                
                print(f"Moves not found")
            
        except Exception as e:
            print(f"[Player_Moves] Error getting weapon moves: {e}")
            
        return weapon_moves
    
    
    def get_basic_moves(self):
        """Get only the basic player moves (without weapon moves)"""
        return self.moves.copy()
        
    def get_moves_count(self):
        """Get number of basic moves only"""
        return len(self.moves)
        
    def get_all_moves_count(self):
        """Get total number of moves including weapon moves"""
        return len(self.get_all_moves())

# Global player moves instance
player_moves = None

def initialize_player_moves(character_name="Default Player"):
    """Initialize the global player moves instance"""
    global player_moves
    player_moves = PlayerMoves(character_name)
    print(f"[PlayerMoves] Initialized player moves for '{character_name}'")
    
    # Add default moves for the player
    setup_default_player_moves()
    
    return player_moves

def setup_default_player_moves():
    """Set up species-specific starting moves for the player"""
    global player_moves
    
    if player_moves is None:
        print("[PlayerMoves] ERROR: player_moves not initialized")
        return
        
    # Clear existing moves
    player_moves.clear_all_moves()
    
    # Get player species information
    try:
        from Overworld_Main_V7 import PLAYER_CHARACTER_DATA
        species = PLAYER_CHARACTER_DATA.get('species', 'Selkio')  # Default to Selkio
        print(f"[PlayerMoves] Setting up moves for species: {species}")
    except ImportError:
        species = 'Selkio'  # Fallback default
        print("[PlayerMoves] Could not import PLAYER_CHARACTER_DATA, using Selkio default")
    
    # Add species-specific starting moves if available
    if SPECIES_CONFIG_AVAILABLE:
        try:
            starting_moves = get_starting_moves(species)
            if starting_moves:
                print(f"[PlayerMoves] Adding {len(starting_moves)} species-specific moves for {species}")
                for move_data in starting_moves:
                    player_moves.add_move(
                        move_data['name'],
                        move_data['type'],
                        move_data['scaling']['forz'],
                        move_data['scaling']['des'], 
                        move_data['scaling']['spe'],
                        effects=move_data.get('effects', []),
                        requirements=move_data.get('requirements', []),
                        elements=move_data.get('elements', []),
                        accuracy=move_data.get('accuracy', 100),
                        species_name=species
                    )
                print(f"[PlayerMoves] Set up {len(starting_moves)} species-specific moves for {species}")
                return
            else:
                print(f"[PlayerMoves] No starting moves found for {species}, using fallback")
        except Exception as e:
            print(f"[PlayerMoves] Error loading species-specific moves: {e}")
    
    # Fallback: Add default moves (original system)
    
    # Basic attack moves
    
    player_moves.add_move(
        "Salt the Wound", "ATK", 0, 3, 3,
        effects=[["bleed", 2, 2, 0]], 
        requirements=["TARGET BLEED", "NEEDS 2 ARMS"], 
        elements=["CUT"], 
        accuracy=90
    )
    
    player_moves.add_move(
        "Sawblade Hands", "ATK", 0, 1, 1,
        effects=[["bleed", 1, 1, 0]], 
        requirements=["NEEDS 2 ARMS"], 
        elements=["CUT"], 
        accuracy=90
    )
    
    player_moves.add_move(
        "Head-Chopping Kick", "ATK", 0, 2, 4,
        effects=[["bleed", 2, 2, 0]], 
        requirements=["NEEDS 2 LEGS", "TARGET HEAD"], 
        elements=["CUT"], 
        accuracy=90
    )
    
    player_moves.add_move(
        "Running Onslaught", "ATK", 0, 4, 4,
        effects=[], 
        requirements=["NEEDS 2 LEGS", "NEEDS 2 ARMS"], 
        elements=["CUT"], 
        accuracy=90
    )
    
    player_moves.add_move(
        "High Frequency", "BUF", 0, 0, 0,
        effects=[["buf_spe", 2, 2, 0]], 
        requirements=["NEEDS 2 ARMS"], 
        accuracy=90
    )

    player_moves.add_move(
       "Raise Shield", "BUF", 0, 0, 0,
       effects=[["buf_shield", 2, 2, 0]], 
        requirements=["NEEDS ARM"], 
        accuracy=90
    )
    
    print(f"[PlayerMoves] Set up {player_moves.get_moves_count()} fallback default moves (species-specific moves unavailable)")

def get_player_moves():
    """Get the global player moves instance"""
    global player_moves
    if player_moves is None:
        print("[PlayerMoves] WARNING: player_moves not initialized, initializing now")
        initialize_player_moves()
    return player_moves

def add_move_to_player(name, move_type, forz_scaling, des_scaling, spe_scaling, 
                      effects=None, requirements=None, elements=None, accuracy=100, species_name="Maedo"):
    """Add a move to the player (convenience function)"""
    moves = get_player_moves()
    return moves.add_move(name, move_type, forz_scaling, des_scaling, spe_scaling,
                         effects, requirements, elements, accuracy, species_name)

def remove_move_from_player(move_name):
    """Remove a move from the player (convenience function)"""
    moves = get_player_moves()
    return moves.remove_move(move_name)

# Auto-initialize when module is imported
print("[Player_Moves.py] *** GLOBAL MODULE EXECUTION: Creating player moves system ***")
initialize_player_moves("Player")
