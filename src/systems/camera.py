import pygame

class Camera:
    def __init__(self, width: int, height: int):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        
    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """应用摄像机偏移到给定矩形"""
        return pygame.Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)
        
    def update(self, target):
        """更新摄像机位置以跟随目标"""
        self.x = target.x - self.width // 2
        self.y = target.y - self.height // 2
        
        # 边界检查可以根据地图大小进行调整
        # 这里暂时不做边界限制