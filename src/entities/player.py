import math
import pygame
from entities.entity import Entity
from weapons.projectile import Projectile

class Player(Entity):
    def __init__(self, x=0, y=0, player_id=None):
        super().__init__(x, y, radius=20, mass=10, max_health=100)
        self.player_id = player_id if player_id else "player"
        self.level = 1
        self.experience = 0
        self.experience_needed = 100
        
        # Base stats
        self.base_max_health = 100
        self.base_movement_speed = 200  # pixels per second
        self.base_acceleration_rate = 100
        self.base_friction_coefficient = 50
        self.base_attack_speed = 1.0
        self.base_damage = 10
        self.base_attack_range = 50
        
        # Current stats (affected by level and equipment)
        self.max_speed = self.base_movement_speed
        self.acceleration_rate = self.base_acceleration_rate
        self.friction_coefficient = self.base_friction_coefficient
        self.attack_speed = self.base_attack_speed
        self.damage = self.base_damage
        self.attack_range = self.base_attack_range
        
        # Combat
        self.last_attack_time = 0
        self.projectiles = []
        
        # Weapon
        self.weapon = None
        self.weapon_name = "Unarmed"
        
        # Color (different for different players)
        if self.player_id == "player":
            self.color = (0, 255, 0)  # Green for main player
        else:
            self.color = (0, 255, 255)  # Cyan for other players
    
    def gain_experience(self, amount):
        self.experience += amount
        if self.experience >= self.experience_needed:
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.experience -= self.experience_needed
        self.experience_needed = int(self.experience_needed * 1.5)  # 50% increase each level
        
        # Improve stats on level up
        self.base_max_health = int(self.base_max_health * 1.1)  # 10% increase
        self.current_health = self.base_max_health  # Heal on level up
        self.base_movement_speed = int(self.base_movement_speed * 1.05)  # 5% increase
        self.base_acceleration_rate *= 1.05  # 5% increase
        self.base_damage = int(self.base_damage * 1.1)  # 10% increase
        self.base_attack_range = int(self.base_attack_range * 1.05)  # 5% increase
        
        # Update current stats
        self.update_stats()
    
    def update_stats(self):
        # Apply weapon modifiers if equipped
        self.max_health = self.base_max_health
        self.max_speed = self.base_movement_speed
        self.acceleration_rate = self.base_acceleration_rate
        self.friction_coefficient = self.base_friction_coefficient
        self.attack_speed = self.base_attack_speed
        self.damage = self.base_damage
        self.attack_range = self.base_attack_range
        
        if self.weapon:
            self.weapon_name = self.weapon.name
            self.damage += self.weapon.damage
            self.attack_speed = self.base_attack_speed * self.weapon.attack_speed
            if hasattr(self.weapon, 'attack_range'):
                self.attack_range = self.base_attack_range + self.weapon.attack_range
        else:
            self.weapon_name = "Unarmed"
    
    def equip_weapon(self, weapon):
        self.weapon = weapon
        self.update_stats()
    
    def attack(self, target_x, target_y):
        """Attack towards a target position"""
        current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
        
        # Check if we can attack based on attack speed
        if current_time - self.last_attack_time >= 1.0 / self.attack_speed:
            self.last_attack_time = current_time
            
            # Calculate direction to target
            dx = target_x - self.x
            dy = target_y - self.y
            distance = max(0.1, math.sqrt(dx*dx + dy*dy))  # Avoid division by zero
            
            # Normalize direction
            dx /= distance
            dy /= distance
            
            # Create projectile
            projectile_speed = 300  # pixels per second
            projectile_vx = dx * projectile_speed
            projectile_vy = dy * projectile_speed
            
            projectile = Projectile(
                self.x + dx * self.radius * 2,  # Start outside player
                self.y + dy * self.radius * 2,
                projectile_vx,
                projectile_vy,
                self.damage,
                "player"
            )
            
            self.projectiles.append(projectile)
            return True
        return False
    
    def update(self, dt):
        # Handle player movement with acceleration and friction
        keys = pygame.key.get_pressed()
        
        # Apply acceleration based on input (only for main player)
        if self.player_id == "player":
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.apply_acceleration(-self.acceleration_rate, 0)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.apply_acceleration(self.acceleration_rate, 0)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.apply_acceleration(0, -self.acceleration_rate)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.apply_acceleration(0, self.acceleration_rate)
        
        # Update entity with physics
        super().update(dt)
        
        # Update projectiles
        self.projectiles = [p for p in self.projectiles if p.update(dt)]
    
    def draw(self, screen, camera_x, camera_y):
        # Draw player (centered on screen)
        player_screen_x = self.x - camera_x
        player_screen_y = self.y - camera_y
        pygame.draw.circle(screen, self.color, (int(player_screen_x), int(player_screen_y)), self.radius)
        
        # Draw direction indicator
        pygame.draw.circle(screen, (0, 100, 0), (int(player_screen_x), int(player_screen_y)), self.radius//2)
        
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(screen, camera_x, camera_y)