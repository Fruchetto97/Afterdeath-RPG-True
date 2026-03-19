#IMPORTS
import pygame
import sys
from pytmx.util_pygame import load_pygame

# Initialize pygame
pygame.init()

# Screen settings
screen_width = 1920
screen_height = 1080
windowed_width = 1280  # Smaller windowed size
windowed_height = 720  # 16:9 aspect ratio maintained

# Start in windowed mode - use normal window controls to maximize/minimize
screen = pygame.display.set_mode((windowed_width, windowed_height), pygame.RESIZABLE)
current_width = windowed_width
current_height = windowed_height

pygame.display.set_caption("Foresta Dorsale Map")
clock = pygame.time.Clock()

# Load map
tmx_data = load_pygame(r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Mappe\Exports\Foresta_Dorsale_01.tmx")

# Load character sprite
character_spritesheet = pygame.image.load(r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\characters\Scheletro_daun.png").convert_alpha()

# Character animation setup
sprite_width = character_spritesheet.get_width() // 4  # 4 columns
sprite_height = character_spritesheet.get_height() // 4  # 4 rows

# Extract all frames from the spritesheet
character_frames = {}
directions = ['down', 'right', 'up', 'left']
for row, direction in enumerate(directions):
    character_frames[direction] = []
    for col in range(4):  # 4 frames per direction
        frame_rect = pygame.Rect(col * sprite_width, row * sprite_height, sprite_width, sprite_height)
        frame = character_spritesheet.subsurface(frame_rect)
        character_frames[direction].append(frame)

# Character properties
character_x = 600  # Starting x position
character_y = 40  # Starting y position
character_speed = 5
character_direction = 'down'  # Current facing direction
character_frame = 0  # Current animation frame
animation_speed = 0.2  # Animation speed (lower = slower)
animation_timer = 0
is_moving = False

# Camera properties
camera_x = 0
camera_y = 0
# Use the actual screen dimensions
zoom_factor = 2.0  # 100% more zoomed in (2x zoom)
map_width = tmx_data.width * tmx_data.tilewidth
map_height = tmx_data.height * tmx_data.tileheight

# Get all map layers
tile_layers = []  # All tile layers (rendered under character)
all_objects = []  # All objects from the map (rendered with depth sorting)
collision_tiles = set()  # Set to store collision tile positions

# Get all objects directly from tmx_data
for obj in tmx_data.objects:
    print(f"Found object: '{obj.name}' at ({obj.x}, {obj.y}) with size ({obj.width}, {obj.height}), gid: {getattr(obj, 'gid', 'None')}")
    all_objects.append(obj)

for layer in tmx_data.layers:
    if hasattr(layer, 'tiles'):  # Tile layers
        print(f"Found tile layer: '{layer.name}'")
        # Check for collision layers
        if 'collision' in layer.name.lower():
            # Add collision tiles
            for x, y, gid in layer:
                if gid:  # If there's a tile here
                    collision_tiles.add((x, y))
            print(f"Collision layer '{layer.name}' found with {len([1 for x, y, gid in layer if gid])} collision tiles")
            
            # Only render visible collision layers
            if 'invisible' not in layer.name.lower():
                tile_layers.append(layer)
        else:
            # Regular tile layer - always render under character
            tile_layers.append(layer)
            
        # Check individual tiles for collision properties
        for x, y, gid in layer:
            if gid:
                tile_properties = tmx_data.get_tile_properties_by_gid(gid)
                if tile_properties and tile_properties.get('collision', False):
                    collision_tiles.add((x, y))
    
    elif hasattr(layer, 'objects'):  # Object layers
        print(f"Found object layer: '{layer.name}' with {len(layer.objects)} objects")
        # Add objects from this layer too
        for obj in layer.objects:
            all_objects.append(obj)

print(f"Total collision tiles loaded: {len(collision_tiles)}")
print(f"Total tile layers: {len(tile_layers)}")
print(f"Total objects found: {len(all_objects)}")

# Function to check collision at a specific position
def check_collision(x, y, width, height):
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

def get_character_hitbox(char_x, char_y, char_image):
    """Calculate the character's 1x1 tile hitbox centered in the lower half"""
    # Character sprite dimensions
    sprite_width = char_image.get_width()
    sprite_height = char_image.get_height()
    
    # Hitbox dimensions (1 tile)
    hitbox_width = tmx_data.tilewidth
    hitbox_height = tmx_data.tileheight
    
    # Center the hitbox horizontally within the sprite
    hitbox_x = char_x + (sprite_width - hitbox_width) // 2
    
    # Position hitbox in the lower half of the sprite
    # Start at 3/4 down the sprite height
    hitbox_y = char_y + (sprite_height * 3 // 4) - (hitbox_height // 2)
    
    return hitbox_x, hitbox_y, hitbox_width, hitbox_height

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            # Handle window resizing
            current_width = event.w
            current_height = event.h
            screen = pygame.display.set_mode((current_width, current_height), pygame.RESIZABLE)
    
    # Handle character movement and animation
    keys = pygame.key.get_pressed()
    new_x = character_x
    new_y = character_y
    is_moving = False
    
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        new_x -= character_speed
        character_direction = 'left'
        is_moving = True
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        new_x += character_speed
        character_direction = 'right'
        is_moving = True
    elif keys[pygame.K_UP] or keys[pygame.K_w]:
        new_y -= character_speed
        character_direction = 'up'
        is_moving = True
    elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
        new_y += character_speed
        character_direction = 'down'
        is_moving = True
    
    # Get current character image for collision detection
    current_character_image = character_frames[character_direction][character_frame]
    
    # Calculate the character's hitbox for collision detection
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(new_x, new_y, current_character_image)
    
    # Check collision using the smaller hitbox instead of full sprite
    if not check_collision(hitbox_x, hitbox_y, hitbox_width, hitbox_height):
        # Keep character within map bounds using full sprite dimensions for boundary check
        character_width = current_character_image.get_width()
        character_height = current_character_image.get_height()
        new_x = max(0, min(new_x, map_width - character_width))
        new_y = max(0, min(new_y, map_height - character_height))
        
        # Update character position only if no collision
        character_x = new_x
        character_y = new_y
    else:
        # If there's a collision, stop the movement animation
        is_moving = False
    
    # Update animation
    if is_moving:
        animation_timer += animation_speed
        if animation_timer >= 1.0:
            character_frame = (character_frame + 1) % 3 + 1  # Cycle through frames 1, 2, 3
            animation_timer = 0
    else:
        character_frame = 0  # Idle frame
        animation_timer = 0
    
    # Get current character image (may have changed due to animation)
    current_character_image = character_frames[character_direction][character_frame]
    
    # Update camera to keep character centered (accounting for zoom)
    camera_x = character_x - (current_width / zoom_factor) // 2 + character_width // 2
    camera_y = character_y - (current_height / zoom_factor) // 2 + character_height // 2
    
    # Keep camera within map bounds (accounting for zoom)
    camera_x = max(0, min(camera_x, map_width - (current_width / zoom_factor)))
    camera_y = max(0, min(camera_y, map_height - (current_height / zoom_factor)))

    # Clear screen
    screen.fill((0, 0, 0))
    
    # Step 1: Draw all tile layers (always below character)
    for layer in tile_layers:
        for x, y, surface in layer.tiles():
            if surface:
                # Apply camera offset to tile positions
                tile_x = (x * tmx_data.tilewidth) - camera_x
                tile_y = (y * tmx_data.tileheight) - camera_y
                
                # Only draw tiles that are visible on screen (accounting for zoom)
                if (-tmx_data.tilewidth * zoom_factor <= tile_x * zoom_factor <= current_width and 
                    -tmx_data.tileheight * zoom_factor <= tile_y * zoom_factor <= current_height):
                    # Scale the surface for zoom
                    scaled_surface = pygame.transform.scale(surface, 
                        (int(tmx_data.tilewidth * zoom_factor), int(tmx_data.tileheight * zoom_factor)))
                    screen.blit(scaled_surface, (tile_x * zoom_factor, tile_y * zoom_factor))
    
    # Step 2: Create depth-sorted rendering for character and objects
    render_objects = []
    
    # Calculate character's base Y position (bottom of the hitbox)
    hitbox_x, hitbox_y, hitbox_width, hitbox_height = get_character_hitbox(character_x, character_y, current_character_image)
    character_base_y = hitbox_y + hitbox_height
    
    # Add character to render list
    character_screen_x = (character_x - camera_x) * zoom_factor
    character_screen_y = (character_y - camera_y) * zoom_factor
    scaled_character = pygame.transform.scale(current_character_image, 
        (int(current_character_image.get_width() * zoom_factor), int(current_character_image.get_height() * zoom_factor)))
    
    render_objects.append({
        'type': 'character',
        'y': character_base_y,
        'surface': scaled_character,
        'x': character_screen_x,
        'screen_y': character_screen_y
    })
    
    # Step 3: Add objects with depth sorting
    for obj in all_objects:
        # Calculate object position relative to camera
        obj_x = obj.x - camera_x
        obj_y = obj.y - camera_y
        
        # Only process objects that are visible on screen (accounting for zoom)
        if (-obj.width * zoom_factor <= obj_x * zoom_factor <= current_width and 
            -obj.height * zoom_factor <= obj_y * zoom_factor <= current_height):
            
            # Check if object has a tile/gid (sprite object)
            if hasattr(obj, 'gid') and obj.gid:
                # Get the tile surface from the tileset
                tile_surface = tmx_data.get_tile_image_by_gid(obj.gid)
                
                if tile_surface:
                    # For tile objects in Tiled, the position (obj.x, obj.y) represents the BOTTOM-LEFT corner
                    # We need to adjust for pygame's TOP-LEFT rendering system
                    render_x = obj_x
                    render_y = obj_y - obj.height  # Move up by object height
                    
                    # Scale the surface for zoom
                    scaled_surface = pygame.transform.scale(tile_surface, 
                        (int(obj.width * zoom_factor), int(obj.height * zoom_factor)))
                    
                    # For depth sorting, use the bottom Y position (original obj.y)
                    object_base_y = obj.y
                    
                    render_objects.append({
                        'type': 'object',
                        'y': object_base_y,
                        'surface': scaled_surface,
                        'x': render_x * zoom_factor,
                        'screen_y': render_y * zoom_factor
                    })
            else:
                # Geometric objects (rectangles) use TOP-LEFT positioning - no adjustment needed
                object_surface = pygame.Surface((int(obj.width * zoom_factor), int(obj.height * zoom_factor)))
                object_surface.fill((0, 255, 0))  # Green color for geometric objects
                object_surface.set_alpha(128)  # Semi-transparent
                
                object_base_y = obj.y + obj.height
                render_objects.append({
                    'type': 'geometric_object',
                    'y': object_base_y,
                    'surface': object_surface,
                    'x': obj_x * zoom_factor,
                    'screen_y': obj_y * zoom_factor
                })
    
    # Sort objects by Y position and render them
    render_objects.sort(key=lambda obj: obj['y'])
    
    for obj in render_objects:
        screen.blit(obj['surface'], (obj['x'], obj['screen_y']))
    
    # Update display
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

