import pygame
import threading
import time
from network.network_manager import NetworkManager

class JoinGameScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Network manager
        self.network_manager = NetworkManager()
        
        # Discovered games
        self.discovered_games = []
        self.selected_game = None
        
        # UI elements
        self.back_button = pygame.Rect(50, 50, 100, 40)
        self.refresh_button = pygame.Rect(screen.get_width() - 150, 50, 100, 40)
        self.join_button = pygame.Rect(screen.get_width() - 150, screen.get_height() - 100, 100, 40)
        
        # Start discovery
        self.network_manager.discovery_running = True
        discovery_thread = threading.Thread(target=self._continuous_discovery)
        discovery_thread.daemon = True
        discovery_thread.start()
        
        # Give some time for discovery
        time.sleep(0.1)
        self.discover_games()
        
        # Error message
        self.error_message = ""
        self.error_time = 0
        
    def _continuous_discovery(self):
        """Continuously discover games"""
        # Start listening for other broadcasts
        self.network_manager._discover_games()
        
    def discover_games(self):
        """Discover games on the local network"""
        self.discovered_games = self.network_manager.get_discovered_games()
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                # Back button
                if self.back_button.collidepoint(event.pos):
                    from screens.main_menu import MainMenu
                    return MainMenu(self.screen)
                
                # Refresh button
                if self.refresh_button.collidepoint(event.pos):
                    self.discover_games()
                
                # Join button
                if self.join_button.collidepoint(event.pos) and self.selected_game is not None:
                    # Connect to the selected game
                    game = self.discovered_games[self.selected_game]
                    print(f"Attempting to connect to {game['name']} at {game['host']}:{game['port']}")
                    if self.network_manager.connect_to_game(game["host"], game["port"]):
                        # TODO: Navigate to game screen
                        from screens.game_screen import GameScreen
                        return GameScreen(self.screen)
                    else:
                        print("Failed to connect to game")
                        # Show error message
                        self.error_message = "Failed to connect to game"
                        self.error_time = time.time()
                
                # Game selection
                for i, game in enumerate(self.discovered_games):
                    game_rect = pygame.Rect(100, 150 + i * 60, 600, 50)
                    if game_rect.collidepoint(event.pos):
                        self.selected_game = i
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from screens.main_menu import MainMenu
                return MainMenu(self.screen)
                
        return None
    
    def update(self, dt=None):
        # Update discovered games periodically
        self.discover_games()
        
        # Clear error message after 3 seconds
        if self.error_message and time.time() - self.error_time > 3:
            self.error_message = ""
    
    def draw(self):
        self.screen.fill((50, 50, 50))  # Dark gray background
        
        # Draw title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("Join Game", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Draw back button
        pygame.draw.rect(self.screen, (150, 150, 150), self.back_button)
        back_text = self.small_font.render("Back", True, (0, 0, 0))
        back_text_rect = back_text.get_rect(center=self.back_button.center)
        self.screen.blit(back_text, back_text_rect)
        
        # Draw refresh button
        pygame.draw.rect(self.screen, (70, 130, 180), self.refresh_button)
        refresh_text = self.small_font.render("Refresh", True, (255, 255, 255))
        refresh_text_rect = refresh_text.get_rect(center=self.refresh_button.center)
        self.screen.blit(refresh_text, refresh_text_rect)
        
        # Draw discovered games
        if not self.discovered_games:
            no_games_text = self.font.render("No games found", True, (200, 200, 200))
            no_games_rect = no_games_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            self.screen.blit(no_games_text, no_games_rect)
        else:
            for i, game in enumerate(self.discovered_games):
                game_rect = pygame.Rect(100, 150 + i * 60, 600, 50)
                color = (100, 100, 150) if self.selected_game != i else (150, 150, 200)
                pygame.draw.rect(self.screen, color, game_rect)
                pygame.draw.rect(self.screen, (200, 200, 200), game_rect, 2)
                
                game_text = self.font.render(f"{game['name']} ({game['host']})", True, (255, 255, 255))
                game_text_rect = game_text.get_rect(midleft=(game_rect.left + 20, game_rect.centery))
                self.screen.blit(game_text, game_text_rect)
        
        # Draw join button
        if self.selected_game is not None:
            pygame.draw.rect(self.screen, (70, 130, 180), self.join_button)
            join_text = self.font.render("Join", True, (255, 255, 255))
            join_text_rect = join_text.get_rect(center=self.join_button.center)
            self.screen.blit(join_text, join_text_rect)
        
        # Draw error message if exists
        if self.error_message and time.time() - self.error_time < 3:
            error_text = self.font.render(self.error_message, True, (255, 0, 0))
            error_rect = error_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
            self.screen.blit(error_text, error_rect)