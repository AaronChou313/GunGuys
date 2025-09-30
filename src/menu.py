import pygame
import sys
import threading
from network.network import NetworkManager

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (192, 192, 192)
DARK_GRAY = (64, 64, 64)
BLUE = (0, 128, 255)

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)
        self.running = True
        self.state = "main"  # main, settings, join_game
        self.game_shared = False
        self.discovered_games = []
        self.discovering = False
        
    def draw_text(self, text, font, color, x, y):
        """绘制文本"""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)
        
    def draw_button(self, text, x, y, width, height, hover=False):
        """绘制按钮"""
        color = LIGHT_GRAY if hover else GRAY
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)
        
        text_surface = self.font.render(text, True, BLACK)
        text_rect = text_surface.get_rect(center=(x + width//2, y + height//2))
        self.screen.blit(text_surface, text_rect)
        
        return pygame.Rect(x, y, width, height)
        
    def main_menu(self):
        """主菜单"""
        self.screen.fill(BLACK)
        
        # 绘制标题
        self.draw_text("GUNGUYS", self.title_font, BLUE, self.screen.get_width()//2, 150)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_click = True
                    
        # 绘制按钮
        start_button = self.draw_button("Start Game", 
                                       self.screen.get_width()//2 - 100, 
                                       300, 200, 50,
                                       pygame.Rect(self.screen.get_width()//2 - 100, 300, 200, 50).collidepoint(mouse_pos))
                                       
        join_button = self.draw_button("Join Game", 
                                      self.screen.get_width()//2 - 100, 
                                      370, 200, 50,
                                      pygame.Rect(self.screen.get_width()//2 - 100, 370, 200, 50).collidepoint(mouse_pos))
        
        settings_button = self.draw_button("Settings", 
                                          self.screen.get_width()//2 - 100, 
                                          440, 200, 50,
                                          pygame.Rect(self.screen.get_width()//2 - 100, 440, 200, 50).collidepoint(mouse_pos))
        
        quit_button = self.draw_button("Quit", 
                                      self.screen.get_width()//2 - 100, 
                                      510, 200, 50,
                                      pygame.Rect(self.screen.get_width()//2 - 100, 510, 200, 50).collidepoint(mouse_pos))
        
        # 检查按钮点击
        if mouse_click:
            if start_button.collidepoint(mouse_pos):
                return "start_game"
            elif join_button.collidepoint(mouse_pos):
                self.state = "join_game"
            elif settings_button.collidepoint(mouse_pos):
                self.state = "settings"
            elif quit_button.collidepoint(mouse_pos):
                return "quit"
                
        return None
        
    def settings_menu(self):
        """设置菜单"""
        self.screen.fill(BLACK)
        
        # 绘制标题
        self.draw_text("SETTINGS", self.title_font, BLUE, self.screen.get_width()//2, 100)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_click = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "main"
                    
        # 绘制游戏共享选项
        self.draw_text("Game Sharing:", self.font, WHITE, self.screen.get_width()//2 - 100, 250)
        
        # 绘制开关按钮
        switch_color = BLUE if self.game_shared else GRAY
        switch_rect = pygame.Rect(self.screen.get_width()//2 + 50, 235, 60, 30)
        pygame.draw.rect(self.screen, switch_color, switch_rect)
        pygame.draw.rect(self.screen, WHITE, switch_rect, 2)
        
        # 开关按钮的小圆圈
        circle_x = self.screen.get_width()//2 + 55 if not self.game_shared else self.screen.get_width()//2 + 85
        pygame.draw.circle(self.screen, WHITE, (circle_x, 250), 10)
        
        # 检查开关点击
        if mouse_click and switch_rect.collidepoint(mouse_pos):
            self.game_shared = not self.game_shared
            
        # 绘制返回按钮
        back_button = self.draw_button("Back", 
                                      50, 50, 100, 40,
                                      pygame.Rect(50, 50, 100, 40).collidepoint(mouse_pos))
        
        # 绘制保存并退出按钮
        save_button = self.draw_button("Save and Exit", 
                                      self.screen.get_width()//2 - 100, 
                                      400, 200, 50,
                                      pygame.Rect(self.screen.get_width()//2 - 100, 400, 200, 50).collidepoint(mouse_pos))
        
        # 绘制退出按钮
        quit_button = self.draw_button("Quit", 
                                      self.screen.get_width()//2 - 100, 
                                      460, 200, 50,
                                      pygame.Rect(self.screen.get_width()//2 - 100, 460, 200, 50).collidepoint(mouse_pos))
        
        # 检查按钮点击
        if mouse_click:
            if back_button.collidepoint(mouse_pos):
                self.state = "main"
            elif save_button.collidepoint(mouse_pos):
                self.state = "main"
            elif quit_button.collidepoint(mouse_pos):
                return "quit"
                
        return None
        
    def join_game_menu(self):
        """加入游戏菜单"""
        self.screen.fill(BLACK)
        
        # 绘制标题
        self.draw_text("JOIN GAME", self.title_font, BLUE, self.screen.get_width()//2, 100)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_click = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "main"
                    
        # 显示"搜索中..."文本或搜索按钮
        if self.discovering:
            self.draw_text("Searching for games...", self.font, WHITE, self.screen.get_width()//2, 250)
        else:
            search_button = self.draw_button("Search for Games", 
                                            self.screen.get_width()//2 - 150, 
                                            250, 300, 50,
                                            pygame.Rect(self.screen.get_width()//2 - 150, 250, 300, 50).collidepoint(mouse_pos))
            
            if mouse_click and search_button.collidepoint(mouse_pos):
                self.discovering = True
                # 在后台线程中搜索游戏
                discovery_thread = threading.Thread(target=self._discover_games)
                discovery_thread.daemon = True
                discovery_thread.start()
        
        # 显示找到的游戏列表
        if self.discovered_games:
            self.draw_text("Local Network Games:", self.font, WHITE, self.screen.get_width()//2, 320)
            
            for i, game in enumerate(self.discovered_games):
                game_text = f"{game['name']} ({game['players']} players)"
                game_button = self.draw_button(game_text, 
                                              self.screen.get_width()//2 - 150, 
                                              370 + i * 60, 300, 50,
                                              pygame.Rect(self.screen.get_width()//2 - 150, 370 + i * 60, 300, 50).collidepoint(mouse_pos))
                
                if mouse_click and game_button.collidepoint(mouse_pos):
                    return {"action": "join_game", "host": game["host"], "port": game["port"]}
        
        # 绘制返回按钮
        back_button = self.draw_button("Back", 
                                      50, 50, 100, 40,
                                      pygame.Rect(50, 50, 100, 40).collidepoint(mouse_pos))
        
        # 绘制退出按钮
        quit_button = self.draw_button("Quit", 
                                      self.screen.get_width()//2 - 100, 
                                      550, 200, 50,
                                      pygame.Rect(self.screen.get_width()//2 - 100, 550, 200, 50).collidepoint(mouse_pos))
        
        # 检查返回按钮点击
        if mouse_click:
            if back_button.collidepoint(mouse_pos):
                self.state = "main"
            elif quit_button.collidepoint(mouse_pos):
                return "quit"
            
        return None
        
    def _discover_games(self):
        """在后台线程中发现游戏"""
        self.discovered_games = NetworkManager.discover_games()
        self.discovering = False
        
    def run(self):
        """运行菜单"""
        while self.running:
            if self.state == "main":
                result = self.main_menu()
                if result == "start_game":
                    return {"action": "start_game", "share_game": self.game_shared}
                elif result == "quit":
                    return {"action": "quit"}
            elif self.state == "settings":
                result = self.settings_menu()
                if result == "quit":
                    return {"action": "quit"}
            elif self.state == "join_game":
                result = self.join_game_menu()
                if result and isinstance(result, dict) and result.get("action") == "join_game":
                    return result
                elif result == "quit":
                    return {"action": "quit"}
                    
            pygame.display.flip()
            
        return {"action": "quit"}