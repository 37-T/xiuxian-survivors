"""Pixel-art presentation and Chinese UI."""

from __future__ import annotations

import math
from pathlib import Path
import pygame

from game import Game, HEIGHT, RUN_LENGTH, UPGRADES, WIDTH


class Renderer:
    def __init__(self) -> None:
        self.fonts: dict[int, pygame.font.Font] = {}
        self.player_art: dict[str, dict[str, list[pygame.Surface]]] = {}
        self.enemy_art: dict[str, pygame.Surface] = {}
        self.load_art()

    def load_art(self) -> None:
        root = Path(__file__).resolve().parent / "assets" / "third_party"
        male_sheet = pygame.image.load(str(root / "player_male.png")).convert_alpha()

        def male_frame(row: int, column: int) -> pygame.Surface:
            frame = male_sheet.subsurface((column * 40, row * 64, 40, 64)).copy()
            return pygame.transform.scale(frame, (32, 48))

        side = [male_frame(1, i) for i in range(4)]
        self.player_art["male"] = {
            "down": [male_frame(0, 0), male_frame(0, 1)],
            "up": [male_frame(0, 2), male_frame(0, 3)],
            "left": side,
            "right": [pygame.transform.flip(sprite, True, False) for sprite in side],
        }

        julia_dir = root / "julia" / "Sprite-Sheets-Julia"
        female_files = {
            "down": "Julia_walk_Foward_64x64.png",
            "up": "Julia_walk_Up_64x64.png",
            "left": "Julia_walk_Left_64x64.png",
            "right": "Julia_walk_Rigth_64x64.png",
        }
        self.player_art["female"] = {}
        for direction, filename in female_files.items():
            sheet = pygame.image.load(str(julia_dir / filename)).convert_alpha()
            self.player_art["female"][direction] = [
                pygame.transform.scale(sheet.subsurface((i * 64, 0, 64, 64)).copy(), (44, 48))
                for i in range(4)
            ]

        creature_dir = root / "miteclops"
        creature_files = {
            "wisp": ("Miteclops Yellow.png", (16, 25)),
            "wolf": ("Miteclops Red.png", (20, 29)),
            "brute": ("Red Eye Stalagmite.png", (24, 35)),
            "elite": ("Yellow Eye Stalagmite.png", (40, 54)),
        }
        for kind, (filename, size) in creature_files.items():
            image = pygame.image.load(str(creature_dir / filename)).convert_alpha()
            bounds = image.get_bounding_rect(min_alpha=1)
            image = image.subsurface(bounds).copy()
            self.enemy_art[kind] = pygame.transform.scale(image, size)

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
        for orb in game.orbs:
            pygame.draw.rect(surface, (116, 246, 183), (int(orb.x) - 2, int(orb.y) - 2, 5, 5))
            surface.set_at((int(orb.x), int(orb.y) - 3), (218, 255, 219))
        for shot in game.projectiles:
            pygame.draw.line(surface, (191, 216, 255), (int(shot.x), int(shot.y)),
                             (int(shot.x - shot.vx * 0.055), int(shot.y - shot.vy * 0.055)), 2)
            surface.set_at((int(shot.x), int(shot.y)), (255, 248, 200))
        for x, y, radius, life in game.slashes:
            col = (133, 215, 247) if radius > 30 else (249, 232, 174)
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
        pygame.draw.ellipse(surface, (10, 16, 26), (x - 12, y + 13, 24, 7))
        pygame.draw.circle(surface, (103, 166, 196), (x, y + 2), 17, 1)
        surface.blit(sprite, sprite.get_rect(center=(x, y)))

    def enemy(self, surface: pygame.Surface, enemy, time: float) -> None:
        x, y, r = int(enemy.x), int(enemy.y), enemy.radius
        sprite = self.enemy_art[enemy.kind]
        bob = round(math.sin(time * 5 + x) * (1 if not enemy.elite else 2))
        pygame.draw.ellipse(surface, (9, 14, 23), (x - r - 3, y + r - 2, r * 2 + 6, 5))
        surface.blit(sprite, sprite.get_rect(center=(x, y + bob)))
        if enemy.attack_flash > 0:
            pygame.draw.circle(surface, (255, 209, 147), (x, y), r + 3, 1)
        if enemy.elite:
            pygame.draw.rect(surface, (53, 25, 36), (x - 22, y - 34, 44, 5))
            pygame.draw.rect(surface, (230, 78, 96), (x - 21, y - 33, max(1, int(42 * enemy.hp / 520)), 3))
            self.text(surface, "秘境妖王", (x, y - 41), 8, (250, 193, 168), "midbottom")

    def hud(self, surface: pygame.Surface, game: Game) -> None:
        p = game.player
        pygame.draw.rect(surface, (13, 18, 30), (7, 7, 135, 34))
        pygame.draw.rect(surface, (46, 51, 66), (10, 10, 68, 6))
        pygame.draw.rect(surface, (204, 86, 105), (10, 10, int(68 * p.hp / p.max_hp), 6))
        self.text(surface, f"气血 {int(p.hp)}/{int(p.max_hp)}", (10, 19), 9)
        self.text(surface, f"修为  Lv.{p.level}", (84, 9), 10, (218, 207, 161))
        self.text(surface, f"斩妖 {game.kills}", (84, 24), 9, (173, 200, 205))
        left = max(0, RUN_LENGTH - game.time)
        self.text(surface, self.time_text(left), (WIDTH - 9, 9), 13, (226, 220, 185), "topright")
        label = "精英现世" if game.elite_spawned else "秘境历练"
        self.text(surface, label, (WIDTH - 9, 25), 9, (238, 153, 153) if game.elite_spawned else (148, 185, 182), "topright")
        pygame.draw.rect(surface, (18, 25, 35), (7, HEIGHT - 9, WIDTH - 14, 4))
        pygame.draw.rect(surface, (83, 193, 147), (7, HEIGHT - 9, int((WIDTH - 14) * min(1, p.xp / p.next_xp)), 4))
        self.text(surface, "灵气", (8, HEIGHT - 22), 8, (151, 216, 182))
        if game.time < 14:
            self.text(surface, "WASD 移动  ·  灵剑自动御敌  ·  P 暂停", (WIDTH // 2, 49), 9, (206, 218, 209), "midtop")

    def veil(self, surface: pygame.Surface) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 8, 16, 190))
        surface.blit(shade, (0, 0))

    def panel(self, surface: pygame.Surface, title: str, subtitle: str, info: str,
              button: str, accent: tuple[int, int, int]) -> None:
        self.veil(surface)
        pygame.draw.rect(surface, (29, 38, 53), (90, 64, 300, 150))
        pygame.draw.rect(surface, accent, (90, 64, 300, 2))
        self.text(surface, title, (WIDTH // 2, 89), 23, accent, "midtop")
        self.text(surface, subtitle, (WIDTH // 2, 124), 10, (206, 214, 222), "midtop")
        self.text(surface, info, (WIDTH // 2, 141), 9, (165, 178, 190), "midtop")
        self.button(surface, button, 164, 166, 152, 29, accent)
        self.text(surface, "Enter 开始 / 继续", (WIDTH // 2, 202), 8, (136, 150, 163), "midtop")

    def button(self, surface: pygame.Surface, label: str, x: int, y: int,
               w: int, h: int, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(surface, (46, 54, 69), (x, y, w, h))
        pygame.draw.rect(surface, color, (x, y, w, h), 1)
        self.text(surface, label, (x + w // 2, y + h // 2), 11, color, "center")

    def menu(self, surface: pygame.Surface, game: Game) -> None:
        self.veil(surface)
        pygame.draw.rect(surface, (27, 36, 51), (48, 14, 384, 242))
        pygame.draw.rect(surface, (180, 164, 119), (48, 14, 384, 2))
        self.text(surface, "仙 途", (WIDTH // 2, 23), 27, (233, 218, 171), "midtop")
        self.text(surface, "选择你的修行者", (WIDTH // 2, 58), 10, (168, 201, 193), "midtop")

        choices = [
            ("male", "云归", "男修"),
            ("female", "洛璃", "女修"),
        ]
        for i, (key, name, subtitle) in enumerate(choices):
            x = 92 + i * 160
            selected = key == game.selected_character
            border = (235, 210, 148) if selected else (79, 93, 105)
            pygame.draw.rect(surface, (37, 48, 64), (x, 83, 136, 96))
            pygame.draw.rect(surface, border, (x, 83, 136, 96), 2 if selected else 1)
            sprite = self.player_art[key]["down"][0]
            surface.blit(sprite, sprite.get_rect(center=(x + 68, 124)))
            self.text(surface, f"{name}  ·  {subtitle}", (x + 68, 163), 9,
                      (240, 220, 173) if selected else (182, 195, 199), "midtop")

        self.button(surface, "踏入秘境", 166, 190, 148, 30, (230, 207, 145))
        self.text(surface, "点击角色选择 · ← → 切换 · Enter 开始", (WIDTH // 2, 226), 8,
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
            pygame.draw.rect(surface, (28, 38, 53), (x, 91, 128, 126))
            pygame.draw.rect(surface, accents[i], (x, 91, 128, 2))
            self.text(surface, f"0{i + 1}", (x + 12, 101), 9, accents[i])
            self.text(surface, UPGRADES[key][0], (x + 64, 126), 13, (232, 229, 213), "midtop")
            desc = UPGRADES[key][1]
            self.text(surface, desc[:8], (x + 64, 153), 9, (165, 181, 188), "midtop")
            if len(desc) > 8:
                self.text(surface, desc[8:], (x + 64, 166), 9, (165, 181, 188), "midtop")
            self.text(surface, f"按 {i + 1} 选择", (x + 64, 194), 9, accents[i], "midtop")
        self.text(surface, "点击卡牌或按数字键", (WIDTH // 2, 235), 8, (139, 154, 164), "midtop")
