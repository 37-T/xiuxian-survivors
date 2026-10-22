"""Headless regression tests for 修仙幸存者."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game import (
    BOSS_HP,
    FIRE_ZONE_DAMAGE,
    HEIGHT,
    RUN_LENGTH,
    EVOLUTIONS,
    UPGRADES,
    Enemy,
    Game,
    Hazard,
    WIDTH,
)
from layout import CHARACTER_CARDS, PANEL_BUTTON, START_BUTTON, UPGRADE_CARDS
from renderer import Renderer


class FakeKeys:
    def __init__(self, *pressed: int) -> None:
        self.pressed = set(pressed)

    def __getitem__(self, key: int) -> bool:
        return key in self.pressed


class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        pygame.display.set_mode((WIDTH, HEIGHT))
        cls.renderer = Renderer()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    @staticmethod
    def surface() -> pygame.Surface:
        return pygame.Surface((WIDTH, HEIGHT))

    def test_renders_every_upgrade_and_evolution(self) -> None:
        for key in (*UPGRADES, *EVOLUTIONS):
            with self.subTest(key=key):
                game = Game()
                game.start()
                game.state = "upgrade"
                game.upgrades = [key, "spirit", "guard"]
                self.renderer.draw(self.surface(), game)

    def test_fire_zone_damages_enemies_not_player(self) -> None:
        game = Game()
        game.start()
        game.spawn_timer = 999
        game.player.cooldown = 999
        game.player.hp = game.player.max_hp = 100
        game.player.x, game.player.y = 240, 135
        wolf = Enemy(200, 135, "wolf", 100, 0, 0, 10, (0, 0, 0))
        game.enemies = [wolf]
        game.hazards = [Hazard(200, 135, 25, 3.0, hostile=False)]
        for _ in range(60):
            game.update(1 / 60, FakeKeys())
        self.assertLessEqual(wolf.hp, 100 - FIRE_ZONE_DAMAGE)
        self.assertEqual(game.player.hp, 100)

        game = Game()
        game.start()
        game.spawn_timer = 999
        game.player.cooldown = 999
        game.player.hp = game.player.max_hp = 100
        game.player.x, game.player.y = 240, 135
        game.enemies = []
        game.hazards = [Hazard(240, 135, 25, 3.0, hostile=False)]
        for _ in range(60):
            game.update(1 / 60, FakeKeys())
        self.assertEqual(game.player.hp, 100)

    def test_hazard_ellipse_contains(self) -> None:
        hazard = Hazard(100, 100, 19, 3.0)
        self.assertTrue(hazard.contains(100, 104))
        self.assertFalse(hazard.contains(100, 111))
        self.assertFalse(hazard.contains(120, 100))

    def test_player_moves_freely_on_infinite_map(self) -> None:
        game = Game()
        game.start()
        game.spawn_timer = 999
        game.enemies = []
        right = FakeKeys(pygame.K_d)
        for _ in range(600):
            game.update(1 / 60, right)
        self.assertGreater(game.player.x, WIDTH)

        up = FakeKeys(pygame.K_w)
        for _ in range(1200):
            game.update(1 / 60, up)
        self.assertLess(game.player.y, 0)

    def test_world_renders_far_from_origin(self) -> None:
        game = Game()
        game.start()
        game.player.x, game.player.y = 10000, -5000
        game.enemies = [Enemy(10040, -5000, "wolf", 50, 0, 10, 10, (0, 0, 0))]
        self.renderer.draw(self.surface(), game)

    def test_pause_enter_resumes(self) -> None:
        game = Game()
        game.start()
        game.on_key(pygame.K_p)
        self.assertEqual(game.state, "paused")
        game.on_key(pygame.K_RETURN)
        self.assertEqual(game.state, "playing")

    def test_boss_spawns_with_max_hp_and_winning_blocks_damage(self) -> None:
        game = Game()
        game.start()
        game.time = RUN_LENGTH
        game.update(1 / 60, FakeKeys())
        boss = next(enemy for enemy in game.enemies if enemy.elite)
        self.assertEqual(boss.max_hp, BOSS_HP)
        hp_before = game.player.hp
        game.damage_enemy(boss, BOSS_HP * 2)
        self.assertEqual(game.state, "won")
        game.hit_player(100)
        self.assertEqual(game.state, "won")
        self.assertEqual(game.player.hp, hp_before)

    def test_click_targets_match_layout(self) -> None:
        game = Game()
        game.on_click(CHARACTER_CARDS["female"].center)
        self.assertEqual(game.selected_character, "female")
        game.on_click(START_BUTTON.center)
        self.assertEqual(game.state, "playing")

        game.state = "upgrade"
        game.upgrades = ["sword", "guard", "talisman"]
        game.on_click(UPGRADE_CARDS[1].center)
        self.assertEqual(game.player.guard_level, 1)
        self.assertEqual(game.state, "playing")

        game.state = "paused"
        game.on_click(PANEL_BUTTON.center)
        self.assertEqual(game.state, "playing")

        game.state = "won"
        game.on_click(PANEL_BUTTON.center)
        self.assertEqual(game.state, "playing")

    def test_evolution_is_not_offered_again(self) -> None:
        game = Game()
        game.selected_character = "female"
        game.start()
        game.player.sword_level = 5
        game.player.fire_evolution = True
        for _ in range(100):
            self.assertNotIn("fire_evo", game.make_upgrade_choices())

        game = Game()
        game.start()
        game.player.sword_level = 5
        game.player.sword_evolution = True
        for _ in range(100):
            self.assertNotIn("sword_evo", game.make_upgrade_choices())

    def test_chain_lightning_is_second_attack(self) -> None:
        game = Game()
        game.start()
        game.spawn_timer = 999
        game.player.cooldown = 999
        game.player.chain_level = 1
        game.player.x, game.player.y = 240, 135
        first = Enemy(200, 135, "wolf", 100, 0, 0, 10, (0, 0, 0))
        second = Enemy(170, 135, "wolf", 100, 0, 0, 10, (0, 0, 0))
        game.enemies = [first, second]
        game.update(1 / 60, FakeKeys())
        self.assertLess(first.hp, 100)
        self.assertLess(second.hp, 100)
        self.assertTrue(game.bolts)

    def test_raven_does_not_fire_projectiles(self) -> None:
        game = Game()
        game.start()
        game.spawn_timer = 999
        game.player.cooldown = 999
        game.player.x, game.player.y = 240, 135
        game.enemies = [Enemy(100, 135, "raven", 50, 40, 10, 8, (0, 0, 0))]
        for _ in range(120):
            game.update(1 / 60, FakeKeys())
        self.assertFalse(any(shot.hostile for shot in game.projectiles))

    def test_high_res_text_overlay(self) -> None:
        game = Game()
        target = pygame.Surface((1280, 720))
        self.renderer.begin_text_layer()
        self.renderer.draw(pygame.Surface((WIDTH, HEIGHT)), game)
        self.renderer.flush_text(target, (0, 0), 1280 / WIDTH)


if __name__ == "__main__":
    unittest.main()
