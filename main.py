"""修仙幸存者 — Pygame entry point."""

import pygame

from game import Game
from renderer import Renderer

LOGICAL_SIZE = (480, 270)
WINDOW_SIZE = (1280, 720)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("修仙幸存者")
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    canvas = pygame.Surface(LOGICAL_SIZE)
    clock = pygame.time.Clock()
    game = Game()
    renderer = Renderer()
    fullscreen = False
    windowed_size = WINDOW_SIZE
    scaled_canvas = None
    scaled_size = None
    running = True

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        size = screen.get_size()
        # Fit the 16:9 pixel-art canvas to the available window. Nearest-neighbor
        # scaling keeps the original pixel edges crisp at both integer and
        # fractional display scales.
        scale = min(size[0] / LOGICAL_SIZE[0], size[1] / LOGICAL_SIZE[1])
        view_size = (max(1, round(LOGICAL_SIZE[0] * scale)), max(1, round(LOGICAL_SIZE[1] * scale)))
        origin = ((size[0] - view_size[0]) // 2, (size[1] - view_size[1]) // 2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                windowed_size = event.size
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.WINDOWFOCUSLOST and game.state == "playing":
                game.state = "paused"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                else:
                    game.on_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if origin[0] <= mx < origin[0] + view_size[0] and origin[1] <= my < origin[1] + view_size[1]:
                    logical = ((mx - origin[0]) * LOGICAL_SIZE[0] / view_size[0],
                               (my - origin[1]) * LOGICAL_SIZE[1] / view_size[1])
                    game.on_click(logical)

        keys = pygame.key.get_pressed()
        game.update(dt, keys)
        renderer.begin_text_layer()
        renderer.draw(canvas, game)

        screen.fill((8, 11, 22))
        if scaled_canvas is None or scaled_size != view_size:
            scaled_size = view_size
            scaled_canvas = pygame.Surface(view_size).convert()
        pygame.transform.scale(canvas, view_size, scaled_canvas)
        screen.blit(scaled_canvas, origin)
        renderer.flush_text(screen, origin, scale)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
