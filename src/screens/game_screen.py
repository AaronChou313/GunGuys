import pygame
import random
from entities.player import Player
from entities.monster import Monster
from network.network_manager import NetworkManager

class GameScreen:
    def __init__(self, screen, save_file=None):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        
        # Network manager
        self.network_manager = NetworkManager()
        
        # Camera position (player is always centered)
        self.camera_x = 0
        self.camera_y = 0
        
        # Grid properties
        self.grid_size = 50
        self.grid_color = (200, 200, 200)
        
        # Create player
        self.player = Player(400, 300)  # Start at center of screen
        
        # Create monsters
        self.monsters = []
        for _ in range(5):
            x = random.randint(100, 700)
            y = random.randint(100, 500)
            self.monsters.append(Monster(x, y))
        
        # All entities list for collision detection
        self.entities = [self.player] + self.monsters
        
        # Mouse position for targeting
        self.mouse_x = 0
        self.mouse_y = 0
        
        # Load save if provided
        if save_file:
            self.load_game(save_file)
            
        # Menu
        self.paused = False
        self.menu_buttons = [
            {"rect": pygame.Rect(screen.get_width()//2 - 100, 200, 200, 50),
             "text": "Resume",
             "action": "resume"},
            {"rect": pygame.Rect(screen.get_width()//2 - 100, 270, 200, 50),
             "text": "Settings",
             "action": "settings"},
            {"rect": pygame.Rect(screen.get_width()//2 - 100, 340, 200, 50),
             "text": "Save and Quit",
             "action": "save_quit"}
        ]
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.mouse_x, self.mouse_y = event.pos
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                if self.paused:
                    for button in self.menu_buttons:
                        if button["rect"].collidepoint(event.pos):
                            return self.handle_menu_action(button["action"])
                else:
                    # Convert mouse position to world coordinates
                    world_x = self.mouse_x + self.camera_x
                    world_y = self.mouse_y + self.camera_y
                    self.player.attack(world_x, world_y)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
                return None
        
        if self.paused:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.menu_buttons:
                    if button["rect"].collidepoint(event.pos):
                        return self.handle_menu_action(button["action"])
        
        return None
    
    def handle_menu_action(self, action):
        if action == "resume":
            self.paused = False
        elif action == "settings":
            # TODO: Implement settings
            pass
        elif action == "save_quit":
            # Stop network sharing when quitting to main menu
            self.network_manager.stop_networking()
            
            # TODO: Save game
            from screens.main_menu import MainMenu
            return MainMenu(self.screen)
        return None
    
    def update(self, dt):
        if not self.paused:
            # Update player
            self.player.update(dt)
            
            # Update monsters
            for monster in self.monsters:
                monster.update(dt, self.player.x, self.player.y)
            
            # Handle collisions between entities
            for i in range(len(self.entities)):
                for j in range(i+1, len(self.entities)):
                    if self.entities[i].check_collision(self.entities[j]):
                        self.entities[i].resolve_collision(self.entities[j])
            
            # Handle projectile collisions
            self.handle_projectile_collisions()
            
            # Update camera to follow player
            self.camera_x = self.player.x - self.screen.get_width() // 2
            self.camera_y = self.player.y - self.screen.get_height() // 2
    
    def handle_projectile_collisions(self):
        """Handle collisions between projectiles and entities"""
        # Player projectiles hitting monsters
        for projectile in self.player.projectiles:
            for monster in self.monsters:
                if projectile.check_collision(monster):
                    monster.current_health -= projectile.damage
                    # Remove projectile on hit
                    if projectile in self.player.projectiles:
                        self.player.projectiles.remove(projectile)
                    # Remove monster if dead
                    if monster.current_health <= 0:
                        self.monsters.remove(monster)
                        self.entities.remove(monster)
                        # Give player experience for killing monster
                        self.player.gain_experience(20)
                    break
        
        # Monster projectiles hitting player
        for monster in self.monsters:
            for projectile in monster.projectiles:
                if projectile.check_collision(self.player):
                    self.player.current_health -= projectile.damage
                    # Remove projectile on hit
                    if projectile in monster.projectiles:
                        monster.projectiles.remove(projectile)
                    # Remove player if dead (in a real game, this would trigger game over)
                    if self.player.current_health <= 0:
                        self.player.current_health = 0
                    break
    
    def draw_grid(self):
        """Draw a grid on the background"""
        # Calculate visible grid bounds
        left = int(self.camera_x) // self.grid_size * self.grid_size
        top = int(self.camera_y) // self.grid_size * self.grid_size
        right = left + self.screen.get_width() + self.grid_size
        bottom = top + self.screen.get_height() + self.grid_size
        
        # Draw vertical lines
        for x in range(left, right, self.grid_size):
            screen_x = x - self.camera_x
            pygame.draw.line(self.screen, self.grid_color, 
                            (screen_x, 0), 
                            (screen_x, self.screen.get_height()))
        
        # Draw horizontal lines
        for y in range(top, bottom, self.grid_size):
            screen_y = y - self.camera_y
            pygame.draw.line(self.screen, self.grid_color, 
                            (0, screen_y), 
                            (self.screen.get_width(), screen_y))
    
    def draw(self):
        # Draw game world with grid background
        self.screen.fill((30, 30, 30))  # Dark background
        self.draw_grid()
        
        # Draw monsters
        for monster in self.monsters:
            monster.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw player (should be drawn last so it's on top)
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw UI
        # Health bar
        health_ratio = self.player.current_health / self.player.max_health
        pygame.draw.rect(self.screen, (100, 0, 0), (10, 10, 200, 20))
        pygame.draw.rect(self.screen, (0, 200, 0), (10, 10, int(200 * health_ratio), 20))
        
        # Level and XP
        level_text = self.font.render(f"Level: {self.player.level}", True, (255, 255, 255))
        self.screen.blit(level_text, (10, 40))
        
        xp_text = self.font.render(f"XP: {self.player.experience}/{self.player.experience_needed}", True, (255, 255, 255))
        self.screen.blit(xp_text, (10, 70))
        
        # Pause menu
        if self.paused:
            # Semi-transparent overlay
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # Menu title
            title_font = pygame.font.Font(None, 48)
            title = title_font.render("Game Paused", True, (255, 255, 255))
            title_rect = title.get_rect(center=(self.screen.get_width()//2, 150))
            self.screen.blit(title, title_rect)
            
            # Menu buttons
            for button in self.menu_buttons:
                pygame.draw.rect(self.screen, (70, 130, 180), button["rect"])
                pygame.draw.rect(self.screen, (255, 255, 255), button["rect"], 2)
                
                text = self.font.render(button["text"], True, (255, 255, 255))
                text_rect = text.get_rect(center=button["rect"].center)
                self.screen.blit(text, text_rect)
    
    def load_game(self, save_file):
        # TODO: Implement game loading
        pass
    
    def update(self, dt=None):
        if dt is not None:
            self._update_with_dt(dt)
        else:
            self._update_with_dt(1/60)  # Default delta time
    
    def _update_with_dt(self, dt):
        if not self.paused:
            # Update player
            self.player.update(dt)
            
            # Update monsters
            for monster in self.monsters:
                monster.update(dt, self.player.x, self.player.y)
            
            # Handle collisions between entities
            for i in range(len(self.entities)):
                for j in range(i+1, len(self.entities)):
                    if self.entities[i].check_collision(self.entities[j]):
                        self.entities[i].resolve_collision(self.entities[j])
            
            # Handle projectile collisions
            self.handle_projectile_collisions()
            
            # Update camera to follow player
            self.camera_x = self.player.x - self.screen.get_width() // 2
            self.camera_y = self.player.y - self.screen.get_height() // 2