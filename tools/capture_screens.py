"""Render deterministic README screenshots without opening a window."""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from game import Enemy, Game, Hazard, Orb, Projectile, RUN_LENGTH
from renderer import Renderer

OUT = ROOT / "docs" / "screenshots"
CANVAS = (480, 270)
OUTPUT = (1280, 720)


def save(game: Game, renderer: Renderer, name: str) -> None:
    canvas = pygame.Surface(CANVAS)
    renderer.begin_text_layer()
    renderer.draw(canvas, game)
    image = pygame.transform.scale(canvas, OUTPUT)
    renderer.flush_text(image, (0, 0), OUTPUT[0] / CANVAS[0])
    pygame.image.save(image, str(OUT / name))


def main() -> None:
    random.seed(7)
    pygame.init()
    pygame.display.set_mode((1, 1))
    renderer = Renderer()
    OUT.mkdir(parents=True, exist_ok=True)

    menu = Game()
    save(menu, renderer, "menu.png")

    gameplay = Game()
    gameplay.start()
    gameplay.time = 300.0
    gameplay.kills = 27
    gameplay.player.hp = 68
    gameplay.player.level = 4
    gameplay.player.xp = 10
    gameplay.player.next_xp = 34
    gameplay.player.x, gameplay.player.y = 240, 150
    gameplay.enemies = [
        Enemy(110, 80, "raven", 26, 0, 10, 8, (102, 116, 141), attack_cooldown=1.2),
        Enemy(150, 200, "raven", 28, 0, 10, 8, (102, 116, 141), attack_cooldown=0.8),
        Enemy(330, 110, "wolf", 42, 0, 14, 10, (154, 112, 86), attack_cooldown=1.0),
        Enemy(370, 210, "wolf", 45, 0, 14, 10, (154, 112, 86), attack_cooldown=1.4),
    ]
    gameplay.orbs = [Orb(260, 120), Orb(215, 185), Orb(305, 92)]
    gameplay.projectiles = [Projectile(180, 120, 205, 0, 12, 1.8, "sword")]
    gameplay.bolts = [(240, 150, 330, 110, 0.12)]
    save(gameplay, renderer, "gameplay.png")

    upgrade = Game()
    upgrade.start()
    upgrade.time = 90.0
    upgrade.state = "upgrade"
    upgrade.upgrades = ["chain", "sword_evo", "guard"]
    save(upgrade, renderer, "upgrade.png")

    boss = Game()
    boss.selected_character = "female"
    boss.start()
    boss.time = RUN_LENGTH + 12
    boss.player.hp = 74
    boss.player.level = 7
    boss.player.fire_evolution = True
    boss.elite_spawned = True
    boss.spawn_enemy(elite=True)
    boss.enemies.extend([
        Enemy(90, 90, "raven", 40, 0, 10, 8, (102, 116, 141)),
        Enemy(380, 200, "raven", 40, 0, 10, 8, (102, 116, 141)),
        Enemy(200, 230, "wolf", 55, 0, 14, 10, (154, 112, 86)),
    ])
    boss.player.x, boss.player.y = 240, 140
    boss_boss = next(enemy for enemy in boss.enemies if enemy.elite)
    boss_boss.x, boss_boss.y = 340, 200
    boss.hazards = [
        Hazard(270, 180, 19, 4.5),
        Hazard(210, 190, 19, 3.0),
        Hazard(300, 150, 25, 3.0, hostile=False),
    ]
    boss.projectiles = [Projectile(260, 160, -76, 76, 13, 2.6, "poison", True)]
    save(boss, renderer, "boss.png")

    pygame.quit()
    print(f"Wrote screenshots to {OUT}")


if __name__ == "__main__":
    main()
