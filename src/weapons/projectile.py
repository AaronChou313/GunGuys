import pygame
import math
from entities.entity import Entity

class Projectile(Entity):
    def __init__(self, x, y, vx, vy, damage, owner_type="player"):
        # Projectiles are small and light
        super().__init__(x, y, radius=5, mass=1, max_health=1)
        
        # Set initial velocity
        self.vx = vx
        self.vy = vy
        
        # Projectile properties
        self.damage = damage
        self.owner_type = owner_type  # "player" or "monster"
        self.lifetime = 5.0  # seconds
        self.age = 0.0
        
        # Colors for different projectile types
        if owner_type == "player":
            self.color = (255, 255, 0)  # Yellow
        else:
            self.color = (255, 0, 0)  # Red
    
    def update(self, dt):
        # Update position based on velocity
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Age the projectile
        self.age += dt
        
        # Remove old projectiles
        if self.age >= self.lifetime:
            return False  # Indicates this projectile should be removed
            
        return True  # Projectile still alive
    
    def draw(self, screen, camera_x, camera_y):
        # Draw projectile
        projectile_screen_x = self.x - camera_x
        projectile_screen_y = self.y - camera_y
        pygame.draw.circle(screen, self.color, 
                          (int(projectile_screen_x), int(projectile_screen_y)), 
                          self.radius)