import pygame
from screens.save_selection import SaveSelection
from screens.game_screen import GameScreen

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        
        # Define buttons
        button_width = 200
        button_height = 50
        button_margin = 20
        center_x = screen.get_width() // 2 - button_width // 2
        start_y = screen.get_height() // 2 - (4 * button_height + 3 * button_margin) // 2
        
        self.buttons = [
            {"rect": pygame.Rect(center_x, start_y, button_width, button_height),
             "text": "Start Game",
             "action": "start"},
            {"rect": pygame.Rect(center_x, start_y + (button_height + button_margin), button_width, button_height),
             "text": "Join Game",
             "action": "join"},
            {"rect": pygame.Rect(center_x, start_y + 2 * (button_height + button_margin), button_width, button_height),
             "text": "Settings",
             "action": "settings"},
            {"rect": pygame.Rect(center_x, start_y + 3 * (button_height + button_margin), button_width, button_height),
             "text": "Exit Game",
             "action": "exit"}
        ]
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                for button in self.buttons:
                    if button["rect"].collidepoint(event.pos):
                        return self.handle_action(button["action"])
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "quit"
                
        return None
    
    def handle_action(self, action):
        if action == "start":
            # Navigate to save selection screen
            save_selection = SaveSelection(self.screen)
            return save_selection
        elif action == "join":
            # For now, directly start a game for testing
            game_screen = GameScreen(self.screen)
            return game_screen
        elif action == "settings":
            # TODO: Implement settings functionality
            print("Settings button clicked")
            pass
        elif action == "exit":
            return "quit"
        return None
    
    def update(self, dt=None):
        pass
    
    def draw(self):
        self.screen.fill((50, 50, 50))  # Dark gray background
        
        # Draw title
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("GUNGUYS", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Draw buttons
        for button in self.buttons:
            pygame.draw.rect(self.screen, (70, 130, 180), button["rect"])  # Steel blue
            pygame.draw.rect(self.screen, (255, 255, 255), button["rect"], 2)  # White border
            
            text = self.font.render(button["text"], True, (255, 255, 255))
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)