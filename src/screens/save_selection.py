import pygame
import os

class SaveSelection:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Create saves directory if it doesn't exist
        self.saves_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "saves")
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
        
        # Get list of save files
        self.save_files = [f for f in os.listdir(self.saves_dir) if f.endswith('.save')]
        
        # UI elements
        self.back_button = pygame.Rect(50, 50, 100, 40)
        self.select_button = pygame.Rect(screen.get_width() - 150, screen.get_height() - 100, 100, 40)
        
        # Selection
        self.selected_save = None
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                # Back button
                if self.back_button.collidepoint(event.pos):
                    from screens.main_menu import MainMenu
                    return MainMenu(self.screen)
                
                # Select button
                if self.select_button.collidepoint(event.pos) and self.selected_save is not None:
                    # Load selected save and start game
                    from screens.game_screen import GameScreen
                    save_file = self.save_files[self.selected_save]
                    return GameScreen(self.screen, save_file)
                
                # Save file selection
                for i, save_file in enumerate(self.save_files):
                    save_rect = pygame.Rect(100, 150 + i * 50, 600, 40)
                    if save_rect.collidepoint(event.pos):
                        self.selected_save = i
        
        if event.type == pygame.KEYDOWN:
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
        title = title_font.render("Select Save File", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Draw back button
        pygame.draw.rect(self.screen, (150, 150, 150), self.back_button)
        back_text = self.small_font.render("Back", True, (0, 0, 0))
        back_text_rect = back_text.get_rect(center=self.back_button.center)
        self.screen.blit(back_text, back_text_rect)
        
        # Draw save files
        if not self.save_files:
            no_saves_text = self.font.render("No save files found", True, (200, 200, 200))
            no_saves_rect = no_saves_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            self.screen.blit(no_saves_text, no_saves_rect)
        else:
            for i, save_file in enumerate(self.save_files):
                save_rect = pygame.Rect(100, 150 + i * 50, 600, 40)
                color = (100, 100, 150) if self.selected_save != i else (150, 150, 200)
                pygame.draw.rect(self.screen, color, save_rect)
                pygame.draw.rect(self.screen, (200, 200, 200), save_rect, 2)
                
                save_text = self.font.render(save_file, True, (255, 255, 255))
                save_text_rect = save_text.get_rect(midleft=(save_rect.left + 20, save_rect.centery))
                self.screen.blit(save_text, save_text_rect)
        
        # Draw select button
        if self.selected_save is not None:
            pygame.draw.rect(self.screen, (70, 130, 180), self.select_button)
            select_text = self.font.render("Enter", True, (255, 255, 255))
            select_text_rect = select_text.get_rect(center=self.select_button.center)
            self.screen.blit(select_text, select_text_rect)