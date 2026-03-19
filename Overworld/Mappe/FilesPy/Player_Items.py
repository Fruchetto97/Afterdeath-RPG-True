import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pygame


# Item class
class Item:
    def __init__(self, name, icon_path, image_path, item_type, description, short_description, value, weight, script=None, **kwargs):
        self.name = name
        self.icon_path = icon_path
        self.image_path = image_path
        self.type = item_type  # 'MISC', 'FOOD', or 'KEY'
        self.description = description
        self.short_description = short_description
        self.icon = None
        self.image = None
        self.value = value if value is not None else 10  # Default value to 0 if not provided
        self.weight = weight if weight is not None else 1
        self.script = script  # Function or script to execute when item is used
        
        # Food-specific attributes
        self.reserve_restored = kwargs.get('reserve_restored', 0)  # Amount of reserve restored for food items

        
        # Validate item type
        valid_types = ['MISC', 'FOOD', 'KEY']
        if self.type not in valid_types:
            pass  # Silently ignore invalid types in production

    def use_item(self, player_stats=None, count=1):
        """Execute the item's script when used."""
        if self.script:
            try:
                results = []
                for i in range(count):
                    if callable(self.script):
                        # For food items using the universal use_food function, pass the item as well
                        if self.type == 'FOOD' and self.script.__name__ == 'use_food':
                            result = self.script(player_stats, self)
                        else:
                            result = self.script(player_stats)
                        
                        if isinstance(result, dict):
                            results.append(result)
                        else:
                            # Legacy support for scripts that don't return dict
                            results.append({'success': True, 'message': f"Used {self.name}", 'show_message': False})
                    else:
                        return {'success': False, 'message': f"Script error for {self.name}", 'show_message': True}
                
                # Combine results - if any failed, the whole usage fails
                overall_success = all(r.get('success', True) for r in results)
                
                # For multiple uses, use the message from the LAST result to show final state
                if count > 1:
                    message = results[-1].get('message', f"Used {count}x {self.name}") if results else f"Used {count}x {self.name}"
                    show_message = results[-1].get('show_message', False) if results else False
                    
                    # Update message to reflect multiple uses for items that restore things
                    if "restored " in message and overall_success:
                        message = message.replace("restored ", f"restored {count}x ")
                else:
                    # Single use - use the first (and only) result
                    message = results[0].get('message', f"Used {count}x {self.name}") if results else f"Used {count}x {self.name}"
                    show_message = results[0].get('show_message', False) if results else False
                
                return {'success': overall_success, 'message': message, 'show_message': show_message}
                
            except Exception as e:
                return {'success': False, 'message': f"Error using {self.name}: {str(e)}", 'show_message': True}
        else:
            return {'success': False, 'message': f"No script defined for {self.name}", 'show_message': True}

    def load_images(self):
        """Load icon and image from their paths, if not already loaded."""
        if self.icon is None and self.icon_path:
            try:
                self.icon = pygame.image.load(self.icon_path).convert_alpha()
            except Exception as e:
                self.icon = None
        if self.image is None and self.image_path:
            try:
                self.image = pygame.image.load(self.image_path).convert_alpha()
            except Exception as e:
                self.image = None

    def __repr__(self):
        return f"<Item name={self.name} type={self.type} short_desc={self.short_description[:20]}...>"


# PlayerItems class
class PlayerItems:
    def __init__(self, name):
        self.name = name
        self.items = {}  # Dictionary of {item_name: {'item': Item, 'count': int}}

    def add_item(self, item, count=1):
        """Add an item to the player's inventory."""
        if isinstance(item, Item):
            if item.name in self.items:
                self.items[item.name]['count'] += count
            else:
                self.items[item.name] = {'item': item, 'count': count}
        else:
            pass  # Silently ignore non-item objects

    def remove_item(self, item, count=1):
        """Remove an item from the player's inventory."""
        if item.name in self.items:
            if self.items[item.name]['count'] > count:
                self.items[item.name]['count'] -= count
                return True
            elif self.items[item.name]['count'] == count:
                del self.items[item.name]
                return True
            else:
                return False
        else:
            return False

    def remove_item_by_name(self, item_name, count=1):
        """Remove an item from inventory by name (removes specified count)."""
        if item_name in self.items:
            item = self.items[item_name]['item']
            return self.remove_item(item, count)
        return False

    def get_item_list(self):
        """Get all unique items in the inventory with their counts."""
        result = []
        for item_data in self.items.values():
            # Add count attribute to item for display purposes
            item = item_data['item']
            item.count = item_data['count']
            result.append(item)
        return result

    def get_items_by_type(self, item_type):
        """Get all items of a specific type."""
        result = []
        for item_data in self.items.values():
            item = item_data['item']
            if item.type == item_type:
                item.count = item_data['count']
                result.append(item)
        return result

    def has_item(self, item_name):
        """Check if the player has a specific item by name."""
        return item_name in self.items

    def get_item_by_name(self, item_name):
        """Get the first item with the specified name, or None if not found."""
        if item_name in self.items:
            item = self.items[item_name]['item']
            item.count = self.items[item_name]['count']
            return item
        return None

    def get_item_count(self, item_name):
        """Get the count of a specific item."""
        if item_name in self.items:
            return self.items[item_name]['count']
        return 0

    def count_items_by_type(self):
        """Get a count of items by type."""
        counts = {'MISC': 0, 'FOOD': 0, 'KEY': 0}
        for item_data in self.items.values():
            item_type = item_data['item'].type
            if item_type in counts:
                counts[item_type] += item_data['count']
        return counts

    def get_inventory_summary(self):
        """Get a formatted summary of the inventory."""
        if not self.items:
            return f"{self.name}'s inventory is empty."
        
        counts = self.count_items_by_type()
        summary = f"=== {self.name}'s Inventory ===\n"
        summary += f"Total items: {sum(item_data['count'] for item_data in self.items.values())}\n"
        
        for item_type, count in counts.items():
            if count > 0:
                summary += f"{item_type}: {count} items\n"
        
        summary += "\nItems:\n"
        for item_data in self.items.values():
            item = item_data['item']
            count = item_data['count']
            summary += f"  • {item.name} x{count} ({item.type}): {item.short_description}\n"
        
        return summary

    def clear_inventory(self):
        """Remove all items from inventory."""
        count = len(self.items)
        self.items.clear()
        print(f"[PlayerItems] Cleared {count} items for {self.name}")


# Global dictionary to hold all players' items
player_items = {}

def get_player_items(player_name):
    """Return the items list for the specified player name, or None if not found."""
    player = player_items.get(player_name)
    if player:
        return player.get_item_list()
    return None

# Example item scripts
def use_spacchiotti(player_stats):
    """Script for using Spacchiotti (currency - cannot be consumed)"""
    return {
        'success': False,
        'message': "Spacchiotti cannot be used directly. Use them for trading.",
        'show_message': True
    }

def use_black_ooze(player_stats):
    """Script for using Black Ooze (key item)"""
    if player_stats:
        # Simulate some effect, e.g., temporary stat boost or crafting material
        return {
            'success': True,
            'message': "You ingest the Black Ooze. It feels strange but invigorating.",
            'show_message': True
        }
    else:
        return {
            'success': False,
            'message': "Black Ooze would have an effect (no player stats available)",
            'show_message': True
        }

def use_mnemonic_fruit(player_stats):
    """Script for using Mnemonic Fruit (increases ability points)"""
    if player_stats:
        ability_points_gained = 1
        player_stats.ability_points += ability_points_gained
        message = f"The Mnemonic Fruit enhances your memory. Total ability points: {player_stats.ability_points}"
        return {
            'success': True,
            'message': message,
            'show_message': True
        }
    else:
        message = "The Mnemonic Fruit would enhance your memory (no player stats available)"
        return {
            'success': False,
            'message': message,
            'show_message': True
        }

def use_food(player_stats, item=None):
    """Universal script for using food items that restore reserve"""
    if not item:
        return {
            'success': False,
            'message': "No item provided to use_food function",
            'show_message': True
        }
    
    if player_stats:
        reserve_restore = getattr(item, 'reserve_restored', 0)
        if reserve_restore <= 0:
            return {
                'success': False,
                'message': f"{item.name} doesn't restore any reserve",
                'show_message': True
            }
        
        old_reserve = player_stats.reserve
        player_stats.regen_reserve(reserve_restore)
        restored_amount = player_stats.reserve - old_reserve
        return {
            'success': True,
            'message': f"{item.name} restored {restored_amount} reserve. Current reserve: {player_stats.reserve}/{player_stats.max_reserve}",
            'show_message': True
        }
    else:
        reserve_restore = getattr(item, 'reserve_restored', 0)
        return {
            'success': False,
            'message': f"{item.name} would restore {reserve_restore} reserve (no player stats available)",
            'show_message': True
        }

# Example items for demonstration
example_misc_items = [
    Item(
        "Spacchiotti",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Misc\\Spacchiotti_Icon.png",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Misc\\Spacchiotti_Image.png",
        'MISC',
        "Made out of the same material of the World Altars, the Green Ambresite, the Spacchiotti are the main currency used in the Dethrovia continent." \
        "The Green Ambresite can only be obtained by destroying the altars or adventuring in the depths of the Network Caves, far beneath the surface. This " \
        "metal can also be used to forge Equipment of medium quality. For this reason the Spacchiotti are universally considered precious, and accepted as a " \
        "form of payment almost everywhere.",
        "Currency used all over the continent.",
        1,  # value
        10.3,  # weight
        use_spacchiotti  # script
    ),
]

example_food_items = [
    Item(
        "Red Rathos Meat",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Meat_Red.png",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Meat_Red.png",
        'FOOD',
        "Red Rathos Meat, tough but nutritious. Restores some Reserve.",
        "Nutritious Red Rathos Meat chunk.",
        5,  # value
        250,  # weight
        use_food,  # script
        reserve_restored=15  # Amount of reserve this food restores
    ),
    Item(
        "Green Rathos Meat",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Meat_Green.png",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Meat_Green.png",
        'FOOD',
        "Green Rathos Meat, tender and juicy. Restores a good amount of Reserve.",
        "Juicy Green Rathos Meat chunk.",
        7,  # value
        250,  # weight
        use_food,  # script
        reserve_restored=20  # Amount of reserve this food restores
    ),
    Item(
        "Purple Rathos Meat",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Meat_Purple.png",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Meat_Purple.png",
        'FOOD',
        "Purple Rathos Meat, rich and flavorful. Restores a large amount of Reserve.",
        "Rich Purple Rathos Meat chunk.",
        10,  # value
        250,  # weight
        use_food,  # script
        reserve_restored=30  # Amount of reserve this food restores
    ),
    Item(
        "Red Rathos Pulp",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Pulp_Red.png",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Pulp_Red.png",
        'FOOD',
        "Red pulp coming from the body of a shelled Rathos, squishy and juicy. Restores a good amount of Reserve.",
        "Squishy Red Rathos Pulp.",
        7,  # value
        400,  # weight
        use_food,  # script
        reserve_restored=20  # Amount of reserve this food restores
    ),
    Item(
        "Pink Rathos Pulp",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Pulp_Pink.png",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Food\\Rathos_Pulp_Pink.png",
        'FOOD',
        "Pink pulp coming from the body of a shelled Rathos, squishy and juicy. Restores a large amount of Reserve.",
        "Squishy Pink Rathos Pulp.",
        10,  # value
        400,  # weight
        use_food,  # script
        reserve_restored=30  # Amount of reserve this food restores
    ),
]

example_key_items = [
    Item(
        "Mnemonic Fruit",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Key\\Mnemonic_Fruit_Icon.png",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Key\\Mnemonic_Fruit_Image.png",
        'KEY',
        "A fruit that enhances memory and recall.",
        "Memory-enhancing fruit.",
        0,  # value (key items typically have no monetary value)
        23.5,  # weight
        use_mnemonic_fruit  # script
    ),

        Item(
        "Black Ooze",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Key\\Black_Ooze_Icon.png",
        "C:\\Users\\franc\\Desktop\\Afterdeath_RPG\\Overworld\\Items\\Key\\Black_Ooze_Image.png",
        'KEY',
        "A mysterious black substance with unknown properties, found on the body of a dead Rathos. You could try ingesting it, but it might not be a great idea. Maybe it could be used to craft something if given to a capable person.",
        "black substance of unknown properties.",
        0,  # value (key items typically have no monetary value)
        23.5,  # weight
        use_black_ooze  # script
    ),
]

# ===== AUTOMATED ITEMS REGISTRY =====
# Global list that collects all items automatically
ALL_ITEMS = []

# Add all item types to the registry
ALL_ITEMS.extend(example_misc_items)
ALL_ITEMS.extend(example_food_items) 
ALL_ITEMS.extend(example_key_items)

def get_all_items():
    """Get a list of all items in the game."""
    return ALL_ITEMS.copy()

def find_item_by_name(item_name):
    """Find an item by name from the global registry."""
    for item in ALL_ITEMS:
        if item.name == item_name:
            return item
    return None

# Create main player items
player1_items = PlayerItems("Selkio Guerriero")

# Add example items to player1
for item in example_misc_items:
    player1_items.add_item(item)
# Add some duplicates for testing stacking
for item in example_misc_items:
    player1_items.add_item(item, 3)  # Add 3 more of each misc item

for item in example_food_items:
    player1_items.add_item(item)
# Add some food duplicates
player1_items.add_item(example_food_items[0], 5)  # 5 more dried meat
player1_items.add_item(example_food_items[1], 2)  # 2 more bread

for item in example_key_items:
    player1_items.add_item(item)

# Register player in global dictionary
player_items[player1_items.name] = player1_items

def Clear_Items(player_name=None):
    """Clear items for specified player or main player if None."""
    target = None
    if player_name is None:
        target = player1_items
    else:
        target = player_items.get(player_name)
    if not target:
        print(f"[PlayerItems] Clear_Items: No items object for '{player_name}'")
        return False
    target.clear_inventory()
    return True

# Utility: Load all item images for a list
def load_item_images(item_list):
    """Load images for all items in the list."""
    for item in item_list:
        if hasattr(item, 'load_images'):
            item.load_images()

# Utility: Get the main player's items object
def get_main_player_items():
    """Return the main player's PlayerItems object (player1_items)."""
    return player1_items

# Utility functions for item management
def give_item_to_player(player_name, item):
    """Give an item to a specific player."""
    player_obj = player_items.get(player_name)
    if player_obj:
        player_obj.add_item(item)
        return True
    else:
        return False

def take_item_from_player(player_name, item_name):
    """Take an item from a specific player by name."""
    player_obj = player_items.get(player_name)
    if player_obj:
        return player_obj.remove_item_by_name(item_name)
    else:
        return False

def player_has_item(player_name, item_name):
    """Check if a player has a specific item."""
    player_obj = player_items.get(player_name)
    if player_obj:
        return player_obj.has_item(item_name)
    else:
        return False

def get_all_player_inventories():
    """Get a summary of all players' inventories."""
    if not player_items:
        return "No players found."
    
    summary = "=== All Player Inventories ===\n"
    for player_name, player_obj in player_items.items():
        summary += f"\n{player_obj.get_inventory_summary()}\n"
    
    return summary

# Debug function to print all items
def debug_print_all_items():
    """Debug function to print all items for all players."""
    for player_name, player_obj in player_items.items():
        print(f"\n[DEBUG] {player_name}'s Items:")
        for item in player_obj.get_item_list():
            print(f"  - {item.name} ({item.type}): {item.short_description}")
