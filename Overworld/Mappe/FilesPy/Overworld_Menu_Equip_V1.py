# Overworld_Menu_Equip_V1.py
# EQUIP sub-menu for the overworld pause menu
import pygame
import os
import sys

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

def open_equipment_info(screen_width, screen_height, menu_box_width, menu_box_height, equipment, font_path, player_stats=None, player_equip_obj=None):
    """Display detailed equipment information modal"""
    # Load weapon info PNG for weapons, use default equip PNG for others
    if getattr(equipment, 'type', None) == 'weapon':
        info_png_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Menus\Pause_Menu_Equip_V02.png"
    else:
        info_png_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Menus\Pause_Menu_Equip_V01.png"
    
    try:
        info_png = pygame.image.load(info_png_path).convert_alpha()
    except Exception as e:
        print(f"[EquipInfo] Could not load info PNG: {e}")
        info_png = None
    
    # Load ESC sound for closing the modal using global SFX system
    esc_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\discard-sound-effect-221455.mp3", 1.0)
    
    # Calculate menu box position
    menu_box_x = (screen_width - menu_box_width) // 2
    menu_box_y = (screen_height - menu_box_height) // 2
    
    # Get main display surface
    screen = pygame.display.get_surface()
    
    running = True
    clock = pygame.time.Clock()
    
    # Status effect GIF system
    status_gifs = {}  # Cache for loaded GIFs: {effect_name: {'frames': [...], 'durations': [...], 'current_frame': 0, 'timer': 0}}
    status_gifs_folder = r"C:\Users\franc\Desktop\Afterdeath_RPG\Statuses_Gifs"
    
    def load_status_gif(effect_name):
        """Load a status effect GIF by name using the format: EffectName_gif.gif"""
        if effect_name in status_gifs:
            return status_gifs[effect_name]
        
        # Format: EffectName_gif.gif (capitalize first letter)
        gif_filename = f"{effect_name.capitalize()}_gif.gif"
        gif_path = os.path.join(status_gifs_folder, gif_filename)
        
        try:
            from PIL import Image
            pil_img = Image.open(gif_path)
            
            # Load all frames
            frames = []
            durations = []
            for frame_idx in range(getattr(pil_img, 'n_frames', 1)):
                pil_img.seek(frame_idx)
                frame_img = pil_img.convert('RGBA')
                mode = frame_img.mode
                size = frame_img.size
                data = frame_img.tobytes()
                surf = pygame.image.fromstring(data, size, mode)
                frames.append(surf)
                duration = pil_img.info.get('duration', 100)  # Default 100ms
                durations.append(duration)
            
            gif_data = {
                'frames': frames,
                'durations': durations,
                'current_frame': 0,
                'timer': 0
            }
            status_gifs[effect_name] = gif_data
            print(f"[EquipInfo] Loaded status GIF: {gif_filename} ({len(frames)} frames)")
            return gif_data
            
        except ImportError:
            print(f"[EquipInfo] Pillow not available for GIF loading: {gif_filename}")
        except Exception as e:
            print(f"[EquipInfo] Could not load status GIF: {gif_filename} - {e}")
        
        return None
    
    def update_status_gifs(dt):
        """Update animation timers for all loaded status GIFs"""
        for effect_name, gif_data in status_gifs.items():
            if gif_data and len(gif_data['frames']) > 1:
                gif_data['timer'] += dt
                current_duration = gif_data['durations'][gif_data['current_frame']]
                if gif_data['timer'] >= current_duration:
                    gif_data['timer'] = 0
                    gif_data['current_frame'] = (gif_data['current_frame'] + 1) % len(gif_data['frames'])
    
    def get_current_status_frame(effect_name):
        """Get the current frame surface for a status effect"""
        if effect_name in status_gifs and status_gifs[effect_name]:
            gif_data = status_gifs[effect_name]
            return gif_data['frames'][gif_data['current_frame']]
        return None
    
    # Setup fonts
    title_font_size = max(20, int(menu_box_height * 0.055))
    desc_font_size = max(16, int(menu_box_height * 0.04))
    try:
        title_font = pygame.font.Font(font_path, title_font_size)
        desc_font = pygame.font.Font(font_path, desc_font_size)
    except Exception:
        title_font = pygame.font.SysFont(None, title_font_size, bold=True)
        desc_font = pygame.font.SysFont(None, desc_font_size)
    
    while running:
        dt = clock.tick(60)  # Get delta time for GIF animation
        update_status_gifs(dt)  # Update GIF animations
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_z or event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if esc_sound:
                        esc_sound.play()
                    running = False
            # Handle controller events
            elif event.type == pygame.JOYBUTTONDOWN:
                # Circle button (cancel/ESC equivalent) or Square button (shift equivalent)
                if is_controller_button_just_pressed(event, 'circle') or is_controller_button_just_pressed(event, 'square'):
                    if esc_sound:
                        esc_sound.play()
                    running = False
        
        # Draw transparent overlay
        overlay = pygame.Surface((menu_box_width, menu_box_height), pygame.SRCALPHA)
        overlay.fill((30, 30, 40, 180))  # Semi-transparent base
        
        # Draw weapon proficiency bar for weapons (UNDER the PNG)
        if (getattr(equipment, 'type', None) == 'weapon' and 
            hasattr(equipment, 'weapon_class') and equipment.weapon_class and 
            player_equip_obj and hasattr(player_equip_obj, 'weapon_proficiency')):
            
            weapon_class = equipment.weapon_class
            proficiency_system = player_equip_obj.weapon_proficiency
            
            # Get progress ratio using the new method
            progress_ratio = proficiency_system.get_proficiency_progress(weapon_class)
            
            # Position the proficiency bar (adjust these coordinates based on your PNG layout)
            # This should be positioned where the "PROFICIENCY" bar hole is in your PNG
            bar_x = int(menu_box_width * 0.148)  # Moved a bit right (was 0.072)
            bar_y = int(menu_box_height * 0.475)  # Moved a little up (was 0.515)
            bar_width = int(menu_box_width * 0.405)  # Wide enough to fill the proficiency area
            bar_height = int(menu_box_height * 0.075)  # Appropriate height for the bar
            
            # Draw proficiency bar background (dark)
            pygame.draw.rect(overlay, (20, 20, 20), (bar_x, bar_y, bar_width, bar_height))
            
            # Draw proficiency bar progress (blue)
            progress_width = int(bar_width * progress_ratio)
            if progress_width > 0:
                pygame.draw.rect(overlay, (30, 100, 200), (bar_x, bar_y, progress_width, bar_height))
            
            # Draw border around bar
            pygame.draw.rect(overlay, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 2)

        # Draw PNG background
        if info_png:
            info_w = info_png.get_width()
            info_h = info_png.get_height()
            scale_w = menu_box_width
            scale_h = menu_box_height
            aspect = info_w / info_h if info_h > 0 else 1
            if scale_w / aspect < scale_h:
                scale_h = int(scale_w / aspect)
            else:
                scale_w = int(scale_h * aspect)
            info_surface = pygame.transform.smoothscale(info_png, (scale_w, scale_h))
            temp_surface = pygame.Surface((scale_w, scale_h), pygame.SRCALPHA)
            temp_surface.blit(info_surface, (0, 0))
            temp_surface.set_alpha(255)  # Make PNG semi-transparent (150 out of 255)
            x = (menu_box_width - scale_w) // 2
            y = (menu_box_height - scale_h) // 2
            overlay.blit(temp_surface, (x, y))
        
        # Draw equipment image in the right panel (same as main menu)
        img_box_x = int(menu_box_width * 0.60)
        img_box_y = int(menu_box_height * 0.175)
        img_box_w = int(menu_box_width * 0.38)
        img_box_h = int(menu_box_height * 0.78)
        
        # Draw equipment name text (without green box since it's in the PNG)
        name_font_size = max(16, int(menu_box_height * 0.04))
        try:
            name_display_font = pygame.font.Font(font_path, name_font_size)
        except Exception:
            name_display_font = pygame.font.SysFont(None, name_font_size, bold=True)
        
        name_text = equipment.name
        name_surf = name_display_font.render(name_text, True, (255, 255, 255))
        name_x = img_box_x + (img_box_w - name_surf.get_width()) // 2
        name_y = int(menu_box_height * 0.049)  # Raised position
        overlay.blit(name_surf, (name_x, name_y))
        
        # Draw move data for weapons using the PNG table grid
        if getattr(equipment, 'type', None) == 'weapon' and hasattr(equipment, 'moves') and equipment.moves:
            # Use real player stats for damage calculations if available, otherwise fallback to dummy
            if player_stats:
                # Map player stats to the format expected by Battle_Menu_Beta
                character_for_calcs = type('PlayerCharacter', (), {
                    'forz': player_stats.strength,  # strength -> forz (this is what Battle_Menu_Beta expects!)
                    'des': player_stats.dexterity,  # dexterity -> des (this is what Battle_Menu_Beta expects!)
                    'spe': player_stats.special,   # special -> spe (this is what Battle_Menu_Beta expects!)
                    'forza': player_stats.strength,  # also keep original names for compatibility
                    'destrezza': player_stats.dexterity,
                    'special': player_stats.special,
                    'strength': player_stats.strength,
                    'dexterity': player_stats.dexterity,
                    'speed': player_stats.speed
                })()
            else:
                # Fallback to dummy character if no player stats provided
                character_for_calcs = type('DummyCharacter', (), {
                    'forz': 10, 'des': 10, 'spe': 10,  # Use the correct attribute names!
                    'forza': 10, 'destrezza': 10, 'special': 10,
                    'strength': 10, 'dexterity': 10, 'speed': 10
                })()
            
            # Get move info with calculated damage and stamina costs
            try:
                # Get the current proficiency level for this weapon
                proficiency_level = 0  # Default to level 0
                if player_equip_obj and hasattr(equipment, 'weapon_class'):
                    proficiency_level = player_equip_obj.get_weapon_proficiency(equipment.weapon_class)
                
                move_info_list = equipment.get_move_info(character_for_calcs, proficiency_level)
            except Exception as e:
                print(f"[EquipInfo] Error getting move info: {e}")
                move_info_list = []
            
            # Setup fonts for table text (300% larger)
            table_font_size = max(27, int(menu_box_height * 0.066))  # 300% increase: 9*3=27, 0.022*3=0.066
            try:
                table_font = pygame.font.Font(font_path, table_font_size)
            except Exception:
                table_font = pygame.font.SysFont(None, table_font_size)
            
            # Setup smaller font for move names and accuracy (half size)
            small_font_size = max(13, int(menu_box_height * 0.044))  # Half of the 300% increase
            try:
                small_font = pygame.font.Font(font_path, small_font_size)
            except Exception:
                small_font = pygame.font.SysFont(None, small_font_size)
            
            # Table positioning (based on PNG grid)
            table_start_x = int(menu_box_width * 0.056)
            table_start_y = int(menu_box_height * 0.188)  # Start below the header row
            row_height = int(menu_box_height * 0.1)  # Height of each row
            
            # Column positions (adjust these to match your PNG grid)
            col_positions = [
                int(menu_box_width * 0.056),   # Move name column
                int(menu_box_width * 0.2615),   # STA column  
                int(menu_box_width * 0.286),   # STR column
                int(menu_box_width * 0.310),   # DEX column
                int(menu_box_width * 0.335),   # SPE column
                int(menu_box_width * 0.360),   # DMG column
                int(menu_box_width * 0.4062),   # ACC column
                int(menu_box_width * 0.4172),   # EFF1 column
                int(menu_box_width * 0.463)    # EFF2 column
            ]
            
            # Store level numbers to draw after all GIFs
            level_numbers_to_draw = []
            
            # Draw move data in the PNG table rows
            for row_idx, move_info in enumerate(move_info_list[:3]):  # Max 3 moves (rows I, II, III)
                row_y = table_start_y + (row_idx * row_height)
                
                # Prepare row data
                effects = move_info.get('effects', []) or []
                eff1 = effects[0] if len(effects) > 0 else ""
                eff2 = effects[1] if len(effects) > 1 else ""
                
                # Extract effect names and levels for GIF loading (effects format: [["EffectName", level, duration, target], ...])
                eff1_name = eff1[0] if eff1 and len(eff1) > 0 else ""
                eff1_level = eff1[1] if eff1 and len(eff1) > 1 else 1
                eff2_name = eff2[0] if eff2 and len(eff2) > 0 else ""
                eff2_level = eff2[1] if eff2 and len(eff2) > 1 else 1
                
                row_data = [
                    move_info.get('name', 'Unknown').upper(),  # Convert to uppercase
                    str(move_info.get('stamina_cost', 0)).upper(),
                    str(move_info.get('strength_scaling', 'N/A')).upper(),
                    str(move_info.get('dexterity_scaling', 'N/A')).upper(),
                    str(move_info.get('special_scaling', 'N/A')).upper(),
                    str(move_info.get('damage', 0)).upper(),
                    f"{move_info.get('accuracy', 100) / 100:.1f}".upper(),  # Convert to decimal with 1 decimal place (e.g., 0.9)
                    eff1_name,  # EFF1 - will be displayed as GIF
                    eff2_name   # EFF2 - will be displayed as GIF
                ]
                
                # Draw text in each column (excluding effect columns which will be GIFs)
                for col_idx, (text, x_pos) in enumerate(zip(row_data[:7], col_positions[:7])):  # Only first 7 columns (excluding EFF1/EFF2)
                    if text and str(text).strip():  # Only draw non-empty text
                        # Truncate text if too long and convert to uppercase
                        display_text = str(text).upper()
                        if col_idx == 0 and len(display_text) > 10:  # Move name
                            display_text = display_text[:8] + ".."
                        elif col_idx > 0 and len(display_text) > 6:  # Other columns
                            display_text = display_text[:4] + ".."
                        
                        # Use smaller font for move names (col 0) and accuracy (col 6)
                        if col_idx == 0:  # Move name
                            text_surf = small_font.render(display_text, True, (255, 255, 255))
                        else:  # Other columns use regular font
                            text_surf = table_font.render(display_text, True, (255, 255, 255))
                        
                        # Center text in column (adjust x_pos if needed for centering)
                        text_x = x_pos + 5  # Small offset from column start
                        text_y = row_y + (row_height - text_surf.get_height()) // 2
                        overlay.blit(text_surf, (text_x, text_y))
                
                # Draw effect GIFs in EFF1 and EFF2 columns
                # Calculate effect box size: GIFs went from 170x170 to 50x50, so scale proportionally
                original_gif_size = 170  # Original GIF size
                new_gif_size = 50        # New GIF size after manual downscaling
                size_ratio = new_gif_size / original_gif_size  # 50/170 ≈ 0.294
                
                # Scale the effect box size proportionally to the new GIF size
                base_effect_box_size = min(int(row_height * 4.0), int(menu_box_width * 0.125))
                effect_box_size = int(base_effect_box_size * size_ratio)  # Make it proportionally smaller
                
                # EFF1 column
                if eff1_name:
                    gif_data = load_status_gif(eff1_name)
                    eff1_x = col_positions[7]  # EFF1 column position
                    eff1_y = row_y + (row_height - effect_box_size) // 2
                    
                    if gif_data:
                        current_frame = get_current_status_frame(eff1_name)
                        if current_frame:
                            # Scale GIF to fit the box
                            scaled_frame = pygame.transform.smoothscale(current_frame, (effect_box_size, effect_box_size))
                            overlay.blit(scaled_frame, (eff1_x, eff1_y))
                            
                            # Store level number info for drawing on top layer later
                            level_numbers_to_draw.append({
                                'level': eff1_level,
                                'gif_x': eff1_x,
                                'gif_y': eff1_y,
                                'gif_size': effect_box_size,
                                'column': 'EFF1',
                                'row': row_idx
                            })
                    else:
                        # Fallback: draw effect name as text if GIF not available
                        fallback_text = eff1_name[:3].upper()  # First 3 letters
                        fallback_surf = small_font.render(fallback_text, True, (255, 255, 0))
                        overlay.blit(fallback_surf, (eff1_x + 2, eff1_y + (effect_box_size - fallback_surf.get_height()) // 2))
                
                # EFF2 column
                if eff2_name:
                    gif_data = load_status_gif(eff2_name)
                    eff2_x = col_positions[8]  # EFF2 column position
                    eff2_y = row_y + (row_height - effect_box_size) // 2
                    
                    if gif_data:
                        current_frame = get_current_status_frame(eff2_name)
                        if current_frame:
                            # Scale GIF to fit the box
                            scaled_frame = pygame.transform.smoothscale(current_frame, (effect_box_size, effect_box_size))
                            overlay.blit(scaled_frame, (eff2_x, eff2_y))
                            
                            # Store level number info for drawing on top layer later
                            level_numbers_to_draw.append({
                                'level': eff2_level,
                                'gif_x': eff2_x,
                                'gif_y': eff2_y,
                                'gif_size': effect_box_size,
                                'column': 'EFF2',
                                'row': row_idx
                            })
                    else:
                        # Fallback: draw effect name as text if GIF not available
                        fallback_text = eff2_name[:3].upper()  # First 3 letters
                        fallback_surf = small_font.render(fallback_text, True, (255, 255, 0))
                        overlay.blit(fallback_surf, (eff2_x + 2, eff2_y + (effect_box_size - fallback_surf.get_height()) // 2))
            
            # Draw all level numbers on top of GIFs (final layer for visibility)
            for level_info in level_numbers_to_draw:
                level_font_size = max(8, int(level_info['gif_size'] * 0.15))  # Much smaller font (15% of GIF size)
                try:
                    level_font = pygame.font.Font(font_path, level_font_size)
                except Exception:
                    level_font = pygame.font.SysFont(None, level_font_size, bold=True)
                
                level_text = str(level_info['level'])
                level_surf = level_font.render(level_text, True, (255, 255, 255))
                
                # Position in bottom right corner, inside the GIF bounds
                # Manual offset adjustment: shift left and up to align with GIFs properly
                level_x = level_info['gif_x'] + level_info['gif_size'] - level_surf.get_width() - menu_box_width * 0.045
                level_y = level_info['gif_y'] + level_info['gif_size'] - level_surf.get_height() - menu_box_width * 0.045

                # Draw black outline for visibility
                level_outline = level_font.render(level_text, True, (0, 0, 0))
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx != 0 or dy != 0:
                            overlay.blit(level_outline, (level_x + dx, level_y + dy))
                # Draw main text on top
                overlay.blit(level_surf, (level_x, level_y))
            
            # Draw description below the table
            desc_x = int(menu_box_width * 0.056)
            desc_y = int(menu_box_height * 0.64)
            desc_width = int(menu_box_width * 0.47)
            desc_height = int(menu_box_height * 0.31)
        else:
            # Draw long description in bottom left area for non-weapons
            desc_x = int(menu_box_width * 0.056)
            desc_y = int(menu_box_height * 0.64)
            desc_width = int(menu_box_width * 0.48)
            desc_height = int(menu_box_height * 0.17)
        
        # Word wrap the description
        description = getattr(equipment, 'description', 'No detailed description available.')
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
                current_line = word
        if current_line:
            wrapped_lines.append(current_line)
        
        # Draw wrapped description lines
        line_height = desc_font.get_height() + 2
        max_lines = int(desc_height / line_height)  # Limit lines to fit in available space
        for i, line in enumerate(wrapped_lines[:max_lines]):  # Only show lines that fit
            line_surf = desc_font.render(line, True, (255, 255, 255))
            overlay.blit(line_surf, (desc_x, desc_y + i * line_height))
        
        # Draw equipment image below the name box
        if equipment.image:
            iw, ih = equipment.image.get_width(), equipment.image.get_height()
            # Scale image to fit inside the box, preserving aspect ratio with safety margin
            safety_margin = 0.9  # Use 90% of available space to prevent border overlap
            scale = min((img_box_w * safety_margin)/iw, (img_box_h * safety_margin)/ih, 1.0)
            new_w = int(iw*scale)
            new_h = int(ih*scale)
            img_surf = pygame.transform.smoothscale(equipment.image, (new_w, new_h))
            # Center the image in the box
            img_x = img_box_x + (img_box_w - new_w)//2
            img_y = img_box_y + (img_box_h - new_h)//2
            overlay.blit(img_surf, (img_x, img_y))
        else:
            no_img_font = pygame.font.SysFont(None, max(14, img_box_h//8), bold=True)
            no_img_surf = no_img_font.render("NO IMAGE", True, (200,200,200))
            nx = img_box_x + (img_box_w - no_img_surf.get_width())//2
            ny = img_box_y + (img_box_h - no_img_surf.get_height())//2
            overlay.blit(no_img_surf, (nx, ny))
        
        # Blit overlay on top of game
        screen.blit(overlay, (menu_box_x, menu_box_y))
        pygame.display.flip()
        # Clock tick is now handled at the start of the loop for delta time

def open_equip_menu(screen_width, screen_height, menu_box_width, menu_box_height, player_equip, player_stats=None):
    # player_equip should be either a list of Equipment objects or a PlayerEquip object
    # Handle both cases for compatibility
    if hasattr(player_equip, 'get_equipment_list'):
        # It's a PlayerEquip object
        player_equip_obj = player_equip
        equipment_list = player_equip.get_equipment_list()
    else:
        # It's a list of Equipment objects - create a temporary PlayerEquip for slot management
        from Player_Equipment import PlayerEquip
        player_equip_obj = PlayerEquip("temp")
        for eq in player_equip:
            player_equip_obj.add_equipment(eq)
        equipment_list = player_equip
    
    # Ensure all equipment images are loaded (after display is set)
    try:
        from Player_Equipment import load_equipment_images
        load_equipment_images(equipment_list)
    except Exception as e:
        print(f"[EquipMenu] ERROR loading equipment images: {e}")
    # Load sounds using global SFX system
    Global_SFX.load_global_sfx_volume()  # Ensure latest SFX volume is loaded
    menu_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\menu-selection-102220.mp3", 0.4)
    spacebar_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\casual-click-pop-ui-3-262120.mp3", 0.45)
    esc_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\discard-sound-effect-221455.mp3", 1.0)

    # Load PNG
    equip_png_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Menus\Pause_Menu_Equip_V01.png"
    try:
        equip_png = pygame.image.load(equip_png_path).convert_alpha()
    except Exception as e:
        print(f"[EquipMenu] Could not load equip PNG: {e}")
        equip_png = None

    # Calculate menu box position
    menu_box_x = (screen_width - menu_box_width) // 2
    menu_box_y = (screen_height - menu_box_height) // 2

    # Get main display surface
    screen = pygame.display.get_surface()

    running = True
    clock = pygame.time.Clock()
    section_names = ["WEAPONS", "ARMORS", "ARTIFACTS"]
    section_types = ["weapon", "armor", "artifact"]
    selected_section = 0  # 0: weapons, 1: armors, 2: artifacts
    selected_row = 0
    font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
    font_size = max(18, min(64, int(menu_box_height * 0.05)))
    try:
        font = pygame.font.Font(font_path, font_size)
    except Exception:
        font = pygame.font.SysFont(None, font_size, bold=True)

    # Split equipment by type for fast access
    weapons = [eq for eq in equipment_list if getattr(eq, 'type', None) == 'weapon']
    armors = [eq for eq in equipment_list if getattr(eq, 'type', None) == 'armor']
    artifacts = [eq for eq in equipment_list if getattr(eq, 'type', None) == 'artifact']
    section_lists = [weapons, armors, artifacts]

    while running:
        current_list = section_lists[selected_section]
        num_rows = len(current_list)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_z:
                    if esc_sound:
                        esc_sound.play()
                    running = False
                elif event.key == pygame.K_UP:
                    if num_rows > 0:
                        selected_row = (selected_row - 1) % num_rows
                        if menu_sound:
                            menu_sound.play()
                elif event.key == pygame.K_DOWN:
                    if num_rows > 0:
                        selected_row = (selected_row + 1) % num_rows
                        if menu_sound:
                            menu_sound.play()
                elif event.key == pygame.K_LEFT:
                    selected_section = (selected_section - 1) % 3
                    selected_row = 0
                    if menu_sound:
                        menu_sound.play()
                elif event.key == pygame.K_RIGHT:
                    selected_section = (selected_section + 1) % 3
                    selected_row = 0
                    if menu_sound:
                        menu_sound.play()
                elif event.key == pygame.K_SPACE:
                    if spacebar_sound:
                        spacebar_sound.play()
                    if num_rows > 0:
                        # Toggle equip/unequip for selected equipment using PlayerEquip slot management
                        eq = current_list[selected_row]
                        if eq.equipped:
                            # Unequip the item
                            player_equip_obj.unequip_item(eq)
                            print(f"[EquipMenu] Unequipped: {eq.name}")
                        else:
                            # Equip the item (will auto-unequip others of same type)
                            success = player_equip_obj.equip_item(eq)
                            if success:
                                print(f"[EquipMenu] Equipped: {eq.name}")
                            else:
                                print(f"[EquipMenu] Failed to equip: {eq.name}")
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if num_rows > 0:
                        # Show info for selected equipment
                        eq = current_list[selected_row]
                        print(f"[EquipMenu] INFO: {eq.name} - {getattr(eq, 'description', 'No description available')}")
                        # Open equipment info modal
                        open_equipment_info(screen_width, screen_height, menu_box_width, menu_box_height, eq, font_path, player_stats, player_equip_obj)
            
            # Handle controller button events
            elif event.type == pygame.JOYBUTTONDOWN:
                # Circle button (cancel/ESC equivalent)
                if is_controller_button_just_pressed(event, 'circle'):
                    if esc_sound:
                        esc_sound.play()
                    running = False
                # X button (confirm/spacebar equivalent)
                elif is_controller_button_just_pressed(event, 'x'):
                    if spacebar_sound:
                        spacebar_sound.play()
                    if num_rows > 0:
                        # Toggle equip/unequip for selected equipment using PlayerEquip slot management
                        eq = current_list[selected_row]
                        if eq.equipped:
                            # Unequip the item
                            player_equip_obj.unequip_item(eq)
                            print(f"[EquipMenu] Unequipped: {eq.name}")
                        else:
                            # Equip the item (will auto-unequip others of same type)
                            success = player_equip_obj.equip_item(eq)
                            if success:
                                print(f"[EquipMenu] Equipped: {eq.name}")
                            else:
                                print(f"[EquipMenu] Failed to equip: {eq.name}")
                # Square button (info/shift equivalent)
                elif is_controller_button_just_pressed(event, 'square'):
                    if num_rows > 0:
                        # Show info for selected equipment
                        eq = current_list[selected_row]
                        print(f"[EquipMenu] INFO: {eq.name} - {getattr(eq, 'description', 'No description available')}")
                        # Open equipment info modal
                        open_equipment_info(screen_width, screen_height, menu_box_width, menu_box_height, eq, font_path, player_stats, player_equip_obj)
            
            # Handle controller D-pad events
            elif event.type == pygame.JOYHATMOTION:
                # Up
                if is_controller_hat_just_moved(event, 'up'):
                    if num_rows > 0:
                        selected_row = (selected_row - 1) % num_rows
                        if menu_sound:
                            menu_sound.play()
                # Down
                elif is_controller_hat_just_moved(event, 'down'):
                    if num_rows > 0:
                        selected_row = (selected_row + 1) % num_rows
                        if menu_sound:
                            menu_sound.play()
                # Left
                elif is_controller_hat_just_moved(event, 'left'):
                    selected_section = (selected_section - 1) % 3
                    selected_row = 0
                    if menu_sound:
                        menu_sound.play()
                # Right
                elif is_controller_hat_just_moved(event, 'right'):
                    selected_section = (selected_section + 1) % 3
                    selected_row = 0
                    if menu_sound:
                        menu_sound.play()

        # Draw transparent overlay
        overlay = pygame.Surface((menu_box_width, menu_box_height), pygame.SRCALPHA)
        overlay.fill((30, 30, 40, 180))  # Semi-transparent base

        # Draw PNG
        if equip_png:
            equip_w = equip_png.get_width()
            equip_h = equip_png.get_height()
            scale_w = menu_box_width
            scale_h = menu_box_height
            aspect = equip_w / equip_h if equip_h > 0 else 1
            if scale_w / aspect < scale_h:
                scale_h = int(scale_w / aspect)
            else:
                scale_w = int(scale_h * aspect)
            equip_surface = pygame.transform.smoothscale(equip_png, (scale_w, scale_h))
            temp_surface = pygame.Surface((scale_w, scale_h), pygame.SRCALPHA)
            temp_surface.blit(equip_surface, (0, 0))
            temp_surface.set_alpha(255)
            x = (menu_box_width - scale_w) // 2
            y = (menu_box_height - scale_h) // 2
            overlay.blit(temp_surface, (x, y))


        # Draw section tabs at the far left, all caps
        tab_font_size = max(18, int(menu_box_height * 0.055))
        try:
            tab_font = pygame.font.Font(font_path, tab_font_size)
        except Exception:
            tab_font = pygame.font.SysFont(None, tab_font_size, bold=True)
        tab_spacing = int(menu_box_width * 0.16)
        tab_y = int(menu_box_height * 0.057)
        tab_x_start = int(menu_box_width * 0.045)  # Far left
        for idx, name in enumerate(section_names):
            color = (80, 205, 80) if idx == selected_section else (255, 255, 255)
            tab_surf = tab_font.render(name, True, color)
            tab_x = tab_x_start + idx * tab_spacing
            overlay.blit(tab_surf, (tab_x, tab_y))

        # Draw equipment list for selected section
        if num_rows > 0:
            icon_box_size = int(menu_box_height * 0.165)
            col_x = int(menu_box_width * 0.040)
            start_y = int(menu_box_height * 0.16)
            row_height = int(menu_box_height * 0.175)
            name_font_size = max(18, int(menu_box_height * 0.045))
            desc_font_size = max(14, int(menu_box_height * 0.032))
            try:
                name_font = pygame.font.Font(font_path, name_font_size)
            except Exception:
                name_font = pygame.font.SysFont(None, name_font_size, bold=True)
            try:
                short_font = pygame.font.Font(font_path, desc_font_size)
            except Exception:
                short_font = pygame.font.SysFont(None, desc_font_size, bold=True)

            max_visible_rows = 4
            scroll_offset = 0
            if selected_row >= max_visible_rows:
                scroll_offset = selected_row - max_visible_rows + 1
            elif selected_row < 0:
                scroll_offset = 0

            visible_indices = range(scroll_offset, min(scroll_offset + max_visible_rows, num_rows))
            for draw_idx, i in enumerate(visible_indices):
                eq = current_list[i]
                y = start_y + draw_idx * row_height
                # Highlight background for selected
                if i == selected_row:
                    bg_rect = pygame.Rect(col_x-10, y-4, int(menu_box_width*0.38), row_height)
                    pygame.draw.rect(overlay, (255,255,255), bg_rect, border_radius=8)
                # Draw icon box
                icon_rect = pygame.Rect(col_x, y, icon_box_size, icon_box_size)
                pygame.draw.rect(overlay, (60,60,60), icon_rect, border_radius=6)
                
                # Draw yellow-golden border for equipped items
                if getattr(eq, 'equipped', False):
                    # Golden yellow color for equipped items
                    equipped_color = (255, 215, 0)  # Golden yellow
                    pygame.draw.rect(overlay, equipped_color, icon_rect, width=3, border_radius=6)
                
                # Draw icon or 'NO ICON'
                if hasattr(eq, 'icon') and eq.icon:
                    icon_img = pygame.transform.smoothscale(eq.icon, (icon_box_size-6, icon_box_size-6))
                    overlay.blit(icon_img, (col_x+3, y+3))
                else:
                    no_icon_font = pygame.font.SysFont(None, max(12, icon_box_size//4), bold=True)
                    no_icon_surf = no_icon_font.render("NO ICON", True, (200,200,200))
                    nx = col_x + (icon_box_size - no_icon_surf.get_width())//2
                    ny = y + (icon_box_size - no_icon_surf.get_height())//2
                    overlay.blit(no_icon_surf, (nx, ny))
                # Draw name (right of icon)
                name_color = (0,0,0) if i == selected_row else (255,255,255)
                # Remove [EQUIPPED] text indicator since we now use visual border
                name_surf = name_font.render(eq.name, True, name_color)
                overlay.blit(name_surf, (col_x + icon_box_size + 12, y))
                # Draw short description (below name)
                short_color = (40,40,40) if i == selected_row else (200,200,200)
                short_surf = short_font.render(eq.short_description, True, short_color)
                overlay.blit(short_surf, (col_x + icon_box_size + 12, y + name_surf.get_height() + 2))
                
                # Draw weapon class for weapons (below short description)
                if getattr(eq, 'type', None) == 'weapon' and hasattr(eq, 'weapon_class') and eq.weapon_class:
                    weapon_class_color = (60,60,60) if i == selected_row else (150,150,200)  # Slightly different color
                    weapon_class_text = f"Class: {eq.weapon_class}"
                    weapon_class_surf = short_font.render(weapon_class_text, True, weapon_class_color)
                    overlay.blit(weapon_class_surf, (col_x + icon_box_size + 12, y + name_surf.get_height() + short_surf.get_height() + 4))

        # Draw full image of selected equipment in the right panel (responsive)
        if num_rows > 0:
            # --- Equipment Image Box (easy to adjust) ---
            # Change these values to move/resize the image box:
            img_box_x = int(menu_box_width * 0.60)   # X position (fraction of menu width)
            img_box_y = int(menu_box_height * 0.175)  # Y position (fraction of menu height)
            img_box_w = int(menu_box_width * 0.38)   # Width (fraction of menu width)
            img_box_h = int(menu_box_height * 0.78)  # Height (fraction of menu height)
            eq = current_list[selected_row]
            
            # Draw equipment name text (without green box since it's in the PNG)
            name_font_size = max(16, int(menu_box_height * 0.04))
            try:
                name_display_font = pygame.font.Font(font_path, name_font_size)
            except Exception:
                name_display_font = pygame.font.SysFont(None, name_font_size, bold=True)
            
            name_text = eq.name
            name_surf = name_display_font.render(name_text, True, (255, 255, 255))
            name_x = img_box_x + (img_box_w - name_surf.get_width()) // 2
            name_y = int(menu_box_height * 0.049)  # Same position as INFO menu
            overlay.blit(name_surf, (name_x, name_y))
            
            # Draw equipment image below the name box
            if eq.image:
                iw, ih = eq.image.get_width(), eq.image.get_height()
                # Scale image to fit inside the box, preserving aspect ratio with safety margin
                safety_margin = 0.9  # Use 90% of available space to prevent border overlap
                scale = min((img_box_w * safety_margin)/iw, (img_box_h * safety_margin)/ih, 1.0)
                new_w = int(iw*scale)
                new_h = int(ih*scale)
                img_surf = pygame.transform.smoothscale(eq.image, (new_w, new_h))
                # Center the image in the box
                img_x = img_box_x + (img_box_w - new_w)//2
                img_y = img_box_y + (img_box_h - new_h)//2
                overlay.blit(img_surf, (img_x, img_y))
            else:
                no_img_font = pygame.font.SysFont(None, max(14, img_box_h//8), bold=True)
                no_img_surf = no_img_font.render("NO IMAGE", True, (200,200,200))
                nx = img_box_x + (img_box_w - no_img_surf.get_width())//2
                ny = img_box_y + (img_box_h - no_img_surf.get_height())//2
                overlay.blit(no_img_surf, (nx, ny))

        # Draw control instructions at bottom left
        control_font_size = max(14, int(menu_box_height * 0.035))
        try:
            control_font = pygame.font.Font(font_path, control_font_size)
        except Exception:
            control_font = pygame.font.SysFont(None, control_font_size, bold=True)
        
        control_text = "SPACEBAR: EQUIP/UNEQUIP      SHIFT: INFO"
        control_surf = control_font.render(control_text, True, (255, 255, 255))
        control_x = int(menu_box_width * 0.08)
        control_y = int(menu_box_height * 0.92)
        overlay.blit(control_surf, (control_x, control_y))

        # Blit overlay on top of game
        screen.blit(overlay, (menu_box_x, menu_box_y))
        pygame.display.flip()
        clock.tick(60)
    return
