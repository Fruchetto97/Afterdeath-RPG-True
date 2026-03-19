"""
Enemy AI V3 - Simple If-Else Decision Tree
A straightforward AI system using sequential if-else checks for reliable decision making.
"""

import random
import sys
import os
from typing import Any

class AIAction:
    """Represents an AI decision with all necessary information"""
    def __init__(self, action_type, move=None, target_part=None, description="", stamina_cost=0):
        self.action_type = action_type  # 'attack', 'buff', 'regenerate', 'pass'
        self.move = move  # Move object if applicable
        self.target_part = target_part  # Target body part or index
        self.description = description  # Human readable description
        self.stamina_cost = stamina_cost
        self.can_execute = True
        self.execution_reason = "Can execute"

class EnemyAI_V3:
    def __init__(self, enemy, player, battle_menu_instance=None):
        self.enemy = enemy
        self.player = player
        self.battle_menu = battle_menu_instance
        self.turns_since_buff = 0  # Track turns since last buff usage
        self.player_move_history = []  # Track player moves for analysis
        
        # Import stamina costs from battle menu
        try:
            from Battle_Menu_Beta_V18 import DodgeShield_Stamina_Cost, stamina_cost_per_regeneration
            self.dodge_shield_cost = DodgeShield_Stamina_Cost
            self.regen_stamina_cost = stamina_cost_per_regeneration
        except ImportError:
            self.dodge_shield_cost = 3  # Default value
            self.regen_stamina_cost = 3  # Default value
        
        print(f"[AI_V3] Initialized with dodge/shield cost: {self.dodge_shield_cost}, regen cost: {self.regen_stamina_cost}")
    
    def log(self, message):
        """Simple logging function"""
        print(f"[AI_V3] {message}")
    
    def get_available_moves(self):
        """Get all available moves for the enemy"""
        if not hasattr(self.enemy, 'moves') or not self.enemy.moves:
            return []
        return self.enemy.moves
    
    def calculate_move_damage(self, move):
        """Calculate the damage a move would deal"""
        if not hasattr(move, 'danno'):
            return 0
        return move.danno
    
    def get_move_stamina_cost(self, move):
        """Get the stamina cost of a move"""
        if hasattr(move, 'stamina_cost'):
            return move.stamina_cost
        return 3  # Default cost
    
    def can_use_move(self, move, target_part=None):
        """Check if the enemy can use a specific move"""
        # Check stamina
        stamina_cost = self.get_move_stamina_cost(move)
        if self.enemy.sta < stamina_cost:
            return False, f"Insufficient stamina: {self.enemy.sta} < {stamina_cost}"
        
        # Check if it's an attack move and enemy head has >= 2 HP
        if hasattr(move, 'tipo') and move.tipo in ['ATK', 'REA']:
            enemy_head = self.get_body_part_by_name(self.enemy, "HEAD")
            if not enemy_head or enemy_head.p_pvt < 2:
                return False, f"Cannot aim attacks - head HP: {enemy_head.p_pvt if enemy_head else 'missing'}"
        
        # Check move requirements (simplified)
        if hasattr(move, 'reqs') and move.reqs:
            for req in move.reqs:
                if not req:
                    continue
                req_str = str(req).upper().strip()
                
                # Check NEEDS requirements (body parts with >=2 HP)
                if req_str.startswith("NEEDS"):
                    needed_part = req_str.replace("NEEDS", "").strip()
                    if not self.check_body_part_requirement(needed_part):
                        return False, f"Missing required body part: {needed_part}"
                
                # Check TARGET requirements
                if req_str.startswith("TARGET") and target_part:
                    target_req = req_str.replace("TARGET", "").strip()
                    if target_req.upper() not in target_part.name.upper():
                        return False, f"Target requirement not met: {target_req}"
        
        return True, "Can use"
    
    def can_move_target_bodypart(self, move, target_part):
        """Check if a move can target a specific body part based on TARGET requirements"""
        if not hasattr(move, 'reqs') or not move.reqs:
            return True  # No target restrictions
            
        # Check for TARGET requirements
        has_target_req = False
        for req in move.reqs:
            if not req:
                continue
            req_str = str(req).upper().strip()
            
            if req_str.startswith("TARGET"):
                has_target_req = True
                target_req = req_str.replace("TARGET", "").strip()
                if target_req.upper() in target_part.name.upper():
                    return True  # Found matching target requirement
        
        # If move has TARGET requirements but none match, can't use this move on this target
        if has_target_req:
            return False
            
        return True  # No target restrictions
    
    def check_body_part_requirement(self, requirement):
        """Check if enemy has required body parts with >=2 HP and not paralyzed"""
        req = requirement.upper().strip()
        
        def is_part_usable(part):
            """Check if a body part is usable (>=2 HP and not paralyzed)"""
            if part.p_pvt < 2:
                return False
            
            # Check for paralysis effect
            if hasattr(part, 'p_eff') and hasattr(part.p_eff, 'paralysis'):
                paralysis_data = getattr(part.p_eff, 'paralysis')
                if isinstance(paralysis_data, list) and len(paralysis_data) >= 3:
                    level = paralysis_data[1] if len(paralysis_data) > 1 else 0
                    duration = paralysis_data[2] if len(paralysis_data) > 2 else 0
                    if level > 0 and duration > 0:
                        return False  # Body part is paralyzed
            
            return True
        
        if req == "ARM":
            return any(is_part_usable(part) for part in self.enemy.body_parts 
                      if "ARM" in part.name.upper())
        elif req == "2 ARMS":
            arms = [part for part in self.enemy.body_parts 
                   if "ARM" in part.name.upper() and is_part_usable(part)]
            return len(arms) >= 2
        elif req == "LEG":
            return any(is_part_usable(part) for part in self.enemy.body_parts 
                      if "LEG" in part.name.upper())
        elif req == "2 LEGS":
            legs = [part for part in self.enemy.body_parts 
                   if "LEG" in part.name.upper() and is_part_usable(part)]
            return len(legs) >= 2
        elif req == "TENTACLE":
            return any(is_part_usable(part) for part in self.enemy.body_parts 
                      if "TENTACLE" in part.name.upper())
        elif req == "HEAD":
            head = self.get_body_part_by_name(self.enemy, "HEAD")
            return head and is_part_usable(head)
        elif req == "BODY":
            body = self.get_body_part_by_name(self.enemy, "BODY")
            return body and is_part_usable(body)
        
        return True  # Unknown requirement - assume met
    
    def get_body_part_by_name(self, character, name):
        """Get a body part by name"""
        for part in character.body_parts:
            if name.upper() in part.name.upper():
                return part
        return None
    
    def get_body_part_index(self, character, part):
        """Get the index of a body part"""
        for i, body_part in enumerate(character.body_parts):
            if body_part == part:
                return i
        return -1
    
    def calculate_effect_damage_this_turn(self, part):
        """Calculate damage that will be dealt to a body part by effects this turn"""
        total_damage = 0
        
        if hasattr(part, 'p_eff'):
            effects = part.p_eff
            # Check burn, bleed, poison effects
            for effect_name in ['burn', 'bleed', 'poison']:
                if hasattr(effects, effect_name):
                    effect_data = getattr(effects, effect_name)
                    if len(effect_data) >= 3 and effect_data[2] > 0:  # Has duration
                        level = effect_data[1]
                        # Approximate damage per level (adjust as needed)
                        if effect_name == 'burn':
                            total_damage += level * 3
                        elif effect_name == 'bleed':
                            total_damage += level * 2
                        elif effect_name == 'poison':
                            total_damage += level * 1
        
        return total_damage
    
    def decide_action(self, turn=None):
        """
        Main decision function using simple if-else structure.
        Re-evaluates all options from the beginning after each action.
        """
        self.log(f"=== DECISION START - Enemy STA: {self.enemy.sta}, RIG: {self.enemy.rig} ===")
        
        # Increment turns since last buff
        self.turns_since_buff += 1
        
        # 1. KILL ENEMY BODY - Check if we can kill player's body part
        kill_action = self.check_kill_opportunity()
        if kill_action:
            self.log(f"DECISION: Kill opportunity - {kill_action.description}")
            return kill_action
        
        # 1.5. PASS if low stamina and has dodge/shield
        pass_action = self.check_pass_opportunity()
        if pass_action:
            self.log(f"DECISION: Pass opportunity - {pass_action.description}")
            return pass_action
        
        # 2. HEAL HEAD if < 60% (accounting for effect damage)
        head_heal = self.check_heal_head()
        if head_heal:
            self.log(f"DECISION: Heal head - {head_heal.description}")
            return head_heal
        
        # 3. HEAL BODY if < 60% (accounting for effect damage)
        body_heal = self.check_heal_body()
        if body_heal:
            self.log(f"DECISION: Heal body - {body_heal.description}")
            return body_heal
        
        # 4. USE BUFF if no buff active and none used in last 5 turns
        buff_action = self.check_buff_opportunity()
        if buff_action:
            self.log(f"DECISION: Buff opportunity - {buff_action.description}")
            self.turns_since_buff = 0  # Reset counter
            return buff_action

        # 5. ATTACK if arms+legs >= 30% health
        attack_action = self.check_attack_opportunity()
        if attack_action:
            self.log(f"DECISION: Attack opportunity - {attack_action.description}")
            return attack_action
        
        # 6. HEAL most damaged body part
        heal_action = self.check_heal_most_damaged()
        if heal_action:
            self.log(f"DECISION: Heal most damaged - {heal_action.description}")
            return heal_action
        
        # 7. ATTACK if cannot do better (any available move)
        desperation_attack = self.check_desperation_attack()
        if desperation_attack:
            self.log(f"DECISION: Desperation attack - {desperation_attack.description}")
            return desperation_attack
        
        # Fallback: Pass
        self.log("DECISION: No valid actions - passing")
        return AIAction('pass', description='No valid actions available')
    
    def check_kill_opportunity(self):
        """Check if we can kill a player body part"""
        available_moves = self.get_available_moves()
        
        for move in available_moves:
            if not hasattr(move, 'tipo') or move.tipo not in ['ATK', 'REA']:
                continue
            
            # Check general move requirements first
            can_use_general, _ = self.can_use_move(move)
            if not can_use_general:
                continue
            
            move_damage = self.calculate_move_damage(move)
            if move_damage <= 0:
                continue
            
            # Check each player body part
            for i, player_part in enumerate(self.player.body_parts):
                if player_part.p_pvt <= 0:
                    continue  # Already dead
                
                # Check if move can kill this part AND can target it
                if move_damage >= player_part.p_pvt:
                    can_target = self.can_move_target_bodypart(move, player_part)
                    if can_target:
                        return AIAction(
                            'attack',
                            move=move,
                            target_part=i,
                            description=f"Kill {player_part.name} with {move.name} ({move_damage} dmg vs {player_part.p_pvt} HP)",
                            stamina_cost=move.stamina_cost
                        )
        
        return None
    
    def check_heal_head(self):
        """Check if head needs healing (< 60%)"""
        head = self.get_body_part_by_name(self.enemy, "HEAD")
        if not head:
            return None
        
        effect_damage = self.calculate_effect_damage_this_turn(head)
        effective_hp = head.p_pvt - effect_damage
        health_percent = effective_hp / head.max_p_pvt if head.max_p_pvt > 0 else 0
        
        if health_percent < 0.6:  # Less than 60%
            if self.enemy.rig >= 5 and self.enemy.sta >= self.regen_stamina_cost:  # Can regenerate
                head_index = self.get_body_part_index(self.enemy, head)
                return AIAction(
                    'regenerate',
                    target_part=head_index,
                    description=f"Heal head - {head.p_pvt}/{head.max_p_pvt} ({health_percent:.1%}) - Effect dmg: {effect_damage}",
                    stamina_cost=self.regen_stamina_cost
                )
        
        return None
    
    def check_heal_body(self):
        """Check if body needs healing (< 60%)"""
        body = self.get_body_part_by_name(self.enemy, "BODY")
        if not body:
            return None
        
        effect_damage = self.calculate_effect_damage_this_turn(body)
        effective_hp = body.p_pvt - effect_damage
        health_percent = effective_hp / body.max_p_pvt if body.max_p_pvt > 0 else 0
        
        if health_percent < 0.6:  # Less than 60%
            if self.enemy.rig >= 5 and self.enemy.sta >= self.regen_stamina_cost:  # Can regenerate
                body_index = self.get_body_part_index(self.enemy, body)
                return AIAction(
                    'regenerate',
                    target_part=body_index,
                    description=f"Heal body - {body.p_pvt}/{body.max_p_pvt} ({health_percent:.1%}) - Effect dmg: {effect_damage}",
                    stamina_cost=self.regen_stamina_cost
                )
        
        return None
    
    def check_buff_opportunity(self):
        """Check if we should use a buff move"""
        if self.turns_since_buff < 5:  # Used buff in last 5 turns
            return None
        
        # Check if any buff is already active
        if hasattr(self.enemy, 'active_buffs') and hasattr(self.enemy.active_buffs, 'get_active_buff_moves'):
            active_buffs = self.enemy.active_buffs.get_active_buff_moves()
            if active_buffs:  # Has active buffs
                return None
        
        # Find available buff moves
        available_moves = self.get_available_moves()
        buff_moves = [move for move in available_moves 
                     if hasattr(move, 'tipo') and move.tipo == 'BUF']
        
        for move in buff_moves:
            # Use main battle system's requirement checking instead of simplified AI version
            try:
                # Import and use the main requirements check
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), 'Overworld', 'Mappe', 'FilesPy'))
                from Battle_Menu_Beta_V18 import check_move_requirements
                can_use, failed_reqs = check_move_requirements(self.enemy, move)
                if can_use:
                    return AIAction(
                        'buff',
                        move=move,
                        description=f"Use buff {move.name} (no active buffs, {self.turns_since_buff} turns since last)",
                        stamina_cost=self.get_move_stamina_cost(move)
                    )
                else:
                    self.log(f"Cannot use buff {move.name}: {failed_reqs}")
            except ImportError:
                # Fallback to AI's own check if import fails
                can_use_general, reason = self.can_use_move(move)
                if can_use_general:
                    return AIAction(
                        'buff',
                        move=move,
                        description=f"Use buff {move.name} (no active buffs, {self.turns_since_buff} turns since last)",
                        stamina_cost=self.get_move_stamina_cost(move)
                    )
                else:
                    self.log(f"Cannot use buff {move.name}: {reason}")
        
        return None
    
    def check_attack_opportunity(self):
        """Check if we can attack (arms+legs >= 30% health)"""
        # Calculate arms + legs total health
        arms_legs_current = 0
        arms_legs_max = 0
        
        for part in self.enemy.body_parts:
            if "ARM" in part.name.upper() or "LEG" in part.name.upper():
                arms_legs_current += part.p_pvt
                arms_legs_max += part.max_p_pvt
        
        if arms_legs_max == 0:
            health_percent = 0
        else:
            health_percent = arms_legs_current / arms_legs_max

        if health_percent < 0.3:  # Less than 30%
            return None
        
        # Find attack moves
        available_moves = self.get_available_moves()
        attack_moves = [move for move in available_moves 
                       if hasattr(move, 'tipo') and move.tipo in ['ATK', 'REA']]
        
        if not attack_moves:
            return None
        
        # Get available targets
        targets = []
        head = self.get_body_part_by_name(self.player, "HEAD")
        body = self.get_body_part_by_name(self.player, "BODY")
        other_parts = [part for part in self.player.body_parts 
                      if part.p_pvt > 0 and "HEAD" not in part.name.upper() 
                      and "BODY" not in part.name.upper()]
        
        if head and head.p_pvt > 0:
            targets.append(("HEAD", head))
        if body and body.p_pvt > 0:
            targets.append(("BODY", body))
        for part in other_parts:
            targets.append(("OTHER", part))
        
        if not targets:
            return None
        
        # Find valid move-target combinations
        valid_combinations = []
        
        for move in attack_moves:
            # Check general move requirements first
            can_use_general, _ = self.can_use_move(move)
            if not can_use_general:
                continue
                
            for target_type, target_part in targets:
                # Check if this move can target this body part based on requirements
                can_target = self.can_move_target_bodypart(move, target_part)
                if can_target:
                    target_index = self.get_body_part_index(self.player, target_part)
                    valid_combinations.append((move, target_part, target_index, target_type))
        
        if not valid_combinations:
            return None
        
        # Choose random valid combination
        move, target_part, target_index, target_type = random.choice(valid_combinations)
        
        return AIAction(
            'attack',
            move=move,
            target_part=target_index,
            description=f"Attack player {target_part.name} with {move.name} (limbs: {health_percent:.1%})",
            stamina_cost=move.stamina_cost
        )
        
        return None
    
    def check_heal_most_damaged(self):
        """Check if we should heal the most damaged body part"""
        if self.enemy.rig < 5 or self.enemy.sta < self.regen_stamina_cost:
            return None
        
        # Find most damaged part
        most_damaged = None
        lowest_percent = 1.0
        
        for part in self.enemy.body_parts:
            if part.max_p_pvt <= 0:
                continue
            
            effect_damage = self.calculate_effect_damage_this_turn(part)
            effective_hp = max(0, part.p_pvt - effect_damage)
            health_percent = effective_hp / part.max_p_pvt
            
            if health_percent < lowest_percent:
                lowest_percent = health_percent
                most_damaged = part
        
        if most_damaged and lowest_percent < 1.0:  # Found a damaged part
            part_index = self.get_body_part_index(self.enemy, most_damaged)
            effect_damage = self.calculate_effect_damage_this_turn(most_damaged)
            return AIAction(
                'regenerate',
                target_part=part_index,
                description=f"Heal most damaged {most_damaged.name} - {most_damaged.p_pvt}/{most_damaged.max_p_pvt} ({lowest_percent:.1%}) - Effect dmg: {effect_damage}",
                stamina_cost=self.regen_stamina_cost
            )
        
        return None
    
    def check_pass_opportunity(self):
        """Check if we should pass (low stamina + has dodge/shield)"""
        stamina = self.enemy.sta
        # Only pass if stamina is between DodgeShield_Stamina_Cost (2) and DodgeShield_Stamina_Cost+1 (3)
        if self.dodge_shield_cost <= stamina <= (self.dodge_shield_cost + 1):
            # Check if enemy has active dodge or shield buffs
            has_defensive_buff = False
            
            if hasattr(self.enemy, 'buffs'):
                # Check dodge buff (must have level >= 1 AND duration > 0)
                if hasattr(self.enemy.buffs, 'buf_dodge'):
                    dodge_data = self.enemy.buffs.buf_dodge
                    if len(dodge_data) >= 3 and dodge_data[1] >= 1 and dodge_data[2] > 0:
                        has_defensive_buff = True
                        self.log(f"Has active DODGE buff: level={dodge_data[1]}, duration={dodge_data[2]}")
                
                # Check shield buff (must have level >= 1 AND duration > 0)
                if hasattr(self.enemy.buffs, 'buf_shield'):
                    shield_data = self.enemy.buffs.buf_shield
                    if len(shield_data) >= 3 and shield_data[1] >= 1 and shield_data[2] > 0:
                        has_defensive_buff = True
                        self.log(f"Has active SHIELD buff: level={shield_data[1]}, duration={shield_data[2]}")
            
            if has_defensive_buff:
                return AIAction(
                    'pass',
                    description=f"Pass - low stamina ({stamina}) with defensive buffs active"
                )
            else:
                self.log(f"Low stamina ({stamina}) but NO defensive buffs active - not passing")
        else:
            self.log(f"Stamina ({stamina}) not in pass range ({self.dodge_shield_cost}-{self.dodge_shield_cost + 1})")
        
        return None
    
    def check_desperation_attack(self):
        """Check if we can execute any attack move without health requirements"""
        available_moves = self.get_available_moves()
        
        # Get attack moves that we can afford - USE MAIN REQUIREMENTS SYSTEM
        attack_moves = []
        for move in available_moves:
            if (hasattr(move, 'tipo') and move.tipo in ['ATK', 'REA'] 
                and self.get_move_stamina_cost(move) <= self.enemy.sta):
                # Use main battle requirements system instead of AI's simplified version
                try:
                    # Import and use the main requirements check
                    import sys
                    import os
                    sys.path.append(os.path.join(os.path.dirname(__file__), 'Overworld', 'Mappe', 'FilesPy'))
                    from Battle_Menu_Beta_V18 import check_move_requirements
                    can_use, failed_reqs = check_move_requirements(self.enemy, move)
                    if can_use:
                        attack_moves.append(move)
                    else:
                        print(f"[AI DEBUG] {self.enemy.name} BLOCKED from using {move.name}: {failed_reqs}")
                except ImportError:
                    # Fallback to AI's own check if import fails
                    can_use = self.battle_menu.check_move_requirements(move, self.enemy)
                    if can_use:
                        attack_moves.append(move)
        
        if not attack_moves:
            self.log("No attack moves available for desperation attack")
            return None
        
        # Find valid move-target combinations
        valid_combinations = []
        
        for move in attack_moves:
            # Target selection: prioritize body > head > any limb
            target_candidates = []
            
            # 1. Check body parts with HP > 1
            for idx, part in enumerate(self.player.body_parts):
                if part.p_pvt > 1:
                    target_candidates.append((idx, part))
            
            if not target_candidates:
                continue
                
            # Sort by priority: body, head, then others
            def get_priority(item):
                idx, part = item
                name = part.name.upper()
                if "BODY" in name:
                    return 1
                elif "HEAD" in name:
                    return 2
                else:
                    return 3
            
            target_candidates.sort(key=get_priority)
            
            # Check if move can target any of these parts
            for idx, part in target_candidates:
                can_target = self.can_move_target_bodypart(move, part)
                if can_target:
                    valid_combinations.append((move, idx, part))
                    break  # Take first valid target for this move
        
        if not valid_combinations:
            self.log("No valid move-target combinations for desperation attack")
            return None
        
        # Pick the first valid combination
        chosen_move, target_index, target_part = valid_combinations[0]
        
        return AIAction(
            'attack',
            move=chosen_move,
            target_part=target_index,
            description=f"Desperation attack {target_part.name} with {chosen_move.name}",
            stamina_cost=self.get_move_stamina_cost(chosen_move)
        )

    def track_player_move(self, move_name, body_part_used, target_part, turn_number=None):
        """Track a player move for analysis (simplified from V2)"""
        if turn_number is None:
            turn_number = len(self.player_move_history)
        
        player_move = {
            'turn': turn_number,
            'move_name': move_name,
            'body_part': body_part_used,  # Which body part the player used to attack
            'target': target_part  # Which enemy part the player targeted
        }
        
        self.player_move_history.append(player_move)
        # Keep only last 5 moves to prevent unlimited growth (simpler than V2's 10)
        if len(self.player_move_history) > 5:
            self.player_move_history = self.player_move_history[-5:]
        
        self.log(f"Tracked player move: {move_name} using {body_part_used} targeting {target_part}")


def create_enemy_ai_v3(enemy, player, battle_menu_instance=None):
    """
    Factory function to create EnemyAI_V3 instance.
    Compatible with existing AI system interface.
    """
    return EnemyAI_V3(enemy, player, battle_menu_instance)


# Test function
if __name__ == "__main__":
    print("Enemy AI V3 - Simple Decision Tree System")
    print("This AI uses straightforward if-else logic for reliable decision making.")