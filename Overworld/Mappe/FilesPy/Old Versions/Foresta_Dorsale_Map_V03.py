import pygame, sys
from pytmx.util_pygame import load_pygame

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        
        # Load character spritesheet
        character_spritesheet = pygame.image.load(r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Scheletro_daun.png").convert_alpha()
        
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
    
    def update(self, keys, collision_tiles, tmx_data):
        # Handle movement
        self.is_moving = False
        new_pos = self.pos.copy()
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_pos.x -= self.speed
            self.direction = 'left'
            self.is_moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_pos.x += self.speed
            self.direction = 'right'
            self.is_moving = True
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            new_pos.y -= self.speed
            self.direction = 'up'
            self.is_moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_pos.y += self.speed
            self.direction = 'down'
            self.is_moving = True
        
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
        self.box_height = 80
        self.box_y = 5  # 5 pixels from top (close to top)
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
        """Draw the message box and text with a purple outline"""
        if self.is_visible and self.message:
            # Create semi-transparent black surface for the message box
            text_surface = self.font.render(self.message, True, (255, 255, 255))  # White text
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()

            # Calculate box dimensions
            box_width = text_width + (self.padding * 2)
            box_x = (self.screen_width - box_width) // 2  # Center horizontally

            # Create the semi-transparent box
            box_surface = pygame.Surface((box_width, self.box_height))
            box_surface.set_alpha(180)  # Semi-transparent (0=fully transparent, 255=opaque)
            box_surface.fill((0, 0, 0))  # Black background

            # Draw the box
            screen.blit(box_surface, (box_x, self.box_y))

            # Draw the purple outline (3px thick)
            outline_rect = pygame.Rect(box_x, self.box_y, box_width, self.box_height)
            purple = (128, 0, 128)
            for i in range(3):
                pygame.draw.rect(screen, purple, outline_rect.inflate(i*2, i*2), 1)

            # Draw the text centered in the box
            text_x = box_x + self.padding
            text_y = self.box_y + (self.box_height - text_height) // 2
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

# --- Music System ---
import pygame.mixer
pygame.mixer.init()
try:
    pygame.mixer.music.load(r"C:\Users\franc\Desktop\Afterdeath_RPG\Musics\Battle-Walzer.MP3")
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

    # Handle player movement and animation
    keys = pygame.key.get_pressed()
    player.update(keys, collision_tiles, tmx_data)

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
    for obj_sprite in object_group:
        scaled_surface = pygame.transform.scale(obj_sprite.image,
            (int(obj_sprite.image.get_width() * camera.zoom_factor),
             int(obj_sprite.image.get_height() * camera.zoom_factor)))
        sprite_rect = camera.apply(obj_sprite)

        render_objects.append({
            'type': 'object',
            'depth_y': obj_sprite.depth_y,
            'surface': scaled_surface,
            'rect': sprite_rect
        })

    # Sort by depth_y and render
    render_objects.sort(key=lambda obj: obj['depth_y'])

    for obj in render_objects:
        screen.blit(obj['surface'], (obj['rect'].x, obj['rect'].y))

    # Step 3: Draw UI elements (message display) on top of everything
    message_display.draw(screen)

    pygame.display.flip()