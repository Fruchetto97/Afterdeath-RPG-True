# Overworld_Menu_Items_V1.py
# ITEMS sub-menu for the overworld pause menu
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

def draw_usage_prompt(overlay, menu_box_width, menu_box_height, item_name, max_count, selected_count, font_path):
    """Draw the 'Use How Many?' prompt dialog."""
    # Create semi-transparent background
    prompt_width = int(menu_box_width * 0.4)
    prompt_height = int(menu_box_height * 0.25)
    prompt_x = (menu_box_width - prompt_width) // 2
    prompt_y = (menu_box_height - prompt_height) // 2
    
    # Draw dark background with red border
    prompt_rect = pygame.Rect(prompt_x, prompt_y, prompt_width, prompt_height)
    pygame.draw.rect(overlay, (30, 30, 30, 220), prompt_rect)
    pygame.draw.rect(overlay, (200, 50, 50), prompt_rect, 3)
    
    # Setup fonts
    title_font_size = max(16, int(menu_box_height * 0.04))
    text_font_size = max(14, int(menu_box_height * 0.032))
    try:
        title_font = pygame.font.Font(font_path, title_font_size)
        text_font = pygame.font.Font(font_path, text_font_size)
    except Exception:
        title_font = pygame.font.SysFont(None, title_font_size, bold=True)
        text_font = pygame.font.SysFont(None, text_font_size)
    
    # Draw title
    title_surf = title_font.render("Use How Many?", True, (255, 255, 255))
    title_x = prompt_x + (prompt_width - title_surf.get_width()) // 2
    title_y = prompt_y + 15
    overlay.blit(title_surf, (title_x, title_y))
    
    # Draw item name
    item_surf = text_font.render(f"Item: {item_name}", True, (200, 200, 200))
    item_x = prompt_x + (prompt_width - item_surf.get_width()) // 2
    item_y = title_y + title_surf.get_height() + 10
    overlay.blit(item_surf, (item_x, item_y))
    
    # Draw count selector
    count_text = f"< {selected_count} / {max_count} >"
    count_surf = title_font.render(count_text, True, (255, 215, 0))
    count_x = prompt_x + (prompt_width - count_surf.get_width()) // 2
    count_y = item_y + item_surf.get_height() + 15
    overlay.blit(count_surf, (count_x, count_y))
    
    # Draw instructions
    instr_surf = text_font.render("LEFT/RIGHT: Change  SPACEBAR: Confirm  ESC: Cancel", True, (180, 180, 180))
    instr_x = prompt_x + (prompt_width - instr_surf.get_width()) // 2
    instr_y = count_y + count_surf.get_height() + 15
    overlay.blit(instr_surf, (instr_x, instr_y))

def draw_message_dialog(overlay, menu_box_width, menu_box_height, message, font_path):
    """Draw a message dialog with dark background and red border."""
    # Calculate dialog size based on message length
    dialog_width = min(int(menu_box_width * 0.6), 500)
    dialog_height = int(menu_box_height * 0.3)
    dialog_x = (menu_box_width - dialog_width) // 2
    dialog_y = (menu_box_height - dialog_height) // 2
    
    # Draw dark background with red border
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(overlay, (30, 30, 30, 220), dialog_rect)
    pygame.draw.rect(overlay, (200, 50, 50), dialog_rect, 3)
    
    # Setup fonts
    text_font_size = max(14, int(menu_box_height * 0.032))
    try:
        text_font = pygame.font.Font(font_path, text_font_size)
    except Exception:
        text_font = pygame.font.SysFont(None, text_font_size)
    
    # Word wrap the message
    words = message.split(' ')
    lines = []
    current_line = ''
    max_width = dialog_width - 40  # 20px padding on each side
    
    for word in words:
        test_line = current_line + (' ' if current_line else '') + word
        test_surf = text_font.render(test_line, True, (255, 255, 255))
        if test_surf.get_width() <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Draw message lines
    line_height = text_font.get_height() + 2
    total_text_height = len(lines) * line_height
    start_y = dialog_y + (dialog_height - total_text_height) // 2 - 20  # Leave space for instruction
    
    for i, line in enumerate(lines):
        line_surf = text_font.render(line, True, (255, 255, 255))
        line_x = dialog_x + (dialog_width - line_surf.get_width()) // 2
        line_y = start_y + i * line_height
        overlay.blit(line_surf, (line_x, line_y))
    
    # Draw instruction at bottom
    instr_surf = text_font.render("SPACEBAR or ESC: Continue", True, (180, 180, 180))
    instr_x = dialog_x + (dialog_width - instr_surf.get_width()) // 2
    instr_y = dialog_y + dialog_height - 30
    overlay.blit(instr_surf, (instr_x, instr_y))

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
    if controller and controller.get_numhats() > 0:
        hat = controller.get_hat(0)
        dpad_up = hat[1] == 1
        dpad_down = hat[1] == -1
        dpad_left = hat[0] == -1
        dpad_right = hat[0] == 1
    
    # Get button states
    button_x = button_circle = button_square = False
    if controller:
        button_x = controller.get_button(0) if controller.get_numbuttons() > 0 else False
        button_circle = controller.get_button(1) if controller.get_numbuttons() > 1 else False
        button_square = controller.get_button(2) if controller.get_numbuttons() > 2 else False
    
    return {
        'up': keys[pygame.K_UP] or keys[pygame.K_w] or dpad_up,
        'down': keys[pygame.K_DOWN] or keys[pygame.K_s] or dpad_down,
        'left': keys[pygame.K_LEFT] or keys[pygame.K_a] or dpad_left,
        'right': keys[pygame.K_RIGHT] or keys[pygame.K_d] or dpad_right,
        'confirm': keys[pygame.K_SPACE] or button_x,
        'cancel': keys[pygame.K_ESCAPE] or keys[pygame.K_z] or button_circle,
        'info': keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or button_square
    }

def open_items_menu(screen_width, screen_height, menu_box_width, menu_box_height, player_items, player_stats=None):
    # player_items should be either a list of Item objects or a PlayerItems object
    # Handle both cases for compatibility
    if hasattr(player_items, 'get_item_list'):
        # It's a PlayerItems object
        player_items_obj = player_items
        items_list = player_items.get_item_list()
    else:
        # It's a list of Item objects - create a temporary PlayerItems for compatibility
        from Player_Items import PlayerItems
        player_items_obj = PlayerItems("temp")
        for item in player_items:
            player_items_obj.add_item(item)
        items_list = player_items

    # Ensure all item images are loaded (after display is set)
    try:
        from Player_Items import load_item_images
        load_item_images(items_list)
    except Exception as e:
        pass  # Silently ignore image loading errors

    # Load sounds using global SFX system
    Global_SFX.load_global_sfx_volume()  # Ensure latest SFX volume is loaded
    menu_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\menu-selection-102220.mp3", 0.4)
    spacebar_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\casual-click-pop-ui-3-262120.mp3", 0.45)
    esc_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\discard-sound-effect-221455.mp3", 1.0)

    # Load PNG (using the same base PNG as the Equip menu)
    items_png_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Menus\Pause_Menu_Equip_V01.png"
    try:
        items_png = pygame.image.load(items_png_path).convert_alpha()
    except Exception as e:
        items_png = None

    # Calculate menu box position
    menu_box_x = (screen_width - menu_box_width) // 2
    menu_box_y = (screen_height - menu_box_height) // 2

    # Get main display surface
    screen = pygame.display.get_surface()

    running = True
    clock = pygame.time.Clock()
    show_info = False  # Toggle between image and detailed info display
    show_usage_prompt = False  # Show usage prompt dialog
    show_message_dialog = False  # Show message dialog
    message_dialog_text = ""  # Text to show in message dialog
    usage_count = 1  # How many items to use
    usage_item = None  # Which item is being used
    section_names = ["MISC", "FOOD", "KEY"]
    section_types = ["MISC", "FOOD", "KEY"]
    selected_section = 0  # 0: MISC, 1: FOOD, 2: KEY
    selected_row = 0
    font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
    font_size = max(18, min(64, int(menu_box_height * 0.05)))
    try:
        font = pygame.font.Font(font_path, font_size)
    except Exception:
        font = pygame.font.SysFont(None, font_size, bold=True)

    # Split items by type for fast access
    misc_items = [item for item in items_list if getattr(item, 'type', None) == 'MISC']
    food_items = [item for item in items_list if getattr(item, 'type', None) == 'FOOD']
    key_items = [item for item in items_list if getattr(item, 'type', None) == 'KEY']
    section_lists = [misc_items, food_items, key_items]

    while running:
        # Refresh section lists at the beginning of each loop to ensure they're current
        misc_items = [item for item in items_list if getattr(item, 'type', None) == 'MISC']
        food_items = [item for item in items_list if getattr(item, 'type', None) == 'FOOD']
        key_items = [item for item in items_list if getattr(item, 'type', None) == 'KEY']
        section_lists = [misc_items, food_items, key_items]
        
        current_list = section_lists[selected_section]
        num_rows = len(current_list)
        
        # Ensure selected_row is within bounds
        if num_rows > 0 and selected_row >= num_rows:
            selected_row = num_rows - 1
        elif num_rows == 0:
            selected_row = 0
        
        # Get unified input state for continuous checking
        unified_input = get_unified_menu_input()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION):
                # Unified input handling for keyboard and controller events
                key_pressed = None
                if event.type == pygame.KEYDOWN:
                    key_pressed = event.key
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Map controller buttons to keyboard equivalents
                    if is_controller_button_just_pressed(event, 'x'):
                        key_pressed = pygame.K_SPACE
                    elif is_controller_button_just_pressed(event, 'circle'):
                        key_pressed = pygame.K_ESCAPE
                    elif is_controller_button_just_pressed(event, 'square'):
                        key_pressed = pygame.K_LSHIFT  # Map Square to Shift for info toggle
                elif event.type == pygame.JOYHATMOTION:
                    # Map D-pad to arrow keys
                    if is_controller_hat_just_moved(event, 'up'):
                        key_pressed = pygame.K_UP
                    elif is_controller_hat_just_moved(event, 'down'):
                        key_pressed = pygame.K_DOWN
                    elif is_controller_hat_just_moved(event, 'left'):
                        key_pressed = pygame.K_LEFT
                    elif is_controller_hat_just_moved(event, 'right'):
                        key_pressed = pygame.K_RIGHT
                
                # Process the mapped key input
                if key_pressed is not None:
                    if show_message_dialog:
                        # Handle message dialog events
                        if key_pressed == pygame.K_SPACE or key_pressed == pygame.K_ESCAPE or key_pressed == pygame.K_z:
                            # Close message dialog
                            show_message_dialog = False
                            message_dialog_text = ""
                            if menu_sound:
                                menu_sound.play()
                    elif show_usage_prompt:
                        # Handle usage prompt events
                        if key_pressed == pygame.K_ESCAPE or key_pressed == pygame.K_z:
                            # Cancel usage
                            show_usage_prompt = False
                            usage_item = None
                            usage_count = 1
                            if esc_sound:
                                esc_sound.play()
                        elif key_pressed == pygame.K_LEFT:
                            # Decrease count
                            if usage_count > 1:
                                usage_count -= 1
                                if menu_sound:
                                    menu_sound.play()
                        elif key_pressed == pygame.K_RIGHT:
                            # Increase count
                            max_count = getattr(usage_item, 'count', 1)
                            if usage_count < max_count:
                                usage_count += 1
                                if menu_sound:
                                    menu_sound.play()
                        elif key_pressed == pygame.K_SPACE:
                            # Confirm usage
                            if spacebar_sound:
                                spacebar_sound.play()
                            
                            # Use the item - UNIFIED PROCESSING PATH
                            try:
                                result = usage_item.use_item(player_stats, usage_count)
                                
                                # Parse result - IDENTICAL TO DIRECT PATH
                                if isinstance(result, dict):
                                    success = result.get('success', False)
                                    message = result.get('message', '')
                                    show_msg = result.get('show_message', False)
                                else:
                                    success = bool(result)
                                    message = ''
                                    show_msg = False
                                
                                # Handle inventory management based on success
                                if success:
                                    # Only remove items from inventory if usage was successful
                                    player_items_obj.remove_item_by_name(usage_item.name, usage_count)
                                    
                                    # Refresh the global items list
                                    items_list = player_items_obj.get_item_list()
                                
                                # Show message dialog regardless of success/failure - GENERAL PURPOSE SYSTEM
                                if show_msg and message:
                                    show_message_dialog = True
                                    message_dialog_text = message
                                
                                # Close prompt
                                show_usage_prompt = False
                                
                            except Exception as e:
                                import traceback
                                traceback.print_exc()
                                show_usage_prompt = False
                            usage_item = None
                            usage_count = 1
                    else:
                        # Handle normal menu events
                        if key_pressed == pygame.K_ESCAPE or key_pressed == pygame.K_z:
                            if esc_sound:
                                esc_sound.play()
                            running = False
                        elif key_pressed == pygame.K_UP:
                            if num_rows > 0:
                                selected_row = (selected_row - 1) % num_rows
                                if menu_sound:
                                    menu_sound.play()
                        elif key_pressed == pygame.K_DOWN:
                            if num_rows > 0:
                                selected_row = (selected_row + 1) % num_rows
                                if menu_sound:
                                    menu_sound.play()
                        elif key_pressed == pygame.K_LEFT:
                            selected_section = (selected_section - 1) % 3
                            selected_row = 0
                            if menu_sound:
                                menu_sound.play()
                        elif key_pressed == pygame.K_RIGHT:
                            selected_section = (selected_section + 1) % 3
                            selected_row = 0
                            if menu_sound:
                                menu_sound.play()
                        elif key_pressed == pygame.K_SPACE:
                            if num_rows > 0:
                                item = current_list[selected_row]
                                item_count = getattr(item, 'count', 1)
                                
                                if item_count > 1:
                                    # Show usage prompt for multiple items
                                    show_usage_prompt = True
                                    usage_item = item
                                    usage_count = 1
                                    if spacebar_sound:
                                        spacebar_sound.play()
                                else:
                                    # Use single item directly - UNIFIED PROCESSING PATH
                                    if spacebar_sound:
                                        spacebar_sound.play()
                                    
                                    try:
                                        result = item.use_item(player_stats, 1)
                                        
                                        # Parse result - IDENTICAL TO USAGE PROMPT PATH
                                        if isinstance(result, dict):
                                            success = result.get('success', False)
                                            message = result.get('message', '')
                                            show_msg = result.get('show_message', False)
                                        else:
                                            success = bool(result)
                                            message = ''
                                            show_msg = False
                                        
                                        # Handle inventory management based on success
                                        if success:
                                            player_items_obj.remove_item_by_name(item.name, 1)
                                            
                                            # Refresh the global items list
                                            items_list = player_items_obj.get_item_list()
                                        
                                        # Show message dialog regardless of success/failure - GENERAL PURPOSE SYSTEM
                                        if show_msg and message:
                                            show_message_dialog = True
                                            message_dialog_text = message
                                        
                                    except Exception as e:
                                        import traceback
                                        traceback.print_exc()
                        elif key_pressed == pygame.K_LSHIFT or key_pressed == pygame.K_RSHIFT:
                            if num_rows > 0:
                                # Toggle info display mode
                                show_info = not show_info
                                if menu_sound:
                                    menu_sound.play()

        # Draw transparent overlay
        overlay = pygame.Surface((menu_box_width, menu_box_height), pygame.SRCALPHA)
        overlay.fill((30, 30, 40, 180))  # Semi-transparent base

        # Draw PNG
        if items_png:
            items_w = items_png.get_width()
            items_h = items_png.get_height()
            scale_w = menu_box_width
            scale_h = menu_box_height
            aspect = items_w / items_h if items_h > 0 else 1
            if scale_w / aspect < scale_h:
                scale_h = int(scale_w / aspect)
            else:
                scale_w = int(scale_h * aspect)
            items_surface = pygame.transform.smoothscale(items_png, (scale_w, scale_h))
            temp_surface = pygame.Surface((scale_w, scale_h), pygame.SRCALPHA)
            temp_surface.blit(items_surface, (0, 0))
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

        # Draw items list for selected section
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
                # Bounds check to prevent IndexError
                if i >= len(current_list):
                    break
                    
                item = current_list[i]
                y = start_y + draw_idx * row_height
                
                # Highlight background for selected
                if i == selected_row:
                    bg_rect = pygame.Rect(col_x-10, y-4, int(menu_box_width*0.38), row_height)
                    pygame.draw.rect(overlay, (255,255,255), bg_rect, border_radius=8)
                
                # Draw icon box
                icon_rect = pygame.Rect(col_x, y, icon_box_size, icon_box_size)
                pygame.draw.rect(overlay, (60,60,60), icon_rect, border_radius=6)
                
                # Draw icon or 'NO ICON'
                if hasattr(item, 'icon') and item.icon:
                    icon_img = pygame.transform.smoothscale(item.icon, (icon_box_size-6, icon_box_size-6))
                    overlay.blit(icon_img, (col_x+3, y+3))
                else:
                    no_icon_font = pygame.font.SysFont(None, max(12, icon_box_size//4), bold=True)
                    no_icon_surf = no_icon_font.render("NO ICON", True, (200,200,200))
                    nx = col_x + (icon_box_size - no_icon_surf.get_width())//2
                    ny = y + (icon_box_size - no_icon_surf.get_height())//2
                    overlay.blit(no_icon_surf, (nx, ny))
                
                # Draw name (right of icon)
                name_color = (0,0,0) if i == selected_row else (255,255,255)
                name_surf = name_font.render(item.name, True, name_color)
                overlay.blit(name_surf, (col_x + icon_box_size + 12, y))
                
                # Draw short description (below name)
                short_color = (40,40,40) if i == selected_row else (200,200,200)
                short_surf = short_font.render(item.short_description, True, short_color)
                overlay.blit(short_surf, (col_x + icon_box_size + 12, y + name_surf.get_height() + 2))
                
                # Draw item count (below short description)
                count_color = (80,80,80) if i == selected_row else (180,180,180)
                count_text = f"In possession: {getattr(item, 'count', 1)}"
                count_surf = short_font.render(count_text, True, count_color)
                overlay.blit(count_surf, (col_x + icon_box_size + 12, y + name_surf.get_height() + short_surf.get_height() + 4))
                
                # Draw item type for clarity (below count)
                type_color = (60,60,60) if i == selected_row else (150,150,200)
                type_text = f"Type: {item.type}"
                type_surf = short_font.render(type_text, True, type_color)
                overlay.blit(type_surf, (col_x + icon_box_size + 12, y + name_surf.get_height() + short_surf.get_height() + count_surf.get_height() + 8))

        # Draw full image of selected item in the right panel (responsive)
        if num_rows > 0:
            # --- Item Image Box (easy to adjust) ---
            # Change these values to move/resize the image box:
            img_box_x = int(menu_box_width * 0.60)   # X position (fraction of menu width)
            img_box_y = int(menu_box_height * 0.175)  # Y position (fraction of menu height)
            img_box_w = int(menu_box_width * 0.38)   # Width (fraction of menu width)
            img_box_h = int(menu_box_height * 0.78)  # Height (fraction of menu height)
            item = current_list[selected_row]
            
            # Draw item name text (without green box since it's in the PNG)
            name_font_size = max(16, int(menu_box_height * 0.04))
            try:
                name_display_font = pygame.font.Font(font_path, name_font_size)
            except Exception:
                name_display_font = pygame.font.SysFont(None, name_font_size, bold=True)
            
            name_text = item.name
            name_surf = name_display_font.render(name_text, True, (255, 255, 255))
            name_x = img_box_x + (img_box_w - name_surf.get_width()) // 2
            name_y = int(menu_box_height * 0.049)  # Same position as INFO menu
            overlay.blit(name_surf, (name_x, name_y))
            
            if show_info:
                # Show detailed item information instead of image
                info_x = img_box_x + 10
                info_y = img_box_y + 20  # Moved down slightly to avoid touching UI
                info_width = img_box_w - 20
                
                # Setup fonts for detailed info
                info_title_font_size = max(16, int(menu_box_height * 0.04))
                info_text_font_size = max(14, int(menu_box_height * 0.032))
                try:
                    info_title_font = pygame.font.Font(font_path, info_title_font_size)
                    info_text_font = pygame.font.Font(font_path, info_text_font_size)
                except Exception:
                    info_title_font = pygame.font.SysFont(None, info_title_font_size, bold=True)
                    info_text_font = pygame.font.SysFont(None, info_text_font_size)
                
                current_y = info_y
                line_spacing = 8
                
                # Item Value (if it has one)
                if hasattr(item, 'value') and item.value:
                    value_surf = info_text_font.render(f"Value: {item.value} S", True, (200, 200, 200))
                    overlay.blit(value_surf, (info_x, current_y))
                    current_y += value_surf.get_height() + line_spacing
                
                # Item Weight (if it has one)
                if hasattr(item, 'weight') and item.weight:
                    weight_surf = info_text_font.render(f"Weight: {item.weight} g", True, (200, 200, 200))
                    overlay.blit(weight_surf, (info_x, current_y))
                    current_y += weight_surf.get_height() + line_spacing
                
                # Add some spacing before description
                current_y += line_spacing
                
                # Item Description (word-wrapped)
                description_title_surf = info_title_font.render("DESCRIPTION:", True, (255, 215, 0))
                overlay.blit(description_title_surf, (info_x, current_y))
                current_y += description_title_surf.get_height() + line_spacing
                
                # Word wrap the description
                description = getattr(item, 'description', 'No detailed description available.')
                wrapped_lines = []
                words = description.split(' ')
                current_line = ''
                
                for word in words:
                    test_line = current_line + (' ' if current_line else '') + word
                    test_surf = info_text_font.render(test_line, True, (255, 255, 255))
                    if test_surf.get_width() <= info_width:
                        current_line = test_line
                    else:
                        if current_line:
                            wrapped_lines.append(current_line)
                        current_line = word
                if current_line:
                    wrapped_lines.append(current_line)
                
                # Draw wrapped description lines
                desc_line_height = info_text_font.get_height() + 2
                remaining_height = img_box_y + img_box_h - current_y - 20  # Leave some bottom margin
                max_desc_lines = int(remaining_height / desc_line_height)
                
                for i, line in enumerate(wrapped_lines[:max_desc_lines]):
                    line_surf = info_text_font.render(line, True, (255, 255, 255))
                    overlay.blit(line_surf, (info_x, current_y + i * desc_line_height))
                
            else:
                # Show item image (original behavior)
                if item.image:
                    iw, ih = item.image.get_width(), item.image.get_height()
                    # Scale image to fit inside the box, preserving aspect ratio with safety margin
                    safety_margin = 0.9  # Use 90% of available space to prevent border overlap
                    scale = min((img_box_w * safety_margin)/iw, (img_box_h * safety_margin)/ih, 1.0)
                    new_w = int(iw*scale)
                    new_h = int(ih*scale)
                    img_surf = pygame.transform.smoothscale(item.image, (new_w, new_h))
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
        
        # Update control text based on current mode
        if show_info:
            control_text = "SPACEBAR/X: USE ITEM      SHIFT/SQUARE: SHOW IMAGE"
        else:
            control_text = "SPACEBAR/X: USE ITEM      SHIFT/SQUARE: SHOW INFO"
        control_surf = control_font.render(control_text, True, (255, 255, 255))
        control_x = int(menu_box_width * 0.08)
        control_y = int(menu_box_height * 0.92)
        overlay.blit(control_surf, (control_x, control_y))

        # Draw usage prompt if active
        if show_usage_prompt and usage_item:
            max_count = getattr(usage_item, 'count', 1)
            draw_usage_prompt(overlay, menu_box_width, menu_box_height, usage_item.name, max_count, usage_count, font_path)
        
        # Draw message dialog if active
        if show_message_dialog and message_dialog_text:
            draw_message_dialog(overlay, menu_box_width, menu_box_height, message_dialog_text, font_path)

        # Blit overlay on top of game
        screen.blit(overlay, (menu_box_x, menu_box_y))
        pygame.display.flip()
        clock.tick(60)
    
    return
