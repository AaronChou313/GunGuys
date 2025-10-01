import pygame
import sys
from screens.main_menu import MainMenu

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("GunGuys")
    clock = pygame.time.Clock()
    
    # Initialize the main menu
    current_screen = MainMenu(screen)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Pass events to the current screen
            screen_result = current_screen.handle_event(event)
            if screen_result == "quit":
                running = False
            elif screen_result is not None:
                # Switch to the new screen
                current_screen = screen_result
        
        # Update the current screen
        if hasattr(current_screen, 'update'):
            current_screen.update(dt)
        else:
            current_screen.update()
        
        # Draw the current screen
        current_screen.draw()
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()