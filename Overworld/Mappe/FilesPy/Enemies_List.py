# --- Utility functions for character logic (duplicated for self-containment) ---
import pygame
import random

# Import Character and related classes from Battle_Menu_Beta_V18 in same directory
import sys
import os
# Import from the same directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def load_character_frames(image_path):
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
            if direction == 'down':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, -13))
                frames[direction].append(shifted_surface)
            elif direction == 'right':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, -7))
                frames[direction].append(shifted_surface)
            elif direction == 'up':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (-1, 3))
                frames[direction].append(shifted_surface)
            elif direction == 'left':
                shifted_surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                shifted_surface.blit(frame, (0, 9))
                frames[direction].append(shifted_surface)
            else:
                frames[direction].append(frame)
        start_frames[direction] = 1
    return {'frames': frames, 'start_frames': start_frames}

def check_collision(x, y, width, height, collision_tiles, tmx_data):
    left_tile = int(x // tmx_data.tilewidth)
    right_tile = int((x + width - 1) // tmx_data.tilewidth)
    top_tile = int(y // tmx_data.tileheight)
    bottom_tile = int((y + height - 1) // tmx_data.tileheight)
    for tile_x in range(left_tile, right_tile + 1):
        for tile_y in range(top_tile, bottom_tile + 1):
            if (tile_x, tile_y) in collision_tiles:
                return True
    return False

def get_character_hitbox(char_x, char_y, char_image, tmx_data):
    sprite_width = char_image.get_width()
    sprite_height = char_image.get_height()
    hitbox_width = int(tmx_data.tilewidth * 0.7) + 2
    hitbox_height = int(tmx_data.tileheight * 0.3) + 4
    hitbox_x = char_x + (sprite_width - hitbox_width) // 2
    hitbox_y = char_y + (sprite_height * 3 // 4) - (hitbox_height // 2) - 2
    return hitbox_x, hitbox_y, hitbox_width, hitbox_height

# --- NPC class definition (moved from npc_base.py) ---
import pygame
import inspect
import random
## Utility functions are now defined above; no import needed

class NPC(pygame.sprite.Sprite):
    def __init__(self, name, image_path, death_image_path, pos, speed=2, active=True, sight_range=30, groups=None, battle_character=None):
        if groups is not None:
            super().__init__(groups)
        else:
            super().__init__()
        self.name = name
        self.death_image_path = death_image_path
        self.speed = speed
        self.active = active
        self.sight_range = sight_range
        self.axis_priority = None
        self.axis_steps_left = 0
        self.last_axis_change_time = 0
        self.last_random_move_time = 0
        self.random_move_dir = None
        self.random_move_steps_left = 0
        self.random_move_dx = 0
        self.random_move_dy = 0
        
        # Battle character data - stores the Character instance for battle
        self.battle_character = battle_character
        
        frames_data = load_character_frames(image_path)
        self.frames = frames_data['frames']
        self.start_frames = frames_data['start_frames']
        self.direction = 'up'
        self.frame_index = 0
        self.animation_speed = 0.2
        self.animation_timer = 0
        self.pingpong_forward = True
        self.pos = pygame.math.Vector2(pos)
        # Store spawn coordinates for world state tracking
        self.spawn_x = pos[0]
        self.spawn_y = pos[1]
        self.image = self.frames[self.direction][self.frame_index]
        self.rect = self.image.get_rect(center=self.pos)
        self.depth_y = self.rect.bottom
        print(f"[DEBUG] Created NPC '{self.name}' at {self.rect.topleft} depth_y={self.depth_y}")
        print(f"[DEBUG] NPC groups: {self.groups()} (object_group id: {id(groups)})")
        self.spawn_time = pygame.time.get_ticks()  # Track spawn time

    def update(self, player, collision_tiles, tmx_data):
        dx = player.pos.x - self.pos.x
        dy = player.pos.y - self.pos.y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        moved = False
        tile_size = tmx_data.tilewidth
        min_steps = 10
        now = pygame.time.get_ticks()
        cooldown_ms = 500
        # --- Prevent movement for 2 seconds after spawn ---
        if now - getattr(self, 'spawn_time', 0) < 2000:
            self.frame_index = 0
            self.animation_timer = 0
            self.pingpong_forward = True
            self.image = self.frames[self.direction][self.frame_index]
            self.rect.center = self.pos
            self.depth_y = self.rect.bottom
            return
        if dist <= self.sight_range:
            can_change_axis = (self.axis_priority is None or self.axis_steps_left == 0) and (now - self.last_axis_change_time >= cooldown_ms)
            if can_change_axis:
                if abs(dx) > abs(dy):
                    self.axis_priority = 'x'
                elif abs(dy) > abs(dx):
                    self.axis_priority = 'y'
                else:
                    if self.axis_priority is None:
                        self.axis_priority = 'x'
                self.axis_steps_left = min_steps
                self.last_axis_change_time = now
            directions = []
            frame = inspect.currentframe()
            dt = frame.f_back.f_locals.get('dt', 16)
            speed_dt = self.speed * (dt / 1000.0)
            # --- Improved obstacle handling when aligned ---
            aligned_x = abs(int(self.pos.y // tile_size) - int(player.pos.y // tile_size)) < 1
            aligned_y = abs(int(self.pos.x // tile_size) - int(player.pos.x // tile_size)) < 1
            blocked_main = False
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
                # If aligned on X and blocked, try sliding up/down
                if aligned_x:
                    # Check if main direction is blocked
                    test_dir = 'right' if dx > 0 else 'left' if dx < 0 else None
                    if test_dir:
                        mx = speed_dt if test_dir == 'right' else -speed_dt
                        my = 0
                        test_pos = self.pos + pygame.math.Vector2(mx, my)
                        current_image = self.frames[test_dir][self.frame_index]
                        hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
                            test_pos.x - current_image.get_width()//2,
                            test_pos.y - current_image.get_height()//2,
                            current_image, tmx_data)
                        if check_collision(hitbox_x, hitbox_y, hitbox_width, hitbox_height, collision_tiles, tmx_data):
                            blocked_main = True
                    if blocked_main:
                        # Prioritize up/down to slide around obstacle
                        directions = [('down', (0, speed_dt)), ('up', (0, -speed_dt))] + directions
            else:
                if dy > 0:
                    directions.append(('down', (0, speed_dt)))
                elif dy < 0:
                    directions.append(('up', (0, -speed_dt)))
                if dx != 0:
                    if dx > 0:
                        directions.append(('right', (speed_dt, 0)))
                    else:
                        directions.append(('left', (-speed_dt, 0)))
                # If aligned on Y and blocked, try sliding left/right
                if aligned_y:
                    test_dir = 'down' if dy > 0 else 'up' if dy < 0 else None
                    if test_dir:
                        mx = 0
                        my = speed_dt if test_dir == 'down' else -speed_dt
                        test_pos = self.pos + pygame.math.Vector2(mx, my)
                        current_image = self.frames[test_dir][self.frame_index]
                        hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(
                            test_pos.x - current_image.get_width()//2,
                            test_pos.y - current_image.get_height()//2,
                            current_image, tmx_data)
                        if check_collision(hitbox_x, hitbox_y, hitbox_width, hitbox_height, collision_tiles, tmx_data):
                            blocked_main = True
                    if blocked_main:
                        # Prioritize left/right to slide around obstacle
                        directions = [('right', (speed_dt, 0)), ('left', (-speed_dt, 0))] + directions
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
                if self.axis_steps_left > 0:
                    self.axis_steps_left -= 1
                if self.axis_steps_left < 0:
                    self.axis_steps_left = 0
            self.random_move_steps_left = 0
            self.random_move_dir = None
            self.random_move_dx = 0
            self.random_move_dy = 0
        else:
            self.axis_priority = None
            self.axis_steps_left = 0
            frame = inspect.currentframe()
            dt = frame.f_back.f_locals.get('dt', 16)
            speed_dt = self.speed * (dt / 1000.0)
            # Only allow random movement if within 35 tiles of the player
            tile_distance = dist / tmx_data.tilewidth if tmx_data.tilewidth else 0
            if tile_distance <= 35:
                if self.random_move_steps_left == 0 and now - self.last_random_move_time >= 1500:
                    directions_list = [
                        ('up', (0, -1)),
                        ('down', (0, 1)),
                        ('left', (-1, 0)),
                        ('right', (1, 0))
                    ]
                    dir_name, (dx_step, dy_step) = random.choice(directions_list)
                    self.random_move_dir = dir_name
                    self.random_move_steps_left = 36
                    self.random_move_dx = dx_step
                    self.random_move_dy = dy_step
                    self.last_random_move_time = now
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
            else:
                # If too far, reset random movement state
                self.random_move_steps_left = 0
                self.random_move_dir = None
                self.random_move_dx = 0
                self.random_move_dy = 0
        dt = 16
        frame = inspect.currentframe()
        if frame and frame.f_back and 'dt' in frame.f_back.f_locals:
            dt = frame.f_back.f_locals['dt']
        dt_seconds = dt / 1000.0
        animation_speed_dt = self.animation_speed * dt_seconds * 60 * 0.7
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


        
#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

# BATTLE CHARACTER DEFINITIONS
# Generic functions to create battle characters for any enemy type

def create_enemy_battle_character(enemy_data):
    """Generic function to create battle character from enemy data"""
    # Import here to avoid circular import issues
    from Battle_Menu_Beta_V18 import Character, BodyPart, Effetti, Difese
    
    # Get character definition from enemy data
    char_def = enemy_data.get("battle_character", {})
    if not char_def:
        return None
    
    # Create body parts from definition
    body_parts = []
    for part_data in char_def.get("body_parts", []):
        body_part = BodyPart(
            part_data["name"], 
            part_data["max_hp"], 
            part_data["hp"], 
            Effetti(), 
            Difese(), 
            part_data.get("elusione", 1)
        )
        body_parts.append(body_part)
    
    # Create character with stats from definition
    stats = char_def.get("stats", {})
    character = Character(
        char_def.get("name", enemy_data["name"]),
        200, 200,  # max_pvt, pvt (will be recalculated from body parts)
        stats.get("rig", [18, 18])[0], stats.get("rig", [18, 18])[1],
        stats.get("res", [45, 45])[0], stats.get("res", [45, 45])[1],
        stats.get("sta", [14, 14])[0], stats.get("sta", [14, 14])[1],
        stats.get("forz", [12, 12])[0], stats.get("forz", [12, 12])[1],
        stats.get("des", [16, 16])[0], stats.get("des", [16, 16])[1],
        stats.get("spe", [14, 14])[0], stats.get("spe", [14, 14])[1],
        stats.get("vel", [12, 12])[0], stats.get("vel", [12, 12])[1],
        body_parts,
        char_def.get("gif_path", enemy_data.get("image_path", ""))
    )
    
    # Set species from enemy data (essential for elemental resistance calculations)
    character.species = enemy_data.get("species", "Maedo")
    
    # Add skills from enemy data (new skills system)
    add_skills_to_enemy_character(character, enemy_data)
    
    return character

def add_skills_to_enemy_character(character, enemy_data):
    """Generic function to add skills to enemy character from enemy data"""
    # Get skills definition from enemy data
    skills_list = enemy_data.get("skills", [])
    
    if skills_list:
        # Set the equipped_memory_skills attribute for the battle system
        character.equipped_memory_skills = list(skills_list)
        print(f"[EnemiesList] Loaded skills for {character.name}: {character.equipped_memory_skills}")
    else:
        # Default to empty skills if none specified
        character.equipped_memory_skills = []
        print(f"[EnemiesList] No skills specified for {character.name}, using empty list")

def add_moves_to_enemy_character(character, enemy_data):
    """Generic function to add moves to enemy character from enemy data"""
    from Battle_Menu_Beta_V18 import add_move_to_character
    
    # Get moves definition from enemy data
    moves_list = enemy_data.get("battle_character", {}).get("moves", [])
    
    # Get species from enemy data or character name for auto element calculation
    enemy_species = enemy_data.get("species", "Maedo")  # Default to Maedo if no species specified
    if not hasattr(character, 'species'):
        character.species = enemy_species  # Set species on character for element calculation
    
    for move_data in moves_list:
        add_move_to_character(
            character, 
            move_data["name"], 
            move_data["type"], 
            move_data["scaling"]["forz"], 
            move_data["scaling"]["des"], 
            move_data["scaling"]["spe"],
            effects=move_data.get("effects", []), 
            requirements=move_data.get("requirements", []), 
            elements=move_data.get("elements", []), 
            accuracy=move_data.get("accuracy", 100)
        )

# ENEMIES list contains complete battle character definitions
ENEMIES_DATA = [
    {
        "name": "Selkio_Guerriero",
        "species": "Selkio",
        "image_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Selkio_32p.png",
        "death_image_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Selkio_32p_morto.png",
        "speed": 105,
        "active": True,
        "sight_range": 200,
        "study_limit": 2,
        "battle_character": {
            "name": "SELKIO GUERRIERO",
            "gif_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Mappe\FilesPy\enemies_gifs\Selkio_NPC_2_gif.gif",
            "stats": {
                "rig": [20, 20],
                "res": [30, 30],
                "sta": [14, 14],
                "forz": [10, 14],
                "des": [10, 10],
                "spe": [16, 16],
                "vel": [12, 12]
            },
            "body_parts": [
                {"name": "HEAD", "max_hp": 35, "hp": 35, "elusione": 0.5},
                {"name": "RIGHT ARM", "max_hp": 15, "hp": 15, "elusione": 1},
                {"name": "LEFT ARM", "max_hp": 15, "hp": 15, "elusione": 1},
                {"name": "BODY", "max_hp": 100, "hp": 100, "elusione": 1},
                {"name": "RIGHT LEG", "max_hp": 20, "hp": 20, "elusione": 1},
                {"name": "LEFT LEG", "max_hp": 20, "hp": 20, "elusione": 1}
            ],
            "moves": [
                {
                    "name": "Sawblade Hands",
                    "type": "ATK",
                    "scaling": {"forz": 0, "des": 1, "spe": 1},
                    "effects": [["bleed", 2, 2, 0]],
                    "requirements": ["NEEDS 2 ARMS"],
                    "elements": ["CUT"],
                    "accuracy": 90
                },
                {
                    "name": "Messy Slash",
                    "type": "ATK",
                    "scaling": {"forz": 0, "des": 1, "spe": 2},
                    "effects": [["mess_up", 1, 1, 0]],
                    "requirements": ["NEEDS 2 ARMS"],
                    "elements": ["CUT"],
                    "accuracy": 90
                },
                {
                    "name": "Decapitating Kick",
                    "type": "ATK",
                    "scaling": {"forz": 3, "des": 0, "spe": 0},
                    "effects": [["amputate", 1, 1, 0]],
                    "requirements": ["NEEDS LEG", "TARGET HEAD"],
                    "elements": ["IMPACT"],
                    "accuracy": 90
                },
                
                # BUFF/DEBUFF MOVES - Testing buff system for enemies
                {
                    "name": "Moving Blades",
                    "type": "BUF",  # Self-buff for enemy
                    "scaling": {"forz": 0, "des": 0, "spe": 0},
                    "effects": [["moving_blades", 1, 1, 0]],
                    "requirements": ["NEEDS ARM"],
                    "accuracy": 100
                },
            ]
        },
        "skills": ["raising_speed"],  # Enemy memory skills from Skills_Config.py
        "limit_script": {
            "messages": [
                "You have already seen many bodies subjected to the same surgical procedures.",
                "Further study yields no new insights."
            ],
            "actions": [None, None]
        },
        "script": {
            "messages": [
                "You analyze the body of this Selkio Anathei...",
                "His exposed dark muscles have a simple but efficient structure.",
                "This must be the work of a skilled surgeon...",
                "By studying it, your knowledge of anatomy increases.",
                "On the body you also find a Messer of Blusqua.",
            ],
            "actions": [
                {"type": "give_exp", "amount": 5},
                {"type": "add_equipment", "item": "messer_blusqua"},
            ],
            "repeat": {
                "messages": [
                    "You have already studied this body.",
                    "There is nothing more to learn from it."
                ],
                "actions": [None, None]
            }
        }
    },
    
    # Add Maedo Warrior as second enemy type
    {
        "name": "Maedo_Warrior",
        "species": "Maedo",
        "image_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Maedo_32p.png",
        "death_image_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Maedo_32p_morto.png",
        "speed": 80,
        "active": True,
        "sight_range": 150,
        "study_limit": 3,
        "battle_character": {
            "name": "MAEDO WARRIOR",
            "gif_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Mappe\FilesPy\Enemies_GIFs\Maedo_NPC_1_Gif.gif",
            "stats": {
                "rig": [20, 20],
                "res": [30, 30],
                "sta": [14, 14],
                "forz": [10, 10],
                "des": [10, 10],
                "spe": [16, 16],
                "vel": [9, 9]
            },
            "body_parts": [
                {"name": "HEAD", "max_hp": 35, "hp": 35, "elusione": 0.5},
                {"name": "BODY", "max_hp": 80, "hp": 80, "elusione": 1},
                {"name": "RIGHT ARM", "max_hp": 15, "hp": 15, "elusione": 1},
                {"name": "LEFT ARM", "max_hp": 15, "hp": 15, "elusione": 1},
                {"name": "TENTACLE 1", "max_hp": 10, "hp": 10, "elusione": 1},
                {"name": "TENTACLE 2", "max_hp": 10, "hp": 10, "elusione": 1},
                {"name": "RIGHT LEG", "max_hp": 20, "hp": 20, "elusione": 1},
                {"name": "LEFT LEG", "max_hp": 20, "hp": 20, "elusione": 1}
            ],
            "moves": [
                {
                    "name": "Small Zap",
                    "type": "ATK",
                    "scaling": {"forz": 0, "des": 0, "spe": 1},
                    "effects": [["stun", 2, 2, 0]],
                    "requirements": ["NEEDS TENTACLE", "TARGET BODY"],
                    "elements": ["ELECTRIC"],
                    "accuracy": 90
                },
                {
                    "name": "Electro Scratch",
                    "type": "ATK",
                    "scaling": {"forz": 1, "des": 0, "spe": 3},
                    "effects": [["paralysis", 1, 1, 0]],
                    "requirements": ["NEEDS ARM"],
                    "elements": ["ELECTRIC"],
                    "accuracy": 90
                },
                {
                    "name": "Electro Kick",
                    "type": "ATK",
                    "scaling": {"forz": 1, "des": 0, "spe": 3},
                    "effects": [["fry_Neurons", 2, 2, 0]],
                    "requirements": ["NEEDS 2 LEGS", "TARGET BODY"],
                    "elements": ["ELECTRIC"],
                    "accuracy": 90
                },
                {
                    "name": "Static Charge",
                    "type": "BUF",  # Self-buff for enemy
                    "scaling": {"forz": 0, "des": 0, "spe": 0},
                    "effects": [["buf_spe", 2, 1, 0]],
                    "requirements": ["NEEDS 2 ARMS"],
                    "accuracy": 90
                },
            ]
        },
        "skills": ["exploit_stun"],  # Enemy memory skills from Skills_Config.py
        "limit_script": {
            "messages": [
                "The basic structure of the Maedo's electric organs has been thoroughly studied.",
                "No new insights can be gained."
            ],
            "actions": [None, None]
        },
        "script": {
            "messages": [
                "You examine the Maedo Warrior's bio-electric structures...",
                "They were trained to generate powerful electric shocks.",
                "Your understanding of bio-electricity increases.",
            ],
            "actions": [
                {"type": "give_exp", "amount": 7},
            ],
            "repeat": {
                "messages": [
                    "You have already studied this body.",
                    "There is nothing more to learn from it."
                ],
                "actions": [None, None]
            }
        }
    },
    {
        "name": "Blubbertone",
        "species": "Maedo",
        "image_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Maedo_32p.png",
        "death_image_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Maedo_32p_morto.png",
        "speed": 100,
        "active": True,
        "sight_range": 150,
        "study_limit": 1,
        "battle_character": {
            "name": "BLUBBERTONE",
            "gif_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Mappe\FilesPy\Enemies_GIFs\Blubbertone_GIF.gif",
            "stats": {
                "rig": [20, 20],
                "res": [50, 50],
                "sta": [22, 22],
                "forz": [20, 20],
                "des": [16, 16],
                "spe": [16, 16],
                "vel": [9, 9]
            },
            "body_parts": [
                {"name": "HEAD", "max_hp": 100, "hp": 100, "elusione": 0.5},
                {"name": "BODY", "max_hp": 800, "hp": 800, "elusione": 1},
                {"name": "RIGHT ARM", "max_hp": 40, "hp": 40, "elusione": 1},
                {"name": "LEFT ARM", "max_hp": 40, "hp": 40, "elusione": 1},
                {"name": "TENTACLE 1", "max_hp": 20, "hp": 20, "elusione": 1},
                {"name": "TENTACLE 2", "max_hp": 20, "hp": 20, "elusione": 1},
                {"name": "TENTACLE 3", "max_hp": 20, "hp": 20, "elusione": 1},
                {"name": "TENTACLE 4", "max_hp": 20, "hp": 20, "elusione": 1},
                {"name": "TENTACLE 5", "max_hp": 20, "hp": 20, "elusione": 1},
            ],
            "moves": [
                {
                    "name": "Tentacle Slam",
                    "type": "ATK",
                    "scaling": {"forz": 1, "des": 1, "spe": 0},
                    "effects": [["confusion", 1, 1, 0]],
                    "requirements": ["NEEDS TENTACLE", "TARGET BODY"],
                    "elements": ["IMPACT"],
                    "accuracy": 50
                },
                {
                    "name": "Claw Swipe",
                    "type": "ATK",
                    "scaling": {"forz": 2, "des": 2, "spe": 0},
                    "effects": [["bleed", 2, 2, 0]],
                    "requirements": ["NEEDS ARM"],
                    "elements": ["CUT"],
                    "accuracy": 90
                },
                {
                    "name": "Metalhead",
                    "type": "ATK",
                    "scaling": {"forz": 5, "des": 1, "spe": 0},
                    "effects": [["confusion", 3, 3, 0]],
                    "requirements": ["NEEDS BODY", "TARGET BODY"],
                    "elements": ["IMPACT"],
                    "accuracy": 50
                },
                {
                    "name": "Acid Spray",
                    "type": "ATK",
                    "scaling": {"forz": 0, "des": 0, "spe": 3},
                    "effects": [["acid", 2, 2, 0]],
                    "requirements": ["NEEDS HEAD"],
                    "elements": ["SPRAY"],
                    "accuracy": 90
                },
            ]
        },
        "skills": ["fiery_presence"],  # Enemy memory skills from Skills_Config.py
        "limit_script": {
            "messages": [
                "The Rathos lays dead at your feet...",
                "Its body is a mass of tentacles surmounting a central core.",
                "the core is protected by a thick layer of chitin, so hard it feels almost metallic.",
            ],
            "actions": [None, None]
        },
        "script": {
            "messages": [
                "The Rathos lays dead at your feet...",
                "Its body is a mass of tentacles surmounting a central core.",
                "the core is protected by a thick layer of chitin, so hard it feels almost metallic.",
                "You've never seen a creature like this before...",
                "By studying it, your knowledge of anatomy greatly increases."
            ],
            "actions": [
                {"type": "give_exp", "amount": 20},
            ],
            "repeat": {
                "messages": [
                    "You have already studied this body.",
                    "There is nothing more to learn from it."
                ],
                "actions": [None, None]
            }
        }
    },
    
    # Add Sapifer Warrior with spore-based Effect-on-Hit buffs for testing
    {
        "name": "Sapifer_Warrior",
        "species": "Sapifer",
        "image_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Sapifer_32p.png",  
        "death_image_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Sapifer_32p_morto.png", 
        "speed": 120,
        "active": True,
        "sight_range": 180,
        "study_limit": 2,
        "battle_character": {
            "name": "SAPIFER WARRIOR",
            "gif_path": r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Mappe\FilesPy\Enemies_GIFs\Sapifer_NPC_1_Gif.gif",  # Using Sapifer GIF
            "stats": {
                "rig": [20, 20],
                "res": [40, 40],
                "sta": [14, 14],
                "forz": [8, 8],
                "des": [12, 12],
                "spe": [18, 18],
                "vel": [15, 15]
            },
            "body_parts": [
                {"name": "HEAD", "max_hp": 40, "hp": 40, "elusione": 0.6},
                {"name": "RIGHT ARM", "max_hp": 18, "hp": 18, "elusione": 1},
                {"name": "LEFT ARM", "max_hp": 18, "hp": 18, "elusione": 1},
                {"name": "BODY", "max_hp": 120, "hp": 120, "elusione": 1},
                {"name": "RIGHT LEG", "max_hp": 25, "hp": 25, "elusione": 1},
                {"name": "LEFT LEG", "max_hp": 25, "hp": 25, "elusione": 1}
            ],
            "moves": [
                {
                    "name": "Spore Burst",
                    "type": "ATK",
                    "scaling": {"forz": 0, "des": 1, "spe": 2},
                    "effects": [["poison", 3, 3, 0], ["fine_dust", 1, 1, 0]],
                    "requirements": ["TARGET BODY"],
                    "elements": ["SPORES"],
                    "accuracy": 90
                },
                {
                    "name": "Hooking Strike",
                    "type": "ATK",
                    "scaling": {"forz": 0, "des": 3, "spe": 1},
                    "effects": [["poison", 1, 1, 0]],
                    "requirements": ["NEEDS ARM"],
                    "elements": ["CUT"],
                    "accuracy": 90
                },
                {
                    "name": "Poision Spores",
                    "type": "BUF",  # Self-buff for enemy
                    "scaling": {"forz": 0, "des": 0, "spe": 0},
                    "effects": [["poison_spores", 1, 1, 0]],
                    "requirements": ["NEEDS 2 LEGS"],
                    "elements": ["SPORES"],
                    "accuracy": 100
                },

            ]
        },
        "skills": ["exploit_wounds"],  # Enemy memory skills from Skills_Config.py
        "limit_script": {
            "messages": [
                "You have studied enough Sapifers to understand their bio-structures.",
                "Further analysis provides no new information."
            ],
            "actions": [None, None]
        },
        "script": {
            "messages": [
                "You examine the Sapifer Warrior's plant-producing organs...",
                "The bushes on their bodies have expertly crafted structures.",
                "They allow for the growth of several different types of spores.",
            ],
            "actions": [
                {"type": "give_exp", "amount": 10},
            ],
            "repeat": {
                "messages": [
                    "You have already studied this body.",
                    "There is nothing more to learn from it."
                ],
                "actions": [None, None]
            }
        }
    }
    # ... more NPCs can be easily added with the same structure ...
]

# Factory function to create NPCs from ENEMIES_DATA
def create_npc_from_data(data, pos, groups):
    # Create battle character using generic function
    battle_character = None
    if "battle_character" in data:
        try:
            battle_character = create_enemy_battle_character(data)
            # Add moves to the character using generic function
            if battle_character:
                add_moves_to_enemy_character(battle_character, data)
            print(f"[EnemiesList] Created battle character for {data['name']}: {battle_character.name if battle_character else 'None'}")
        except Exception as e:
            print(f"[EnemiesList] Error creating battle character for {data['name']}: {e}")
            battle_character = None
    
    return NPC(
        name=data["name"],
        image_path=data["image_path"],
        death_image_path=data.get("death_image_path", None),
        pos=pos,
        speed=data.get("speed", 2),
        active=data.get("active", True),
        sight_range=data.get("sight_range", 30),
        groups=groups,
        battle_character=battle_character
    )

# Helper: get enemy data by name
def get_enemy_data_by_name(name):
    for data in ENEMIES_DATA:
        if data["name"] == name:
            return data
    return None
