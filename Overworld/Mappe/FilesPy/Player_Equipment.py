import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pygame
from Battle_Menu_Beta_V18 import Mossa, calculate_move_damage, calculate_move_stamina_cost


# Weapon Proficiency System
class WeaponProficiency:
    """Manages weapon class proficiencies and experience for a player."""
    
    # Define weapon classes and their experience thresholds
    WEAPON_CLASSES = [
        "Side Sword", "Long Sword", "Curved Sword", "Curved Longsword", "SwordStaff", "Spear", "Greatsword", 
        "Rapier", "Axe", "Hammer", "Mace", "Bow", "Crossbow", 
        "Great Axe", "Halberd", "Dagger", "Sword & Shield"
    ]
    
    # Experience thresholds for proficiency levels
    EXP_THRESHOLDS = {
        0: 0,    # Starting level
        1: 15,   # 0 -> 1 requires 15 hits
        2: 30,   # 1 -> 2 requires 30 more hits (45 total)
        3: -1    # 2 -> 3 requires special means (weapon masters)
    }
    
    def __init__(self):
        """Initialize weapon proficiencies and experience counters."""
        print(f"[WeaponProficiency] *** INIT DEBUG: Creating NEW WeaponProficiency object {id(self)} ***")
        self.wpn_class_proficiency = {weapon_class: 0 for weapon_class in self.WEAPON_CLASSES}
        self.wpn_class_exp = {weapon_class: 0 for weapon_class in self.WEAPON_CLASSES}
        print(f"[WeaponProficiency] *** INIT DEBUG: Initialized {len(self.wpn_class_proficiency)} weapon classes ***")
    
    def add_experience(self, weapon_class, hits=1):
        """Add experience to a weapon class and check for proficiency increase."""
        print(f"[WeaponProficiency] *** ADDING EXPERIENCE DEBUG START ***")
        print(f"[WeaponProficiency] Adding {hits} hits to {weapon_class}")
        print(f"[WeaponProficiency] BEFORE - {weapon_class}: Level {self.wpn_class_proficiency.get(weapon_class, 0)}, EXP {self.wpn_class_exp.get(weapon_class, 0)}")
        print(f"[WeaponProficiency] Object ID: {id(self)}")
        
        if weapon_class not in self.WEAPON_CLASSES:
            print(f"[WeaponProficiency] Warning: Unknown weapon class '{weapon_class}'")
            return False
        
        old_proficiency = self.wpn_class_proficiency[weapon_class]
        old_exp = self.wpn_class_exp[weapon_class]
        self.wpn_class_exp[weapon_class] += hits
        new_exp = self.wpn_class_exp[weapon_class]
        
        print(f"[WeaponProficiency] EXP updated: {old_exp} -> {new_exp}")
        
        # Check for proficiency increase (only up to level 2 automatically)
        new_proficiency = self._calculate_proficiency_level(weapon_class)
        if new_proficiency > old_proficiency and new_proficiency <= 2:
            self.wpn_class_proficiency[weapon_class] = new_proficiency
            print(f"[WeaponProficiency] {weapon_class} proficiency increased from {old_proficiency} to {new_proficiency}!")
            print(f"[WeaponProficiency] AFTER LEVEL UP - {weapon_class}: Level {self.wpn_class_proficiency.get(weapon_class, 0)}, EXP {self.wpn_class_exp.get(weapon_class, 0)}")
            print(f"[WeaponProficiency] *** ADDING EXPERIENCE DEBUG END ***")
            return True
        
        print(f"[WeaponProficiency] AFTER - {weapon_class}: Level {self.wpn_class_proficiency.get(weapon_class, 0)}, EXP {self.wpn_class_exp.get(weapon_class, 0)}")
        print(f"[WeaponProficiency] *** ADDING EXPERIENCE DEBUG END ***")
        return False
    
    def _calculate_proficiency_level(self, weapon_class):
        """Calculate the proficiency level based on current experience."""
        exp = self.wpn_class_exp[weapon_class]
        current_proficiency = self.wpn_class_proficiency[weapon_class]
        
        # Don't automatically increase beyond level 2
        if current_proficiency >= 2:
            return current_proficiency
        
        if exp >= 45:  # 15 + 30 = 45 total for level 2
            return 2
        elif exp >= 15:  # 15 for level 1
            return 1
        else:
            return 0
    
    def master_weapon_class(self, weapon_class):
        """Special function to increase proficiency from 2 to 3 via weapon masters."""
        if weapon_class not in self.WEAPON_CLASSES:
            print(f"[WeaponProficiency] Warning: Unknown weapon class '{weapon_class}'")
            return False
        
        if self.wpn_class_proficiency[weapon_class] == 2:
            self.wpn_class_proficiency[weapon_class] = 3
            print(f"[WeaponProficiency] {weapon_class} mastered! Proficiency increased to 3!")
            return True
        elif self.wpn_class_proficiency[weapon_class] < 2:
            print(f"[WeaponProficiency] Cannot master {weapon_class}: proficiency must be 2 first (current: {self.wpn_class_proficiency[weapon_class]})")
            return False
        else:
            print(f"[WeaponProficiency] {weapon_class} is already mastered!")
            return False
    
    def get_proficiency(self, weapon_class):
        """Get the current proficiency level for a weapon class."""
        return self.wpn_class_proficiency.get(weapon_class, 0)
    
    def get_experience(self, weapon_class):
        """Get the current experience for a weapon class."""
        return self.wpn_class_exp.get(weapon_class, 0)
    
    def get_exp_to_next_level(self, weapon_class):
        """Get experience needed to reach the next proficiency level."""
        if weapon_class not in self.WEAPON_CLASSES:
            return None
        
        current_proficiency = self.wpn_class_proficiency[weapon_class]
        current_exp = self.wpn_class_exp[weapon_class]
        
        if current_proficiency >= 2:
            return "Master via weapon master"  # Level 3 requires special means
        elif current_proficiency == 1:
            return 45 - current_exp  # Need 45 total for level 2
        else:
            return 15 - current_exp  # Need 15 total for level 1
    
    def get_proficiency_progress(self, weapon_class):
        """Get proficiency progress as a ratio (0.0 to 1.0) for UI bars."""
        if weapon_class not in self.WEAPON_CLASSES:
            return 0.0
        
        current_proficiency = self.wpn_class_proficiency[weapon_class]
        current_exp = self.wpn_class_exp[weapon_class]
        
        if current_proficiency == 0:
            # Level 0 -> 1 needs 15 exp total
            return min(1.0, current_exp / 15.0)
        elif current_proficiency == 1:
            # Level 1 -> 2 needs 30 more exp (experience between 15 and 45)
            if current_exp < 15:
                return 0.0  # Should not happen, but safety check
            exp_in_current_level = current_exp - 15  # Subtract the 15 exp used for level 1
            return min(1.0, exp_in_current_level / 30.0)
        elif current_proficiency == 2:
            # Level 2 -> 3 requires weapon master (show full bar)
            return 1.0
        else:
            # Max level (3) - show full bar
            return 1.0
    
    def get_all_proficiencies(self):
        """Get a summary of all weapon class proficiencies."""
        summary = {}
        for weapon_class in self.WEAPON_CLASSES:
            summary[weapon_class] = {
                'proficiency': self.wpn_class_proficiency[weapon_class],
                'experience': self.wpn_class_exp[weapon_class],
                'exp_to_next': self.get_exp_to_next_level(weapon_class)
            }
        return summary
    
    def __repr__(self):
        return f"<WeaponProficiency classes={len(self.WEAPON_CLASSES)}>"


# Equipment class

class Equipment:
    def __init__(self, name, icon_path, image_path, eq_type, description, short_description, equipped=False, moves=None, weapon_class=None, weapon_type=None):
        self.name = name
        self.type = eq_type  # 'weapon', 'armor', or 'artifact'
        self.description = description
        self.short_description = short_description
        self.icon_path = icon_path
        self.image_path = image_path
        self.equipped = equipped  # Use the parameter value
        self.icon = None
        self.image = None
        self.weapon_class = weapon_class  # Manually assigned weapon class for proficiency system
        
        # Weapon type system: "One Handed", "One and a Half Handed", "Two Handed"
        self.weapon_type = weapon_type if self.type == 'weapon' else None
        
        if self.type == 'weapon':
            self.moves = moves[:4] if moves else []  # Weapons can have up to 4 moves
        else:
            self.moves = []

    def get_weapon_class(self):
        """Get the manually assigned weapon class for proficiency system."""
        return self.weapon_class if self.type == 'weapon' else None

    def get_weapon_type(self):
        """Get the weapon type for hand requirements and stamina bonuses."""
        return self.weapon_type if self.type == 'weapon' else None

    def get_stamina_bonus(self):
        """Get stamina cost reduction bonus based on weapon type."""
        if self.type != 'weapon' or not self.weapon_type:
            return 0
        
        weapon_type_bonuses = {
            "One Handed": -2,
            "One and a Half Handed": -3,
            "Two Handed": -4
        }
        
        bonus = weapon_type_bonuses.get(self.weapon_type, 0)
        print(f"[Equipment] Stamina bonus for {self.name} ({self.weapon_type}): {bonus}")
        return bonus

    

    def load_images(self):
        """Load icon and image from their paths, if not already loaded."""
        if self.icon is None and self.icon_path:
            try:
                print(f"[PlayerEquipment][DEBUG] Loading icon for '{self.name}': {self.icon_path}")
                self.icon = pygame.image.load(self.icon_path).convert_alpha()
            except Exception as e:
                print(f"[PlayerEquipment][ERROR] Could not load icon for '{self.name}' at '{self.icon_path}': {e}")
                self.icon = None
        if self.image is None and self.image_path:
            try:
                print(f"[PlayerEquipment][DEBUG] Loading image for '{self.name}': {self.image_path}")
                self.image = pygame.image.load(self.image_path).convert_alpha()
            except Exception as e:
                print(f"[PlayerEquipment][ERROR] Could not load image for '{self.name}' at '{self.image_path}': {e}")
                self.image = None

    def equip(self):
        """Mark this equipment as equipped."""
        # Check weapon requirements if this is a weapon
        if self.type == 'weapon':
            # Try to access the player object to check requirements
            try:
                # Get the global player1 object
                import sys
                current_module = sys.modules[__name__]
                if hasattr(current_module, 'player1'):
                    player_obj = getattr(current_module, 'player1')
                    can_equip, reason = player_obj.check_weapon_requirements(self)
                    if not can_equip:
                        print(f"[PlayerEquipment] Cannot equip {self.name}: {reason}")
                        return False
            except Exception as e:
                print(f"[PlayerEquipment] Could not check weapon requirements for {self.name}: {e}")
                # Continue with equipping if we can't check requirements
        
        self.equipped = True
        print(f"[PlayerEquipment] Equipped: {self.name}")
        return True

    def unequip(self):
        """Mark this equipment as unequipped."""
        self.equipped = False
        print(f"[PlayerEquipment] Unequipped: {self.name}")

    def toggle_equipped(self):
        """Toggle the equipped status and return the new status."""
        # This method should be called by PlayerEquip to handle slot management
        print(f"[PlayerEquipment] Warning: toggle_equipped called directly on {self.name}. Use PlayerEquip.equip_item() instead for proper slot management.")
        if self.equipped:
            self.unequip()
        else:
            self.equip()
        return self.equipped

    def add_move(self, move):
        if self.type == 'weapon' and isinstance(move, Mossa) and len(self.moves) < 3:
            self.moves.append(move)

    def calculate_move_damages(self, character):
        """Calculate damage for all moves using Battle_Menu_Beta functions."""
        if self.type != 'weapon' or not self.moves:
            return []
        
        damages = []
        for move in self.moves:
            damage = calculate_move_damage(character, move.sca_for, move.sca_des, move.sca_spe)
            damages.append(damage)
        return damages

    def calculate_move_stamina_costs(self):
        """Calculate stamina costs for all moves using Battle_Menu_Beta functions."""
        if self.type != 'weapon' or not self.moves:
            return []
        
        stamina_costs = []
        for move in self.moves:
            cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, 
                                             effects=move.eff_appl, requirements=move.reqs, accuracy=move.accuracy)
            stamina_costs.append(cost)
        return stamina_costs

    def get_move_info(self, character, proficiency_level=None):
        """Get comprehensive info for all moves including damage and stamina cost, filtered by proficiency level."""
        if self.type != 'weapon' or not self.moves:
            return []

        # Get available moves based on proficiency level
        available_moves = self.get_available_moves(proficiency_level)
        
        # Get the actual weapon stamina bonus from weapon type
        weapon_stamina_bonus = abs(self.get_stamina_bonus())  # Use absolute value since bonus is negative

        # Calculate damages only for available moves
        available_damages = []
        for move in available_moves:
            damage = calculate_move_damage(character, move.sca_for, move.sca_des, move.sca_spe)
            available_damages.append(damage)
        
        # Calculate stamina costs only for available moves
        available_stamina_costs = []
        for move in available_moves:
            cost = calculate_move_stamina_cost(move.sca_for, move.sca_des, move.sca_spe, 
                                             effects=move.eff_appl, requirements=move.reqs, accuracy=move.accuracy)
            available_stamina_costs.append(cost)
        
        # Apply weapon stamina bonus to each cost individually
        available_stamina_costs = [max(0, cost - weapon_stamina_bonus) for cost in available_stamina_costs]
        
        move_info = []
        for i, move in enumerate(available_moves):
            info = {
                'name': move.name,
                'type': move.tipo,
                'damage': available_damages[i] if i < len(available_damages) else 0,
                'stamina_cost': available_stamina_costs[i] if i < len(available_stamina_costs) else 0,
                'strength_scaling': move.sca_for,
                'dexterity_scaling': move.sca_des,
                'special_scaling': move.sca_spe,
                'effects': move.eff_appl,
                'requirements': move.reqs,
                'elements': move.elem,
                'accuracy': move.accuracy
            }
            move_info.append(info)
        return move_info

    def get_available_moves(self, proficiency_level=None):
        """Returns moves available at the given proficiency level."""
        if self.type != 'weapon' or not self.moves:
            return []
            
        if proficiency_level is None:
            # If no proficiency level provided, return all moves (for backwards compatibility)
            return self.moves
            
        # Move progression system:
        # Level 0: Move 1 only
        # Level 1: Move 2 replaces Move 1
        # Level 2: Move 2 + Move 3
        # Level 3: Move 2 + Move 3 + Move 4
        
        if proficiency_level == 0:
            return [self.moves[0]] if len(self.moves) > 0 else []
        elif proficiency_level == 1:
            return [self.moves[1]] if len(self.moves) > 1 else [self.moves[0]] if len(self.moves) > 0 else []
        elif proficiency_level == 2:
            available = []
            if len(self.moves) > 1:
                available.append(self.moves[1])
            if len(self.moves) > 2:
                available.append(self.moves[2])
            return available
            return available
        elif proficiency_level >= 3:
            available = []
            if len(self.moves) > 1:
                available.append(self.moves[1])
            if len(self.moves) > 2:
                available.append(self.moves[2])
            if len(self.moves) > 3:
                available.append(self.moves[3])
            return available
        else:
            return []

    def __repr__(self):
        return f"<Equipment name={self.name} type={self.type} moves={len(self.moves)} short_desc={self.short_description[:20]}...>"

# PlayerEquip class
class PlayerEquip:
    def __init__(self, name):
        print(f"[PlayerEquip] *** CREATING PlayerEquip object for '{name}' ***")
        self.name = name
        self.equip = []  # List of Equipment objects
        self.weapon_proficiency = WeaponProficiency()  # Weapon proficiency system
        print(f"[PlayerEquip] *** Created WeaponProficiency object {id(self.weapon_proficiency)} for '{name}' ***")

    def clear_equipment(self, reset_proficiencies=False):
        """Remove all equipment (optionally reset proficiencies)."""
        print(f"[PlayerEquip] *** CLEAR_EQUIPMENT DEBUG: reset_proficiencies={reset_proficiencies} ***")
        print(f"[PlayerEquip] BEFORE clear - WeaponProficiency object ID: {id(self.weapon_proficiency)}")
        
        count = len(self.equip)
        self.equip.clear()
        
        if reset_proficiencies:
            print(f"[PlayerEquip] *** RESETTING WEAPON PROFICIENCY! Creating new object ***")
            old_id = id(self.weapon_proficiency)
            self.weapon_proficiency = WeaponProficiency()
            print(f"[PlayerEquip] *** WeaponProficiency RESET: {old_id} -> {id(self.weapon_proficiency)} ***")
        else:
            print(f"[PlayerEquip] *** PRESERVING WEAPON PROFICIENCY - NOT RESET ***")
            
        print(f"[PlayerEquip] AFTER clear - WeaponProficiency object ID: {id(self.weapon_proficiency)}")
        print(f"[PlayerEquip] Cleared {count} equipment entries for {self.name}")

    def add_equipment(self, equipment):
        if isinstance(equipment, Equipment):
            self.equip.append(equipment)
        else:
            print(f"[PlayerEquip] Tried to add non-equipment object: {equipment}")

    def remove_equipment(self, equipment):
        if equipment in self.equip:
            self.equip.remove(equipment)
        else:
            print(f"[PlayerEquip] Tried to remove equipment not in list: {equipment}")

    def get_equipment_list(self):
        return self.equip

    def get_equipped_by_type(self, eq_type):
        """Get the currently equipped equipment of a specific type."""
        for eq in self.equip:
            if eq.type == eq_type and eq.equipped:
                return eq
        return None

    def check_weapon_requirements(self, weapon):
        """Check if a weapon can be equipped based on current arm HP."""
        if weapon.type != 'weapon':
            return True, "Not a weapon"
        
        weapon_type = getattr(weapon, 'weapon_type', 'Unknown')
        print(f"[PlayerEquip] Checking equip requirements for {weapon.name} (Type: {weapon_type})")
        
        # Try to get current battle character data
        try:
            # Import battle system to get current player status
            import sys
            sys.path.append(r'c:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Mappe\FilesPy')
            from Battle_Menu_Beta_V18 import player
            
            if hasattr(player, 'body_parts'):
                # Count functional arms (HP >= 2 as per user requirements)
                functional_arms = []
                for part in player.body_parts:
                    if "ARM" in part.name.upper() and part.p_pvt >= 2:
                        functional_arms.append(part.name)
                        print(f"[PlayerEquip] Functional arm: {part.name} ({part.p_pvt}/{part.max_p_pvt} HP)")
                
                functional_arm_count = len(functional_arms)
                print(f"[PlayerEquip] Total functional arms (≥2 HP): {functional_arm_count}")
                
                # Check weapon requirements based on user specifications
                if weapon_type == "Two Handed":
                    if functional_arm_count < 2:
                        return False, f"Two Handed weapon requires 2 arms with ≥2 HP, but only {functional_arm_count} available"
                elif weapon_type in ["One Handed", "One and a Half Handed"]:
                    if functional_arm_count < 1:
                        return False, f"{weapon_type} weapon requires 1 arm with ≥2 HP, but only {functional_arm_count} available"
                
                print(f"[PlayerEquip] {weapon.name} can be equipped with {functional_arm_count} functional arms")
                return True, "Requirements met"
            else:
                # If no battle is active, allow equipping
                print(f"[PlayerEquip] No active battle - allowing {weapon.name} to be equipped")
                return True, "No battle active"
                
        except Exception as e:
            # If we can't access battle data, allow equipping
            print(f"[PlayerEquip] Cannot access battle data ({e}) - allowing {weapon.name} to be equipped")
            return True, "Battle data unavailable"

    def equip_item(self, equipment):
        """Equip an item, automatically unequipping any other item of the same type."""
        if not isinstance(equipment, Equipment):
            print(f"[PlayerEquip] Cannot equip non-Equipment object: {equipment}")
            return False
        
        if equipment not in self.equip:
            print(f"[PlayerEquip] Cannot equip item not in inventory: {equipment.name}")
            return False
        
        # Check weapon requirements before equipping
        if equipment.type == 'weapon':
            can_equip, reason = self.check_weapon_requirements(equipment)
            if not can_equip:
                print(f"[PlayerEquip] Cannot equip {equipment.name}: {reason}")
                return False
        
        # Check if there's already an equipped item of this type
        currently_equipped = self.get_equipped_by_type(equipment.type)
        
        if currently_equipped and currently_equipped != equipment:
            # Unequip the currently equipped item
            currently_equipped.unequip()
            print(f"[PlayerEquip] Auto-unequipped {currently_equipped.name} to make room for {equipment.name}")
        
        # Equip the new item
        equipment.equip()
        return True

    def unequip_item(self, equipment):
        """Unequip a specific item."""
        if isinstance(equipment, Equipment) and equipment in self.equip:
            equipment.unequip()
            return True
        return False

    # Weapon Proficiency Methods
    def add_weapon_hit(self, weapon, hits=1):
        """Add experience when hitting with a weapon."""
        if not isinstance(weapon, Equipment) or weapon.type != 'weapon':
            return False
        
        weapon_class = weapon.get_weapon_class()
        if weapon_class:
            return self.weapon_proficiency.add_experience(weapon_class, hits)
        else:
            print(f"[PlayerEquip] Warning: Could not determine weapon class for {weapon.name}")
            return False

    def get_weapon_proficiency(self, weapon_class):
        """Get the proficiency level for a specific weapon class."""
        return self.weapon_proficiency.get_proficiency(weapon_class)

    def get_weapon_experience(self, weapon_class):
        """Get the experience for a specific weapon class."""
        return self.weapon_proficiency.get_experience(weapon_class)

    def master_weapon_class(self, weapon_class):
        """Master a weapon class (increase proficiency from 2 to 3)."""
        return self.weapon_proficiency.master_weapon_class(weapon_class)

    def get_all_weapon_proficiencies(self):
        """Get a summary of all weapon proficiencies."""
        return self.weapon_proficiency.get_all_proficiencies()

    def get_equipped_weapon_proficiency(self):
        """Get the proficiency level for the currently equipped weapon."""
        equipped_weapon = self.get_equipped_by_type('weapon')
        if equipped_weapon:
            weapon_class = equipped_weapon.get_weapon_class()
            if weapon_class:
                return {
                    'weapon': equipped_weapon.name,
                    'weapon_class': weapon_class,
                    'proficiency': self.get_weapon_proficiency(weapon_class),
                    'experience': self.get_weapon_experience(weapon_class),
                    'exp_to_next': self.weapon_proficiency.get_exp_to_next_level(weapon_class)
                }
        return None

    def get_equipped_weapon_type(self):
        """Get the weapon type of the currently equipped weapon."""
        equipped_weapon = self.get_equipped_by_type('weapon')
        if equipped_weapon:
            return equipped_weapon.get_weapon_type()
        return None

    def get_equipped_weapon_stamina_bonus(self):
        """Get the stamina bonus of the currently equipped weapon."""
        equipped_weapon = self.get_equipped_by_type('weapon')
        if equipped_weapon:
            return equipped_weapon.get_stamina_bonus()
        return 0

    def check_weapon_hand_restrictions(self, move_requirements):
        """
        Check if equipped weapon restricts the use of moves with hand requirements.
        Returns True if the move is restricted by the weapon, False if it can be used.
        """
        equipped_weapon = self.get_equipped_by_type('weapon')
        if not equipped_weapon:
            return False  # No weapon equipped, no restrictions
        
        weapon_type = equipped_weapon.get_weapon_type()
        if not weapon_type:
            return False  # No weapon type defined, no restrictions
        
        # Check for specific hand requirements in move
        has_needs_2_hands = False
        has_needs_hand = False
        
        for req in move_requirements:
            req_str = str(req).upper().strip()
            
            # Check for NEEDS 2 HANDS/ARMS requirement
            if "NEEDS 2 HANDS" in req_str or "NEEDS 2 ARMS" in req_str or "NEEDS_2_HANDS" in req_str:
                has_needs_2_hands = True
            
            # Check for single hand requirement (NEEDS HAND, NEEDS ARM, etc.)
            elif ("NEEDS HAND" in req_str or "NEEDS ARM" in req_str or 
                  "NEEDS_HAND" in req_str or "NEEDS_ARM" in req_str or
                  req_str == "NEEDS ARM" or req_str == "NEEDS HAND"):
                has_needs_hand = True
        
        # Apply simple weapon restrictions based on type
        if weapon_type == "One Handed":
            # Block only moves that have NEEDS_2_HANDS
            if has_needs_2_hands:
                return True
        
        elif weapon_type == "One and a Half Handed":
            # Block only moves that have NEEDS_2_HANDS  
            if has_needs_2_hands:
                return True
        
        elif weapon_type == "Two Handed":
            # Block both moves that have NEEDS_2_HANDS and moves that have NEEDS_HAND
            if has_needs_2_hands or has_needs_hand:
                return True
        
        return False

# Global dictionary to hold all players' equipment
player_equip = {}

def get_player_equipment(player_name):
    """Return the equipment list for the specified player name, or None if not found."""
    player = player_equip.get(player_name)
    if player:
        return player.get_equipment_list()
    return None

# Example moves for demonstration (replace with real Mossa objects as needed)
# Note: Using None as character since these are template moves - damage will be calculated later
example_move1 = Mossa("Slash", "ATK", 2, 3, 0, None, eff_appl=[["Burn", 2, 1, 0]], reqs=["WEAPON"], elem=["CUT"], accuracy=90)
example_move2 = Mossa("Pierce", "ATK", 3, 3, 0, None, eff_appl=[["Bleed", 1, 1, 0]], reqs=["WEAPON"], elem=["PIERCE"], accuracy=100)
example_move3 = Mossa("Smash", "ATK", 4, 2, 0, None, eff_appl=[["Bleed", 1, 1, 0], ["Confusion", 2, 1, 0]], reqs=["WEAPON"], elem=["BLOW"], accuracy=70)
example_move4 = Mossa("Ultimate", "ATK", 6, 6, 0, None, eff_appl=[["Bleed", 3, 1, 0], ["Confusion", 2, 1, 0]], reqs=["WEAPON"], elem=["BLOW"], accuracy=100)


# 10 example armors
example_armors = [
    Equipment(
        f"Armor {i+1}",
        None,
        None,
        'armor',
        f"A sturdy armor number {i+1}.",
        f"Armor {i+1}: sturdy protection."
    )
    for i in range(10)
]

# 10 example artifacts
example_artifacts = [
    Equipment(
        f"Artifact {i+1}",
        None,
        None,
        'artifact',
        f"A mysterious artifact number {i+1}.",
        f"Artifact {i+1}: mysterious power."
    )
    for i in range(10)
]


print(f"[Player_Equipment.py] *** GLOBAL MODULE EXECUTION: Creating player1 object ***")
player1 = PlayerEquip("Selkio Guerriero")
print(f"[Player_Equipment.py] *** GLOBAL player1 created with WeaponProficiency ID: {id(player1.weapon_proficiency)} ***")


for eq in example_armors:
    player1.add_equipment(eq)
for eq in example_artifacts:
    player1.add_equipment(eq)

# Global registry of all equipment items
ALL_EQUIPMENT = []

# Add custom weapon: Messer of Blusqua
messer_blusqua = Equipment(
    "Messer of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Messer_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Messer_Blusqua_Image.png",
    'weapon',
    "A single-edged curved sword forged with Blusqua. Swift and deadly in skilled hands.",
    "Single-edged messer sword, made of Blusqua.",
    moves=[
        Mossa("Basic Slash", "ATK", 3, 2, 0, None, eff_appl=[["Bleed", 1, 1, 0]], reqs=["WEAPON"], elem=["CUT"], accuracy=90),
        Mossa("Clean Cut", "ATK", 3, 4, 0, None, eff_appl=[["Bleed", 2, 2, 0]], reqs=["WEAPON"], elem=["CUT"], accuracy=90),
        Mossa("Piercing Thrust", "ATK", 3, 4, 0, None, eff_appl=[["Bleed", 2, 2, 0]], reqs=["WEAPON"], elem=["PIERCE"], accuracy=90)
    ],
    weapon_class="Curved Sword",  # Manually assigned weapon class
    weapon_type="One Handed"  # Weapon type for hand requirements and stamina bonus
)
ALL_EQUIPMENT.append(messer_blusqua)
player1.add_equipment(messer_blusqua)
# Equip the messer as default weapon
player1.equip_item(messer_blusqua)


# Add custom weapon: Kriegmesser of Blusqua
kriegmesser_blusqua = Equipment(
    "Kriegmesser of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Kriegmesser_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Kriegmesser_Blusqua_Image.png",
    'weapon',
    "A long curved sword forged with Blusqua. Light, sharp, and perfect for quick strikes.",
    "Two handed sword, made of Blusqua.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="Curved Longsword",  # Manually assigned weapon class
    weapon_type="One and a Half Handed"  # Can be used with one or two hands
)
player1.add_equipment(kriegmesser_blusqua)

# Add custom weapon: Dane Axe of Blusqua
dane_axe_blusqua = Equipment(
    "Dane Axe of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Dane_Axe_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Dane_Axe_Blusqua_Image.png",
    'weapon',
    "A long Dane axe forged with Blusqua.",
    "Two handed axe, made of Blusqua.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="Great Axe",  # Manually assigned weapon class
    weapon_type="Two Handed"  # Requires both hands
)
player1.add_equipment(dane_axe_blusqua)

# Add custom weapon: Hammer of Blusqua
hammer_blusqua = Equipment(
    "Hammer of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Hammer_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Hammer_Blusqua_Image.png",
    'weapon',
    "A Light hammer forged with Blusqua. Unstoppable force in the right hands.",
    "One handed hammer, made of Blusqua.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="Hammer",  # Manually assigned weapon class
    weapon_type="One Handed"  # Single hand weapon
)

# Add custom weapon: Labrys Axe of Blusqua
labrys_axe_blusqua = Equipment(
    "Labrys Axe of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Labrys_Axe_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Labrys_Axe_Blusqua_Image.png",
    'weapon',
    "A double-headed Labrys axe forged with Blusqua. Balanced for both power and precision.",
    "Double-headed axe, made of Blusqua.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="Great Axe",  # Manually assigned weapon class
    weapon_type="Two Handed"  # Requires both hands
)

# Add custom weapon: Swordstaff of Blusqua
swordstaff_blusqua = Equipment(
    "Swordstaff of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Swordstaff_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Swordstaff_Blusqua_Image.png",
    'weapon',
    "A swordstaff forged with Blusqua. Deadly reach and versatility.",
    "Swordstaff, made of Blusqua.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="SwordStaff",  # Manually assigned weapon class
    weapon_type="Two Handed"  # Can be used with two hands
)

# Add custom weapon: Monatante of Blusqua
monatante_blusqua = Equipment(
    "Monatante of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Montante_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Montante_Blusqua_Image.png",
    'weapon',
    "A massive Montante sword forged with Blusqua. Heavy, powerful, and awe-inspiring.",
    "Two handed sword, made of Blusqua.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="Greatsword",  # Manually assigned weapon class
    weapon_type="Two Handed"  # Requires both hands
)   

# Add custom weapon: Spear of Blusqua
spear_blusqua = Equipment(
    "Spear of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Spear_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Spear_Blusqua_Image.png",
    'weapon',
    "A spear forged with Blusqua. Long reach and piercing power.",
    "Spear, made of Blusqua.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="Spear",  # Manually assigned weapon class
    weapon_type="Two Handed"  # Can be used with two hands
)

# Add custom weapon: Staffsword of Blusqua (alternative name for swordstaff)
staffsword_blusqua = Equipment(
    "Staffsword of Blusqua",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Swordstaff_Blusqua_Icon.png",
    r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Items\Equipment\Swordstaff_Blusqua_Image.png",
    'weapon',
    "A staffsword forged with Blusqua metal. Combines the reach of a staff with the cutting power of a sword.",
    "Staffsword, made of Blusqua.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="SwordStaff",  # Manually assigned weapon class
    weapon_type="Two Handed"  # Can be used with two hands
)

# Add custom weapon: Marrow Pair of Blusqua
marrow_pair = Equipment(
    "Marrow Pair",
    r"C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Equipment\\Marrow_Pair_Icon.png",
    r"C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Equipment\\Marrow_Pair_Image.png",
    'weapon',
    "A Marrow Sword and Shield forged using minerals extracted from the Dorsal Trees. The shield is decorated with spiraling patterns, that evoke the shape of the Rebirth Towers. The Sword Hilt and Shield Rim are made out of Green Ambresite.",
    "Sword & Shield, made of Marrow.",
    moves=[example_move1, example_move2, example_move3, example_move4],
    weapon_class="Sword & Shield",  # Manually assigned weapon class
    weapon_type="Two Handed"  #one hand for the sword, another for the shield
)


# === WEAPON TYPE VERIFICATION AND FIXING ===
# Ensure all weapons have proper weapon_type values to prevent None values in battle
for equipment in ALL_EQUIPMENT:
    if equipment.type == 'weapon' and equipment.weapon_type is None:
        # Set default weapon types based on weapon names/classes
        if "messer" in equipment.name.lower():
            equipment.weapon_type = "One Handed"
        elif "kriegmesser" in equipment.name.lower():
            equipment.weapon_type = "Two Handed"  
        elif "axe" in equipment.name.lower() or "dane" in equipment.name.lower():
            equipment.weapon_type = "Two Handed"
        elif "sword" in equipment.weapon_class.lower() and "shield" in equipment.weapon_class.lower():
            equipment.weapon_type = "Two Handed"  # Sword & Shield
        elif "staff" in equipment.name.lower():
            equipment.weapon_type = "Two Handed"
        else:
            equipment.weapon_type = "One Handed"  # Default fallback
        print(f"[Equipment] Fixed weapon_type for {equipment.name}: {equipment.weapon_type}")

print(f"[Equipment] All weapon types verified and fixed")

# ===== AUTOMATED EQUIPMENT REGISTRY =====
# Global list that collects all equipment automatically
ALL_EQUIPMENT = [
    messer_blusqua,
    kriegmesser_blusqua, 
    dane_axe_blusqua,
    hammer_blusqua,
    labrys_axe_blusqua,
    swordstaff_blusqua,
    monatante_blusqua,
    spear_blusqua,
    staffsword_blusqua,
    marrow_pair
]

# Add example equipment to the registry too
ALL_EQUIPMENT.extend(example_armors)
ALL_EQUIPMENT.extend(example_artifacts)

def get_all_equipment():
    """Get a list of all equipment items in the game."""
    return ALL_EQUIPMENT.copy()

def find_equipment_by_name(equipment_name):
    """Find an equipment item by name from the global registry."""
    for equipment in ALL_EQUIPMENT:
        if equipment.name == equipment_name:
            return equipment
    return None

# Add all weapons to player1
player1.add_equipment(marrow_pair)
# Unequip any currently equipped weapon and equip the messer instead
currently_equipped = player1.get_equipped_by_type('weapon')
if currently_equipped:
    currently_equipped.unequip()
# Equip the messer as default weapon (it has proper weapon_type)
player1.equip_item(messer_blusqua)


player_equip[player1.name] = player1

# Global clear helper
def Clear_Equipment(player_name=None, reset_proficiencies=False):
    """Clear equipment for a specific player (or main player if None)."""
    try:
        if player_name is None:
            target = player1
        else:
            target = player_equip.get(player_name)
        if not target:
            print(f"[PlayerEquip] Clear_Equipment: No equipment object for '{player_name}'")
            return False
        target.clear_equipment(reset_proficiencies=reset_proficiencies)
        return True
    except Exception as e:
        print(f"[PlayerEquip] Clear_Equipment error: {e}")
        return False

# Utility: Load all equipment images for a list
def load_equipment_images(equipment_list):
    for eq in equipment_list:
        if hasattr(eq, 'load_images'):
            eq.load_images()

# Utility: Get the main player's equipment object
def get_main_player_equipment():
    """Return the main player's PlayerEquip object (player1)."""
    print(f"[get_main_player_equipment] *** ACCESSING player1 object ***")
    print(f"[get_main_player_equipment] player1 ID: {id(player1)}")
    print(f"[get_main_player_equipment] player1.weapon_proficiency ID: {id(player1.weapon_proficiency)}")
    
    # Try to detect character name and sync weapon proficiency data
    character_name = None
    try:
        # Try to get character name from various sources
        import sys
        for module_name, module in sys.modules.items():
            if hasattr(module, 'player_stats') and hasattr(module.player_stats, 'name'):
                character_name = module.player_stats.name
                break
        
        if not character_name and hasattr(player1, 'name'):
            character_name = player1.name
        
        if character_name:
            # Check if proficiencies are all zero (indicating they haven't been loaded)
            prof_sys = player1.weapon_proficiency
            all_zero = all(v == 0 for v in prof_sys.wpn_class_proficiency.values()) and all(v == 0 for v in prof_sys.wpn_class_exp.values())
            
            if all_zero:
                print(f"[get_main_player_equipment] Loading weapon proficiencies for {character_name}")
                sync_weapon_proficiency_from_save(player1, character_name)
    except Exception as e:
        print(f"[get_main_player_equipment] Error loading weapon proficiencies: {e}")
    
    # Show current weapon proficiency state for debugging
    if hasattr(player1, 'weapon_proficiency'):
        prof_sys = player1.weapon_proficiency
        nonzero_profs = {k: {'level': v, 'exp': prof_sys.wpn_class_exp.get(k, 0)} 
                        for k, v in prof_sys.wpn_class_proficiency.items() 
                        if v > 0 or prof_sys.wpn_class_exp.get(k, 0) > 0}
        if nonzero_profs:
            print(f"[get_main_player_equipment] Current non-zero proficiencies: {nonzero_profs}")
        else:
            print(f"[get_main_player_equipment] ALL WEAPON PROFICIENCIES ARE ZERO!")
    
    return player1

# Utility functions for weapon proficiency system
def get_player_weapon_proficiency_summary(player_name=None):
    """Get a formatted summary of weapon proficiencies for a player."""
    if player_name is None:
        player = get_main_player_equipment()
    else:
        player_obj = player_equip.get(player_name)
        if not player_obj:
            return f"Player '{player_name}' not found."
        player = player_obj
    
    all_profs = player.get_all_weapon_proficiencies()
    summary = f"=== {player.name}'s Weapon Proficiencies ===\n"
    
    # Group by proficiency level
    by_level = {0: [], 1: [], 2: [], 3: []}
    for weapon_class, info in all_profs.items():
        by_level[info['proficiency']].append((weapon_class, info))
    
    for level in [3, 2, 1, 0]:
        if by_level[level]:
            level_names = {0: "Novice", 1: "Apprentice", 2: "Adept", 3: "Master"}
            summary += f"\n{level_names[level]} (Level {level}):\n"
            for weapon_class, info in by_level[level]:
                if info['experience'] > 0 or level > 0:
                    exp_info = f"{info['experience']} exp"
                    if info['exp_to_next'] != 'Master via weapon master':
                        exp_info += f", {info['exp_to_next']} to next"
                    else:
                        exp_info += f", {info['exp_to_next']}"
                    summary += f"  • {weapon_class}: {exp_info}\n"
    
    return summary

def simulate_weapon_training(weapon_name, hits, player_name=None):
    """Simulate training with a weapon by adding hits."""
    if player_name is None:
        player = get_main_player_equipment()
    else:
        player_obj = player_equip.get(player_name)
        if not player_obj:
            return f"Player '{player_name}' not found."
        player = player_obj
    
    # Find the weapon
    weapon = None
    for eq in player.get_equipment_list():
        if eq.name == weapon_name:
            weapon = eq
            break
    
    if not weapon:
        return f"Weapon '{weapon_name}' not found in {player.name}'s equipment."
    
    if weapon.type != 'weapon':
        return f"'{weapon_name}' is not a weapon."
    
    weapon_class = weapon.get_weapon_class()
    if not weapon_class:
        return f"Could not determine weapon class for '{weapon_name}'."
    
    # Get initial state
    initial_prof = player.get_weapon_proficiency(weapon_class)
    initial_exp = player.get_weapon_experience(weapon_class)
    
    # Add hits
    player.add_weapon_hit(weapon, hits)
    
    # Get final state
    final_prof = player.get_weapon_proficiency(weapon_class)
    final_exp = player.get_weapon_experience(weapon_class)
    
    result = f"Training with {weapon_name} ({weapon_class}):\n"
    result += f"  Added {hits} hits\n"
    result += f"  Experience: {initial_exp} → {final_exp}\n"
    result += f"  Proficiency: {initial_prof} → {final_prof}"
    
    if final_prof > initial_prof:
        level_names = {1: "Apprentice", 2: "Adept"}
        result += f" (Promoted to {level_names.get(final_prof, f'Level {final_prof}')}!)"
    
    return result

def add_combat_experience(player_equip_obj):
    """Add weapon experience after combat based on equipped weapon."""
    if not player_equip_obj or not hasattr(player_equip_obj, 'weapon_proficiency'):
        print("[WeaponTraining] No player equipment object or weapon proficiency system found")
        return
    
    # Find the currently equipped weapon
    equipped_weapon = None
    for eq in player_equip_obj.get_equipment_list():
        if eq.type == 'weapon' and getattr(eq, 'equipped', False):
            equipped_weapon = eq
            break
    
    if not equipped_weapon:
        print("[WeaponTraining] No equipped weapon found")
        return
    
    if not hasattr(equipped_weapon, 'weapon_class') or not equipped_weapon.weapon_class:
        print(f"[WeaponTraining] Weapon '{equipped_weapon.name}' has no weapon class")
        return
    
    # Add 1 hit of experience for the weapon class
    weapon_class = equipped_weapon.weapon_class
    proficiency_system = player_equip_obj.weapon_proficiency
    
    # Get initial state for logging
    initial_prof = proficiency_system.get_proficiency(weapon_class)  
    initial_exp = proficiency_system.get_experience(weapon_class)
    
    # Add experience
    level_up = proficiency_system.add_experience(weapon_class, 1)
    
    # Get final state for logging
    final_prof = proficiency_system.get_proficiency(weapon_class)
    final_exp = proficiency_system.get_experience(weapon_class)
    
    print(f"[WeaponTraining] Combat experience added:")
    print(f"  Weapon: {equipped_weapon.name} ({weapon_class})")
    print(f"  Experience: {initial_exp} → {final_exp}")
    print(f"  Proficiency: {initial_prof} → {final_prof}")
    
    if level_up:
        level_names = {1: "Apprentice", 2: "Adept", 3: "Master"}
        print(f"  🎉 PROFICIENCY INCREASED! Now {level_names.get(final_prof, f'Level {final_prof}')}")
    
    return level_up

def sync_weapon_proficiency_from_save(player_equip_obj, character_name):
    """Sync weapon proficiency data from save file to equipment system"""
    if not player_equip_obj or not hasattr(player_equip_obj, 'weapon_proficiency'):
        print("[WeaponSync] No player equipment object or weapon proficiency system found")
        return False
    
    try:
        # Import Save System
        from Save_System import SaveSystem
        save_system = SaveSystem()
        
        # Load save data
        save_data = save_system.load_save(character_name)
        if not save_data:
            print(f"[WeaponSync] No save data found for {character_name}")
            return False
        
        # Load weapon proficiencies from save data
        if 'weapon_proficiencies' in save_data:
            proficiencies = save_data['weapon_proficiencies']
            print(f"[WeaponSync] Loading weapon proficiencies for {character_name}")
            
            for weapon_class, data in proficiencies.items():
                if weapon_class in player_equip_obj.weapon_proficiency.wpn_class_proficiency:
                    player_equip_obj.weapon_proficiency.wpn_class_proficiency[weapon_class] = data.get('proficiency', 0)
                    player_equip_obj.weapon_proficiency.wpn_class_exp[weapon_class] = data.get('experience', 0)
                    print(f"[WeaponSync] {weapon_class}: Level {data.get('proficiency', 0)}, EXP {data.get('experience', 0)}")
            
            print(f"[WeaponSync] Weapon proficiency data loaded successfully")
            return True
        else:
            print(f"[WeaponSync] No weapon proficiency data in save file for {character_name}")
            return False
            
    except Exception as e:
        print(f"[WeaponSync] Error syncing weapon proficiency: {e}")
        return False

