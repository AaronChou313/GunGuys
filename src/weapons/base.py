class Weapon:
    def __init__(self, name, damage, attack_speed):
        self.name = name
        self.damage = damage
        self.attack_speed = attack_speed

class RangedWeapon(Weapon):
    def __init__(self, name, damage, attack_speed, projectile_type, range):
        super().__init__(name, damage, attack_speed)
        self.projectile_type = projectile_type
        self.range = range

class MeleeWeapon(Weapon):
    def __init__(self, name, damage, attack_speed, attack_range):
        super().__init__(name, damage, attack_speed)
        self.attack_range = attack_range

class DefensiveWeapon(Weapon):
    def __init__(self, name, damage, attack_speed, defense_type):
        super().__init__(name, damage, attack_speed)
        self.defense_type = defense_type