import math
import pygame
from entities.entity import Entity

class Player(Entity):
    def __init__(self, x=0, y=0):
        super().__init__(x, y, radius=20, mass=10, max_health=100)
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
        
        # Weapon
        self.weapon = None
    
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
            self.damage += self.weapon.damage
            self.attack_speed = self.base_attack_speed * self.weapon.attack_speed
            if hasattr(self.weapon, 'attack_range'):
                self.attack_range = self.base_attack_range + self.weapon.attack_range
    
    def equip_weapon(self, weapon):
        self.weapon = weapon
        self.update_stats()
    
    def update(self, dt):
        # Handle player movement with acceleration and friction
        keys = pygame.key.get_pressed()
        
        # Apply acceleration based on input
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
    
    def draw(self, screen, camera_x, camera_y):
        # Draw player (centered on screen)
        player_screen_x = self.x - camera_x
        player_screen_y = self.y - camera_y
        pygame.draw.circle(screen, (0, 255, 0), (int(player_screen_x), int(player_screen_y)), self.radius)
        
        # Draw direction indicator
        pygame.draw.circle(screen, (0, 100, 0), (int(player_screen_x), int(player_screen_y)), self.radius//2)