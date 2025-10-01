import pygame
from network.network_manager import NetworkManager

class SettingsScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Network manager
        self.network_manager = NetworkManager()
        
        # Settings values
        self.difficulty = "Medium"  # Easy, Medium, Hard
        self.network_sharing = False
        self.game_name = "Player's Game"
        
        # UI elements
        self.back_button = pygame.Rect(50, 50, 100, 40)
        
        # Difficulty buttons
        self.difficulty_buttons = [
            {"rect": pygame.Rect(300, 200, 100, 40), "text": "Easy", "value": "Easy"},
            {"rect": pygame.Rect(300, 250, 100, 40), "text": "Medium", "value": "Medium"},
            {"rect": pygame.Rect(300, 300, 100, 40), "text": "Hard", "value": "Hard"}
        ]
        
        # Network sharing button
        self.network_button = pygame.Rect(250, 370, 200, 40)
        
        # Game name input
        self.game_name_rect = pygame.Rect(250, 420, 300, 40)
        self.game_name_active = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                # Back button
                if self.back_button.collidepoint(event.pos):
                    from screens.main_menu import MainMenu
                    return MainMenu(self.screen)
                
                # Difficulty buttons
                for button in self.difficulty_buttons:
                    if button["rect"].collidepoint(event.pos):
                        self.difficulty = button["value"]
                
                # Network sharing button
                if self.network_button.collidepoint(event.pos):
                    self.network_sharing = not self.network_sharing
                    
                    # Enable/disable network sharing
                    if self.network_sharing:
                        if self.network_manager.start_hosting(self.game_name):
                            print("Network sharing enabled")
                        else:
                            self.network_sharing = False
                            print("Failed to enable network sharing")
                    else:
                        self.network_manager.stop_networking()
                        print("Network sharing disabled")
                
                # Game name input
                if self.game_name_rect.collidepoint(event.pos):
                    self.game_name_active = True
                else:
                    self.game_name_active = False
        
        if event.type == pygame.KEYDOWN:
            if self.game_name_active:
                if event.key == pygame.K_BACKSPACE:
                    self.game_name = self.game_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.game_name_active = False
                else:
                    # Limit game name length
                    if len(self.game_name) < 20:
                        self.game_name += event.unicode
            
            if event.key == pygame.K_ESCAPE:
                from screens.main_menu import MainMenu
                return MainMenu(self.screen)
                
        return None
    
    def update(self, dt=None):
        pass
    
    def draw(self):
        self.screen.fill((50, 50, 50))  # Dark gray background
        
        # Draw title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("Settings", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Draw back button
        pygame.draw.rect(self.screen, (150, 150, 150), self.back_button)
        back_text = self.small_font.render("Back", True, (0, 0, 0))
        back_text_rect = back_text.get_rect(center=self.back_button.center)
        self.screen.blit(back_text, back_text_rect)
        
        # Draw difficulty settings
        difficulty_title = self.font.render("Difficulty:", True, (255, 255, 255))
        self.screen.blit(difficulty_title, (100, 150))
        
        for button in self.difficulty_buttons:
            color = (70, 130, 180) if self.difficulty == button["value"] else (100, 100, 150)
            pygame.draw.rect(self.screen, color, button["rect"])
            pygame.draw.rect(self.screen, (200, 200, 200), button["rect"], 2)
            
            text = self.font.render(button["text"], True, (255, 255, 255))
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)
        
        # Draw network sharing settings
        network_title = self.font.render("Network Sharing:", True, (255, 255, 255))
        self.screen.blit(network_title, (100, 370))
        
        network_color = (70, 130, 180) if self.network_sharing else (100, 100, 150)
        pygame.draw.rect(self.screen, network_color, self.network_button)
        pygame.draw.rect(self.screen, (200, 200, 200), self.network_button, 2)
        
        network_text = self.font.render(
            "ON" if self.network_sharing else "OFF", True, (255, 255, 255)
        )
        network_text_rect = network_text.get_rect(center=self.network_button.center)
        self.screen.blit(network_text, network_text_rect)
        
        # Draw game name settings
        name_title = self.font.render("Game Name:", True, (255, 255, 255))
        self.screen.blit(name_title, (100, 420))
        
        # Draw game name input box
        name_color = (70, 130, 180) if self.game_name_active else (100, 100, 150)
        pygame.draw.rect(self.screen, name_color, self.game_name_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.game_name_rect, 2)
        
        name_text = self.font.render(self.game_name, True, (255, 255, 255))
        self.screen.blit(name_text, (self.game_name_rect.x + 10, self.game_name_rect.y + 10))