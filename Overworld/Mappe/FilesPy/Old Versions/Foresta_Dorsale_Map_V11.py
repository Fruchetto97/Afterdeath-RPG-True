# --- Standard and third-party imports (all at top) ---
import sys
import os
import time
import random
import pygame
from io import BytesIO
try:
    from pytmx.util_pygame import load_pygame
except ImportError:
    load_pygame = None
from Overworld_Menu_V2 import PauseMenu, show_pause_menu
import random
import math

# --- Object interaction logic: run_object_script ---
def run_object_script(obj):
    obj_name = getattr(obj, 'name', None)
    norm_name = obj_name.strip().lower() if obj_name else None
    prompt_scripts = getattr(map_config.Config_Data, 'PROMPT_SCRIPTS', {})
    print(f"[DEBUG] run_object_script: norm_name='{norm_name}', PROMPT_SCRIPTS keys={list(prompt_scripts.keys())}")
    if norm_name in prompt_scripts:
        script = prompt_scripts[norm_name]
        print(f"[DEBUG] Found script for '{norm_name}': {repr(script)} (type: {type(script)})")
        if isinstance(script, dict):
            msg = script.get('message', '')
            duration = script.get('duration', 3500)
            message_display.show_message(msg, duration)
            print(f"[DEBUG] Showing message from dict: {msg} (duration: {duration})")
            return True
    print(f"[DEBUG] run_object_script called for object: {obj_name if obj_name else 'Unknown'}")
    return False

# --- Stub for enemy_touches_player (needed for main loop) ---
def enemy_touches_player(player, object_group):
    # This should contain logic to check for collisions between player and enemies
    # For now, just print debug info
    pass

# --- PlayerStats class (needed for player and menu) ---
class PlayerStats:
    def __init__(self, name, gif_path, sprite_path, max_stamina, max_regen, max_reserve, max_head_hp, max_body_hp,
                 max_left_arm_hp, max_right_arm_hp, max_left_leg_hp, max_right_leg_hp, has_extra_limbs, max_extral_limbs_hp):
        self.name = name
        self.gif_path = gif_path
        self.sprite_path = sprite_path
        self.max_stamina = max_stamina
        self.stamina = max_stamina
        self.max_regen = max_regen
        self.regen = max_regen
        self.max_reserve = max_reserve
        self.reserve = max_reserve
        self.max_head_hp = max_head_hp
        self.max_left_arm_hp = max_left_arm_hp
        self.max_right_arm_hp = max_right_arm_hp
        self.max_left_leg_hp = max_left_leg_hp  
        self.max_right_leg_hp = max_right_leg_hp    
        self.has_extra_limbs = has_extra_limbs
        self.max_extral_limbs_hp = max_extral_limbs_hp if has_extra_limbs else 0
        # Dynamically set max_hp as the sum of all body parts HP, treating body as a part
        self.max_body_hp = max_body_hp # Default body HP, can be made configurable
        self.max_hp = (
            self.max_body_hp +
            self.max_head_hp +
            self.max_left_arm_hp +
            self.max_right_arm_hp +
            self.max_left_leg_hp +
            self.max_right_leg_hp +
            (self.max_extral_limbs_hp if self.has_extra_limbs else 0)
        )

        # Current HP for each part
        self.body_hp = self.max_body_hp
        self.head_hp = self.max_head_hp
        self.left_arm_hp = self.max_left_arm_hp
        self.right_arm_hp = self.max_right_arm_hp
        self.left_leg_hp = self.max_left_leg_hp
        self.right_leg_hp = self.max_right_leg_hp
        self.extral_limbs_hp = self.max_extral_limbs_hp if has_extra_limbs else 0

        # Current HP is always calculated as the sum of all current part HPs, including body
        def calc_hp(self):
            total = (
                self.body_hp +
                self.head_hp +
                self.left_arm_hp +
                self.right_arm_hp +
                self.left_leg_hp +
                self.right_leg_hp
            )
            if self.has_extra_limbs:
                total += self.extral_limbs_hp
            return min(total, self.max_hp)
        self.calc_hp = calc_hp.__get__(self)
        self.hp = self.calc_hp()



    def take_damage(self, amount, part=None):
        import random
        # If part is 'legs', apply damage to a random leg
        if part == 'legs':
            leg = random.choice(['left_leg', 'right_leg'])
            if leg == 'left_leg':
                self.left_leg_hp = max(0, self.left_leg_hp - amount)
            else:
                self.right_leg_hp = max(0, self.right_leg_hp - amount)
            # Recalculate total HP
            self.hp = self.calc_hp()
        else:
            # Default: apply damage to total HP
            self.hp = max(0, self.hp - amount)
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
    def use_stamina(self, amount):
        self.stamina = max(0, self.stamina - amount)
    def regen_stamina(self, amount):
        self.stamina = min(self.max_stamina, self.stamina + amount)
    def use_reserve(self, amount):
        self.reserve = max(0, self.reserve - amount)
    def regen_reserve(self, amount):
        self.reserve = min(self.max_reserve, self.reserve + amount)
    def __repr__(self):
        return f"PlayerStats(name={self.name}, hp={self.hp}/{self.max_hp}, stamina={self.stamina}/{self.max_stamina}, regen={self.regen}/{self.max_regen}, reserve={self.reserve}/{self.max_reserve})"

def load_character_frames(image_path):
    """
    Loads a 4x4 spritesheet and returns a dict of frames for directions.
    Args:
        image_path (str): Path to the PNG spritesheet.
    Returns:
        dict: {direction: [frame0, frame1, frame2, frame3]}
    """
    character_spritesheet = pygame.image.load(image_path).convert_alpha()
    sprite_width = character_spritesheet.get_width() // 4
    sprite_height = character_spritesheet.get_height() // 4
    frames = {}
    start_frames = {}
    directions = ['down', 'right', 'up', 'left']
    for row, direction in enumerate(directions):
        frames[direction] = []
        for col in range(4):
            frame_rect = pygame.Rect(col * sprite_width, row * sprite_height, sprite_width, sprite_height)
            frame = character_spritesheet.subsurface(frame_rect)
            # For 'down' direction, shift the frame 13px higher on a new surface
            if direction == 'down':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, -13))
                frames[direction].append(shifted_surface)
            # For 'right' direction, shift the frame 7px up
            elif direction == 'right':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, -7))
                frames[direction].append(shifted_surface)
            # For 'up' direction, shift the frame 1px left and 3px down
            elif direction == 'up':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (-1, 3))
                frames[direction].append(shifted_surface)
            # For 'left' direction, shift the frame 9px down
            elif direction == 'left':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, 9))
                frames[direction].append(shifted_surface)
            else:
                frames[direction].append(frame)
        # Animation should start from frame 1 (second frame) when moving
        start_frames[direction] = 1
    return {'frames': frames, 'start_frames': start_frames}

def is_player_on_bone_grass(player, tmx_data):
    """
    Return (on_bone_grass, is_moving, is_running):
    - on_bone_grass: True if the player's feet are inside a tile of class 'Bone_Grass'.
    - is_moving: True if the player is moving.
    - is_running: True if the player is running (sprinting).
    """
    # Circle: center = player feet, radius = 0.4 * tilewidth
    player_center = (player.rect.centerx, player.rect.centery + tmx_data.tileheight)
    radius = tmx_data.tilewidth / 2


    # Check all Bone_Grass tiles: if their center is within the circle
    on_bone_grass = False
    for layer in tmx_data.layers:
        if hasattr(layer, 'data'):
            for y, row in enumerate(layer.data):
                for x, tile in enumerate(row):
                    if tile:
                        props = tmx_data.get_tile_properties_by_gid(tile)
                        if props and props.get('type') == 'Bone_grass':
                            tile_center = (
                                x * tmx_data.tilewidth + tmx_data.tilewidth // 2,
                                y * tmx_data.tileheight + tmx_data.tileheight // 2
                            )
                            dx = player_center[0] - tile_center[0]
                            dy = player_center[1] - tile_center[1]
                            if (dx*dx + dy*dy) <= (radius*radius):
                                on_bone_grass = True
                                break
                if on_bone_grass:
                    break
        if on_bone_grass:
            break


    # Determine movement and running state
    is_moving = getattr(player, 'is_moving', False)
    # Sprinting: shift pressed and not locked and stamina > 0
    is_running = False
    return on_bone_grass, is_moving, is_running


# --- Bone grass sound rate limiting ---
last_bone_grass_sound_time = 0
from pytmx.util_pygame import load_pygame

# --- Initialize mixer before loading any sounds ---
try:
    pygame.mixer.init()
    print("Pygame mixer initialized.")
except Exception as e:
    print(f"[ERROR] Could not initialize pygame mixer: {e}")

# --- Sound Effect for Bone Grass Damage ---
bone_grass_sound = None
bone_grass_sound_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Sound Effects\knife-stab-pull-7005.mp3"
try:
    bone_grass_sound = pygame.mixer.Sound(bone_grass_sound_path)
    bone_grass_sound.set_volume(0.1)
    print("Loaded bone grass damage sound.")
except Exception as e:
    print(f"Could not load bone grass sound: {e}")

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class NPC(pygame.sprite.Sprite):
    def __init__(self, name, image_path, pos, speed=2, active=True, sight_range=30, groups=None):
        # Always add to object_group for consistency
        import pygame
        if groups is None:
            from __main__ import object_group  # fallback if not passed
            groups = object_group
        super().__init__(groups)
        self.name = name
        self.speed = speed  # Store base speed, apply dt scaling in update
        self.active = active
        self.sight_range = sight_range

        # For axis-priority memory (to avoid erratic diagonal movement)
        self.axis_priority = None  # 'x' or 'y'
        self.axis_steps_left = 0
        self.last_axis_change_time = 0  # ms since pygame.init()
        self.last_random_move_time = 0  # ms since pygame.init()

        # For smooth random movement
        self.random_move_dir = None
        self.random_move_steps_left = 0
        self.random_move_dx = 0
        self.random_move_dy = 0

        # Use the same animation logic as Player
        frames_data = load_character_frames(image_path)
        self.frames = frames_data['frames']
        self.start_frames = frames_data['start_frames']

        # Animation properties
        self.direction = 'up'
        self.frame_index = 0
        self.animation_speed = 0.2
        self.animation_timer = 0
        self.pingpong_forward = True

        # Use Vector2 for position (like Player)
        self.pos = pygame.math.Vector2(pos)
        self.image = self.frames[self.direction][self.frame_index]
        self.rect = self.image.get_rect(center=self.pos)
        self.depth_y = self.rect.bottom
        print(f"[DEBUG] Created NPC '{self.name}' at {self.rect.topleft} depth_y={self.depth_y}")
        print(f"[DEBUG] NPC groups: {self.groups()} (object_group id: {id(groups)})")

    def update(self, player, collision_tiles, tmx_data):
        # --- Enemy AI: Move towards player if within sight_range, avoid obstacles ---
        dx = player.pos.x - self.pos.x
        dy = player.pos.y - self.pos.y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        moved = False
        tile_size = tmx_data.tilewidth  # Assume square tiles
        min_steps = 10  # commit to at least 2 tiles before switching axis
        now = pygame.time.get_ticks()  # ms since pygame.init()
        cooldown_ms = 500  # 0.5 seconds
        if dist <= self.sight_range:
            # Only allow axis switch if axis_steps_left == 0 and cooldown passed
            can_change_axis = (self.axis_priority is None or self.axis_steps_left == 0) and (now - self.last_axis_change_time >= cooldown_ms)
            if can_change_axis:
                if abs(dx) > abs(dy):
                    self.axis_priority = 'x'
                elif abs(dy) > abs(dx):
                    self.axis_priority = 'y'
                else:
                    if self.axis_priority is None:
                        self.axis_priority = 'x'  # default
                self.axis_steps_left = min_steps
                self.last_axis_change_time = now
            # Build movement order based on axis_priority
            directions = []
            # dt scaling for framerate independence
            import inspect
            frame = inspect.currentframe()
            dt = frame.f_back.f_locals.get('dt', 16)  # fallback to 16ms if not found
            speed_dt = self.speed * (dt / 1000.0)
            if self.axis_priority == 'x':
                if dx > 0:
                    directions.append(('right', (speed_dt, 0)))
                elif dx < 0:
                    directions.append(('left', (-speed_dt, 0)))
                if dy != 0:
                    if dy > 0:
                        directions.append(('down', (0, speed_dt)))
                    else:
                        directions.append(('up', (0, -speed_dt)))
            else:  # 'y'
                if dy > 0:
                    directions.append(('down', (0, speed_dt)))
                elif dy < 0:
                    directions.append(('up', (0, -speed_dt)))
                if dx != 0:
                    if dx > 0:
                        directions.append(('right', (speed_dt, 0)))
                    else:
                        directions.append(('left', (-speed_dt, 0)))
            # Try each direction, stop at first non-colliding move
            blocked = True
            for dir_name, (mx, my) in directions:
                new_pos = self.pos + pygame.math.Vector2(mx, my)
                current_image = self.frames[dir_name][self.frame_index]
                hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
                    new_pos.x - current_image.get_width()//2,
                    new_pos.y - current_image.get_height()//2,
                    current_image, tmx_data)
                if not check_collision(hitbox_x, hitbox_y, hitbox_width, hitbox_height, collision_tiles, tmx_data):
                    self.pos = new_pos
                    self.direction = dir_name
                    moved = True
                    self.axis_steps_left = max(0, self.axis_steps_left - 1)
                    blocked = False
                    break
            if blocked:
                # Only decrement axis_steps_left if > 0, never below 0
                if self.axis_steps_left > 0:
                    self.axis_steps_left -= 1
                if self.axis_steps_left < 0:
                    self.axis_steps_left = 0

            # Cancel random movement if chasing player
            self.random_move_steps_left = 0
            self.random_move_dir = None
            self.random_move_dx = 0
            self.random_move_dy = 0
        else:
            self.axis_priority = None
            self.axis_steps_left = 0
            # --- Smooth random movement if player not in sight ---
            import inspect
            frame = inspect.currentframe()
            dt = frame.f_back.f_locals.get('dt', 16)
            speed_dt = self.speed * (dt / 1000.0)
            # If not currently moving randomly, pick a direction every 1.5s
            if self.random_move_steps_left == 0 and now - self.last_random_move_time >= 1500:
                import random
                directions_list = [
                    ('up', (0, -1)),
                    ('down', (0, 1)),
                    ('left', (-1, 0)),
                    ('right', (1, 0))
                ]
                dir_name, (dx_step, dy_step) = random.choice(directions_list)
                self.random_move_dir = dir_name
                # Move for a fixed number of frames (e.g. 36 frames = 2 steps × 3 tiles × 6 frames per tile)
                self.random_move_steps_left = 36
                self.random_move_dx = dx_step
                self.random_move_dy = dy_step
                self.last_random_move_time = now
            # If currently moving randomly, move a small amount each frame
            if self.random_move_steps_left > 0 and self.random_move_dir:
                mx = self.random_move_dx * speed_dt
                my = self.random_move_dy * speed_dt
                new_pos = self.pos + pygame.math.Vector2(mx, my)
                current_image = self.frames[self.random_move_dir][self.frame_index]
                hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
                    new_pos.x - current_image.get_width()//2,
                    new_pos.y - current_image.get_height()//2,
                    current_image, tmx_data)
                if not check_collision(hitbox_x, hitbox_y, hitbox_width, hitbox_height, collision_tiles, tmx_data):
                    self.pos = new_pos
                    self.direction = self.random_move_dir
                    moved = True
                self.random_move_steps_left -= 1
                if self.random_move_steps_left <= 0:
                    self.random_move_dir = None
                    self.random_move_dx = 0
                    self.random_move_dy = 0
        # Animation logic (idle if not moved)
        # --- Framerate-independent animation, 30% slower (matches player) ---
        dt = 16  # fallback default
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back and 'dt' in frame.f_back.f_locals:
            dt = frame.f_back.f_locals['dt']
        dt_seconds = dt / 1000.0
        animation_speed_dt = self.animation_speed * dt_seconds * 60 * 0.7  # 30% slower
        if moved:
            if self.frame_index == 0:
                self.frame_index = self.start_frames[self.direction]
                self.pingpong_forward = True
            self.animation_timer += animation_speed_dt
            if self.animation_timer >= 1.0:
                if self.pingpong_forward:
                    self.frame_index += 1
                    if self.frame_index == 4:
                        self.frame_index = 2
                        self.pingpong_forward = False
                else:
                    self.frame_index -= 1
                    if self.frame_index == 0:
                        self.frame_index = 2
                        self.pingpong_forward = True
                self.animation_timer = 0
        else:
            self.frame_index = 0
            self.animation_timer = 0
            self.pingpong_forward = True
        self.image = self.frames[self.direction][self.frame_index]
        self.rect.center = self.pos
        self.depth_y = self.rect.bottom

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, image_path):
        super().__init__(groups)
        frames_data = load_character_frames(image_path)
        self.frames = frames_data['frames']
        self.start_frames = frames_data['start_frames']
        self.direction = 'down'
        self.frame_index = 0
        self.animation_speed = 0.2
        self.animation_timer = 0
        self.is_moving = False
        self.pingpong_forward = True
        self.image = self.frames[self.direction][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        self.speed = 5
        self.pos = pygame.math.Vector2(pos)
        self.stamina_regen_timer = 0.0
        self.stamina_drain_timer = 0.0
        self.sprint_locked = False

    def update(self, keys, collision_tiles, tmx_data, dt=16):
        self.is_moving = False
        new_pos = self.pos.copy()
        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        # --- Leg injury sprint lock ---
        legs_hp = player_stats.left_leg_hp + player_stats.right_leg_hp
        legs_max_hp = player_stats.max_left_leg_hp + player_stats.max_right_leg_hp
        legs_usable = legs_hp >= (legs_max_hp / 3)
        # If legs are too injured, lock sprint and show message
        if not legs_usable:
            self.sprint_locked = True
            # Show message if shift is pressed and message not already visible
            if shift_pressed and not message_display.is_visible:
                message_display.show_message(f"{player_stats.name}'s legs are too injured to run", 2500)
        can_sprint = not self.sprint_locked and player_stats.stamina > 0
        sprinting = shift_pressed and can_sprint
        move_speed = (self.speed * 1.5 if sprinting else self.speed) * (dt / 1000.0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_pos.x -= move_speed
            self.direction = 'left'
            self.is_moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_pos.x += move_speed
            self.direction = 'right'
            self.is_moving = True
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            new_pos.y -= move_speed
            self.direction = 'up'
            self.is_moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_pos.y += move_speed
            self.direction = 'down'
            self.is_moving = True
        if sprinting and self.is_moving:
            self.stamina_regen_timer = 0.0
            self.stamina_drain_timer += dt / 1000.0
            if self.stamina_drain_timer >= 0.001:
                player_stats.stamina = max(0, player_stats.stamina - 1)
                self.stamina_drain_timer -= 0.5
            if player_stats.stamina <= 0:
                self.sprint_locked = True
        else:
            self.stamina_drain_timer = 0.0
            if player_stats.stamina < player_stats.max_stamina:
                self.stamina_regen_timer += dt / 1000.0
                if self.stamina_regen_timer >= 1.0:
                    player_stats.stamina = min(player_stats.max_stamina, player_stats.stamina + 1)
                    self.stamina_regen_timer -= 1.0
            if self.sprint_locked and player_stats.stamina >= player_stats.max_stamina / 2 and legs_usable:
                self.sprint_locked = False
        if self.is_moving:
            current_image = self.frames[self.direction][self.frame_index]
            hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
                new_pos.x - current_image.get_width()//2,
                new_pos.y - current_image.get_height()//2,
                current_image, tmx_data)
            if not check_collision(hitbox_x, hitbox_y, hitbox_width, hitbox_height, collision_tiles, tmx_data):
                self.pos = new_pos
            else:
                self.is_moving = False
        # Animation logic for 4 frames per direction
        # --- Framerate-independent animation ---
        dt_seconds = dt / 1000.0
        animation_speed_dt = self.animation_speed * dt_seconds * 60 * 0.7  # 30% slower
        if self.is_moving:
            if self.frame_index == 0:
                self.frame_index = self.start_frames[self.direction]
                self.pingpong_forward = True
            self.animation_timer += animation_speed_dt
            if self.animation_timer >= 1.0:
                if self.pingpong_forward:
                    self.frame_index += 1
                    if self.frame_index == 4:
                        self.frame_index = 2
                        self.pingpong_forward = False
                else:
                    self.frame_index -= 1
                    if self.frame_index == 0:
                        self.frame_index = 2
                        self.pingpong_forward = True
                self.animation_timer = 0
        else:
            self.frame_index = 0
            self.animation_timer = 0
            self.pingpong_forward = True
        self.image = self.frames[self.direction][self.frame_index]
        self.rect.center = self.pos

def draw_hp_bar(screen, player, player_HP, player_max_HP):
    # HP bar settings
    bar_x, bar_y = 20, 8  # 12px above stamina bar
    bar_width, bar_height = 600, int(24 * 0.75)  # 3x stamina bar width
    # Background
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
    # Foreground (current HP)
    hp_ratio = player_HP / player_max_HP
    fg_width = int(bar_width * hp_ratio)
    pygame.draw.rect(screen, (200, 0, 0), (bar_x, bar_y, fg_width, bar_height))
    # Black border
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)

def draw_stamina_bar(screen, player):
    # Bar settings
    bar_x, bar_y = 20, 25
    bar_width, bar_height = 200, int(24 * 0.75)  # 18px height
    # Background
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
    # Foreground (current stamina)
    # Use player_stats for stamina values
    stamina = player_stats.stamina
    max_stamina = player_stats.max_stamina
    stamina_ratio = stamina / max_stamina if max_stamina > 0 else 0
    fg_width = int(bar_width * stamina_ratio)
    pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, fg_width, bar_height))
    # Black border
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)

def is_player_facing_object_center(player, tmx_data):
    """Return the object (no image) the player is inside and facing its center, or None if not found."""
    # Use the player's hitbox rect for interaction, not the sprite rect
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    player_hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    for obj in tmx_data.objects:
        if not hasattr(obj, 'image') or obj.image is None:
            obj_rect = pygame.Rect(obj.x, obj.y, getattr(obj, 'width', 0), getattr(obj, 'height', 0))
            if player_hitbox_rect.colliderect(obj_rect):
                # Get centers
                player_center = pygame.math.Vector2(player_hitbox_rect.center)
                object_center = pygame.math.Vector2(obj_rect.center)
                direction = getattr(player, 'direction', None)
                to_object = object_center - player_center
                # Allow some tolerance for being "close enough"
                tolerance = 40
                if to_object.length() > max(player_hitbox_rect.width, player_hitbox_rect.height) + tolerance:
                    continue
                # Facing direction check
                if direction == 'up' and to_object.y < -abs(to_object.x):
                    return obj
                if direction == 'down' and to_object.y > abs(to_object.x):
                    return obj
                if direction == 'left' and to_object.x < -abs(to_object.y):
                    return obj
                if direction == 'right' and to_object.x > abs(to_object.y):
                    return obj
    return None

# --- Utility: Handle SPACEBAR interaction for facing object center ---
def handle_spacebar_facing_check(player, tmx_data):
    """Call this when SPACEBAR is pressed. If player is facing object center, print 'OK'."""
    obj = is_player_facing_object_center(player, tmx_data)
    if obj:
        handled = run_object_script(obj)
        if not handled:
            # Display a message on the screen when interacting with an object
            obj_name = obj.name if hasattr(obj, 'name') else 'Unnamed Object'
            message_display.show_message(f"Interacted with object: {obj_name}", 2500)
            print(f"Interacted with object: {obj_name}")

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.zoom_factor = 3  # 2x zoom like in V02

    def apply(self, entity):
        # Apply camera offset and zoom
        x = (entity.rect.x + self.camera.x) * self.zoom_factor
        y = (entity.rect.y + self.camera.y) * self.zoom_factor
        return pygame.Rect(x, y, entity.rect.width * self.zoom_factor, entity.rect.height * self.zoom_factor)

    def apply_rect(self, rect):
        # Apply camera offset and zoom to a rect
        x = (rect.x + self.camera.x) * self.zoom_factor
        y = (rect.y + self.camera.y) * self.zoom_factor
        return pygame.Rect(x, y, rect.width * self.zoom_factor, rect.height * self.zoom_factor)

    def update(self, target):
        # Center camera on target accounting for zoom
        x = target.x - (self.width / self.zoom_factor) // 2
        y = target.y - (self.height / self.zoom_factor) // 2
        
        # Limit scrolling to map size (accounting for zoom)
        x = max(0, min(x, self.map_width - (self.width / self.zoom_factor)))
        y = max(0, min(y, self.map_height - (self.height / self.zoom_factor)))
        
        self.camera = pygame.Rect(-x, -y, self.width, self.height)

    def set_map_size(self, map_width, map_height):
        self.map_width = map_width
        self.map_height = map_height

class MessageDisplay:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
        try:
            self.font = pygame.font.Font(font_path, 36)
        except Exception as e:
            print(f"[MessageDisplay] Could not load Pixellari.ttf: {e}")
            self.font = pygame.font.Font(None, 36)
            print("Desired Font not found, using default font")

        self.message = ""
        self.display_time = 0
        self.max_display_time = 3000  # 3 seconds in milliseconds
        self.is_visible = False
        
        # Message box properties
        self.box_height = 40  # 50% less vertically long
        self.box_y = 40  # 40 pixels from top to avoid health bar
        self.padding = 15
        
    def show_message(self, text, duration=3000):
        """Show a message for the specified duration (in milliseconds)"""
        self.message = text
        self.display_time = 0
        self.max_display_time = duration
        self.is_visible = True
        
    def update(self, dt):
        """Update the message display timer"""
        if self.is_visible:
            self.display_time += dt
            if self.display_time >= self.max_display_time:
                self.is_visible = False
                
    def draw(self, screen):
        """Draw the message box and text with a desaturated purple box and outline"""
        if self.is_visible and self.message:
            # Create semi-transparent desaturated purple surface for the message box
            text_surface = self.font.render(self.message, True, (255, 255, 255))  # White text
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()

            # Calculate box dimensions
            box_width = text_width + (self.padding * 2)
            box_x = (self.screen_width - box_width) // 2  # Center horizontally

            # Desaturated purple for outline only
            outline_color = (110, 80, 130)

            # Create the semi-transparent black box
            box_surface = pygame.Surface((box_width, self.box_height))
            box_surface.set_alpha(180)  # Semi-transparent (0=fully transparent, 255=opaque)
            box_surface.fill((0, 0, 0))

            # Draw the box
            screen.blit(box_surface, (box_x, self.box_y))

            # Draw the desaturated purple outline (3px thick)
            outline_rect = pygame.Rect(box_x, self.box_y, box_width, self.box_height)
            for i in range(3):
                pygame.draw.rect(screen, outline_color, outline_rect.inflate(i*2, i*2), 1)

            # Draw the text centered in the box (horizontally and vertically)
            text_x = box_x + (box_width - text_width) // 2
            text_y = self.box_y + (self.box_height - text_height) // 2 + 3  # Move text 6px lower
            screen.blit(text_surface, (text_x, text_y))

# Collision detection functions
def check_collision(x, y, width, height, collision_tiles, tmx_data):
    """Check if a rectangle collides with any collision tiles"""
    # Convert pixel coordinates to tile coordinates
    left_tile = int(x // tmx_data.tilewidth)
    right_tile = int((x + width - 1) // tmx_data.tilewidth)
    top_tile = int(y // tmx_data.tileheight)
    bottom_tile = int((y + height - 1) // tmx_data.tileheight)
    
    # Check all tiles that the character would overlap
    for tile_x in range(left_tile, right_tile + 1):
        for tile_y in range(top_tile, bottom_tile + 1):
            if (tile_x, tile_y) in collision_tiles:
                return True
    return False

def get_character_hitbox(char_x, char_y, char_image, tmx_data):
    """Calculate the character's 1x1 tile hitbox centered in the lower half"""
    # Character sprite dimensions
    sprite_width = char_image.get_width()
    sprite_height = char_image.get_height()
    
    # Hitbox dimensions (smaller than 1 tile, e.g. 70% of tile size)
    hitbox_width = int(tmx_data.tilewidth * 0.7) + 2 # decrease width by 1px
    hitbox_height = int(tmx_data.tileheight * 0.3) + 4  # increase height by 2px

    # Center the hitbox horizontally within the sprite
    hitbox_x = char_x + (sprite_width - hitbox_width) // 2

    # Position hitbox in the lower half of the sprite
    # Start at 3/4 down the sprite height, move 2px up
    hitbox_y = char_y + (sprite_height * 3 // 4) - (hitbox_height // 2) - 2

    return hitbox_x, hitbox_y, hitbox_width, hitbox_height


screen_width = 1280
screen_height = 720

pygame.init()


# --- Initialize PlayerStats and Pause Menu ---
player_stats = PlayerStats(
    name="Selkio Guerriero",
    gif_path=r"C:\Users\franc\Desktop\Afterdeath_RPG\Enemies_GIFs\Selkio_NPC_2_GIF.gif",
    sprite_path=r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Selkio_32p.png",
    max_stamina=20,
    max_regen=20,
    max_reserve=100,
    max_head_hp=30,
    max_left_arm_hp=15,
    max_right_arm_hp=15,
    max_left_leg_hp=20,
    max_right_leg_hp=20,
    max_body_hp=100,
    has_extra_limbs=False,
    max_extral_limbs_hp=0
)
pause_menu = PauseMenu(screen_width, screen_height, player_stats)
game_paused = False

# --- Music System ---

import pygame.mixer
pygame.mixer.init()
# --- Music Volume Control ---
music_volume = 0.7  # Default music volume (0.0 to 1.0)
def set_music_volume(vol):
    global music_volume
    music_volume = max(0.0, min(1.0, vol))
    pygame.mixer.music.set_volume(music_volume)
    return music_volume

try:
    pygame.mixer.music.load(r"C:\Users\franc\Desktop\Afterdeath_RPG\Musics\Boney Rattle.MP3")
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play(-1)  # Loop forever
    print("Music started: Battle-Walzer.MP3")
except Exception as e:
    print(f"Music could not be loaded: {e}")


screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("TMX Map with Camera")
clock = pygame.time.Clock()

pause_menu.reload_frame_png()

# --- Precompute vignette for ambient occlusion ---
def create_vignette(width, height, strength=120, power=1.7):
    import math
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    cx, cy = width // 2, height // 2
    max_radius = math.hypot(cx, cy)
    # Always use config values for strength and power
    strength = getattr(map_config.Config_Data, 'VIGNETTE_STRENGTH', 180)
    power = getattr(map_config.Config_Data, 'VIGNETTE_POWER', 1.7)
    for y in range(height):
        for x in range(width):
            dx = x - cx
            dy = y - cy
            dist = math.hypot(dx, dy)
            alpha = int(strength * (dist / max_radius) ** power)
            if alpha > 0:
                vignette.set_at((x, y), (0, 0, 0, min(alpha, strength)))
    return vignette

# --- Import map config ---
import foresta_dorsale_sud_config as map_config

# --- Vignette from config ---
if getattr(map_config.Config_Data, 'HAS_VIGNETTE', False):
    vignette_surface = create_vignette(screen_width, screen_height)
else:
    vignette_surface = None

# --- TMX path from config ---
tmx_data = load_pygame(map_config.Config_Data.TMX_PATH)

tile_group = pygame.sprite.Group()  # Renamed for clarity
object_group = pygame.sprite.Group()  # Separate group for objects
player_group = pygame.sprite.Group()

# Calculate map dimensions
map_width = tmx_data.width * tmx_data.tilewidth
map_height = tmx_data.height * tmx_data.tileheight

# Create camera
camera = Camera(screen_width, screen_height)
camera.set_map_size(map_width, map_height)

# Find spawn point from map objects
def find_spawn_point(tmx_data, selected_spawnpoint="Spawnpoint_2"):
    """Find the spawn point from objects with 'spawnpoint' in their name"""
    
    # First pass: collect all spawn points
    spawn_points = {}
    object_count = 0
    
    for obj in tmx_data.objects:
        object_count += 1
        
        # Check if object name contains 'spawnpoint' 
        if hasattr(obj, 'name') and obj.name and 'spawnpoint' in obj.name.lower():
            spawn_points[obj.name] = (obj.x, obj.y)
            print(f"  -> Found spawn point '{obj.name}' at ({obj.x}, {obj.y})")
    
    print(f"Checked {object_count} total objects")
    print(f"Found {len(spawn_points)} spawn points: {list(spawn_points.keys())}")
    
    # Try to find the selected spawn point
    if selected_spawnpoint in spawn_points:
        print(f"Using selected spawn point '{selected_spawnpoint}' at {spawn_points[selected_spawnpoint]}")
        return spawn_points[selected_spawnpoint]
    elif spawn_points:
        # If selected spawn point not found, use the first available one
        first_spawn = list(spawn_points.keys())[0]
        print(f"Selected spawn point '{selected_spawnpoint}' not found, using '{first_spawn}' at {spawn_points[first_spawn]}")
        return spawn_points[first_spawn]
    else:
        # If no spawn points found, use default position
        print("No spawn points found, using default position (600, 400)")
        return (600, 400)

# Configuration: Select which spawn point to use
selected_spawnpoint = "Spawnpoint_2"  # Change this to use different spawn points

# Create player at dynamic spawn point
spawn_position = find_spawn_point(tmx_data, selected_spawnpoint)
player = Player(spawn_position, player_group, player_stats.sprite_path)
player.speed *= 24  

# --- Example Enemy ---
# You can change the image path and position as needed
enemy_example = NPC(
    name="Selkio_Nemico",
    image_path=r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Selkio_32p.png",
    pos=(spawn_position[0] + 5, spawn_position[1] - 500),  # Example: 5px to the right of player
    speed=3 * 35,  #
    active=True,
    sight_range=200,
    groups=object_group
)

# Create message display system
message_display = MessageDisplay(screen_width, screen_height)

# --- Event System ---
class GameEvent:
    def __init__(self, name, x, y, width, height):
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        self.triggered = False  # Prevent retriggering if needed

# Find all event objects
event_list = []
for obj in tmx_data.objects:
    if hasattr(obj, 'name') and obj.name and 'event' in obj.name.lower():
        event_rect = pygame.Rect(obj.x, obj.y, getattr(obj, 'width', 0), getattr(obj, 'height', 0))
        event_list.append(GameEvent(obj.name, obj.x, obj.y, getattr(obj, 'width', 0), getattr(obj, 'height', 0)))
        print(f"Event found: {obj.name} at ({obj.x}, {obj.y}, {getattr(obj, 'width', 0)}, {getattr(obj, 'height', 0)})")


# Collision detection setup
collision_tiles = set()  # Set to store collision tile positions

for layer in tmx_data.layers:
    if hasattr(layer, 'data'):  # Tile layers
        # Add collision tiles from ALL layers (both visible and invisible)
        # Check for collision layers by name OR if layer is invisible
        if 'collision' in layer.name.lower() or not layer.visible:
            for x, y, gid in layer:
                if gid:  # If there's a tile here
                    collision_tiles.add((x, y))
            if not layer.visible:
                print(f"Invisible collision layer '{layer.name}' found with {len([1 for x, y, gid in layer if gid])} collision tiles")
            else:
                print(f"Named collision layer '{layer.name}' found with {len([1 for x, y, gid in layer if gid])} collision tiles")
        
        # Only render visible layers
        if layer.visible:
            for x, y, surface in layer.tiles():
                if surface:  # Only create tiles for non-empty tiles
                    pos = (x * tmx_data.tilewidth, y * tmx_data.tileheight)
                    Tile(pos=pos, surf=surface, groups=tile_group)
            print(f"Visible layer '{layer.name}' rendered")

print(f"Total collision tiles loaded: {len(collision_tiles)}")

print(f"Map info: {tmx_data.width}x{tmx_data.height} tiles, tile size: {tmx_data.tilewidth}x{tmx_data.tileheight}")
print(f"Map pixel size: {map_width}x{map_height}")

for obj in tmx_data.objects:
    if obj.image:
        # Ensure object images are loaded with convert_alpha for transparency
        if hasattr(obj.image, 'convert_alpha'):
            surf = obj.image.convert_alpha()
        else:
            surf = obj.image
        pos = (obj.x, obj.y)
        obj_tile = Tile(pos=pos, surf=surf, groups=object_group)
        obj_tile.depth_y = obj.y + obj.height  # Bottom of the object for depth sorting



# --- Music Volume Display Timer ---
music_volume_display_time = 0
music_volume_display_max = 1200  # ms


while True:
    # Calculate delta time in milliseconds
    dt = clock.tick(60)  # 60 FPS like in V02

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            # ...existing code...
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            screen_width, screen_height = screen.get_size()
            camera.width = screen_width
            camera.height = screen_height
            message_display.screen_width = screen_width
            message_display.screen_height = screen_height
            pause_menu.update_dimensions(screen_width, screen_height)
            pause_menu.reload_frame_png()
            if getattr(map_config.Config_Data, 'HAS_VIGNETTE', False):
                vignette_surface = create_vignette(screen_width, screen_height)
            else:
                vignette_surface = None
        elif event.type == pygame.KEYDOWN:
            # --- Fullscreen toggle (F11) ---
            if event.key == pygame.K_F11:
                if screen.get_flags() & pygame.FULLSCREEN:
                    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
                else:
                    info = pygame.display.Info()
                    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                screen_width, screen_height = screen.get_size()
                camera.width = screen_width
                camera.height = screen_height
                message_display.screen_width = screen_width
                message_display.screen_height = screen_height
                pause_menu.update_dimensions(screen_width, screen_height)
                pause_menu.reload_frame_png()
            # --- Pause menu toggle ---
            if event.key == pygame.K_ESCAPE:
                game_paused = not game_paused
                continue  # Don't process other keys this frame
            if event.key == pygame.K_SPACE:
                handle_spacebar_facing_check(player, tmx_data)
            # --- Music volume control: +/- keys ---
            elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                set_music_volume(music_volume + 0.05)
                music_volume_display_time = music_volume_display_max
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                set_music_volume(music_volume - 0.05)
                music_volume_display_time = music_volume_display_max

        # --- PAUSE MENU EVENT HANDLING ---
        if game_paused:
            # Only handle pause menu events while paused
            if event.type == pygame.KEYDOWN:
                if not pause_menu.in_regen_menu and event.key == pygame.K_r:
                    pause_menu.enter_regen_menu()
                elif pause_menu.in_regen_menu:
                    pause_menu.handle_regen_event(event)

    if game_paused:
        # Show the pause menu using the new function
        show_pause_menu(screen, pause_menu, dt)
        pygame.display.flip()
        continue

    # ...existing code for game update and rendering
    # Handle player movement and animation
    keys = pygame.key.get_pressed()
    player.update(keys, collision_tiles, tmx_data, dt)

    # Check if any enemy touches the player
    enemy_touches_player(player, object_group)

    # --- Bone_Grass tile detection with exponential damage stacking ---
    on_bone_grass, is_moving, is_running = is_player_on_bone_grass(player, tmx_data)
    # Track consecutive bone grass steps
    if not hasattr(player, 'bone_grass_steps'):
        player.bone_grass_steps = 0
    if not hasattr(player, 'last_on_bone_grass_list'):
        player.last_on_bone_grass_list = [False] * 5
    damage = 0
    base_damage = 0.002 if is_running else 0.001
    if on_bone_grass:
        # Update history (keep last 5)
        player.last_on_bone_grass_list.append(True)
        if len(player.last_on_bone_grass_list) > 5:
            player.last_on_bone_grass_list.pop(0)
        # Continue stacking if at least one of the last 5 was on bone grass
        if any(player.last_on_bone_grass_list):
            player.bone_grass_steps += 1
        else:
            player.bone_grass_steps = 1
        # Exponential stacking, max 100% more (double damage)
        stack_multiplier = min(2000.0, 1.0 * (1.016 ** (player.bone_grass_steps - 1)))
        if is_moving:
            damage = base_damage * stack_multiplier
    else:
        # Update history (keep last 5)
        player.last_on_bone_grass_list.append(False)
        if len(player.last_on_bone_grass_list) > 5:
            player.last_on_bone_grass_list.pop(0)
        # Only reset counter if last 5 steps were NOT on bone grass
        if not any(player.last_on_bone_grass_list):
            player.bone_grass_steps = 0
    if damage > 0:
        # Only legs receive bone grass damage
        player_stats.take_damage(damage, part='legs')
        print(f"[DEBUG] Bone grass damage dealt to legs: {damage:.3f}")
        # Play sound if at least 0.5 seconds since last play (max 2 times per second)
        now = time.time()
        if bone_grass_sound is not None:
            if now - last_bone_grass_sound_time >= 0.3:
                bone_grass_sound.play()
                last_bone_grass_sound_time = now
        else:
            print("[DEBUG] Bone grass sound not loaded, cannot play sound.")

    # --- Event Trigger Check ---
    # Get player hitbox (same as collision)
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    player_hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)

    for game_event in event_list:
        if not game_event.triggered and player_hitbox.colliderect(game_event.rect):
            if game_event.name.lower() == "event_1":
                message_display.show_message("FORESTA DORSALE SUD", 4000)
                game_event.triggered = True  # Prevent retriggering
            # Add more event triggers here as needed

    # Update message display
    message_display.update(dt)

    # Music volume display timer
    if music_volume_display_time > 0:
        music_volume_display_time -= dt
        if music_volume_display_time < 0:
            music_volume_display_time = 0

    # Keep player within map bounds using full sprite dimensions for boundary check
    # Keep player within map bounds using hitbox position and size
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
    player.pos.x - current_image.get_width()//2,
    player.pos.y - current_image.get_height()//2,
    current_image, tmx_data)
    # Calculate the offset from player.pos to hitbox center
    hitbox_center_x = hitbox_x + hitbox_width // 2
    hitbox_center_y = hitbox_y + hitbox_height // 2
    offset_x = player.pos.x - hitbox_center_x
    offset_y = player.pos.y - hitbox_center_y
    # Clamp hitbox center to map bounds
    min_x = hitbox_width // 2
    max_x = map_width - (hitbox_width // 2)
    min_y = hitbox_height // 2
    max_y = map_height - (hitbox_height // 2)
    new_hitbox_center_x = max(min_x, min(player.pos.x - offset_x, max_x))
    new_hitbox_center_y = max(min_y, min(player.pos.y - offset_y, max_y))
    # Update player.pos so that hitbox stays within bounds
    player.pos.x = new_hitbox_center_x + offset_x
    player.pos.y = new_hitbox_center_y + offset_y
    player.rect.center = player.pos

    # Update camera to follow player
    camera.update(player.pos)

    # Clear screen
    screen.fill((0, 0, 0))


    # --- Dynamic Rendering: Only draw tiles/objects in camera view plus margin ---
    margin = 2 * tmx_data.tilewidth  # 2 tiles margin around camera
    # Camera world rect (unzoomed)
    cam_x = -camera.camera.x
    cam_y = -camera.camera.y
    cam_w = camera.width / camera.zoom_factor
    cam_h = camera.height / camera.zoom_factor
    camera_world_rect = pygame.Rect(cam_x - margin, cam_y - margin, cam_w + 2*margin, cam_h + 2*margin)

    # Step 1: Draw only visible tile sprites
    for sprite in tile_group:
        # Only draw if tile is in camera view + margin
        if camera_world_rect.colliderect(sprite.rect):
            # Calculate scaled size and position, rounding to nearest integer
            scaled_width = round(sprite.image.get_width() * camera.zoom_factor)
            scaled_height = round(sprite.image.get_height() * camera.zoom_factor)
            scaled_surface = pygame.transform.scale(sprite.image, (scaled_width, scaled_height))
            sprite_rect = camera.apply(sprite)
            blit_x = round(sprite_rect.x)
            blit_y = round(sprite_rect.y)
            screen.blit(scaled_surface, (blit_x, blit_y))

    # Step 2: Depth-sorted rendering for player and visible objects
    render_objects = []

    # Add player to render list (always use hitbox bottom)
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    player_hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    player_depth_y = player_hitbox_rect.bottom
    scaled_player = pygame.transform.scale(player.image,
        (int(player.image.get_width() * camera.zoom_factor),
         int(player.image.get_height() * camera.zoom_factor)))
    player_rect = camera.apply(player)
    render_objects.append({
        'type': 'player',
        'depth_y': player_depth_y,
        'surface': scaled_player,
        'rect': player_rect
    })

    # Add only visible objects to render list
    for obj_sprite in object_group:
        # Only draw if object is in camera view + margin
        if camera_world_rect.colliderect(obj_sprite.rect):
            if isinstance(obj_sprite, NPC):
                obj_sprite.update(player, collision_tiles, tmx_data)
                obj_image = obj_sprite.image
                obj_hitbox_x, obj_hitbox_y, obj_hitbox_width, obj_hitbox_height = get_character_hitbox(
                    obj_sprite.pos.x - obj_image.get_width()//2,
                    obj_sprite.pos.y - obj_image.get_height()//2,
                    obj_image, tmx_data)
                obj_depth_y = obj_hitbox_y + obj_hitbox_height
            else:
                obj_depth_y = obj_sprite.rect.bottom

            scaled_surface = pygame.transform.scale(obj_sprite.image,
                (int(obj_sprite.image.get_width() * camera.zoom_factor),
                 int(obj_sprite.image.get_height() * camera.zoom_factor)))
            sprite_rect = camera.apply(obj_sprite)
            render_objects.append({
                'type': 'object',
                'depth_y': obj_depth_y,
                'surface': scaled_surface,
                'rect': sprite_rect
            })

    # Sort by depth_y and render
    render_objects.sort(key=lambda obj: obj['depth_y'])
    for obj in render_objects:
        screen.blit(obj['surface'], (obj['rect'].x, obj['rect'].y))

    # Step 3: Draw UI elements (message display) on top of everything
    draw_hp_bar(screen, player, player_stats.hp, player_stats.max_hp)
    if player_stats.stamina < player_stats.max_stamina:
        draw_stamina_bar(screen, player)
    message_display.draw(screen)

    # Draw player hitbox as a semitransparent red rectangle
    current_image = player.image
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
        player.pos.x - current_image.get_width()//2,
        player.pos.y - current_image.get_height()//2,
        current_image, tmx_data)
    # Convert world coordinates to screen coordinates using camera
    hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    screen_hitbox_rect = camera.apply_rect(hitbox_rect)
    hitbox_surface = pygame.Surface((screen_hitbox_rect.width, screen_hitbox_rect.height), pygame.SRCALPHA)
    hitbox_surface.fill((255, 0, 0, 120))  # Red, alpha=120
    screen.blit(hitbox_surface, (screen_hitbox_rect.x, screen_hitbox_rect.y))

    # Draw music volume if recently changed
    if music_volume_display_time > 0:
        font = pygame.font.SysFont(None, 32, bold=True)
        vol_text = f"Music Volume: {int(music_volume*100)}%"
        text_surface = font.render(vol_text, True, (255, 255, 0))
        text_rect = text_surface.get_rect(center=(screen_width//2, 60))
        # Draw a black box behind
        box_rect = text_rect.inflate(20, 10)
        s = pygame.Surface((box_rect.width, box_rect.height))
        s.set_alpha(180)
        s.fill((0,0,0))
        screen.blit(s, box_rect.topleft)
        screen.blit(text_surface, text_rect)

    # --- Ambient Occlusion Vignette Overlay (precomputed) ---
    if vignette_surface is not None:
        screen.blit(vignette_surface, (0, 0))

    pygame.display.flip()