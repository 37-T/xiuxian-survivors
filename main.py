"""修仙幸存者 — Pygame entry point."""

import pygame

from game import Game
from renderer import Renderer


def main() -> None:
    pygame.init()
    pygame.display.set_caption("修仙幸存者")
    screen = pygame.display.set_mode((960, 540), pygame.RESIZABLE)
    canvas = pygame.Surface((480, 270))
    clock = pygame.time.Clock()
    game = Game()
    renderer = Renderer()
    fullscreen = False
    running = True

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        size = screen.get_size()
        scale = max(1, min(size[0] // 480, size[1] // 270))
        view_size = (480 * scale, 270 * scale)
        origin = ((size[0] - view_size[0]) // 2, (size[1] - view_size[1]) // 2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if fullscreen else pygame.display.set_mode((960, 540), pygame.RESIZABLE)
                else:
                    game.on_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                logical = ((mx - origin[0]) / scale, (my - origin[1]) / scale)
                game.on_click(logical)

        keys = pygame.key.get_pressed()
        game.update(dt, keys)
        renderer.draw(canvas, game)

        screen.fill((8, 11, 22))
        scaled = pygame.transform.scale(canvas, view_size)
        screen.blit(scaled, origin)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
