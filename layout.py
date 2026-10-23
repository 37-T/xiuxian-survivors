"""Shared UI layout, used by both drawing and hit-testing."""

from __future__ import annotations

import pygame

MENU_PANEL = pygame.Rect(36, 10, 408, 250)

CHARACTER_CARDS = {
    "male": pygame.Rect(92, 73, 136, 108),
    "female": pygame.Rect(252, 73, 136, 108),
}

START_BUTTON = pygame.Rect(166, 190, 148, 30)

PANEL = pygame.Rect(84, 56, 312, 162)
PANEL_BUTTON = pygame.Rect(164, 165, 152, 30)
PAUSE_CONTINUE_BUTTON = pygame.Rect(100, 162, 118, 28)
PAUSE_MENU_BUTTON = pygame.Rect(262, 162, 118, 28)

UPGRADE_CARDS = tuple(pygame.Rect(42 + 136 * index, 88, 128, 132) for index in range(3))
