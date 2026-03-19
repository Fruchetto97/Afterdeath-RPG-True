# Overworld_Menu_Stats_V1.py
# STATS sub-menu for the overworld pause menu
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
    button_x = button_circle = False
    if controller:
        button_x = controller.get_button(0) if controller.get_numbuttons() > 0 else False
        button_circle = controller.get_button(1) if controller.get_numbuttons() > 1 else False
    
    return {
        'up': keys[pygame.K_UP] or keys[pygame.K_w] or dpad_up,
        'down': keys[pygame.K_DOWN] or keys[pygame.K_s] or dpad_down,
        'left': keys[pygame.K_LEFT] or keys[pygame.K_a] or dpad_left,
        'right': keys[pygame.K_RIGHT] or keys[pygame.K_d] or dpad_right,
        'confirm': keys[pygame.K_SPACE] or button_x,
        'cancel': keys[pygame.K_ESCAPE] or keys[pygame.K_z] or button_circle
    }

def open_stats_menu(screen_width, screen_height, menu_box_width, menu_box_height, player_stats):
    # Load sounds using global SFX system
    Global_SFX.load_global_sfx_volume()  # Ensure latest SFX volume is loaded
    menu_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\menu-selection-102220.mp3", 0.4)
    spacebar_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\casual-click-pop-ui-3-262120.mp3", 0.45)
    esc_sound = Global_SFX.load_sound_with_global_volume(
        r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\discard-sound-effect-221455.mp3", 1.0)

    """
    Opens a new window centered on the screen, with the same dimensions as the base menu.
    Displays player stats and a PNG background. Closes on ESC or Z.
    """
    # Load PNG
    stats_png_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Menus\Pause_Menu_Stats_V01.png"
    try:
        stats_png = pygame.image.load(stats_png_path).convert_alpha()
    except Exception as e:
        print(f"[StatsMenu] Could not load stats PNG: {e}")
        stats_png = None

    # Calculate menu box position
    menu_box_x = (screen_width - menu_box_width) // 2
    menu_box_y = (screen_height - menu_box_height) // 2

    # Get main display surface
    screen = pygame.display.get_surface()

    

    # Handle close events
    running = True
    clock = pygame.time.Clock()
    selected_row = 0
    blink_timer = 0.0
    blink_on = True
    BLINK_PERIOD = 0.25  # seconds (2Hz)
    num_rows = 8  # Number of stat rows
    level_up_mode = False
    confirming = False
    confirm_selected = 1  # 0 = YES, 1 = NO (default)
    stat_rows = [
        ("Health", "evo_points_hp", getattr(player_stats, "total_hp", 0)),
        ("Regen", "evo_points_regen", getattr(player_stats, "max_regen", 0)),
        ("Reserve", "evo_points_reserve", getattr(player_stats, "max_reserve", 0)),
        ("Stamina", "evo_points_stamina", getattr(player_stats, "max_stamina", 0)),
        ("Strength", "evo_points_strength", getattr(player_stats, "strength", 0)),
        ("Dexterity", "evo_points_dexterity", getattr(player_stats, "dexterity", 0)),
        ("Special", "evo_points_special", getattr(player_stats, "special", 0)),
        ("Speed", "evo_points_speed", getattr(player_stats, "speed", 0)),
    ]
    # Save original evo points for revert
    original_evo = {evo_attr: getattr(player_stats, evo_attr, 0) for _, evo_attr, _ in stat_rows}
    original_evo_points_remaining = getattr(player_stats, 'evo_points_remaining', 0)

    # Define original stat values for level up mode
    orig_hp = None
    orig_regen = None
    orig_stamina = None
    orig_reserve = None
    orig_strength = None
    orig_dexterity = None
    orig_special = None
    orig_speed = None

    while running:
        dt = clock.tick(60) / 1000.0  # seconds
        blink_timer += dt
        if blink_timer >= BLINK_PERIOD:
            blink_timer -= BLINK_PERIOD
            blink_on = not blink_on
        
        # Get unified input state for continuous checking
        unified_input = get_unified_menu_input()
        
        # Ensure blink always starts with black for selection
        # This is handled in event logic below for both modes
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION):
                # Unified input handling for keyboard and controller
                key_pressed = None
                if event.type == pygame.KEYDOWN:
                    key_pressed = event.key
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Map controller buttons to keyboard equivalents
                    if is_controller_button_just_pressed(event, 'x'):
                        key_pressed = pygame.K_SPACE
                    elif is_controller_button_just_pressed(event, 'circle'):
                        key_pressed = pygame.K_ESCAPE
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
                    if confirming:
                        if key_pressed == pygame.K_LEFT or key_pressed == pygame.K_RIGHT:
                            confirm_selected = 1 - confirm_selected  # Toggle YES/NO
                        elif key_pressed == pygame.K_RETURN or key_pressed == pygame.K_SPACE:
                            if spacebar_sound:
                                spacebar_sound.play()
                            if confirm_selected == 0:
                                # YES: apply changes, exit level up mode
                                confirming = False
                                level_up_mode = False
                                # Changes are already applied
                            else:
                                # NO: revert changes and exit level up mode
                                for _, evo_attr, _ in stat_rows:
                                    setattr(player_stats, evo_attr, original_evo[evo_attr])
                                setattr(player_stats, 'evo_points_remaining', original_evo_points_remaining)
                                if hasattr(player_stats, 'update_main_stats'):
                                    player_stats.update_main_stats()
                                if hasattr(player_stats, 'update_evo_points_remaining'):
                                    player_stats.update_evo_points_remaining()
                                confirming = False
                                level_up_mode = False
                        elif key_pressed == pygame.K_ESCAPE or key_pressed == pygame.K_z:
                            if esc_sound:
                                esc_sound.play()
                            # Cancel confirmation, revert changes, exit level up mode
                            for _, evo_attr, _ in stat_rows:
                                setattr(player_stats, evo_attr, original_evo[evo_attr])
                            setattr(player_stats, 'evo_points_remaining', original_evo_points_remaining)
                            if hasattr(player_stats, 'update_main_stats'):
                                player_stats.update_main_stats()
                            if hasattr(player_stats, 'update_evo_points_remaining'):
                                player_stats.update_evo_points_remaining()
                            confirming = False
                            level_up_mode = False
                    elif level_up_mode:
                        if key_pressed == pygame.K_ESCAPE:
                            if esc_sound:
                                esc_sound.play()
                            # Exit level up mode and revert changes
                            for _, evo_attr, _ in stat_rows:
                                setattr(player_stats, evo_attr, original_evo[evo_attr])
                            setattr(player_stats, 'evo_points_remaining', original_evo_points_remaining)
                            if hasattr(player_stats, 'update_main_stats'):
                                player_stats.update_main_stats()
                            if hasattr(player_stats, 'update_evo_points_remaining'):
                                player_stats.update_evo_points_remaining()
                            level_up_mode = False
                        elif key_pressed == pygame.K_UP:
                            selected_row = (selected_row - 1) % num_rows
                            blink_timer = 0.0
                            blink_on = False  # Start with black
                            if menu_sound:
                                menu_sound.play()
                        elif key_pressed == pygame.K_DOWN:
                            selected_row = (selected_row + 1) % num_rows
                            blink_timer = 0.0
                            blink_on = False  # Start with black
                            if menu_sound:
                                menu_sound.play()
                        elif key_pressed == pygame.K_RIGHT:
                            stat_name, evo_attr, stat_val = stat_rows[selected_row]
                            current_val = getattr(player_stats, evo_attr, 0)
                            spent = sum(getattr(player_stats, attr, 0) for _, attr, _ in stat_rows)
                            available = getattr(player_stats, 'evo_points', 0)
                            if spent < available:
                                setattr(player_stats, evo_attr, current_val + 1)
                                if hasattr(player_stats, 'update_evo_points_remaining'):
                                    player_stats.update_evo_points_remaining()
                                if hasattr(player_stats, 'update_main_stats'):
                                    player_stats.update_main_stats()
                                if menu_sound:
                                    menu_sound.play()
                        elif key_pressed == pygame.K_LEFT:
                            stat_name, evo_attr, stat_val = stat_rows[selected_row]
                            current_val = getattr(player_stats, evo_attr, 0)
                            allow_decrease = False
                            if evo_attr == 'evo_points_hp' and current_val > orig_hp:
                                allow_decrease = True
                            elif evo_attr == 'evo_points_regen' and current_val > orig_regen:
                                allow_decrease = True
                            elif evo_attr == 'evo_points_stamina' and current_val > orig_stamina:
                                allow_decrease = True
                            elif evo_attr == 'evo_points_reserve' and current_val > orig_reserve:
                                allow_decrease = True
                            elif evo_attr == 'evo_points_strength' and current_val > orig_strength:
                                allow_decrease = True
                            elif evo_attr == 'evo_points_dexterity' and current_val > orig_dexterity:
                                allow_decrease = True
                            elif evo_attr == 'evo_points_special' and current_val > orig_special:
                                allow_decrease = True
                            elif evo_attr == 'evo_points_speed' and current_val > orig_speed:
                                allow_decrease = True
                            elif current_val > 0 and evo_attr in ('evo_points_special', 'evo_points_speed'):
                                allow_decrease = True
                            if allow_decrease:
                                setattr(player_stats, evo_attr, current_val - 1)
                                if hasattr(player_stats, 'update_evo_points_remaining'):
                                    player_stats.update_evo_points_remaining()
                                if hasattr(player_stats, 'update_main_stats'):
                                    player_stats.update_main_stats()
                                if menu_sound:
                                    menu_sound.play()
                        elif key_pressed == pygame.K_SPACE:
                            # Only allow confirmation if all points spent
                            if spacebar_sound:
                                spacebar_sound.play()
                            if getattr(player_stats, 'evo_points_remaining', 0) == 0:
                                confirming = True
                                confirm_selected = 1  # Default to NO
                    else:
                        if key_pressed == pygame.K_ESCAPE or key_pressed == pygame.K_z:
                            if esc_sound:
                                esc_sound.play()
                            running = False
                            if hasattr(player_stats, 'update_max_hp'):
                                player_stats.update_max_hp()
                        elif key_pressed == pygame.K_UP:
                            selected_row = (selected_row - 1) % num_rows
                            blink_timer = 0.0
                            blink_on = False  # Start with black
                            if menu_sound:
                                menu_sound.play()
                        elif key_pressed == pygame.K_DOWN:
                            selected_row = (selected_row + 1) % num_rows
                            blink_timer = 0.0
                            blink_on = False  # Start with black
                            if menu_sound:
                                menu_sound.play()
                        elif key_pressed == pygame.K_SPACE:
                            # Enter level up mode if evo points > 0
                            if spacebar_sound:
                                spacebar_sound.play()
                            if getattr(player_stats, 'evo_points_remaining', 0) > 0:
                                level_up_mode = True
                                # Save original evo points for revert
                                original_evo = {evo_attr: getattr(player_stats, evo_attr, 0) for _, evo_attr, _ in stat_rows}
                                original_evo_points_remaining = getattr(player_stats, 'evo_points_remaining', 0)
                                orig_hp = getattr(player_stats, 'evo_points_hp', 0)
                                orig_regen = getattr(player_stats, 'evo_points_regen', 0)
                                orig_stamina = getattr(player_stats, 'evo_points_stamina', 0)
                                orig_reserve = getattr(player_stats, 'evo_points_reserve', 0)
                                orig_strength = getattr(player_stats, 'evo_points_strength', 0)
                                orig_dexterity = getattr(player_stats, 'evo_points_dexterity', 0)
                                orig_special = getattr(player_stats, 'evo_points_special', 0)
                                orig_speed = getattr(player_stats, 'evo_points_speed', 0)

        # Draw transparent overlay
        overlay = pygame.Surface((menu_box_width, menu_box_height), pygame.SRCALPHA)
        overlay.fill((30, 30, 40, 180))  # Semi-transparent base (adjust alpha as needed)

                # Draw EXP bar
        exp_bar_width = int(menu_box_width * 0.4085)
        exp_bar_height = max(12, int(menu_box_height * 0.075))
        # Position: top right of stats menu, matching reference image
        exp_bar_x = int(menu_box_width * 0.46)
        exp_bar_y = int(menu_box_height * 0.157)

        # Get EXP values
        current_exp = getattr(player_stats, 'exp', 0)
        required_exp = getattr(player_stats, 'required_exp', 1)
        exp_ratio = min(1.0, current_exp / required_exp if required_exp > 0 else 0)
        filled_width = int(exp_bar_width * exp_ratio)

        # Draw EXP bar background (very dark blue, almost black)
        exp_bar_bg = (10, 18, 28)  # Very dark blue
        pygame.draw.rect(overlay, exp_bar_bg, (exp_bar_x, exp_bar_y, exp_bar_width, exp_bar_height), border_radius=6)
        # Draw filled EXP bar (EVOLUTION box blue)
        evolution_blue = (44, 142, 186)  # Sampled from the EVOLUTION box in the image
        pygame.draw.rect(overlay, evolution_blue, (exp_bar_x, exp_bar_y, filled_width, exp_bar_height), border_radius=6)



        # Draw PNG
        if stats_png:
            stats_w = stats_png.get_width()
            stats_h = stats_png.get_height()
            scale_w = menu_box_width
            scale_h = menu_box_height
            aspect = stats_w / stats_h if stats_h > 0 else 1
            if scale_w / aspect < scale_h:
                scale_h = int(scale_w / aspect)
            else:
                scale_w = int(scale_h * aspect)
            stats_surface = pygame.transform.smoothscale(stats_png, (scale_w, scale_h))
            # Set PNG fully opaque (alpha=255)
            temp_surface = pygame.Surface((scale_w, scale_h), pygame.SRCALPHA)
            temp_surface.blit(stats_surface, (0, 0))
            temp_surface.set_alpha(255)
            x = (menu_box_width - scale_w) // 2
            y = (menu_box_height - scale_h) // 2
            overlay.blit(temp_surface, (x, y))
        # Draw player stats
        # Use Pixellari font for stats
        font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
        # Font size scales with menu box height (e.g. 5% of height, min 18, max 64)
        font_size = max(18, min(64, int(menu_box_height * 0.05)))
        try:
            font = pygame.font.Font(font_path, font_size)
        except Exception:
            font = pygame.font.SysFont(None, font_size, bold=True)

        # Responsive column positions based on menu box dimensions
        col_margin = int(menu_box_width * 0.045)
        col_width_stat = int(menu_box_width * 0.17)
        col_width_evo = int(menu_box_width * 0.08)
        col_stat_x = col_margin
        col_evo_x = col_stat_x + col_width_stat
        col_val_x = col_evo_x + col_width_evo
        start_y = int(menu_box_height * 0.26)
        row_height = max(font.get_height() + 12, int(menu_box_height * 0.09))

        # Draw each stat row
        for i, (stat_name, evo_attr, stat_val) in enumerate(stat_rows):
            evo_val = getattr(player_stats, evo_attr, 0)
            # Blinking color for selected stat
            if i == selected_row:
                stat_color = (0,0,0) if not blink_on else (255,255,255)
                if level_up_mode:
                    evo_color = (0,0,0) if not blink_on else (255,255,255)
                else:
                    evo_color = (255,255,255)
            else:
                stat_color = (255,255,255)
                evo_color = (255,255,255)
            label_stat = font.render(stat_name.upper(), True, stat_color)
            label_evo = font.render(str(evo_val), True, evo_color)
            label_val = font.render(str(stat_val), True, (255,255,255))
            label_y = start_y + i * row_height
            overlay.blit(label_stat, (col_stat_x, label_y))
            overlay.blit(label_evo, (col_evo_x, label_y))
            overlay.blit(label_val, (col_val_x, label_y))

        # Define stats and evo points mapping
        stat_rows = [
            ("Health", "evo_points_hp", getattr(player_stats, "total_hp", 0)),
            ("Regen", "evo_points_regen", getattr(player_stats, "max_regen", 0)),
            ("Reserve", "evo_points_reserve", getattr(player_stats, "max_reserve", 0)),
            ("Stamina", "evo_points_stamina", getattr(player_stats, "max_stamina", 0)),
            ("Strength", "evo_points_strength", getattr(player_stats, "strength", 0)),
            ("Dexterity", "evo_points_dexterity", getattr(player_stats, "dexterity", 0)),
            ("Special", "evo_points_special", getattr(player_stats, "special", 0)),
            ("Speed", "evo_points_speed", getattr(player_stats, "speed", 0)),
        ]

        # EVO points color: red if >0, green if 0
        if getattr(player_stats, 'evo_points_remaining', 0) > 0:
            evo_text_color = (40, 220, 40)
        else:
            evo_text_color = (255, 255, 255)
        col_margin = int(menu_box_width * 0.045)
        col_width_stat = int(menu_box_width * 0.17)
        col_width_evo = int(menu_box_width * 0.08)
        col_stat_x = col_margin
        col_evo_x = col_stat_x + col_width_stat
        col_val_x = col_evo_x + col_width_evo
        start_y = int(menu_box_height * 0.26)
        row_height = max(font.get_height() + 12, int(menu_box_height * 0.09))

                # Draw EXP numbers (right side, current/required)
        exp_font_size = max(16, int(menu_box_height * 0.045))
        exp_text_color = (220, 220, 255)
        exp_text = f"{current_exp}/{required_exp}"
        # Dynamically reduce font size if text is too long for the menu
        max_exp_text_width = int(menu_box_width * 0.18)
        font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
        while True:
            try:
                exp_font = pygame.font.Font(font_path, exp_font_size)
            except Exception:
                exp_font = pygame.font.SysFont(None, exp_font_size, bold=True)
            exp_text_surface = exp_font.render(exp_text, True, exp_text_color)
            if exp_text_surface.get_width() <= max_exp_text_width or exp_font_size <= 12:
                break
            exp_font_size -= 2  # Reduce font size until it fits or hits minimum
        exp_text_y = exp_bar_y + (exp_bar_height - exp_text_surface.get_height()) // 2
        exp_text_x = exp_bar_x + exp_bar_width + int(menu_box_width * 0.013)
        overlay.blit(exp_text_surface, (exp_text_x, exp_text_y))

        # Draw available EVO points and Level near their labels in the image
        evo_font_size = max(27, int(menu_box_height * 0.082))
        try:
            evo_font = pygame.font.Font(font_path, evo_font_size)
        except Exception:
            evo_font = pygame.font.SysFont(None, evo_font_size, bold=True)
        evo_points_text = str(getattr(player_stats, 'evo_points_remaining', 0))
        level_text = str(getattr(player_stats, 'level', 1))
        # Position: EVO.PTS. value (right of icon/label)
        evo_pts_x = int(menu_box_width * 0.66)
        evo_pts_y = int(menu_box_height * 0.267)
        evo_points_surface = evo_font.render(evo_points_text, True, evo_text_color)
        overlay.blit(evo_points_surface, (evo_pts_x, evo_pts_y))
        # Position: LV. value (right of LV. label)
        # Draw confirmation prompt ON TOP of everything
        if confirming:
            # Draw a dark box background directly onto the overlay
            box_width = int(menu_box_width * 0.6)
            box_height = int(menu_box_height * 0.28)
            box_x = (menu_box_width - box_width) // 2
            box_y = int(menu_box_height * 0.13)
            box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            box_surface.fill((10, 10, 20, 230))  # Very dark, mostly opaque
            # Draw a rounded rectangle for the text box background
            pygame.draw.rect(box_surface, (10, 10, 20, 230), (0, 0, box_width, box_height), border_radius=18)  # Rounded corners
            pygame.draw.rect(box_surface, (60, 60, 80), (0, 0, box_width, box_height), border_radius=18)  # Border with rounded corners

            # Ensure the base of the text box is rounded
            box_surface.fill((0, 0, 0, 0))  # Clear the surface
            pygame.draw.rect(box_surface, (10, 10, 20, 255), (0, 0, box_width, box_height), border_radius=18)  # Fully opaque background

            # Define border color and thickness before drawing the border
            border_color = (205, 20, 20)  # Red color
            border_thickness = 3  # Thickness of the border
            pygame.draw.rect(box_surface, border_color, (0, 0, box_width, box_height), width=border_thickness, border_radius=18)

            # Draw prompt text
            prompt_font_size = max(24, int(menu_box_height * 0.07))
            try:
                prompt_font = pygame.font.Font(font_path, prompt_font_size)
            except Exception:
                prompt_font = pygame.font.SysFont(None, prompt_font_size, bold=True)
            prompt_text = "Are you sure?"
            prompt_surface = prompt_font.render(prompt_text, True, (255,255,255))
            prompt_x = (box_width - prompt_surface.get_width()) // 2
            prompt_y = int(box_height * 0.18)
            box_surface.blit(prompt_surface, (prompt_x, prompt_y))

            # Draw YES/NO options
            option_font_size = max(22, int(menu_box_height * 0.06))
            try:
                option_font = pygame.font.Font(font_path, option_font_size)
            except Exception:
                option_font = pygame.font.SysFont(None, option_font_size, bold=True)
            yes_color = (255,255,255) if confirm_selected == 0 else (120,120,120)
            no_color = (255,255,255) if confirm_selected == 1 else (120,120,120)
            yes_surface = option_font.render("YES", True, yes_color)
            no_surface = option_font.render("NO", True, no_color)
            options_y = int(box_height * 0.55)
            yes_x = (box_width // 2) - yes_surface.get_width() - 30
            no_x = (box_width // 2) + 30
            box_surface.blit(yes_surface, (yes_x, options_y))
            box_surface.blit(no_surface, (no_x, options_y))

            # Blit the box_surface onto the overlay
            overlay.blit(box_surface, (box_x, box_y))
        lv_x = evo_pts_x + int(menu_box_width * 0.225)
        lv_y = evo_pts_y
        level_surface = evo_font.render(level_text, True, evo_text_color)
        overlay.blit(level_surface, (lv_x, lv_y))

        # --- Stat Description Box ---
        stat_descriptions = {
            "Health": "Health represents an Anathei's ability to withstand damage. To increase their Health, an Anathei must learn how to create more dense and "
            "resilient body structures when regenerating. Upon spending evolution points in health, the resulting increase will be distributed to all body parts.",
            "Regen": "Regenerating is the distinctive feature of the Anatheis and is the base of all their abilities. By repetedly getting hurt and regenerating, "
            "an Anathei can learn faster and more efficient regeneration strategies. With enough time and practice, they can learn how to remodel their body according to their needs.",
            "Reserve": "Reserve represents the amount of mass an Anathei has stored for regeneration. To store the mass, an Anathei needs to eat more than what they expend in a day. "
            "The Anatheis have very high daily energy requirements, so managing their Reserve is no easy task in a world where nutritious food is so scarce.",
            "Stamina": "Stamina represents an Anathei's ability to sustain prolonged physical activity. It determines the the quality and quantity of attacks an Anathei can perform "
            "and how long they can run. To train it, an Anathei must learn to create more efficient and durable slow muscle fibers through regeneration.",
            "Strength": "Strength represents an Anathei's physical prowess and ability to utilize their body effectively to exert force. It affects the damage dealt with "
            "moves and weapons that rely on it. To increase it, an Anathei must learn to create more dense and contractile muscle fibers through regeneration.",
            "Dexterity": "Dexterity represents an Anathei's ability to perform precise movements, and their coordination. It affects the damage dealt by moves and "
            "weapons that rely on skill and finesse. To increase it, an Anathei must practice fine motor skills and improve their hand-eye coordination.",
            "Special": "Special represents an Anathei's mastery over the physical traits of their species. It affects the potency and effectiveness of moves and weapons"
            " that rely on them. To increase it, an Anathei must use their regeneration to enhance the organs and/or body structures associated with those traits.",
            "Speed": "Speed represents an Anathei's agility and quickness. In battle, it affects turn order and the effectiveness of their dodges. To increase it, an"
            " Anathei must learn to enhance their fast-twitch muscle fibers through repeated regeneration.",
        }
        desc_box_x = int(menu_box_width * 0.48)
        desc_box_y = int(menu_box_height * 0.527)
        desc_box_w = int(menu_box_width * 0.47)
        desc_box_h = int(menu_box_height * 0.34)
        desc_font_size = max(18, int(menu_box_height * 0.045))
        try:
            desc_font = pygame.font.Font(font_path, desc_font_size)
        except Exception:
            desc_font = pygame.font.SysFont(None, desc_font_size, bold=True)
        selected_stat_name = stat_rows[selected_row][0] if 0 <= selected_row < len(stat_rows) else ""
        desc_text = stat_descriptions.get(selected_stat_name, "")
        def render_wrapped_text(surface, text, font, color, rect, line_spacing=4):
            words = text.split(' ')
            lines = []
            line = ""
            for word in words:
                test_line = line + word + " "
                if font.size(test_line)[0] <= rect[2]:
                    line = test_line
                else:
                    lines.append(line)
                    line = word + " "
            if line:
                lines.append(line)
            y = rect[1]
            for l in lines:
                rendered = font.render(l.strip(), True, color)
                surface.blit(rendered, (rect[0], y))
                y += rendered.get_height() + line_spacing
        desc_rect = (desc_box_x + 12, desc_box_y + 12, desc_box_w - 24, desc_box_h - 24)
        desc_color = (255,255,255)
        render_wrapped_text(overlay, desc_text, desc_font, desc_color, desc_rect)

        # Blit overlay on top of game
        screen.blit(overlay, (menu_box_x, menu_box_y))
        pygame.display.flip()
        clock.tick(60)
    return
