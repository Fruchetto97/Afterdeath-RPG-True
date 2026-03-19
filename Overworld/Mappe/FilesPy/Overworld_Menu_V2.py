# Overworld_Menu_V0.py
# Contains PauseMenu and all menu-related logic for the overworld
import pygame
import json
import os
import sys
import time
from pathlib import Path
from Overworld_Menu_Stats_V1 import open_stats_menu
from Overworld_Menu_Equip_V1 import open_equip_menu
from Overworld_Menu_Items_V1 import open_items_menu
from Overworld_Menu_Moves_V1 import open_moves_menu
# Update to use Skills V2 menu
from Overworld_Menu_Skills_V2 import open_skills_menu
from Player_Equipment import player_equip, get_player_equipment
from Player_Items import player_items, get_player_items
from Save_System import save_system

# Add the parent directory to sys.path to import Global_SFX
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import Global_SFX

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

class PauseMenu:
    def regenerate_selected_bodypart(self):
        # Only allow if in regen menu and enough regen points
        if not self.in_regen_menu:
            return False
        # Map selected_bodypart to stat name
        bodypart_map = [
            ('head_hp', 'max_head_hp'),
            ('body_hp', 'max_body_hp'),
            ('right_arm_hp', 'max_right_arm_hp'),
            ('left_arm_hp', 'max_left_arm_hp'),
            ('right_leg_hp', 'max_right_leg_hp'),
            ('left_leg_hp', 'max_left_leg_hp'),
            ('extral_limbs_hp', 'max_extral_limbs_hp'),
        ]
        stat, max_stat = bodypart_map[self.selected_bodypart]
        current = getattr(self.player_stats, stat, 0)
        maximum = getattr(self.player_stats, max_stat, 0)
        missing = maximum - current
        if missing <= 0:
            print(f"[PauseMenu] {stat} already at max.")
            return False
        heal_amount = min(5, missing, self.player_stats.regen)
        if heal_amount <= 0:
            print("[PauseMenu] Not enough regeneration points.")
            return False
        setattr(self.player_stats, stat, current + heal_amount)
        self.player_stats.regen = max(0, self.player_stats.regen - heal_amount)
        # Recalculate total HP
        if hasattr(self.player_stats, 'calc_hp'):
            self.player_stats.hp = self.player_stats.calc_hp()
        print(f"[PauseMenu] Healed {stat} by {heal_amount}, lost {heal_amount} regen points.")
        return True
    
    def __init__(self, screen_width, screen_height, player_stats):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.player_stats = player_stats
        self.player_img_path = player_stats.gif_path
        self.frame_png = None
        self.frame_png_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Menus\Pause_Menu_V01.png"
        self.frame_png_orig = None
        self.frame_png_size = (0, 0)
        self._set_menu_box()
        self.player_frames = []
        self.player_frame_durations = []
        self.player_frame_index = 0
        self.player_frame_timer = 0
        self.player_frame_count = 1
        self.player_img = None
        self._update_gif_scale()
        # Regeneration menu state
        self.in_regen_menu = False
        self.selected_bodypart = 0  # 0=head, 1=body, ...
        self.regen_menu_just_entered = False  # Flag to prevent immediate exit
        self.bodypart_names = [
            "Head", "Body", "Right Arm", "Left Arm", "Right Leg", "Left Leg", "Extra Limbs"
        ]
        # Exit flag for signaling to main game
        self.should_exit_to_main_menu = False
        # Equipment list
        self.player_equip = get_player_equipment(player_stats.name)
        
        # Items list
        try:
            self.player_items = get_player_items(player_stats.name)
        except (ImportError, NameError):
            # Fallback if Player_Items not available
            print("[PauseMenu] Player_Items not available, items menu will be disabled")
            self.player_items = None

        # Blinking state for selected bar (use ticks for independence)
        self.blink_on = True
        self.blink_last_switch = pygame.time.get_ticks()
        # Menu navigation state
        self.selected_menu_row = 0  # 0-3 (last row is OPTIONS)
        self.selected_menu_col = 0  # 0-1 (OPTIONS is col=0)
        self.menu_blink_on = True
        self.menu_blink_last_switch = pygame.time.get_ticks()
        # Load sounds using global SFX system
        Global_SFX.load_global_sfx_volume()  # Ensure latest SFX volume is loaded
        try:
            self.selection_sound = Global_SFX.load_sound_with_global_volume(
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\menu-selection-102220.mp3", 0.4)
        except Exception as e:
            print(f"[PauseMenu] Could not load selection sound: {e}")
            self.selection_sound = None
        # Load ESC discard sound
        try:
            self.esc_sound = Global_SFX.load_sound_with_global_volume(
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\discard-sound-effect-221455.mp3", 1.0)
        except Exception as e:
            print(f"[PauseMenu] Could not load ESC sound: {e}")
            self.esc_sound = None
        # Load SPACEBAR select sound
        try:
            self.spacebar_sound = Global_SFX.load_sound_with_global_volume(
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\casual-click-pop-ui-3-262120.mp3", 0.45)
        except Exception as e:
            print(f"[PauseMenu] Could not load SPACEBAR sound: {e}")
            self.spacebar_sound = None
            
        # System menu state
        self.in_system_menu = False
        self.system_selected_option = 0
        self.system_options = [
            "Music Volume: 70%",
            "SFX Volume: 80%", 
            "Fullscreen: OFF",
            "Save and Exit",
            "Back"
        ]
        self.game_settings = self.load_game_settings()
        self.update_system_options()
        
        # Auto-save timer (2 minutes = 120000 ms)
        self.auto_save_timer = 0
        self.auto_save_interval = 120000  # 2 minutes in milliseconds
        self.last_save_time = pygame.time.get_ticks()
        
        # Game start time for play time tracking
        self.game_start_time = time.time()
        
    def load_sounds(self):
        """Load menu sound effects using the global SFX system"""
        Global_SFX.load_global_sfx_volume()  # Ensure latest SFX volume is loaded
        try:
            self.selection_sound = Global_SFX.load_sound_with_global_volume(
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\menu-selection-102220.mp3", 0.4)
        except Exception as e:
            print(f"[PauseMenu] Could not load selection sound: {e}")
            self.selection_sound = None
        # Load ESC discard sound
        try:
            self.esc_sound = Global_SFX.load_sound_with_global_volume(
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\discard-sound-effect-221455.mp3", 1.0)
        except Exception as e:
            print(f"[PauseMenu] Could not load ESC sound: {e}")
            self.esc_sound = None
        # Load SPACEBAR select sound
        try:
            self.spacebar_sound = Global_SFX.load_sound_with_global_volume(
                r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\casual-click-pop-ui-3-262120.mp3", 0.45)
        except Exception as e:
            print(f"[PauseMenu] Could not load SPACEBAR sound: {e}")
            self.spacebar_sound = None
        print("[PauseMenu] Reloaded all menu sounds with updated SFX volume.")
        
    def enter_regen_menu(self):
        if  not self.in_regen_menu:
            print("[PauseMenu] Entering regeneration menu.")
            self.in_regen_menu = True
            self.selected_bodypart = 0
            self.regen_menu_just_entered = True

    def handle_regen_event(self, event):
        if not self.in_regen_menu:
            return
            
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            print(f"[PauseMenu] Regen menu key: {event.key}")
            if event.key in (pygame.K_ESCAPE, pygame.K_r):
                print("[PauseMenu] Exiting regeneration menu.")
                if self.esc_sound:
                    self.esc_sound.play()
                self.in_regen_menu = False
                self.regen_menu_just_entered = False
            elif event.key in (pygame.K_UP, pygame.K_w):
                print(f"[PauseMenu] Up or W pressed. Before: {self.selected_bodypart}")
                self.selected_bodypart = (self.selected_bodypart - 1) % 7
                print(f"[PauseMenu] After: {self.selected_bodypart}")
                if self.selection_sound:
                    self.selection_sound.play()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                print(f"[PauseMenu] Down or S pressed. Before: {self.selected_bodypart}")
                self.selected_bodypart = (self.selected_bodypart + 1) % 7
                print(f"[PauseMenu] After: {self.selected_bodypart}")
                if self.selection_sound:
                    self.selection_sound.play()
            elif event.key == pygame.K_SPACE:
                # Regenerate selected body part
                success = self.regenerate_selected_bodypart()
                if self.spacebar_sound:
                    self.spacebar_sound.play()
        
        # Handle controller button events
        elif event.type == pygame.JOYBUTTONDOWN:
            # Skip R1 button handling if we just entered the regen menu
            if self.regen_menu_just_entered and is_controller_button_just_pressed(event, 'r1'):
                print("[PauseMenu] Controller: Ignoring R1 - just entered regen menu.")
                self.regen_menu_just_entered = False  # Reset the flag
                return
                
            # Circle button (cancel/ESC equivalent) or R1 button (exit regen menu)
            if is_controller_button_just_pressed(event, 'circle') or is_controller_button_just_pressed(event, 'r1'):
                print("[PauseMenu] Controller: Exiting regeneration menu.")
                if self.esc_sound:
                    self.esc_sound.play()
                self.in_regen_menu = False
                self.regen_menu_just_entered = False
            # X button (confirm/spacebar equivalent)
            elif is_controller_button_just_pressed(event, 'x'):
                # Regenerate selected body part
                success = self.regenerate_selected_bodypart()
                if self.spacebar_sound:
                    self.spacebar_sound.play()
        
        # Handle controller D-pad events
        elif event.type == pygame.JOYHATMOTION:
            if is_controller_hat_just_moved(event, 'up'):
                print(f"[PauseMenu] Controller Up pressed. Before: {self.selected_bodypart}")
                self.selected_bodypart = (self.selected_bodypart - 1) % 7
                print(f"[PauseMenu] After: {self.selected_bodypart}")
                if self.selection_sound:
                    self.selection_sound.play()
            elif is_controller_hat_just_moved(event, 'down'):
                print(f"[PauseMenu] Controller Down pressed. Before: {self.selected_bodypart}")
                self.selected_bodypart = (self.selected_bodypart + 1) % 7
                print(f"[PauseMenu] After: {self.selected_bodypart}")
                if self.selection_sound:
                    self.selection_sound.play()

    def handle_menu_event(self, event):
        # Handle system menu first if active
        if self.in_system_menu:
            self.handle_system_menu_event(event)
            return
            
        # Only handle main menu if NOT in regen menu
        if self.in_regen_menu:
            return
            
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            prev_row, prev_col = self.selected_menu_row, self.selected_menu_col
            # Up
            if event.key in (pygame.K_UP, pygame.K_w):
                if self.selected_menu_row > 0:
                    self.selected_menu_row -= 1
            # Down
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self.selected_menu_row < 3:
                    self.selected_menu_row += 1
            # Left
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                if self.selected_menu_row < 3 and self.selected_menu_col > 0:
                    self.selected_menu_col -= 1
            # Right
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.selected_menu_row < 3 and self.selected_menu_col < 1:
                    self.selected_menu_col += 1
            # Snap to OPTIONS if on last row
            if self.selected_menu_row == 3:
                self.selected_menu_col = 0
            if (prev_row, prev_col) != (self.selected_menu_row, self.selected_menu_col):
                if self.selection_sound:
                    self.selection_sound.play()
            # Enter/Space to activate
            if event.key == pygame.K_SPACE:
                if self.spacebar_sound:
                    self.spacebar_sound.play()
                self.activate_selected_menu_voice()
            # ESC or Z to exit menu
            if event.key in (pygame.K_ESCAPE, pygame.K_z):
                if self.esc_sound:
                    self.esc_sound.play()
                self.visible = False

        # Handle controller button events
        elif event.type == pygame.JOYBUTTONDOWN:
            # X button (confirm/spacebar equivalent)
            if is_controller_button_just_pressed(event, 'x'):
                if self.spacebar_sound:
                    self.spacebar_sound.play()
                self.activate_selected_menu_voice()
        
        # Handle controller D-pad events
        elif event.type == pygame.JOYHATMOTION:
            prev_row, prev_col = self.selected_menu_row, self.selected_menu_col
            # Up
            if is_controller_hat_just_moved(event, 'up'):
                if self.selected_menu_row > 0:
                    self.selected_menu_row -= 1
            # Down
            elif is_controller_hat_just_moved(event, 'down'):
                if self.selected_menu_row < 3:
                    self.selected_menu_row += 1
            # Left
            elif is_controller_hat_just_moved(event, 'left'):
                if self.selected_menu_row < 3 and self.selected_menu_col > 0:
                    self.selected_menu_col -= 1
            # Right
            elif is_controller_hat_just_moved(event, 'right'):
                if self.selected_menu_row < 3 and self.selected_menu_col < 1:
                    self.selected_menu_col += 1
            # Snap to OPTIONS if on last row
            if self.selected_menu_row == 3:
                self.selected_menu_col = 0
            if (prev_row, prev_col) != (self.selected_menu_row, self.selected_menu_col):
                if self.selection_sound:
                    self.selection_sound.play()

    def activate_selected_menu_voice(self):
        # Map selection to function
        if self.selected_menu_row == 3:
            self.open_system()
        else:
            idx = self.selected_menu_row * 2 + self.selected_menu_col
            # Order matches display: ["STATS", "PARTY", "MOVES", "SKILLS", "EQUIP", "ITEMS"]
            funcs = [self.open_stats, self.open_party, self.open_moves, self.open_skills, self.open_evolve, self.open_items]
            if idx < len(funcs):
                funcs[idx]()

    def _update_gif_scale(self):
        try:
            from PIL import Image
            pil_img = Image.open(self.player_img_path)
            self.player_frames = []
            self.player_frame_durations = []
            gif_scale = 0.85
            gif_target_height = int(self.menu_box_height * gif_scale)
            aspect = pil_img.width / pil_img.height if pil_img.height != 0 else 1
            gif_target_width = int(gif_target_height * aspect)
            for frame in range(0, getattr(pil_img, 'n_frames', 1)):
                pil_img.seek(frame)
                frame_img = pil_img.convert('RGBA')
                mode = frame_img.mode
                size = frame_img.size
                data = frame_img.tobytes()
                surf = pygame.image.fromstring(data, size, mode)
                surf = pygame.transform.smoothscale(surf, (gif_target_width, gif_target_height))
                self.player_frames.append(surf)
                duration = pil_img.info.get('duration', 100)
                self.player_frame_durations.append(duration)
            self.player_frame_count = len(self.player_frames)
            self.player_img = self.player_frames[0] if self.player_frames else None
            self.gif_target_width = gif_target_width
            self.gif_target_height = gif_target_height
        except ImportError:
            print("[PauseMenu] Pillow (PIL) not installed. GIF loading may fail.")
            try:
                img = pygame.image.load(self.player_img_path).convert_alpha()
                aspect = img.get_width() / img.get_height() if img.get_height() != 0 else 1
                gif_scale = 0.7
                gif_target_height = int(self.menu_box_height * gif_scale)
                gif_target_width = int(gif_target_height * aspect)
                self.player_img = pygame.transform.smoothscale(img, (gif_target_width, gif_target_height))
                self.gif_target_width = gif_target_width
                self.gif_target_height = gif_target_height
            except Exception as e:
                print(f"[PauseMenu] Could not load player image: {e}")
                self.player_img = None
                self.gif_target_width = 120
                self.gif_target_height = int(self.menu_box_height * 0.7)
        except Exception as e:
            print(f"[PauseMenu] Could not load GIF with Pillow: {e}")
            try:
                img = pygame.image.load(self.player_img_path).convert_alpha()
                aspect = img.get_width() / img.get_height() if img.get_height() != 0 else 1
                gif_scale = 0.7
                gif_target_height = int(self.menu_box_height * gif_scale)
                gif_target_width = int(gif_target_height * aspect)
                self.player_img = pygame.transform.smoothscale(img, (gif_target_width, gif_target_height))
                self.gif_target_width = gif_target_width
                self.gif_target_height = gif_target_height
            except Exception as e2:
                print(f"[PauseMenu] Could not load player image: {e2}")
                self.player_img = None
                self.gif_target_width = 120
                self.gif_target_height = int(self.menu_box_height * 0.7)
        try:
            font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
            self.font = pygame.font.Font(font_path, 32)
            font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
            self.font_big = pygame.font.Font(font_path, font_big_size)
        except Exception as e:
            print(f"[PauseMenu] Could not load Pixellari.ttf: {e}")
            self.font = pygame.font.SysFont(None, 32, bold=True)
            font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
            self.font_big = pygame.font.SysFont(None, font_big_size, bold=True)

    def _set_menu_box(self):
        # Always keep width at 85% of screen width, height/width ratio 1:2
        menu_box_width = int(self.screen_width * 0.85)
        menu_box_height = int(menu_box_width / 2.0545454)
        # If height exceeds screen, adjust width and height
        if menu_box_height > self.screen_height:
            menu_box_height = self.screen_height
            menu_box_width = int(menu_box_height * 2)
        self.menu_box_width = menu_box_width
        self.menu_box_height = menu_box_height
        self.menu_box_x = (self.screen_width - self.menu_box_width) // 2
        self.menu_box_y = (self.screen_height - self.menu_box_height) // 2
        self.menu_surface = pygame.Surface((self.menu_box_width, self.menu_box_height), pygame.SRCALPHA)
        self.menu_surface.fill((30, 30, 40, 200))
        self._update_gif_scale()

    def reload_frame_png(self):
        try:
            self.frame_png_orig = pygame.image.load(self.frame_png_path).convert_alpha()
        except Exception as e:
            print(f"Could not load PNG frame: {e}")
            self.frame_png_orig = None
        self.update_frame_png()

    def update(self, dt):
        # Update GIF animation
        if self.player_frame_count > 1 and self.player_frames:
            self.player_frame_timer += dt
            frame_duration = self.player_frame_durations[self.player_frame_index]
            if self.player_frame_timer >= frame_duration:
                self.player_frame_timer = 0
                self.player_frame_index = (self.player_frame_index + 1) % self.player_frame_count
                self.player_img = self.player_frames[self.player_frame_index]
        
        # Reset the regen menu just entered flag after first frame
        if self.regen_menu_just_entered:
            self.regen_menu_just_entered = False
            
        # Blinking for selected bar in regen menu (independent of dt)
        now = pygame.time.get_ticks()
        if self.in_regen_menu:
            if now - self.blink_last_switch >= 250:
                self.blink_on = not self.blink_on
                self.blink_last_switch = now
        else:
            self.blink_on = True
            self.blink_last_switch = now
            
        # Blinking for selected menu voice (independent of dt)
        if not self.in_regen_menu:
            if now - self.menu_blink_last_switch >= 250:
                self.menu_blink_on = not self.menu_blink_on
                self.menu_blink_last_switch = now
        else:
            self.menu_blink_on = True
            self.menu_blink_last_switch = now
            
        # Auto-save timer
        if now - self.last_save_time >= self.auto_save_interval:
            self.auto_save_game()
            self.last_save_time = now

    def update_frame_png(self):
        if self.frame_png_orig:
            scale_factor = 1
            orig_w, orig_h = self.frame_png_orig.get_width(), self.frame_png_orig.get_height()
            scale_h = int(self.menu_box_height * scale_factor)
            scale_w = int(scale_h * (orig_w / orig_h))
            self.frame_png = pygame.transform.smoothscale(self.frame_png_orig, (scale_w, scale_h))
            self.frame_png_size = (scale_w, scale_h)
        else:
            self.frame_png = None
            self.frame_png_size = (0, 0)

    # --- New menu functions ---
    def open_stats(self):
        print("[PauseMenu] STATS menu opened.")
        # Create and show the stats menu, hide base menu
        self.visible = False
        # Pass screen dimensions and menu box dimensions to the STATS menu
        result = open_stats_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, self.player_stats)
        # After stats menu closes, keep pause menu hidden to allow normal gameplay
        # self.visible = True  # Commented out to fix regeneration/pickup blocking issue
        return result

    def open_moves(self):
        print("[PauseMenu] MOVES menu opened.")
        # Create and show the moves menu, hide base menu
        self.visible = False
        # Pass player_stats to the moves menu for damage/stamina calculations
        result = open_moves_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, self.game_settings, self.player_stats)
        # After moves menu closes, keep pause menu hidden to allow normal gameplay
        # self.visible = True  # Commented out to fix regeneration/pickup blocking issue
        return result

    def open_skills(self):
        """Open the Skills menu"""
        print("[PauseMenu] SKILLS menu opened.")
        self.visible = False
        
        try:
            # Use the same pattern as other menu functions - call the open function
            result = open_skills_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, self.player_stats)
            return result
            
        except Exception as e:
            print(f"[PauseMenu] Error opening Skills menu: {e}")
            import traceback
            traceback.print_exc()
            return True

    def open_equip(self):
        print("[PauseMenu] EQUIP menu opened.")
        # Implement equip menu logic here
        self.visible = False
        # Import the current player equipment to ensure we get updated proficiency data
        try:
            from Player_Equipment import player1
            result = open_equip_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, player1, self.player_stats)
        except ImportError:
            # Fallback to existing player_equip if Player_Equipment not available
            result = open_equip_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, self.player_equip, self.player_stats)
        # After equip menu closes, keep pause menu hidden to allow normal gameplay
        # self.visible = True  # Commented out to fix regeneration/pickup blocking issue
        return result

    def open_party(self):
        print("[PauseMenu] PARTY menu opened.")
        # Placeholder - return True to continue game without crashes
        print("[PauseMenu] PARTY menu not yet implemented - returning to pause menu")
        return True

    def open_evolve(self):
        print("[PauseMenu] EQUIP menu opened.")
        # Implement equip menu logic here
        self.visible = False
        # Import the current player equipment to ensure we get updated proficiency data
        try:
            from Player_Equipment import player1
            result = open_equip_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, player1, self.player_stats)
        except ImportError:
            # Fallback to existing player_equip if Player_Equipment not available
            result = open_equip_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, self.player_equip, self.player_stats)
        # After equip menu closes, keep pause menu hidden to allow normal gameplay
        # self.visible = True  # Commented out to fix regeneration/pickup blocking issue
        return result

    def open_items(self):
        print("[PauseMenu] ITEMS menu opened.")
        # Implement items menu logic here
        self.visible = False
        # Import the current player items to ensure we get updated data
        result = None
        try:
            from Player_Items import player1_items
            if player1_items:
                result = open_items_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, player1_items, self.player_stats)
            else:
                print("[PauseMenu] No player items available")
                result = True
        except ImportError:
            # Fallback to existing player_items if Player_Items not available
            if self.player_items:
                result = open_items_menu(self.screen_width, self.screen_height, self.menu_box_width, self.menu_box_height, self.player_items, self.player_stats)
            else:
                print("[PauseMenu] Items menu not available - Player_Items not loaded")
                result = True
        # After items menu closes, keep pause menu hidden to allow normal gameplay
        # self.visible = True  # Commented out to fix regeneration/pickup blocking issue
        return result

    def open_options(self):
        print("[PauseMenu] OPTIONS menu opened.")
        # Implement options menu logic here

    def open_system(self):
        print("[PauseMenu] SYSTEM menu opened.")
        self.in_system_menu = True
        self.system_selected_option = 0
        self.update_system_options()
        
    def load_game_settings(self):
        """Load game settings from file"""
        settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "game_settings.json")
        
        # Default settings
        settings = {
            "music_volume": 0.7,
            "sfx_volume": 0.8,
            "fullscreen": False,
            "last_save_slot": 1
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    settings.update(loaded_settings)
                    print(f"[PauseMenu] Loaded game settings")
                    
                    # Sync global SFX volume with loaded settings
                    Global_SFX.set_global_sfx_volume(settings['sfx_volume'])
                    
        except Exception as e:
            print(f"[PauseMenu] Error loading game settings: {e}")
            # Set default SFX volume if loading failed
            Global_SFX.set_global_sfx_volume(settings['sfx_volume'])
        
        return settings
    
    def save_game_settings(self):
        """Save game settings to file"""
        settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "game_settings.json")
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.game_settings, f, indent=4)
                print("[PauseMenu] Game settings saved successfully")
        except Exception as e:
            print(f"[PauseMenu] Error saving game settings: {e}")
    
    def update_system_options(self):
        """Update system options list with current values"""
        self.system_options = [
            f"Music Volume: {int(self.game_settings['music_volume'] * 100)}%",
            f"SFX Volume: {int(self.game_settings['sfx_volume'] * 100)}%",
            f"Fullscreen: {'ON' if self.game_settings['fullscreen'] else 'OFF'}",
            "Save and Exit",
            "Back"
        ]
    
    def handle_system_menu_event(self, event):
        """Handle system menu navigation and actions"""
        if not self.in_system_menu:
            return
            
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            prev_option = self.system_selected_option
            
            # Up/Down navigation
            if event.key in (pygame.K_UP, pygame.K_w):
                self.system_selected_option = (self.system_selected_option - 1) % len(self.system_options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.system_selected_option = (self.system_selected_option + 1) % len(self.system_options)
            
            # Left/Right to adjust values
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.adjust_system_setting(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.adjust_system_setting(1)
            
            # Space to activate option
            elif event.key == pygame.K_SPACE:
                if self.spacebar_sound:
                    self.spacebar_sound.play()
                self.activate_system_option()
            
            # ESC to exit system menu
            elif event.key == pygame.K_ESCAPE:
                if self.esc_sound:
                    self.esc_sound.play()
                self.in_system_menu = False
            
            # Play selection sound if option changed
            if prev_option != self.system_selected_option and self.selection_sound:
                self.selection_sound.play()
        
        # Handle controller button events
        elif event.type == pygame.JOYBUTTONDOWN:
            # X button (confirm/spacebar equivalent)
            if is_controller_button_just_pressed(event, 'x'):
                if self.spacebar_sound:
                    self.spacebar_sound.play()
                self.activate_system_option()
            # Circle button (cancel/ESC equivalent)
            elif is_controller_button_just_pressed(event, 'circle'):
                if self.esc_sound:
                    self.esc_sound.play()
                self.in_system_menu = False
        
        # Handle controller D-pad events
        elif event.type == pygame.JOYHATMOTION:
            prev_option = self.system_selected_option
            
            # Up/Down navigation
            if is_controller_hat_just_moved(event, 'up'):
                self.system_selected_option = (self.system_selected_option - 1) % len(self.system_options)
            elif is_controller_hat_just_moved(event, 'down'):
                self.system_selected_option = (self.system_selected_option + 1) % len(self.system_options)
            # Left/Right to adjust values
            elif is_controller_hat_just_moved(event, 'left'):
                self.adjust_system_setting(-1)
            elif is_controller_hat_just_moved(event, 'right'):
                self.adjust_system_setting(1)
            
            # Play selection sound if option changed
            if prev_option != self.system_selected_option and self.selection_sound:
                self.selection_sound.play()
    
    def adjust_system_setting(self, direction):
        """Adjust system setting values with left/right"""
        option = self.system_selected_option
        
        if option == 0:  # Music Volume
            self.game_settings['music_volume'] = max(0, min(1, self.game_settings['music_volume'] + direction * 0.1))
            # Apply volume change immediately
            pygame.mixer.music.set_volume(self.game_settings['music_volume'])
        elif option == 1:  # SFX Volume  
            old_volume = self.game_settings['sfx_volume']
            self.game_settings['sfx_volume'] = max(0, min(1, self.game_settings['sfx_volume'] + direction * 0.1))
            
            # Update global SFX volume and all tracked sounds
            if old_volume != self.game_settings['sfx_volume']:
                Global_SFX.set_global_sfx_volume(self.game_settings['sfx_volume'])
                Global_SFX.update_all_tracked_sounds()
                
                # Reload our own menu sounds with new volume
                self.load_sounds()
        elif option == 2:  # Fullscreen
            self.game_settings['fullscreen'] = not self.game_settings['fullscreen']
            # Note: Fullscreen change would need to be handled by main game loop
            print(f"[PauseMenu] Fullscreen setting changed to: {self.game_settings['fullscreen']}")
        
        self.update_system_options()
        self.save_game_settings()
    
    def activate_system_option(self):
        """Activate selected system option"""
        option = self.system_selected_option
        
        if option == 2:  # Fullscreen toggle
            self.game_settings['fullscreen'] = not self.game_settings['fullscreen']
            self.update_system_options()
            self.save_game_settings()
            print(f"[PauseMenu] Fullscreen toggled to: {self.game_settings['fullscreen']}")
        elif option == 3:  # Save and Exit
            print("[PauseMenu] Save and Exit selected")
            self.save_game_and_exit()
        elif option == 4:  # Back
            self.in_system_menu = False
    
    def save_game_and_exit(self):
        """Save current game state and exit to main menu"""
        print("[PauseMenu] ========== SAVE AND EXIT STARTED ==========")
        print(f"[PauseMenu] Initial state - should_exit_to_main_menu: {getattr(self, 'should_exit_to_main_menu', 'NOT_SET')}")
        
        try:
            # Access the running game module to use its centralized save function
            import sys
            main_game = sys.modules.get('__main__')
            if main_game is None:
                print('[PauseMenu] ERROR: Could not access running game module (__main__)')
                return
            
            # Use the centralized save function from the main game module
            if hasattr(main_game, 'create_complete_save'):
                print("[PauseMenu] Using centralized save function from main game")
                save_path = main_game.create_complete_save("save_and_exit")
                if save_path:
                    print(f"[PauseMenu] Game saved successfully to {save_path}")
                else:
                    print("[PauseMenu] ERROR: Save failed!")
                    return
            else:
                print("[PauseMenu] ERROR: Main game module missing create_complete_save function!")
                return
            
            # Set exit flag
            self.should_exit_to_main_menu = True
            self.in_system_menu = False
            self.visible = False
            print(f"[PauseMenu] SUCCESS: Exit flags set - should_exit_to_main_menu: {self.should_exit_to_main_menu}, in_system_menu: {self.in_system_menu}, visible: {self.visible}")
            
        except Exception as e:
            print(f"[PauseMenu] ERROR during save and exit: {e}")
            import traceback
            traceback.print_exc()
        
        print("[PauseMenu] ========== SAVE AND EXIT COMPLETED ==========")
    
    def auto_save_game(self):
        """Automatically save game state every 2 minutes"""
        print("[PauseMenu] Auto-saving game...")
        
        try:
            # TODO: Collect world state data from game
            world_data = {
                "enemies": {},  # This would come from the main game
                "interactions": {},  # This would come from the main game
                "corpse_interactions": {},  # This would come from the main game
                "map_events": {},  # This would come from the main game
                "visited_maps": []  # This would come from the main game
            }
            
            # Auto-save the game
            save_path = save_system.auto_save(
                self.player_stats,
                world_data,
                self.game_start_time
            )
            
            if save_path:
                print(f"[PauseMenu] Auto-save completed")
            else:
                print("[PauseMenu] Auto-save failed")
                
        except Exception as e:
            print(f"[PauseMenu] Error during auto-save: {e}")

    def draw(self, screen):
        self.menu_surface.fill((30, 30, 40, 200))
        self.update_frame_png()
        frame_w, frame_h = 0, 0
        frame_x, frame_y = 0, 0
        if self.frame_png:
            frame_w, frame_h = self.frame_png_size
            frame_x = 0
            frame_y = self.menu_box_height - frame_h
        # Move GIF by 1/4 of the menu PNG width to the left
        shift_left = int(frame_w // 3.65)
        # --- Draw the four bars UNDER the PNG, positioned as in the reference image ---
        # Reference positions from screenshot: bars are left-aligned, icons and labels to the left
        bar_panel_x = int(self.menu_box_width * 0.5585)  # Start of right panel
        bar_panel_y = int(self.menu_box_height * 0.16)
        bar_width = int(self.menu_box_width / 7.2)
        bar_height = int(self.menu_box_height * 0.03)
        bar_gap = int(self.menu_box_height * 0.0518)  # 50% closer
        # Health Bar
        hp_y = bar_panel_y
        hp_ratio = self.player_stats.hp / self.player_stats.max_hp if self.player_stats.max_hp > 0 else 0
        hp_bar_rect = pygame.Rect(bar_panel_x, hp_y, bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (60, 20, 20), hp_bar_rect)
        pygame.draw.rect(self.menu_surface, (200, 0, 0), (bar_panel_x, hp_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), hp_bar_rect, 2)
        # Regen Bar
        regen_y = hp_y + bar_height + bar_gap
        regen_ratio = self.player_stats.regen / self.player_stats.max_regen if self.player_stats.max_regen > 0 else 0
        regen_bar_rect = pygame.Rect(bar_panel_x, regen_y, bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (20, 20, 60), regen_bar_rect)
        pygame.draw.rect(self.menu_surface, (0, 120, 255), (bar_panel_x, regen_y, int(bar_width * regen_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), regen_bar_rect, 2)
        # Reserve Bar
        reserve_y = regen_y + bar_height + bar_gap
        reserve_ratio = self.player_stats.reserve / self.player_stats.max_reserve if self.player_stats.max_reserve > 0 else 0
        reserve_bar_rect = pygame.Rect(bar_panel_x, reserve_y, bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (60, 60, 20), reserve_bar_rect)
        pygame.draw.rect(self.menu_surface, (255, 200, 0), (bar_panel_x, reserve_y, int(bar_width * reserve_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), reserve_bar_rect, 2)
        # Stamina Bar
        stamina_y = reserve_y + bar_height + bar_gap
        stamina_ratio = self.player_stats.stamina / self.player_stats.max_stamina if self.player_stats.max_stamina > 0 else 0
        stamina_bar_rect = pygame.Rect(bar_panel_x, stamina_y, bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (20, 60, 20), stamina_bar_rect)
        pygame.draw.rect(self.menu_surface, (0, 200, 0), (bar_panel_x, stamina_y, int(bar_width * stamina_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), stamina_bar_rect, 2)
        # --- Add 7 new bars for body part HPs to the right of the original 4 bars (no labels) ---
        bodypart_bar_width = int(self.menu_box_height * 0.201)
        bodypart_bar_height = int(self.menu_box_height * 0.041)
        bodypart_bar_gap = int(self.menu_box_height * 0.012)
        bodypart_panel_x = int(self.menu_box_width * 0.792)
        bodypart_panel_y = int(self.menu_box_height * 0.113)
        # All bars use the same red color as the first one
        red_color = (200, 0, 0)
        bodypart_stats = [
            (getattr(self.player_stats, 'head_hp', 0), getattr(self.player_stats, 'max_head_hp', 1)),
            (getattr(self.player_stats, 'body_hp', 0), getattr(self.player_stats, 'max_body_hp', 1)),
            (getattr(self.player_stats, 'right_arm_hp', 0), getattr(self.player_stats, 'max_right_arm_hp', 1)),
            (getattr(self.player_stats, 'left_arm_hp', 0), getattr(self.player_stats, 'max_left_arm_hp', 1)),
            (getattr(self.player_stats, 'right_leg_hp', 0), getattr(self.player_stats, 'max_right_leg_hp', 1)),
            (getattr(self.player_stats, 'left_leg_hp', 0), getattr(self.player_stats, 'max_left_leg_hp', 1)),
            (getattr(self.player_stats, 'extral_limbs_hp', 0), getattr(self.player_stats, 'max_extral_limbs_hp', 1)),
        ]
        for i, (hp, max_hp) in enumerate(bodypart_stats):
            ratio = hp / max_hp if max_hp > 0 else 0
            bar_rect = pygame.Rect(bodypart_panel_x, bodypart_panel_y + i * (bodypart_bar_height + bodypart_bar_gap), bodypart_bar_width, bodypart_bar_height)
            # Always draw green base for selected bar, gray for others
            if self.in_regen_menu and i == self.selected_bodypart:
                pygame.draw.rect(self.menu_surface, (30, 80, 30), bar_rect)  # green background
            else:
                pygame.draw.rect(self.menu_surface, (30, 30, 30), bar_rect)
            # Draw red HP part, blinking if selected
            if self.in_regen_menu and i == self.selected_bodypart:
                if self.blink_on:
                    pygame.draw.rect(
                        self.menu_surface,
                        red_color,
                        (bodypart_panel_x, bodypart_panel_y + i * (bodypart_bar_height + bodypart_bar_gap), int(bodypart_bar_width * ratio), bodypart_bar_height)
                    )
            else:
                pygame.draw.rect(
                    self.menu_surface,
                    red_color,
                    (bodypart_panel_x, bodypart_panel_y + i * (bodypart_bar_height + bodypart_bar_gap), int(bodypart_bar_width * ratio), bodypart_bar_height)
                )
            pygame.draw.rect(self.menu_surface, (255,255,255), bar_rect, 2)
        # Draw body part names if in regen menu
        if self.in_regen_menu:
            try:
                font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
                bp_font = pygame.font.Font(font_path, max(14, int(self.menu_box_height * 0.035)))
            except Exception:
                bp_font = pygame.font.SysFont(None, max(14, int(self.menu_box_height * 0.035)), bold=True)
            for i, name in enumerate(self.bodypart_names):
                color = (255,255,255) if i != self.selected_bodypart else (0,255,0)
                label_surface = bp_font.render(name, True, color)
                label_x = bodypart_panel_x + bodypart_bar_width + 8
                label_y = bodypart_panel_y + i * (bodypart_bar_height + bodypart_bar_gap) + (bodypart_bar_height - label_surface.get_height()) // 2
                self.menu_surface.blit(label_surface, (label_x, label_y))
        # --- Draw GIF and PNG on top of bars ---
        if self.player_img and self.frame_png:
            gif_x = frame_x + (frame_w - self.gif_target_width) // 2  - shift_left
            gif_y = frame_y + (frame_h - self.gif_target_height) // 2 + 25
            self.menu_surface.blit(self.player_img, (gif_x, gif_y))
        elif self.player_img:
            gif_x = (self.menu_box_width - self.gif_target_width) // 2 - shift_left
            gif_y = (self.menu_box_height - self.gif_target_height) // 2 + 25
            self.menu_surface.blit(self.player_img, (gif_x, gif_y))
        if self.frame_png:
            png_surface = self.frame_png.copy()
            png_surface.set_alpha(255)
            self.menu_surface.blit(png_surface, (frame_x, frame_y))
        screen.blit(self.menu_surface, (self.menu_box_x, self.menu_box_y))
        # --- Draw bar labels OVER the PNG ---
        # --- Draw numbers in the format max/current value, font reduced by 60% ---
        small_font_size = max(10, int(self.menu_box_height * 0.035))
        try:
            font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
            small_font = pygame.font.Font(font_path, small_font_size)
        except Exception:
            small_font = pygame.font.SysFont(None, small_font_size, bold=True)
        label_x = bar_panel_x + bar_width + int(self.menu_box_width * 0.016)
        # Health value
        hp_text = f"{int(self.player_stats.hp)}/{int(self.player_stats.max_hp)}"
        hp_label_surface = small_font.render(hp_text, True, (255, 255, 255))
        hp_label_y = hp_y + (bar_height - small_font.get_height()) // 2
        screen.blit(hp_label_surface, (self.menu_box_x + label_x, self.menu_box_y + hp_label_y))
        # Regen value
        regen_text = f"{int(self.player_stats.regen)}/{int(self.player_stats.max_regen)}"
        regen_label_surface = small_font.render(regen_text, True, (255, 255, 255))
        regen_label_y = regen_y + (bar_height - small_font.get_height()) // 2
        screen.blit(regen_label_surface, (self.menu_box_x + label_x, self.menu_box_y + regen_label_y))
        # Reserve value
        reserve_text = f"{int(self.player_stats.reserve)}/{int(self.player_stats.max_reserve)}"
        reserve_label_surface = small_font.render(reserve_text, True, (255, 255, 255))
        reserve_label_y = reserve_y + (bar_height - small_font.get_height()) // 2
        screen.blit(reserve_label_surface, (self.menu_box_x + label_x, self.menu_box_y + reserve_label_y))
        # Stamina value
        stamina_text = f"{int(self.player_stats.stamina)}/{int(self.player_stats.max_stamina)}"
        stamina_label_surface = small_font.render(stamina_text, True, (255, 255, 255))
        stamina_label_y = stamina_y + (bar_height - small_font.get_height()) // 2
        screen.blit(stamina_label_surface, (self.menu_box_x + label_x, self.menu_box_y + stamina_label_y))
        # Draw name as before
        if self.frame_png:
            name_text = self.player_stats.name or "NO NAME"
            name_surface = self.font_big.render(name_text, True, (255,255,255))
            rect_width = name_surface.get_width() + 40
            rect_height = name_surface.get_height() + 18
            rect_x = self.menu_box_x + frame_x + (frame_w - rect_width) // 2 - shift_left
            rect_y = self.menu_box_y + frame_y + (frame_h - rect_height) // 2
            rect_x += 0
            rect_y -= frame_h // 2.25
            text_x = rect_x + (rect_width - name_surface.get_width()) // 2
            text_y = rect_y + (rect_height - name_surface.get_height()) // 2
            screen.blit(name_surface, (text_x, text_y))
        # --- Draw selected body part HP value in the center of the menu if in regen mode ---
        # Draw directly onto the main screen after menu is blitted
        if self.in_regen_menu:
            selected_hp, selected_max_hp = bodypart_stats[self.selected_bodypart]
            hp_text = f"{int(selected_hp)}/{int(selected_max_hp)}"
            try:
                font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
                # Font size: scale with menu height, always proportional
                hp_font_size = max(14, int(self.menu_box_height * 0.035))
                hp_font = pygame.font.Font(font_path, hp_font_size)
            except Exception:
                hp_font_size = max(14, int(self.menu_box_height * 0.025))
                hp_font = pygame.font.SysFont(None, hp_font_size, bold=True)
            hp_surface = hp_font.render(hp_text, True, (255,255,255))
            # Position: start from top right of menu box, offset left and down by fractions of menu size
            # This keeps it inside the small box even when resized
            offset_x = int(self.menu_box_width * 0.041)  # 4.1% of menu width to the left
            offset_y = int(self.menu_box_height * 0.373)  # 37.4% of menu height down
            hp_x = self.menu_box_x + self.menu_box_width - offset_x - hp_surface.get_width() // 2
            hp_y = self.menu_box_y + offset_y - hp_surface.get_height() // 2
            screen.blit(hp_surface, (hp_x, hp_y))


        # --- Draw 7 menu option labels at bottom right (no boxes, just text) ---
        option_names = ["STATS", "PARTY", "MOVES", "SKILLS", "EQUIP", "ITEMS", "SYSTEM"]
        box_w = int(self.menu_box_width * 0.19)
        box_h = int(self.menu_box_height * 0.09)
        box_gap_x = int(self.menu_box_width * 0.028)
        box_gap_y = int(self.menu_box_height * 0.0365)
        # Shift all option labels left and higher
        shift_left = int(self.menu_box_width * 0.072)  # 7.3% of menu width
        shift_up = int(self.menu_box_height * 0.01)   # 2% of menu height
        start_x = self.menu_box_x + self.menu_box_width - (box_w * 2 + box_gap_x) - shift_left
        start_y = self.menu_box_y + self.menu_box_height - (box_h * 4 + box_gap_y * 3) - shift_up
        # Draw first 6 labels (2 columns x 3 rows)
        for i in range(6):
            col = i % 2
            row = i // 2
            x = start_x + col * (box_w + box_gap_x)
            y = start_y + row * (box_h + box_gap_y)
            try:
                font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
                label_font = pygame.font.Font(font_path, int(1.2 * max(18, int(box_h * 0.55))))
            except Exception:
                label_font = pygame.font.SysFont(None, int(1.2 * max(18, int(box_h * 0.55))), bold=True)
            selected = (row == self.selected_menu_row and col == self.selected_menu_col and not self.in_regen_menu)
            if selected:
                color = (255,255,255) if self.menu_blink_on else (0,0,0)
            else:
                color = (255,255,255)
            label_surface = label_font.render(option_names[i], True, color)
            label_x = x + (box_w - label_surface.get_width()) // 2
            label_y = y + (box_h - label_surface.get_height()) // 2
            screen.blit(label_surface, (label_x, label_y))
        # Draw OPTIONS label (full width below)
        options_x = start_x
        options_y = start_y + 3 * (box_h + box_gap_y)
        options_w = box_w * 2 + box_gap_x
        try:
            font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
            options_font = pygame.font.Font(font_path, int(1.2 * max(22, int(box_h * 0.6))))
        except Exception:
            options_font = pygame.font.SysFont(None, int(1.2 * max(22, int(box_h * 0.6))), bold=True)
        selected = (self.selected_menu_row == 3 and not self.in_regen_menu)
        if selected:
            color = (255,255,255) if self.menu_blink_on else (0,0,0)
        else:
            color = (255,255,255)
        options_surface = options_font.render(option_names[6], True, color)
        options_label_x = options_x + (options_w - options_surface.get_width()) // 2
        options_label_y = options_y + (box_h - options_surface.get_height()) // 2
        screen.blit(options_surface, (options_label_x, options_label_y))
        
        # Draw system menu overlay if active
        if self.in_system_menu:
            self.draw_system_menu(screen)
    
    def draw_system_menu(self, screen):
        """Draw the system menu overlay with red rounded edges"""
        # System menu dimensions
        menu_width = int(self.screen_width * 0.4)
        menu_height = int(self.screen_height * 0.6)
        menu_x = (self.screen_width - menu_width) // 2
        menu_y = (self.screen_height - menu_height) // 2
        
        # Create system menu surface without alpha (opaque)
        system_surface = pygame.Surface((menu_width, menu_height))
        
        # Draw rounded rectangle background (dark with red edges)
        corner_radius = 20
        # Fill entire surface with background color first
        system_surface.fill((40, 40, 50))
        
        # Draw rounded rectangle background
        pygame.draw.rect(system_surface, (40, 40, 50), 
                        (0, 0, menu_width, menu_height), 0, corner_radius)
        
        # Red border effect - draw multiple rounded rectangles for glow
        border_colors = [(150, 50, 50), (200, 80, 80), (255, 120, 120)]
        for i, border_color in enumerate(border_colors):
            border_thickness = 3 + i
            pygame.draw.rect(system_surface, border_color,
                           (0, 0, menu_width, menu_height), border_thickness, corner_radius)
        
        # Title
        try:
            font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
            title_font = pygame.font.Font(font_path, int(menu_height * 0.08))
            option_font = pygame.font.Font(font_path, int(menu_height * 0.05))
        except Exception:
            title_font = pygame.font.SysFont(None, int(menu_height * 0.08), bold=True)
            option_font = pygame.font.SysFont(None, int(menu_height * 0.05), bold=True)
        
        title_surface = title_font.render("SYSTEM", True, (255, 255, 255))
        title_x = (menu_width - title_surface.get_width()) // 2
        title_y = int(menu_height * 0.1)
        system_surface.blit(title_surface, (title_x, title_y))
        
        # Options
        option_start_y = int(menu_height * 0.25)
        option_height = int(menu_height * 0.08)
        
        for i, option_text in enumerate(self.system_options):
            # Highlight selected option
            if i == self.system_selected_option:
                # Blinking effect for selected option
                if self.menu_blink_on:
                    color = (255, 255, 100)  # Yellow when blinking
                    # Draw selection background without alpha
                    selection_rect = pygame.Rect(int(menu_width * 0.1), 
                                                option_start_y + i * option_height - 5,
                                                int(menu_width * 0.8), option_height - 10)
                    pygame.draw.rect(system_surface, (80, 80, 30), selection_rect, 0, 10)
                else:
                    color = (200, 200, 200)
            else:
                color = (255, 255, 255)
            
            option_surface = option_font.render(option_text, True, color)
            option_x = int(menu_width * 0.15)
            option_y = option_start_y + i * option_height
            system_surface.blit(option_surface, (option_x, option_y))
        
        # Instructions
        try:
            inst_font = pygame.font.Font(font_path, int(menu_height * 0.03))
        except Exception:
            inst_font = pygame.font.SysFont(None, int(menu_height * 0.03))
        
        instructions = [
            "Arrow Keys: Navigate",
            "Left/Right: Adjust Values", 
            "Space: Select",
            "ESC: Back"
        ]
        
        inst_start_y = int(menu_height * 0.8)
        for i, instruction in enumerate(instructions):
            inst_surface = inst_font.render(instruction, True, (180, 180, 180))
            inst_x = int(menu_width * 0.15)
            inst_y = inst_start_y + i * int(menu_height * 0.04)
            system_surface.blit(inst_surface, (inst_x, inst_y))
        
        # Blit system menu to main screen
        screen.blit(system_surface, (menu_x, menu_y))

    def update_dimensions(self, width, height):
        self.screen_width = width
        self.screen_height = height
        self._set_menu_box()
        try:
            font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
            font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
            self.font_big = pygame.font.Font(font_path, font_big_size)
        except Exception as e:
            print(f"[PauseMenu] Could not load Pixellari.ttf for resize: {e}")
            font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
            self.font_big = pygame.font.SysFont(None, font_big_size, bold=True)
        self._update_gif_scale()
        self.update_frame_png()

# --- Menu system entry point ---
def show_pause_menu(screen, pause_menu, dt):
    pause_menu.update(dt)
    pause_menu.draw(screen)
    font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
    font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
    self.font_big = pygame.font.Font(font_path, font_big_size)
    self._update_gif_scale()
    self.update_frame_png()

# --- Menu system entry point ---
def show_pause_menu(screen, pause_menu, dt):
    pause_menu.update(dt)
    pause_menu.draw(screen)
