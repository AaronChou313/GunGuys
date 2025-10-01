import pygame
import random
import math
from entities.entity import Entity
from weapons.projectile import Projectile

class Monster(Entity):
    def __init__(self, x, y):
        # Randomize monster properties
        radius = random.randint(15, 25)
        mass = random.randint(5, 20)
        max_health = random.randint(30, 80)
        
        super().__init__(x, y, radius, mass, max_health)
        
        # Monster-specific properties
        self.max_speed = random.randint(50, 150)
        self.acceleration_rate = random.randint(30, 80)
        self.friction_coefficient = random.randint(20, 60)
        self.damage = random.randint(5, 15)
        self.attack_speed = random.uniform(0.5, 1.5)
        
        # AI properties
        self.move_timer = 0
        self.move_direction = (0, 0)
        self.last_attack_time = 0
        self.projectiles = []
        
        # Color for drawing
        self.color = (
            random.randint(100, 255),
            random.randint(0, 100),
            random.randint(0, 100)
        )
    
    def update(self, dt, player_x, player_y):
        # Simple AI: periodically change direction towards player
        self.move_timer -= dt
        if self.move_timer <= 0:
            self.move_timer = random.uniform(0.5, 2.0)  # Change direction every 0.5-2 seconds
            
            # Move towards player with some randomness
            dx = player_x - self.x
            dy = player_y - self.y
            distance = max(0.1, math.sqrt(dx*dx + dy*dy))  # Avoid division by zero
            
            # Normalize and add some randomness
            self.move_direction = (
                dx/distance + random.uniform(-0.5, 0.5),
                dy/distance + random.uniform(-0.5, 0.5)
            )
            
            # Normalize direction
            length = max(0.1, math.sqrt(self.move_direction[0]**2 + self.move_direction[1]**2))
            self.move_direction = (self.move_direction[0]/length, self.move_direction[1]/length)
        
        # Apply acceleration in the current direction
        self.apply_acceleration(
            self.move_direction[0] * self.acceleration_rate,
            self.move_direction[1] * self.acceleration_rate
        )
        
        # Attack player if close enough
        distance_to_player = math.sqrt((player_x - self.x)**2 + (player_y - self.y)**2)
        if distance_to_player < 200:  # Attack range
            self.attack(player_x, player_y)
        
        # Update entity with physics
        super().update(dt)
        
        # Update projectiles
        self.projectiles = [p for p in self.projectiles if p.update(dt)]
    
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
            projectile_speed = 200  # pixels per second
            projectile_vx = dx * projectile_speed
            projectile_vy = dy * projectile_speed
            
            projectile = Projectile(
                self.x + dx * self.radius * 2,  # Start outside monster
                self.y + dy * self.radius * 2,
                projectile_vx,
                projectile_vy,
                self.damage,
                "monster"
            )
            
            self.projectiles.append(projectile)
            return True
        return False
    
    def draw(self, screen, camera_x, camera_y):
        # Draw monster
        monster_screen_x = self.x - camera_x
        monster_screen_y = self.y - camera_y
        pygame.draw.circle(screen, self.color, (int(monster_screen_x), int(monster_screen_y)), self.radius)
        
        # Draw eyes
        eye_offset = self.radius // 3
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(monster_screen_x - eye_offset), int(monster_screen_y - eye_offset)), 
                          self.radius // 4)
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(monster_screen_x + eye_offset), int(monster_screen_y - eye_offset)), 
                          self.radius // 4)
        
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(screen, camera_x, camera_y)