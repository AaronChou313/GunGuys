from weapons.base import RangedWeapon, MeleeWeapon, DefensiveWeapon

# Ranged weapons
class Rifle(RangedWeapon):
    def __init__(self):
        super().__init__("Rifle", damage=20, attack_speed=5, projectile_type="bullet", range=500)

class Sniper(RangedWeapon):
    def __init__(self):
        super().__init__("Sniper", damage=50, attack_speed=2, projectile_type="piercing_bullet", range=800)

class GrenadeLauncher(RangedWeapon):
    def __init__(self):
        super().__init__("Grenade Launcher", damage=40, attack_speed=3, projectile_type="bomb", range=300)

class Staff(RangedWeapon):
    def __init__(self):
        super().__init__("Staff", damage=25, attack_speed=4, projectile_type="magic_orb", range=400)

# Melee weapons
class Sword(MeleeWeapon):
    def __init__(self):
        super().__init__("Sword", damage=15, attack_speed=6, attack_range=60)

class Axe(MeleeWeapon):
    def __init__(self):
        super().__init__("Axe", damage=30, attack_speed=3, attack_range=40)

class Dagger(MeleeWeapon):
    def __init__(self):
        super().__init__("Dagger", damage=10, attack_speed=10, attack_range=30)

# Defensive weapons
class Shield(DefensiveWeapon):
    def __init__(self):
        super().__init__("Shield", damage=5, attack_speed=2, defense_type="physical")

class SpellBarrier(DefensiveWeapon):
    def __init__(self):
        super().__init__("Spell Barrier", damage=5, attack_speed=2, defense_type="magical")