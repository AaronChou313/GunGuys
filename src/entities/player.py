import pygame
import time
from typing import Tuple
from entities.weapon import Weapon, Pistol, Rifle, Sniper, RocketLauncher, Bow, Wand, Sword, Dagger

class Player:
    def __init__(self, x: int, y: int, player_id: str = "player"):
        self.x = x
        self.y = y
        self.player_id = player_id
        self.width = 40
        self.height = 40
        self.base_speed = 5  # 基础速度
        self.color = (0, 128, 255)
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
        # 玩家属性
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        
        # 物理属性
        self.vx = 0  # x方向速度
        self.vy = 0  # y方向速度
        self.ax = 0  # x方向加速度
        self.ay = 0  # y方向加速度
        self.mass = 100          # 质量
        self.max_speed = self.base_speed + (self.level - 1) * 0.5  # 基于等级的最大速度
        self.acceleration = 1  # 加速度
        self.friction = 0.2      # 摩擦力
        
        # 武器系统
        self.weapons = [
            Pistol(),    # 0
            Rifle(),     # 1
            Sniper(),    # 2
            RocketLauncher(), # 3
            Bow(),       # 4
            Wand(),      # 5
            Sword(),     # 6
            Dagger()     # 7
        ]
        self.current_weapon_index = 0
        self.current_weapon: Weapon = self.weapons[0]
        
    def update_physics(self, dx: int, dy: int, enemies=None):
        """更新玩家物理状态，包括加速度、速度和摩擦力"""
        # 根据按键设置加速度
        if dx != 0 or dy != 0:
            # 标准化移动向量
            magnitude = max(0.1, (dx**2 + dy**2)**0.5)
            dx_normalized = dx / magnitude
            dy_normalized = dy / magnitude
            
            # 应用加速度
            self.ax = dx_normalized * self.acceleration
            self.ay = dy_normalized * self.acceleration
        else:
            # 没有按键时应用摩擦力
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
        collision_x = False
        if enemies:
            collision_x = self._check_enemy_collision(new_rect_x, enemies)
        
        # 检查Y方向碰撞
        collision_y = False
        if enemies:
            collision_y = self._check_enemy_collision(new_rect_y, enemies)
        
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
            
    def move(self, dx: int, dy: int, enemies=None):
        """移动玩家，支持碰撞检测"""
        self.update_physics(dx, dy, enemies)
            
    def _check_enemy_collision(self, rect, enemies):
        """检查与敌人的碰撞"""
        if enemies:
            for enemy in enemies:
                if rect.colliderect(enemy.rect):
                    # 处理碰撞反应
                    self._handle_collision_with_enemy(enemy)
                    return True
        return False
    
    def _handle_collision_with_enemy(self, enemy):
        """处理与敌人的碰撞反应（动量守恒）"""
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
        
    def gain_experience(self, amount: int):
        """获得经验值"""
        self.experience += amount
        # 检查是否升级
        while self.experience >= self.experience_to_next_level:
            self.level_up()
        
    def level_up(self):
        """升级"""
        self.experience -= self.experience_to_next_level
        self.level += 1
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)  # 每级所需经验增加50%
        
        # 提升属性
        self.max_health += 20
        self.health = self.max_health  # 回满血
        
        # 提升近战武器攻击范围
        for weapon in self.weapons:
            if isinstance(weapon, Sword):
                weapon.range += 5  # 每级增加5攻击范围
            elif isinstance(weapon, Dagger):
                weapon.range += 3  # 每级增加3攻击范围
        
    def switch_weapon(self, index: int):
        """切换武器"""
        if 0 <= index < len(self.weapons):
            self.current_weapon_index = index
            self.current_weapon = self.weapons[index]
            
    def switch_to_next_weapon(self):
        """切换到下一个武器"""
        self.current_weapon_index = (self.current_weapon_index + 1) % len(self.weapons)
        self.current_weapon = self.weapons[self.current_weapon_index]
        
    def switch_to_previous_weapon(self):
        """切换到上一个武器"""
        self.current_weapon_index = (self.current_weapon_index - 1) % len(self.weapons)
        self.current_weapon = self.weapons[self.current_weapon_index]
        
    def can_shoot(self):
        """检查是否可以射击（基于攻击速度）"""
        current_time = time.time()
        # 基础攻击间隔（秒）
        base_interval = 1.0 / self.current_weapon.fire_rate
        # 每升一级减少5%的攻击间隔
        level_modifier = 0.05 * (self.level - 1)
        actual_interval = max(0.1, base_interval * (1 - level_modifier))  # 最小间隔0.1秒
        
        return (current_time - self.current_weapon.last_shot_time) >= actual_interval
        
    def shoot(self, direction: Tuple[int, int]):
        """射击"""
        if not self.can_shoot():
            return None
            
        self.current_weapon.last_shot_time = time.time()
        
        # 简化实现：实际游戏中可能需要更复杂的逻辑
        return self.current_weapon.shoot(
            self.x + self.width // 2, 
            self.y + self.height // 2, 
            direction
        )
    
    def apply_knockback(self, source, force=10.0):
        """应用击退效果"""
        # 计算从源到玩家的方向
        dx = self.x - source.x
        dy = self.y - source.y
        distance = max(0.1, math.sqrt(dx*dx + dy*dy))
        
        # 标准化方向向量
        dx_normalized = dx / distance
        dy_normalized = dy / distance
        
        # 应击退力（根据质量调整）
        self.vx += dx_normalized * force * (source.mass / self.mass)
        self.vy += dy_normalized * force * (source.mass / self.mass)
        
    def get_melee_targets(self, direction: Tuple[int, int], enemies):
        """获取近战攻击目标"""
        if hasattr(self.current_weapon, 'get_melee_targets'):
            return self.current_weapon.get_melee_targets(
                self.x + self.width // 2,
                self.y + self.height // 2,
                direction,
                enemies
            )
        return []
        
    def update(self):
        """更新玩家状态"""
        pass
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制玩家（考虑摄像机偏移）"""
        # 计算屏幕位置
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # 绘制玩家
        pygame.draw.rect(screen, self.color, (screen_x, screen_y, self.width, self.height))
        
        # 绘制当前武器标识
        font = pygame.font.Font(None, 24)
        weapon_text = font.render(self.current_weapon.name, True, (255, 255, 255))
        screen.blit(weapon_text, (screen_x, screen_y - 30))
        
        # 绘制血条
        bar_width = self.width
        bar_height = 5
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y - 10, bar_width, bar_height))
        health_width = bar_width * (self.health / self.max_health)
        pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 10, health_width, bar_height))
        
        # 绘制等级信息
        level_text = font.render(f"Lv.{self.level}", True, (255, 255, 0))
        screen.blit(level_text, (screen_x, screen_y - 50))