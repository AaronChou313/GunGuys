import math
import pygame

class Entity:
    def __init__(self, x, y, radius, mass, max_health):
        # Position and movement
        self.x = x
        self.y = y
        self.vx = 0  # Velocity in x direction
        self.vy = 0  # Velocity in y direction
        self.ax = 0  # Acceleration in x direction
        self.ay = 0  # Acceleration in y direction
        
        # Physics properties
        self.radius = radius
        self.mass = mass
        self.max_health = max_health
        self.current_health = max_health
        
        # Movement constraints
        self.max_speed = 200  # Maximum speed in pixels/second
        self.acceleration_rate = 100  # Acceleration in pixels/second^2
        self.friction_coefficient = 50  # Friction in pixels/second^2
        
        # Collision properties
        self.collision_radius = radius
    
    def update(self, dt):
        # Apply friction
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 0:
            # Calculate friction force opposite to movement direction
            friction_x = -self.vx / speed * self.friction_coefficient
            friction_y = -self.vy / speed * self.friction_coefficient
            
            # Apply friction
            self.ax += friction_x
            self.ay += friction_y
        
        # Update velocity based on acceleration
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        
        # Limit speed to maximum
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > self.max_speed:
            self.vx = self.vx / speed * self.max_speed
            self.vy = self.vy / speed * self.max_speed
        
        # Update position based on velocity
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Reset acceleration for next frame
        self.ax = 0
        self.ay = 0
    
    def apply_acceleration(self, ax, ay):
        """Apply acceleration to the entity"""
        self.ax += ax
        self.ay += ay
    
    def check_collision(self, other):
        """Check if this entity collides with another entity"""
        distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        return distance < (self.collision_radius + other.collision_radius)
    
    def resolve_collision(self, other):
        """Resolve collision between this entity and another entity using elastic collision"""
        # Calculate distance
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check if objects are colliding
        if distance < (self.collision_radius + other.collision_radius) and distance > 0:
            # Normalize direction vector
            dx /= distance
            dy /= distance
            
            # Separate entities to prevent overlap
            overlap = (self.collision_radius + other.collision_radius) - distance
            separation_x = dx * overlap * 0.5
            separation_y = dy * overlap * 0.5
            
            self.x -= separation_x
            self.y -= separation_y
            other.x += separation_x
            other.y += separation_y
            
            # Calculate relative velocity
            dvx = other.vx - self.vx
            dvy = other.vy - self.vy
            
            # Calculate relative velocity along collision normal
            dvn = dvx * dx + dvy * dy
            
            # Do not resolve if velocities are separating
            if dvn > 0:
                return
            
            # Calculate collision impulse
            e = 1.0  # Coefficient of restitution (1.0 for perfectly elastic collision)
            impulse = -(1 + e) * dvn / (1/self.mass + 1/other.mass)
            
            # Apply impulse
            self.vx -= impulse * dx / self.mass
            self.vy -= impulse * dy / self.mass
            other.vx += impulse * dx / other.mass
            other.vy += impulse * dy / other.mass