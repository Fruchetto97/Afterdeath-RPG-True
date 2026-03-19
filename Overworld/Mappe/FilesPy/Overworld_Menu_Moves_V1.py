# Overworld_Menu_Moves_V1.py
# MOVES sub-menu for the overworld pause menu with move creation functionality
#
# MOVE UNLOCK SYSTEM:
# - Players start with 3 moves (level 1 + 2)
# - Gain 1 move slot per level up to maximum of 10 moves
# - New slots are filled with "Basic Attack" placeholder moves
# - Placeholder moves use species' physical element from Species_Config
# - Placeholder structure: 1 Forz scaling, 90% accuracy, NEEDS ARM requirement
#
# INTEGRATION:
# - Call handle_level_up(player_stats) when player levels up
# - System automatically manages move slots when accessing MOVES menu
#
import pygame
import os
import sys
import json

# Add the parent directory to sys.path to import Global_SFX
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import Global_SFX

from Player_Moves import get_player_moves

# Import damage calculation functions from Battle_Menu_Beta_V18
try:
    from Battle_Menu_Beta_V18 import calculate_move_damage, calculate_move_stamina_cost, calculate_move_element
    CALCULATION_AVAILABLE = True
except ImportError:
    CALCULATION_AVAILABLE = False

# Import Status Effects Config
try:
    from Status_Effects_Config import STATUS_EFFECTS_CONFIG, get_effect_cost, is_property_effect
    STATUS_CONFIG_AVAILABLE = True
except ImportError:
    STATUS_CONFIG_AVAILABLE = False

# Import Species Config
try:
    from Species_Config import get_available_effects, get_available_buffs, get_species_config
    SPECIES_CONFIG_AVAILABLE = True
except ImportError:
    SPECIES_CONFIG_AVAILABLE = False

# Import Skills Config
try:
    from Skills_Config import PROFICIENCY_SKILLS
    SKILLS_CONFIG_AVAILABLE = True
except ImportError:
    SKILLS_CONFIG_AVAILABLE = False

# Import Player Equipment for weapon moves
try:
    from Player_Equipment import get_main_player_equipment
    EQUIPMENT_AVAILABLE = True
except ImportError:
    EQUIPMENT_AVAILABLE = False

# Color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
RED = (150, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARK_RED = (139, 0, 0)

def get_active_status_effects(available_effects):
    """Get count of active status effects (non-property effects with level > 0)"""
    count = 0
    for effect in available_effects:
        if effect[1] > 0 and STATUS_CONFIG_AVAILABLE and not is_property_effect(effect[0]):
            count += 1
    return count

def validate_move_rules(custom_move, player_stats):
    """Validate move against creation rules. Returns (is_valid, error_message)"""
    
    # Rule 1: ATK moves need STR >= 1 OR DEX >= 1, unless player has Special_Proficiency
    if custom_move['type'] == 'ATK':
        scaling = custom_move['scaling']
        has_physical_scaling = scaling['forz'] >= 1 or scaling['des'] >= 1
        
        # Check if player has Special_Proficiency skill
        has_special_proficiency = False
        if SKILLS_CONFIG_AVAILABLE and hasattr(player_stats, 'skills'):
            player_skills = getattr(player_stats, 'skills', {})
            has_special_proficiency = player_skills.get('Special_Proficiency', 0) > 0
        
        if not has_physical_scaling and not has_special_proficiency:
            return False, "ATK moves require at least 1 Strength OR 1 Dexterity\n(unless you have Special Proficiency skill)"
    
    # Rule 2: ATK moves with effects/properties must have SPE >= 1 (BUF moves excluded since they don't use scaling)
    if custom_move['type'] == 'ATK':
        has_effects = False
        
        # Check for status effects (only for ATK moves)
        if custom_move.get('effects'):
            for effect in custom_move['effects']:
                if isinstance(effect, list) and len(effect) >= 2 and effect[1] > 0:
                    has_effects = True
                    break
        
        if has_effects and custom_move['scaling']['spe'] < 1:
            return False, "ATK moves with effects require at least 1 Special scaling"
    
    # Rule 3: All moves need at least 1 NEEDS requirement
    requirements = custom_move.get('requirements', [])
    has_needs_requirement = False
    for req in requirements:
        if req.startswith('NEEDS'):
            has_needs_requirement = True
            break
    
    if not has_needs_requirement:
        return False, "All moves require at least one NEEDS requirement\n(body parts needed to execute the move)"
    
    return True, ""

def get_element_description(current_section, sections, custom_move, available_effects, effects_selected, 
                          available_requirements, requirements_selected, available_buffs, buffs_selected,
                          scaling_selected, scaling_names, accuracy_options, accuracy_selected, in_top_row):
    """Get description for currently selected element in move customization"""
    
    if current_section < 0 or current_section >= len(sections):
        return "Navigate between sections", ""
    
    section_name = sections[current_section]
    
    # If we're in the top row (section selection), show section descriptions
    if in_top_row:
        if section_name == "Scaling":
            return "Scaling", "Choose how the move's power scales with your stats. Select attributes that determine effectiveness."
        elif section_name == "Accuracy":
            return "Accuracy", "Set how likely the move is to hit targets. Higher accuracy means more reliable attacks, but increases the stamina cost."
        elif section_name == "Effects":
            return "Effects", "Add special effects to your move. Effects can inflict status conditions, like bleeding, burn and poison, or give the move special properties, like being ranged, hitting multiple targets, or bypassing defence."
        elif section_name == "Buffs":
            return "Buffs", "Add beneficial status effects to your move. Buffs enhance your character's capabilities."
        elif section_name == "Requirements":
            return "Requirements", "Set what's needed to use this move. Includes body parts requirements and conditions."
        elif section_name == "Confirm":
            return "Confirm", "Review your move's details and finalize the creation. Check all settings before saving."
        else:
            return section_name, f"Configure {section_name.lower()} settings for your custom move."
    
    # If we're not in top row, show element-specific descriptions
    if section_name == "Scaling":
        if scaling_selected < len(scaling_names):
            selected_stat = scaling_names[scaling_selected]
            if selected_stat == "forz":
                return "Strength (STR)", "Strength scaling represents the how reliant the move is on strength. Damage increases with higher STR values. Attack moves require at least 1 STR or DEX."
            elif selected_stat == "des":
                return "Dexterity (DEX)", "Dexterity scaling represents the how reliant the move is on dexterity. Damage increases with higher DEX values. Attack moves require at least 1 STR or DEX."
            elif selected_stat == "spe":
                return "Special (SPE)", "Special scaling represents the how reliant the move is on species-specific abilities. Damage increases with higher SPE values. Moves with effects require at least 1 SPE."
        return "Scaling Selection", "Choose how much each stat contributes to this move's power."
    
    elif section_name == "Accuracy":
        if accuracy_selected < len(accuracy_options):
            acc_value = accuracy_options[accuracy_selected]
            return f"Accuracy: {acc_value}%", f"Chance for this move to hit successfully. {acc_value}% means the move will hit {acc_value} times out of 100 attempts on average. \n 100% costs 1 STM \n 90% costs 0 STM \n 50% costs -1 STM \n 30% costs -2 STM."
        return "Accuracy Selection", "Choose how likely this move is to hit its target."
    
    elif section_name == "Effects":
        if effects_selected < len(available_effects):
            effect_name = available_effects[effects_selected][0]
            effect_level = available_effects[effects_selected][1]
            
            # Try to get description from Status Effects Config
            if STATUS_CONFIG_AVAILABLE and effect_name in STATUS_EFFECTS_CONFIG:
                effect_data = STATUS_EFFECTS_CONFIG[effect_name]
                desc = effect_data.get('description', 'No description available')
                cost_info = ""
                if 'cost' in effect_data:
                    cost_info = f"\nCost: {effect_data['cost']} per level"
                elif 'cost_per_level' in effect_data:
                    cost_info = f"\nCost: {effect_data['cost_per_level']} per level"
                return f"{effect_name.title()} (Level {effect_level})", desc + cost_info
            else:
                # Fallback descriptions for common effects
                fallback_descriptions = {
                    "poison": "Deals damage over time to the target.",
                    "burn": "Causes fire damage over multiple turns.",
                    "freeze": "Prevents target from acting for several turns.",
                    "paralysis": "Reduces target's ability to move and act.",
                    "regeneration": "Slowly heals the target over time.",
                    "bleeding": "Causes continuous health loss.",
                    "stunning": "Temporarily prevents target from taking actions."
                }
                desc = fallback_descriptions.get(effect_name.lower(), "A special effect that modifies combat behavior.")
                return f"{effect_name.title()} (Level {effect_level})", desc + "\nCost: Variable per level"
        return "Status Effects", "Choose special effects that your move will apply to targets. You can choose up to 1 status effect and 1 property effect for each move."
    
    elif section_name == "Buffs":
        if buffs_selected < len(available_buffs):
            buff_name = available_buffs[buffs_selected][0]
            buff_level = available_buffs[buffs_selected][1]
            
            # Buff descriptions - handle various buff name formats
            buff_descriptions = {
                "strength": "Temporarily increases physical attack power.",
                "dexterity": "Temporarily increases agility and precision.",
                "special": "Temporarily increases magical/special abilities.",
                "defense": "Temporarily increases resistance to damage.",
                "speed": "Temporarily increases movement and reaction speed.",
                "health": "Temporarily increases maximum health points.",
                "stamina": "Temporarily increases maximum stamina points.",
                "forz": "Temporarily increases physical attack power (strength).",
                "des": "Temporarily increases agility and precision (dexterity).",
                "spe": "Temporarily increases magical/special abilities (special)."
            }
            # Try multiple name formats to match buff names
            desc = (buff_descriptions.get(buff_name.lower()) or 
                   buff_descriptions.get(buff_name.title().lower()) or
                   buff_descriptions.get(buff_name) or
                   "A beneficial effect that enhances abilities.")
            return f"{buff_name.title()} Buff (Level {buff_level})", desc + f"\nLevel: {buff_level}"
        return "Buffs Selection", "Choose beneficial effects for BUF-type moves."
    
    elif section_name == "Requirements":
        if requirements_selected < len(available_requirements):
            req_name = available_requirements[requirements_selected]
            
            # Requirement descriptions
            req_descriptions = {
                "NEEDS ARM": "If selected, the move will require at least one functional arm to execute.",
                "NEEDS LEG": "If selected, the move will require at least one functional leg to execute.",
                "NEEDS 2 ARMS": "If selected, the move will require both arms to be functional to execute.",
                "NEEDS 2 LEGS": "If selected, the move will require both legs to be functional to execute.",
                "NEEDS HEAD": "If selected, the move will require the head to be functional to execute.",
                "NEEDS BODY": "If selected, the move will require the body/torso to be functional to execute.",
                "NEEDS EXTRA_LIMB": "If selected, the move will require species-specific extra limbs to execute."
            }
            desc = req_descriptions.get(req_name, "A body part requirement for executing this move.")
            return req_name, desc + "\nAll moves must have at least one NEEDS requirement."
        return "Requirements", "Choose which body parts are needed to execute this move."
    
    elif section_name == "Confirm":
        move_type = custom_move.get('type', 'UNKNOWN')
        if move_type == 'ATK':
            return "Attack Move Ready", "Review your attack move before saving. Check scaling, accuracy, effects, and requirements."
        elif move_type == 'BUF':
            return "Buff Move Ready", "Review your buff move before saving. Check buffs and requirements."
        else:
            return "Move Ready", "Review your move configuration before saving."
    
    return "Move Customization", "Use the interface to customize your move's properties."

def get_active_property_effects(available_effects):
    """Get count of active property effects (property effects with level > 0)"""
    count = 0
    for effect in available_effects:
        if effect[1] > 0 and STATUS_CONFIG_AVAILABLE and is_property_effect(effect[0]):
            count += 1
    return count

def validate_accuracy(accuracy):
    """Validate and convert accuracy to one of the supported values (30, 50, 90, 100)"""
    supported_accuracies = [30, 50, 90, 100]
    
    # If accuracy is already in the supported list, return it
    if accuracy in supported_accuracies:
        return accuracy
    
    # Find the closest supported accuracy value
    closest = min(supported_accuracies, key=lambda x: abs(x - accuracy))
    return closest

def calculate_move_damage_and_stamina(player_stats, move):
    """Calculate damage and stamina cost for a move using Battle Menu formulas"""
    if not CALCULATION_AVAILABLE:
        return "N/A", "N/A"
    
    if not player_stats:
        return "No Stats", "No Stats"
    
    try:        
        # Handle BUF moves using the proper BUF formula
        if move.get('type') == 'BUF':
            effects_to_use = []
            effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
            
            # Check for buffs field first (preferred for newer moves)
            if 'buffs' in move and move['buffs']:
                # Use buffs field directly
                for buff in move['buffs']:
                    if isinstance(buff, list) and len(buff) >= 2:
                        buff_name = buff[0]
                        buff_level = buff[1]
                        
                        if buff_level > 0:  # Only add buffs with level > 0
                            # Handle Effect-on-Hit buffs specially
                            if buff_name in effect_on_hit_buffs:
                                effects_to_use.append([buff_name, buff_level, 999, 0])
                            else:
                                # Regular buffs need 'buf_' prefix
                                prefixed_name = f"buf_{buff_name}"
                                effects_to_use.append([prefixed_name, buff_level, 2, 0])
            
            elif 'effects' in move and move['effects']:
                # Fallback to effects field (for BUF moves from Player_Moves.py)
                # Use the same logic as the move creation menu conversion
                for effect in move['effects']:
                    if isinstance(effect, list) and len(effect) >= 2:
                        effect_name = effect[0]
                        effect_level = effect[1]
                        
                        if effect_level > 0:  # Only add effects with level > 0
                            # Effects in BUF moves are already in the correct format
                            effects_to_use.append([effect_name, effect_level, effect[2] if len(effect) > 2 else 2, effect[3] if len(effect) > 3 else 0])
                    elif isinstance(effect, str) and effect:
                        # Handle string-only effects as level 1
                        effects_to_use.append([effect, 1, 2, 0])
            
            else:
                # If no buffs or effects found, initialize empty buffs field for move editing
                move['buffs'] = [['forz', 0], ['des', 0], ['spe', 0]]
            
            # Use the proper BUF stamina calculation function from battle system
            stamina_cost = calculate_move_stamina_cost(
                move['scaling']['forz'],
                move['scaling']['des'],
                move['scaling']['spe'],
                effects_to_use,
                move.get('requirements', []),
                move.get('accuracy', 100),
                move_type="BUF"  # Pass move type for proper calculation
            )
            
            return "Buff", stamina_cost
        
        # For ATK moves, use original calculation
        # Create a mock character object for calculation
        class MockCharacter:
            def __init__(self, stats):
                # Try to get stats directly if they're accessible
                if hasattr(stats, 'forz'):
                    self.forz = stats.forz
                    self.des = stats.des
                    self.spe = stats.spe
                else:                    
                    # Try multiple possible attribute names for each stat
                    possible_forz = ['forz', 'strength', 'str', 'force', 'attack', 'atk']
                    possible_des = ['des', 'dexterity', 'dex', 'agility', 'agi']
                    possible_spe = ['spe', 'special', 'int', 'intelligence', 'magic', 'mag']
                    
                    self.forz = 0
                    self.des = 0
                    self.spe = 0
                    
                    # Try to find strength/forz
                    for attr in possible_forz:
                        if hasattr(stats, attr):
                            self.forz = getattr(stats, attr, 0)
                            break
                    
                    # Try to find dexterity/des
                    for attr in possible_des:
                        if hasattr(stats, attr):
                            self.des = getattr(stats, attr, 0)
                            break
                    
                    # Try to find special/spe
                    for attr in possible_spe:
                        if hasattr(stats, attr):
                            self.spe = getattr(stats, attr, 0)
                            break
                    
                    # If all stats are 0, try some default values for testing
                    if self.forz == 0 and self.des == 0 and self.spe == 0:
                        self.forz = 10  # Test value
                        self.des = 10   # Test value  
                        self.spe = 10   # Test value
        
        mock_char = MockCharacter(player_stats)
        
        # Calculate damage
        damage = calculate_move_damage(
            mock_char,
            move['scaling']['forz'],
            move['scaling']['des'], 
            move['scaling']['spe']
        )
        
        # Calculate stamina cost
        stamina_cost = calculate_move_stamina_cost(
            move['scaling']['forz'],
            move['scaling']['des'],
            move['scaling']['spe'],
            move.get('effects', []),
            move.get('requirements', []),
            move.get('accuracy', 100),
            move_type=move.get('type', 'ATK')  # Pass move type for proper calculation
        )
        
        return damage, stamina_cost
        
    except Exception as e:
        return "Error", "Error"

def draw_rounded_rect(surface, color, rect, radius=10):
    """Draw a rounded rectangle"""
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def get_mandatory_requirement_for_buff(buff_name):
    """Get the mandatory requirement for a specific buff, if any"""
    mandatory_requirements = {
        'dodge': 'NEEDS 2 LEGS',
        'shield': 'NEEDS ARM'
    }
    return mandatory_requirements.get(buff_name.lower())

def get_active_buffs(available_buffs):
    """Get list of active buffs (level > 0) from available buffs"""
    active_buffs = []
    for buff in available_buffs:
        if len(buff) >= 2 and buff[1] > 0:  # buff = [name, level]
            active_buffs.append(buff[0].lower())
    return active_buffs

def get_mandatory_requirements(available_buffs):
    """Get all mandatory requirements based on active buffs"""
    active_buffs = get_active_buffs(available_buffs)
    mandatory_reqs = []
    
    for buff_name in active_buffs:
        req = get_mandatory_requirement_for_buff(buff_name)
        if req and req not in mandatory_reqs:
            mandatory_reqs.append(req)
    
    return mandatory_reqs

def is_requirement_mandatory(requirement, available_buffs):
    """Check if a requirement is mandatory based on current active buffs"""
    mandatory_reqs = get_mandatory_requirements(available_buffs)
    return requirement in mandatory_reqs

def has_active_mandatory_buffs(available_buffs):
    """Check if any buffs with mandatory requirements are active"""
    active_buffs = get_active_buffs(available_buffs)
    mandatory_buffs = ['dodge', 'shield']
    
    for buff_name in active_buffs:
        if buff_name in mandatory_buffs:
            return True
    return False

def show_mandatory_requirement_error(screen, font, requirement_type):
    """Show error message when trying to remove a mandatory requirement"""
    if requirement_type == 'NEEDS 2 LEGS':
        message = "2 Legs are required to dodge"
    elif requirement_type == 'NEEDS ARM':
        message = "1 Arm is required for shield"
    else:
        message = f"{requirement_type} is required"
    
    # Create wider dialog to fit the text
    text_surface = font.render(message, True, WHITE)
    dialog_width = max(400, text_surface.get_width() + 60)
    dialog_height = 120
    
    # Center on screen
    screen_width, screen_height = screen.get_size()
    dialog_x = (screen_width - dialog_width) // 2
    dialog_y = (screen_height - dialog_height) // 2
    
    # Draw dialog background
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(screen, (40, 40, 60), dialog_rect, border_radius=15)
    pygame.draw.rect(screen, (255, 0, 0), dialog_rect, 3, border_radius=15)  # Red border
    
    # Draw message text
    text_x = dialog_x + (dialog_width - text_surface.get_width()) // 2
    text_y = dialog_y + 30
    screen.blit(text_surface, (text_x, text_y))
    
    # Draw OK instruction
    ok_text = font.render("Press any key to continue", True, (200, 200, 200))
    ok_x = dialog_x + (dialog_width - ok_text.get_width()) // 2
    ok_y = dialog_y + 70
    screen.blit(ok_text, (ok_x, ok_y))
    
    pygame.display.flip()
    
    # Wait for key press
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                waiting = False

def draw_confirmation_dialog(screen, message, font, selected_option=0):
    """Draw a confirmation dialog with rounded edges and red border"""
    screen_width, screen_height = screen.get_size()
    
    # Dialog dimensions
    dialog_width = 400
    dialog_height = 150
    dialog_x = (screen_width - dialog_width) // 2
    dialog_y = (screen_height - dialog_height) // 2
    
    # Create dialog surface with alpha
    dialog_surface = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
    
    # Draw rounded background (dark with red border)
    draw_rounded_rect(dialog_surface, BLACK, (5, 5, dialog_width-10, dialog_height-10), 15)
    draw_rounded_rect(dialog_surface, RED, (0, 0, dialog_width, dialog_height), 15)
    draw_rounded_rect(dialog_surface, BLACK, (3, 3, dialog_width-6, dialog_height-6), 12)
    
    # Draw message
    text_surface = font.render(message, True, WHITE)
    text_rect = text_surface.get_rect(center=(dialog_width//2, 40))
    dialog_surface.blit(text_surface, text_rect)
    
    # Draw options
    options = ["No", "Yes"]
    option_y = 80
    for i, option in enumerate(options):
        color = RED if i == selected_option else WHITE
        option_surface = font.render(option, True, color)
        option_x = 100 + i * 200
        option_rect = option_surface.get_rect(center=(option_x, option_y))
        dialog_surface.blit(option_surface, option_rect)
    
    # Draw instructions
    instruction = "A/D to select, SPACE to confirm, ESC to cancel"
    instruction_surface = pygame.font.Font(None, 20).render(instruction, True, GRAY)
    instruction_rect = instruction_surface.get_rect(center=(dialog_width//2, 120))
    dialog_surface.blit(instruction_surface, instruction_rect)
    
    # Blit to main screen
    screen.blit(dialog_surface, (dialog_x, dialog_y))
    
    return (dialog_x, dialog_y, dialog_width, dialog_height)

# --- Controller Support Functions ---
def is_controller_button_just_pressed(event, button_name):
    """Check if controller button was just pressed (for events)"""
    if event.type == pygame.JOYBUTTONDOWN:
        button_map = {
            'x': 0, 'circle': 1, 'square': 2, 'triangle': 3,
            'l1': 4, 'r1': 5, 'l2': 6, 'r2': 7,
            'share': 8, 'options': 9, 'l3': 10, 'r3': 11,
            'ps': 12, 'touchpad': 13
        }
        return event.button == button_map.get(button_name, -1)
    return False

def is_controller_hat_just_moved(event, direction):
    """Check if controller D-pad was just moved in direction"""
    if event.type == pygame.JOYHATMOTION and event.hat == 0:
        if direction == 'up' and event.value[1] == 1:
            return True
        elif direction == 'down' and event.value[1] == -1:
            return True
        elif direction == 'left' and event.value[0] == -1:
            return True
        elif direction == 'right' and event.value[0] == 1:
            return True
    return False

def get_unified_menu_input():
    """Get unified input from keyboard and controller for menus"""
    keys = pygame.key.get_pressed()
    
    # Initialize controller if needed
    pygame.joystick.init()
    controller = None
    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        if not controller.get_init():
            controller.init()
    
    # Get D-pad input
    dpad_up = dpad_down = dpad_left = dpad_right = False
    if controller:
        hat = controller.get_hat(0)
        dpad_up = hat[1] == 1
        dpad_down = hat[1] == -1
        dpad_left = hat[0] == -1
        dpad_right = hat[0] == 1
    
    return {
        'up': keys[pygame.K_UP] or keys[pygame.K_w] or dpad_up,
        'down': keys[pygame.K_DOWN] or keys[pygame.K_s] or dpad_down,
        'left': keys[pygame.K_LEFT] or keys[pygame.K_a] or dpad_left,
        'right': keys[pygame.K_RIGHT] or keys[pygame.K_d] or dpad_right,
        'select': keys[pygame.K_RETURN] or keys[pygame.K_SPACE] or keys[pygame.K_z],
        'back': keys[pygame.K_ESCAPE] or keys[pygame.K_x]
    }

def open_moves_menu(screen_width, screen_height, menu_box_width, menu_box_height, game_settings, player_stats=None):
    """
    Open and handle the moves submenu using overlay approach with move customization
    Returns: True to continue game, False to quit
    """
    # Calculate menu box position
    menu_box_x = (screen_width - menu_box_width) // 2
    menu_box_y = (screen_height - menu_box_height) // 2
    
    # Get main display surface
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    
    # Load sounds using Global_SFX pattern
    Global_SFX.load_global_sfx_volume()  # Ensure latest SFX volume is loaded
    try:
        navigation_sound = Global_SFX.load_sound_with_global_volume(
            r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\Selection_Normal.wav"
        )
        cancel_sound = Global_SFX.load_sound_with_global_volume(
            r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\Esc_Sound.wav"
        )
    except:
        navigation_sound = None
        cancel_sound = None
    
    # Get moves data - ensure player has correct number of move slots based on level
    moves_list = ensure_move_slots(player_stats)
    
    # Performance optimization: Pre-calculate damage and stamina for all moves to avoid lag
    moves_cache = {}
    for i, move in enumerate(moves_list):
        damage, stamina_cost = calculate_move_damage_and_stamina(player_stats, move) if player_stats else ("N/A", "N/A")
        moves_cache[i] = {'damage': damage, 'stamina': stamina_cost}
    
    # Load background PNG for the moves menu
    moves_png_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Menus\Pause_Menu_Moves_V1.png"
    try:
        moves_png = pygame.image.load(moves_png_path).convert_alpha()
    except Exception as e:
        moves_png = None
    
    # Load font
    font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
    if os.path.exists(font_path):
        font = pygame.font.Font(font_path, 24)
        title_font = pygame.font.Font(font_path, 32)
        small_font = pygame.font.Font(font_path, 18)
    else:
        font = pygame.font.Font(None, 24)
        title_font = pygame.font.Font(None, 32)
        small_font = pygame.font.Font(None, 18)
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    GRAY = (128, 128, 128)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    
    # Menu state - adjust based on menu box height
    selected_move = 0
    scroll_offset = 0
    # Calculate max visible moves based on menu box height
    title_height = 80  # Space for title
    instruction_height = 80  # Space for instructions at bottom
    available_height = menu_box_height - title_height - instruction_height
    move_display_height = 110  # Height per move (increased for separator line spacing)
    max_visible_moves = max(3, min(8, available_height // move_display_height))  # Between 3 and 8 moves
    
    # Input timing - reduced for better responsiveness  
    last_input_time = 0
    input_delay = 120  # milliseconds (further reduced for better responsiveness)
    
    # Frame rate control for better performance
    clock = pygame.time.Clock()
    
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle navigation with event-based input for controller
            elif is_controller_button_just_pressed(event, 'circle') or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if cancel_sound:
                    cancel_sound.play()
                running = False
            
            elif (is_controller_hat_just_moved(event, 'up') or 
                  (event.type == pygame.KEYDOWN and event.key in [pygame.K_UP, pygame.K_w])):
                if current_time - last_input_time > input_delay:
                    if moves_list:
                        if navigation_sound:
                            navigation_sound.play()
                        selected_move = (selected_move - 1) % len(moves_list)
                        
                        # Handle wrapping: if we went from 0 to last item, scroll to end
                        if selected_move == len(moves_list) - 1 and len(moves_list) > max_visible_moves:
                            scroll_offset = len(moves_list) - max_visible_moves
                        # Normal scroll up
                        elif selected_move < scroll_offset:
                            scroll_offset = selected_move
                    last_input_time = current_time
            
            elif (is_controller_hat_just_moved(event, 'down') or 
                  (event.type == pygame.KEYDOWN and event.key in [pygame.K_DOWN, pygame.K_s])):
                if current_time - last_input_time > input_delay:
                    if moves_list:
                        if navigation_sound:
                            navigation_sound.play()
                        selected_move = (selected_move + 1) % len(moves_list)
                        
                        # Handle wrapping: if we went from last to first item, scroll to beginning
                        if selected_move == 0 and len(moves_list) > max_visible_moves:
                            scroll_offset = 0
                        # Normal scroll down
                        elif selected_move >= scroll_offset + max_visible_moves:
                            scroll_offset = selected_move - max_visible_moves + 1
                    last_input_time = current_time
            
            # Handle spacebar for move customization
            elif (is_controller_button_just_pressed(event, 'x') or 
                  (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)):
                if moves_list and current_time - last_input_time > input_delay:
                    selected_move_data = moves_list[selected_move]
                    
                    # Check if this is a weapon move (WPN flag)
                    if is_weapon_move(selected_move_data):
                        print(f"[MovesMenu] Cannot edit weapon move: {selected_move_data['name']}")
                        # Show a message that weapon moves cannot be edited
                        show_weapon_move_warning(screen, font)
                    else:
                        # Show confirmation dialog for custom moves
                        confirmation_result = show_move_customization_confirmation(screen, selected_move_data['name'], font)
                        if confirmation_result:
                            # Open move customization menu
                            new_move = open_move_customization_menu(screen, selected_move_data, player_stats, font, small_font, menu_box_width, menu_box_height, menu_box_x, menu_box_y)
                            if new_move:
                                # Replace the move in the moves list
                                moves_list[selected_move] = new_move
                                # Update cache for the modified move
                                damage, stamina_cost = calculate_move_damage_and_stamina(player_stats, new_move) if player_stats else ("N/A", "N/A")
                                moves_cache[selected_move] = {'damage': damage, 'stamina': stamina_cost}
                                # Save the updated moves to the save file (only custom moves)
                                custom_moves_only = [move for move in moves_list if not is_weapon_move(move)]
                                save_custom_moves(custom_moves_only, player_stats)
                            save_custom_moves(moves_list, player_stats)
                    last_input_time = current_time
        
        # Create transparent overlay (like stats menu)
        overlay = pygame.Surface((menu_box_width, menu_box_height), pygame.SRCALPHA)
        
        # Draw PNG background on overlay if available
        if moves_png:
            # Scale PNG to fill the entire menu box
            moves_surface = pygame.transform.smoothscale(moves_png, (menu_box_width, menu_box_height))
            
            # Use PNG as primary background (fully opaque)
            overlay.blit(moves_surface, (0, 0))
        else:
            # Fallback to semi-transparent base if PNG not available
            overlay.fill((30, 30, 40, 180))
        
        # Draw title on overlay
        title_text = title_font.render("MOVES", True, WHITE)
        title_rect = title_text.get_rect(center=(menu_box_width // 2, 50))
        overlay.blit(title_text, title_rect)
        
        # Draw moves list on overlay
        if moves_list:
            start_y = 80  # Adjusted for better spacing
            move_height = move_display_height  # Use calculated height
            
            # Calculate visible range
            visible_start = scroll_offset
            visible_end = min(scroll_offset + max_visible_moves, len(moves_list))
            
            for i in range(visible_start, visible_end):
                move = moves_list[i]
                y_pos = start_y + (i - scroll_offset) * move_height
                
                # No highlight rectangle - just change text color for selected move
                name_color = BLACK if i == selected_move else WHITE
                
                # Use cached damage and stamina for better performance
                damage, stamina_cost = moves_cache[i]['damage'], moves_cache[i]['stamina']
                
                # Move name with selection coloring and WPN flag for weapon moves
                move_name = move['name']
                if is_weapon_move(move):
                    move_name += " [WPN]"
                name_text = font.render(move_name, True, name_color)
                overlay.blit(name_text, (50, y_pos))
                
                # Move type (increased spacing)
                type_color = GREEN if move['type'] == 'ATK' else BLUE if move['type'] == 'BUF' else WHITE
                type_text = small_font.render(f"Type: {move['type']}", True, type_color)
                overlay.blit(type_text, (50, y_pos + 28))  # Increased spacing
                
                # For BUF moves: don't show scaling, accuracy, or damage 
                if move['type'] != 'BUF':
                    # Scaling info (only for non-BUF moves)
                    scaling = move['scaling']
                    scaling_text = small_font.render(
                        f"STR: {scaling['forz']} | DEX: {scaling['des']} | SPE: {scaling['spe']}", 
                        True, WHITE
                    )
                    overlay.blit(scaling_text, (50, y_pos + 48))  # Increased spacing
                    
                    # MIDDLE COLUMN: Accuracy (only for non-BUF moves) - moved right by 50% of PNG width
                    middle_column_x = min(320, menu_box_width // 2 - 50) + (menu_box_width // 4)  # Move right by 50% of PNG width
                    accuracy_text = small_font.render(f"Accuracy: {move['accuracy']}%", True, WHITE)
                    overlay.blit(accuracy_text, (middle_column_x, y_pos + 28))
                    
                    # RIGHT COLUMN: Damage (only for non-BUF moves)
                    right_column_x = menu_box_width - 120  # Move to near the right edge of the menu
                    damage_text = small_font.render(f"DMG: {damage}", True, YELLOW)
                    overlay.blit(damage_text, (right_column_x, y_pos + 28))
                else:
                    # For BUF moves, position requirements and stamina cost differently
                    middle_column_x = min(320, menu_box_width // 2 - 50) + (menu_box_width // 4)  # Same adjustment
                    right_column_x = menu_box_width - 120
                
                # Requirements (for all moves)
                if move['requirements']:
                    req_text = small_font.render(f"Req: {', '.join(move['requirements'][:4])}", True, GRAY)  # Limit to 4 for space
                    if move['type'] == 'BUF':
                        overlay.blit(req_text, (50, y_pos + 48))  # Move to left for BUF moves
                    else:
                        overlay.blit(req_text, (middle_column_x, y_pos + 48))  # Middle for non-BUF moves
                
                # Stamina Cost (for all moves)
                stamina_text = small_font.render(f"STA: {stamina_cost}", True, RED)
                if move['type'] == 'BUF':
                    overlay.blit(stamina_text, (right_column_x, y_pos + 28))  # Right position for BUF moves (third column)
                else:
                    overlay.blit(stamina_text, (right_column_x, y_pos + 48))  # Right position for non-BUF moves
                
                # Draw horizontal line between moves (except for the last visible move)
                if i < visible_end - 1:  # Don't draw line after the last visible move
                    line_y = y_pos + 95  # Position line well after all move content
                    line_start_x = 40  # Start a bit from the left edge
                    line_end_x = menu_box_width - 40  # End a bit from the right edge
                    pygame.draw.line(overlay, (120, 120, 120), (line_start_x, line_y), (line_end_x, line_y), 2)
                
                # Effects (left side, increased spacing) - format depends on move type
                if move['effects']:
                    effects_list = []
                    for effect in move['effects'][:2]:  # Limit to 2 for space
                        if isinstance(effect, list) and len(effect) >= 3:
                            # New format: [name, level, duration, immunity]
                            name, level, duration = effect[0], effect[1], effect[2]
                            
                            # Check if this is a property effect
                            if STATUS_CONFIG_AVAILABLE and is_property_effect(name):
                                # Property effects: show only name (no level/duration)
                                effects_list.append(f"{name}")
                            elif move['type'] == 'BUF':
                                # For BUF moves: only show name and level (no duration)
                                effects_list.append(f"{name} L{level}")
                            else:
                                # For other moves: show name, level, and duration
                                effects_list.append(f"{name} L{level} ({duration}t)")
                        elif isinstance(effect, list) and len(effect) >= 1:
                            # Partial format: just name
                            effects_list.append(f"{effect[0]}")
                        else:
                            # String format
                            effects_list.append(str(effect))
                    effects_str = ", ".join(effects_list)
                    effects_text = small_font.render(f"Effects: {effects_str}", True, RED)
                    overlay.blit(effects_text, (50, y_pos + 68))
                
                # Elements (middle column, increased spacing) - hide for BUF moves
                if move['elements'] and move.get('type') != 'BUF':
                    elements_text = small_font.render(f"Elements: {', '.join(move['elements'][:2])}", True, YELLOW)  # Limit for space
                    overlay.blit(elements_text, (middle_column_x, y_pos + 68))
            
            # Draw scroll indicator if needed
            if len(moves_list) > max_visible_moves:
                # Scroll bar with proper dimensions
                scroll_area_height = max_visible_moves * move_height
                scroll_bar_width = 8
                scroll_bar_x = menu_box_width - 20
                scroll_bar_height = max(15, int(scroll_area_height * max_visible_moves / len(moves_list)))
                
                if len(moves_list) > max_visible_moves:
                    scroll_ratio = scroll_offset / (len(moves_list) - max_visible_moves)
                else:
                    scroll_ratio = 0
                    
                scroll_bar_y = start_y + int(scroll_ratio * (scroll_area_height - scroll_bar_height))
                
                # Draw scroll track
                pygame.draw.rect(overlay, GRAY, (scroll_bar_x, start_y, scroll_bar_width, scroll_area_height))
                # Draw scroll thumb
                pygame.draw.rect(overlay, WHITE, (scroll_bar_x, scroll_bar_y, scroll_bar_width, scroll_bar_height))
        else:
            # No moves message
            no_moves_text = font.render("No moves available", True, WHITE)
            no_moves_rect = no_moves_text.get_rect(center=(menu_box_width // 2, menu_box_height // 2))
            overlay.blit(no_moves_text, no_moves_rect)
        
        # Draw instructions on overlay
        instructions = [
            "Up/Down Navigate | Space/x: Customize Move | Esc/Circle: go Back"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_text = small_font.render(instruction, True, WHITE)
            overlay.blit(inst_text, (20, menu_box_height - 60 + i * 20))
        
        # Draw move count on overlay
        count_text = small_font.render(f"Total Moves: {len(moves_list)}", True, WHITE)
        overlay.blit(count_text, (menu_box_width - 200, menu_box_height - 40))
        
        # Blit overlay on top of game (like stats menu)
        screen.blit(overlay, (menu_box_x, menu_box_y))
        pygame.display.flip()
        clock.tick(60)
    
    return True  # Continue game

def show_move_customization_confirmation(screen, move_name, font):
    """Show confirmation dialog for move customization"""
    clock = pygame.time.Clock()
    selected_option = 0  # 0 = No, 1 = Yes
    last_input_time = 0
    input_delay = 200
    
    while True:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE and current_time - last_input_time > input_delay:
                    return selected_option == 1
                elif event.key in [pygame.K_a, pygame.K_LEFT] and current_time - last_input_time > input_delay:
                    selected_option = 0
                    last_input_time = current_time
                elif event.key in [pygame.K_d, pygame.K_RIGHT] and current_time - last_input_time > input_delay:
                    selected_option = 1
                    last_input_time = current_time
        
        # Draw overlay with confirmation dialog
        draw_confirmation_dialog(screen, f"change the move?", font, selected_option)
        pygame.display.flip()
        clock.tick(60)

def handle_name_input(event, custom_move, char_grid, selected_char_row, selected_char_col, uppercase_mode, max_name_length):
    """Handle keyboard input for name editing - returns updated values"""
    new_selected_char_row = selected_char_row
    new_selected_char_col = selected_char_col
    new_uppercase_mode = uppercase_mode
    name_changed = False
    
    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
        new_selected_char_col = (selected_char_col - 1) % len(char_grid[0])
    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
        new_selected_char_col = (selected_char_col + 1) % len(char_grid[0])
    elif event.key == pygame.K_UP or event.key == pygame.K_w:
        new_selected_char_row = (selected_char_row - 1) % len(char_grid)
    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
        new_selected_char_row = (selected_char_row + 1) % len(char_grid)
    elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
        char = char_grid[selected_char_row][selected_char_col]
        if char == 'Del':  # Delete/backspace
            if len(custom_move['name']) > 0:
                custom_move['name'] = custom_move['name'][:-1]
                name_changed = True
        elif char == 'Ok':  # Confirm name and exit
            return new_selected_char_row, new_selected_char_col, new_uppercase_mode, name_changed, True
        elif char == 'Spc':  # Space
            if len(custom_move['name']) < max_name_length:
                custom_move['name'] += ' '
                name_changed = True
        elif char == 'Lwr':  # Switch to lowercase
            new_uppercase_mode = False
        elif char == 'Upr':  # Switch to uppercase
            new_uppercase_mode = True
        elif char not in ['Del', 'Ok', 'Spc', 'Lwr', 'Upr']:  # Regular character
            if len(custom_move['name']) < max_name_length:
                custom_move['name'] += char
                name_changed = True
    elif event.key == pygame.K_ESCAPE:
        # ESC key exits name editing without saving
        return new_selected_char_row, new_selected_char_col, new_uppercase_mode, name_changed, True
    
    return new_selected_char_row, new_selected_char_col, new_uppercase_mode, name_changed, False

def draw_name_editing_keyboard(surface, char_grid, selected_char_row, selected_char_col, font, small_font, custom_move):
    """Draw the character selection keyboard for name editing"""
    # Draw keyboard background only (no full-screen overlay to preserve overworld background)
    keyboard_width = 500
    keyboard_height = 300
    keyboard_x = (surface.get_width() - keyboard_width) // 2
    keyboard_y = (surface.get_height() - keyboard_height) // 2
    
    # Draw a semi-transparent background only for the keyboard area
    keyboard_surface = pygame.Surface((keyboard_width, keyboard_height), pygame.SRCALPHA)
    keyboard_surface.fill((40, 40, 40, 220))  # Semi-transparent dark background
    surface.blit(keyboard_surface, (keyboard_x, keyboard_y))
    
    # Draw keyboard border
    pygame.draw.rect(surface, (150, 150, 150), (keyboard_x, keyboard_y, keyboard_width, keyboard_height), 3, border_radius=10)
    
    # Title
    title_text = font.render("Edit Move Name", True, (255, 255, 255))
    title_x = keyboard_x + (keyboard_width - title_text.get_width()) // 2
    surface.blit(title_text, (title_x, keyboard_y + 10))
    
    # Current name display
    name_text = small_font.render(f"Name: {custom_move['name']}", True, (200, 200, 200))
    name_x = keyboard_x + (keyboard_width - name_text.get_width()) // 2
    surface.blit(name_text, (name_x, keyboard_y + 40))
    
    # Draw character grid
    char_width = 40
    char_height = 35
    start_x = keyboard_x + 20
    start_y = keyboard_y + 80
    
    for row_idx, row in enumerate(char_grid):
        for col_idx, char in enumerate(row):
            char_x = start_x + col_idx * (char_width + 5)
            char_y = start_y + row_idx * (char_height + 5)
            
            # Highlight selected character
            if row_idx == selected_char_row and col_idx == selected_char_col:
                color = (100, 255, 100)
                text_color = (0, 0, 0)
            else:
                color = (60, 60, 60)
                text_color = (255, 255, 255)
            
            # Draw character box
            pygame.draw.rect(surface, color, (char_x, char_y, char_width, char_height), border_radius=5)
            pygame.draw.rect(surface, (150, 150, 150), (char_x, char_y, char_width, char_height), 2, border_radius=5)
            
            # Draw character
            char_text = small_font.render(char, True, text_color)
            text_x = char_x + (char_width - char_text.get_width()) // 2
            text_y = char_y + (char_height - char_text.get_height()) // 2
            surface.blit(char_text, (text_x, text_y))

def get_species_specific_requirements(player_stats, move_type):
    """Get available requirements based on player's species and move type"""
    base_requirements = ['NEEDS ARM', 'NEEDS LEG', 'NEEDS 2 ARMS', 'NEEDS 2 LEGS']
    
    # Add species-specific extra limb requirements
    if SPECIES_CONFIG_AVAILABLE and player_stats and hasattr(player_stats, 'species'):
        try:
            species_config = get_species_config(player_stats.species)
            if species_config and species_config["body_parts"]["has_extra_limbs"]:
                extra_limb_name = species_config["body_parts"]["extra_limbs_name"]
                if extra_limb_name:
                    # Add single extra limb requirement only (extra limbs are unified as one body part)
                    base_requirements.append(f'NEEDS {extra_limb_name}')
        except (KeyError, AttributeError, TypeError) as e:
            print(f"Warning: Could not get extra limb requirements for species {getattr(player_stats, 'species', 'Unknown')}: {e}")
    
    # For ATK moves, add TARGET requirements
    if move_type == 'ATK':
        base_requirements.extend([
            'TARGET HEAD', 'TARGET BODY', 'TARGET ARM', 'TARGET LEG',
            'TARGET BLEED', 'TARGET BURN', 'TARGET POISON', 'TARGET STUN'
        ])
        
        # Add species-specific target requirements
        if SPECIES_CONFIG_AVAILABLE and player_stats and hasattr(player_stats, 'species'):
            try:
                species_config = get_species_config(player_stats.species)
                if species_config and species_config["body_parts"]["has_extra_limbs"]:
                    extra_limb_name = species_config["body_parts"]["extra_limbs_name"]
                    if extra_limb_name:
                        base_requirements.append(f'TARGET {extra_limb_name}')
            except (KeyError, AttributeError, TypeError) as e:
                print(f"Warning: Could not get extra limb target requirements for species {getattr(player_stats, 'species', 'Unknown')}: {e}")
    
    return base_requirements

def open_move_customization_menu(screen, original_move, player_stats, font, small_font, menu_box_width, menu_box_height, menu_box_x, menu_box_y):
    """Open the move customization interface with improved navigation"""
    clock = pygame.time.Clock()
    
    # Initialize customization state
    custom_move = {
        'name': original_move['name'],
        'type': original_move['type'],
        'scaling': {
            'forz': original_move['scaling']['forz'],
            'des': original_move['scaling']['des'],
            'spe': original_move['scaling']['spe']
        },
        'effects': original_move.get('effects', []).copy(),
        'requirements': original_move.get('requirements', []).copy(),
        'elements': original_move.get('elements', []).copy(),
        'buffs': original_move.get('buffs', []).copy(),  # Copy existing buffs
        'accuracy': validate_accuracy(original_move.get('accuracy', 100))
    }
    
    # Auto-calculate elements if not provided or if calculation is available (skip for BUF moves)
    if custom_move['type'] != 'BUF':  # Skip element calculation for buff moves
        if CALCULATION_AVAILABLE and (not custom_move['elements'] or len(custom_move['elements']) == 0):
            species_name = getattr(player_stats, 'species', 'Maedo')  # Default to Maedo if no species
            calculated_element = calculate_move_element(custom_move['scaling'], species_name)
            custom_move['elements'] = [calculated_element]
            print(f"[Move Customization] Auto-calculated element: {calculated_element} for species {species_name}")
        elif not CALCULATION_AVAILABLE and (not custom_move['elements'] or len(custom_move['elements']) == 0):
            # Fallback if calculation not available
            custom_move['elements'] = ['IMPACT']
    else:
        # BUF moves don't use elements - clear any existing elements
        custom_move['elements'] = []
        print(f"[Move Customization] Cleared elements for BUF move: {custom_move['name']}")
    
    # Navigation state  
    in_top_row = True  # Whether we're navigating the top section tabs
    current_section = 0  
    
    # Dynamic sections based on move type
    if custom_move['type'] == 'BUF':
        sections = ['Buffs', 'Requirements', 'Confirm']
        # 0=buffs, 1=requirements, 2=confirm for BUF moves
    else:
        sections = ['Scaling', 'Accuracy', 'Effects', 'Requirements', 'Confirm']
        # 0=scaling, 1=accuracy, 2=effects, 3=requirements, 4=confirm for ATK moves
    
    # Name editing state
    in_name_editing = False
    selected_char_row = 0
    selected_char_col = 0
    uppercase_mode = True
    max_name_length = 20
    
    # Character selection grid (identical to Main_Menu.py)
    char_grid_uppercase = [
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
        ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'],
        ['U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3'],
        ['4', '5', '6', '7', '8', '9', 'Spc', 'Del', 'Ok', 'Lwr']
    ]
    
    char_grid_lowercase = [
        ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
        ['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'],
        ['u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3'],
        ['4', '5', '6', '7', '8', '9', 'Spc', 'Del', 'Ok', 'Upr']
    ]
    
    char_grid = char_grid_uppercase if uppercase_mode else char_grid_lowercase
    
    # Move type selection (ATK or BUF)
    move_types = ['ATK', 'BUF']
    current_move_type = 0 if custom_move['type'] == 'ATK' else 1  # Initialize based on current move type
    in_type_selection = False
    
    # Name/type area navigation state (when user presses UP from sections)
    in_name_type_area = False
    name_type_selection = 0  # 0=name, 1=type
    
    # Section-specific navigation
    scaling_selected = 0  # 0=forz, 1=des, 2=spe
    scaling_names = ['forz', 'des', 'spe']
    
    # Accuracy options (only balanced values: 30%, 50%, 90%, 100%)
    accuracy_options = [30, 50, 90, 100]
    accuracy_selected = accuracy_options.index(custom_move['accuracy']) if custom_move['accuracy'] in accuracy_options else 3  # Default to 100%
    
    # Enhanced effects system - each effect has [name, level, duration, immunity]
    # Get species-specific available effects
    if SPECIES_CONFIG_AVAILABLE and player_stats and hasattr(player_stats, 'species'):
        try:
            species_effects = get_available_effects(player_stats.species)
            available_effects = []
            for effect_name, (available, unlocked) in species_effects.items():
                if available and unlocked:  # Only show effects that are both available and unlocked
                    available_effects.append([effect_name, 0, 0, False])
            
            # Add species-specific property effects (they are treated as effects with level 0 or 1)
            try:
                species_config = get_species_config(player_stats.species)
                if species_config and 'available_properties' in species_config:
                    for prop_name, (available, unlocked) in species_config['available_properties'].items():
                        if available and unlocked:
                            # Property effects are binary (0 or 1) and have no duration
                            available_effects.append([prop_name, 0, 1, False])
            except (ImportError, KeyError, AttributeError) as e:
                print(f"Warning: Could not load property effects: {e}")
                
        except (KeyError, AttributeError) as e:
            print(f"Warning: Could not get species-specific effects for {getattr(player_stats, 'species', 'Unknown')}, using fallback: {e}")
            # Fallback to default effects
            available_effects = [
                ['bleed', 0, 0, False],
                ['burn', 0, 0, False], 
                ['poison', 0, 0, False],
                ['stun', 0, 0, False],
                ['confusion', 0, 0, False],
                ['regeneration', 0, 0, False]
            ]
    else:
        # Fallback to default effects
        available_effects = [
            ['bleed', 0, 0, False],
            ['burn', 0, 0, False], 
            ['poison', 0, 0, False],
            ['stun', 0, 0, False],
            ['confusion', 0, 0, False],
            ['regeneration', 0, 0, False]
        ]
    
    # Initialize effects from original move
    for effect in custom_move['effects']:
        if isinstance(effect, list) and len(effect) >= 3:
            effect_name = effect[0].lower()
            for available_effect in available_effects:
                if available_effect[0] == effect_name:
                    available_effect[1] = effect[1]  # level
                    available_effect[2] = effect[2]  # duration
                    break
    
    effects_selected = 0
    effects_scroll_offset = 0  # For scrolling through effects
    max_visible_effects = 8   # Show up to 8 effects at once
    
    # Buffs system (for BUF type moves) - Get from Status_Effects_Config
    # Get species-specific available buffs
    if SPECIES_CONFIG_AVAILABLE and player_stats and hasattr(player_stats, 'species'):
        try:
            species_buffs = get_available_buffs(player_stats.species)
            available_buffs = []
            
            # List of Effect-on-Hit buffs that should not have levels
            effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
            
            for buff_name, (available, unlocked) in species_buffs.items():
                if available and unlocked:  # Only show buffs that are both available and unlocked
                    # Check if this is an Effect-on-Hit buff
                    if buff_name in effect_on_hit_buffs:
                        # Effect-on-Hit buffs don't have levels, just on/off (0 or 1)
                        available_buffs.append([buff_name, 0])
                    else:
                        # Regular buffs with 'buf_' prefix - remove prefix for display
                        display_name = buff_name[4:] if buff_name.startswith('buf_') else buff_name
                        available_buffs.append([display_name, 0])
        except (KeyError, AttributeError) as e:
            print(f"Warning: Could not get species-specific buffs for {getattr(player_stats, 'species', 'Unknown')}, using fallback: {e}")
            # Fallback - try STATUS_CONFIG if available
            if STATUS_CONFIG_AVAILABLE:
                available_buffs = []
                for effect_name, config in STATUS_EFFECTS_CONFIG.items():
                    if effect_name.startswith('buf_'):
                        display_name = effect_name[4:]
                        available_buffs.append([display_name, 0])
            else:
                available_buffs = [
                    ['rig', 0], ['res', 0], ['sta', 0], ['forz', 0], 
                    ['des', 0], ['spe', 0], ['vel', 0], ['dodge', 0], ['shield', 0]
                ]
    elif STATUS_CONFIG_AVAILABLE:
        # Get all buff effects from the config file
        available_buffs = []
        for effect_name, config in STATUS_EFFECTS_CONFIG.items():
            if effect_name.startswith('buf_'):
                # Remove 'buf_' prefix for display
                display_name = effect_name[4:]
                available_buffs.append([display_name, 0])
    else:
        # Fallback if config not available
        available_buffs = [
            ['rig', 0], ['res', 0], ['sta', 0], ['forz', 0], 
            ['des', 0], ['spe', 0], ['vel', 0], ['dodge', 0], ['shield', 0]
        ]
    
    # Initialize buffs from original move - handle both 'buffs' field and 'effects' field for BUF moves
    if 'buffs' in custom_move and custom_move['buffs']:
        # Direct buffs field (for moves created by customization menu)
        for buff in custom_move['buffs']:
            if isinstance(buff, list) and len(buff) >= 2:
                buff_name = buff[0].lower()
                for available_buff in available_buffs:
                    if available_buff[0] == buff_name:
                        available_buff[1] = buff[1]  # level
                        break
    elif custom_move['type'] == 'BUF' and 'effects' in custom_move and custom_move['effects']:
        # Convert effects to buffs for BUF moves (for moves from Player_Moves.py)
        for effect in custom_move['effects']:
            if isinstance(effect, list) and len(effect) >= 2:
                effect_name = effect[0].lower()
                if effect_name.startswith('buf_'):
                    # Remove 'buf_' prefix to match available_buffs format
                    buff_name = effect_name[4:]
                    for available_buff in available_buffs:
                        if available_buff[0] == buff_name:
                            available_buff[1] = effect[1]  # level
                            break
    elif custom_move['type'] == 'BUF':
        # Initialize empty buffs list for BUF moves with no existing buffs
        custom_move['buffs'] = []
    
    buffs_selected = 0
    buffs_scroll_offset = 0
    max_visible_buffs = 8
    
    # Enhanced requirements system - different for BUF vs ATK moves
    available_requirements = get_species_specific_requirements(player_stats, custom_move['type'])
    
    selected_requirements = []  # Currently selected requirements
    
    # Auto-add mandatory requirements for active buffs (dodge/shield)
    mandatory_reqs = get_mandatory_requirements(available_buffs)
    for req in mandatory_reqs:
        if req not in selected_requirements and req in available_requirements:
            selected_requirements.append(req)
    
    requirements_selected = 0
    requirements_scroll_offset = 0  # For scrolling through requirements
    max_visible_requirements = 10   # Show up to 10 requirements at once
    
    last_input_time = 0
    input_delay = 150
    
    while True:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Handle ESC during name editing - only close keyboard, not entire menu
                    if in_name_editing:
                        in_name_editing = False
                        in_name_type_area = True  # Return to name/type area
                        name_type_selection = 0   # Keep name selected
                        last_input_time = current_time
                    else:
                        return None
                # Handle type selection input immediately (no timing delay)
                elif in_type_selection:
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                        # Toggle between ATK and BUF and immediately confirm
                        current_move_type = (current_move_type + 1) % len(move_types)
                        custom_move['type'] = move_types[current_move_type]
                        # Update sections array and requirements based on new move type
                        if custom_move['type'] == 'BUF':
                            sections = ['Buffs', 'Requirements', 'Confirm']
                            available_requirements = get_species_specific_requirements(player_stats, 'BUF')
                            # Clear ATK-specific data when switching to BUF
                            custom_move['effects'] = []
                            custom_move['scaling'] = {'forz': 0, 'des': 0, 'spe': 0}
                            custom_move['accuracy'] = 100
                            # Reset effects data
                            for effect in available_effects:
                                effect[1] = 0  # level
                                effect[2] = 0  # duration
                        else:
                            sections = ['Scaling', 'Accuracy', 'Effects', 'Requirements', 'Confirm']
                            available_requirements = get_species_specific_requirements(player_stats, 'ATK')
                            # Clear BUF-specific data when switching to ATK
                            custom_move['buffs'] = []
                            # Reset buffs data
                            for buff in available_buffs:
                                buff[1] = 0  # level
                        # Reset current section to 0 to avoid index out of bounds
                        current_section = 0
                        requirements_selected = min(requirements_selected, len(available_requirements) - 1)
                        in_type_selection = False
                        in_name_type_area = True  # Return to name/type area
                        name_type_selection = 1   # Keep type selected
                        last_input_time = current_time
                    elif event.key in [pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN, pygame.K_ESCAPE]:
                        # Exit type selection
                        in_type_selection = False
                        in_name_type_area = True  # Return to name/type area
                        name_type_selection = 1   # Keep type selected
                        last_input_time = current_time
                elif current_time - last_input_time > input_delay:
                    
                    # Handle name editing input
                    if in_name_editing:
                        selected_char_row, selected_char_col, uppercase_mode, name_changed, exit_editing = handle_name_input(
                            event, custom_move, char_grid, selected_char_row, selected_char_col, uppercase_mode, max_name_length)
                        
                        # Update char_grid if case changed
                        char_grid = char_grid_uppercase if uppercase_mode else char_grid_lowercase
                        
                        if exit_editing:
                            in_name_editing = False
                            in_name_type_area = True  # Return to name/type area
                            name_type_selection = 0   # Keep name selected
                            last_input_time = current_time
                        
                    
                    elif in_name_type_area:
                        # Navigation in name/type area (after pressing UP from sections)
                        if event.key in [pygame.K_a, pygame.K_LEFT]:
                            name_type_selection = (name_type_selection - 1) % 2
                            last_input_time = current_time
                        elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                            name_type_selection = (name_type_selection + 1) % 2
                            last_input_time = current_time
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            # Exit name/type area back to section navigation
                            in_name_type_area = False
                            last_input_time = current_time
                        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                            if name_type_selection == 0:  # Name selected
                                in_name_editing = True
                                in_name_type_area = False
                                selected_char_row = 0
                                selected_char_col = 0
                                last_input_time = current_time
                            elif name_type_selection == 1:  # Type selected
                                # Immediately toggle the type without entering selection mode
                                current_move_type = (current_move_type + 1) % len(move_types)
                                custom_move['type'] = move_types[current_move_type]
                                
                                # Update sections array and requirements based on new move type
                                if custom_move['type'] == 'BUF':
                                    sections = ['Buffs', 'Requirements', 'Confirm']
                                    available_requirements = get_species_specific_requirements(player_stats, 'BUF')
                                    # Clear ATK-specific data when switching to BUF
                                    custom_move['effects'] = []
                                    custom_move['scaling'] = {'forz': 0, 'des': 0, 'spe': 0}
                                    custom_move['accuracy'] = 100
                                    # Reset effects data
                                    for effect in available_effects:
                                        effect[1] = 0  # level
                                        effect[2] = 0  # duration
                                else:
                                    sections = ['Scaling', 'Accuracy', 'Effects', 'Requirements', 'Confirm']
                                    available_requirements = get_species_specific_requirements(player_stats, 'ATK')
                                    # Clear BUF-specific data when switching to ATK
                                    custom_move['buffs'] = []
                                    # Reset buffs data
                                    for buff in available_buffs:
                                        buff[1] = 0  # level
                                # Reset current section to 0 to avoid index out of bounds
                                current_section = 0
                                requirements_selected = min(requirements_selected, len(available_requirements) - 1)
                                last_input_time = current_time
                    
                    elif in_top_row:
                        # Navigation in top row (section selection)
                        if event.key in [pygame.K_a, pygame.K_LEFT]:
                            current_section = (current_section - 1) % len(sections)
                            last_input_time = current_time
                        elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                            current_section = (current_section + 1) % len(sections)
                            last_input_time = current_time
                        elif event.key in [pygame.K_w, pygame.K_UP]:
                            # Enter name/type area
                            in_name_type_area = True
                            name_type_selection = 0  # Start with name
                            last_input_time = current_time
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            # Enter the selected section
                            in_top_row = False
                            
                            # Handle section entry differently based on move type
                            if custom_move['type'] == 'BUF':
                                # BUF move sections: 0=buffs, 1=requirements, 2=confirm
                                if current_section == 1:  # Requirements section for BUF
                                    requirements_selected = find_next_compatible_requirement(available_requirements, selected_requirements, -1, 1)
                                    # Update scroll offset for new selection
                                    if requirements_selected >= requirements_scroll_offset + max_visible_requirements:
                                        requirements_scroll_offset = requirements_selected - max_visible_requirements + 1
                                    elif requirements_selected < requirements_scroll_offset:
                                        requirements_scroll_offset = requirements_selected
                            else:
                                # ATK move sections: 0=scaling, 1=accuracy, 2=effects, 3=requirements, 4=confirm
                                if current_section == 3:  # Requirements section for ATK
                                    requirements_selected = find_next_compatible_requirement(available_requirements, selected_requirements, -1, 1)
                                    # Update scroll offset for new selection
                                    if requirements_selected >= requirements_scroll_offset + max_visible_requirements:
                                        requirements_scroll_offset = requirements_selected - max_visible_requirements + 1
                                    elif requirements_selected < requirements_scroll_offset:
                                        requirements_scroll_offset = requirements_selected
                            last_input_time = current_time
                    
                    else:
                        # Navigation within sections - handle both ATK and BUF move types
                        if event.key in [pygame.K_w, pygame.K_UP]:
                            # Go back to top row or navigate within section
                            if custom_move['type'] == 'BUF':
                                # BUF move navigation: 0=buffs, 1=requirements, 2=confirm
                                if current_section == 0:  # Buffs section
                                    if buffs_selected == 0:
                                        in_top_row = True
                                    else:
                                        buffs_selected = (buffs_selected - 1) % len(available_buffs)
                                        # Update scroll offset to keep selection visible
                                        if buffs_selected >= buffs_scroll_offset + max_visible_buffs:
                                            buffs_scroll_offset = buffs_selected - max_visible_buffs + 1
                                        elif buffs_selected < buffs_scroll_offset:
                                            buffs_scroll_offset = buffs_selected
                                elif current_section == 1:  # Requirements section
                                    # Try to find the next compatible requirement going up without wrapping
                                    new_selected = find_next_compatible_requirement(available_requirements, selected_requirements, requirements_selected, -1, allow_wrap=False)
                                    
                                    # If we can't find a compatible requirement going up (without wrapping), go to top row
                                    if new_selected == requirements_selected:
                                        in_top_row = True
                                    else:
                                        requirements_selected = new_selected
                                        # Update scroll offset to keep selection visible
                                        if requirements_selected >= requirements_scroll_offset + max_visible_requirements:
                                            requirements_scroll_offset = requirements_selected - max_visible_requirements + 1
                                        elif requirements_selected < requirements_scroll_offset:
                                            requirements_scroll_offset = requirements_selected
                                elif current_section == 2:  # Confirm section
                                    in_top_row = True
                            else:
                                # ATK move navigation: 0=scaling, 1=accuracy, 2=effects, 3=requirements, 4=confirm
                                if current_section == 0:  # Scaling section
                                    if scaling_selected == 0:
                                        in_top_row = True
                                    else:
                                        scaling_selected = (scaling_selected - 1) % 3
                                elif current_section == 1:  # Accuracy section
                                    in_top_row = True
                                elif current_section == 2:  # Effects section
                                    if effects_selected == 0:
                                        in_top_row = True
                                    else:
                                        effects_selected = (effects_selected - 1) % len(available_effects)
                                        # Update scroll offset to keep selection visible
                                        if effects_selected >= effects_scroll_offset + max_visible_effects:
                                            effects_scroll_offset = effects_selected - max_visible_effects + 1
                                        elif effects_selected < effects_scroll_offset:
                                            effects_scroll_offset = effects_selected
                                elif current_section == 3:  # Requirements section
                                    # Try to find the next compatible requirement going up without wrapping
                                    new_selected = find_next_compatible_requirement(available_requirements, selected_requirements, requirements_selected, -1, allow_wrap=False)
                                    
                                    # If we can't find a compatible requirement going up (without wrapping), go to top row
                                    if new_selected == requirements_selected:
                                        in_top_row = True
                                    else:
                                        requirements_selected = new_selected
                                        # Update scroll offset to keep selection visible
                                        if requirements_selected >= requirements_scroll_offset + max_visible_requirements:
                                            requirements_scroll_offset = requirements_selected - max_visible_requirements + 1
                                        elif requirements_selected < requirements_scroll_offset:
                                            requirements_scroll_offset = requirements_selected
                                elif current_section == 4:  # Confirm section
                                    in_top_row = True
                            last_input_time = current_time
                        
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            # Navigate down within section - handle both ATK and BUF move types
                            if custom_move['type'] == 'BUF':
                                # BUF move navigation: 0=buffs, 1=requirements, 2=confirm
                                if current_section == 0:  # Buffs section
                                    buffs_selected = (buffs_selected + 1) % len(available_buffs)
                                    # Update scroll offset to keep selection visible
                                    if buffs_selected >= buffs_scroll_offset + max_visible_buffs:
                                        buffs_scroll_offset = buffs_selected - max_visible_buffs + 1
                                    elif buffs_selected < buffs_scroll_offset:
                                        buffs_scroll_offset = buffs_selected
                                elif current_section == 1:  # Requirements section
                                    # Smart navigation - skip incompatible requirements
                                    new_selected = find_next_compatible_requirement(available_requirements, selected_requirements, requirements_selected, 1)
                                    if new_selected != requirements_selected:
                                        requirements_selected = new_selected
                                        # Update scroll offset to keep selection visible
                                        if requirements_selected >= requirements_scroll_offset + max_visible_requirements:
                                            requirements_scroll_offset = requirements_selected - max_visible_requirements + 1
                                        elif requirements_selected < requirements_scroll_offset:
                                            requirements_scroll_offset = requirements_selected
                            else:
                                # ATK move navigation: 0=scaling, 1=accuracy, 2=effects, 3=requirements, 4=confirm
                                if current_section == 0:  # Scaling section
                                    scaling_selected = (scaling_selected + 1) % 3
                                elif current_section == 2:  # Effects section
                                    effects_selected = (effects_selected + 1) % len(available_effects)
                                    # Update scroll offset to keep selection visible
                                    if effects_selected >= effects_scroll_offset + max_visible_effects:
                                        effects_scroll_offset = effects_selected - max_visible_effects + 1
                                    elif effects_selected < effects_scroll_offset:
                                        effects_scroll_offset = effects_selected
                                elif current_section == 3:  # Requirements section
                                    # Smart navigation - skip incompatible requirements
                                    new_selected = find_next_compatible_requirement(available_requirements, selected_requirements, requirements_selected, 1)
                                    if new_selected != requirements_selected:
                                        requirements_selected = new_selected
                                        # Update scroll offset to keep selection visible
                                        if requirements_selected >= requirements_scroll_offset + max_visible_requirements:
                                            requirements_scroll_offset = requirements_selected - max_visible_requirements + 1
                                        elif requirements_selected < requirements_scroll_offset:
                                            requirements_scroll_offset = requirements_selected
                            last_input_time = current_time
                        
                        elif event.key in [pygame.K_a, pygame.K_LEFT]:
                            # Decrease values - handle both ATK and BUF move types
                            if custom_move['type'] == 'BUF':
                                # BUF move navigation: 0=buffs, 1=requirements, 2=confirm
                                if current_section == 0:  # Buffs section
                                    # Decrease buff level
                                    buff = available_buffs[buffs_selected]
                                    old_level = buff[1]
                                    
                                    # Check if this is an Effect-on-Hit buff
                                    effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
                                    if buff[0] in effect_on_hit_buffs:
                                        # Effect-on-Hit buffs are binary: 0 or 1 (off or on)
                                        buff[1] = 0 if buff[1] > 0 else 0
                                    else:
                                        # Regular buffs can have multiple levels
                                        buff[1] = max(0, buff[1] - 1)  # level
                                    
                                    # Handle mandatory requirements when buff level changes
                                    if old_level > 0 and buff[1] == 0:
                                        # Buff was deactivated, remove its mandatory requirement
                                        mandatory_req = get_mandatory_requirement_for_buff(buff[0])
                                        if mandatory_req and mandatory_req in selected_requirements:
                                            selected_requirements.remove(mandatory_req)
                            else:
                                # ATK move navigation: 0=scaling, 1=accuracy, 2=effects, 3=requirements, 4=confirm
                                if current_section == 0:  # Scaling section
                                    stat_name = scaling_names[scaling_selected]
                                    custom_move['scaling'][stat_name] = max(0, custom_move['scaling'][stat_name] - 1)
                                    # Auto-recalculate element after scaling change
                                    if CALCULATION_AVAILABLE:
                                        species_name = getattr(player_stats, 'species', 'Maedo')
                                        calculated_element = calculate_move_element(custom_move['scaling'], species_name)
                                        custom_move['elements'] = [calculated_element]
                                elif current_section == 1:  # Accuracy section
                                    accuracy_selected = max(0, accuracy_selected - 1)
                                    custom_move['accuracy'] = accuracy_options[accuracy_selected]
                                elif current_section == 2:  # Effects section
                                    effect = available_effects[effects_selected]
                                    if STATUS_CONFIG_AVAILABLE and is_property_effect(effect[0]):
                                        # Property effect - binary toggle (0 or 1)
                                        if effect[1] > 0:
                                            effect[1] = 0  # Disable property
                                            effect[2] = 0  # Set duration to 0 when disabled
                                    else:
                                        # Regular status effect
                                        effect[1] = max(0, effect[1] - 1)  # level
                                        effect[2] = max(0, effect[2] - 1)  # duration
                            last_input_time = current_time
                        
                        elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                            # Increase values - handle both ATK and BUF move types
                            if custom_move['type'] == 'BUF':
                                # BUF move navigation: 0=buffs, 1=requirements, 2=confirm
                                if current_section == 0:  # Buffs section
                                    # Check if any other buff is already active (level > 0)
                                    buff = available_buffs[buffs_selected]
                                    old_level = buff[1]
                                    
                                    # Count active buffs (excluding current one)
                                    active_count = sum(1 for b in available_buffs if b != buff and b[1] > 0)
                                    
                                    # Only allow increase if no other buffs are active or this buff is already active
                                    if active_count == 0 or old_level > 0:
                                        # Check if this is an Effect-on-Hit buff
                                        effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
                                        if buff[0] in effect_on_hit_buffs:
                                            # Effect-on-Hit buffs are binary: 0 or 1 (off or on)
                                            buff[1] = 1 if buff[1] == 0 else 1
                                        else:
                                            # Regular buffs can have multiple levels
                                            buff[1] = min(10, buff[1] + 1)  # level
                                        
                                        # Handle mandatory requirements when buff level changes
                                        if old_level == 0 and buff[1] > 0:
                                            # Buff was activated, add its mandatory requirement
                                            mandatory_req = get_mandatory_requirement_for_buff(buff[0])
                                            if mandatory_req and mandatory_req not in selected_requirements:
                                                if len(selected_requirements) < 4:
                                                    selected_requirements.append(mandatory_req)
                            else:
                                # ATK move navigation: 0=scaling, 1=accuracy, 2=effects, 3=requirements, 4=confirm
                                if current_section == 0:  # Scaling section
                                    stat_name = scaling_names[scaling_selected]
                                    custom_move['scaling'][stat_name] = min(10, custom_move['scaling'][stat_name] + 1)
                                    # Auto-recalculate element after scaling change
                                    if CALCULATION_AVAILABLE:
                                        species_name = getattr(player_stats, 'species', 'Maedo')
                                        calculated_element = calculate_move_element(custom_move['scaling'], species_name)
                                        custom_move['elements'] = [calculated_element]
                                elif current_section == 1:  # Accuracy section
                                    accuracy_selected = min(len(accuracy_options) - 1, accuracy_selected + 1)
                                    custom_move['accuracy'] = accuracy_options[accuracy_selected]
                                elif current_section == 2:  # Effects section
                                    effect = available_effects[effects_selected]
                                    old_level = effect[1]
                                    
                                    if STATUS_CONFIG_AVAILABLE and is_property_effect(effect[0]):
                                        # Property effect - binary toggle (0 or 1)
                                        if old_level == 0:
                                            # Check if we can add a property (max 1 property allowed)
                                            active_properties = get_active_property_effects(available_effects)
                                            if active_properties == 0:
                                                effect[1] = 1  # Enable property
                                                effect[2] = 1  # Properties always have duration 1
                                    else:
                                        # Regular status effect
                                        if old_level == 0:
                                            # Check if we can add a status effect (max 1 status effect allowed)
                                            active_status = get_active_status_effects(available_effects)
                                            if active_status == 0:
                                                effect[1] = 1  # Start with level 1
                                                effect[2] = 1  # Start with duration 1
                                        else:
                                            # Increase existing effect
                                            effect[1] = min(10, effect[1] + 1)  # level
                                            effect[2] = min(10, effect[2] + 1)  # duration
                            last_input_time = current_time
                        
                        elif event.key == pygame.K_SPACE:
                            # Handle SPACE key for both ATK and BUF move types
                            if custom_move['type'] == 'BUF':
                                # BUF move navigation: 0=buffs, 1=requirements, 2=confirm
                                if current_section == 1:  # Requirements section
                                    req = available_requirements[requirements_selected]
                                    if is_requirement_compatible(req, selected_requirements):
                                        if req in selected_requirements:
                                            # Check if this is a mandatory requirement
                                            if is_requirement_mandatory(req, available_buffs):
                                                show_mandatory_requirement_error(screen, font, req)
                                            else:
                                                selected_requirements.remove(req)
                                        elif len(selected_requirements) < 4:
                                            # Check if mandatory buffs are active and prevent non-mandatory selection
                                            if has_active_mandatory_buffs(available_buffs):
                                                # Only allow selection of mandatory requirements
                                                if not is_requirement_mandatory(req, available_buffs):
                                                    # Don't add non-mandatory requirements when mandatory buffs are active
                                                    pass
                                                else:
                                                    selected_requirements.append(req)
                                            else:
                                                selected_requirements.append(req)
                                elif current_section == 2:  # Confirm section
                                    # Update custom move with final buffs and requirements
                                    final_buffs = []
                                    for buff in available_buffs:
                                        if buff[1] > 0:  # Only include buffs with level > 0
                                            final_buffs.append([buff[0], buff[1]])
                                    custom_move['buffs'] = final_buffs
                                    custom_move['requirements'] = selected_requirements.copy()
                                    
                                    # Convert buffs to effects format for compatibility with battle system
                                    if custom_move['type'] == 'BUF' and 'buffs' in custom_move:
                                        # Convert buffs to effects format: ["buf_stat", level, duration, 0]
                                        converted_effects = []
                                        effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
                                        
                                        for buff in custom_move['buffs']:
                                            if isinstance(buff, list) and len(buff) >= 2:
                                                buff_name = buff[0]
                                                buff_level = buff[1]
                                                
                                                # Handle Effect-on-Hit buffs specially (no prefix needed, permanent duration)
                                                if buff_name in effect_on_hit_buffs:
                                                    # Effect-on-Hit buffs don't need 'buf_' prefix and have permanent duration
                                                    converted_effects.append([buff_name, buff_level, 999, 0])
                                                else:
                                                    # Regular buffs need 'buf_' prefix and standard duration
                                                    prefixed_name = f"buf_{buff_name}"
                                                    # Use duration of 2 for buffs (standard for player buffs)
                                                    converted_effects.append([prefixed_name, buff_level, 2, 0])
                                        custom_move['effects'] = converted_effects
                                        # Remove buffs field to avoid confusion
                                        if 'buffs' in custom_move:
                                            del custom_move['buffs']
                                    
                                    # BUF moves don't use elements - clear any existing elements
                                    custom_move['elements'] = []
                                    print(f"[Move Save BUF] Cleared elements for BUF move: {custom_move['name']}")
                                    
                                    # Validate move before confirmation
                                    is_valid, error_message = validate_move_rules(custom_move, player_stats)
                                    if not is_valid:
                                        show_validation_error(screen, font, error_message)
                                        last_input_time = current_time
                                        continue
                                    
                                    # Show final confirmation
                                    if show_final_confirmation(screen, font):
                                        return custom_move
                            else:
                                # ATK move navigation: 0=scaling, 1=accuracy, 2=effects, 3=requirements, 4=confirm
                                if current_section == 3:  # Requirements section
                                    req = available_requirements[requirements_selected]
                                    if is_requirement_compatible(req, selected_requirements):
                                        if req in selected_requirements:
                                            # Check if this is a mandatory requirement
                                            if is_requirement_mandatory(req, available_buffs):
                                                show_mandatory_requirement_error(screen, font, req)
                                            else:
                                                selected_requirements.remove(req)
                                        elif len(selected_requirements) < 4:
                                            # Check if mandatory buffs are active and prevent non-mandatory selection
                                            if has_active_mandatory_buffs(available_buffs):
                                                # Only allow selection of mandatory requirements
                                                if not is_requirement_mandatory(req, available_buffs):
                                                    # Don't add non-mandatory requirements when mandatory buffs are active
                                                    pass
                                                else:
                                                    selected_requirements.append(req)
                                            else:
                                                selected_requirements.append(req)
                                elif current_section == 4:  # Confirm section
                                    # Update custom move with final effects and requirements
                                    final_effects = []
                                    for effect in available_effects:
                                        if effect[1] > 0 and effect[2] > 0:  # Only include effects with level and duration > 0
                                            final_effects.append([effect[0], effect[1], effect[2], effect[3]])
                                    custom_move['effects'] = final_effects
                                    custom_move['requirements'] = selected_requirements.copy()
                                    
                                    # Convert buffs to effects format for compatibility with battle system (for converted ATK->BUF moves)
                                    if custom_move['type'] == 'BUF' and 'buffs' in custom_move:
                                        # Convert buffs to effects format: ["buf_stat", level, duration, 0]
                                        converted_effects = []
                                        effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
                                        
                                        for buff in custom_move['buffs']:
                                            if isinstance(buff, list) and len(buff) >= 2:
                                                buff_name = buff[0]
                                                buff_level = buff[1]
                                                
                                                # Handle Effect-on-Hit buffs specially (no prefix needed, permanent duration)
                                                if buff_name in effect_on_hit_buffs:
                                                    # Effect-on-Hit buffs don't need 'buf_' prefix and have permanent duration
                                                    converted_effects.append([buff_name, buff_level, 999, 0])
                                                else:
                                                    # Regular buffs need 'buf_' prefix and standard duration
                                                    prefixed_name = f"buf_{buff_name}"
                                                    # Use duration of 2 for buffs (standard for player buffs)
                                                    converted_effects.append([prefixed_name, buff_level, 2, 0])
                                        custom_move['effects'] = converted_effects
                                        # Remove buffs field to avoid confusion
                                        if 'buffs' in custom_move:
                                            del custom_move['buffs']
                                    
                                    # Recalculate element before saving (ATK moves)
                                    if CALCULATION_AVAILABLE:
                                        species_name = getattr(player_stats, 'species', 'Maedo')
                                        calculated_element = calculate_move_element(custom_move['scaling'], species_name)
                                        custom_move['elements'] = [calculated_element]
                                        print(f"[Move Save ATK] Recalculated element: {calculated_element} for species {species_name}")
                                    elif not custom_move.get('elements'):
                                        custom_move['elements'] = ['IMPACT']
                                    
                                    # Validate move before confirmation
                                    is_valid, error_message = validate_move_rules(custom_move, player_stats)
                                    if not is_valid:
                                        show_validation_error(screen, font, error_message)
                                        last_input_time = current_time
                                        continue
                                    
                                    # Show final confirmation
                                    if show_final_confirmation(screen, font):
                                        return custom_move
                            last_input_time = current_time
        
        # Always update selected requirements list with current selection
        custom_move['requirements'] = selected_requirements.copy()
        
        # Always update effects/buffs in custom_move for real-time calculation
        if custom_move['type'] == 'BUF':
            # Update buffs for BUF moves
            final_buffs = []
            for buff in available_buffs:
                if buff[1] > 0:  # Only include buffs with level > 0
                    final_buffs.append([buff[0], buff[1]])
            custom_move['buffs'] = final_buffs
        else:
            # Update effects for ATK moves
            final_effects = []
            for effect in available_effects:
                if effect[1] > 0 and effect[2] > 0:  # Only include effects with level and duration > 0
                    final_effects.append([effect[0], effect[1], effect[2], effect[3]])
            custom_move['effects'] = final_effects
        
        # Draw customization interface
        draw_move_customization_interface_v2(screen, custom_move, player_stats, in_top_row, current_section, sections,
                                           scaling_selected, scaling_names, accuracy_options, accuracy_selected,
                                           available_effects, effects_selected, available_requirements, requirements_selected,
                                           selected_requirements, font, small_font, menu_box_width, menu_box_height, menu_box_x, menu_box_y,
                                           effects_scroll_offset, max_visible_effects, requirements_scroll_offset, max_visible_requirements,
                                           move_types, current_move_type, in_name_editing, in_type_selection, in_name_type_area, name_type_selection,
                                           available_buffs, buffs_selected, buffs_scroll_offset, max_visible_buffs)
        
        # Draw name editing keyboard overlay if active
        if in_name_editing:
            draw_name_editing_keyboard(screen, char_grid, selected_char_row, selected_char_col, font, small_font, custom_move)
        
        pygame.display.flip()
        clock.tick(60)

def draw_move_customization_interface_v2(screen, custom_move, player_stats, in_top_row, current_section, sections,
                                        scaling_selected, scaling_names, accuracy_options, accuracy_selected,
                                        available_effects, effects_selected, available_requirements, requirements_selected,
                                        selected_requirements, font, small_font, menu_box_width, menu_box_height, menu_box_x, menu_box_y,
                                        effects_scroll_offset, max_visible_effects, requirements_scroll_offset, max_visible_requirements,
                                        move_types, current_move_type, in_name_editing, in_type_selection, in_name_type_area, name_type_selection,
                                        available_buffs, buffs_selected, buffs_scroll_offset, max_visible_buffs):
    """Draw the enhanced move customization interface using overlay system"""
    # Create an overlay using menu box dimensions instead of fullscreen
    overlay = pygame.Surface((menu_box_width, menu_box_height))
    overlay.fill((20, 20, 30))  # Solid background to prevent lingering
    
    # Header with name and type
    # Move name (left side) - clickable for editing
    if in_name_editing:
        name_color = (100, 255, 100)  # Green when editing
        name_text = font.render(f"{custom_move['name']}_", True, name_color)  # Add cursor
    elif in_name_type_area and name_type_selection == 0:
        name_color = (255, 255, 100)  # Yellow when selected in name/type area
        name_text = font.render(f"{custom_move['name']}", True, name_color)
    else:
        name_color = (255, 255, 255)
        name_text = font.render(f"{custom_move['name']}", True, name_color)
    
    # Draw name background if selected in name/type area
    if in_name_type_area and name_type_selection == 0:
        name_bg = pygame.Rect(40, 25, name_text.get_width() + 20, name_text.get_height() + 10)
        pygame.draw.rect(overlay, (60, 60, 60), name_bg, border_radius=5)
        pygame.draw.rect(overlay, (255, 255, 100), name_bg, 2, border_radius=5)
    
    overlay.blit(name_text, (50, 30))
    
    # Move type (right side) - shows ATK or BUF
    type_x = 400
    if in_type_selection:
        type_color = (100, 255, 100)  # Green when selecting
        type_bg_color = (40, 40, 40)
    elif in_name_type_area and name_type_selection == 1:
        type_color = (255, 255, 100)  # Yellow when selected in name/type area
        type_bg_color = (60, 60, 60)
    else:
        type_color = (255, 255, 255)
        type_bg_color = (60, 60, 60)
    
    type_text = font.render(f"Type: {move_types[current_move_type]}", True, type_color)
    
    # Draw type background if in selection mode or selected in name/type area
    if in_type_selection or (in_name_type_area and name_type_selection == 1):
        type_bg = pygame.Rect(type_x - 10, 25, type_text.get_width() + 20, type_text.get_height() + 10)
        pygame.draw.rect(overlay, type_bg_color, type_bg, border_radius=5)
        border_color = (150, 150, 150) if in_type_selection else (255, 255, 100)
        pygame.draw.rect(overlay, border_color, type_bg, 2, border_radius=5)
    
    overlay.blit(type_text, (type_x, 30))
    
    # Navigation instructions
    if in_name_type_area:
        nav_text = small_font.render("Navigate name/type: LEFT/RIGHT | Select: SPACE | Back: DOWN", True, (200, 200, 200))
    elif in_top_row:
        nav_text = small_font.render("Navigate sections: LEFT/RIGHT | Name/Type area: UP | Enter section: DOWN", True, (200, 200, 200))
    else:
        nav_text = small_font.render("Back to sections: UP | Navigate: UP/DOWN | Adjust: LEFT/RIGHT | Select: SPACE", True, (200, 200, 200))
    overlay.blit(nav_text, (50, 70))
    
    # Calculate and display damage/stamina in bottom right (except for confirm section, and for BUF moves only show outside confirm)
    show_current_stats = current_section != 4 and not (custom_move["type"] == "BUF" and current_section == 2)  # Hide stats for BUF moves in Confirm section
    if show_current_stats:
        damage, stamina_cost = calculate_move_damage_and_stamina(player_stats, custom_move)
        
        # Bottom right stats box
        stats_box_width = 200
        stats_box_height = 80
        stats_box_x = menu_box_width - stats_box_width - 20
        stats_box_y = menu_box_height - stats_box_height - 20
        
        pygame.draw.rect(overlay, (40, 40, 60), (stats_box_x, stats_box_y, stats_box_width, stats_box_height), border_radius=10)
        pygame.draw.rect(overlay, (100, 100, 150), (stats_box_x, stats_box_y, stats_box_width, stats_box_height), 2, border_radius=10)
        
        stats_title = small_font.render("Current Stats:", True, (255, 255, 255))
        
        # Display different content based on move type
        if custom_move["type"] == "BUF":
            # Show buff information instead of damage
            # BUF moves store buffs as a list of [buff_name, level] pairs
            buffs = custom_move.get("buffs", [])
            selected_buffs = []
            if isinstance(buffs, list):
                selected_buffs = [buff for buff in buffs if isinstance(buff, list) and len(buff) >= 2 and buff[1] > 0]
            
            if selected_buffs:
                # Show first selected buff
                buff_name, buff_level = selected_buffs[0][:2]
                
                # Check if this is an Effect-on-Hit buff (should only show name)
                effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
                if buff_name in effect_on_hit_buffs:
                    # Effect-on-Hit buffs: show only the name
                    display_name = buff_name.replace('_', ' ').title()
                    damage_text = small_font.render(f"Buff: {display_name}", True, (255, 200, 200))
                else:
                    # Regular buffs: show name and level
                    damage_text = small_font.render(f"Buff: {buff_name} Lv. {buff_level}", True, (255, 200, 200))
            else:
                damage_text = small_font.render("Buff: None", True, (255, 200, 200))
        else:
            damage_text = small_font.render(f"Damage: {damage}", True, (255, 200, 200))
        
        stamina_text = small_font.render(f"Stamina: {stamina_cost}", True, (200, 200, 255))
        
        overlay.blit(stats_title, (stats_box_x + 10, stats_box_y + 10))
        overlay.blit(damage_text, (stats_box_x + 10, stats_box_y + 30))
        overlay.blit(stamina_text, (stats_box_x + 10, stats_box_y + 50))
    
    # Top row - Section tabs
    tab_width = 120
    tab_height = 40
    tab_y = 100
    tab_spacing = 10
    
    for i, section_name in enumerate(sections):
        tab_x = 50 + i * (tab_width + tab_spacing)
        
        # Highlight current section
        if in_top_row and i == current_section:
            color = (100, 100, 255)  # Blue when in top row and selected
            border_color = (150, 150, 255)
        elif not in_top_row and i == current_section:
            color = (100, 255, 100)  # Green when section is active but not in top row
            border_color = (150, 255, 150)
        else:
            color = (60, 60, 60)
            border_color = (100, 100, 100)
        
        pygame.draw.rect(overlay, color, (tab_x, tab_y, tab_width, tab_height), border_radius=5)
        pygame.draw.rect(overlay, border_color, (tab_x, tab_y, tab_width, tab_height), 2, border_radius=5)
        
        tab_text = small_font.render(section_name, True, (255, 255, 255))
        text_x = tab_x + (tab_width - tab_text.get_width()) // 2
        text_y = tab_y + (tab_height - tab_text.get_height()) // 2
        overlay.blit(tab_text, (text_x, text_y))
    
    # Content area
    content_y = 160
    left_column_width = 400
    right_column_x = left_column_width + 100
    
    # Draw sections based on current section name (dynamic based on sections array)
    if current_section < len(sections):
        section_name = sections[current_section]
        
        if section_name == 'Buffs':  # BUF move buffs section
            draw_buffs_section(overlay, available_buffs, buffs_selected, content_y, font, small_font, not in_top_row, buffs_scroll_offset, max_visible_buffs)
        
        elif section_name == 'Scaling':  # ATK move scaling section
            draw_scaling_section(overlay, custom_move, scaling_selected, scaling_names, content_y, font, small_font, not in_top_row)
        
        elif section_name == 'Accuracy':  # ATK move accuracy section
            draw_accuracy_section(overlay, custom_move, accuracy_options, accuracy_selected, content_y, font, small_font, not in_top_row)
        
        elif section_name == 'Effects':  # ATK move effects section
            draw_enhanced_effects_section(overlay, available_effects, effects_selected, content_y, font, small_font, not in_top_row, effects_scroll_offset, max_visible_effects)
        
        elif section_name == 'Requirements':  # Requirements section (both ATK and BUF)
            draw_enhanced_requirements_section(overlay, available_requirements, requirements_selected, selected_requirements, 
                                             content_y, right_column_x, font, small_font, not in_top_row, requirements_scroll_offset, max_visible_requirements, available_buffs)
        
        elif section_name == 'Confirm':  # Confirm section (both ATK and BUF)
            draw_confirm_section(overlay, custom_move, player_stats, content_y, font, small_font, not in_top_row, available_effects)
    
    # Description box in top-right (visible in all sections)
    desc_title, desc_text = get_element_description(current_section, sections, custom_move, available_effects, effects_selected,
                                                   available_requirements, requirements_selected, available_buffs, buffs_selected,
                                                   scaling_selected, scaling_names, accuracy_options, accuracy_selected, in_top_row)

    desc_box_width = 360  # Increased from 280 to 360 (80 pixels wider)
    desc_box_height = 200  # Increased from 140 to 200 (60 pixels taller)
    desc_box_x = menu_box_width - desc_box_width - 20  # Automatically moves left to accommodate wider box
    desc_box_y = 100  # Position in top-right, below navigation instructions
    
    # Draw description box background
    pygame.draw.rect(overlay, (30, 30, 50), (desc_box_x, desc_box_y, desc_box_width, desc_box_height), border_radius=8)
    pygame.draw.rect(overlay, (100, 150, 200), (desc_box_x, desc_box_y, desc_box_width, desc_box_height), 2, border_radius=8)
    
    # Draw description title
    title_text = small_font.render(desc_title, True, (150, 200, 255))
    title_rect = title_text.get_rect()
    if title_rect.width > desc_box_width - 20:
        # Truncate title if too long
        desc_title = desc_title[:25] + "..." if len(desc_title) > 25 else desc_title
        title_text = small_font.render(desc_title, True, (150, 200, 255))
    overlay.blit(title_text, (desc_box_x + 10, desc_box_y + 10))
    
    # Draw description text with word wrapping (respect newlines for cost display)
    paragraphs = desc_text.split('\n')  # Split by newlines first
    lines = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():  # Empty line
            lines.append("")
            continue
            
        words = paragraph.split()
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            test_width = small_font.size(test_line)[0]
            if test_width <= desc_box_width - 20:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
    
    # Draw wrapped text (limit to fit in box)
    max_lines = 9  # Increased from 6 to 9 lines to fit larger box
    y_offset = 35
    for i, line in enumerate(lines[:max_lines]):
        if i == max_lines - 1 and len(lines) > max_lines:
            line = line[:60] + "..." if len(line) > 60 else line  # Increased character limit for wider box
        line_text = small_font.render(line, True, (200, 200, 200))
        overlay.blit(line_text, (desc_box_x + 10, desc_box_y + y_offset + i * 18))
    
    # Blit the complete overlay to the screen at the correct menu position
    screen.blit(overlay, (menu_box_x, menu_box_y))

def draw_scaling_section(surface, custom_move, scaling_selected, scaling_names, y_pos, font, small_font, is_active):
    """Draw the scaling customization section"""
    section_text = font.render("Stat Scaling (0-10):", True, (255, 255, 255))
    surface.blit(section_text, (50, y_pos))
    
    for i, stat_name in enumerate(scaling_names):
        item_y = y_pos + 50 + i * 40
        value = custom_move['scaling'][stat_name]
        
        # Highlight selected stat
        if is_active and i == scaling_selected:
            color = (100, 255, 100)
            text_color = (0, 0, 0)
        else:
            color = (60, 60, 60)
            text_color = (255, 255, 255)
        
        # Draw stat box
        stat_box = pygame.Rect(50, item_y - 5, 300, 30)
        pygame.draw.rect(surface, color, stat_box, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), stat_box, 2, border_radius=5)
        
        stat_text = small_font.render(f"{stat_name.upper()}: {value}", True, text_color)
        surface.blit(stat_text, (60, item_y))

def draw_accuracy_section(surface, custom_move, accuracy_options, accuracy_selected, y_pos, font, small_font, is_active):
    """Draw the accuracy customization section"""
    section_text = font.render("Accuracy:", True, (255, 255, 255))
    surface.blit(section_text, (50, y_pos))
    
    accuracy_value = custom_move['accuracy']
    
    # Highlight if active
    if is_active:
        color = (100, 255, 100)
        text_color = (0, 0, 0)
    else:
        color = (60, 60, 60)
        text_color = (255, 255, 255)
    
    # Draw accuracy box
    accuracy_box = pygame.Rect(50, y_pos + 40, 200, 30)
    pygame.draw.rect(surface, color, accuracy_box, border_radius=5)
    pygame.draw.rect(surface, (150, 150, 150), accuracy_box, 2, border_radius=5)
    
    accuracy_text = small_font.render(f"{accuracy_value}%", True, text_color)
    surface.blit(accuracy_text, (60, y_pos + 45))

def draw_enhanced_effects_section(surface, available_effects, effects_selected, y_pos, font, small_font, is_active, effects_scroll_offset=0, max_visible=8):
    """Draw the enhanced effects section with scrolling support"""
    section_text = font.render("Effects & Properties:", True, (255, 255, 255))
    surface.blit(section_text, (50, y_pos))
    
    # Calculate visible effects range
    start_idx = effects_scroll_offset
    end_idx = min(start_idx + max_visible, len(available_effects))
    
    for i in range(start_idx, end_idx):
        effect = available_effects[i]
        effect_name, level, duration, immunity = effect
        display_idx = i - start_idx  # Index for display positioning
        item_y = y_pos + 50 + display_idx * 40
        
        # Highlight selected effect
        if is_active and i == effects_selected:
            color = (100, 255, 100)
            text_color = (0, 0, 0)
        else:
            # Different color for active effects (level > 0 and duration > 0)
            if level > 0 and duration > 0:
                color = (80, 80, 120)
                text_color = (255, 255, 255)
            else:
                color = (40, 40, 40)
                text_color = (150, 150, 150)
        
        # Draw effect box - increased width by 50%
        effect_box = pygame.Rect(50, item_y - 5, 525, 30)  # Changed from 350 to 525 (50% increase)
        pygame.draw.rect(surface, color, effect_box, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), effect_box, 2, border_radius=5)
        
        # Check if this is a property effect and display accordingly
        if STATUS_CONFIG_AVAILABLE and is_property_effect(effect_name):
            # Property effects: show only name and ON/OFF status
            if level > 0:
                effect_text = small_font.render(f"{effect_name}: ON (Property)", True, text_color)
            else:
                effect_text = small_font.render(f"{effect_name}: OFF (Property)", True, text_color)
        else:
            # Regular effects: show level and duration
            effect_text = small_font.render(f"{effect_name}: Level {level}, Duration {duration}", True, text_color)
        
        surface.blit(effect_text, (60, item_y))
        
        if level == 0 and duration == 0:
            disabled_text = small_font.render("(Disabled)", True, (100, 100, 100))
            # Position disabled text at the far right of the box
            disabled_x = effect_box.x + effect_box.width - disabled_text.get_width() - 10
            surface.blit(disabled_text, (disabled_x, item_y))
    
    # Draw scroll indicators if needed
    if len(available_effects) > max_visible:
        # Draw scrollbar on the right side of effects area
        scrollbar_x = 580  # Right side of effects boxes
        scrollbar_y = y_pos + 50
        scrollbar_width = 8
        scrollbar_height = max_visible * 40
        
        # Scrollbar background
        pygame.draw.rect(surface, (60, 60, 60), (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
        
        # Scrollbar thumb
        thumb_height = max(20, int(scrollbar_height * max_visible / len(available_effects)))
        thumb_y = scrollbar_y + int((effects_scroll_offset / len(available_effects)) * scrollbar_height)
        pygame.draw.rect(surface, (150, 150, 150), (scrollbar_x, thumb_y, scrollbar_width, thumb_height))

def draw_buffs_section(surface, available_buffs, buffs_selected, y_pos, font, small_font, is_active, buffs_scroll_offset=0, max_visible=8):
    """Draw the buffs customization section for BUF moves"""
    section_text = font.render("Buffs (Level 0-10):", True, (255, 255, 255))
    surface.blit(section_text, (50, y_pos))
    
    # Calculate visible buffs range
    start_idx = buffs_scroll_offset
    end_idx = min(start_idx + max_visible, len(available_buffs))
    
    for i in range(start_idx, end_idx):
        buff = available_buffs[i]
        buff_name, level = buff
        display_idx = i - start_idx  # Index for display positioning
        item_y = y_pos + 50 + display_idx * 40
        
        # Highlight selected buff
        if is_active and i == buffs_selected:
            color = (100, 255, 100)
            text_color = (0, 0, 0)
        else:
            # Different color for active buffs (level > 0)
            if level > 0:
                color = (80, 120, 80)
                text_color = (255, 255, 255)
            else:
                color = (60, 60, 60)
                text_color = (200, 200, 200)
        
        # Draw buff box
        buff_box = pygame.Rect(50, item_y, 500, 30)
        pygame.draw.rect(surface, color, buff_box, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), buff_box, 2, border_radius=5)
        
        # Draw buff info - special display for Effect-on-Hit buffs
        effect_on_hit_buffs = ['poison_spores', 'confusion_spores', 'sleep_spores', 'burning_flesh', 'moving_blades']
        if buff_name in effect_on_hit_buffs:
            # Effect-on-Hit buffs show as On/Off instead of levels
            status_text = "On" if level > 0 else "Off"
            buff_text = small_font.render(f"{buff_name.replace('_', ' ').title()}: {status_text}", True, text_color)
        else:
            # Regular buffs show levels
            buff_text = small_font.render(f"{buff_name.title()}: Level {level}", True, text_color)
        
        surface.blit(buff_text, (buff_box.x + 10, item_y + 5))
        
        # Show status for Effect-on-Hit buffs or disabled status for regular buffs
        if buff_name in effect_on_hit_buffs:
            if level == 0:
                status_text = small_font.render("(Inactive)", True, (100, 100, 100))
                status_x = buff_box.x + buff_box.width - status_text.get_width() - 10
                surface.blit(status_text, (status_x, item_y + 5))
        else:
            # Regular buffs - show disabled status
            if level == 0:
                disabled_text = small_font.render("(Disabled)", True, (100, 100, 100))
                # Position disabled text at the far right of the box
                disabled_x = buff_box.x + buff_box.width - disabled_text.get_width() - 10
                surface.blit(disabled_text, (disabled_x, item_y + 5))
    
    # Draw scroll indicators if needed
    if len(available_buffs) > max_visible:
        # Draw scrollbar on the right side of buffs area
        scrollbar_x = 580  # Right side of buff boxes
        scrollbar_y = y_pos + 50
        scrollbar_width = 8
        scrollbar_height = max_visible * 40
        
        # Scrollbar background
        pygame.draw.rect(surface, (60, 60, 60), (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
        
        # Scrollbar thumb
        thumb_height = max(20, int(scrollbar_height * max_visible / len(available_buffs)))
        thumb_y = scrollbar_y + int((buffs_scroll_offset / len(available_buffs)) * scrollbar_height)
        pygame.draw.rect(surface, (150, 150, 150), (scrollbar_x, thumb_y, scrollbar_width, thumb_height))

def draw_enhanced_requirements_section(surface, available_requirements, requirements_selected, selected_requirements, 
                                     y_pos, right_column_x, font, small_font, is_active, requirements_scroll_offset=0, max_visible=10, available_buffs=None):
    """Draw the enhanced requirements section with compatibility checking and scrolling support"""
    section_text = font.render("Requirements (max 4):", True, (255, 255, 255))
    surface.blit(section_text, (50, y_pos))
    
    # Left side - Available requirements with scrolling
    start_idx = requirements_scroll_offset
    end_idx = min(start_idx + max_visible, len(available_requirements))
    
    for i in range(start_idx, end_idx):
        req = available_requirements[i]
        display_idx = i - start_idx  # Index for display positioning
        item_y = y_pos + 50 + display_idx * 30
        
        # Check if requirement is compatible and selectable
        is_compatible = is_requirement_compatible(req, selected_requirements)
        is_selected = req in selected_requirements
        is_current = is_active and i == requirements_selected
        is_mandatory = available_buffs and is_requirement_mandatory(req, available_buffs)
        
        # Check if we have mandatory buffs active that would gray out other requirements
        has_mandatory_buffs = available_buffs and get_mandatory_requirements(available_buffs)
        should_gray_out = has_mandatory_buffs and not is_mandatory and not is_selected
        
        # Determine colors
        if not is_compatible and not is_selected:
            color = (40, 40, 40)  # Grayed out - incompatible
            text_color = (100, 100, 100)
        elif should_gray_out:
            color = (30, 30, 30)  # Extra grayed out - not allowed due to mandatory requirements
            text_color = (80, 80, 80)
        elif is_current:
            if is_mandatory:
                color = (255, 150, 100)  # Orange - mandatory and selected
                text_color = (0, 0, 0)
            else:
                color = (100, 255, 100)  # Green - currently selected
                text_color = (0, 0, 0)
        elif is_selected:
            if is_mandatory:
                color = (200, 100, 50)  # Darker orange - mandatory and already selected
                text_color = (255, 255, 255)
            else:
                color = (100, 100, 200)  # Blue - already selected
                text_color = (255, 255, 255)
        else:
            color = (60, 60, 60)  # Normal
            text_color = (255, 255, 255)
        
        # Draw requirement box
        req_box = pygame.Rect(50, item_y - 2, 300, 25)
        pygame.draw.rect(surface, color, req_box, border_radius=3)
        pygame.draw.rect(surface, (150, 150, 150), req_box, 1, border_radius=3)
        
        req_text = small_font.render(req, True, text_color)
        surface.blit(req_text, (55, item_y))
        
        # Mark selected requirements
        if is_selected:
            check_text = small_font.render("✓", True, (0, 255, 0))
            surface.blit(check_text, (320, item_y))
    
    # Draw scroll indicators if needed for available requirements
    if len(available_requirements) > max_visible:
        # Draw scrollbar on the right side of requirements area
        scrollbar_x = 355  # Right side of requirement boxes
        scrollbar_y = y_pos + 50
        scrollbar_width = 8
        scrollbar_height = max_visible * 30
        
        # Scrollbar background
        pygame.draw.rect(surface, (60, 60, 60), (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
        
        # Scrollbar thumb
        thumb_height = max(15, int(scrollbar_height * max_visible / len(available_requirements)))
        thumb_y = scrollbar_y + int((requirements_scroll_offset / len(available_requirements)) * scrollbar_height)
        pygame.draw.rect(surface, (150, 150, 150), (scrollbar_x, thumb_y, scrollbar_width, thumb_height))
    
    # Right side - Selected requirements list
    selected_text = font.render("Selected:", True, (255, 255, 255))
    surface.blit(selected_text, (right_column_x, y_pos))
    
    for i, req in enumerate(selected_requirements):
        req_y = y_pos + 50 + i * 30
        selected_req_text = small_font.render(f"{i+1}. {req}", True, (200, 255, 200))
        surface.blit(selected_req_text, (right_column_x, req_y))
    
    # Show remaining slots
    remaining_slots = 4 - len(selected_requirements)
    slots_text = small_font.render(f"Remaining slots: {remaining_slots}", True, (150, 150, 150))
    surface.blit(slots_text, (right_column_x, y_pos + 50 + len(selected_requirements) * 30))

def draw_confirm_section(surface, custom_move, player_stats, y_pos, font, small_font, is_active, available_effects):
    """Draw the confirmation section with move preview - different for ATK vs BUF moves"""
    section_text = font.render("Move Preview:", True, (255, 255, 255))
    surface.blit(section_text, (50, y_pos))
    
    preview_y = y_pos + 50
    current_y = preview_y
    
    if custom_move['type'] == 'BUF':
        # BUF move preview - show buff name/level instead of damage
        # Calculate stamina cost for BUF moves (if supported)
        try:
            _, stamina_cost = calculate_move_damage_and_stamina(player_stats, custom_move)
        except:
            stamina_cost = "N/A"
        
        # Basic info for BUF moves
        basic_info = [
            f"Name: {custom_move['name']}",
            f"Type: {custom_move['type']}",
            f"Stamina Cost: {stamina_cost}"
        ]
        
        for text in basic_info:
            preview_text = small_font.render(text, True, (200, 200, 200))
            surface.blit(preview_text, (50, current_y))
            current_y += 25
        
        # Buffs and Requirements in two columns  
        current_y += 10
        
        # Left column - Active Buffs (1/3 of window width)
        left_column_width = surface.get_width() // 3
        buffs_title = small_font.render("Active Buffs:", True, (150, 255, 150))
        surface.blit(buffs_title, (50, current_y))
        buffs_start_y = current_y + 25
        
        # Right column - Requirements (1/3 of window width, with 1/3 spacing in between)
        # Move down by one row (25px) for BUF moves to avoid overlap with description UI
        right_column_x = left_column_width + (surface.get_width() // 4)  # 1/3 spacing
        req_title = small_font.render("Requirements:", True, (255, 200, 100))
        surface.blit(req_title, (right_column_x, current_y + 25))  # Move down by 25px for BUF moves
        req_start_y = current_y + 50  # Move start position down accordingly
        
        # Draw active buffs in left column
        buffs_y = buffs_start_y
        active_buffs_found = False
        for buff in custom_move.get('buffs', []):
            if isinstance(buff, list) and len(buff) >= 2:
                buff_name, level = buff
                if level > 0:
                    buff_text = small_font.render(f"  - {buff_name.title()}: Level {level}", True, (150, 255, 150))
                    surface.blit(buff_text, (70, buffs_y))
                    buffs_y += 20
                    active_buffs_found = True
        
        if not active_buffs_found:
            no_buffs_text = small_font.render("  - None", True, (150, 150, 150))
            surface.blit(no_buffs_text, (70, buffs_y))
            buffs_y += 20
        
        # Draw requirements in right column
        req_y = req_start_y
        requirements = custom_move.get('requirements', [])
        if requirements:
            for req in requirements:
                req_text = small_font.render(f"  - {req}", True, (255, 200, 150))
                surface.blit(req_text, (right_column_x, req_y))
                req_y += 20
        else:
            no_req_text = small_font.render("  - None", True, (150, 150, 150))
            surface.blit(no_req_text, (right_column_x, req_y))
            req_y += 20
        
        # Use the maximum Y position for button placement
        current_y = max(buffs_y, req_y) + 10
    
    else:
        # ATK move preview - original behavior with damage, accuracy, etc.
        # Calculate final damage and stamina
        damage, stamina_cost = calculate_move_damage_and_stamina(player_stats, custom_move)
        
        # Basic info for ATK moves
        basic_info = [
            f"Name: {custom_move['name']}",
            f"Type: {custom_move['type']}",
            f"Damage: {damage}",
            f"Stamina Cost: {stamina_cost}",
            f"Accuracy: {custom_move['accuracy']}%",
            f"Scaling: forz={custom_move['scaling']['forz']}, des={custom_move['scaling']['des']}, spe={custom_move['scaling']['spe']}"
        ]
        
        for text in basic_info:
            preview_text = small_font.render(text, True, (200, 200, 200))
            surface.blit(preview_text, (50, current_y))
            current_y += 25
        
        # Effects and Requirements in two columns
        current_y += 10
        
        # Left column - Effects (1/3 of window width)
        left_column_width = surface.get_width() // 3
        effects_title = small_font.render("Active Effects:", True, (255, 255, 100))
        surface.blit(effects_title, (50, current_y))
        effects_start_y = current_y + 25
        
        # Right column - Requirements (1/3 of window width, with 1/3 spacing in between)
        right_column_x = left_column_width + (surface.get_width() // 4)  # 1/3 spacing
        req_title = small_font.render("Requirements:", True, (255, 200, 100))
        surface.blit(req_title, (right_column_x, current_y))
        req_start_y = current_y + 25
        
        # Get all available effects for display (including property effects)
        # Use the working available_effects list passed from the main interface
        
        # Draw effects in left column
        effects_y = effects_start_y
        active_effects_found = False
        for effect in available_effects:
            effect_name, level, duration, immunity = effect
            if level > 0:
                # Check if this is a property effect
                if STATUS_CONFIG_AVAILABLE and is_property_effect(effect_name):
                    # Property effects: show only name (no level/duration)
                    effect_text = small_font.render(f"  - {effect_name.title()}", True, (255, 150, 255))
                else:
                    # Regular effects: show level and duration
                    if duration > 0:
                        effect_text = small_font.render(f"  - {effect_name.title()}: Level {level}, Duration {duration}", True, (150, 255, 150))
                    else:
                        effect_text = small_font.render(f"  - {effect_name.title()}: Level {level}", True, (150, 255, 150))
                
                surface.blit(effect_text, (70, effects_y))
                effects_y += 20
                active_effects_found = True
        
        if not active_effects_found:
            no_effects_text = small_font.render("  - None", True, (150, 150, 150))
            surface.blit(no_effects_text, (70, effects_y))
            effects_y += 20
        
        # Draw requirements in right column
        req_y = req_start_y
        requirements = custom_move.get('requirements', [])
        if requirements:
            for req in requirements:
                req_text = small_font.render(f"  - {req}", True, (255, 200, 150))
                surface.blit(req_text, (right_column_x, req_y))
                req_y += 20
        else:
            no_req_text = small_font.render("  - None", True, (150, 150, 150))
            surface.blit(no_req_text, (right_column_x, req_y))
            req_y += 20
        
        # Use the maximum Y position for button placement
        current_y = max(effects_y, req_y) + 10
    
    # Save button positioned at bottom right (same for both move types)
    if is_active:
        button_color = (100, 255, 100)
        button_text_color = (0, 0, 0)
    else:
        button_color = (60, 60, 60)
        button_text_color = (255, 255, 255)
    
    # Position button at bottom right of the surface
    button_width, button_height = 200, 40
    button_x = surface.get_width() - button_width - 20  # 20 pixels from right edge
    # For BUF moves, no stats overlay in confirm section, so use original position
    # For ATK moves, avoid overlapping with stats box (stats box is 80 high + 20 margin = 100 pixels)
    if custom_move['type'] == 'BUF':
        button_y = surface.get_height() - button_height - 20  # Original position for BUF moves
    else:
        button_y = surface.get_height() - button_height - 120  # Higher position for ATK moves to avoid stats overlap
    
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    pygame.draw.rect(surface, button_color, button_rect, border_radius=10)
    pygame.draw.rect(surface, (150, 150, 150), button_rect, 2, border_radius=10)
    
    button_text = font.render("SAVE MOVE", True, button_text_color)
    text_x = button_rect.x + (button_rect.width - button_text.get_width()) // 2
    text_y = button_rect.y + (button_rect.height - button_text.get_height()) // 2
    surface.blit(button_text, (text_x, text_y))

def find_next_compatible_requirement(available_requirements, selected_requirements, current_index, direction=1, allow_wrap=True):
    """Find the next compatible requirement in the given direction, skipping incompatible ones"""
    total_reqs = len(available_requirements)
    if total_reqs == 0:
        return current_index
    
    start_index = current_index
    next_index = current_index
    
    # Search for the next compatible requirement
    for _ in range(total_reqs):  # Prevent infinite loop
        if allow_wrap:
            next_index = (next_index + direction) % total_reqs
        else:
            next_index = next_index + direction
            # If we go out of bounds, return current index
            if next_index < 0 or next_index >= total_reqs:
                return current_index
        
        req = available_requirements[next_index]
        
        # Check if this requirement is compatible
        if is_requirement_compatible(req, selected_requirements):
            return next_index
            
        # If we've looped back to start without finding compatible, return current
        if next_index == start_index:
            break
    
    return current_index  # No compatible requirements found

def is_requirement_compatible(new_req, existing_reqs):
    """Check if a requirement is compatible with existing requirements"""
    # Define mutually exclusive groups
    arm_requirements = ['NEEDS ARM', 'NEEDS 2 ARMS']
    leg_requirements = ['NEEDS LEG', 'NEEDS 2 LEGS']
    target_parts = ['TARGET HEAD', 'TARGET BODY', 'TARGET ARM', 'TARGET LEG']
    
    # Check for ARM conflicts (NEEDS ARM and NEEDS 2 ARMS are mutually exclusive)
    if new_req in arm_requirements:
        for existing in existing_reqs:
            if existing in arm_requirements and existing != new_req:
                return False
    
    # Check for LEG conflicts (NEEDS LEG and NEEDS 2 LEGS are mutually exclusive)
    if new_req in leg_requirements:
        for existing in existing_reqs:
            if existing in leg_requirements and existing != new_req:
                return False
    
    # Check for target exclusivity (only one target allowed)
    if new_req in target_parts:
        for existing_target in target_parts:
            if existing_target in existing_reqs and existing_target != new_req:
                return False
    
    return True

def show_final_confirmation(screen, font):
    """Show final confirmation dialog"""
    clock = pygame.time.Clock()
    selected_option = 0  # 0 = No, 1 = Yes
    last_input_time = 0
    input_delay = 200
    
    while True:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE and current_time - last_input_time > input_delay:
                    return selected_option == 1
                elif event.key in [pygame.K_a, pygame.K_LEFT] and current_time - last_input_time > input_delay:
                    selected_option = 0
                    last_input_time = current_time
                elif event.key in [pygame.K_d, pygame.K_RIGHT] and current_time - last_input_time > input_delay:
                    selected_option = 1
                    last_input_time = current_time
        
        # Draw overlay with confirmation dialog
        draw_confirmation_dialog(screen, "Are you sure?", font, selected_option)
        pygame.display.flip()
        clock.tick(60)

def show_validation_error(screen, font, error_message):
    """Show validation error dialog as overlay on current UI (non-intrusive)"""
    clock = pygame.time.Clock()
    
    # Wait for any key press to close
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                return
        
        # Draw error dialog directly on the current screen without full overlay
        draw_error_dialog(screen, error_message, font)
        pygame.display.flip()
        clock.tick(60)

def draw_error_dialog(screen, message, font):
    """Draw error dialog as a floating dialog box (like keyboard editing)"""
    # Dialog box dimensions (similar to keyboard editing style)
    dialog_width = 500
    dialog_height = 180  # Slightly smaller to be less intrusive
    dialog_x = (screen.get_width() - dialog_width) // 2
    dialog_y = (screen.get_height() - dialog_height) // 2
    
    # Draw dialog background with border (no full-screen overlay)
    pygame.draw.rect(screen, (60, 60, 80), (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=10)
    pygame.draw.rect(screen, (255, 100, 100), (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=10)
    
    # Title
    title_text = font.render("Invalid Move!", True, (255, 100, 100))
    title_rect = title_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
    screen.blit(title_text, title_rect)
    
    # Message (split by newlines)
    lines = message.split('\n')
    small_font = pygame.font.Font(None, 24)
    y_offset = 70
    for line in lines:
        if line.strip():  # Skip empty lines
            line_text = small_font.render(line.strip(), True, (255, 255, 255))
            line_rect = line_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + y_offset))
            screen.blit(line_text, line_rect)
            y_offset += 30
    
    # Instructions
    instruction_text = small_font.render("Press any key to continue", True, (200, 200, 200))
    instruction_rect = instruction_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + dialog_height - 30))
    screen.blit(instruction_text, instruction_rect)

def save_custom_moves(moves_list, player_stats=None):
    """Save custom moves to the character's save file using Save System"""
    try:
        # Import Save System
        from Save_System import SaveSystem
        
        # Get character name from player_stats or fallback to character_data.json
        character_name = None
        if player_stats and hasattr(player_stats, 'name'):
            character_name = player_stats.name
        else:
            # Fallback: try to get name from character_data.json for backward compatibility
            try:
                import json
                import os
                char_data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                            "character_data.json")
                if os.path.exists(char_data_file):
                    with open(char_data_file, 'r') as f:
                        char_data = json.load(f)
                        character_name = char_data.get('name')
            except:
                pass
        
        if not character_name:
            print("[MovesMenu] Cannot save moves: no character name available")
            return False
        
        # Use Save System to save moves to character's save file
        save_system = SaveSystem()
        
        # Load existing save data
        save_data = save_system.load_save(character_name)
        if not save_data:
            print(f"[MovesMenu] No save file found for {character_name}")
            return False
        
        # Filter out weapon moves (WPN flag) before saving - only save custom moves
        custom_moves_only = [move for move in moves_list if not is_weapon_move(move)]
        
        # Update custom moves in save data
        save_data['player']['custom_moves'] = custom_moves_only
        
        # Save back to autosave file first
        success = save_system.save_game(save_data, character_name)
        if success:
            print(f"[MovesMenu] Saved {len(custom_moves_only)} custom moves for {character_name} (autosave)")
            
            # Also trigger a complete save to update the main save file
            # This ensures both autosave and main save stay in sync
            try:
                # Try to access the main game's complete save function
                import sys
                main_module = None
                for module_name in sys.modules:
                    if 'Overworld_Main' in module_name:
                        main_module = sys.modules[module_name]
                        break
                
                if main_module and hasattr(main_module, 'create_complete_save'):
                    print("[MovesMenu] Triggering complete save to sync main save file...")
                    main_module.create_complete_save("moves_modified")
                    print("[MovesMenu] Complete save triggered successfully")
                else:
                    print("[MovesMenu] Warning: Could not trigger complete save - main game module not found")
                    
            except Exception as e:
                print(f"[MovesMenu] Warning: Could not trigger complete save: {e}")
                # This is not critical - the autosave worked and our Save System fix will preserve custom_moves
                
        else:
            print(f"[MovesMenu] Failed to save moves for {character_name}")
        
        return success
        
    except Exception as e:
        print(f"[MovesMenu] Error saving custom moves: {e}")
        return False

def load_custom_moves(player_stats=None):
    """Load custom moves from character's save file using Save System, fallback to default moves"""
    try:
        # Import Save System
        from Save_System import SaveSystem
        
        # Get character name from player_stats or fallback to character_data.json
        character_name = None
        if player_stats and hasattr(player_stats, 'name'):
            character_name = player_stats.name
        else:
            # Fallback: try to get name from character_data.json for backward compatibility
            try:
                import json
                import os
                char_data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                            "character_data.json")
                if os.path.exists(char_data_file):
                    with open(char_data_file, 'r') as f:
                        char_data = json.load(f)
                        character_name = char_data.get('name')
            except:
                pass
        
        if character_name:
            # Use Save System to load moves from character's save file
            save_system = SaveSystem()
            save_data = save_system.load_save(character_name)
            
            if save_data and 'player' in save_data and 'custom_moves' in save_data['player']:
                custom_moves = save_data['player']['custom_moves']
                if custom_moves:
                    print(f"[MovesMenu] Loaded {len(custom_moves)} custom moves for {character_name}")
                    return custom_moves
        
        # Fallback: try character_data.json for backward compatibility
        try:
            save_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                    "character_data.json")
            
            if os.path.exists(save_file):
                with open(save_file, 'r') as f:
                    save_data = json.load(f)
                
                if 'custom_moves' in save_data:
                    print("[MovesMenu] Loaded moves from legacy character_data.json")
                    return save_data['custom_moves']
        except:
            pass
        
        # Final fallback to default moves
        print("[MovesMenu] No custom moves found, using default moves")
        player_moves_obj = get_player_moves()
        # Only get basic moves, not weapon moves (weapon moves are added separately)
        return player_moves_obj.moves  # Use .moves instead of .get_all_moves() to avoid weapon move duplication
        
    except Exception as e:
        print(f"[MovesMenu] Error loading custom moves: {e}")
        # Final fallback
        player_moves_obj = get_player_moves()
        # Only get basic moves, not weapon moves (weapon moves are added separately)
        return player_moves_obj.moves  # Use .moves instead of .get_all_moves() to avoid weapon move duplication

def get_species_physical_element(species_name):
    """Get the physical element for a species from Species_Config"""
    try:
        if SPECIES_CONFIG_AVAILABLE:
            species_config = get_species_config(species_name)
            if species_config and 'normal_element' in species_config:
                return species_config['normal_element']
    except Exception as e:
        print(f"[MovesMenu] Error getting species physical element: {e}")
    
    # Fallback to IMPACT if species config not available
    return "IMPACT"

def convert_weapon_move_to_dict(weapon_move):
    """Convert a weapon move (Mossa object) to the dictionary format used by the moves menu"""
    try:
        move_dict = {
            "name": weapon_move.name,
            "type": weapon_move.tipo,  # Should be "ATK" or "BUF"
            "scaling": {
                "forz": weapon_move.sca_for,
                "des": weapon_move.sca_des,
                "spe": weapon_move.sca_spe
            },
            "effects": weapon_move.eff_appl,  # Should be in format [["effect_name", level, duration, target]]
            "requirements": weapon_move.reqs,  # Should be list like ["NEEDS ARM"]
            "elements": weapon_move.elem,  # Should be list like ["CUT", "FIRE"]
            "accuracy": weapon_move.accuracy,
            "WPN": True  # Special flag to mark as weapon move (non-editable)
        }
        return move_dict
    except Exception as e:
        print(f"[MovesMenu] Error converting weapon move {getattr(weapon_move, 'name', 'Unknown')}: {e}")
        return None

def get_weapon_moves(player_stats=None):
    """Get weapon moves from equipped weapon based on proficiency level"""
    weapon_moves = []
    
    if not EQUIPMENT_AVAILABLE:
        print("[MovesMenu] Player_Equipment not available, no weapon moves")
        return weapon_moves
    
    try:
        # Get the main player equipment object
        player_equip = get_main_player_equipment()
        if not player_equip:
            print("[MovesMenu] No player equipment found")
            return weapon_moves
        
        # Get equipped weapon
        equipped_weapon = player_equip.get_equipped_by_type('weapon')
        if not equipped_weapon:
            print("[MovesMenu] No weapon equipped")
            return weapon_moves
        
        # Get weapon class and proficiency
        weapon_class = equipped_weapon.get_weapon_class()
        if not weapon_class:
            print(f"[MovesMenu] No weapon class for {equipped_weapon.name}")
            return weapon_moves
        
        proficiency_level = player_equip.get_weapon_proficiency(weapon_class)
        print(f"[MovesMenu] Weapon: {equipped_weapon.name}, Class: {weapon_class}, Proficiency: {proficiency_level}")
        
        # Get available moves for current proficiency level
        weapon_move_objects = equipped_weapon.get_available_moves(proficiency_level)
        
        # Convert to dictionary format with WPN flag
        for move_obj in weapon_move_objects:
            move_dict = convert_weapon_move_to_dict(move_obj)
            if move_dict:
                weapon_moves.append(move_dict)
                print(f"[MovesMenu] Added weapon move: {move_dict['name']}")
        
        print(f"[MovesMenu] Total weapon moves: {len(weapon_moves)}")
        
    except Exception as e:
        print(f"[MovesMenu] Error getting weapon moves: {e}")
        import traceback
        traceback.print_exc()
    
    return weapon_moves

def is_weapon_move(move):
    """Check if a move is a weapon move (has WPN flag)"""
    return move.get("WPN", False)

def show_weapon_move_warning(screen, font):
    """Show a warning message that weapon moves cannot be edited"""
    try:
        # Create a simple modal overlay
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Create warning box
        box_width = 400
        box_height = 200
        box_x = (screen.get_width() - box_width) // 2
        box_y = (screen.get_height() - box_height) // 2
        
        pygame.draw.rect(screen, (60, 60, 80), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 3)
        
        # Warning text
        warning_text = font.render("Weapon Move", True, (255, 255, 0))
        text_rect = warning_text.get_rect(center=(box_x + box_width//2, box_y + 50))
        screen.blit(warning_text, text_rect)
        
        message_text = font.render("This move cannot be edited.", True, (255, 255, 255))
        text_rect = message_text.get_rect(center=(box_x + box_width//2, box_y + 90))
        screen.blit(message_text, text_rect)
        
        message_text2 = font.render("It depends on your weapon", True, (255, 255, 255))
        text_rect2 = message_text2.get_rect(center=(box_x + box_width//2, box_y + 120))
        screen.blit(message_text2, text_rect2)
        
        message_text3 = font.render("proficiency level.", True, (255, 255, 255))
        text_rect3 = message_text3.get_rect(center=(box_x + box_width//2, box_y + 140))
        screen.blit(message_text3, text_rect3)
        
        continue_text = font.render("Press any key to continue", True, (200, 200, 200))
        text_rect4 = continue_text.get_rect(center=(box_x + box_width//2, box_y + 170))
        screen.blit(continue_text, text_rect4)
        
        pygame.display.flip()
        
        # Wait for key press
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN:
                    waiting = False
                elif event.type == pygame.QUIT:
                    waiting = False
                    
    except Exception as e:
        print(f"[MovesMenu] Error showing weapon move warning: {e}")

def create_placeholder_move(species_name, move_number):
    """Create a placeholder Basic Attack move for the species"""
    physical_element = get_species_physical_element(species_name)
    
    placeholder_move = {
        "name": "Basic Attack",
        "type": "ATK",
        "scaling": {
            "forz": 1,  # 1 Forz scaling
            "des": 0,
            "spe": 0
        },
        "effects": [],  # No effects
        "requirements": ["NEEDS ARM"],  # 1 ARM requirement
        "elements": [physical_element],  # Species physical element
        "accuracy": 90,  # 90% accuracy
        "is_placeholder": True  # Mark as placeholder for potential UI differences
    }
    
    return placeholder_move

def is_placeholder_move(move):
    """Check if a move is a placeholder move"""
    return (move.get("is_placeholder", False) or 
            (move.get("name") == "Basic Attack" and 
             len(move.get("scaling", {}).keys()) == 3 and
             move.get("scaling", {}).get("forz") == 1 and
             move.get("scaling", {}).get("des") == 0 and
             move.get("scaling", {}).get("spe") == 0 and
             move.get("accuracy") == 90 and
             move.get("requirements") == ["NEEDS ARM"] and
             len(move.get("effects", [])) == 0))

def calculate_max_moves(player_level):
    """Calculate maximum number of moves based on player level (level + 2, max 10)"""
    return min(player_level + 2, 10)

def ensure_move_slots(player_stats):
    """Ensure player has the correct number of move slots based on their level"""
    if not player_stats:
        print("[MovesMenu] No player stats provided for move slot check")
        return []
    
    # Get player level
    player_level = getattr(player_stats, 'level', 1)
    
    # Get player species
    player_species = getattr(player_stats, 'species', 'Selkio')
    
    # Calculate how many moves the player should have
    target_move_count = calculate_max_moves(player_level)
    
    # Load current moves (excluding weapon moves)
    current_moves = load_custom_moves(player_stats)
    if not current_moves:
        current_moves = []
    
    # Filter out any existing weapon moves (they'll be re-added fresh)
    current_custom_moves = [move for move in current_moves if not is_weapon_move(move)]
    current_custom_count = len(current_custom_moves)
    
    # Get current weapon moves
    weapon_moves = get_weapon_moves(player_stats)
    weapon_moves_count = len(weapon_moves)
    
    print(f"[MovesMenu] Player level: {player_level}, Target total moves: {target_move_count}")
    print(f"[MovesMenu] Current custom moves: {current_custom_count}, Weapon moves: {weapon_moves_count}")
    
    # Calculate how many custom move slots we need (total - weapon moves)
    target_custom_count = max(0, target_move_count - weapon_moves_count)
    
    # If player needs more custom move slots, add placeholder moves
    if current_custom_count < target_custom_count:
        moves_to_add = target_custom_count - current_custom_count
        print(f"[MovesMenu] Adding {moves_to_add} placeholder moves for {player_species}")
        
        # Add placeholder moves
        for i in range(moves_to_add):
            placeholder = create_placeholder_move(player_species, current_custom_count + i + 1)
            current_custom_moves.append(placeholder)
            print(f"[MovesMenu] Added placeholder move: {placeholder['name']} with {placeholder['elements'][0]} element")
        
        # Save the updated custom moves list (without weapon moves)
        if save_custom_moves(current_custom_moves, player_stats):
            print(f"[MovesMenu] Successfully saved {len(current_custom_moves)} custom moves")
        else:
            print("[MovesMenu] Failed to save updated moves")
    
    # Combine weapon moves and custom moves for the final list
    final_moves = weapon_moves + current_custom_moves
    
    print(f"[MovesMenu] Final moves list: {len(final_moves)} total ({len(weapon_moves)} weapon + {len(current_custom_moves)} custom)")
    
    return final_moves

def handle_level_up(player_stats):
    """Public function to handle move unlock when player levels up"""
    if not player_stats:
        print("[MovesMenu] Cannot handle level up: no player stats provided")
        return False
    
    player_level = getattr(player_stats, 'level', 1)
    player_name = getattr(player_stats, 'name', 'Unknown')
    
    print(f"[MovesMenu] Handling level up for {player_name} (Level {player_level})")
    
    # Ensure player has correct number of move slots
    updated_moves = ensure_move_slots(player_stats)
    
    # Return True if new moves were added
    return len(updated_moves) > 0
