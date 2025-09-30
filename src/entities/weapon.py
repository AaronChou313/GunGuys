import pygame
from typing import Tuple
from abc import ABC, abstractmethod
import math

class Weapon(ABC):
    """武器基类"""
    def __init__(self, name: str, damage: int, fire_rate: float):
        self.name = name
        self.damage = damage  # 单次攻击伤害
        self.fire_rate = fire_rate  # 每秒攻击次数
        self.last_shot_time = 0
        
    @abstractmethod
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> 'Projectile':
        """射击方法，返回子弹对象"""
        pass

class MeleeWeapon(Weapon):
    """近战武器基类"""
    def __init__(self, name: str, damage: int, fire_rate: float, range: float):
        super().__init__(name, damage, fire_rate)
        self.range = range  # 攻击范围
        
    def get_melee_targets(self, player_x: int, player_y: int, direction: Tuple[int, int], enemies):
        """获取近战攻击的目标"""
        targets = []
        # 计算方向角度
        angle = math.atan2(direction[1], direction[0])
        
        for enemy in enemies:
            # 计算敌人与玩家的距离
            dx = enemy.x - player_x
            dy = enemy.y - player_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 检查距离是否在攻击范围内
            if distance <= self.range:
                # 计算敌人相对于玩家的角度
                enemy_angle = math.atan2(dy, dx)
                
                # 计算角度差（弧度）
                angle_diff = abs(enemy_angle - angle)
                # 处理角度跨越π的情况
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                    
                # 扇形角度为π/3（60度）
                if angle_diff <= math.pi / 3:
                    targets.append(enemy)
                    
        return targets

class Projectile:
    """子弹/抛射物类"""
    def __init__(self, x: int, y: int, direction: Tuple[int, int], speed: int, damage: int, weapon_type: str):
        self.x = x
        self.y = y
        self.direction = direction  # (dx, dy) 方向向量
        self.speed = speed
        self.damage = damage
        self.weapon_type = weapon_type
        self.radius = 5
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius * 2, self.radius * 2)
        
    def update(self):
        """更新子弹位置"""
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed
        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制子弹"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        pygame.draw.circle(screen, (255, 255, 0), (screen_x, screen_y), self.radius)

class ExplosiveProjectile(Projectile):
    """爆炸子弹"""
    def __init__(self, x: int, y: int, direction: Tuple[int, int], speed: int, damage: int, weapon_type: str, explosion_radius: int = 200):
        super().__init__(x, y, direction, speed, damage, weapon_type)
        self.explosion_radius = explosion_radius
        self.exploded = False
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制爆炸子弹"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        # 火箭弹用红色表示
        pygame.draw.circle(screen, (255, 0, 0), (screen_x, screen_y), self.radius)

class PiercingProjectile(Projectile):
    """穿透子弹"""
    def __init__(self, x: int, y: int, direction: Tuple[int, int], speed: int, damage: int, weapon_type: str, max_pierce: int = 1):
        super().__init__(x, y, direction, speed, damage, weapon_type)
        self.max_pierce = max_pierce  # 最大穿透敌人数量
        self.pierced_count = 0  # 已穿透的敌人数量
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制穿透子弹"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        # 穿透子弹用蓝色表示
        pygame.draw.circle(screen, (0, 0, 255), (screen_x, screen_y), self.radius)

class MagicProjectile(Projectile):
    """魔法子弹"""
    def __init__(self, x: int, y: int, direction: Tuple[int, int], speed: int, damage: int, weapon_type: str, max_distance: int = 300):
        super().__init__(x, y, direction, speed, damage, weapon_type)
        self.start_x = x
        self.start_y = y
        self.max_distance = max_distance
        self.distance_traveled = 0
        
    def update(self):
        """更新魔法子弹位置"""
        old_x, old_y = self.x, self.y
        super().update()
        # 计算已移动距离
        self.distance_traveled += math.sqrt((self.x - old_x)**2 + (self.y - old_y)**2)
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制魔法子弹"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        # 魔法子弹用紫色表示
        pygame.draw.circle(screen, (255, 0, 255), (screen_x, screen_y), self.radius)

class MagicZone:
    """魔法区域（法阵）"""
    def __init__(self, x: int, y: int, radius: int, damage: int, duration: float):
        self.x = x
        self.y = y
        self.radius = radius
        self.damage = damage
        self.duration = duration  # 持续时间（秒）
        self.start_time = None  # 开始时间
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        
    def activate(self):
        """激活法阵"""
        import time
        self.start_time = time.time()
        
    def update(self, enemies):
        """更新法阵，对敌人造成伤害"""
        import time
        if not self.start_time:
            self.activate()
            
        # 检查是否超过持续时间
        if time.time() - self.start_time > self.duration:
            return False  # 法阵已失效
            
        # 对范围内的敌人造成伤害
        for enemy in enemies:
            distance = math.sqrt((enemy.x - self.x)**2 + (enemy.y - self.y)**2)
            if distance <= self.radius:
                # 每秒造成伤害，这里简化为每帧造成部分伤害
                enemy.health -= self.damage / 60  # 假设60FPS
                
        return True  # 法阵仍然有效
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制法阵"""
        import time
        if not self.start_time:
            return
            
        # 计算透明度（随时间递减）
        elapsed = time.time() - self.start_time
        alpha = max(0, 255 * (1 - elapsed / self.duration))
        
        # 绘制法阵（带透明度的圆形）
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # 创建临时Surface来处理透明度
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (128, 0, 128, int(alpha/2)), (self.radius, self.radius), self.radius)
        screen.blit(s, (screen_x - self.radius, screen_y - self.radius))

class Pistol(Weapon):
    """手枪"""
    def __init__(self):
        super().__init__("Pistol", 25, 2.0)  # 伤害25，每秒2发
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        return Projectile(player_x, player_y, direction, 10, self.damage, "pistol")

class Rifle(Weapon):
    """步枪"""
    def __init__(self):
        super().__init__("Rifle", 15, 5.0)  # 伤害15，每秒5发
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        return Projectile(player_x, player_y, direction, 12, self.damage, "rifle")

class Sniper(Weapon):
    """狙击枪"""
    def __init__(self):
        super().__init__("Sniper", 100, 0.5)  # 伤害100，每秒0.5发
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        # 狙击枪子弹具有穿透能力，默认穿透1个敌人，每升5级增加1个穿透
        return PiercingProjectile(player_x, player_y, direction, 20, self.damage, "sniper", 1)

class Shotgun(Weapon):
    """霰弹枪"""
    def __init__(self):
        super().__init__("Shotgun", 30, 1.0)  # 伤害30，每秒1发
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        return Projectile(player_x, player_y, direction, 8, self.damage, "shotgun")

class RocketLauncher(Weapon):
    """火箭炮"""
    def __init__(self):
        super().__init__("Rocket Launcher", 80, 0.3)  # 伤害80，每秒0.3发
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        # 火箭弹具有爆炸效果
        return ExplosiveProjectile(player_x, player_y, direction, 6, self.damage, "rocket", 200)

class Bow(Weapon):
    """弓箭"""
    def __init__(self):
        super().__init__("Bow", 35, 1.5)  # 伤害35，每秒1.5发
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        return Projectile(player_x, player_y, direction, 15, self.damage, "bow")

class Wand(Weapon):
    """法杖"""
    def __init__(self):
        super().__init__("Wand", 20, 3.0)  # 伤害20，每秒3发
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        # 法杖发射魔法弹，最大距离固定为300
        return MagicProjectile(player_x, player_y, direction, 9, self.damage, "wand", 300)

class Sword(MeleeWeapon):
    """剑"""
    def __init__(self):
        super().__init__("Sword", 40, 2.5, 120)  # 伤害40，每秒2.5发，范围120
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        # 剑是近战武器，不产生远程子弹
        return None

class Dagger(MeleeWeapon):
    """短刀"""
    def __init__(self):
        super().__init__("Dagger", 15, 6.0, 100)  # 伤害15，每秒6发，范围100
        
    def shoot(self, player_x: int, player_y: int, direction: Tuple[int, int]) -> Projectile:
        # 短刀是近战武器，不产生远程子弹
        return None