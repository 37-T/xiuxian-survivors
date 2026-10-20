"""Pixel-art presentation and Chinese UI."""

from __future__ import annotations

import math
from pathlib import Path
import pygame

from game import EVOLUTIONS, Game, HEIGHT, RUN_LENGTH, UPGRADES, WIDTH


class Renderer:
    def __init__(self) -> None:
        self.fonts: dict[int, pygame.font.Font] = {}
        self.player_art: dict[str, dict[str, list[pygame.Surface]]] = {}
        self.enemy_art: dict[str, pygame.Surface] = {}
        self.enemy_rims: dict[str, pygame.Surface] = {}
        self.background_art: dict[str, pygame.Surface] = {}
        self.hit_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.load_art()

    def load_art(self) -> None:
        root = Path(__file__).resolve().parent / "assets" / "characters"
        for key, filename in (("male", "yungui.png"), ("female", "luoli.png")):
            sprite = pygame.image.load(str(root / filename)).convert_alpha()
            sprite = pygame.transform.scale(sprite, (48, 56))
            mirrored = pygame.transform.flip(sprite, True, False)
            self.player_art[key] = {
                "down": [sprite],
                "up": [sprite],
                "left": [mirrored],
                "right": [sprite],
            }

        creature_dir = Path(__file__).resolve().parent / "assets" / "enemies"
        creature_files = {
            "raven": ("raven.png", (28, 32)),
            "wolf": ("wolf.png", (30, 30)),
            "toad_boss": ("toad_boss.png", (48, 44)),
        }
        for kind, (filename, size) in creature_files.items():
            image = pygame.image.load(str(creature_dir / filename)).convert_alpha()
            image = pygame.transform.scale(image, size)
            self.enemy_art[kind] = image
            rim_color = {
                "raven": (255, 50, 72, 235),
                "wolf": (255, 82, 45, 235),
                "toad_boss": (255, 28, 82, 245),
            }[kind]
            self.enemy_rims[kind] = pygame.mask.from_surface(image).to_surface(
                setcolor=rim_color, unsetcolor=(0, 0, 0, 0))

        background_dir = Path(__file__).resolve().parent / "assets" / "backgrounds"
        for key in ("raven_realm", "wolf_realm", "toad_realm"):
            image = pygame.image.load(str(background_dir / f"{key}.png")).convert()
            self.background_art[key] = pygame.transform.scale(image, (WIDTH, HEIGHT))

    def font(self, size: int) -> pygame.font.Font:
        if size not in self.fonts:
            for name in ("Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "Noto Sans CJK SC"):
                candidate = pygame.font.SysFont(name, size)
                if candidate:
                    self.fonts[size] = candidate
                    break
            else:
                self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size]

    def text(self, surface: pygame.Surface, value: str, pos: tuple[int, int], size: int = 12,
             color: tuple[int, int, int] = (230, 234, 244), anchor: str = "topleft") -> None:
        image = self.font(size).render(value, True, color)
        rect = image.get_rect(**{anchor: pos})
        surface.blit(image, rect)

    def draw(self, surface: pygame.Surface, game: Game) -> None:
        self.background(surface, game.time)
        if game.state == "menu":
            self.menu(surface, game)
            return
        self.world(surface, game)
        if game.shake > 0:
            alpha = min(58, int(game.shake * 18))
            self.hit_overlay.fill((156, 38, 58, alpha))
            surface.blit(self.hit_overlay, (0, 0))
        self.hud(surface, game)
        if game.state == "upgrade":
            self.upgrade(surface, game)
        elif game.state == "paused":
            self.panel(surface, "静修中", "秘境中的时间已停驻", "按 P / Esc 继续", "继续", (207, 193, 141))
        elif game.state == "won":
            self.panel(surface, "秘境通关", "你已参透此境，踏入新的仙途。", f"存活 {self.time_text(game.time)}  ·  斩妖 {game.kills}", "再入秘境", (154, 226, 190))
        elif game.state == "lost":
            self.panel(surface, "道消身殒", "此番修行止步于此，来日再战。", f"修行 {self.time_text(game.time)}  ·  斩妖 {game.kills}", "重新开始", (226, 142, 147))

    @staticmethod
    def time_text(seconds: float) -> str:
        return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"

    def background(self, surface: pygame.Surface, t: float) -> None:
        if self.background_art:
            key = "raven_realm" if t < RUN_LENGTH / 3 else "wolf_realm" if t < RUN_LENGTH else "toad_realm"
            surface.blit(self.background_art[key], (0, 0))
            mote_colors = {
                "raven_realm": (146, 194, 208),
                "wolf_realm": (219, 170, 111),
                "toad_realm": (180, 135, 222),
            }
            mote = mote_colors[key]
            for i in range(13):
                x = (i * 83 + int(t * (4 + i % 3))) % WIDTH
                y = 58 + (i * 47 + int(math.sin(t * 0.7 + i) * 5)) % 184
                surface.set_at((x, y), mote)
                if i % 4 == 0:
                    surface.set_at((x + 1, y), (min(255, mote[0] + 38), min(255, mote[1] + 38), min(255, mote[2] + 38)))
            return
        surface.fill((15, 22, 37))
        # Pixelated mountain silhouettes and softly glimmering spirit lights.
        pygame.draw.rect(surface, (19, 31, 45), (0, 190, WIDTH, 80))
        for layer, color, baseline in ((0, (24, 43, 56), 162), (1, (30, 51, 61), 185)):
            for x in range(-24, WIDTH + 32, 48):
                offset = int(12 * math.sin(x * 0.047 + layer * 2))
                points = [(x - 18, baseline + 22), (x + 5, baseline - 20 + offset),
                          (x + 20, baseline - 2 + offset), (x + 39, baseline + 22),
                          (x + 48, baseline + 28), (x - 18, baseline + 28)]
                pygame.draw.polygon(surface, color, points)
        for i in range(24):
            x = (i * 83 + int(t * (5 + i % 3))) % WIDTH
            y = (i * 47 + 31) % HEIGHT
            if i % 3:
                surface.set_at((x, y), (57, 100, 111))
        # Stone path marks ground texture without introducing external art.
        for i in range(34):
            x = (i * 71 + 11) % WIDTH
            y = 198 + (i * 29) % 66
            pygame.draw.rect(surface, (36, 52, 59), (x, y, 4 + i % 5, 1))

    def world(self, surface: pygame.Surface, game: Game) -> None:
        for hazard in game.hazards:
            pulse = int(2 * math.sin(game.time * 5))
            pygame.draw.ellipse(surface, (72, 22, 39), (int(hazard.x - hazard.radius), int(hazard.y - hazard.radius // 2), hazard.radius * 2, hazard.radius))
            pygame.draw.ellipse(surface, (235, 48 + pulse, 72), (int(hazard.x - hazard.radius + 3), int(hazard.y - hazard.radius // 2 + 2), hazard.radius * 2 - 6, hazard.radius - 4), 1)
            pygame.draw.circle(surface, (255, 117, 117), (int(hazard.x), int(hazard.y - 2)), 2)
        for orb in game.orbs:
            pygame.draw.rect(surface, (116, 246, 183), (int(orb.x) - 2, int(orb.y) - 2, 5, 5))
            surface.set_at((int(orb.x), int(orb.y) - 3), (218, 255, 219))
        for shot in game.projectiles:
            if shot.hostile:
                if shot.kind == "feather":
                    tail = (int(shot.x - shot.vx * 0.065), int(shot.y - shot.vy * 0.065))
                    pygame.draw.line(surface, (139, 27, 51), tail, (int(shot.x), int(shot.y)), 3)
                    pygame.draw.line(surface, (255, 77, 94), tail, (int(shot.x), int(shot.y)), 1)
                    surface.set_at((int(shot.x), int(shot.y)), (255, 220, 206))
                else:
                    pygame.draw.circle(surface, (193, 29, 66), (int(shot.x), int(shot.y)), 6)
                    pygame.draw.circle(surface, (255, 89, 110), (int(shot.x), int(shot.y)), 4)
                    pygame.draw.circle(surface, (255, 222, 214), (int(shot.x) - 1, int(shot.y) - 1), 2)
            elif shot.kind == "fire":
                pygame.draw.circle(surface, (248, 103, 66), (int(shot.x), int(shot.y)), 4)
                pygame.draw.rect(surface, (255, 224, 135), (int(shot.x) - 1, int(shot.y) - 2, 3, 3))
            else:
                pygame.draw.line(surface, (191, 216, 255), (int(shot.x), int(shot.y)),
                                 (int(shot.x - shot.vx * 0.055), int(shot.y - shot.vy * 0.055)), 2)
                surface.set_at((int(shot.x), int(shot.y)), (255, 248, 200))
        for x, y, radius, life in game.slashes:
            col = (255, 143, 79) if game.selected_character == "female" and radius > 20 else (133, 215, 247) if radius > 30 else (249, 232, 174)
            pygame.draw.circle(surface, col, (int(x), int(y)), int(radius * max(0.2, life / 0.22)), 1)
        for enemy in game.enemies:
            self.enemy(surface, enemy, game.time)
        p = game.player
        for i in range(p.talisman_level):
            if i >= 8:
                break
            a = game.time * 2.3 + math.tau * i / min(8, p.talisman_level)
            x, y = int(p.x + math.cos(a) * 21), int(p.y + math.sin(a) * 14)
            pygame.draw.rect(surface, (244, 184, 92), (x - 2, y - 3, 5, 7))
            pygame.draw.rect(surface, (255, 232, 157), (x - 1, y - 2, 2, 4))
        if not (p.invulnerable > 0 and int(p.invulnerable * 18) % 2):
            self.player_sprite(surface, p, game.selected_character, game.time)

    def player_sprite(self, surface: pygame.Surface, player, character: str, time: float) -> None:
        x, y = int(player.x), int(player.y)
        frames = self.player_art[character][player.facing]
        frame = int(time * 10) % len(frames) if player.moving else 0
        sprite = frames[frame]
        pygame.draw.ellipse(surface, (10, 16, 26), (x - 15, y + 23, 30, 6))
        pygame.draw.circle(surface, (103, 166, 196), (x, y + 2), 17, 1)
        bob = round(math.sin(time * (12 if player.moving else 2)) * (1 if player.moving else 0.5))
        surface.blit(sprite, sprite.get_rect(center=(x, y + bob)))

    def enemy(self, surface: pygame.Surface, enemy, time: float) -> None:
        x, y, r = int(enemy.x), int(enemy.y), enemy.radius
        sprite = self.enemy_art[enemy.kind]
        bob = round(math.sin(time * 5 + x) * (1 if not enemy.elite else 2))
        pygame.draw.ellipse(surface, (9, 14, 23), (x - r - 3, y + r - 2, r * 2 + 6, 5))
        if enemy.elite and enemy.attack_cooldown < 0.28:
            pulse = int(1 + 2 * abs(math.sin(time * 15)))
            pygame.draw.circle(surface, (255, 42, 69), (x, y), r + 6 + pulse, 2)
        rim = self.enemy_rims[enemy.kind]
        rim_rect = rim.get_rect(center=(x, y + bob))
        for offset in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(rim, rim_rect.move(*offset))
        surface.blit(sprite, sprite.get_rect(center=(x, y + bob)))
        if enemy.attack_flash > 0:
            pygame.draw.circle(surface, (255, 57, 78), (x, y), r + 4, 2)
        if enemy.elite:
            pygame.draw.rect(surface, (53, 25, 36), (x - 22, y - 34, 44, 5))
            pygame.draw.rect(surface, (230, 78, 96), (x - 21, y - 33, max(1, int(42 * enemy.hp / 760)), 3))
            self.text(surface, "毒沼蛙君", (x, y - 49), 8, (255, 116, 133), "midbottom")

    def hud(self, surface: pygame.Surface, game: Game) -> None:
        p = game.player
        # Compact, framed status panels leave the playfield readable.
        pygame.draw.rect(surface, (11, 17, 29), (7, 7, 142, 39))
        pygame.draw.rect(surface, (57, 73, 84), (7, 7, 142, 39), 1)
        self.text(surface, "气血", (12, 11), 8, (192, 204, 207))
        self.text(surface, f"{int(p.hp):03d}/{int(p.max_hp):03d}", (139, 10), 9, (239, 220, 211), "topright")
        pygame.draw.rect(surface, (43, 49, 62), (12, 25, 130, 7))
        ratio = max(0, min(1, p.hp / p.max_hp))
        pygame.draw.rect(surface, (196, 75, 96), (13, 26, int(128 * ratio), 5))
        pygame.draw.rect(surface, (235, 137, 146), (13, 26, int(128 * ratio), 1))
        self.text(surface, f"修为 Lv.{p.level}", (12, 35), 8, (226, 207, 151))
        self.text(surface, f"斩妖 {game.kills}", (139, 35), 8, (173, 200, 205), "topright")
        left = max(0, RUN_LENGTH - game.time)
        pygame.draw.rect(surface, (11, 17, 29), (WIDTH - 104, 7, 97, 39))
        pygame.draw.rect(surface, (57, 73, 84), (WIDTH - 104, 7, 97, 39), 1)
        label = "蛙君现世" if game.elite_spawned else "秘境历练"
        self.text(surface, label, (WIDTH - 96, 11), 8,
                  (238, 153, 153) if game.elite_spawned else (148, 185, 182))
        self.text(surface, self.time_text(left), (WIDTH - 13, 20), 15, (239, 224, 180), "topright")
        boss = next((enemy for enemy in game.enemies if enemy.elite), None)
        if boss:
            bx, by, bw = (WIDTH - 184) // 2, 52, 184
            pygame.draw.rect(surface, (11, 16, 27), (bx, by, bw, 20))
            pygame.draw.rect(surface, (116, 76, 100), (bx, by, bw, 20), 1)
            self.text(surface, "秘境首领 · 毒沼蛙君", (bx + 5, by + 3), 8, (229, 190, 203))
            hp = max(0, min(1, boss.hp / 760))
            pygame.draw.rect(surface, (45, 31, 43), (bx + 5, by + 14, bw - 10, 3))
            pygame.draw.rect(surface, (216, 77, 103), (bx + 5, by + 14, int((bw - 10) * hp), 3))
        pygame.draw.rect(surface, (11, 17, 28), (0, HEIGHT - 14, WIDTH, 14))
        pygame.draw.rect(surface, (42, 58, 58), (7, HEIGHT - 7, WIDTH - 14, 3))
        xp_width = int((WIDTH - 14) * min(1, p.xp / p.next_xp))
        pygame.draw.rect(surface, (83, 193, 147), (7, HEIGHT - 7, xp_width, 3))
        if xp_width > 0:
            pygame.draw.rect(surface, (173, 239, 185), (7, HEIGHT - 7, xp_width, 1))
        self.text(surface, f"灵气 {int(p.xp)}/{int(p.next_xp)}", (8, HEIGHT - 13), 7, (151, 216, 182), "bottomleft")
        if game.time < 14:
            attack_hint = "火球爆燃  ·  范围伤害" if game.selected_character == "female" else "灵剑追击  ·  高速单体"
            self.text(surface, f"WASD 移动  ·  {attack_hint}  ·  P 暂停", (WIDTH // 2, 49), 9, (206, 218, 209), "midtop")

    def veil(self, surface: pygame.Surface) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 8, 16, 190))
        surface.blit(shade, (0, 0))

    def panel(self, surface: pygame.Surface, title: str, subtitle: str, info: str,
              button: str, accent: tuple[int, int, int]) -> None:
        self.veil(surface)
        pygame.draw.rect(surface, (19, 27, 41), (84, 56, 312, 162))
        pygame.draw.rect(surface, (73, 85, 96), (84, 56, 312, 162), 1)
        pygame.draw.rect(surface, accent, (85, 57, 310, 2))
        self.text(surface, "✦", (WIDTH // 2, 69), 12, accent, "midtop")
        self.text(surface, title, (WIDTH // 2, 84), 23, accent, "midtop")
        self.text(surface, subtitle, (WIDTH // 2, 119), 10, (206, 214, 222), "midtop")
        self.text(surface, info, (WIDTH // 2, 139), 9, (165, 178, 190), "midtop")
        self.button(surface, button, 164, 165, 152, 30, accent)
        self.text(surface, "Enter 确认", (WIDTH // 2, 201), 8, (136, 150, 163), "midtop")

    def button(self, surface: pygame.Surface, label: str, x: int, y: int,
               w: int, h: int, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(surface, (19, 27, 40), (x, y, w, h))
        pygame.draw.rect(surface, (46, 58, 71), (x + 2, y + 2, w - 4, h - 4))
        pygame.draw.rect(surface, color, (x, y, w, h), 1)
        self.text(surface, label, (x + w // 2, y + h // 2), 11, color, "center")

    def menu(self, surface: pygame.Surface, game: Game) -> None:
        self.veil(surface)
        pygame.draw.rect(surface, (12, 20, 32), (36, 10, 408, 250))
        pygame.draw.rect(surface, (74, 91, 99), (36, 10, 408, 250), 1)
        pygame.draw.rect(surface, (180, 164, 119), (37, 11, 406, 2))
        self.text(surface, "秘 境 求 生", (WIDTH // 2, 18), 23, (233, 218, 171), "midtop")
        self.text(surface, "择一位修行者，开启你的仙途", (WIDTH // 2, 49), 9, (168, 201, 193), "midtop")

        choices = [
            ("male", "云归", "男修"),
            ("female", "洛璃", "女修"),
        ]
        for i, (key, name, subtitle) in enumerate(choices):
            x = 92 + i * 160
            selected = key == game.selected_character
            border = (235, 210, 148) if selected else (79, 93, 105)
            pygame.draw.rect(surface, (24, 35, 51), (x, 73, 136, 108))
            pygame.draw.rect(surface, border, (x, 73, 136, 108), 2 if selected else 1)
            if selected:
                pygame.draw.rect(surface, (65, 67, 60), (x + 5, 78, 126, 98), 1)
            sprite = self.player_art[key]["down"][0]
            surface.blit(sprite, sprite.get_rect(center=(x + 68, 116)))
            self.text(surface, f"{name}  ·  {subtitle}", (x + 68, 151), 9,
                      (240, 220, 173) if selected else (182, 195, 199), "midtop")
            attack = "灵剑：高速单体" if key == "male" else "火球：爆燃范围"
            self.text(surface, attack, (x + 68, 165), 7,
                      (157, 204, 224) if key == "male" else (246, 169, 119), "midtop")

        self.button(surface, "踏入秘境", 166, 190, 148, 30, (230, 207, 145))
        self.text(surface, "点击角色选择 · ← → 切换 · Enter 开始", (WIDTH // 2, 225), 8,
                  (148, 165, 172), "midtop")
        self.text(surface, "WASD 移动 · 自动施法 · 八分钟后迎战妖王", (WIDTH // 2, 240), 8,
                  (134, 151, 164), "midtop")

    def upgrade(self, surface: pygame.Surface, game: Game) -> None:
        self.veil(surface)
        self.text(surface, "灵台顿悟", (WIDTH // 2, 30), 22, (231, 214, 165), "midtop")
        self.text(surface, "选择一门功法，继续你的修行", (WIDTH // 2, 58), 10, (179, 194, 198), "midtop")
        accents = [(133, 199, 222), (215, 174, 119), (179, 158, 215)]
        for i, key in enumerate(game.upgrades):
            x = 42 + i * 136
            pygame.draw.rect(surface, (15, 23, 37), (x, 88, 128, 132))
            pygame.draw.rect(surface, (72, 82, 94), (x, 88, 128, 132), 1)
            pygame.draw.rect(surface, accents[i], (x + 1, 89, 126, 2))
            self.text(surface, f"{i + 1}  ·  功法", (x + 10, 100), 8, accents[i])
            title, desc = EVOLUTIONS[key] if key in EVOLUTIONS else UPGRADES[key][0], EVOLUTIONS[key][1] if key in EVOLUTIONS else UPGRADES[key][1]
            if key == "sword":
                title = "控火诀" if game.selected_character == "female" else "御剑术"
                desc = "火球伤害提高" if game.selected_character == "female" else "灵剑伤害提高"
            self.text(surface, title, (x + 64, 128), 12, (232, 229, 213), "midtop")
            self.text(surface, desc[:9], (x + 64, 155), 8, (165, 181, 188), "midtop")
            if len(desc) > 9:
                self.text(surface, desc[9:18], (x + 64, 167), 8, (165, 181, 188), "midtop")
            self.button(surface, f"按 {i + 1} 选择", x + 16, 190, 96, 22, accents[i])
        self.text(surface, "点击卡牌或按数字键", (WIDTH // 2, 235), 8, (139, 154, 164), "midtop")
