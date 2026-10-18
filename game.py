"""Game state and simulation for 仙途：秘境求生."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

WIDTH, HEIGHT = 480, 270
RUN_LENGTH = 8 * 60


@dataclass
class Player:
    x: float = WIDTH / 2
    y: float = HEIGHT / 2
    hp: float = 100
    max_hp: float = 100
    speed: float = 100
    damage: float = 12
    attack_delay: float = 0.85
    pickup_radius: float = 44
    invulnerable: float = 0
    level: int = 1
    xp: float = 0
    next_xp: float = 12
    sword_level: int = 1
    talisman_level: int = 0
    thunder_level: int = 0
    guard_level: int = 0
    cooldown: float = 0
    thunder_cooldown: float = 0
    facing: str = "down"
    moving: bool = False


@dataclass
class Enemy:
    x: float
    y: float
    kind: str
    hp: float
    speed: float
    damage: float
    radius: int
    color: tuple[int, int, int]
    elite: bool = False
    attack_flash: float = 0


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    life: float = 1.8


@dataclass
class Orb:
    x: float
    y: float
    value: float = 1


UPGRADES = {
    "sword": ("御剑术", "灵剑伤害提高", "sword_level"),
    "talisman": ("护身符箓", "增加一枚环绕符箓", "talisman_level"),
    "thunder": ("引雷真诀", "雷霆术威力提高", "thunder_level"),
    "guard": ("金光护体", "减伤并恢复少许气血", "guard_level"),
    "breath": ("周天吐纳", "气血上限提高并恢复", "breath"),
    "wind": ("御风而行", "移动速度提高", "wind"),
    "spirit": ("灵台清明", "灵气拾取范围扩大", "spirit"),
    "focus": ("剑心通明", "攻击间隔缩短", "focus"),
}


class Game:
    def __init__(self) -> None:
        self.selected_character = "male"
        self.state = "menu"
        self.reset()
        self.state = "menu"

    def reset(self) -> None:
        self.player = Player()
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.orbs: list[Orb] = []
        self.time = 0.0
        self.spawn_timer = 0.5
        self.kills = 0
        self.upgrades: list[str] = []
        self.elite_spawned = False
        self.elite_defeated = False
        self.shake = 0.0
        self.slashes: list[tuple[float, float, float, float]] = []

    def start(self) -> None:
        self.reset()
        self.state = "playing"

    def on_key(self, key: int) -> None:
        if self.state == "menu":
            if key in (pygame.K_LEFT, pygame.K_a):
                self.selected_character = "male"
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_character = "female"
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start()
            return
        if self.state in ("won", "lost"):
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start()
            return
        if self.state == "upgrade":
            if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.choose_upgrade(key - pygame.K_1)
            return
        if key in (pygame.K_p, pygame.K_ESCAPE):
            self.state = "paused" if self.state == "playing" else "playing" if self.state == "paused" else self.state

    def on_click(self, point: tuple[float, float]) -> None:
        x, y = point
        if self.state == "menu":
            if 94 <= y <= 182 and 65 <= x <= 227:
                self.selected_character = "male"
            elif 94 <= y <= 182 and 253 <= x <= 415:
                self.selected_character = "female"
            elif 160 <= x <= 320 and 190 <= y <= 225:
                self.start()
        elif self.state in ("won", "lost") and 150 <= x <= 330 and 143 <= y <= 190:
            self.start()
        elif self.state == "upgrade":
            for i in range(3):
                if 42 + i * 136 <= x <= 170 + i * 136 and 114 <= y <= 217:
                    self.choose_upgrade(i)
                    break
        elif self.state == "paused" and 155 <= x <= 325 and 155 <= y <= 192:
            self.state = "playing"

    def choose_upgrade(self, index: int) -> None:
        if self.state != "upgrade" or not 0 <= index < len(self.upgrades):
            return
        key = self.upgrades[index]
        p = self.player
        if key == "sword":
            p.sword_level += 1
            p.damage += 3.5
            p.attack_delay = max(0.30, p.attack_delay * 0.96)
        elif key == "talisman":
            p.talisman_level += 1
        elif key == "thunder":
            p.thunder_level += 1
        elif key == "guard":
            p.guard_level += 1
            p.max_hp += 12
            p.hp = min(p.max_hp, p.hp + 22)
        elif key == "breath":
            p.max_hp += 22
            p.hp = min(p.max_hp, p.hp + 35)
        elif key == "wind":
            p.speed += 8
        elif key == "spirit":
            p.pickup_radius += 18
        elif key == "focus":
            p.attack_delay = max(0.28, p.attack_delay * 0.88)
        self.state = "playing"

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper) -> None:
        if self.state != "playing":
            return
        self.time += dt
        p = self.player
        dx = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(keys[pygame.K_w] or keys[pygame.K_UP])
        length = math.hypot(dx, dy)
        p.moving = bool(length)
        if length:
            if abs(dx) > abs(dy):
                p.facing = "right" if dx > 0 else "left"
            else:
                p.facing = "down" if dy > 0 else "up"
            p.x += dx / length * p.speed * dt
            p.y += dy / length * p.speed * dt
        p.x = max(10, min(WIDTH - 10, p.x))
        p.y = max(18, min(HEIGHT - 10, p.y))
        p.invulnerable = max(0, p.invulnerable - dt)
        self.shake = max(0, self.shake - dt * 16)
        self.slashes = [(x, y, r, t - dt) for x, y, r, t in self.slashes if t > dt]

        self.spawn_timer -= dt
        interval = max(0.32, 1.05 - self.time / 720)
        while self.spawn_timer <= 0:
            if len(self.enemies) < 44:
                self.spawn_enemy()
            self.spawn_timer += interval
        if self.time >= RUN_LENGTH and not self.elite_spawned:
            self.spawn_enemy(elite=True)
            self.elite_spawned = True

        p.cooldown -= dt
        if p.cooldown <= 0:
            target = self.nearest_enemy()
            if target:
                vx, vy = target.x - p.x, target.y - p.y
                dist = max(1, math.hypot(vx, vy))
                self.projectiles.append(Projectile(p.x, p.y, vx / dist * 185, vy / dist * 185, p.damage))
                p.cooldown = p.attack_delay

        if p.thunder_level:
            p.thunder_cooldown -= dt
            if p.thunder_cooldown <= 0:
                target = self.nearest_enemy(155)
                if target:
                    self.damage_enemy(target, 13 + p.thunder_level * 9)
                    self.slashes.append((target.x, target.y, 80, 0.22))
                    self.slashes.append((target.x, target.y, 38, 0.18))
                    p.thunder_cooldown = max(0.55, 2.0 - p.thunder_level * 0.12)

        for shot in self.projectiles[:]:
            shot.x += shot.vx * dt
            shot.y += shot.vy * dt
            shot.life -= dt
            hit = next((e for e in self.enemies if math.hypot(e.x - shot.x, e.y - shot.y) < e.radius + 4), None)
            if hit:
                self.damage_enemy(hit, shot.damage)
                self.slashes.append((shot.x, shot.y, 17, 0.12))
                self.projectiles.remove(shot)
            elif shot.life <= 0 or not (-5 < shot.x < WIDTH + 5 and -5 < shot.y < HEIGHT + 5):
                self.projectiles.remove(shot)

        for enemy in self.enemies[:]:
            enemy.attack_flash = max(0, enemy.attack_flash - dt)
            vx, vy = p.x - enemy.x, p.y - enemy.y
            dist = max(1, math.hypot(vx, vy))
            if dist > 9:
                enemy.x += vx / dist * enemy.speed * dt
                enemy.y += vy / dist * enemy.speed * dt
            if dist < enemy.radius + 8 and p.invulnerable <= 0:
                reduction = min(0.65, p.guard_level * 0.1)
                p.hp -= enemy.damage * (1 - reduction)
                p.invulnerable = max(0.55, 0.85 - p.guard_level * 0.04)
                enemy.attack_flash = 0.2
                self.shake = 3
                if p.hp <= 0:
                    p.hp = 0
                    self.state = "lost"
                    return

        for orb in self.orbs[:]:
            vx, vy = p.x - orb.x, p.y - orb.y
            dist = max(1, math.hypot(vx, vy))
            if dist < p.pickup_radius:
                orb.x += vx / dist * (150 + (p.pickup_radius - dist) * 3) * dt
                orb.y += vy / dist * (150 + (p.pickup_radius - dist) * 3) * dt
            if dist < 9:
                p.xp += orb.value
                self.orbs.remove(orb)
                if p.xp >= p.next_xp:
                    p.xp -= p.next_xp
                    p.level += 1
                    p.next_xp = int(12 + p.level * 5.5)
                    self.upgrades = self.make_upgrade_choices()
                    self.state = "upgrade"
                    return

        if p.talisman_level:
            count = min(8, p.talisman_level)
            for enemy in self.enemies[:]:
                for i in range(count):
                    angle = self.time * 2.3 + math.tau * i / count
                    tx = p.x + math.cos(angle) * 21
                    ty = p.y + math.sin(angle) * 14
                    if math.hypot(enemy.x - tx, enemy.y - ty) < enemy.radius + 4:
                        self.damage_enemy(enemy, (6 + p.talisman_level * 2) * dt * 4)
                        break

    def spawn_enemy(self, elite: bool = False) -> None:
        side = random.randrange(4)
        x = random.randrange(WIDTH) if side in (0, 2) else (-8 if side == 3 else WIDTH + 8)
        y = (-8 if side == 0 else HEIGHT + 8) if side in (0, 2) else random.randrange(HEIGHT)
        if elite:
            self.enemies.append(Enemy(x, y, "elite", 520, 27, 22, 14, (203, 80, 117), True))
            return
        roll = random.random()
        if roll < 0.68:
            self.enemies.append(Enemy(x, y, "wisp", 16 + self.time * 0.02, 34 + min(18, self.time / 25), 8, 6, (104, 204, 153)))
        elif roll < 0.91:
            self.enemies.append(Enemy(x, y, "wolf", 28 + self.time * 0.025, 24 + min(12, self.time / 32), 12, 8, (196, 123, 91)))
        else:
            self.enemies.append(Enemy(x, y, "brute", 66 + self.time * 0.04, 15, 18, 11, (167, 120, 196)))

    def nearest_enemy(self, max_dist: float = 9999) -> Enemy | None:
        p = self.player
        candidates = [(math.hypot(e.x - p.x, e.y - p.y), e) for e in self.enemies]
        if not candidates:
            return None
        distance, enemy = min(candidates, key=lambda pair: pair[0])
        return enemy if distance <= max_dist else None

    def damage_enemy(self, enemy: Enemy, amount: float) -> None:
        if enemy not in self.enemies:
            return
        enemy.hp -= amount
        if enemy.hp <= 0:
            self.enemies.remove(enemy)
            self.kills += 1
            if enemy.elite:
                self.elite_defeated = True
                self.state = "won"
            else:
                value = 5 if enemy.kind == "brute" else 2 if enemy.kind == "wolf" else 1
                self.orbs.append(Orb(enemy.x, enemy.y, value))

    def make_upgrade_choices(self) -> list[str]:
        keys = list(UPGRADES)
        random.shuffle(keys)
        return keys[:3]
