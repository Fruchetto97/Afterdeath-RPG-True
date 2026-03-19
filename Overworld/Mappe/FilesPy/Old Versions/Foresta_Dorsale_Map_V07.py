def is_player_on_bone_grass(player, tmx_data):
    """
    Return (on_bone_grass, is_moving, is_running):
    - on_bone_grass: True if the player's feet are inside a tile of class 'Bone_Grass'.
    - is_moving: True if the player is moving.
    - is_running: True if the player is running (sprinting).
    """
    # Circle: center = player feet, radius = 0.4 * tilewidth
    player_center = (player.rect.centerx, player.rect.centery + tmx_data.tileheight)
    radius = tmx_data.tilewidth / 2.6


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
    if hasattr(player, 'sprint_locked') and hasattr(player, 'stamina') and hasattr(player, 'max_stamina'):
        # This logic matches Player.update
        keys = pygame.key.get_pressed()
        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        can_sprint = not player.sprint_locked and player.stamina > 0
        is_running = shift_pressed and can_sprint and is_moving
    return on_bone_grass, is_moving, is_running

# --- Utility: Check if any enemy touches the player (center-to-center within 8 pixels) ---
def enemy_touches_player(player, object_group):
    player_center = pygame.math.Vector2(player.rect.center)
    for obj in object_group:
        if isinstance(obj, NPC):
            npc_center = pygame.math.Vector2(obj.rect.center)
            if player_center.distance_to(npc_center) <= 10:
                print(f"[DEBUG] Enemy '{obj.name}' touches player at {npc_center} (distance: {player_center.distance_to(npc_center)})")
                return True
    return False
# Run script for object by name ---
def run_object_script(obj):
    """Run a script based on the object's name. Extend this for more objects/scripts."""
    if hasattr(obj, 'name'):
        if obj.name == 'prompt_albero_dorsale':
            message_display.show_message("questo albero sembra fatto di vertebre...", 2000)
    # Add more object.name checks and scripts here as needed

import pygame, sys, time

# --- PlayerStats class for all player stats and info ---
class PlayerStats:
    def __init__(self, name, gif_path, sprite_path, max_hp, max_stamina, max_regen, max_reserve):
        self.name = name
        self.gif_path = gif_path
        self.sprite_path = sprite_path
        # Stats: current and max
        self.max_hp = max_hp
        self.hp = max_hp
        self.max_stamina = max_stamina
        self.stamina = max_stamina
        self.max_regen = max_regen
        self.regen = max_regen
        self.max_reserve = max_reserve
        self.reserve = max_reserve
        # Images
        self.gif_image = None  # Loaded by PauseMenu
        self.sprite_image = None  # Loaded by Player

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def use_stamina(self, amount):
        self.stamina = max(0, self.stamina - amount)

    def regen_stamina(self, amount):
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def use_regen(self, amount):
        self.regen = max(0, self.regen - amount)

    def regen_regen(self, amount):
        self.regen = min(self.max_regen, self.regen + amount)

    def use_reserve(self, amount):
        self.reserve = max(0, self.reserve - amount)

    def regen_reserve(self, amount):
        self.reserve = min(self.max_reserve, self.reserve + amount)

    # Add more stat logic as needed

# --- Pause Menu System ---



class PauseMenu:
    def __init__(self, screen_width, screen_height, player_stats):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.player_stats = player_stats
        self.player_img_path = player_stats.gif_path
        self._set_menu_box()
        self.player_frames = []
        self.player_frame_durations = []
        self.player_frame_index = 0
        self.player_frame_timer = 0
        self.player_frame_count = 1
        self.player_img = None
        try:
            from PIL import Image
            pil_img = Image.open(self.player_img_path)
            self.player_frames = []
            self.player_frame_durations = []
            gif_target_height = int(self.menu_box_height * 0.96)
            pil_img.seek(0)
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
                gif_target_height = int(self.menu_box_height * 0.96)
                gif_target_width = int(gif_target_height * aspect)
                self.player_img = pygame.transform.smoothscale(img, (gif_target_width, gif_target_height))
                self.gif_target_width = gif_target_width
                self.gif_target_height = gif_target_height
            except Exception as e:
                print(f"[PauseMenu] Could not load player image: {e}")
                self.player_img = None
                self.gif_target_width = 120
                self.gif_target_height = int(self.menu_box_height * 0.96)
        except Exception as e:
            print(f"[PauseMenu] Could not load GIF with Pillow: {e}")
            try:
                img = pygame.image.load(self.player_img_path).convert_alpha()
                aspect = img.get_width() / img.get_height() if img.get_height() != 0 else 1
                gif_target_height = int(self.menu_box_height * 0.96)
                gif_target_width = int(gif_target_height * aspect)
                self.player_img = pygame.transform.smoothscale(img, (gif_target_width, gif_target_height))
                self.gif_target_width = gif_target_width
                self.gif_target_height = gif_target_height
            except Exception as e2:
                print(f"[PauseMenu] Could not load player image: {e2}")
                self.player_img = None
                self.gif_target_width = 120
                self.gif_target_height = int(self.menu_box_height * 0.96)
        try:
            self.font = pygame.font.SysFont('arial', 32, bold=True)
            self.font_big = pygame.font.SysFont('arial', 38, bold=True)
        except Exception:
            self.font = pygame.font.SysFont(None, 32, bold=True)
            self.font_big = pygame.font.SysFont(None, 38, bold=True)

    def _set_menu_box(self):
        # 2/3 of screen, centered, but width is 50% larger
        base_width = int(self.screen_width * 2 / 3)
        self.menu_box_width = int(base_width * 1.4)
        # Cap width to screen width
        if self.menu_box_width > self.screen_width:
            self.menu_box_width = self.screen_width
        self.menu_box_height = int(self.screen_height * 2 / 3)
        self.menu_box_x = (self.screen_width - self.menu_box_width) // 2
        self.menu_box_y = (self.screen_height - self.menu_box_height) // 2
        self.menu_surface = pygame.Surface((self.menu_box_width, self.menu_box_height), pygame.SRCALPHA)
        self.menu_surface.fill((30, 30, 40, 200))  # semi-transparent, slightly blue/gray

    def update(self, dt):
        # Animate GIF if multiple frames
        if self.player_frame_count > 1 and self.player_frames:
            self.player_frame_timer += dt
            frame_duration = self.player_frame_durations[self.player_frame_index]
            if self.player_frame_timer >= frame_duration:
                self.player_frame_timer = 0
                self.player_frame_index = (self.player_frame_index + 1) % self.player_frame_count
                self.player_img = self.player_frames[self.player_frame_index]


    def draw(self, screen):
        # Draw menu box (centered, semi-transparent)
        self.menu_surface.fill((30, 30, 40, 200))

        # --- Draw player GIF image occupying full menu height ---
        gif_x = 30
        gif_y = (self.menu_box_height - self.gif_target_height) // 2
        if self.player_img:
            self.menu_surface.blit(self.player_img, (gif_x, gif_y))

        # --- Draw double vertical white line to the right of the GIF ---
        line_x = gif_x + self.gif_target_width + 4  # 4px gap after GIF
        line_top = int(self.menu_box_height * 0.02)
        line_bottom = self.menu_box_height - int(self.menu_box_height * 0.02)
        # First line
        pygame.draw.line(self.menu_surface, (255,255,255), (line_x, line_top), (line_x, line_bottom), 2)
        # Second line (4px to the right)
        pygame.draw.line(self.menu_surface, (255,255,255), (line_x+6, line_top), (line_x+6, line_bottom), 2)




        # --- Independent positions for name and bars ---
        stats_x = line_x + 18  # 12px gap after second line
        name_y = gif_y + 30  # Name position (independent)
        bars_y = gif_y + 100  # Bars position (independent)
        bar_width = int(self.menu_box_width * 0.16)  # half as long as before
        bar_height = int(32 * 0.90)  # 5% less tall
        bar_gap = 32

        # Character name
        name_surface = self.font_big.render(self.player_stats.name.upper(), True, (255,255,255))
        name_x = stats_x
        self.menu_surface.blit(name_surface, (name_x, name_y))

        # Health bar
        hp_ratio = self.player_stats.hp / self.player_stats.max_hp if self.player_stats.max_hp > 0 else 0
        hp_bar_rect = pygame.Rect(stats_x, bars_y, bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (60, 20, 20), hp_bar_rect)  # background
        pygame.draw.rect(self.menu_surface, (200, 0, 0), (stats_x, bars_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), hp_bar_rect, 2)
        hp_text = f"HEALTH: {self.player_stats.hp} / {self.player_stats.max_hp}"
        hp_surface = self.font.render(hp_text.upper(), True, (255,255,255))
        hp_text_x = stats_x + bar_width + 18
        hp_text_y = bars_y + (bar_height - hp_surface.get_height()) // 2
        self.menu_surface.blit(hp_surface, (hp_text_x, hp_text_y))

        # Stamina bar
        stamina_ratio = self.player_stats.stamina / self.player_stats.max_stamina if self.player_stats.max_stamina > 0 else 0
        stamina_bar_rect = pygame.Rect(stats_x, bars_y + bar_height + bar_gap, bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (20, 60, 20), stamina_bar_rect)  # background
        pygame.draw.rect(self.menu_surface, (0, 200, 0), (stats_x, bars_y + bar_height + bar_gap, int(bar_width * stamina_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), stamina_bar_rect, 2)
        stamina_text = f"STAMINA: {self.player_stats.stamina} / {self.player_stats.max_stamina}"
        stamina_surface = self.font.render(stamina_text.upper(), True, (255,255,255))
        stamina_text_x = stats_x + bar_width + 18
        stamina_text_y = bars_y + bar_height + bar_gap + (bar_height - stamina_surface.get_height()) // 2
        self.menu_surface.blit(stamina_surface, (stamina_text_x, stamina_text_y))

        # Regen bar
        regen_ratio = self.player_stats.regen / self.player_stats.max_regen if self.player_stats.max_regen > 0 else 0
        regen_bar_rect = pygame.Rect(stats_x, bars_y + 2*(bar_height + bar_gap), bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (20, 20, 60), regen_bar_rect)  # background
        pygame.draw.rect(self.menu_surface, (0, 120, 255), (stats_x, bars_y + 2*(bar_height + bar_gap), int(bar_width * regen_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), regen_bar_rect, 2)
        regen_text = f"REGEN: {self.player_stats.regen} / {self.player_stats.max_regen}"
        regen_surface = self.font.render(regen_text.upper(), True, (255,255,255))
        regen_text_x = stats_x + bar_width + 18
        regen_text_y = bars_y + 2*(bar_height + bar_gap) + (bar_height - regen_surface.get_height()) // 2
        self.menu_surface.blit(regen_surface, (regen_text_x, regen_text_y))

        # Reserve bar
        reserve_ratio = self.player_stats.reserve / self.player_stats.max_reserve if self.player_stats.max_reserve > 0 else 0
        reserve_bar_rect = pygame.Rect(stats_x, bars_y + 3*(bar_height + bar_gap), bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (60, 60, 20), reserve_bar_rect)  # background
        pygame.draw.rect(self.menu_surface, (255, 200, 0), (stats_x, bars_y + 3*(bar_height + bar_gap), int(bar_width * reserve_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), reserve_bar_rect, 2)
        reserve_text = f"RESERVE: {self.player_stats.reserve} / {self.player_stats.max_reserve}"
        reserve_surface = self.font.render(reserve_text.upper(), True, (255,255,255))
        reserve_text_x = stats_x + bar_width + 18
        reserve_text_y = bars_y + 3*(bar_height + bar_gap) + (bar_height - reserve_surface.get_height()) // 2
        self.menu_surface.blit(reserve_surface, (reserve_text_x, reserve_text_y))

        # Draw the menu surface onto the main screen
        screen.blit(self.menu_surface, (self.menu_box_x, self.menu_box_y))

    def update_dimensions(self, width, height):
        self.screen_width = width
        self.screen_height = height
        self._set_menu_box()
        # Recalculate GIF size for new menu dimensions
        try:
            from PIL import Image
            pil_img = Image.open(self.player_img_path)
            gif_target_height = int(self.menu_box_height * 0.96)
            aspect = pil_img.width / pil_img.height if pil_img.height != 0 else 1
            gif_target_width = int(gif_target_height * aspect)
            new_frames = []
            for frame in range(0, getattr(pil_img, 'n_frames', 1)):
                pil_img.seek(frame)
                frame_img = pil_img.convert('RGBA')
                mode = frame_img.mode
                size = frame_img.size
                data = frame_img.tobytes()
                surf = pygame.image.fromstring(data, size, mode)
                surf = pygame.transform.smoothscale(surf, (gif_target_width, gif_target_height))
                new_frames.append(surf)
            self.player_frames = new_frames
            self.player_img = self.player_frames[self.player_frame_index] if self.player_frames else None
            self.gif_target_width = gif_target_width
            self.gif_target_height = gif_target_height
        except Exception:
            pass

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
    bone_grass_sound.set_volume(0.3)
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
        self.speed = speed
        self.active = active
        self.sight_range = sight_range

        # For axis-priority memory (to avoid erratic diagonal movement)
        self.axis_priority = None  # 'x' or 'y'
        self.axis_steps_left = 0
        self.last_axis_change_time = 0  # ms since pygame.init()

        # Load character spritesheet (same logic as Player)
        character_spritesheet = pygame.image.load(image_path).convert_alpha()
        sprite_width = character_spritesheet.get_width() // 4  # 4 columns
        sprite_height = character_spritesheet.get_height() // 4  # 4 rows

        # Extract all frames from the spritesheet
        self.frames = {}
        directions = ['down', 'right', 'up', 'left']
        for row, direction in enumerate(directions):
            self.frames[direction] = []

            for col in range(4):
                frame_rect = pygame.Rect(col * sprite_width, row * sprite_height, sprite_width, sprite_height)
                frame = character_spritesheet.subsurface(frame_rect)
                self.frames[direction].append(frame)
                # --- Bone_Grass tile detection ---
                if is_player_on_bone_grass(player, tmx_data):
                    print("[DEBUG] Player is on a Bone_Grass tile!")

        # Animation properties
        self.direction = 'up'
        self.frame_index = 0
        self.animation_speed = 0.2
        self.animation_timer = 0

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
            if self.axis_priority == 'x':
                if dx > 0:
                    directions.append(('right', (self.speed, 0)))
                elif dx < 0:
                    directions.append(('left', (-self.speed, 0)))
                if dy != 0:
                    if dy > 0:
                        directions.append(('down', (0, self.speed)))
                    else:
                        directions.append(('up', (0, -self.speed)))
            else:  # 'y'
                if dy > 0:
                    directions.append(('down', (0, self.speed)))
                elif dy < 0:
                    directions.append(('up', (0, -self.speed)))
                if dx != 0:
                    if dx > 0:
                        directions.append(('right', (self.speed, 0)))
                    else:
                        directions.append(('left', (-self.speed, 0)))
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
        else:
            self.axis_priority = None
            self.axis_steps_left = 0
        # Animation logic (idle if not moved)
        self.animation_timer += self.animation_speed
        if moved:
            if self.animation_timer >= 1.0:
                self.frame_index = (self.frame_index + 1) % 3 + 1
                self.animation_timer = 0
        else:
            self.frame_index = 0
            self.animation_timer = 0
        self.image = self.frames[self.direction][self.frame_index]
        self.rect.center = self.pos
        self.depth_y = self.rect.bottom

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        # Load character spritesheet from player_stats
        character_spritesheet = pygame.image.load(player_stats.sprite_path).convert_alpha()
        # Character animation setup
        sprite_width = character_spritesheet.get_width() // 4  # 4 columns
        sprite_height = character_spritesheet.get_height() // 4  # 4 rows
        # Extract all frames from the spritesheet
        self.frames = {}
        directions = ['down', 'right', 'up', 'left']
        for row, direction in enumerate(directions):
            self.frames[direction] = []
            for col in range(4):  # 4 frames per direction
                frame_rect = pygame.Rect(col * sprite_width, row * sprite_height, sprite_width, sprite_height)
                frame = character_spritesheet.subsurface(frame_rect)
                self.frames[direction].append(frame)
        # Animation properties
        self.direction = 'down'
        self.frame_index = 0
        self.animation_speed = 0.2
        self.animation_timer = 0
        self.is_moving = False
        # Set initial image and rect
        self.image = self.frames[self.direction][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        # Movement properties
        self.speed = 5  # pixels per frame like in V02
        self.pos = pygame.math.Vector2(pos)
        # Stamina system (now handled by player_stats)
        self.stamina_regen_timer = 0.0
        self.stamina_drain_timer = 0.0
        self.sprint_locked = False
    
    def update(self, keys, collision_tiles, tmx_data, dt=16):
        # dt: milliseconds since last frame (default 16ms for 60fps if not provided)
        self.is_moving = False
        new_pos = self.pos.copy()

        # Sprint logic: if shift is pressed, increase speed, but only if stamina > 0 and not locked
        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        can_sprint = not self.sprint_locked and player_stats.stamina > 0
        sprinting = shift_pressed and can_sprint
        move_speed = self.speed * 1.5 if sprinting else self.speed

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

        # Stamina drain/regeneration logic (use player_stats)
        if sprinting and self.is_moving:
            self.stamina_regen_timer = 0.0  # Reset regen timer while sprinting
            self.stamina_drain_timer += dt / 1000.0  # dt is ms, convert to seconds
            if self.stamina_drain_timer >= 0.001:
                player_stats.stamina = max(0, player_stats.stamina - 1)
                self.stamina_drain_timer -= 0.5
            if player_stats.stamina <= 0:
                self.sprint_locked = True
        else:
            self.stamina_drain_timer = 0.0
            # Only regen if not sprinting and stamina < max
            if player_stats.stamina < player_stats.max_stamina:
                self.stamina_regen_timer += dt / 1000.0
                if self.stamina_regen_timer >= 1.0:
                    player_stats.stamina = min(player_stats.max_stamina, player_stats.stamina + 1)
                    self.stamina_regen_timer -= 1.0
            # Unlock sprint if stamina is at least half max
            if self.sprint_locked and player_stats.stamina >= player_stats.max_stamina / 2:
                self.sprint_locked = False

        # Check collision using the smaller hitbox instead of full sprite
        if self.is_moving:
            # Calculate the character's hitbox for collision detection
            current_image = self.frames[self.direction][self.frame_index]
            hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(new_pos.x - current_image.get_width()//2, 
                                                                                   new_pos.y - current_image.get_height()//2, 
                                                                                   current_image, tmx_data)

            # Only update position if no collision
            if not check_collision(hitbox_x, hitbox_y, hitbox_width, hitbox_height, collision_tiles, tmx_data):
                self.pos = new_pos
            else:
                # If there's a collision, stop the movement animation
                self.is_moving = False

        # Update animation
        if self.is_moving:
            if self.frame_index == 0:
                # Start animation immediately on movement
                self.frame_index = 1
                self.animation_timer = 0
            else:
                self.animation_timer += self.animation_speed
                if self.animation_timer >= 1.0:
                    self.frame_index = (self.frame_index + 1) % 3 + 1  # Cycle through frames 1, 2, 3
                    self.animation_timer = 0
        else:
            self.frame_index = 0  # Idle frame
            self.animation_timer = 0

        # Update image and rect
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
    player_rect = player.rect if hasattr(player, 'rect') else None
    if not player_rect:
        return None
    for obj in tmx_data.objects:
        if not hasattr(obj, 'image') or obj.image is None:
            obj_rect = pygame.Rect(obj.x, obj.y, getattr(obj, 'width', 0), getattr(obj, 'height', 0))
            if player_rect.colliderect(obj_rect):
                # Get centers
                player_center = pygame.math.Vector2(player.rect.center)
                object_center = pygame.math.Vector2(obj_rect.center)
                direction = getattr(player, 'direction', None)
                to_object = object_center - player_center
                # Allow some tolerance for being "close enough"
                tolerance = 40
                if to_object.length() > max(player.rect.width, player.rect.height) + tolerance:
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
        run_object_script(obj)
        print(f"Interacted with object: {obj.name if hasattr(obj, 'name') else 'Unnamed Object'}")

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.zoom_factor = 2.0  # 2x zoom like in V02

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
        self.Used_Font = "romanc"  # Roman font from your system

        # Try to load Roman font, fall back to default if not available
        try:
            self.font = pygame.font.Font(self.Used_Font, 36)
        except FileNotFoundError:
            try:
                # Try system font if ttf file not found
                self.font = pygame.font.SysFont(self.Used_Font, 36, bold=True)
            except:
                # Fall back to default font
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
    hitbox_width = int(tmx_data.tilewidth * 0.7)
    hitbox_height = int(tmx_data.tileheight * 0.3)

    # Center the hitbox horizontally within the sprite
    hitbox_x = char_x + (sprite_width - hitbox_width) // 2

    # Position hitbox in the lower half of the sprite
    # Start at 3/4 down the sprite height
    hitbox_y = char_y + (sprite_height * 3 // 4) - (hitbox_height // 2)

    return hitbox_x, hitbox_y, hitbox_width, hitbox_height


screen_width = 1280
screen_height = 720

pygame.init()


# --- Initialize PlayerStats and Pause Menu ---
player_stats = PlayerStats(
    name="Selkio_NPC",
    gif_path=r"C:\Users\franc\Desktop\Afterdeath_RPG\Enemies_GIFs\Selkio_NPC_2_GIF.gif",
    sprite_path=r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Selkio_Guerriero.png",
    max_hp=500,
    max_stamina=20,
    max_regen=10,
    max_reserve=8
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
    pygame.mixer.music.load(r"C:\Users\franc\Desktop\Afterdeath_RPG\Musics\Battle-Walzer.MP3")
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play(-1)  # Loop forever
    print("Music started: Battle-Walzer.MP3")
except Exception as e:
    print(f"Music could not be loaded: {e}")

screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("TMX Map with Camera")
clock = pygame.time.Clock()

tmx_data = load_pygame("C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Mappe\\Exports\\Foresta_Dorsale_01.tmx")

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
player = Player(spawn_position, player_group)



# --- Example Enemy ---
# You can change the image path and position as needed
enemy_example = NPC(
    name="Selkio_Nemico",
    image_path=r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Katherine_Demonde.png",
    pos=(spawn_position[0] + 5, spawn_position[1] - 500),  # Example: 5px to the right of player
    speed=3,
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
        # Use objects as-is - no flipping needed since you created separate object types
        pos = (obj.x, obj.y)
        # Add Y-position for depth sorting
        obj_tile = Tile(pos=pos, surf=obj.image, groups=object_group)
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
            # Handle window resize (including maximize/fullscreen)
            screen_width, screen_height = event.w, event.h
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)

            # Update camera dimensions
            camera.width = screen_width
            camera.height = screen_height

            # Update message display dimensions
            message_display.screen_width = screen_width
            message_display.screen_height = screen_height

            # Update pause menu dimensions
            pause_menu.update_dimensions(screen_width, screen_height)
        elif event.type == pygame.KEYDOWN:
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

    if game_paused:
        # Animate GIF in pause menu
        pause_menu.update(dt)
        pause_menu.draw(screen)
        pygame.display.flip()
        continue

    # ...existing code for game update and rendering...
    # Handle player movement and animation
    keys = pygame.key.get_pressed()
    player.update(keys, collision_tiles, tmx_data, dt)

    # Check if any enemy touches the player
    enemy_touches_player(player, object_group)

    # --- Bone_Grass tile detection ---
    on_bone_grass, is_moving, is_running = is_player_on_bone_grass(player, tmx_data)
    damage = 0
    if on_bone_grass:
        if is_moving:
            if is_running:
                damage = 2  # Double damage if running
            else:
                damage = 1  # Normal damage if walking
        # else: no damage if not moving
    if damage > 0:
        player_stats.take_damage(damage)
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
    character_width = player.image.get_width()
    character_height = player.image.get_height()
    player.pos.x = max(character_width//2, min(player.pos.x, map_width - character_width//2))
    player.pos.y = max(character_height//2, min(player.pos.y, map_height - character_height//2))
    player.rect.center = player.pos

    # Update camera to follow player
    camera.update(player.pos)

    # Clear screen
    screen.fill((0, 0, 0))

    # Step 1: Draw all tile layers (always below everything)
    for sprite in tile_group:
        scaled_surface = pygame.transform.scale(sprite.image,
            (int(sprite.image.get_width() * camera.zoom_factor),
             int(sprite.image.get_height() * camera.zoom_factor)))
        sprite_rect = camera.apply(sprite)
        screen.blit(scaled_surface, (sprite_rect.x, sprite_rect.y))

    # Step 2: Create depth-sorted rendering for player and objects
    render_objects = []

    # Calculate player's depth Y (base/bottom of player for depth sorting)
    # Since player.rect.center is at the center, we need to get the bottom
    player_depth_y = player.rect.bottom  # Bottom edge of the player sprite

    # Add player to render list
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

    # Add objects to render list
    npc_found = False
    for obj_sprite in object_group:
        # If the object is an NPC, call its update with player and collision info
        if isinstance(obj_sprite, NPC):
            obj_sprite.update(player, collision_tiles, tmx_data)
            npc_found = True
        depth_y = getattr(obj_sprite, 'depth_y', obj_sprite.rect.bottom)
        scaled_surface = pygame.transform.scale(obj_sprite.image,
            (int(obj_sprite.image.get_width() * camera.zoom_factor),
             int(obj_sprite.image.get_height() * camera.zoom_factor)))
        sprite_rect = camera.apply(obj_sprite)
        render_objects.append({
            'type': 'object',
            'depth_y': depth_y,
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

    pygame.display.flip()