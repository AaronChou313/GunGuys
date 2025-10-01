import pygame
import random
from entities.player import Player
from entities.monster import Monster
from network.network_manager import NetworkManager
from screens.settings import SettingsScreen

class GameScreen:
    def __init__(self, screen, save_file=None):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 20)
        
        # Network manager
        self.network_manager = NetworkManager()
        
        # Camera position (player is always centered)
        self.camera_x = 0
        self.camera_y = 0
        
        # Grid properties
        self.grid_size = 50
        self.grid_color = (200, 200, 200)
        
        # Create player
        player_id = self.network_manager.player_id if self.network_manager.player_id else "player_1"
        self.player = Player(400, 300, player_id)  # Start at center of screen
        
        # Create other players (for multiplayer)
        self.other_players = []
        
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
            # Open settings screen with return to game screen
            settings_screen = SettingsScreen(self.screen, self)
            return settings_screen
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
            
            # Update other players
            for other_player in self.other_players:
                other_player.update(dt)
            
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
            
            # Update network state
            self.update_network_state()
            
            # Update from network state
            self.update_from_network_state()
    
    def update_network_state(self):
        """Update network state with current game state"""
        # Update player positions
        player_data = {
            "x": self.player.x,
            "y": self.player.y,
            "health": self.player.current_health,
            "max_health": self.player.max_health,
            "name": "Player",
            "level": self.player.level,
            "weapon": self.player.weapon_name
        }
        
        self.network_manager.game_state["players"][self.player.player_id] = player_data
        
        # Send player update to server if we're a client
        if self.network_manager.is_connected and not self.network_manager.is_host:
            self.network_manager.send_player_update(player_data)
        
        # Update monster positions (only host should do this)
        if self.network_manager.is_host:
            for i, monster in enumerate(self.monsters):
                self.network_manager.game_state["monsters"][f"monster_{i}"] = {
                    "x": monster.x,
                    "y": monster.y,
                    "health": monster.current_health,
                    "max_health": monster.max_health
                }
        
        # Update projectiles (only host should do this)
        if self.network_manager.is_host:
            all_projectiles = []
            # Player projectiles
            for proj in self.player.projectiles:
                all_projectiles.append({
                    "x": proj.x,
                    "y": proj.y,
                    "vx": proj.vx,
                    "vy": proj.vy,
                    "owner": "player"
                })
            
            # Monster projectiles
            for monster in self.monsters:
                for proj in monster.projectiles:
                    all_projectiles.append({
                        "x": proj.x,
                        "y": proj.y,
                        "vx": proj.vx,
                        "vy": proj.vy,
                        "owner": "monster"
                    })
            
            self.network_manager.game_state["projectiles"] = all_projectiles
    
    def update_from_network_state(self):
        """Update game state from network data"""
        # Update other players
        if "players" in self.network_manager.game_state:
            # Create a list to hold the updated players
            updated_players = []
            
            # Process each player from the network state
            for player_id, player_data in self.network_manager.game_state["players"].items():
                if player_id != self.player.player_id:  # Skip main player
                    # Check if player already exists
                    existing_player = None
                    for p in self.other_players:
                        if p.player_id == player_id:
                            existing_player = p
                            break
                    
                    if existing_player:
                        # Update existing player
                        existing_player.x = player_data["x"]
                        existing_player.y = player_data["y"]
                        existing_player.current_health = player_data["health"]
                        existing_player.max_health = player_data["max_health"]
                        existing_player.level = player_data["level"]
                        existing_player.weapon_name = player_data["weapon"]
                        updated_players.append(existing_player)
                    else:
                        # Create new player
                        new_player = Player(player_data["x"], player_data["y"], player_id)
                        new_player.current_health = player_data["health"]
                        new_player.max_health = player_data["max_health"]
                        new_player.level = player_data["level"]
                        new_player.weapon_name = player_data["weapon"]
                        updated_players.append(new_player)
            
            # Update the other_players list
            self.other_players = updated_players
    
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
    
    def draw_entity_info(self, entity, camera_x, camera_y):
        """Draw entity information (health bar, name, level, weapon)"""
        # Draw health bar
        health_ratio = entity.current_health / entity.max_health
        bar_width = 50
        bar_height = 6
        screen_x = entity.x - camera_x
        screen_y = entity.y - camera_y - entity.radius - 15
        
        # Background of health bar
        pygame.draw.rect(self.screen, (100, 0, 0), 
                        (screen_x - bar_width//2, screen_y, bar_width, bar_height))
        # Foreground of health bar
        pygame.draw.rect(self.screen, (0, 200, 0), 
                        (screen_x - bar_width//2, screen_y, int(bar_width * health_ratio), bar_height))
        
        # Draw name and level for players
        if hasattr(entity, 'player_id'):
            # Name
            name_text = self.small_font.render("Player", True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(screen_x, screen_y - 10))
            self.screen.blit(name_text, name_rect)
            
            # Level
            level_text = self.small_font.render(f"Lvl: {entity.level}", True, (255, 255, 0))
            level_rect = level_text.get_rect(center=(screen_x, screen_y - 25))
            self.screen.blit(level_text, level_rect)
            
            # Weapon
            weapon_text = self.small_font.render(entity.weapon_name, True, (200, 200, 255))
            weapon_rect = weapon_text.get_rect(center=(screen_x, screen_y - 40))
            self.screen.blit(weapon_text, weapon_rect)
            
            # Coordinates
            coord_text = self.small_font.render(f"({int(entity.x)}, {int(entity.y)})", True, (255, 255, 255))
            coord_rect = coord_text.get_rect(center=(screen_x, screen_y - 55))
            self.screen.blit(coord_text, coord_rect)
    
    def draw(self):
        # Draw game world with grid background
        self.screen.fill((30, 30, 30))  # Dark background
        self.draw_grid()
        
        # Draw other players
        for other_player in self.other_players:
            other_player.draw(self.screen, self.camera_x, self.camera_y)
            self.draw_entity_info(other_player, self.camera_x, self.camera_y)
        
        # Draw monsters
        for monster in self.monsters:
            monster.draw(self.screen, self.camera_x, self.camera_y)
            self.draw_entity_info(monster, self.camera_x, self.camera_y)
        
        # Draw player (should be drawn last so it's on top)
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        self.draw_entity_info(self.player, self.camera_x, self.camera_y)
        
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
        
        # Weapon
        weapon_text = self.font.render(f"Weapon: {self.player.weapon_name}", True, (200, 200, 255))
        self.screen.blit(weapon_text, (10, 100))
        
        # Player coordinates
        coord_text = self.font.render(f"Position: ({int(self.player.x)}, {int(self.player.y)})", True, (255, 255, 255))
        self.screen.blit(coord_text, (10, 130))
        
        # Host UI - show connected players
        if self.network_manager.is_host:
            connected_players = self.network_manager.get_connected_players()
            players_text = self.small_font.render(f"Connected players: {len(connected_players) + 1}", True, (255, 255, 255))
            self.screen.blit(players_text, (10, self.screen.get_height() - 60))
            
            # List player IDs
            all_players = [self.player.player_id] + connected_players
            for i, player_id in enumerate(all_players):
                player_text = self.small_font.render(f"- {player_id}", True, (200, 200, 255))
                self.screen.blit(player_text, (20, self.screen.get_height() - 30 - (len(all_players) - i - 1) * 20))
        
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
    
    def update(self, dt=None):
        if dt is not None:
            self._update_with_dt(dt)
        else:
            self._update_with_dt(1/60)  # Default delta time
    
    def _update_with_dt(self, dt):
        if not self.paused:
            # Update player
            self.player.update(dt)
            
            # Update other players
            for other_player in self.other_players:
                other_player.update(dt)
            
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
            
            # Update network state
            self.update_network_state()
            
            # Update from network state
            self.update_from_network_state()