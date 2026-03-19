"""
Main Menu System for Afterdeath RPG
This menu serves as the entry point to the game and provides access to:
- New Game
- Load Game
- Options
- Battle Testing (Direct access to battle system)
- Exit
"""

import pygame
import sys
import os
import subprocess
import json
import importlib.util
import traceback
import time
from pathlib import Path

# Import Global SFX system
import Global_SFX

# Initialize Pygame
pygame.init()

# Screen constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Menu colors
MENU_BG = (20, 20, 30)
MENU_SELECTED = (100, 100, 150)
MENU_NORMAL = (60, 60, 80)
MENU_TEXT = (220, 220, 220)
MENU_TEXT_SELECTED = (255, 255, 255)

# Species selection colors
SPECIES_SELECTED_BORDER = (255, 255, 0)  # Yellow border for selected species
SPECIES_NORMAL_BORDER = (100, 100, 100)  # Gray border for normal species

class Species:
    """Class representing an undead species"""
    def __init__(self, species_name, species_icon, species_image, species_description):
        self.species_name = species_name
        self.species_icon = species_icon
        self.species_image = species_image
        self.species_description = species_description

class MainMenu:
    def __init__(self):
        # Initialize display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Afterdeath RPG - Main Menu")
        self.clock = pygame.time.Clock()
        
        # Load font
        self.load_fonts()
        
        # Menu state
        self.running = True
        self.selected_option = 0
        self.menu_options = [
            "New Game",
            "Load Game", 
            "Options",
            "Battle Test",
            "Exit"
        ]
        
        # Controller support
        self.controller = None
        self.init_controller()
        
        # Background
        self.background = None
        self.load_background()
        
        # Game settings
        self.settings_file = Path("game_settings.json")
        self.load_settings()
        
        # Apply fullscreen setting after loading settings
        self.apply_fullscreen_setting()
        
        # Species selection state
        self.in_species_selection = False
        self.selected_species_index = 0
        self.show_species_description = False  # Toggle between image and description
        self.species_list = []
        self.species_background = None
        self.load_species_data()
        
        # Character name selection state
        self.in_name_selection = False
        self.character_name = ""
        self.selected_char_row = 0
        self.selected_char_col = 0
        self.max_name_length = 16
        self.uppercase_mode = True  # Start with uppercase
        
        # Character selection grid layout (A-Z, 0-9, space, backspace)
        self.char_grid = [
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
            ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'],
            ['U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3'],
            ['4', '5', '6', '7', '8', '9', 'Spc', 'Del', 'Ok', 'Lwr']
        ]
        
        # Load game state
        self.in_load_game = False
        self.selected_save_index = 0
        self.save_files = []
        
        # Load sound effects using global SFX system
        Global_SFX.load_global_sfx_volume()  # Ensure we have the latest SFX volume
        self.load_sounds()
        
    def load_sounds(self):
        """Load menu sound effects using the global SFX system"""
        Global_SFX.load_global_sfx_volume()  # Ensure latest SFX volume is loaded
        self.menu_sound = Global_SFX.load_sound_with_global_volume(
            r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\menu-selection-102220.mp3", 0.4)
        self.confirm_sound = Global_SFX.load_sound_with_global_volume(
            r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\casual-click-pop-ui-3-262120.mp3", 0.45)
        self.cancel_sound = Global_SFX.load_sound_with_global_volume(
            r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\discard-sound-effect-221455.mp3", 1.0)
        
        if self.menu_sound:
            print("[Menu] Loaded menu navigation sound with global SFX volume.")
        if self.confirm_sound:
            print("[Menu] Loaded confirm sound with global SFX volume.")
        if self.cancel_sound:
            print("[Menu] Loaded cancel sound with global SFX volume.")
        
    def load_species_data(self):
        """Load available species data"""
        try:
            characters_path = Path("Characters_Images")
            if not characters_path.exists():
                print("[Menu] Characters_Images folder not found")
                return
                
            # Find all species by looking for _Base_Icon files
            icon_files = list(characters_path.glob("*_Base_Icon.png"))
            
            for icon_file in icon_files:
                species_name = icon_file.stem.split("_Base_Icon")[0]
                
                # Look for corresponding image file
                image_file = characters_path / f"{species_name}_Base_Image.png"
                
                if image_file.exists():
                    # Create placeholder description
                    descriptions = {
                        "Sapifer": "The Sapifer are a species of undead resembling fauns covered in bushes. their elongated upper limbs and segmented legs make them particuarly agile and nimble, and allow for movements otherwise impossible for humans. The little red spheres at the end of their fingers and toes are made of little concentric hooks, that can open and close, allowing them to cling to some surfaces. The Anatei of the Sapifer species have special digestive systems, that allow them to remember the composition of all the plants they eat, and are then able to grow small plants with the same properties of the ingested ones from the bushes that cover their bodies.",
                        "Selkio": "The Selkio are a species of undead resembling normal human skeletons. At first glance, they may seem to be alive by some sort of miracle or magic, but in reality, they posses organs and muscles of dark colour, and their bodies function in a very similar way to normal human beings and other undeads. Their thicker bone structure functions as an exoskeleton, protecting them from shear force. The Anathei of the Selkio species have special muscle tissues, that can rotate instead of contracting like normal muscles. This, combined with the absence of skin, makes them able to create rotating saws, whips and other cutting edges with their bodies.",
                        "Maedo" : "The Maedo are a species of undead resembling Humanoid jellifish. The soft and squishy memebrane that covers their skin is completely electrically insulating, but makes them vulnerable to shear forces. The tentacles that come from their earlobes are highly flexible and can be used to manipulate objects. The Anathei of the Maedo species are able to accumulate electrical charge in special organs inside their bodies, called 'Electrocytes'. On contac with a target, these organs can discharge to generate powerful electric shocks, that can be used to stun enemies, impair the use of some of their body parts and inflict serious damage.",
                        "Minnago": "The Minnago are a species of undead resembling humanoid reptiles with thick, leathery skin. Their robust build and natural armor-like hide provide excellent protection against cutting attacks. The Minnago possess heightened resistance to toxins due to their resilient physiology. The Anathei of the Minnago species are born with specialized glands in their skin that can neutralize most poisons and acids, and that, after exposure to a toxic substance, can be trained to produce them, allowing them to collect and use these substances as weapons. Some of them even learn to change the composition of their bodily fluids, to acquire resistance to elements",
                    } 
                    
                    description = descriptions.get(species_name, f"The {species_name} are mysterious undead beings with unique abilities and characteristics. They have adapted to their undead existence in remarkable ways, developing special powers that set them apart from other undead species.")
                    
                    species = Species(
                        species_name=species_name,
                        species_icon=str(icon_file),
                        species_image=str(image_file),
                        species_description=description
                    )
                    
                    self.species_list.append(species)
                    print(f"[Menu] Loaded species: {species_name}")
                    
            # Load species selection background
            species_bg_path = Path("Overworld/Menus/Main_Menu_Species_Select_V1.png")
            if species_bg_path.exists():
                self.species_background = pygame.image.load(str(species_bg_path))
                self.species_background = pygame.transform.scale(self.species_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print(f"[Menu] Loaded species background: {species_bg_path}")
            else:
                print(f"[Menu] Species background not found: {species_bg_path}")
                
        except Exception as e:
            print(f"[Menu] Error loading species data: {e}")
    
    def load_save_files(self):
        """Load available save files"""
        try:
            # Import save system from overworld directory
            save_system_path = Path("Overworld/Mappe/FilesPy/Save_System.py")
            if save_system_path.exists():
                import sys
                sys.path.append(str(save_system_path.parent))
                import importlib.util
                spec = importlib.util.spec_from_file_location("Save_System", save_system_path)
                save_system_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(save_system_module)
                
                # Create save system instance
                save_system = save_system_module.SaveSystem()
                
                # Get save files from the save system
                self.save_files = save_system.get_save_files()
                print(f"[Menu] Save directory: {save_system.saves_dir}")
                print(f"[Menu] Loaded {len(self.save_files)} save files")
                return True
            else:
                print(f"[Menu] Save system not found at {save_system_path}")
                return False
                
        except Exception as e:
            print(f"[Menu] Error loading save files: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def load_fonts(self):
        """Load the game fonts"""
        try:
            # Try to load the game's pixel font
            font_path = Path("Fonts/Pixellari.ttf")
            if not font_path.exists():
                font_path = Path("Pixellari.ttf")
            
            if font_path.exists():
                self.font_large = pygame.font.Font(str(font_path), 48)
                self.font_medium = pygame.font.Font(str(font_path), 32)
                self.font_small = pygame.font.Font(str(font_path), 24)
                print(f"[Menu] Loaded custom font: {font_path}")
            else:
                raise FileNotFoundError("Custom font not found")
                
        except Exception as e:
            print(f"[Menu] Could not load custom font: {e}")
            # Fallback to system fonts
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 20)
            
    def load_background(self):
        """Load background image if available"""
        try:
            # Load the specific start menu background
            bg_path = Path("Overworld/Menus/Start_Menu_V01.png")
            if bg_path.exists():
                self.background = pygame.image.load(str(bg_path))
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print(f"[Menu] Loaded background: {bg_path}")
            else:
                print(f"[Menu] Start menu background not found at: {bg_path}")
                self.background = None
        except Exception as e:
            print(f"[Menu] Could not load background: {e}")
            self.background = None
            
    def init_controller(self):
        """Initialize controller support"""
        try:
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
                print(f"[Menu] Controller connected: {self.controller.get_name()}")
            else:
                print("[Menu] No controller detected")
        except Exception as e:
            print(f"[Menu] Controller initialization failed: {e}")
            
    def load_settings(self):
        """Load game settings from file"""
        self.settings = {
            "music_volume": 0.7,
            "sfx_volume": 0.8,
            "fullscreen": False,
            "last_save_slot": 1
        }
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                    print("[Menu] Settings loaded successfully")
                    
                    # Sync global SFX volume with loaded settings
                    Global_SFX.set_global_sfx_volume(self.settings['sfx_volume'])
                    
        except Exception as e:
            print(f"[Menu] Could not load settings: {e}")
            # Set default SFX volume if loading failed
            Global_SFX.set_global_sfx_volume(self.settings['sfx_volume'])
            
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                print("[Menu] Settings saved successfully")
        except Exception as e:
            print(f"[Menu] Could not save settings: {e}")
            
    def apply_fullscreen_setting(self):
        """Apply the fullscreen setting to the display"""
        try:
            if self.settings['fullscreen']:
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                print("[Menu] Applied fullscreen mode")
            else:
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                print("[Menu] Applied windowed mode")
        except Exception as e:
            print(f"[Menu] Error applying fullscreen setting: {e}")
            # Fallback to windowed mode
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            
    def update_character_grid(self):
        """Update character grid based on current case mode"""
        if self.uppercase_mode:
            self.char_grid = [
                ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
                ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'],
                ['U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3'],
                ['4', '5', '6', '7', '8', '9', 'Spc', 'Del', 'Ok', 'Lwr']
            ]
        else:
            self.char_grid = [
                ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
                ['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'],
                ['u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3'],
                ['4', '5', '6', '7', '8', '9', 'Spc', 'Del', 'Ok', 'Upr']
            ]
            
    def handle_input(self, event):
        """Handle input events"""
        if event.type == pygame.QUIT:
            self.running = False
            
        # Handle name selection input
        if self.in_name_selection:
            self.handle_name_input(event)
            return
            
        # Handle species selection input
        if self.in_species_selection:
            self.handle_species_input(event)
            return
            
        # Handle load game input
        if self.in_load_game:
            self.handle_load_game_input(event)
            return
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                prev_option = self.selected_option
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                if prev_option != self.selected_option and self.menu_sound:
                    self.menu_sound.play()
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                prev_option = self.selected_option
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                if prev_option != self.selected_option and self.menu_sound:
                    self.menu_sound.play()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.confirm_sound:
                    self.confirm_sound.play()
                self.select_option()
            elif event.key == pygame.K_ESCAPE:
                if self.cancel_sound:
                    self.cancel_sound.play()
                self.running = False
                
        # Controller input
        elif self.controller:
            if event.type == pygame.JOYHATMOTION:
                if event.hat == 0:  # D-pad
                    if event.value[1] == 1:  # Up
                        prev_option = self.selected_option
                        self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                        if prev_option != self.selected_option and self.menu_sound:
                            self.menu_sound.play()
                    elif event.value[1] == -1:  # Down
                        prev_option = self.selected_option
                        self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                        if prev_option != self.selected_option and self.menu_sound:
                            self.menu_sound.play()
                        
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # X button (PlayStation) / A button (Xbox)
                    if self.confirm_sound:
                        self.confirm_sound.play()
                    self.select_option()
                elif event.button == 1:  # Circle button (PlayStation) / B button (Xbox)
                    if self.cancel_sound:
                        self.cancel_sound.play()
                    self.running = False
    
    def handle_load_game_input(self, event):
        """Handle input events during load game screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                if len(self.save_files) > 0:
                    prev_index = self.selected_save_index
                    self.selected_save_index = (self.selected_save_index - 1) % len(self.save_files)
                    if prev_index != self.selected_save_index and self.menu_sound:
                        self.menu_sound.play()
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if len(self.save_files) > 0:
                    prev_index = self.selected_save_index
                    self.selected_save_index = (self.selected_save_index + 1) % len(self.save_files)
                    if prev_index != self.selected_save_index and self.menu_sound:
                        self.menu_sound.play()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Load selected save file
                if self.confirm_sound:
                    self.confirm_sound.play()
                self.load_selected_save()
            elif event.key == pygame.K_ESCAPE:
                # Return to main menu
                if self.cancel_sound:
                    self.cancel_sound.play()
                self.in_load_game = False
                
        # Controller input for load game
        elif self.controller:
            if event.type == pygame.JOYHATMOTION:
                if event.hat == 0:  # D-pad
                    if event.value[1] == 1:  # Up
                        if len(self.save_files) > 0:
                            prev_index = self.selected_save_index
                            self.selected_save_index = (self.selected_save_index - 1) % len(self.save_files)
                            if prev_index != self.selected_save_index and self.menu_sound:
                                self.menu_sound.play()
                    elif event.value[1] == -1:  # Down
                        if len(self.save_files) > 0:
                            prev_index = self.selected_save_index
                            self.selected_save_index = (self.selected_save_index + 1) % len(self.save_files)
                            if prev_index != self.selected_save_index and self.menu_sound:
                                self.menu_sound.play()
                            
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # X button (PlayStation) / A button (Xbox)
                    if self.confirm_sound:
                        self.confirm_sound.play()
                    self.load_selected_save()
                elif event.button == 1:  # Circle button (PlayStation) / B button (Xbox)
                    if self.cancel_sound:
                        self.cancel_sound.play()
                    self.in_load_game = False
                    
    def handle_species_input(self, event):
        """Handle input events during species selection"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                if len(self.species_list) > 0:
                    prev_index = self.selected_species_index
                    self.selected_species_index = (self.selected_species_index - 1) % len(self.species_list)
                    if prev_index != self.selected_species_index and self.menu_sound:
                        self.menu_sound.play()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                if len(self.species_list) > 0:
                    prev_index = self.selected_species_index
                    self.selected_species_index = (self.selected_species_index + 1) % len(self.species_list)
                    if prev_index != self.selected_species_index and self.menu_sound:
                        self.menu_sound.play()
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                # Navigate up in species grid (for when we have more than 3 species)
                if len(self.species_list) > 0:
                    prev_index = self.selected_species_index
                    self.selected_species_index = (self.selected_species_index - 1) % len(self.species_list)
                    if prev_index != self.selected_species_index and self.menu_sound:
                        self.menu_sound.play()
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                # Navigate down in species grid (for when we have more than 3 species)
                if len(self.species_list) > 0:
                    prev_index = self.selected_species_index
                    self.selected_species_index = (self.selected_species_index + 1) % len(self.species_list)
                    if prev_index != self.selected_species_index and self.menu_sound:
                        self.menu_sound.play()
            elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                # Toggle between species image and description
                self.show_species_description = not self.show_species_description
                if self.menu_sound:
                    self.menu_sound.play()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Select species and start game
                if self.confirm_sound:
                    self.confirm_sound.play()
                self.confirm_species_selection()
            elif event.key == pygame.K_ESCAPE:
                # Return to main menu
                if self.cancel_sound:
                    self.cancel_sound.play()
                self.in_species_selection = False
                self.show_species_description = False
                
        # Controller input for species selection
        elif self.controller and event.type == pygame.JOYHATMOTION:
            if event.hat == 0:  # D-pad
                if event.value[0] == -1:  # Left
                    if len(self.species_list) > 0:
                        prev_index = self.selected_species_index
                        self.selected_species_index = (self.selected_species_index - 1) % len(self.species_list)
                        if prev_index != self.selected_species_index and self.menu_sound:
                            self.menu_sound.play()
                elif event.value[0] == 1:  # Right
                    if len(self.species_list) > 0:
                        prev_index = self.selected_species_index
                        self.selected_species_index = (self.selected_species_index + 1) % len(self.species_list)
                        if prev_index != self.selected_species_index and self.menu_sound:
                            self.menu_sound.play()
                elif event.value[1] == 1:  # Up
                    if len(self.species_list) > 0:
                        prev_index = self.selected_species_index
                        self.selected_species_index = (self.selected_species_index - 1) % len(self.species_list)
                        if prev_index != self.selected_species_index and self.menu_sound:
                            self.menu_sound.play()
                elif event.value[1] == -1:  # Down
                    if len(self.species_list) > 0:
                        prev_index = self.selected_species_index
                        self.selected_species_index = (self.selected_species_index + 1) % len(self.species_list)
                        if prev_index != self.selected_species_index and self.menu_sound:
                            self.menu_sound.play()
                        
        elif self.controller and event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # X button (PlayStation) / A button (Xbox)
                if self.confirm_sound:
                    self.confirm_sound.play()
                self.confirm_species_selection()
            elif event.button == 1:  # Circle button (PlayStation) / B button (Xbox)
                if self.cancel_sound:
                    self.cancel_sound.play()
                self.in_species_selection = False
                self.show_species_description = False
            elif event.button == 2:  # Square button (PlayStation) / X button (Xbox)
                if self.menu_sound:
                    self.menu_sound.play()
                self.show_species_description = not self.show_species_description
                    
    def handle_name_input(self, event):
        """Handle input events during character name selection"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                prev_col = self.selected_char_col
                self.selected_char_col = (self.selected_char_col - 1) % len(self.char_grid[0])
                if prev_col != self.selected_char_col and self.menu_sound:
                    self.menu_sound.play()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                prev_col = self.selected_char_col
                self.selected_char_col = (self.selected_char_col + 1) % len(self.char_grid[0])
                if prev_col != self.selected_char_col and self.menu_sound:
                    self.menu_sound.play()
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                prev_row = self.selected_char_row
                self.selected_char_row = (self.selected_char_row - 1) % len(self.char_grid)
                if prev_row != self.selected_char_row and self.menu_sound:
                    self.menu_sound.play()
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                prev_row = self.selected_char_row
                self.selected_char_row = (self.selected_char_row + 1) % len(self.char_grid)
                if prev_row != self.selected_char_row and self.menu_sound:
                    self.menu_sound.play()
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                if self.confirm_sound:
                    self.confirm_sound.play()
                self.select_character()
            elif event.key == pygame.K_ESCAPE:
                # Return to species selection
                if self.cancel_sound:
                    self.cancel_sound.play()
                self.in_name_selection = False
                self.in_species_selection = True
                
        # Controller input for name selection
        elif self.controller and event.type == pygame.JOYHATMOTION:
            if event.hat == 0:  # D-pad
                if event.value[0] == -1:  # Left
                    self.selected_char_col = (self.selected_char_col - 1) % len(self.char_grid[0])
                elif event.value[0] == 1:  # Right
                    self.selected_char_col = (self.selected_char_col + 1) % len(self.char_grid[0])
                elif event.value[1] == 1:  # Up
                    self.selected_char_row = (self.selected_char_row - 1) % len(self.char_grid)
                elif event.value[1] == -1:  # Down
                    self.selected_char_row = (self.selected_char_row + 1) % len(self.char_grid)
                    
        elif self.controller and event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # X button (PlayStation) / A button (Xbox)
                self.select_character()
            elif event.button == 1:  # Circle button (PlayStation) / B button (Xbox)
                self.in_name_selection = False
                self.in_species_selection = True
                
    def select_character(self):
        """Handle character selection from the grid"""
        if self.selected_char_row < len(self.char_grid) and self.selected_char_col < len(self.char_grid[self.selected_char_row]):
            char = self.char_grid[self.selected_char_row][self.selected_char_col]
            
            if char == 'Del':  # Delete/backspace
                if len(self.character_name) > 0:
                    self.character_name = self.character_name[:-1]
                    if self.cancel_sound:
                        self.cancel_sound.play()
            elif char == 'Ok':  # Confirm name
                if len(self.character_name) > 0:
                    if self.confirm_sound:
                        self.confirm_sound.play()
                    self.confirm_character_name()
            elif char == 'Spc':  # Space
                if len(self.character_name) < self.max_name_length:
                    self.character_name += ' '
                    if self.confirm_sound:
                        self.confirm_sound.play()
            elif char == 'Lwr':  # Switch to lowercase
                self.uppercase_mode = False
                self.update_character_grid()
                if self.menu_sound:
                    self.menu_sound.play()
            elif char == 'Upr':  # Switch to uppercase
                self.uppercase_mode = True
                self.update_character_grid()
                if self.menu_sound:
                    self.menu_sound.play()
            elif char not in ['Del', 'Ok', 'Spc', 'Lwr', 'Upr']:  # Regular character
                if len(self.character_name) < self.max_name_length:
                    self.character_name += char
                    if self.confirm_sound:
                        self.confirm_sound.play()
                    
    def confirm_character_name(self):
        """Confirm character name and create character save using Save System"""
        print(f"[Menu] Character name: {self.character_name}")
        
        try:
            # Start the game with selected species and character name
            selected_species = self.species_list[self.selected_species_index]
            print(f"[Menu] Creating character: {selected_species.species_name} named '{self.character_name}'")
            
            # Import and use Save System to create character save
            import sys
            import importlib.util
            import os
            from pathlib import Path
            
            # Load Save System from overworld directory
            save_system_path = Path("Overworld/Mappe/FilesPy/Save_System.py")
            if save_system_path.exists():
                spec = importlib.util.spec_from_file_location("Save_System", save_system_path)
                save_system_module = importlib.util.module_from_spec(spec)
                sys.path.append(str(save_system_path.parent))
                spec.loader.exec_module(save_system_module)
                
                # Create Save System instance
                save_system = save_system_module.SaveSystem()
                
                # Create a mock player_stats object with the new character data
                class MockPlayerStats:
                    def __init__(self, name, species):
                        self.name = name
                        self.species = species
                        self.level = 1
                        self.exp = 0
                        self.hp = 200
                        self.max_hp = 200
                        self.gif_path = f"C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Player_GIFs\\{species}_Player_GIF.gif"
                        self.sprite_path = f"C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\characters\\{species}_32p.png"
                        
                        # Initialize default stats based on species
                        if species == "Selkio":
                            self.regen = 25
                            self.max_regen = 25
                            self.reserve = 45
                            self.max_reserve = 50
                            self.stamina = 9
                            self.max_stamina = 14
                        elif species == "Maedo":
                            self.regen = 25
                            self.max_regen = 25
                            self.reserve = 45
                            self.max_reserve = 50
                            self.stamina = 9
                            self.max_stamina = 14
                        elif species == "Sapifer":
                            self.regen = 25
                            self.max_regen = 25
                            self.reserve = 45
                            self.max_reserve = 50
                            self.stamina = 9
                            self.max_stamina = 14
                        elif species == "Minnago":
                            self.regen = 25
                            self.max_regen = 25
                            self.reserve = 45
                            self.max_reserve = 50
                            self.stamina = 9
                            self.max_stamina = 14
                        else:
                            # Default values
                            self.regen = 25
                            self.max_regen = 25
                            self.reserve = 45
                            self.max_reserve = 50
                            self.stamina = 9
                            self.max_stamina = 14
                        
                        # Initialize body part HPs
                        self.head_hp = 30
                        self.max_head_hp = 30
                        self.body_hp = 100
                        self.max_body_hp = 100
                        self.right_arm_hp = 15
                        self.max_right_arm_hp = 15
                        self.left_arm_hp = 15
                        self.max_left_arm_hp = 15
                        self.right_leg_hp = 20
                        self.max_right_leg_hp = 20
                        self.left_leg_hp = 20
                        self.max_left_leg_hp = 20
                
                # Create mock player stats
                mock_player = MockPlayerStats(self.character_name, selected_species.species_name)
                
                # Create initial save file using Save System
                save_path = save_system.create_save_file(mock_player)
                
                if save_path:
                    print(f"[Menu] Character save created successfully: {save_path}")
                    print(f"[Menu] Character: {mock_player.name} ({mock_player.species})")
                    print(f"[Menu] Starting Overworld game...")
                    
                    # Also create legacy character_data.json for backward compatibility during transition
                    character_data = {
                        'name': self.character_name,
                        'species': selected_species.species_name,
                        'gif_path': mock_player.gif_path,
                        'sprite_path': mock_player.sprite_path
                    }
                    
                    import json
                    character_file = "character_data.json"
                    with open(character_file, 'w') as f:
                        json.dump(character_data, f, indent=2)
                    print(f"[Menu] Legacy character_data.json created for compatibility")
                    
                    # Start the Overworld
                    self.start_overworld_game()
                else:
                    raise Exception("Failed to create character save file")
            else:
                raise Exception(f"Save system not found at {save_system_path}")
            
        except Exception as e:
            print(f"[Menu] Error creating character: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message(f"Error creating character: {str(e)}")

    def select_option(self):
        """Handle menu option selection"""
        option = self.menu_options[self.selected_option]
        
        if option == "New Game":
            self.start_new_game()
        elif option == "Load Game":
            self.load_game()
        elif option == "Options":
            self.show_options()
        elif option == "Battle Test":
            self.start_battle_test()
        elif option == "Exit":
            self.running = False
            
    def start_new_game(self):
        """Start species selection screen"""
        if len(self.species_list) == 0:
            self.show_error_message("No species data found!")
            return
            
        print("[Menu] Opening species selection...")
        self.in_species_selection = True
        self.selected_species_index = 0
        self.show_species_description = False
        
    def confirm_species_selection(self):
        """Confirm species selection and transition to name selection"""
        if len(self.species_list) == 0:
            return
            
        selected_species = self.species_list[self.selected_species_index]
        print(f"[Menu] Selected species: {selected_species.species_name}")
        
        # Transition to name selection screen
        self.in_species_selection = False
        self.in_name_selection = True
        self.show_species_description = False  # Always show image during name selection
        self.character_name = ""
        self.selected_char_row = 0
        self.selected_char_col = 0
            
    def load_game(self):
        """Load a saved game"""
        print("[Menu] Load Game selected")
        # Load available save files
        if self.load_save_files():
            self.in_load_game = True
            self.selected_save_index = 0
        else:
            self.show_info_message("No save files found!")
    
    def load_selected_save(self):
        """Load the selected save file and start the game with seamless transition"""
        if not self.save_files or self.selected_save_index >= len(self.save_files):
            print("[Menu] No save file selected")
            return
            
        selected_save = self.save_files[self.selected_save_index]
        print(f"[Menu] Loading save file: {selected_save.get('filename', 'Unknown')}")
        
        try:
            # Start overworld with the selected save file using seamless transition
            overworld_file = Path("Overworld/Mappe/FilesPy/Overworld_Main_V7.py")
            
            if overworld_file.exists():
                save_path = selected_save.get('path', '')
                if not save_path:
                    print("[Menu] ERROR: Invalid save file path")
                    self.show_error_message("Invalid save file!")
                    return
                
                print(f"[Menu] Launching Overworld from: {overworld_file}")
                
                # Show loading screen with progress
                self.show_loading_transition("Loading saved game...", duration=3000)
                
                # Save current directory
                original_cwd = os.getcwd()
                overworld_file_abs = os.path.abspath(overworld_file)
                overworld_dir = os.path.dirname(overworld_file_abs)
                
                try:
                    # Change to overworld directory
                    print(f"[Menu] Changing to directory: {overworld_dir}")
                    os.chdir(overworld_dir)
                    
                    # Add overworld directory to Python path
                    if overworld_dir not in sys.path:
                        sys.path.insert(0, overworld_dir)
                    
                    # Set up the save file argument for the overworld module
                    original_argv = sys.argv.copy()
                    sys.argv = [sys.argv[0], "--load", save_path]
                    
                    # Import the overworld module dynamically
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("overworld_main", overworld_file_abs)
                    overworld_module = importlib.util.module_from_spec(spec)
                    
                    # Clear the current screen and show transition
                    self.screen.fill(BLACK)
                    font = self.font_large if hasattr(self, 'font_large') else pygame.font.Font(None, 48)
                    text = font.render("Loading Game...", True, WHITE)
                    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                    self.screen.blit(text, text_rect)
                    pygame.display.flip()
                    pygame.time.wait(1000)  # Give user time to see loading message
                    
                    # Execute the overworld module in the same window
                    print("[Menu] Executing overworld game in same process...")
                    spec.loader.exec_module(overworld_module)
                    
                    # If we get here, the overworld game has ended
                    print("[Menu] Overworld game ended, returning to menu...")
                    
                    # Restore original sys.argv, directory and path
                    sys.argv = original_argv
                    os.chdir(original_cwd)
                    if overworld_dir in sys.path:
                        sys.path.remove(overworld_dir)
                    
                    # Reinitialize the menu display
                    self.reinitialize_after_game()
                    
                except Exception as e:
                    print(f"[Menu] Error running overworld in same process: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Restore sys.argv and directory first
                    try:
                        sys.argv = original_argv
                    except:
                        pass
                    os.chdir(original_cwd)
                    if overworld_dir in sys.path:
                        sys.path.remove(overworld_dir)
                    
                    # Show error message instead of subprocess fallback
                    self.show_error_message(f"Error starting game: {str(e)}")
                    return
                    
            else:
                print(f"[Menu] ERROR: Overworld file not found at {overworld_file}")
                self.show_error_message("Game files not found!")
                
        except Exception as e:
            print(f"[Menu] Error loading save file: {e}")
            self.show_error_message(f"Error loading save: {str(e)}")
        
    def show_options(self):
        """Show options menu"""
        print("[Menu] Options selected")
        self.show_options_menu()
        
    def start_battle_test(self):
        """Start battle test mode by launching the battle menu directly in same window"""
        try:
            print("[Menu] Starting battle test...")
            battle_file = Path("Overworld/Mappe/FilesPy/Battle_Menu_Beta_V18.py")
            
            if battle_file.exists():
                # Execute battle system in same window
                original_cwd = os.getcwd()
                battle_file_abs = os.path.abspath(battle_file)
                
                # Show loading screen
                self.screen.fill(BLACK)
                font = self.font_large if hasattr(self, 'font_large') else pygame.font.Font(None, 48)
                text = font.render("Loading Battle Test...", True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(text, text_rect)
                pygame.display.flip()
                pygame.time.wait(500)
                
                # Execute battle module in same window
                import importlib.util
                spec = importlib.util.spec_from_file_location("battle_main", battle_file_abs)
                battle_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(battle_module)
                
                # Reinitialize menu after battle
                self.reinitialize_after_game()
            else:
                print(f"[Menu] ERROR: Battle file not found at {battle_file}")
                self.show_error_message("Battle test file not found!")
                
        except Exception as e:
            print(f"[Menu] Error starting battle test: {e}")
            self.show_error_message(f"Error starting battle test: {str(e)}")

    def start_overworld_game(self):
        """Start the Overworld game after character creation with seamless transition"""
        try:
            print("[Menu] Starting Overworld game...")
            overworld_file = Path("Overworld/Mappe/FilesPy/Overworld_Main_V7.py")
            
            if overworld_file.exists():
                print(f"[Menu] Launching Overworld from: {overworld_file}")
                
                # Show loading screen with countdown
                self.show_loading_transition("Preparing Overworld...", duration=2000)
                
                # Save current directory
                original_cwd = os.getcwd()
                overworld_file_abs = os.path.abspath(overworld_file)
                overworld_dir = os.path.dirname(overworld_file_abs)
                
                try:
                    # Change to overworld directory
                    print(f"[Menu] Changing to directory: {overworld_dir}")
                    os.chdir(overworld_dir)
                    
                    # Add overworld directory to Python path
                    if overworld_dir not in sys.path:
                        sys.path.insert(0, overworld_dir)
                    
                    # Import the overworld module dynamically
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("overworld_main", overworld_file_abs)
                    overworld_module = importlib.util.module_from_spec(spec)
                    
                    # Clear the current screen and show transition
                    self.screen.fill(BLACK)
                    font = self.font_large if hasattr(self, 'font_large') else pygame.font.Font(None, 48)
                    text = font.render("Starting Game...", True, WHITE)
                    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                    self.screen.blit(text, text_rect)
                    pygame.display.flip()
                    pygame.time.wait(500)
                    
                    # Execute the overworld module in the same window
                    print("[Menu] Executing overworld game in same process...")
                    spec.loader.exec_module(overworld_module)
                    
                    # If we get here, the overworld game has ended
                    print("[Menu] Overworld game ended, returning to menu...")
                    
                    # Restore original directory and path
                    os.chdir(original_cwd)
                    if overworld_dir in sys.path:
                        sys.path.remove(overworld_dir)
                    
                    # Reinitialize the menu display
                    self.reinitialize_after_game()
                    
                except Exception as e:
                    print(f"[Menu] Error running overworld in same process: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Restore directory first
                    os.chdir(original_cwd)
                    if overworld_dir in sys.path:
                        sys.path.remove(overworld_dir)
                    
                    # Show error message instead of subprocess fallback
                    self.show_error_message(f"Error starting overworld: {str(e)}")
                    return
                    
            else:
                print(f"[Menu] ERROR: Overworld file not found at {overworld_file}")
                self.show_error_message("Overworld game file not found!")
                
        except Exception as e:
            print(f"[Menu] Error starting Overworld: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message(f"Error starting Overworld: {str(e)}")
    
    def reinitialize_after_game(self):
        """Reinitialize menu after returning from overworld game"""
        try:
            # Reinitialize pygame (the overworld might have changed settings)
            pygame.init()
            
            # Recreate the display with proper fullscreen setting
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Afterdeath RPG - Main Menu")
            
            # Apply the correct fullscreen setting
            self.apply_fullscreen_setting()
            
            # Reload fonts and background
            self.load_fonts()
            self.load_background()
            self.load_species()
            
            # Reset menu state
            self.selected_index = 0
            self.in_species_selection = False
            self.character_name = ""
            self.naming_character = False
            
            # Show welcome back message
            self.screen.fill(BLACK)
            font = self.font_large if hasattr(self, 'font_large') else pygame.font.Font(None, 48)
            text = font.render("Welcome back to the menu!", True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.wait(1000)
            
            print("[Menu] Menu successfully reinitialized after game")
            
        except Exception as e:
            print(f"[Menu] Error reinitializing menu: {e}")
            # If reinitialization fails, just continue with current state
    
    def show_loading_transition(self, message="Loading...", duration=2000):
        """Display a smooth loading transition screen"""
        start_time = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        
        while pygame.time.get_ticks() - start_time < duration:
            # Handle events to prevent window freezing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            
            # Calculate progress
            elapsed = pygame.time.get_ticks() - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Clear screen with gradient effect
            self.screen.fill(BLACK)
            
            # Draw loading message
            font = self.font_large if hasattr(self, 'font_large') else pygame.font.Font(None, 48)
            text = font.render(message, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(text, text_rect)
            
            # Draw progress bar
            bar_width = 400
            bar_height = 20
            bar_x = (SCREEN_WIDTH - bar_width) // 2
            bar_y = SCREEN_HEIGHT // 2 + 20
            
            # Background bar
            pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
            
            # Progress bar
            progress_width = int(bar_width * progress)
            pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, progress_width, bar_height))
            
            # Progress text
            progress_text = f"{int(progress * 100)}%"
            small_font = self.font_small if hasattr(self, 'font_small') else pygame.font.Font(None, 24)
            prog_text = small_font.render(progress_text, True, WHITE)
            prog_rect = prog_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height + 30))
            self.screen.blit(prog_text, prog_rect)
            
            # Loading animation dots
            dot_count = int(elapsed / 200) % 4
            dots = "." * dot_count
            dots_text = small_font.render(dots, True, WHITE)
            dots_rect = dots_text.get_rect(center=(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(dots_text, dots_rect)
            
            pygame.display.flip()
            clock.tick(60)
        
        # Final loading screen
        self.screen.fill(BLACK)
        final_text = font.render("Starting Game...", True, WHITE)
        final_rect = final_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(final_text, final_rect)
        pygame.display.flip()
        pygame.time.wait(500)  # Brief pause before transition
            
    def show_options_menu(self):
        """Show the options/settings menu"""
        options_running = True
        selected_option = 0
        options_list = [
            f"Music Volume: {int(self.settings['music_volume'] * 100)}%",
            f"SFX Volume: {int(self.settings['sfx_volume'] * 100)}%", 
            f"Fullscreen: {'ON' if self.settings['fullscreen'] else 'OFF'}",
            "Back"
        ]
        
        while options_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    options_running = False
                    self.running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        prev_option = selected_option
                        selected_option = (selected_option - 1) % len(options_list)
                        if prev_option != selected_option and self.menu_sound:
                            self.menu_sound.play()
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        prev_option = selected_option
                        selected_option = (selected_option + 1) % len(options_list)
                        if prev_option != selected_option and self.menu_sound:
                            self.menu_sound.play()
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        if selected_option < len(options_list) - 1:  # Don't adjust "Back" option
                            if self.confirm_sound:
                                self.confirm_sound.play()
                            self.adjust_setting(selected_option, -1)
                            options_list = self.update_options_list()
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        if selected_option < len(options_list) - 1:  # Don't adjust "Back" option
                            if self.confirm_sound:
                                self.confirm_sound.play()
                            self.adjust_setting(selected_option, 1)
                            options_list = self.update_options_list()
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if selected_option == len(options_list) - 1:  # Back option
                            if self.cancel_sound:
                                self.cancel_sound.play()
                            options_running = False
                        else:
                            if self.confirm_sound:
                                self.confirm_sound.play()
                            self.toggle_setting(selected_option)
                            options_list = self.update_options_list()
                    elif event.key == pygame.K_ESCAPE:
                        if self.cancel_sound:
                            self.cancel_sound.play()
                        options_running = False
                        
                # Controller input for options menu
                elif self.controller:
                    if event.type == pygame.JOYHATMOTION:
                        if event.hat == 0:  # D-pad
                            if event.value[1] == 1:  # Up
                                prev_option = selected_option
                                selected_option = (selected_option - 1) % len(options_list)
                                if prev_option != selected_option and self.menu_sound:
                                    self.menu_sound.play()
                            elif event.value[1] == -1:  # Down
                                prev_option = selected_option
                                selected_option = (selected_option + 1) % len(options_list)
                                if prev_option != selected_option and self.menu_sound:
                                    self.menu_sound.play()
                            elif event.value[0] == -1:  # Left
                                if selected_option < len(options_list) - 1:  # Don't adjust "Back" option
                                    if self.confirm_sound:
                                        self.confirm_sound.play()
                                    self.adjust_setting(selected_option, -1)
                                    options_list = self.update_options_list()
                            elif event.value[0] == 1:  # Right
                                if selected_option < len(options_list) - 1:  # Don't adjust "Back" option
                                    if self.confirm_sound:
                                        self.confirm_sound.play()
                                    self.adjust_setting(selected_option, 1)
                                    options_list = self.update_options_list()
                                    
                    elif event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 0:  # X button (PlayStation) / A button (Xbox)
                            if selected_option == len(options_list) - 1:  # Back option
                                if self.cancel_sound:
                                    self.cancel_sound.play()
                                options_running = False
                            else:
                                if self.confirm_sound:
                                    self.confirm_sound.play()
                                self.toggle_setting(selected_option)
                                options_list = self.update_options_list()
                        elif event.button == 1:  # Circle button (PlayStation) / B button (Xbox)
                            if self.cancel_sound:
                                self.cancel_sound.play()
                            options_running = False
                        
            # Draw options menu
            self.draw_options_menu(options_list, selected_option)
            pygame.display.flip()
            self.clock.tick(FPS)
            
        self.save_settings()
        
    def update_options_list(self):
        """Update the options list with current values"""
        return [
            f"Music Volume: {int(self.settings['music_volume'] * 100)}%",
            f"SFX Volume: {int(self.settings['sfx_volume'] * 100)}%",
            f"Fullscreen: {'ON' if self.settings['fullscreen'] else 'OFF'}",
            "Back"
        ]
        
    def adjust_setting(self, option_index, direction):
        """Adjust a setting value"""
        if option_index == 0:  # Music Volume
            self.settings['music_volume'] = max(0, min(1, self.settings['music_volume'] + direction * 0.1))
        elif option_index == 1:  # SFX Volume
            old_volume = self.settings['sfx_volume']
            self.settings['sfx_volume'] = max(0, min(1, self.settings['sfx_volume'] + direction * 0.1))
            
            # Update global SFX volume immediately and save settings
            if old_volume != self.settings['sfx_volume']:
                Global_SFX.set_global_sfx_volume(self.settings['sfx_volume'])
                Global_SFX.update_all_tracked_sounds()
                
                # Reload our own sounds with new volume
                self.load_sounds()
                
                # Save settings immediately
                self.save_settings()
            
    def toggle_setting(self, option_index):
        """Toggle a boolean setting"""
        if option_index == 2:  # Fullscreen
            self.settings['fullscreen'] = not self.settings['fullscreen']
            # Apply fullscreen change using the dedicated method
            self.apply_fullscreen_setting()
            # Save settings immediately to persist the change
            self.save_settings()
                
    def show_error_message(self, message):
        """Show an error message"""
        self.show_message(message, RED)
        
    def show_info_message(self, message):
        """Show an info message"""
        self.show_message(message, YELLOW)
        
    def show_message(self, message, color):
        """Show a temporary message"""
        # Create a temporary surface for the message
        message_surface = self.font_medium.render(message, True, color)
        message_rect = message_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        # Show message for 2 seconds
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 2000:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                    
            self.draw()
            self.screen.blit(message_surface, message_rect)
            pygame.display.flip()
            self.clock.tick(FPS)
            
    def draw(self):
        """Draw the main menu"""
        # Handle different screens
        if self.in_name_selection:
            self.draw_name_selection()
        elif self.in_species_selection:
            self.draw_species_selection()
        elif self.in_load_game:
            self.draw_load_game_screen()
        else:
            self.draw_main_menu()
    
    def draw_main_menu(self):
        """Draw the main menu screen"""
        # Clear screen
        self.screen.fill(MENU_BG)
        
        # Draw background if available
        if self.background:
            self.screen.blit(self.background, (0, 0))
        
        # Position everything in the left portion of the screen (yellow area)
        # The yellow area appears to be roughly the left 40% of the screen
        left_area_width = int(SCREEN_WIDTH * 0.4)
        left_margin = 50
        
        # Draw title (smaller since "AFTERDEATH" is already in the image)
        title_text = self.font_medium.render("MAIN MENU", True, WHITE)
        title_rect = title_text.get_rect(x=left_margin + SCREEN_WIDTH // 9.3, y=120)
        self.screen.blit(title_text, title_rect)
        
        # Draw menu options in the left area
        menu_start_y = 200
        menu_spacing = 60
        option_width = left_area_width - (left_margin * 2) + SCREEN_WIDTH // 27
        
        for i, option in enumerate(self.menu_options):
            # Determine colors based on selection
            if i == self.selected_option:
                bg_color = (80, 60, 120)  # Dark purple for selection
                text_color = WHITE
                border_color = WHITE
            else:
                bg_color = (40, 30, 60)   # Darker purple for normal state
                text_color = (200, 200, 200)
                border_color = (100, 80, 120)
                
            # Create option rectangle in left area
            option_rect = pygame.Rect(
                left_margin, 
                menu_start_y + i * menu_spacing,
                option_width, 45
            )
            
            # Draw option background with transparency
            option_surface = pygame.Surface((option_width, 45))
            option_surface.set_alpha(180)
            option_surface.fill(bg_color)
            self.screen.blit(option_surface, (left_margin, menu_start_y + i * menu_spacing))
            
            # Draw border
            pygame.draw.rect(self.screen, border_color, option_rect, 2)
            
            # Draw option text
            option_text = self.font_small.render(option, True, text_color)
            option_text_rect = option_text.get_rect(center=option_rect.center)
            self.screen.blit(option_text, option_text_rect)
            
        # Draw controls hint in the left area
        controls_text = self.font_small.render("Arrow Keys/WASD: Navigate", True, WHITE)
        controls_rect = controls_text.get_rect(x=left_margin, y=SCREEN_HEIGHT - SCREEN_HEIGHT//6)
        self.screen.blit(controls_text, controls_rect)
        
        controls_text2 = self.font_small.render("Enter/Space: Select", True, WHITE)
        controls_rect2 = controls_text2.get_rect(x=left_margin, y=SCREEN_HEIGHT - SCREEN_HEIGHT//6 + 20)
        self.screen.blit(controls_text2, controls_rect2)

        controls_text3 = self.font_small.render("ESC: Exit", True, WHITE)
        controls_rect3 = controls_text3.get_rect(x=left_margin, y=SCREEN_HEIGHT - SCREEN_HEIGHT//6 + 40)
        self.screen.blit(controls_text3, controls_rect3)
    
    def draw_load_game_screen(self):
        """Draw the load game screen with save file list"""
        # Clear screen
        self.screen.fill(MENU_BG)
        
        # Draw background if available
        if self.background:
            self.screen.blit(self.background, (0, 0))
        
        # Position everything in the center of the screen
        center_x = SCREEN_WIDTH // 2
        left_margin = 100
        
        # Draw title
        title_text = self.font_medium.render("LOAD GAME", True, BLACK)
        title_rect = title_text.get_rect(centerx=center_x, y=80)
        self.screen.blit(title_text, title_rect)
        
        if not self.save_files:
            # No save files found
            no_saves_text = self.font_small.render("No save files found", True, BLACK)
            no_saves_rect = no_saves_text.get_rect(centerx=center_x, y=200)
            self.screen.blit(no_saves_text, no_saves_rect)
            
            back_text = self.font_small.render("Press ESC to return", True, BLACK)
            back_rect = back_text.get_rect(centerx=center_x, y=250)
            self.screen.blit(back_text, back_rect)
        else:
            # Draw save file list
            save_start_y = 150
            save_spacing = 80
            save_width = SCREEN_WIDTH - (left_margin * 2)
            save_height = 70
            
            for i, save_file in enumerate(self.save_files):
                # Determine colors based on selection
                if i == self.selected_save_index:
                    bg_color = (80, 60, 120)  # Dark purple for selection
                    text_color = WHITE
                    border_color = WHITE
                else:
                    bg_color = (40, 30, 60)   # Darker purple for normal state
                    text_color = (200, 200, 200)
                    border_color = (100, 80, 120)
                
                # Create save file rectangle
                save_rect = pygame.Rect(
                    left_margin,
                    save_start_y + i * save_spacing,
                    save_width,
                    save_height
                )
                
                # Draw save file background with transparency
                save_surface = pygame.Surface((save_width, save_height))
                save_surface.set_alpha(180)
                save_surface.fill(bg_color)
                self.screen.blit(save_surface, (left_margin, save_start_y + i * save_spacing))
                
                # Draw border
                pygame.draw.rect(self.screen, border_color, save_rect, 2)
                
                # Draw species icon on the left (if available)
                icon_size = 50
                icon_x = left_margin + 10
                icon_y = save_start_y + i * save_spacing + 10
                
                # Handle both "player" and "character" keys for backward compatibility
                character_data = save_file.get('character', save_file.get('player', {}))
                species_name = character_data.get('species', '')
                if species_name:
                    # Try to load species icon
                    try:
                        icon_path = Path(f"Characters_Images/{species_name}_Base_Icon.png")
                        if icon_path.exists():
                            icon = pygame.image.load(str(icon_path)).convert_alpha()
                            icon = pygame.transform.scale(icon, (icon_size, icon_size))
                            self.screen.blit(icon, (icon_x, icon_y))
                        else:
                            print(f"[Menu] Species icon not found: {icon_path}")
                    except Exception as e:
                        print(f"[Menu] Error loading species icon for {species_name}: {e}")
                else:
                    print(f"[Menu] No species data found in save file")
                
                # Draw save file info to the right of the icon
                info_x = icon_x + icon_size + 15
                info_y = save_start_y + i * save_spacing + 5
                
                # Character name
                char_name = character_data.get('name', 'Unknown')
                name_text = self.font_small.render(f"Name: {char_name}", True, text_color)
                self.screen.blit(name_text, (info_x, info_y))
                
                # Character level
                char_level = character_data.get('level', 1)
                level_text = self.font_small.render(f"Level: {char_level}", True, text_color)
                self.screen.blit(level_text, (info_x, info_y + 20))
                
                # Play time (if available)
                play_time = save_file.get('metadata', {}).get('playtime', 'Unknown')
                time_text = self.font_small.render(f"Time: {play_time}", True, text_color)
                self.screen.blit(time_text, (info_x, info_y + 40))
                
                # Save date (on the right side)
                save_date = save_file.get('metadata', {}).get('save_date', 'Unknown')
                date_text = self.font_small.render(f"Saved: {save_date}", True, text_color)
                date_rect = date_text.get_rect()
                date_rect.right = save_rect.right - 10
                date_rect.y = info_y + 20
                self.screen.blit(date_text, date_rect)
        
        # Draw controls hint
        controls_y = SCREEN_HEIGHT - 100
        controls_text = self.font_small.render("Arrow Keys/WASD: Navigate", True, BLACK)
        controls_rect = controls_text.get_rect(centerx=center_x, y=controls_y)
        self.screen.blit(controls_text, controls_rect)
        
        controls_text2 = self.font_small.render("Enter/Space: Load Game", True, BLACK)
        controls_rect2 = controls_text2.get_rect(centerx=center_x, y=controls_y + 20)
        self.screen.blit(controls_text2, controls_rect2)
        
        controls_text3 = self.font_small.render("ESC: Back to Main Menu", True, BLACK)
        controls_rect3 = controls_text3.get_rect(centerx=center_x, y=controls_y + 40)
        self.screen.blit(controls_text3, controls_rect3)
        
    def draw_options_menu(self, options_list, selected_option):
        """Draw the options menu"""
        # Clear screen
        self.screen.fill(MENU_BG)
        
        # Draw background if available
        if self.background:
            self.screen.blit(self.background, (0, 0))
        
        # Position everything in the left portion of the screen (yellow area)
        left_area_width = int(SCREEN_WIDTH * 0.4)
        left_margin = 50
        
        # Draw title
        title_text = self.font_medium.render("OPTIONS", True, BLACK)
        title_rect = title_text.get_rect(x=left_margin, y=120)
        self.screen.blit(title_text, title_rect)
        
        # Draw options in the left area
        menu_start_y = 200
        menu_spacing = 60
        option_width = left_area_width - (left_margin * 2)
        
        for i, option in enumerate(options_list):
            if i == selected_option:
                bg_color = (80, 60, 120)  # Dark purple for selection
                text_color = WHITE
                border_color = WHITE
            else:
                bg_color = (40, 30, 60)   # Darker purple for normal state
                text_color = (200, 200, 200)
                border_color = (100, 80, 120)
                
            option_rect = pygame.Rect(
                left_margin,
                menu_start_y + i * menu_spacing,
                option_width, 45
            )
            
            # Draw option background with transparency
            option_surface = pygame.Surface((option_width, 45))
            option_surface.set_alpha(180)
            option_surface.fill(bg_color)
            self.screen.blit(option_surface, (left_margin, menu_start_y + i * menu_spacing))
            
            # Draw border
            pygame.draw.rect(self.screen, border_color, option_rect, 2)
            
            option_text = self.font_small.render(option, True, text_color)
            option_text_rect = option_text.get_rect(center=option_rect.center)
            self.screen.blit(option_text, option_text_rect)
            
        # Draw controls hint in the left area
        controls_text = self.font_small.render("Arrow Keys: Navigate", True, BLACK)
        controls_rect = controls_text.get_rect(x=left_margin, y=SCREEN_HEIGHT - 100)
        self.screen.blit(controls_text, controls_rect)
        
        controls_text2 = self.font_small.render("Left/Right: Adjust", True, BLACK)
        controls_rect2 = controls_text2.get_rect(x=left_margin, y=SCREEN_HEIGHT - 80)
        self.screen.blit(controls_text2, controls_rect2)
        
        controls_text3 = self.font_small.render("Enter: Toggle", True, BLACK)
        controls_rect3 = controls_text3.get_rect(x=left_margin, y=SCREEN_HEIGHT - 60)
        self.screen.blit(controls_text3, controls_rect3)
        
        controls_text4 = self.font_small.render("ESC: Back", True, BLACK)
        controls_rect4 = controls_text4.get_rect(x=left_margin, y=SCREEN_HEIGHT - 40)
        self.screen.blit(controls_text4, controls_rect4)
        
    def run(self):
        """Main menu loop"""
        print("[Menu] Main menu started")
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                self.handle_input(event)
                
            # Draw everything
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
            
        # Cleanup
        self.save_settings()
        pygame.quit()
        print("[Menu] Main menu closed")
        
    def draw_species_selection(self):
        """Draw the species selection screen"""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw background
        if self.species_background:
            self.screen.blit(self.species_background, (0, 0))
        
        # Draw species grid on the left side
        self.draw_species_grid()
        
        # Draw species image or description in the right dark area
        self.draw_species_details()
        
        # Draw controls hint
        self.draw_species_controls()
        
    def draw_species_grid(self):
        """Draw the species selection grid"""
        if len(self.species_list) == 0:
            return
            
        # Grid positioning (left side of screen) - responsive to screen size
        grid_margin_x = int(SCREEN_WIDTH * 0.005)  # 5% margin from left
        grid_margin_y = int(SCREEN_HEIGHT * 0.02)  # 15% from top
        grid_width = int(SCREEN_WIDTH * 0.55)     # 35% of screen width
        grid_height = int(SCREEN_HEIGHT * 0.85)    # 70% of screen height
        
        grid_cols = 5  # 5 columns for 20 slots
        grid_rows = 4  # 4 rows for 20 slots
        
        # Calculate slot size based on available space
        slot_width = (grid_width - grid_margin_x) // grid_cols
        slot_height = (grid_height - grid_margin_y) // grid_rows
        slot_size = min(slot_width, slot_height) - 10  # 10px spacing between slots
        
        # Calculate actual grid start position to center the grid in available space
        total_grid_width = grid_cols * (slot_size + 10) - 10
        total_grid_height = grid_rows * (slot_size + 10) - 10
        grid_start_x = grid_margin_x + (grid_width - total_grid_width) // 2
        grid_start_y = grid_margin_y + (grid_height - total_grid_height) // 2
        
        # Draw all 20 slots (empty slots will be gray)
        for row in range(grid_rows):
            for col in range(grid_cols):
                slot_index = row * grid_cols + col
                
                slot_x = grid_start_x + col * (slot_size + 10)
                slot_y = grid_start_y + row * (slot_size + 10)
                slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
                
                # Determine slot appearance
                if slot_index < len(self.species_list):
                    # This slot has a species
                    species = self.species_list[slot_index]
                    
                    # Draw slot background
                    pygame.draw.rect(self.screen, (50, 50, 50), slot_rect)
                    
                    # Draw border (yellow if selected, gray if not)
                    border_color = SPECIES_SELECTED_BORDER if slot_index == self.selected_species_index else SPECIES_NORMAL_BORDER
                    border_width = 4 if slot_index == self.selected_species_index else 2
                    pygame.draw.rect(self.screen, border_color, slot_rect, border_width)
                    
                    # Load and draw species icon
                    try:
                        icon = pygame.image.load(species.species_icon)
                        icon_size = slot_size - 15  # Leave 15px margin inside slot
                        icon = pygame.transform.scale(icon, (icon_size, icon_size))
                        icon_rect = icon.get_rect(center=slot_rect.center)
                        self.screen.blit(icon, icon_rect)
                    except Exception as e:
                        # If icon fails to load, show species name
                        text = self.font_small.render(species.species_name[:3], True, WHITE)
                        text_rect = text.get_rect(center=slot_rect.center)
                        self.screen.blit(text, text_rect)
                else:
                    # Empty slot
                    pygame.draw.rect(self.screen, (30, 30, 30), slot_rect)
                    pygame.draw.rect(self.screen, (60, 60, 60), slot_rect, 2)
                    
    def draw_species_details(self):
        """Draw species image or description in the right dark area"""
        if len(self.species_list) == 0 or self.selected_species_index >= len(self.species_list):
            return
            
        selected_species = self.species_list[self.selected_species_index]
        
        # Right area dimensions (dark area in the background) - responsive to screen size
        detail_x = int(SCREEN_WIDTH * 0.565)      # Start at 60% of screen width
        detail_y = int(SCREEN_HEIGHT * 0.512)      # 55% from top
        detail_width = int(SCREEN_WIDTH * 0.44)   # 40% of screen width
        detail_height = int(SCREEN_HEIGHT * 0.90) # 80% of screen height
        
        detail_rect = pygame.Rect(detail_x, detail_y, detail_width, detail_height)
        
        if self.show_species_description:
            # Show description
            self.draw_species_description(selected_species, detail_rect)
            # Draw species name above the description box as well
            self.draw_species_name(selected_species, detail_rect)
        else:
            # Show species image with custom scale (adjust this value to change image size)
            image_scale = 1.2  # Regulable parameter for image dimension
            self.draw_species_image(selected_species, detail_rect, image_scale)
            # Draw species name above the image box
            self.draw_species_name(selected_species, detail_rect)
            
    def draw_species_image(self, species, rect, image_scale_factor=1.1, vertical_offset=0):
        """Draw the species full image centered in the dark area, with independent scaling from the centering box."""
        try:
            image = pygame.image.load(species.species_image)

            # Calculate the center area of the dark zone (avoiding the borders)
            margin = int(min(rect.width, rect.height) * 0.06)  # 6% margin
            image_area = pygame.Rect(
                rect.x + margin,
                rect.y + margin,
                rect.width - (margin * 2),
                rect.height - (margin * 2)
            )

            # Get original image dimensions
            image_rect = image.get_rect()
            
            # Calculate base scale to fit in the center area while maintaining aspect ratio
            scale_x = image_area.width / image_rect.width
            scale_y = image_area.height / image_rect.height
            base_scale = min(scale_x, scale_y)
            
            # Apply the independent image scale factor
            final_scale = base_scale * image_scale_factor

            new_width = int(image_rect.width * final_scale)
            new_height = int(image_rect.height * final_scale)

            # Use standard scaling (nearest neighbor effect can be achieved with proper pixel art)
            scaled_image = pygame.transform.scale(image, (new_width, new_height))

            # Adjust position to align the base of the image with the center of the area, with vertical offset
            image_pos = scaled_image.get_rect()
            image_pos.midbottom = (image_area.centerx, image_area.centery + vertical_offset)

            self.screen.blit(scaled_image, image_pos)

        except Exception as e:
            # If image fails to load, show error message centered
            error_text = self.font_small.render(f"Image not found: {species.species_name}", True, RED)
            error_rect = error_text.get_rect(center=rect.center)
            self.screen.blit(error_text, error_rect)
            print(f"[Menu] Error loading image: {e}")

    def draw_species_name(self, species, rect, text_size_factor=0.23, text_offset_factor=0.44):
        """Draw the species name above the species image box, centered, with adjustable size and offset."""
        try:
            # Calculate text size and offset based on screen dimensions
            text_size = int(SCREEN_HEIGHT * text_size_factor)
            text_offset = int(SCREEN_HEIGHT * text_offset_factor)

            # Use the pixelated font for the species name
            font = self.font_medium  # Assuming self.font_medium is the pixelated font
            text_surface = font.render(species.species_name, True, WHITE)

            # Position the text centered above the image box
            text_rect = text_surface.get_rect(
                center=(rect.centerx, rect.top - text_offset)
            )

            self.screen.blit(text_surface, text_rect)

        except Exception as e:
            print(f"[Menu] Error drawing species name: {e}")
            
    def draw_species_description(self, species, rect):
        """Draw the species description with text wrapping in the dark area without additional background"""
        # Calculate text area with margins
        text_margin = int(min(rect.width, rect.height) * 0.08)  # 8% margin
        # Move description box up by a smaller, more reasonable amount
        vertical_offset = int(SCREEN_HEIGHT * 0.36)  # Move up by 36% of screen height instead of 33%
        text_area = pygame.Rect(
            rect.x + text_margin,
            rect.y + text_margin - vertical_offset,
            rect.width - (text_margin * 2),
            rect.height - (text_margin * 2)
        )
        
        # Wrap text to fit in the area
        words = species.species_description.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            text_width = self.font_small.size(test_line)[0]
            
            if text_width <= text_area.width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
                
        if current_line:
            lines.append(current_line.strip())
            
        # Draw wrapped text directly on the dark background
        line_height = self.font_small.get_height() + int(SCREEN_HEIGHT * 0.01)  # Responsive line spacing
        total_text_height = len(lines) * line_height
        
        # Start at a fixed position instead of centering vertically to ensure consistency
        start_y = text_area.y  # Fixed start position independent of text length
        
        for i, line in enumerate(lines):
            if start_y + i * line_height < text_area.y + text_area.height:
                text_surface = self.font_small.render(line, True, WHITE)
                # Center text horizontally
                text_x = text_area.x + (text_area.width - text_surface.get_width()) // 2
                self.screen.blit(text_surface, (text_x, start_y + i * line_height))
                
    def draw_species_controls(self):
        """Draw control hints for species selection - responsive positioning"""
        controls = [
            "Arrow Keys/WASD: Navigate species",
            "Shift/Square: Toggle image/description", 
            "Enter/X: Confirm selection",
            "ESC/Circle: Back to main menu"
        ]
        
        # Position controls at bottom left, responsive to screen size
        start_x = int(SCREEN_WIDTH * 0.05)
        start_y = int(SCREEN_HEIGHT * 0.87)  # 87% down the screen
        line_spacing = int(SCREEN_HEIGHT * 0.025)  # 2.5% of screen height
        
        for i, control in enumerate(controls):
            text = self.font_small.render(control, True, WHITE)
            self.screen.blit(text, (start_x, start_y + i * line_spacing))
            
    def draw_name_selection(self):
        """Draw the character name selection screen"""
        # Clear screen and draw background
        self.screen.fill(MENU_BG)
        if self.species_background:
            self.screen.blit(self.species_background, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        
        # Draw name selection on the left, species image on the right
        self.draw_name_input_area()
        self.draw_character_grid()
        self.draw_selected_species_image()
        self.draw_name_selection_controls()
        
    def draw_name_input_area(self):
        """Draw the name input question and current name"""
        # Left area dimensions
        left_area_width = int(SCREEN_WIDTH * 0.5)
        left_margin = 50
        
        # Draw question text
        question_text = self.font_large.render("What is your name?", True, WHITE)
        question_rect = question_text.get_rect(x=left_margin, y=int(SCREEN_HEIGHT * 0.15))
        self.screen.blit(question_text, question_rect)
        
        # Draw character name box
        name_box_y = int(SCREEN_HEIGHT * 0.25)
        name_box_width = left_area_width - (left_margin * 2)
        name_box_height = 60
        
        name_box_rect = pygame.Rect(left_margin, name_box_y, name_box_width, name_box_height)
        pygame.draw.rect(self.screen, (40, 40, 40), name_box_rect)
        pygame.draw.rect(self.screen, WHITE, name_box_rect, 3)
        
        # Draw current character name
        if self.character_name:
            name_text = self.font_medium.render(self.character_name, True, WHITE)
        else:
            name_text = self.font_medium.render("", True, WHITE)
            
        name_text_rect = name_text.get_rect(x=left_margin + 10, centery=name_box_y + name_box_height//2)
        self.screen.blit(name_text, name_text_rect)
        
        # Draw character limit indicator
        limit_text = self.font_small.render(f"{len(self.character_name)}/{self.max_name_length}", True, GRAY)
        limit_rect = limit_text.get_rect(right=name_box_rect.right - 10, centery=name_box_y + name_box_height//2)
        self.screen.blit(limit_text, limit_rect)
        
    def draw_character_grid(self):
        """Draw the character selection grid"""
        # Grid positioning
        left_margin = 50
        grid_start_y = int(SCREEN_HEIGHT * 0.4)
        cell_size = 45
        cell_spacing = 5
        
        for row_idx, row in enumerate(self.char_grid):
            for col_idx, char in enumerate(row):
                if char == '':  # Empty cell
                    continue
                    
                cell_x = left_margin + col_idx * (cell_size + cell_spacing)
                cell_y = grid_start_y + row_idx * (cell_size + cell_spacing)
                
                cell_rect = pygame.Rect(cell_x, cell_y, cell_size, cell_size)
                
                # Determine cell appearance
                if row_idx == self.selected_char_row and col_idx == self.selected_char_col:
                    # Selected cell
                    pygame.draw.rect(self.screen, (100, 100, 150), cell_rect)
                    pygame.draw.rect(self.screen, WHITE, cell_rect, 3)
                    text_color = WHITE
                else:
                    # Normal cell
                    pygame.draw.rect(self.screen, (60, 60, 80), cell_rect)
                    pygame.draw.rect(self.screen, (100, 100, 100), cell_rect, 2)
                    text_color = (200, 200, 200)
                
                # Draw character or special button text
                if char == '←':
                    display_text = "DEL"
                elif char == ' ':
                    display_text = "SPC"
                else:
                    display_text = char
                    
                char_text = self.font_small.render(display_text, True, text_color)
                char_text_rect = char_text.get_rect(center=cell_rect.center)
                self.screen.blit(char_text, char_text_rect)
                
    def draw_selected_species_image(self):
        """Draw the selected species image on the right side"""
        if len(self.species_list) == 0 or self.selected_species_index >= len(self.species_list):
            return
            
        selected_species = self.species_list[self.selected_species_index]
        
        # Right area dimensions (same as species selection)
        detail_x = int(SCREEN_WIDTH * 0.565)
        detail_y = int(SCREEN_HEIGHT * 0.512)
        detail_width = int(SCREEN_WIDTH * 0.44)
        detail_height = int(SCREEN_HEIGHT * 0.90)
        
        detail_rect = pygame.Rect(detail_x, detail_y, detail_width, detail_height)
        
        # Always show image during name selection
        image_scale = 1.2
        self.draw_species_image(selected_species, detail_rect, image_scale)
        self.draw_species_name(selected_species, detail_rect)
        
    def draw_name_selection_controls(self):
        """Draw control hints for name selection"""
        controls = [
            "Arrow Keys/WASD: Navigate grid",
            "Space/X: Select character", 
            "ESC/Circle: Back to species selection"
        ]
        
        # Position controls at bottom left
        start_x = int(SCREEN_WIDTH * 0.05)
        start_y = int(SCREEN_HEIGHT * 0.87)
        line_spacing = int(SCREEN_HEIGHT * 0.025)
        
        for i, control in enumerate(controls):
            text = self.font_small.render(control, True, WHITE)
            self.screen.blit(text, (start_x, start_y + i * line_spacing))

    def show_game_over_screen(self):
        """Show game over screen with options to return to main menu"""
        print("[Menu] Showing game over screen...")
        
        game_over_running = True
        selected_option = 0
        options = ["Return to Main Menu", "Exit Game"]
        
        while game_over_running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over_running = False
                    self.running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        selected_option = (selected_option - 1) % len(options)
                        if self.menu_sound:
                            self.menu_sound.play()
                            
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        selected_option = (selected_option + 1) % len(options)
                        if self.menu_sound:
                            self.menu_sound.play()
                            
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.confirm_sound:
                            self.confirm_sound.play()
                            
                        if selected_option == 0:  # Return to Main Menu
                            game_over_running = False
                            # Reset menu state
                            self.selected_option = 0
                            self.in_species_selection = False
                            self.in_name_selection = False
                            self.in_load_game = False
                            
                        elif selected_option == 1:  # Exit Game
                            game_over_running = False
                            self.running = False
                            
                # Controller input
                elif event.type == pygame.JOYBUTTONDOWN:
                    if self.controller:
                        if event.button == 0:  # A button (confirm)
                            if self.confirm_sound:
                                self.confirm_sound.play()
                                
                            if selected_option == 0:
                                game_over_running = False
                            elif selected_option == 1:
                                game_over_running = False
                                self.running = False
                                
                elif event.type == pygame.JOYHATMOTION:
                    if self.controller:
                        if event.value[1] == 1:  # Up
                            selected_option = (selected_option - 1) % len(options)
                            if self.menu_sound:
                                self.menu_sound.play()
                        elif event.value[1] == -1:  # Down
                            selected_option = (selected_option + 1) % len(options)
                            if self.menu_sound:
                                self.menu_sound.play()
            
            # Draw game over screen
            self.screen.fill(BLACK)
            
            # Draw background if available
            if self.background:
                self.screen.blit(self.background, (0, 0))
            
            # Draw game over title
            title_font = self.font_title if hasattr(self, 'font_title') else pygame.font.Font(None, 72)
            title_text = title_font.render("GAME OVER", True, RED)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
            self.screen.blit(title_text, title_rect)
            
            # Draw subtitle
            subtitle_font = self.font_large if hasattr(self, 'font_large') else pygame.font.Font(None, 36)
            subtitle_text = subtitle_font.render("Death has claimed you...", True, WHITE)
            subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
            self.screen.blit(subtitle_text, subtitle_rect)
            
            # Draw options
            option_font = self.font_medium if hasattr(self, 'font_medium') else pygame.font.Font(None, 32)
            option_start_y = SCREEN_HEIGHT // 2
            
            for i, option in enumerate(options):
                color = MENU_TEXT_SELECTED if i == selected_option else MENU_TEXT
                bg_color = MENU_SELECTED if i == selected_option else MENU_NORMAL
                
                # Draw option background
                option_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, option_start_y + i * 60 - 20, 300, 50)
                pygame.draw.rect(self.screen, bg_color, option_rect)
                pygame.draw.rect(self.screen, color, option_rect, 2)
                
                # Draw option text
                option_text = option_font.render(option, True, color)
                text_rect = option_text.get_rect(center=option_rect.center)
                self.screen.blit(option_text, text_rect)
            
            pygame.display.flip()
            self.clock.tick(FPS)

def main():
    """Entry point for the main menu"""
    try:
        menu = MainMenu()
        menu.run()
    except Exception as e:
        print(f"[Menu] Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sys.exit()

if __name__ == "__main__":
    main()
