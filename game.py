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
    sword_evolution: bool = False
    fire_evolution: bool = False
    thunder_evolution: bool = False
    guard_evolution: bool = False
    wind_evolution: bool = False
    dash_cooldown: float = 0


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
    attack_cooldown: float = 0


@dataclass
class Hazard:
    x: float
    y: float
    radius: int
    life: float
    tick: float = 0


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    life: float = 1.8
    kind: str = "sword"
    hostile: bool = False


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

EVOLUTIONS = {
    "sword_evo": ("万剑归宗", "灵剑贯穿敌群，伤害提高"),
    "fire_evo": ("焚天业火", "爆炸范围扩大并留下灼烧地带"),
    "thunder_evo": ("九霄天劫", "雷击额外连锁附近妖兽"),
    "guard_evo": ("不动明王", "受击时震击周围妖兽"),
    "wind_evo": ("踏风无痕", "疾行时剑风斩击路径上的妖兽"),
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
        self.hazards: list[Hazard] = []
        self.orbs: list[Orb] = []
        self.time = 0.0
        self.spawn_timer = 0.5
        self.kills = 0
        self.upgrades: list[str] = []
        self.elite_spawned = False
        self.elite_defeated = False
        self.shake = 0.0
        self.slashes: list[tuple[float, float, float, float]] = []
        self.boss_burst_timer = 0

    def start(self) -> None:
        self.reset()
        if self.selected_character == "female":
            self.player.damage = 10
            self.player.attack_delay = 1.0
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
            if 73 <= y <= 181 and 92 <= x <= 228:
                self.selected_character = "male"
            elif 73 <= y <= 181 and 252 <= x <= 388:
                self.selected_character = "female"
            elif 160 <= x <= 320 and 190 <= y <= 225:
                self.start()
        elif self.state in ("won", "lost") and 164 <= x <= 316 and 165 <= y <= 195:
            self.start()
        elif self.state == "upgrade":
            for i in range(3):
                if 42 + i * 136 <= x <= 170 + i * 136 and 88 <= y <= 220:
                    self.choose_upgrade(i)
                    break
        elif self.state == "paused" and 164 <= x <= 316 and 165 <= y <= 195:
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
        elif key == "sword_evo":
            p.sword_evolution = True
        elif key == "fire_evo":
            p.fire_evolution = True
        elif key == "thunder_evo":
            p.thunder_evolution = True
        elif key == "guard_evo":
            p.guard_evolution = True
        elif key == "wind_evo":
            p.wind_evolution = True
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
            if p.wind_evolution and p.dash_cooldown <= 0:
                for enemy in self.enemies[:]:
                    if self._point_segment_distance(enemy.x, enemy.y, p.x-dx/length*24, p.y-dy/length*24, p.x, p.y) < enemy.radius+7:
                        self.damage_enemy(enemy, 20)
                p.dash_cooldown = 0.32
        p.x = max(10, min(WIDTH - 10, p.x))
        p.y = max(18, min(HEIGHT - 10, p.y))
        p.invulnerable = max(0, p.invulnerable - dt)
        p.dash_cooldown = max(0, p.dash_cooldown - dt)
        self.shake = max(0, self.shake - dt * 16)
        self.slashes = [(x, y, r, t - dt) for x, y, r, t in self.slashes if t > dt]

        self.spawn_timer -= dt
        interval = max(0.32, 1.05 - self.time / 720)
        while self.spawn_timer <= 0:
            if self.time < RUN_LENGTH and len(self.enemies) < 44:
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
                if self.selected_character == "female":
                    # Luoli casts a slower fire orb that bursts around its first target.
                    self.projectiles.append(Projectile(p.x, p.y, vx / dist * (165 if p.fire_evolution else 135),
                                                       vy / dist * (165 if p.fire_evolution else 135), p.damage * (1.2 if p.fire_evolution else 1), 2.2, "fire"))
                else:
                    # Yungui's spirit sword is a faster, precise single-target bolt.
                    self.projectiles.append(Projectile(p.x, p.y, vx / dist * (250 if p.sword_evolution else 205),
                                                       vy / dist * (250 if p.sword_evolution else 205), p.damage * (1.15 if p.sword_evolution else 1), 1.8, "sword"))
                p.cooldown = p.attack_delay

        if p.thunder_level:
            p.thunder_cooldown -= dt
            if p.thunder_cooldown <= 0:
                target = self.nearest_enemy(155)
                if target:
                    self.damage_enemy(target, 13 + p.thunder_level * 9 + (18 if p.thunder_evolution else 0))
                    if p.thunder_evolution and target in self.enemies:
                        nearby = sorted((e for e in self.enemies if e is not target), key=lambda e: math.hypot(e.x-target.x, e.y-target.y))
                        for chained in nearby[:3]:
                            if math.hypot(chained.x-target.x, chained.y-target.y) < 105:
                                self.damage_enemy(chained, 20 + p.thunder_level * 4)
                                self.slashes.append((chained.x, chained.y, 22, 0.14))
                    self.slashes.append((target.x, target.y, 80, 0.22))
                    self.slashes.append((target.x, target.y, 38, 0.18))
                    p.thunder_cooldown = max(0.55, 2.0 - p.thunder_level * 0.12)

        for shot in self.projectiles[:]:
            shot.x += shot.vx * dt
            shot.y += shot.vy * dt
            shot.life -= dt
            if shot.hostile:
                if math.hypot(p.x - shot.x, p.y - shot.y) < 9 and p.invulnerable <= 0:
                    self.hit_player(shot.damage)
                    self.projectiles.remove(shot)
                    if self.state == "lost":
                        return
                elif shot.life <= 0 or not (-8 < shot.x < WIDTH + 8 and -8 < shot.y < HEIGHT + 8):
                    self.projectiles.remove(shot)
                continue
            hit = next((e for e in self.enemies if math.hypot(e.x - shot.x, e.y - shot.y) < e.radius + 4), None)
            if hit:
                if shot.kind == "fire":
                    blast_radius = 43 if p.fire_evolution else 26
                    for enemy in self.enemies[:]:
                        if math.hypot(enemy.x - hit.x, enemy.y - hit.y) <= blast_radius + enemy.radius:
                            self.damage_enemy(enemy, shot.damage * (1.3 if p.fire_evolution else 1))
                    if p.fire_evolution:
                        self.hazards.append(Hazard(hit.x, hit.y, 25, 2.8))
                    self.slashes.append((hit.x, hit.y, blast_radius, 0.2))
                else:
                    if p.sword_evolution:
                        for enemy in self.enemies[:]:
                            if self._point_segment_distance(enemy.x, enemy.y, shot.x, shot.y,
                                    shot.x + shot.vx / max(1, math.hypot(shot.vx, shot.vy))*115,
                                    shot.y + shot.vy / max(1, math.hypot(shot.vx, shot.vy))*115) < enemy.radius + 7:
                                self.damage_enemy(enemy, shot.damage)
                    else:
                        self.damage_enemy(hit, shot.damage)
                    self.slashes.append((shot.x, shot.y, 17, 0.12))
                self.projectiles.remove(shot)
            elif shot.life <= 0 or not (-5 < shot.x < WIDTH + 5 and -5 < shot.y < HEIGHT + 5):
                self.projectiles.remove(shot)

        for enemy in self.enemies[:]:
            enemy.attack_flash = max(0, enemy.attack_flash - dt)
            enemy.attack_cooldown -= dt
            vx, vy = p.x - enemy.x, p.y - enemy.y
            dist = max(1, math.hypot(vx, vy))
            if enemy.kind == "raven":
                # 乌鸦盘旋在中距离，以羽刃远程骚扰，不会冲向玩家。
                if dist > 145:
                    enemy.x += vx / dist * enemy.speed * dt
                    enemy.y += vy / dist * enemy.speed * dt
                elif dist < 95:
                    enemy.x -= vx / dist * enemy.speed * 0.8 * dt
                    enemy.y -= vy / dist * enemy.speed * 0.8 * dt
                if enemy.attack_cooldown <= 0 and dist < 200:
                    self.projectiles.append(Projectile(enemy.x, enemy.y, vx / dist * 112, vy / dist * 112,
                                                       7, 2.2, "feather", True))
                    enemy.attack_cooldown = 2.6
            elif enemy.kind == "wolf":
                # 妖狼只会持续追猎，贴近后以普通撕咬造成接触伤害。
                if dist > 9:
                    enemy.x += vx / dist * enemy.speed * dt
                    enemy.y += vy / dist * enemy.speed * dt
            else:
                # 蛙妖首领保持距离，用毒泡封锁地面。
                desired = 118
                if dist > desired + 8:
                    enemy.x += vx / dist * enemy.speed * dt
                    enemy.y += vy / dist * enemy.speed * dt
                elif dist < desired - 25:
                    enemy.x -= vx / dist * enemy.speed * 0.75 * dt
                    enemy.y -= vy / dist * enemy.speed * 0.75 * dt
                if enemy.attack_cooldown <= 0:
                    move_x = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT])
                    move_y = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(keys[pygame.K_w] or keys[pygame.K_UP])
                    ax, ay = p.x + move_x * 18 - enemy.x, p.y + move_y * 18 - enemy.y
                    ad = max(1, math.hypot(ax, ay))
                    self.projectiles.append(Projectile(enemy.x, enemy.y, ax / ad * 76, ay / ad * 76,
                                                       13, 2.6, "poison", True))
                    self.boss_burst_timer += 1
                    if self.boss_burst_timer % 3 == 0:
                        self.hazards.append(Hazard(p.x + move_x * 18, p.y + move_y * 18, 19, 4.5))
                    enemy.attack_cooldown = 1.25
            if dist < enemy.radius + 8 and p.invulnerable <= 0:
                self.hit_player(enemy.damage)
                enemy.attack_flash = 0.2
                if self.state == "lost":
                    return

        for hazard in self.hazards[:]:
            hazard.life -= dt
            hazard.tick -= dt
            if hazard.life <= 0:
                self.hazards.remove(hazard)
            elif math.hypot(p.x - hazard.x, p.y - hazard.y) < hazard.radius - 2 and hazard.tick <= 0 and p.invulnerable <= 0:
                self.hit_player(7)
                hazard.tick = 0.65
                if self.state == "lost":
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
            self.enemies.append(Enemy(x, y, "toad_boss", 760, 13, 18, 19, (119, 152, 112), True,
                                      attack_cooldown=1.4))
            return
        roll = random.random()
        raven_chance = 0.78 if self.time < RUN_LENGTH / 3 else 0.22 if self.time < RUN_LENGTH * 2 / 3 else 0.5
        if roll < raven_chance:
            self.enemies.append(Enemy(x, y, "raven", 22 + self.time * 0.022, 37 + min(20, self.time / 23), 10, 8,
                                      (102, 116, 141), attack_cooldown=random.uniform(0.6, 2.0)))
        else:
            self.enemies.append(Enemy(x, y, "wolf", 39 + self.time * 0.032, 23 + min(10, self.time / 35), 14, 10,
                                      (154, 112, 86), attack_cooldown=random.uniform(0.8, 2.2)))

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
                value = 5 if enemy.elite else 2 if enemy.kind == "wolf" else 1
                self.orbs.append(Orb(enemy.x, enemy.y, value))

    def hit_player(self, damage: float) -> None:
        p = self.player
        reduction = min(0.72 if p.guard_evolution else 0.65, p.guard_level * (0.14 if p.guard_evolution else 0.1))
        p.hp -= damage * (1 - reduction)
        p.invulnerable = max(0.55, 0.85 - p.guard_level * 0.04)
        self.shake = 3
        if p.guard_evolution:
            for enemy in self.enemies[:]:
                if math.hypot(enemy.x-p.x, enemy.y-p.y) < 52:
                    self.damage_enemy(enemy, 28 + p.guard_level * 6)
        if p.hp <= 0:
            p.hp = 0
            self.state = "lost"

    def make_upgrade_choices(self) -> list[str]:
        keys = list(UPGRADES)
        p = self.player
        if p.sword_level >= 5 and not p.sword_evolution:
            keys.append("sword_evo" if self.selected_character == "male" else "fire_evo")
        if p.thunder_level >= 4 and not p.thunder_evolution:
            keys.append("thunder_evo")
        if p.guard_level >= 4 and not p.guard_evolution:
            keys.append("guard_evo")
        if p.speed >= 132 and not p.wind_evolution:
            keys.append("wind_evo")
        random.shuffle(keys)
        return keys[:3]

    @staticmethod
    def _point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
        dx, dy = bx-ax, by-ay
        length2 = dx*dx + dy*dy
        t = 0 if length2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/length2))
        return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
