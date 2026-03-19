"""
Skills Menu System for Afterdeath RPG
DIRECTLY BASED ON the equipment menu structure and rendering to ensure exact layout matching.
Handles Normal Skills and Memory Skills with tab navigation.
"""

import pygame
import os
import sys
from pathlib import Path
# Import skills from centralized config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from Skills_Config import  PROFICIENCY_SKILLS, MEMORY_SKILLS, get_inborn_skills_for_species

# Screen constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)

class Skill:
    """Base class for skills"""
    def __init__(self, name, description, long_description, skill_type="normal", icon_path=None):
        self.name = name
        self.description = description
        self.long_description = long_description
        self.skill_type = skill_type
        self.icon_path = icon_path
        self.icon = None
        self.load_icon()
    
    def load_icon(self):
        """Load skill icon if available"""
        if self.icon_path and Path(self.icon_path).exists():
            try:
                self.icon = pygame.image.load(self.icon_path)
                self.icon = pygame.transform.scale(self.icon, (32, 32))
            except:
                self.icon = None

class NormalSkill(Skill):
    """Normal skill (inborn abilities and proficiencies)"""
    def __init__(self, name, description, long_description, proficiency_level=0, icon_path=None):
        super().__init__(name, description, long_description, "normal", icon_path)
        self.proficiency_level = proficiency_level
        self.is_inborn = proficiency_level == 0

class MemorySkill(Skill):
    """Memory skill (equippable with memory cost)"""
    def __init__(self, name, description, long_description, memory_cost, icon_path=None):
        super().__init__(name, description, long_description, "memory", icon_path)
        self.memory_cost = memory_cost
        self.is_equipped = False

class SkillsMenu:
    """Skills menu - EXACT match to equipment menu structure"""
    def __init__(self, screen_width, screen_height, menu_box_width, menu_box_height, player_stats):
        """Initialize menu with same parameters as equipment menu"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.menu_box_width = menu_box_width
        self.menu_box_height = menu_box_height
        self.player_stats = player_stats
        self.screen = pygame.display.get_surface()
        
        # Menu state
        self.running = True
        self.selected_tab = 0  # 0=Normal Skills, 1=Memory Skills
        self.selected_index = 0
        self.current_items = []
        
        # Load resources in exact same way as equipment menu
        self.load_fonts()
        self.load_background()
        self.load_skills()
        
        # Memory system
        self.max_memory_points = self.calculate_max_memory_points()
        self.used_memory_points = 0
        self.calculate_used_memory()
        
        # Set initial tab
        self.update_current_items()
        
        # Controller support
        self.joystick = None
        self.init_joystick()
    
    def init_joystick(self):
        """Initialize game controller if available"""
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
    
    def calculate_max_memory_points(self):
        """Calculate max memory points based on player level"""
        player_level = getattr(self.player_stats, 'level', 1)
        return 3 + (player_level - 1) * 2
    
    def calculate_used_memory(self):
        """Calculate currently used memory points"""
        self.used_memory_points = sum(skill.memory_cost for skill in self.memory_skills if skill.is_equipped)
    
    def load_fonts(self):
        """Load fonts using the same approach as equipment menu"""
        try:
            font_path = Path("../../../Fonts/Pixellari.ttf")
            if font_path.exists():
                self.font_large = pygame.font.Font(str(font_path), 24)
                self.font_medium = pygame.font.Font(str(font_path), 20)
                self.font_small = pygame.font.Font(str(font_path), 16)
                self.font_tiny = pygame.font.Font(str(font_path), 14)
            else:
                # Fallback to default font
                self.font_large = pygame.font.Font(None, 24)
                self.font_medium = pygame.font.Font(None, 20)
                self.font_small = pygame.font.Font(None, 16)
                self.font_tiny = pygame.font.Font(None, 14)
        except Exception as e:
            print(f"[Skills Menu] Error loading fonts: {e}")
            self.font_large = pygame.font.Font(None, 24)
            self.font_medium = pygame.font.Font(None, 20)
            self.font_small = pygame.font.Font(None, 16)
            self.font_tiny = pygame.font.Font(None, 14)
    
    def load_background(self):
        """Load menu background with same approach as equipment menu"""
        try:
            bg_path = Path("../../Menus/Pause_Menu_Skills_V01.png")
            if bg_path.exists():
                self.background = pygame.image.load(str(bg_path))
                self.background = pygame.transform.scale(self.background, (self.menu_box_width, self.menu_box_height))
                print(f"[Skills Menu] Loaded background: {bg_path}")
            else:
                print(f"[Skills Menu] Background not found: {bg_path}")
                self.background = None
        except Exception as e:
            print(f"[Skills Menu] Error loading background: {e}")
            self.background = None
    
    def load_skills(self):
        """Load normal and memory skills data"""
        # Load normal skills (inborn abilities & proficiencies)
        self.normal_skills = self.load_normal_skills()
        
        # Load memory skills (equippable abilities with memory cost)
        self.memory_skills = self.load_memory_skills()
    
    def load_normal_skills(self):
        """Load normal skills using centralized species association"""
        skills = []
        character_species = getattr(self.player_stats, 'species', 'Sapifer')

        # NEW: resolve species inborn skills via helper
        inborn = get_inborn_skills_for_species(character_species)
        for skill_id, skill_data in inborn.items():
            skills.append(NormalSkill(
                name=skill_data["name"],
                description=skill_data["short_description"],
                long_description=skill_data["long_description"],
                proficiency_level=0,
                icon_path=None
            ))

        # Proficiency skills unchanged
        for skill_id, skill_data in PROFICIENCY_SKILLS.items():
            skills.append(NormalSkill(
                name=skill_data["name"],
                description=skill_data["short_description"],
                long_description=skill_data["long_description"],
                proficiency_level=skill_data.get("level", 1),
                icon_path=None
            ))
        return skills
    
    def load_memory_skills(self):
        """Load memory skills from Skills_Config and set equipped state from player object"""
        skills = []
        
        # Get player's currently equipped memory skills
        player_equipped_skills = []
        if hasattr(self.player_stats, 'equipped_memory_skills'):
            player_equipped_skills = self.player_stats.equipped_memory_skills
            print(f"[Skills Menu] Loading player equipped skills: {player_equipped_skills}")
        
        # Load all memory skills from config
        for skill_id, skill_data in MEMORY_SKILLS.items():
            skill = MemorySkill(
                name=skill_data["name"],
                description=skill_data["short_description"],
                long_description=skill_data["long_description"],
                memory_cost=skill_data["memory_cost"],
                icon_path=None
            )
            
            # Set equipped state based on player's equipped skills
            # Convert skill name to ID for matching
            skill_name_id = skill.name.lower().replace(' ', '_').replace("'", "")
            if skill_id in player_equipped_skills or skill_name_id in player_equipped_skills:
                skill.is_equipped = True
                print(f"[Skills Menu] Skill '{skill.name}' is equipped")
            
            skills.append(skill)
        
        return skills
    
    def update_current_items(self):
        """Update current items based on selected tab"""
        if self.selected_tab == 0:
            self.current_items = self.normal_skills
        else:
            self.current_items = self.memory_skills
        
        # Ensure selected index is valid
        if self.selected_index >= len(self.current_items):
            self.selected_index = 0 if self.current_items else -1
    
    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return True
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Exit menu
                    self.running = False
                    return False
                
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    # Switch to previous tab
                    prev_tab = self.selected_tab
                    self.selected_tab = (self.selected_tab - 1) % 2
                    if prev_tab != self.selected_tab:
                        self.update_current_items()
                
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    # Switch to next tab
                    prev_tab = self.selected_tab
                    self.selected_tab = (self.selected_tab + 1) % 2
                    if prev_tab != self.selected_tab:
                        self.update_current_items()
                
                elif event.key in (pygame.K_UP, pygame.K_w):
                    # Navigate up in list
                    if self.current_items:
                        self.selected_index = (self.selected_index - 1) % len(self.current_items)
                
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    # Navigate down in list
                    if self.current_items:
                        self.selected_index = (self.selected_index + 1) % len(self.current_items)
                
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # Toggle memory skill equip state
                    if self.selected_tab == 1 and self.selected_index >= 0 and self.selected_index < len(self.current_items):
                        self.toggle_memory_skill()
            
            # Handle joystick/controller input
            elif self.joystick:
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0:  # A button
                        # Toggle memory skill equip state
                        if self.selected_tab == 1 and self.selected_index >= 0 and self.selected_index < len(self.current_items):
                            self.toggle_memory_skill()
                    elif event.button == 1:  # B button
                        # Exit menu
                        self.running = False
                        return False
                
                elif event.type == pygame.JOYHATMOTION and event.hat == 0:
                    # D-pad navigation
                    if event.value[1] == 1:  # Up
                        if self.current_items:
                            self.selected_index = (self.selected_index - 1) % len(self.current_items)
                    elif event.value[1] == -1:  # Down
                        if self.current_items:
                            self.selected_index = (self.selected_index + 1) % len(self.current_items)
                    elif event.value[0] == -1:  # Left
                        prev_tab = self.selected_tab
                        self.selected_tab = (self.selected_tab - 1) % 2
                        if prev_tab != self.selected_tab:
                            self.update_current_items()
                    elif event.value[0] == 1:  # Right
                        prev_tab = self.selected_tab
                        self.selected_tab = (self.selected_tab + 1) % 2
                        if prev_tab != self.selected_tab:
                            self.update_current_items()
        
        return False
    
    def toggle_memory_skill(self):
        """Toggle equip state of selected memory skill"""
        if self.selected_index < 0 or self.selected_index >= len(self.current_items):
            return
        
        skill = self.current_items[self.selected_index]
        
        if skill.is_equipped:
            # Unequip skill
            skill.is_equipped = False
            print(f"[Skills Menu] Unequipped: {skill.name}")
        else:
            # Check if enough memory points to equip
            if self.used_memory_points + skill.memory_cost <= self.max_memory_points:
                skill.is_equipped = True
                print(f"[Skills Menu] Equipped: {skill.name}")
            else:
                print(f"[Skills Menu] Not enough memory points to equip {skill.name}")
        
        # Recalculate used memory points
        self.calculate_used_memory()
        
        # Update global player object with equipped skills
        self.update_global_player_memory_skills()

    def update_global_player_memory_skills(self):
        """Update the global player object with currently equipped memory skills"""
        try:
            # Find the global player_stats object
            import sys
            player_stats = None
            
            # Look for player_stats in the overworld module
            for module_name in sys.modules:
                if 'Overworld_Main' in module_name:
                    overworld_module = sys.modules[module_name]
                    if hasattr(overworld_module, 'player_stats'):
                        player_stats = overworld_module.player_stats
                        break
            
            if player_stats and hasattr(player_stats, 'equipped_memory_skills'):
                # Get list of currently equipped skill IDs
                equipped_skills = []
                for skill in self.memory_skills:
                    if skill.is_equipped:
                        # Convert skill name to skill ID (assuming they match)
                        skill_id = skill.name.lower().replace(' ', '_').replace("'", "")
                        equipped_skills.append(skill_id)
                
                # Update player's equipped memory skills
                player_stats.equipped_memory_skills = equipped_skills
                print(f"[Skills Menu] Updated global player equipped skills: {equipped_skills}")
                
                # Also update memory skill states if they exist
                if hasattr(player_stats, 'memory_skill_state'):
                    # Ensure all equipped skills have state entries
                    for skill_id in equipped_skills:
                        if skill_id not in player_stats.memory_skill_state:
                            player_stats.memory_skill_state[skill_id] = {
                                "activations": 0,
                                "applied_bonus": 0
                            }
            else:
                print(f"[Skills Menu] Could not find global player_stats to update memory skills")
                
        except Exception as e:
            print(f"[Skills Menu] Error updating global player memory skills: {e}")
            import traceback
            traceback.print_exc()
    
    def draw(self, screen):
        """Draw the skills menu - IDENTICAL structure to equipment menu"""
        # Create a transparent surface for the menu
        menu_surface = pygame.Surface((self.menu_box_width, self.menu_box_height), pygame.SRCALPHA)
        menu_surface.fill((0, 0, 0, 0))  # Fully transparent
        
        # Draw background image if available
        if self.background:
            menu_surface.blit(self.background, (0, 0))
        
        # Draw tabs
        self.draw_tabs(menu_surface)
        
        # Draw skill list
        self.draw_skill_list(menu_surface)
        
        # Draw selected skill details
        self.draw_skill_details(menu_surface)
        
        # Draw memory points info if on memory skills tab
        if self.selected_tab == 1:
            self.draw_memory_points(menu_surface)
        
        # Draw controls help
        self.draw_controls(menu_surface)
        
        # Position menu in the center of the screen
        menu_x = (self.screen_width - self.menu_box_width) // 2
        menu_y = (self.screen_height - self.menu_box_height) // 2
        screen.blit(menu_surface, (menu_x, menu_y))
    
    def draw_tabs(self, surface):
        """Draw section tabs at the far left, all caps - EXACT COPY from Equipment menu with better spacing"""
        tab_font_size = max(18, int(self.menu_box_height * 0.055))
        try:
            tab_font = pygame.font.Font("../../../Fonts/Pixellari.ttf", tab_font_size)
        except Exception:
            tab_font = pygame.font.SysFont(None, tab_font_size, bold=True)
        
        # INCREASED spacing between tabs to prevent overlap
        tab_spacing = int(self.menu_box_width * 0.25)  # Increased from 0.16 to 0.25
        tab_y = int(self.menu_box_height * 0.057)
        tab_x_start = int(self.menu_box_width * 0.045)  # Far left
        
        tabs = ["NORMAL SKILLS", "MEMORY SKILLS"]
        
        for idx, name in enumerate(tabs):
            color = (80, 205, 80) if idx == self.selected_tab else (255, 255, 255)
            tab_surf = tab_font.render(name, True, color)
            tab_x = tab_x_start + idx * tab_spacing
            surface.blit(tab_surf, (tab_x, tab_y))

    def draw_skill_list(self, surface):
        """Draw equipment list - EXACT COPY from Equipment menu with skill data"""
        current_list = self.current_items
        num_rows = len(current_list)
        
        if num_rows == 0:
            return
        
        # EXACT dimensions from Equipment menu
        icon_box_size = int(self.menu_box_height * 0.165)
        col_x = int(self.menu_box_width * 0.040)
        start_y = int(self.menu_box_height * 0.16)
        row_height = int(self.menu_box_height * 0.175)
        
        # EXACT fonts from Equipment menu
        name_font_size = max(18, int(self.menu_box_height * 0.045))
        desc_font_size = max(14, int(self.menu_box_height * 0.032))
        try:
            name_font = pygame.font.Font("../../../Fonts/Pixellari.ttf", name_font_size)
            short_font = pygame.font.Font("../../../Fonts/Pixellari.ttf", desc_font_size)
        except Exception:
            name_font = pygame.font.SysFont(None, name_font_size, bold=True)
            short_font = pygame.font.SysFont(None, desc_font_size, bold=True)

        # EXACT scrolling logic from Equipment menu
        max_visible_rows = 4
        scroll_offset = 0
        if self.selected_index >= max_visible_rows:
            scroll_offset = self.selected_index - max_visible_rows + 1
        elif self.selected_index < 0:
            scroll_offset = 0

        visible_indices = range(scroll_offset, min(scroll_offset + max_visible_rows, num_rows))
        
        for draw_idx, i in enumerate(visible_indices):
            skill = current_list[i]
            y = start_y + draw_idx * row_height
            
            # EXACT selection highlight from Equipment menu
            if i == self.selected_index:
                bg_rect = pygame.Rect(col_x-10, y-4, int(self.menu_box_width*0.38), row_height)
                pygame.draw.rect(surface, (255,255,255), bg_rect, border_radius=8)
            
            # EXACT icon box from Equipment menu
            icon_rect = pygame.Rect(col_x, y, icon_box_size, icon_box_size)
            pygame.draw.rect(surface, (60,60,60), icon_rect, border_radius=6)
            
            # Draw equipped border for memory skills - EXACT copy from Equipment menu
            if isinstance(skill, MemorySkill) and skill.is_equipped:
                equipped_color = (255, 215, 0)  # Golden yellow
                pygame.draw.rect(surface, equipped_color, icon_rect, width=3, border_radius=6)
            
            # EXACT icon handling from Equipment menu
            if skill.icon:
                icon_img = pygame.transform.smoothscale(skill.icon, (icon_box_size-6, icon_box_size-6))
                surface.blit(icon_img, (col_x+3, y+3))
            else:
                no_icon_font = pygame.font.SysFont(None, max(12, icon_box_size//4), bold=True)
                no_icon_surf = no_icon_font.render("NO ICON", True, (200,200,200))
                nx = col_x + (icon_box_size - no_icon_surf.get_width())//2
                ny = y + (icon_box_size - no_icon_surf.get_height())//2
                surface.blit(no_icon_surf, (nx, ny))
            
            # EXACT text positioning from Equipment menu
            name_color = (0,0,0) if i == self.selected_index else (255,255,255)
            name_surf = name_font.render(skill.name, True, name_color)
            surface.blit(name_surf, (col_x + icon_box_size + 12, y))
            
            # EXACT short description positioning from Equipment menu
            short_color = (40,40,40) if i == self.selected_index else (200,200,200)
            short_surf = short_font.render(skill.description, True, short_color)
            surface.blit(short_surf, (col_x + icon_box_size + 12, y + name_surf.get_height() + 2))
            
            # Skill type info (replacing weapon class) - EXACT positioning from Equipment menu
            type_color = (60,60,60) if i == self.selected_index else (150,150,200)
            if isinstance(skill, NormalSkill):
                if skill.is_inborn:
                    type_text = "(Inborn)"
                else:
                    type_text = f"Level: {skill.proficiency_level}"
            elif isinstance(skill, MemorySkill):
                if skill.is_equipped:
                    type_text = f"Cost: {skill.memory_cost} [EQUIPPED]"
                else:
                    type_text = f"Cost: {skill.memory_cost}"
            else:
                type_text = ""
                
            if type_text:
                type_surf = short_font.render(type_text, True, type_color)
                surface.blit(type_surf, (col_x + icon_box_size + 12, y + name_surf.get_height() + short_surf.get_height() + 4))

    def draw_skill_details(self, surface):
        """Draw skill long description in the image area - MODIFIED for skills"""
        current_list = self.current_items
        num_rows = len(current_list)
        
        if num_rows == 0:
            return
            
        skill = current_list[self.selected_index]
        
        # EXACT image box dimensions from Equipment menu - but use for description
        img_box_x = int(self.menu_box_width * 0.60)   # X position (fraction of menu width)
        img_box_y = int(self.menu_box_height * 0.175)  # Y position (fraction of menu height)
        img_box_w = int(self.menu_box_width * 0.38)   # Width (fraction of menu width)
        img_box_h = int(self.menu_box_height * 0.78)  # Height (fraction of menu height)
        
        # EXACT name display from Equipment menu
        name_font_size = max(16, int(self.menu_box_height * 0.04))
        try:
            name_display_font = pygame.font.Font("../../../Fonts/Pixellari.ttf", name_font_size)
        except Exception:
            name_display_font = pygame.font.SysFont(None, name_font_size, bold=True)
        
        name_text = skill.name
        name_surf = name_display_font.render(name_text, True, (255, 255, 255))
        name_x = img_box_x + (img_box_w - name_surf.get_width()) // 2
        name_y = int(self.menu_box_height * 0.049)  # EXACT position from Equipment menu
        surface.blit(name_surf, (name_x, name_y))
        
        # Draw long description in the main image area - EXACT positioning from Equipment menu description
        desc_x = img_box_x + 10  # Small margin from left edge
        desc_y = img_box_y + 20  # Start near top of text area
        desc_width = img_box_w - 20  # Leave margins on both sides
        desc_height = img_box_h - 40  # Leave space for margins
        
        # EXACT font from Equipment menu description
        desc_font_size = max(16, int(self.menu_box_height * 0.04))
        try:
            desc_font = pygame.font.Font("../../../Fonts/Pixellari.ttf", desc_font_size)
        except Exception:
            desc_font = pygame.font.SysFont(None, desc_font_size)
        
        # Font for skill type info (slightly smaller)
        type_font_size = max(14, int(self.menu_box_height * 0.035))
        try:
            type_font = pygame.font.Font("../../../Fonts/Pixellari.ttf", type_font_size)
        except Exception:
            type_font = pygame.font.SysFont(None, type_font_size, bold=True)
        
        # Draw skill type info as FIRST LINE inside text area
        current_y = desc_y
        if isinstance(skill, NormalSkill):
            if skill.is_inborn:
                type_text = "Inborn Ability"
                type_color = (255, 255, 0)  # Yellow
            else:
                type_text = "Proficiency"
                type_color = (0, 255, 0)    # Green
        elif isinstance(skill, MemorySkill):
            type_text = f"Memory Cost: {skill.memory_cost}"
            if skill.is_equipped:
                type_text += " [EQUIPPED]"
                type_color = (0, 255, 0)    # Green
            else:
                type_color = (255, 165, 0)  # Orange
        
        type_surf = type_font.render(type_text, True, type_color)
        surface.blit(type_surf, (desc_x, current_y))
        current_y += type_surf.get_height() + 15  # Add spacing after type info
        
        # EXACT word wrap logic from Equipment menu for the description
        description = skill.long_description
        wrapped_lines = []
        words = description.split(' ')
        current_line = ''
        
        for word in words:
            test_line = current_line + (' ' if current_line else '') + word
            test_surf = desc_font.render(test_line, True, (255, 255, 255))
            if test_surf.get_width() <= desc_width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word + " "
        if current_line:
            wrapped_lines.append(current_line)
        
        # Draw wrapped description lines
        line_height = desc_font.get_height() + 2
        available_height = desc_height - (current_y - desc_y) - 60  # Reserve space for memory points
        max_lines = int(available_height / line_height)
        
        for i, line in enumerate(wrapped_lines[:max_lines]):
            line_surf = desc_font.render(line, True, (255, 255, 255))
            surface.blit(line_surf, (desc_x, current_y + i * line_height))
    
    def draw_memory_points(self, surface):
        """Draw memory points - positioned in CENTER of right text area"""
        # Position in center of the right text area
        img_box_x = int(self.menu_box_width * 0.60)   # Same as text area
        img_box_w = int(self.menu_box_width * 0.38)   # Same as text area width
        img_box_y = int(self.menu_box_height * 0.175) # Same as text area
        img_box_h = int(self.menu_box_height * 0.78)  # Same as text area height
        
        # Position in vertical center of text area
        points_x = img_box_x + (img_box_w // 2)  # Horizontal center
        points_y = img_box_y + (img_box_h // 1.05)  # Vertical center
        
        # EXACT font from Equipment menu
        control_font_size = max(14, int(self.menu_box_height * 0.035))
        try:
            control_font = pygame.font.Font("../../../Fonts/Pixellari.ttf", control_font_size)
        except Exception:
            control_font = pygame.font.SysFont(None, control_font_size, bold=True)
        
        text = f"MEMORY POINTS: {self.used_memory_points}/{self.max_memory_points}"
        memory_surf = control_font.render(text, True, (255, 255, 255))
        
        # Center the text horizontally
        text_x = points_x - (memory_surf.get_width() // 2)
        surface.blit(memory_surf, (text_x, points_y))

    def draw_controls(self, surface):
        """Draw control instructions - EXACT COPY from Equipment menu"""
        control_font_size = max(14, int(self.menu_box_height * 0.035))
        try:
            control_font = pygame.font.Font("../../../Fonts/Pixellari.ttf", control_font_size)
        except Exception:
            control_font = pygame.font.SysFont(None, control_font_size, bold=True)
        
        if self.selected_tab == 1:  # Memory skills
            control_text = "SPACEBAR: EQUIP/UNEQUIP      SHIFT: INFO"
        else:
            control_text = "LEFT/RIGHT: SWITCH TABS      ESC: BACK"
            
        control_surf = control_font.render(control_text, True, (255, 255, 255))
        control_x = int(self.menu_box_width * 0.08)   # EXACT position from Equipment menu
        control_y = int(self.menu_box_height * 0.92)  # EXACT position from Equipment menu
        surface.blit(control_surf, (control_x, control_y))

    def draw_wrapped_text(self, surface, text, x, y, max_width, max_height, color=WHITE):
        """Draw text with word wrapping - EXACTLY like equipment menu"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            text_width = self.font_small.size(test_line)[0]
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        # Draw lines with proper spacing and height limit
        line_height = self.font_small.get_height() + 2
        current_y = y
        
        for line in lines:
            if current_y + line_height > y + max_height:
                # Add "..." if text is cut off
                ellipsis = self.font_small.render("...", True, color)
                surface.blit(ellipsis, (x, current_y))
                break
                
            line_surface = self.font_small.render(line, True, color)
            surface.blit(line_surface, (x, current_y))
            current_y += line_height

    def run(self):
        """Run the skills menu loop"""
        clock = pygame.time.Clock()
        
        while self.running:
            # Handle events - exit if requested
            if self.handle_events():
                return True
            
            # Draw the menu
            self.draw(self.screen)
            
            # Update display and cap frame rate
            pygame.display.flip()
            clock.tick(60)
        
        return False

def open_skills_menu(screen_width, screen_height, menu_box_width, menu_box_height, player_stats):
    """Entry point function that matches the calling convention of other menus"""
    try:
        pygame.init()
        menu = SkillsMenu(screen_width, screen_height, menu_box_width, menu_box_height, player_stats)
        return menu.run()
    except Exception as e:
        print(f"[Skills Menu] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test function when run directly
def main():
    """Test the skills menu"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skills Menu Test")
    
    # Create mock player stats
    class MockPlayer:
        def __init__(self):
            self.name = "Test Character"
            self.species = "Sapifer"
            self.level = 5
    
    player_stats = MockPlayer()
    
    # Menu dimensions
    menu_box_width = int(SCREEN_WIDTH * 0.85)
    menu_box_height = int(menu_box_width / 2.0545454)
    
    # Run the menu
    open_skills_menu(SCREEN_WIDTH, SCREEN_HEIGHT, menu_box_width, menu_box_height, player_stats)
    
    pygame.quit()

if __name__ == "__main__":
    main()
    # Create mock player stats
    class MockPlayer:
        def __init__(self):
            self.name = "Test Character"
            self.species = "Sapifer"
            self.level = 5
    
    player_stats = MockPlayer()
    
    # Menu dimensions
    menu_box_width = int(SCREEN_WIDTH * 0.85)
    menu_box_height = int(menu_box_width / 2.0545454)
    
    # Run the menu
    open_skills_menu(SCREEN_WIDTH, SCREEN_HEIGHT, menu_box_width, menu_box_height, player_stats)
    
    pygame.quit()

if __name__ == "__main__":
    main()
    
    pygame.quit()

if __name__ == "__main__":
    main()
