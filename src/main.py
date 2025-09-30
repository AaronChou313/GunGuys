import pygame
import sys
import math
import random
import time
from entities.player import Player
from systems.camera import Camera
from entities.weapon import Projectile, MagicProjectile, PiercingProjectile, ExplosiveProjectile, MagicZone, Sword, Dagger
from network.network import NetworkManager
from menu import Menu

# 初始化Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("GunGuys - 2D Shooter Game")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 游戏状态
        self.in_menu = True
        self.in_game = False
        self.show_settings = False
        self.player_dead = False  # 玩家死亡状态
        
        # ESC键防抖计时器
        self.last_escape_time = 0
        self.escape_cooldown = 0.5  # 0.5秒冷却时间
        
        # 创建玩家和摄像机
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.spawn_x = SCREEN_WIDTH // 2  # 出生点X坐标
        self.spawn_y = SCREEN_HEIGHT // 2  # 出生点Y坐标
        
        # 子弹列表
        self.projectiles = []
        
        # 魔法区域列表
        self.magic_zones = []
        
        # 爆炸效果列表
        self.explosion_effects = []
        
        # 敌人列表（用于PVE模式）
        self.enemies = []
        
        # 网络玩家列表
        self.network_players = {}
        
        # 鼠标位置
        self.mouse_x, self.mouse_y = 0, 0
        
        # 游戏模式：0-单人PVE, 1-多人PVE, 2-PVP
        self.game_mode = 0
        
        # PVE难度: 0-简单, 1-均衡, 2-困难
        self.pve_difficulty = 1
        
        # 网络管理器
        self.network_manager = None
        self.is_host = False
        self.game_shared = False
        
        # 上次射击时间
        self.last_shot_time = 0
        
    def run(self):
        while self.running:
            if self.in_menu:
                menu = Menu(self.screen)
                result = menu.run()
                
                if result["action"] == "start_game":
                    self.in_menu = False
                    self.in_game = True
                    self.game_shared = result["share_game"]
                    # 如果开启了游戏共享，则启动服务器
                    if self.game_shared:
                        if not self.start_network_game(True):
                            # 如果启动失败，继续保持在菜单状态
                            self.in_menu = True
                            self.in_game = False
                elif result["action"] == "join_game":
                    self.in_menu = False
                    self.in_game = True
                    if not self.start_network_game(False, result.get("host"), result.get("port")):
                        # 如果连接失败，继续保持在菜单状态
                        self.in_menu = True
                        self.in_game = False
                elif result["action"] == "quit":
                    self.running = False
                    break
                    
            elif self.in_game:
                # 处理事件
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # 使用计时器防抖ESC键
                            import time
                            current_time = time.time()
                            if current_time - self.last_escape_time > self.escape_cooldown:
                                self.last_escape_time = current_time
                                if not self.player_dead:  # 玩家未死亡时才切换设置界面
                                    self.show_settings = not self.show_settings
                        elif event.key == pygame.K_1:
                            self.player.switch_weapon(0)
                        elif event.key == pygame.K_2:
                            self.player.switch_weapon(1)
                        elif event.key == pygame.K_3:
                            self.player.switch_weapon(2)
                        elif event.key == pygame.K_4:
                            self.player.switch_weapon(3)
                        elif event.key == pygame.K_5:
                            self.player.switch_weapon(4)
                        elif event.key == pygame.K_6:
                            self.player.switch_weapon(5)
                        elif event.key == pygame.K_7:
                            self.player.switch_weapon(6)
                        elif event.key == pygame.K_8:
                            self.player.switch_weapon(7)
                        elif event.key == pygame.K_e:
                            self.player.switch_to_next_weapon()
                        elif event.key == pygame.K_q:
                            self.player.switch_to_previous_weapon()
                        elif event.key == pygame.K_F1:
                            self.game_mode = (self.game_mode + 1) % 3
                        elif event.key == pygame.K_r and self.player_dead:  # 复活键
                            self.respawn_player()
                        elif event.key == pygame.K_m and self.player_dead:  # 回到主菜单
                            self.return_to_menu()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # 左键射击
                            if not self.show_settings and not self.player_dead:  # 只有在不显示设置且玩家未死亡时才能射击
                                self.shoot()
                            elif self.show_settings:  # 处理设置界面点击
                                self.handle_settings_click(event.pos)
                
                # 更新鼠标位置
                self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                
                # 更新游戏状态
                self.update()
                
                # 绘制游戏画面
                self.draw()
                
                # 控制帧率
                self.clock.tick(FPS)
                
                # 检查是否需要返回菜单（网络连接失败等情况）
                if not self.in_game and self.in_menu:
                    continue  # 跳过本次循环，重新进入菜单
        
        # 断开网络连接
        if self.network_manager:
            self.network_manager.disconnect()
            
        pygame.quit()
        sys.exit()
    
    def return_to_menu(self):
        """返回主菜单"""
        self.in_game = False
        self.in_menu = True
        self.player_dead = False
        self.show_settings = False
        self.projectiles.clear()
        self.magic_zones.clear()
        self.enemies.clear()
        self.network_players.clear()
        
        # 断开网络连接
        if self.network_manager:
            self.network_manager.disconnect()
            self.network_manager = None
    
    def handle_settings_click(self, pos):
        """处理设置界面点击"""
        # 检查是否点击了返回主菜单按钮
        menu_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 20, 200, 40)
        if menu_button.collidepoint(pos):
            self.show_settings = False
            self.return_to_menu()
            return
        
        # 检查是否点击了退出游戏按钮
        quit_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 40, 200, 40)
        if quit_button.collidepoint(pos):
            self.running = False
    
    def spawn_enemy(self):
        """生成敌人"""
        # 在屏幕边缘随机生成敌人
        side = random.randint(0, 3)  # 0: top, 1: right, 2: bottom, 3: left
        
        if side == 0:  # top
            x = random.randint(0, SCREEN_WIDTH)
            y = -30
        elif side == 1:  # right
            x = SCREEN_WIDTH + 30
            y = random.randint(0, SCREEN_HEIGHT)
        elif side == 2:  # bottom
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT + 30
        else:  # left
            x = -30
            y = random.randint(0, SCREEN_HEIGHT)
            
        # 根据难度创建敌人
        enemy = Enemy(x, y, self.pve_difficulty)
        self.enemies.append(enemy)
    
    def draw(self):
        """绘制游戏画面"""
        # 绘制网格背景
        self.draw_grid_background()
        
        # 获取摄像机位置
        camera_x, camera_y = self.camera.x, self.camera.y
        
        # 绘制所有子弹
        for projectile in self.projectiles:
            projectile.draw(self.screen, camera_x, camera_y)
            
        # 绘制所有魔法区域
        for magic_zone in self.magic_zones:
            magic_zone.draw(self.screen, camera_x, camera_y)
            
        # 绘制所有爆炸效果
        for explosion_effect in self.explosion_effects[:]:
            explosion_effect.draw(self.screen, camera_x, camera_y)
            if not explosion_effect.is_active():
                self.explosion_effects.remove(explosion_effect)
            
        # 绘制所有敌人
        for enemy in self.enemies:
            enemy.draw(self.screen, camera_x, camera_y)
            
        # 绘制所有网络玩家
        for net_player in self.network_players.values():
            net_player.draw(self.screen, camera_x, camera_y)
            
        # 绘制近战武器攻击范围（如果玩家使用近战武器）
        if isinstance(self.player.current_weapon, (Sword, Dagger)) and not self.player_dead:
            self.draw_melee_range(camera_x, camera_y)
            
        # 绘制玩家（除非死亡）
        if not self.player_dead:
            self.player.draw(self.screen, camera_x, camera_y)
            
        # 绘制UI元素
        self.draw_ui()
        
        # 如果显示设置界面，绘制设置界面
        if self.show_settings:
            self.draw_settings()
            
        # 如果玩家死亡，绘制死亡界面
        if self.player_dead:
            self.draw_death_screen()
        
        # 更新显示
        pygame.display.flip()
    
    def _is_player_in_enemy_attack_range(self, enemy):
        """检查玩家是否在敌人的扇形攻击范围内"""
        # 计算敌人到玩家的方向
        dx = self.player.x - enemy.x
        dy = self.player.y - enemy.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # 如果距离太远，不在攻击范围内
        if distance > 50:  # 攻击范围半径
            return False
        
        # 计算敌人面向玩家的方向
        # 简化处理：敌人总是面向玩家
        enemy_direction = (dx / distance, dy / distance) if distance > 0 else (1, 0)
        
        # 计算玩家相对于敌人正前方的角度
        # 这里简化处理，只要在一定距离内就算在攻击范围内
        return True
    
    def _apply_knockback(self, target, source):
        """应用击退效果"""
        # 计算从源到目标的方向
        dx = target.x - source.x
        dy = target.y - source.y
        distance = max(0.1, math.sqrt(dx*dx + dy*dy))
        
        # 标准化方向向量
        dx_normalized = dx / distance
        dy_normalized = dy / distance
        
        # 应击退力（根据质量调整）
        knockback_force = 8.0
        target.vx += dx_normalized * knockback_force * (source.mass / target.mass)
        target.vy += dy_normalized * knockback_force * (source.mass / target.mass)
    
    def draw_melee_range(self, camera_x, camera_y):
        """绘制近战武器攻击范围"""
        # 计算玩家中心点
        player_center_x = self.player.x + self.player.width // 2
        player_center_y = self.player.y + self.player.height // 2
        
        # 获取鼠标位置（相对于屏幕）
        mouse_screen_x = self.mouse_x
        mouse_screen_y = self.mouse_y
        
        # 计算鼠标相对于玩家的位置
        mouse_rel_x = mouse_screen_x - (SCREEN_WIDTH // 2)
        mouse_rel_y = mouse_screen_y - (SCREEN_HEIGHT // 2)
        
        # 计算鼠标方向
        magnitude = max(math.sqrt(mouse_rel_x**2 + mouse_rel_y**2), 0.1)
        direction_x = mouse_rel_x / magnitude
        direction_y = mouse_rel_y / magnitude
        
        # 计算攻击范围的起始点和结束点
        start_x = player_center_x - camera_x
        start_y = player_center_y - camera_y
        end_x = start_x + direction_x * self.player.current_weapon.range
        end_y = start_y + direction_y * self.player.current_weapon.range
        
        # 绘制攻击线
        pygame.draw.line(self.screen, (255, 255, 0, 128), (start_x, start_y), (end_x, end_y), 3)
        
        # 绘制攻击范围圆弧（扇形）
        angle = math.atan2(direction_y, direction_x)
        arc_start_angle = angle - math.pi/4  # 45度扇形
        arc_end_angle = angle + math.pi/4
        
        # 绘制扇形边界线
        arc_start_x = start_x + math.cos(arc_start_angle) * self.player.current_weapon.range
        arc_start_y = start_y + math.sin(arc_start_angle) * self.player.current_weapon.range
        arc_end_x = start_x + math.cos(arc_end_angle) * self.player.current_weapon.range
        arc_end_y = start_y + math.sin(arc_end_angle) * self.player.current_weapon.range
        
        pygame.draw.line(self.screen, (255, 255, 0, 128), (start_x, start_y), (arc_start_x, arc_start_y), 2)
        pygame.draw.line(self.screen, (255, 255, 0, 128), (start_x, start_y), (arc_end_x, arc_end_y), 2)
        
        # 绘制扇形弧线（修正方向）
        rect = pygame.Rect(start_x - self.player.current_weapon.range, 
                          start_y - self.player.current_weapon.range,
                          self.player.current_weapon.range * 2, 
                          self.player.current_weapon.range * 2)
        pygame.draw.arc(self.screen, (255, 255, 0, 128), rect, -arc_end_angle, -arc_start_angle, 2)
    
    def draw_grid_background(self):
        """绘制网格背景"""
        # 填充背景色
        self.screen.fill((30, 30, 30))
        
        # 获取摄像机位置
        camera_x, camera_y = self.camera.x, self.camera.y
        
        # 绘制网格线
        grid_size = 50
        
        # 计算可见区域的网格线范围
        start_x = (camera_x // grid_size) * grid_size - camera_x
        start_y = (camera_y // grid_size) * grid_size - camera_y
        end_x = start_x + SCREEN_WIDTH + grid_size
        end_y = start_y + SCREEN_HEIGHT + grid_size
        
        # 绘制垂直线
        for x in range(int(start_x), int(end_x), grid_size):
            pygame.draw.line(self.screen, (40, 40, 40), (x, start_y), (x, end_y))
        
        # 绘制水平线
        for y in range(int(start_y), int(end_y), grid_size):
            pygame.draw.line(self.screen, (40, 40, 40), (start_x, y), (end_x, y))
    
    def draw_ui(self):
        """绘制UI元素"""
        # 创建字体对象
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        # 绘制生命值
        health_text = font.render(f"Health: {int(self.player.health)}", True, WHITE)
        self.screen.blit(health_text, (10, 10))
        
        # 绘制等级和经验值
        level_text = font.render(f"Level: {self.player.level} XP: {self.player.experience}/{self.player.experience_to_next_level}", True, WHITE)
        self.screen.blit(level_text, (10, 40))
        
        # 绘制当前武器
        weapon_text = font.render(f"Weapon: {self.player.current_weapon.name}", True, WHITE)
        self.screen.blit(weapon_text, (10, 70))
        
        # 绘制游戏模式
        mode_names = ["Single Player", "Multiplayer PVE", "PVP"]
        mode_text = font.render(f"Mode: {mode_names[self.game_mode]}", True, WHITE)
        self.screen.blit(mode_text, (10, 100))
        
        # 绘制武器快捷键提示
        hint_text = small_font.render("Press 1-8 or E/Q to switch weapons", True, WHITE)
        self.screen.blit(hint_text, (10, SCREEN_HEIGHT - 30))
        
        # 绘制攻击冷却条
        self._draw_attack_cooldown_bar()
        
    def _draw_attack_cooldown_bar(self):
        """绘制攻击冷却条"""
        import time
        
        # 计算攻击冷却时间
        current_time = time.time()
        base_interval = 1.0 / self.player.current_weapon.fire_rate
        # 每升一级减少5%的攻击间隔
        level_modifier = 0.05 * (self.player.level - 1)
        actual_interval = max(0.1, base_interval * (1 - level_modifier))  # 最小间隔0.1秒
        
        # 计算冷却进度
        time_since_last_shot = current_time - self.player.current_weapon.last_shot_time
        cooldown_progress = min(1.0, time_since_last_shot / actual_interval)
        
        # 冷却条位置和尺寸
        bar_x = 10
        bar_y = SCREEN_HEIGHT - 70
        bar_width = 200
        bar_height = 20
        
        # 绘制冷却条背景
        pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        
        # 绘制冷却进度
        if cooldown_progress < 1.0:
            # 正在冷却中，绘制红色进度条
            pygame.draw.rect(self.screen, (255, 0, 0), (bar_x, bar_y, bar_width * cooldown_progress, bar_height))
        else:
            # 可以攻击，绘制绿色进度条
            pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # 绘制边框
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # 绘制文字提示
        # 创建字体对象
        font = pygame.font.Font(None, 24)
        if cooldown_progress < 1.0:
            cooldown_text = font.render(f"Cooldown: {int((1 - cooldown_progress) * actual_interval * 1000)}ms", True, WHITE)
        else:
            cooldown_text = font.render("Ready to Attack!", True, WHITE)
        self.screen.blit(cooldown_text, (bar_x + 5, bar_y + 2))
    
    def draw_settings(self):
        """绘制设置界面"""
        # 绘制半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # 绘制设置框
        settings_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 150, 400, 300)
        pygame.draw.rect(self.screen, (64, 64, 64), settings_rect)
        pygame.draw.rect(self.screen, WHITE, settings_rect, 2)
        
        # 创建字体对象
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        # 绘制标题
        title_text = font.render("Settings", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//2 - 140))
        
        # 绘制说明文字
        resume_text = small_font.render("Press ESC to resume game", True, WHITE)
        self.screen.blit(resume_text, (SCREEN_WIDTH//2 - resume_text.get_width()//2, SCREEN_HEIGHT//2 - 110))
        
        # 绘制返回主菜单按钮
        menu_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 20, 200, 40)
        pygame.draw.rect(self.screen, (100, 100, 100), menu_button)
        pygame.draw.rect(self.screen, WHITE, menu_button, 2)
        menu_text = small_font.render("Return to Main Menu", True, WHITE)
        self.screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, SCREEN_HEIGHT//2 - 10))
        
        # 绘制退出游戏按钮
        quit_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 40, 200, 40)
        pygame.draw.rect(self.screen, (100, 100, 100), quit_button)
        pygame.draw.rect(self.screen, WHITE, quit_button, 2)
        quit_text = small_font.render("Quit Game", True, WHITE)
        self.screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
        
    def draw_death_screen(self):
        """绘制死亡界面"""
        # 绘制半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(192)
        overlay.fill(RED)
        self.screen.blit(overlay, (0, 0))
        
        # 创建字体对象
        title_font = pygame.font.Font(None, 72)
        font = pygame.font.Font(None, 36)
        
        # 绘制死亡文本
        death_text = title_font.render("YOU DIED", True, WHITE)
        self.screen.blit(death_text, (SCREEN_WIDTH//2 - death_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        
        # 绘制复活提示
        respawn_text = font.render("Press R to Respawn or M to Return to Menu", True, WHITE)
        self.screen.blit(respawn_text, (SCREEN_WIDTH//2 - respawn_text.get_width()//2, SCREEN_HEIGHT//2))
    
    def start_network_game(self, is_host: bool, host: str = None, port: int = None):
        """开始网络游戏"""
        self.is_host = is_host
        
        if is_host:
            # 启动服务器
            self.network_manager = NetworkManager()
            if self.network_manager.start_server("GunGuys Game"):
                self.game_mode = 1  # 设置为多人PVE模式
                print("Network server started")
                return True
            else:
                print("Failed to start network server")
                # 如果启动失败，返回菜单
                self.in_game = False
                self.in_menu = True
                self.network_manager = None
                return False
        else:
            # 连接到服务器
            self.network_manager = NetworkManager()
            connect_result = self.network_manager.connect_to_server(host, port) if host and port else self.network_manager.connect_to_server()
            if connect_result:
                self.game_mode = 1  # 设置为多人PVE模式
                # 注册数据接收回调
                self.network_manager.on_data_received = self.handle_network_data
                # 发送玩家初始数据
                self.send_player_data()
                print("Connected to network server")
                return True
            else:
                print("Failed to connect to network server")
                # 如果连接失败，返回菜单
                self.in_game = False
                self.in_menu = True
                self.network_manager = None
                return False
    
    def send_player_data(self):
        """发送玩家数据到网络"""
        if not self.network_manager or not self.network_manager.is_connected:
            return
            
        player_data = {
            "type": "player_update",
            "player_id": self.player.player_id,
            "x": self.player.x,
            "y": self.player.y,
            "health": self.player.health,
            "max_health": self.player.max_health,
            "level": self.player.level,
            "weapon": self.player.current_weapon.name,
            "dead": self.player_dead
        }
        
        self.network_manager.send_data(player_data)
    
    def handle_network_data(self, data: dict):
        """处理网络数据"""
        if data["type"] == "player_update":
            player_id = data["player_id"]
            if player_id != self.player.player_id:  # 不是自己的数据
                if player_id not in self.network_players:
                    # 创建新的网络玩家
                    self.network_players[player_id] = NetworkPlayer(
                        data["x"], data["y"], player_id)
                
                # 更新网络玩家数据
                net_player = self.network_players[player_id]
                net_player.x = data["x"]
                net_player.y = data["y"]
                net_player.health = data["health"]
                net_player.max_health = data.get("max_health", 100)
                net_player.level = data["level"]
                net_player.weapon = data["weapon"]
                net_player.dead = data.get("dead", False)
                net_player.rect.x = net_player.x
                net_player.rect.y = net_player.y
    
    def shoot(self):
        """玩家射击"""
        # 计算从玩家到鼠标的向量
        dx = self.mouse_x - (SCREEN_WIDTH // 2)
        dy = self.mouse_y - (SCREEN_HEIGHT // 2)
        
        # 归一化方向向量
        magnitude = max(math.sqrt(dx*dx + dy*dy), 0.1)  # 避免除零
        direction = (dx/magnitude, dy/magnitude)
        
        # 创建子弹或执行近战攻击
        projectile = self.player.shoot(direction)
        
        # 检查是否是近战武器
        if isinstance(self.player.current_weapon, (type(self.player.weapons[6]), type(self.player.weapons[7]))):  # Sword or Dagger
            # 近战攻击
            targets = self.player.get_melee_targets(direction, self.enemies)
            for enemy in targets:
                enemy.health -= self.player.current_weapon.damage
                if enemy.health <= 0:
                    self.player.gain_experience(10)
                    self.enemies.remove(enemy)
                else:
                    # 添加更强的击退效果
                    self._apply_knockback(enemy, self.player)
                    # 额外添加一个反向力，增强击退效果
                    weapon_knockback = 10.0
                    # 剑的击退效果更强
                    if isinstance(self.player.current_weapon, type(self.player.weapons[6])):  # Sword
                        weapon_knockback = 15.0
                                            
                    enemy.vx += direction[0] * weapon_knockback
                    enemy.vy += direction[1] * weapon_knockback
        else:
            # 远程攻击
            if projectile:
                self.projectiles.append(projectile)
                # 如果是魔法弹，设置最大穿透距离基于玩家等级
                if isinstance(projectile, PiercingProjectile):
                    projectile.max_distance = 300 + (self.player.level * 20)
        
        # 在网络游戏中发送射击信息
        if self.network_manager and self.network_manager.is_connected:
            shoot_data = {
                "type": "shoot",
                "player_id": self.player.player_id,
                "x": self.player.x,
                "y": self.player.y,
                "direction": direction
            }
            self.network_manager.send_data(shoot_data)
    
    def update(self):
        # 只有在不显示设置界面时才更新游戏状态（单人模式下）
        # 多人模式下即使显示设置界面也继续更新游戏状态
        if not self.show_settings or self.game_mode != 0 or self.player_dead:
            # 处理玩家输入
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 1
                
            # 移动玩家（支持物理和碰撞检测）
            if not self.player_dead:  # 玩家未死亡时才能移动
                self.player.move(dx, dy, self.enemies)
            
            # 更新摄像机以跟随玩家
            self.camera.update(self.player)
            
            # 发送玩家数据（如果在网络模式下）
            if self.network_manager and self.network_manager.is_connected:
                self.send_player_data()
            
            # 更新子弹
            for projectile in self.projectiles[:]:  # 使用切片复制避免迭代时修改列表
                projectile.update()
                
                # 特殊子弹处理
                if isinstance(projectile, type(None)):
                    # 跳过None子弹（近战武器）
                    continue
                elif hasattr(projectile, 'exploded') and projectile.exploded:
                    # 已爆炸的子弹直接移除
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    continue
                elif hasattr(projectile, 'distance_traveled') and projectile.distance_traveled >= projectile.max_distance:
                    # 魔法弹达到最大距离，创建法阵
                    magic_zone = MagicZone(projectile.x, projectile.y, 30, max(1, projectile.damage // 4), 3)
                    self.magic_zones.append(magic_zone)
                    magic_zone.activate()
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    continue
                
                # 简单的边界检查，超出屏幕一定距离则删除
                if (abs(projectile.x - self.player.x) > SCREEN_WIDTH or 
                    abs(projectile.y - self.player.y) > SCREEN_HEIGHT):
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    continue
                    
                # 检查子弹是否击中敌人
                for enemy in self.enemies[:]:
                    if enemy.rect.colliderect(projectile.rect):
                        # 根据子弹类型处理不同效果
                        if isinstance(projectile, PiercingProjectile):
                            # 穿透子弹
                            enemy.health -= projectile.damage
                            projectile.pierced_count += 1
                            
                            # 检查是否达到最大穿透数（基于玩家等级）
                            max_pierce = projectile.max_pierce + (self.player.level // 5)
                            if projectile.pierced_count >= max_pierce:
                                if projectile in self.projectiles:
                                    self.projectiles.remove(projectile)
                            else:
                                # 根据武器类型添加不同强度的击退效果
                                knockback_force = 3.0
                                # 狙击枪击退效果最强
                                if hasattr(projectile, 'weapon_type') and projectile.weapon_type == "sniper":
                                    knockback_force = 15.0
                                elif hasattr(projectile, 'weapon_type') and projectile.weapon_type == "rocket":
                                    knockback_force = 12.0
                                elif hasattr(projectile, 'weapon_type') and projectile.weapon_type == "wand":
                                    knockback_force = 3.0
                                    # 法杖攻击命中时生成法阵
                                    magic_zone = MagicZone(enemy.x, enemy.y, 30, max(1, projectile.damage // 4), 3)
                                    self.magic_zones.append(magic_zone)
                                    magic_zone.activate()
                                
                                enemy.vx += projectile.direction[0] * knockback_force
                                enemy.vy += projectile.direction[1] * knockback_force
                        elif isinstance(projectile, ExplosiveProjectile):
                            # 爆炸子弹，对范围内敌人造成伤害
                            for e in self.enemies[:]:
                                distance = math.sqrt((e.x - projectile.x)**2 + (e.y - projectile.y)**2)
                                if distance <= projectile.explosion_radius:
                                    e.health -= projectile.damage * (1 - distance/projectile.explosion_radius)  # 距离越远伤害越低
                                    if e.health <= 0 and e in self.enemies:
                                        self.player.gain_experience(10)
                                        self.enemies.remove(e)
                                    else:
                                        # 添加爆炸击退效果
                                        if distance > 0:
                                            knockback_force = 2.0 * (1 - distance/projectile.explosion_radius)
                                            dx = e.x - projectile.x
                                            dy = e.y - projectile.y
                                            # 根据武器类型添加不同强度的击退效果
                                            explosive_knockback = knockback_force * 2.0
                                            if hasattr(projectile, 'weapon_type') and projectile.weapon_type == "rocket":
                                                explosive_knockback = knockback_force * 4.0
                                            
                                            e.vx += dx / distance * explosive_knockback
                                            e.vy += dy / distance * explosive_knockback
                            
                            # 创建爆炸效果可视化
                            explosion_effect = ExplosionEffect(projectile.x, projectile.y, projectile.explosion_radius)
                            self.explosion_effects.append(explosion_effect)
                            
                            # 标记子弹已爆炸
                            projectile.exploded = True
                            if projectile in self.projectiles:
                                self.projectiles.remove(projectile)
                        else:
                            # 普通子弹
                            enemy.health -= projectile.damage
                            if projectile in self.projectiles:
                                self.projectiles.remove(projectile)
                                
                        # 检查敌人是否死亡
                        if enemy.health <= 0 and enemy in self.enemies:
                            self.player.gain_experience(10)
                            self.enemies.remove(enemy)
                        else:
                            # 根据武器类型添加不同强度的击退效果
                            knockback_force = 5.0
                            # 狙击枪击退效果最强
                            if hasattr(projectile, 'weapon_type') and projectile.weapon_type == "sniper":
                                knockback_force = 15.0
                            elif hasattr(projectile, 'weapon_type') and projectile.weapon_type == "rocket":
                                knockback_force = 12.0
                            elif hasattr(projectile, 'weapon_type') and projectile.weapon_type == "wand":
                                knockback_force = 3.0
                                # 法杖攻击命中时生成法阵
                                magic_zone = MagicZone(enemy.x, enemy.y, 30, max(1, projectile.damage // 4), 3)
                                self.magic_zones.append(magic_zone)
                                magic_zone.activate()
                            
                            enemy.vx += projectile.direction[0] * knockback_force
                            enemy.vy += projectile.direction[1] * knockback_force
                        break
                        
            # 更新魔法区域
            for magic_zone in self.magic_zones[:]:
                if not magic_zone.update(self.enemies):
                    # 法阵已失效，移除
                    if magic_zone in self.magic_zones:
                        self.magic_zones.remove(magic_zone)
            
            # 生成敌人（仅在PVE模式）
            if self.game_mode in [0, 1]:
                # 根据难度调整生成率
                spawn_chance = 1
                if self.pve_difficulty == 0:  # 简单
                    spawn_chance = 1
                elif self.pve_difficulty == 2:  # 困难
                    spawn_chance = 2
                    
                if random.randint(1, 100) <= spawn_chance:
                    self.spawn_enemy()
                
            # 更新敌人
            for i, enemy in enumerate(self.enemies[:]):
                # 简单的AI：朝玩家方向移动
                # 在网络模式下，只有主机生成和更新敌人
                if self.game_mode == 1 and not self.is_host:
                    continue
                    
                dx = self.player.x - enemy.x
                dy = self.player.y - enemy.y
                distance = max(math.sqrt(dx*dx + dy*dy), 0.1)
                dx, dy = dx/distance, dy/distance
                
                # 移动敌人（支持物理和碰撞检测）
                other_enemies = self.enemies[:i] + self.enemies[i+1:] if i < len(self.enemies) else self.enemies[:]
                enemy.move(dx, dy, self.player, other_enemies)
                
                # 检查敌人是否攻击玩家
                current_time = time.time()
                if current_time - enemy.last_attack_time >= enemy.attack_cooldown:
                    # 检查玩家是否在敌人攻击范围内
                    if self._is_player_in_enemy_attack_range(enemy):
                        # 对玩家造成伤害
                        self.player.health -= enemy.attack_damage
                        
                        # 添加击退效果
                        self._apply_knockback(self.player, enemy)
                        
                        # 重置攻击冷却时间
                        enemy.last_attack_time = current_time
                
                # 检查敌人是否死亡
                if enemy.health <= 0 and enemy in self.enemies:
                    self.player.gain_experience(10)
                    self.enemies.remove(enemy)
            
            # 检查玩家死亡
            if self.player.health <= 0 and not self.player_dead:
                self.player_dead = True
                self.player.health = 0
    
    def respawn_player(self):
        """玩家复活"""
        self.player_dead = False
        self.player.health = self.player.max_health
        self.player.x = self.spawn_x
        self.player.y = self.spawn_y
        self.player.rect.x = self.spawn_x
        self.player.rect.y = self.spawn_y
        
        # 如果是主机且开启了游戏共享，需要通知其他玩家自己已复活
        if self.is_host and self.game_shared:
            self.send_player_data()

class NetworkPlayer:
    """网络玩家类"""
    def __init__(self, x: int, y: int, player_id: str):
        self.x = x
        self.y = y
        self.player_id = player_id
        self.width = 40
        self.height = 40
        self.color = (0, 255, 128)  # 不同于本地玩家的颜色
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.weapon = "Pistol"
        self.dead = False  # 网络玩家死亡状态
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制网络玩家"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # 绘制玩家
        pygame.draw.rect(screen, self.color, (screen_x, screen_y, self.width, self.height))
        
        # 如果玩家死亡，绘制死亡标识
        if self.dead:
            font = pygame.font.Font(None, 20)
            dead_text = font.render("DEAD", True, (255, 0, 0))
            screen.blit(dead_text, (screen_x + self.width//2 - dead_text.get_width()//2, 
                                   screen_y - 30))
        
        # 绘制玩家ID
        font = pygame.font.Font(None, 24)
        id_text = font.render(self.player_id, True, (255, 255, 255))
        screen.blit(id_text, (screen_x, screen_y - 30))
        
        # 绘制当前武器标识
        weapon_text = font.render(self.weapon, True, (255, 255, 255))
        screen.blit(weapon_text, (screen_x, screen_y - 50))
        
        # 绘制血条
        bar_width = self.width
        bar_height = 5
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y - 10, bar_width, bar_height))
        if self.max_health > 0:
            health_width = bar_width * (self.health / self.max_health)
            pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 10, health_width, bar_height))
        
        # 绘制等级信息
        level_text = font.render(f"Lv.{self.level}", True, (255, 255, 0))
        screen.blit(level_text, (screen_x, screen_y - 70))

class Enemy:
    """简单敌人类"""
    def __init__(self, x: int, y: int, difficulty: int = 1):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.base_speed = 2
        self.color = (255, 0, 0)
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
        # 根据难度设置敌人属性
        if difficulty == 0:  # 简单
            self.health = 30
            self.max_health = 30
            self.base_speed = 1
        elif difficulty == 1:  # 均衡
            self.health = 50
            self.max_health = 50
            self.base_speed = 2
        else:  # 困难
            self.health = 100
            self.max_health = 100
            self.base_speed = 3
        
        # 物理属性
        self.vx = 0  # x方向速度
        self.vy = 0  # y方向速度
        self.ax = 0  # x方向加速度
        self.ay = 0  # y方向加速度
        self.mass = 30           # 质量
        self.max_speed = self.base_speed
        self.acceleration = 0.3  # 加速度
        self.friction = 0.1      # 摩擦力
        
        # 攻击属性
        self.attack_damage = 10
        self.attack_cooldown = 1.0  # 攻击冷却时间（秒）
        self.last_attack_time = 0
        
    def update_physics(self, dx: int, dy: int, player=None, other_enemies=None):
        """更新敌人物理状态，包括加速度、速度和摩擦力"""
        # 标准化移动向量
        if dx != 0 or dy != 0:
            magnitude = max(0.1, (dx**2 + dy**2)**0.5)
            dx_normalized = dx / magnitude
            dy_normalized = dy / magnitude
            
            # 应用加速度
            self.ax = dx_normalized * self.acceleration
            self.ay = dy_normalized * self.acceleration
        else:
            # 没有移动方向时应用摩擦力
            speed = max(0.001, (self.vx**2 + self.vy**2)**0.5)  # 防止除零
            self.ax = -self.vx / speed * self.friction
            self.ay = -self.vy / speed * self.friction
            
            # 如果速度很小，直接停止
            if speed < self.friction:
                self.vx = 0
                self.vy = 0
                self.ax = 0
                self.ay = 0
        
        # 更新速度
        self.vx += self.ax
        self.vy += self.ay
        
        # 限制最大速度
        speed = (self.vx**2 + self.vy**2)**0.5
        if speed > self.max_speed:
            self.vx = self.vx / speed * self.max_speed
            self.vy = self.vy / speed * self.max_speed
        
        # 计算新位置
        new_x = self.x + self.vx
        new_y = self.y + self.vy
        
        # 创建新的矩形用于碰撞检测
        new_rect_x = pygame.Rect(new_x, self.y, self.width, self.height)
        new_rect_y = pygame.Rect(self.x, new_y, self.width, self.height)
        
        # 检查X方向碰撞
        collision_x = self._check_collision(new_rect_x, player, other_enemies)
        
        # 检查Y方向碰撞
        collision_y = self._check_collision(new_rect_y, player, other_enemies)
        
        # 处理碰撞反应
        if collision_x:
            self.vx = -self.vx * 0.9  # 弹性碰撞反应
            # 确保实体不会卡在边界上
            if self.vx > 0 and self.vx < 0.5:
                self.vx = 0.5
            elif self.vx < 0 and self.vx > -0.5:
                self.vx = -0.5
        else:
            self.x = new_x
            self.rect.x = self.x
            
        if collision_y:
            self.vy = -self.vy * 0.9  # 弹性碰撞反应
            # 确保实体不会卡在边界上
            if self.vy > 0 and self.vy < 0.5:
                self.vy = 0.5
            elif self.vy < 0 and self.vy > -0.5:
                self.vy = -0.5
        else:
            self.y = new_y
            self.rect.y = self.y
            
    def move(self, dx: int, dy: int, player=None, other_enemies=None):
        """移动敌人，支持碰撞检测"""
        self.update_physics(dx, dy, player, other_enemies)
            
    def _check_collision(self, rect, player, other_enemies):
        """检查与玩家和其他敌人的碰撞"""
        # 检查与玩家的碰撞
        if player and rect.colliderect(player.rect):
            self._handle_collision_with_player(player)
            return True
            
        # 检查与其他敌人的碰撞
        if other_enemies:
            for enemy in other_enemies:
                if enemy != self and rect.colliderect(enemy.rect):
                    self._handle_collision_with_enemy(enemy)
                    return True
                    
        return False
    
    def _handle_collision_with_player(self, player):
        """处理与玩家的碰撞反应（动量守恒）"""
        # 使用动量守恒公式计算碰撞后的速度
        # 弹性碰撞，质量分别为m1和m2，初始速度为u1和u2，碰撞后速度为v1和v2
        # v1 = (m1-m2)/(m1+m2)*u1 + 2*m2/(m1+m2)*u2
        # v2 = 2*m1/(m1+m2)*u1 + (m2-m1)/(m1+m2)*u2
        
        m1 = self.mass
        m2 = player.mass
        u1x, u1y = self.vx, self.vy
        u2x, u2y = player.vx, player.vy
        
        # 计算碰撞后的速度
        v1x = (m1 - m2) / (m1 + m2) * u1x + 2 * m2 / (m1 + m2) * u2x
        v1y = (m1 - m2) / (m1 + m2) * u1y + 2 * m2 / (m1 + m2) * u2y
        v2x = 2 * m1 / (m1 + m2) * u1x + (m2 - m1) / (m1 + m2) * u2x
        v2y = 2 * m1 / (m1 + m2) * u1y + (m2 - m1) / (m1 + m2) * u2y
        
        # 应用新的速度（减少能量损失以增强弹性）
        self.vx = v1x * 0.95
        self.vy = v1y * 0.95
        player.vx = v2x * 0.95
        player.vy = v2y * 0.95
    
    def _handle_collision_with_enemy(self, enemy):
        """处理与其他敌人的碰撞反应（动量守恒）"""
        # 使用动量守恒公式计算碰撞后的速度
        # 弹性碰撞，质量分别为m1和m2，初始速度为u1和u2，碰撞后速度为v1和v2
        # v1 = (m1-m2)/(m1+m2)*u1 + 2*m2/(m1+m2)*u2
        # v2 = 2*m1/(m1+m2)*u1 + (m2-m1)/(m1+m2)*u2
        
        m1 = self.mass
        m2 = enemy.mass
        u1x, u1y = self.vx, self.vy
        u2x, u2y = enemy.vx, enemy.vy
        
        # 计算碰撞后的速度
        v1x = (m1 - m2) / (m1 + m2) * u1x + 2 * m2 / (m1 + m2) * u2x
        v1y = (m1 - m2) / (m1 + m2) * u1y + 2 * m2 / (m1 + m2) * u2y
        v2x = 2 * m1 / (m1 + m2) * u1x + (m2 - m1) / (m1 + m2) * u2x
        v2y = 2 * m1 / (m1 + m2) * u1y + (m2 - m1) / (m1 + m2) * u2y
        
        # 应用新的速度（减少能量损失以增强弹性）
        self.vx = v1x * 0.95
        self.vy = v1y * 0.95
        enemy.vx = v2x * 0.95
        enemy.vy = v2y * 0.95
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制敌人"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # 绘制敌人
        pygame.draw.rect(screen, self.color, (screen_x, screen_y, self.width, self.height))
        
        # 绘制血条
        bar_width = self.width
        bar_height = 5
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y - 10, bar_width, bar_height))
        health_width = bar_width * (self.health / self.max_health)
        pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 10, health_width, bar_height))

class ExplosionEffect:
    """爆炸效果可视化"""
    def __init__(self, x: int, y: int, radius: int, duration: float = 0.3):
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration  # 持续时间（秒）
        self.start_time = None
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        
    def activate(self):
        """激活爆炸效果"""
        import time
        self.start_time = time.time()
        
    def is_active(self):
        """检查爆炸效果是否仍然活跃"""
        import time
        if not self.start_time:
            return False
        return time.time() - self.start_time < self.duration
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制爆炸效果"""
        import time
        if not self.start_time:
            self.activate()
            
        # 计算透明度（随时间递减）
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            return
            
        alpha = max(0, 255 * (1 - elapsed / self.duration))
        
        # 绘制爆炸范围（带透明度的圆形）
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # 创建临时Surface来处理透明度
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 165, 0, int(alpha/2)), (self.radius, self.radius), self.radius, 3)
        # 绘制内部更亮的圆
        pygame.draw.circle(s, (255, 69, 0, int(alpha/4)), (self.radius, self.radius), self.radius * 0.7, 2)
        screen.blit(s, (screen_x - self.radius, screen_y - self.radius))

if __name__ == "__main__":
    game = Game()
    game.run()
