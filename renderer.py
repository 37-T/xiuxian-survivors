"""Pixel-art presentation and Chinese UI."""

from __future__ import annotations

import math
import random
from pathlib import Path
import pygame

from game import EVOLUTIONS, Game, HEIGHT, RUN_LENGTH, UPGRADES, WIDTH
from layout import (
    CHARACTER_CARDS,
    MENU_PANEL,
    PANEL,
    PANEL_BUTTON,
    START_BUTTON,
    UPGRADE_CARDS,
)

FONT_CANDIDATES = (
    "microsoftyaheiui",
    "microsoftyahei",
    "simhei",
    "notosanssc",
    "notosanscjksc",
)

GROUND_PALETTES = {
    "raven_realm": ((28, 36, 45), (22, 29, 37), (40, 50, 59), (58, 86, 88)),
    "wolf_realm": ((62, 50, 36), (50, 40, 29), (78, 63, 44), (102, 92, 58)),
    "toad_realm": ((32, 28, 43), (24, 21, 33), (45, 38, 58), (82, 62, 112)),
}
DECOR_CELL = 150


class Renderer:
    def __init__(self) -> None:
        self.fonts: dict[int, pygame.font.Font] = {}
        self.player_art: dict[str, dict[str, list[pygame.Surface]]] = {}
        self.enemy_art: dict[str, pygame.Surface] = {}
        self.enemy_rims: dict[str, pygame.Surface] = {}
        self.background_art: dict[str, pygame.Surface] = {}
        self.ground_tiles: dict[str, pygame.Surface] = {}
        self.hit_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.text_queue: list[tuple[str, tuple[float, float], int, tuple[int, int, int], str]] | None = None
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
            "toad_boss": ("toad_boss.png", (48, 48)),
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
        self.ground_tiles = {
            key: self._make_ground_tile(key) for key in ("raven_realm", "wolf_realm", "toad_realm")
        }

    @staticmethod
    def _make_ground_tile(key: str) -> pygame.Surface:
        base, dark, light, accent = GROUND_PALETTES[key]
        rng = random.Random(key + "-ground")
        size = 192
        tile = pygame.Surface((size, size))
        tile.fill(base)

        def wrapped_polygon(color: tuple[int, int, int], points: list[tuple[float, float]]) -> None:
            for dx in (-size, 0, size):
                for dy in (-size, 0, size):
                    pygame.draw.polygon(tile, color, [(x + dx, y + dy) for x, y in points])

        def wrapped_ellipse(color: tuple[int, int, int], x: int, y: int, w: int, h: int) -> None:
            for dx in (-size, 0, size):
                for dy in (-size, 0, size):
                    pygame.draw.ellipse(tile, color, (x + dx, y + dy, w, h))

        def wrapped_line(color: tuple[int, int, int], x1: int, y1: int, x2: int, y2: int) -> None:
            for dx in (-size, 0, size):
                for dy in (-size, 0, size):
                    pygame.draw.line(tile, color, (x1 + dx, y1 + dy), (x2 + dx, y2 + dy), 1)

        for _ in range(16):
            cx, cy = rng.randrange(size), rng.randrange(size)
            radius = rng.randint(8, 24)
            points = []
            for step in range(7):
                angle = math.tau * step / 7
                distance = radius * rng.uniform(0.6, 1.0)
                points.append((cx + math.cos(angle) * distance, cy + math.sin(angle) * distance))
            wrapped_polygon(dark if rng.random() < 0.55 else light, points)
        for _ in range(40):
            x, y = rng.randrange(size), rng.randrange(size)
            wrapped_ellipse(light if rng.random() < 0.5 else dark, x, y, rng.randint(2, 7), rng.randint(2, 4))
        for _ in range(40):
            x, y = rng.randrange(size), rng.randrange(size)
            wrapped_line(dark, x, y, x + rng.randint(-14, 14), y + rng.randint(-8, 8))
        for _ in range(220):
            x, y = rng.randrange(size), rng.randrange(size)
            tile.set_at((x, y), accent if rng.random() < 0.25 else light)

        if key == "wolf_realm":
            for _ in range(14):
                x, y = rng.randrange(size), rng.randrange(size)
                for offset in (-2, 0, 2):
                    wrapped_line(accent, x + offset, y, x + offset + rng.randint(-2, 2), y - rng.randint(3, 6))
        elif key == "toad_realm":
            for _ in range(10):
                x, y = rng.randrange(size), rng.randrange(size)
                wrapped_polygon(accent, [(x, y - 4), (x + 3, y), (x, y + 4), (x - 3, y)])
        else:
            for _ in range(10):
                x, y = rng.randrange(size), rng.randrange(size)
                wrapped_line(accent, x - 3, y, x + 3, y)
        return tile

    def _draw_decorations(self, surface: pygame.Surface, game: Game,
                          camera_x: float, camera_y: float) -> None:
        key = "raven_realm" if game.time < RUN_LENGTH / 3 else "wolf_realm" if game.time < RUN_LENGTH else "toad_realm"
        start_x = math.floor((camera_x - 24) / DECOR_CELL)
        end_x = math.floor((camera_x + WIDTH + 24) / DECOR_CELL)
        start_y = math.floor((camera_y - 24) / DECOR_CELL)
        end_y = math.floor((camera_y + HEIGHT + 24) / DECOR_CELL)
        for gx in range(start_x, end_x + 1):
            for gy in range(start_y, end_y + 1):
                rng = random.Random(f"{key}:{gx}:{gy}")
                if rng.random() > 0.4:
                    continue
                wx = gx * DECOR_CELL + rng.uniform(12, DECOR_CELL - 12)
                wy = gy * DECOR_CELL + rng.uniform(12, DECOR_CELL - 12)
                sx = int(wx - camera_x)
                sy = int(wy - camera_y)
                if -24 <= sx <= WIDTH + 24 and -24 <= sy <= HEIGHT + 24:
                    self._draw_decor(surface, key, sx, sy, rng)

    @staticmethod
    def _draw_decor(surface: pygame.Surface, key: str, x: int, y: int,
                    rng: random.Random) -> None:
        if key == "wolf_realm":
            if rng.random() < 0.55:
                for _ in range(rng.randint(4, 7)):
                    dx = rng.randint(-6, 6)
                    pygame.draw.line(surface, (102, 92, 58), (x + dx, y),
                                     (x + dx + rng.randint(-2, 2), y - rng.randint(4, 9)), 1)
            else:
                pygame.draw.ellipse(surface, (48, 39, 28), (x - 6, y - 3, 12, 8))
                pygame.draw.ellipse(surface, (76, 62, 43), (x - 5, y - 3, 10, 5))
        elif key == "toad_realm":
            if rng.random() < 0.55:
                height = rng.randint(6, 11)
                pygame.draw.polygon(surface, (80, 62, 112),
                                    [(x, y - height), (x + 4, y), (x, y + 4), (x - 4, y)])
                pygame.draw.line(surface, (130, 100, 160), (x, y - height), (x, y), 1)
            else:
                for _ in range(4):
                    pygame.draw.circle(surface, (90, 70, 120),
                                       (x + rng.randint(-4, 4), y + rng.randint(-3, 3)), 1)
        else:
            if rng.random() < 0.5:
                for _ in range(rng.randint(3, 4)):
                    dx, dy = rng.randint(-5, 5), rng.randint(-3, 3)
                    pygame.draw.circle(surface, (55, 66, 76), (x + dx, y + dy), rng.randint(2, 5))
                    pygame.draw.circle(surface, (80, 96, 104), (x + dx - 1, y + dy - 1), 1)
            else:
                pygame.draw.circle(surface, (58, 86, 88), (x, y), 6, 1)
                pygame.draw.line(surface, (58, 86, 88), (x - 4, y), (x + 4, y), 1)

    def font(self, size: int) -> pygame.font.Font:
        if size not in self.fonts:
            path = next(
                (path for path in (pygame.font.match_font(name) for name in FONT_CANDIDATES) if path),
                None,
            )
            self.fonts[size] = pygame.font.Font(path, size) if path else pygame.font.Font(None, size)
        return self.fonts[size]

    def text(self, surface: pygame.Surface, value: str, pos: tuple[int, int], size: int = 12,
             color: tuple[int, int, int] = (230, 234, 244), anchor: str = "topleft") -> None:
        if self.text_queue is not None:
            self.text_queue.append((value, (float(pos[0]), float(pos[1])), size, color, anchor))
            return
        image = self.font(size).render(value, True, color)
        rect = image.get_rect(**{anchor: pos})
        surface.blit(image, rect)

    def begin_text_layer(self) -> None:
        """Collect text so it can be rendered at window resolution after scaling."""
        self.text_queue = []

    def flush_text(self, target: pygame.Surface, origin: tuple[int, int], scale: float) -> None:
        """Render the collected text crisply at the window's pixel size."""
        if self.text_queue is None:
            return
        queue = self.text_queue
        self.text_queue = None
        for value, pos, size, color, anchor in queue:
            image = self.font(max(1, round(size * scale))).render(value, True, color)
            rect = image.get_rect(
                **{anchor: (round(origin[0] + pos[0] * scale), round(origin[1] + pos[1] * scale))}
            )
            target.blit(image, rect)

    def draw(self, surface: pygame.Surface, game: Game) -> None:
        camera_x = game.player.x - WIDTH / 2
        camera_y = game.player.y - HEIGHT / 2
        self.background(surface, game.time, camera_x, camera_y, scenic=game.state == "menu")
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
            self.panel(surface, "静修中", "秘境中的时间已停驻", "按 P / Esc / Enter 继续", "继续", (207, 193, 141))
        elif game.state == "won":
            self.panel(surface, "秘境通关", "你已参透此境，踏入新的仙途。", f"存活 {self.time_text(game.time)}  ·  斩妖 {game.kills}", "再入秘境", (154, 226, 190))
        elif game.state == "lost":
            self.panel(surface, "道消身殒", "此番修行止步于此，来日再战。", f"修行 {self.time_text(game.time)}  ·  斩妖 {game.kills}", "重新开始", (226, 142, 147))

    @staticmethod
    def time_text(seconds: float) -> str:
        return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"

    def background(self, surface: pygame.Surface, t: float,
                   camera_x: float = 0.0, camera_y: float = 0.0, scenic: bool = False) -> None:
        key = "raven_realm" if t < RUN_LENGTH / 3 else "wolf_realm" if t < RUN_LENGTH else "toad_realm"
        if scenic and self.background_art:
            surface.blit(self.background_art[key], (0, 0))
            self._draw_motes(surface, t, key, 0.0, 0.0)
            return
        tile = self.ground_tiles.get(key)
        if tile:
            tw, th = tile.get_size()
            offset_x = int(camera_x) % tw
            offset_y = int(camera_y) % th
            for x in range(-tw - offset_x, WIDTH + tw, tw):
                for y in range(-th - offset_y, HEIGHT + th, th):
                    surface.blit(tile, (x, y))
            self._draw_motes(surface, t, key, camera_x, camera_y)
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

    @staticmethod
    def _draw_motes(surface: pygame.Surface, t: float, key: str,
                    camera_x: float, camera_y: float) -> None:
        mote_colors = {
            "raven_realm": (146, 194, 208),
            "wolf_realm": (219, 170, 111),
            "toad_realm": (180, 135, 222),
        }
        mote = mote_colors[key]
        for i in range(13):
            x = (i * 83 + int(t * (4 + i % 3)) + int(camera_x)) % WIDTH
            y = 58 + (i * 47 + int(math.sin(t * 0.7 + i) * 5) + int(camera_y)) % 184
            surface.set_at((x, y), mote)
            if i % 4 == 0:
                surface.set_at((x + 1, y), (min(255, mote[0] + 38), min(255, mote[1] + 38), min(255, mote[2] + 38)))

    def world(self, surface: pygame.Surface, game: Game) -> None:
        camera_x = game.player.x - WIDTH / 2
        camera_y = game.player.y - HEIGHT / 2
        self._draw_decorations(surface, game, camera_x, camera_y)
        for hazard in game.hazards:
            pulse = int(2 * math.sin(game.time * 5))
            if hazard.hostile:
                fill, edge, dot = (72, 22, 39), (235, 48 + pulse, 72), (255, 117, 117)
            else:
                fill, edge, dot = (74, 39, 19), (255, 168 + pulse, 74), (255, 230, 150)
            hx = int(hazard.x - camera_x)
            hy = int(hazard.y - camera_y)
            pygame.draw.ellipse(surface, fill, (hx - hazard.radius, hy - hazard.radius // 2, hazard.radius * 2, hazard.radius))
            pygame.draw.ellipse(surface, edge, (hx - hazard.radius + 3, hy - hazard.radius // 2 + 2, hazard.radius * 2 - 6, hazard.radius - 4), 1)
            pygame.draw.circle(surface, dot, (hx, hy - 2), 2)
        for orb in game.orbs:
            ox = int(orb.x - camera_x)
            oy = int(orb.y - camera_y)
            pygame.draw.rect(surface, (116, 246, 183), (ox - 2, oy - 2, 5, 5))
            surface.set_at((ox, oy - 3), (218, 255, 219))
        for shot in game.projectiles:
            sx = int(shot.x - camera_x)
            sy = int(shot.y - camera_y)
            if shot.hostile:
                pygame.draw.circle(surface, (193, 29, 66), (sx, sy), 6)
                pygame.draw.circle(surface, (255, 89, 110), (sx, sy), 4)
                pygame.draw.circle(surface, (255, 222, 214), (sx - 1, sy - 1), 2)
            elif shot.kind == "fire":
                pygame.draw.circle(surface, (248, 103, 66), (sx, sy), 4)
                pygame.draw.rect(surface, (255, 224, 135), (sx - 1, sy - 2, 3, 3))
            else:
                pygame.draw.line(surface, (191, 216, 255), (sx, sy),
                                 (int(sx - shot.vx * 0.055), int(sy - shot.vy * 0.055)), 2)
                surface.set_at((sx, sy), (255, 248, 200))
        for x, y, radius, life in game.slashes:
            col = (255, 143, 79) if game.selected_character == "female" and radius > 20 else (133, 215, 247) if radius > 30 else (249, 232, 174)
            pygame.draw.circle(surface, col, (int(x - camera_x), int(y - camera_y)), int(radius * max(0.2, life / 0.22)), 1)
        for enemy in game.enemies:
            self.enemy(surface, enemy, game.time, camera_x, camera_y)
        for x1, y1, x2, y2, _life in game.bolts:
            bx1, by1 = int(x1 - camera_x), int(y1 - camera_y)
            bx2, by2 = int(x2 - camera_x), int(y2 - camera_y)
            pygame.draw.line(surface, (70, 140, 255), (bx1, by1), (bx2, by2), 4)
            pygame.draw.line(surface, (225, 248, 255), (bx1, by1), (bx2, by2), 1)
            pygame.draw.circle(surface, (235, 250, 255), (bx2, by2), 2)
        p = game.player
        cx, cy = WIDTH // 2, HEIGHT // 2
        for i in range(p.talisman_level):
            if i >= 8:
                break
            a = game.time * 2.3 + math.tau * i / min(8, p.talisman_level)
            x, y = int(cx + math.cos(a) * 21), int(cy + math.sin(a) * 14)
            pygame.draw.rect(surface, (244, 184, 92), (x - 2, y - 3, 5, 7))
            pygame.draw.rect(surface, (255, 232, 157), (x - 1, y - 2, 2, 4))
        if not (p.invulnerable > 0 and int(p.invulnerable * 18) % 2):
            self.player_sprite(surface, p, game.selected_character, game.time)

    def player_sprite(self, surface: pygame.Surface, player, character: str, time: float) -> None:
        x, y = WIDTH // 2, HEIGHT // 2
        frames = self.player_art[character][player.facing]
        frame = int(time * 10) % len(frames) if player.moving else 0
        sprite = frames[frame]
        pygame.draw.ellipse(surface, (10, 16, 26), (x - 15, y + 23, 30, 6))
        pygame.draw.circle(surface, (103, 166, 196), (x, y + 2), 17, 1)
        bob = round(math.sin(time * (12 if player.moving else 2)) * (1 if player.moving else 0.5))
        surface.blit(sprite, sprite.get_rect(center=(x, y + bob)))

    def enemy(self, surface: pygame.Surface, enemy, time: float,
              camera_x: float = 0.0, camera_y: float = 0.0) -> None:
        x, y, r = int(enemy.x - camera_x), int(enemy.y - camera_y), enemy.radius
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
            pygame.draw.rect(surface, (230, 78, 96), (x - 21, y - 33, max(1, int(42 * enemy.hp / max(1, enemy.max_hp))), 3))
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
        pygame.draw.rect(surface, (11, 17, 29), (WIDTH - 104, 7, 97, 39))
        pygame.draw.rect(surface, (57, 73, 84), (WIDTH - 104, 7, 97, 39), 1)
        label = "蛙君现世" if game.elite_spawned else "秘境历练"
        self.text(surface, label, (WIDTH - 96, 11), 8,
                  (238, 153, 153) if game.elite_spawned else (148, 185, 182))
        if game.elite_spawned:
            timer = self.time_text(max(0.0, game.time - RUN_LENGTH))
            timer_color = (238, 153, 153)
        else:
            timer = self.time_text(max(0.0, RUN_LENGTH - game.time))
            timer_color = (239, 224, 180)
        self.text(surface, timer, (WIDTH - 13, 20), 15, timer_color, "topright")
        boss = next((enemy for enemy in game.enemies if enemy.elite), None)
        if boss:
            bx, by, bw = (WIDTH - 184) // 2, 52, 184
            pygame.draw.rect(surface, (11, 16, 27), (bx, by, bw, 20))
            pygame.draw.rect(surface, (116, 76, 100), (bx, by, bw, 20), 1)
            self.text(surface, "秘境首领 · 毒沼蛙君", (bx + 5, by + 3), 8, (229, 190, 203))
            hp = max(0, min(1, boss.hp / max(1, boss.max_hp)))
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
            attack_hint = "火球爆燃  ·  范围伤害" if game.selected_character == "female" else "灵剑瞄准  ·  高速单体"
            self.text(surface, f"WASD 移动  ·  {attack_hint}  ·  P 暂停", (WIDTH // 2, 49), 9, (206, 218, 209), "midtop")

    def veil(self, surface: pygame.Surface) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 8, 16, 190))
        surface.blit(shade, (0, 0))

    def panel(self, surface: pygame.Surface, title: str, subtitle: str, info: str,
              button: str, accent: tuple[int, int, int]) -> None:
        self.veil(surface)
        pygame.draw.rect(surface, (19, 27, 41), PANEL)
        pygame.draw.rect(surface, (73, 85, 96), PANEL, 1)
        pygame.draw.rect(surface, accent, (PANEL.x + 1, PANEL.y + 1, PANEL.w - 2, 2))
        self.text(surface, "✦", (WIDTH // 2, 69), 12, accent, "midtop")
        self.text(surface, title, (WIDTH // 2, 84), 23, accent, "midtop")
        self.text(surface, subtitle, (WIDTH // 2, 119), 10, (206, 214, 222), "midtop")
        self.text(surface, info, (WIDTH // 2, 139), 9, (165, 178, 190), "midtop")
        self.button(surface, button, PANEL_BUTTON.x, PANEL_BUTTON.y, PANEL_BUTTON.w, PANEL_BUTTON.h, accent)
        self.text(surface, "Enter 确认", (WIDTH // 2, 201), 8, (136, 150, 163), "midtop")

    def button(self, surface: pygame.Surface, label: str, x: int, y: int,
               w: int, h: int, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(surface, (19, 27, 40), (x, y, w, h))
        pygame.draw.rect(surface, (46, 58, 71), (x + 2, y + 2, w - 4, h - 4))
        pygame.draw.rect(surface, color, (x, y, w, h), 1)
        self.text(surface, label, (x + w // 2, y + h // 2), 11, color, "center")

    def menu(self, surface: pygame.Surface, game: Game) -> None:
        self.veil(surface)
        pygame.draw.rect(surface, (12, 20, 32), MENU_PANEL)
        pygame.draw.rect(surface, (74, 91, 99), MENU_PANEL, 1)
        pygame.draw.rect(surface, (180, 164, 119), (MENU_PANEL.x + 1, MENU_PANEL.y + 1, MENU_PANEL.w - 2, 2))
        self.text(surface, "秘 境 求 生", (WIDTH // 2, 18), 23, (233, 218, 171), "midtop")
        self.text(surface, "择一位修行者，开启你的仙途", (WIDTH // 2, 49), 9, (168, 201, 193), "midtop")

        choices = [
            ("male", "云归", "男修"),
            ("female", "洛璃", "女修"),
        ]
        for key, name, subtitle in choices:
            card = CHARACTER_CARDS[key]
            selected = key == game.selected_character
            border = (235, 210, 148) if selected else (79, 93, 105)
            pygame.draw.rect(surface, (24, 35, 51), card)
            pygame.draw.rect(surface, border, card, 2 if selected else 1)
            if selected:
                pygame.draw.rect(surface, (65, 67, 60), (card.x + 5, card.y + 5, card.w - 10, card.h - 10), 1)
            sprite = self.player_art[key]["down"][0]
            surface.blit(sprite, sprite.get_rect(center=(card.centerx, card.y + 43)))
            self.text(surface, f"{name}  ·  {subtitle}", (card.centerx, card.y + 78), 9,
                      (240, 220, 173) if selected else (182, 195, 199), "midtop")
            attack = "灵剑：高速单体" if key == "male" else "火球：爆燃范围"
            self.text(surface, attack, (card.centerx, card.y + 92), 7,
                      (157, 204, 224) if key == "male" else (246, 169, 119), "midtop")

        self.button(surface, "踏入秘境", START_BUTTON.x, START_BUTTON.y, START_BUTTON.w, START_BUTTON.h, (230, 207, 145))
        self.text(surface, "点击角色选择 · ← → 切换 · Enter 开始", (WIDTH // 2, 225), 8,
                  (148, 165, 172), "midtop")
        self.text(surface, "WASD 移动 · 自动施法 · 八分钟后迎战妖王", (WIDTH // 2, 240), 8,
                  (134, 151, 164), "midtop")

    def upgrade(self, surface: pygame.Surface, game: Game) -> None:
        self.veil(surface)
        self.text(surface, "灵台顿悟", (WIDTH // 2, 30), 22, (231, 214, 165), "midtop")
        self.text(surface, "选择一门功法，继续你的修行", (WIDTH // 2, 58), 10, (179, 194, 198), "midtop")
        accents = [(133, 199, 222), (215, 174, 119), (179, 158, 215)]
        for i, key in enumerate(game.upgrades[:len(UPGRADE_CARDS)]):
            card = UPGRADE_CARDS[i]
            pygame.draw.rect(surface, (15, 23, 37), card)
            pygame.draw.rect(surface, (72, 82, 94), card, 1)
            pygame.draw.rect(surface, accents[i], (card.x + 1, card.y + 1, card.w - 2, 2))
            self.text(surface, f"{i + 1}  ·  功法", (card.x + 10, card.y + 12), 8, accents[i])
            if key in EVOLUTIONS:
                title, desc = EVOLUTIONS[key]
            else:
                title, desc = UPGRADES[key][:2]
            if key == "sword":
                title = "控火诀" if game.selected_character == "female" else "御剑术"
                desc = "火球伤害提高" if game.selected_character == "female" else "灵剑伤害提高"
            self.text(surface, title, (card.centerx, card.y + 40), 12, (232, 229, 213), "midtop")
            for row, line in enumerate([desc[start:start + 13] for start in range(0, len(desc), 13)][:2]):
                self.text(surface, line, (card.centerx, card.y + 67 + row * 12), 8, (165, 181, 188), "midtop")
            self.button(surface, f"按 {i + 1} 选择", card.x + 16, card.y + 102, 96, 22, accents[i])
        self.text(surface, "点击卡牌或按数字键", (WIDTH // 2, 235), 8, (139, 154, 164), "midtop")
