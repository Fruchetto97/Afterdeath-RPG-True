"""Script to verify all weapons have proper weapon_type values after comprehensive fix"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Overworld', 'Mappe', 'FilesPy'))

from Player_Equipment import ALL_EQUIPMENT

def verify_all_weapon_types():
    """Verify that all weapons have proper weapon_type values"""
    print("=== COMPREHENSIVE WEAPON TYPE VERIFICATION ===")
    print(f"Total equipment items in ALL_EQUIPMENT: {len(ALL_EQUIPMENT)}")
    
    weapons_found = 0
    none_weapon_types = 0
    weapon_type_counts = {}
    
    for i, equipment in enumerate(ALL_EQUIPMENT):
        print(f"Item {i}: {equipment.name} - Type: {getattr(equipment, 'type', 'No type')}")
        
        if hasattr(equipment, 'type') and equipment.type == 'weapon':
            weapons_found += 1
            print(f"Weapon: {equipment.name}")
            print(f"  - weapon_type: {equipment.weapon_type}")
            print(f"  - stamina_bonus: {getattr(equipment, 'stamina_bonus', 'Not set')}")
            
            if equipment.weapon_type is None:
                none_weapon_types += 1
                print("  ⚠️  WARNING: weapon_type is None!")
            else:
                # Count weapon types
                if equipment.weapon_type not in weapon_type_counts:
                    weapon_type_counts[equipment.weapon_type] = 0
                weapon_type_counts[equipment.weapon_type] += 1
                print(f"  ✅ weapon_type: {equipment.weapon_type}")
            print()
    
    print(f"\n=== SUMMARY ===")
    print(f"Total weapons found: {weapons_found}")
    print(f"Weapons with None weapon_type: {none_weapon_types}")
    print(f"Weapon type distribution: {weapon_type_counts}")
    
    if none_weapon_types == 0:
        print("✅ ALL WEAPONS HAVE PROPER WEAPON_TYPE!")
    else:
        print(f"❌ {none_weapon_types} weapons still have None weapon_type")

    # Check specific weapons mentioned in battle system
    print("\n=== SPECIFIC WEAPON CHECK ===")
    for equipment in ALL_EQUIPMENT:
        if equipment.name in ["Marrow Pair", "Messer of Blusqua"]:
            print(f"{equipment.name}: weapon_type = {equipment.weapon_type}")

if __name__ == "__main__":
    verify_all_weapon_types()