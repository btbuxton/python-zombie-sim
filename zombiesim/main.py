"""
Created on Nov 29, 2014

@author: btbuxton
"""

import pygame

from zombiesim.event import EventLookup
from zombiesim.field import INITIAL_HUMANS, INITIAL_ZOMBIES, MAX_FOOD, field_creator
import zombiesim.util as zutil


class Done(Exception):
    @classmethod
    def raise_it(cls):
        raise cls()


def main() -> None:
    pygame.init()
    fps = 60
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h

    pygame.display.set_mode(
        (screen_width, screen_height), pygame.DOUBLEBUF | pygame.RESIZABLE
    )
    pygame.display.set_caption("Zombie Simulation")

    events = EventLookup()

    def callback(_) -> None:
        raise Done()

    events.add(pygame.QUIT, callback)

    def set_screen(event):
        pygame.display.set_mode(event.dict["size"], pygame.DOUBLEBUF | pygame.RESIZABLE)

    events.add(pygame.VIDEORESIZE, set_screen)
    events.add_key_press(pygame.K_ESCAPE, events.func_for(pygame.QUIT))
    events.add_key_press(pygame.K_f, lambda _: zutil.make_full_screen())

    max_w = 1440
    ratio = float(screen_width) / max_w
    start_zombies = int(ratio * INITIAL_ZOMBIES)
    start_humans = int(ratio * INITIAL_HUMANS)
    max_food = max(1, int(ratio * MAX_FOOD))
    field_factory = field_creator(
        start_zombies=start_zombies, start_humans=start_humans, max_food=max_food
    )
    field = field_factory(pygame.display.get_surface().get_rect())
    field.start(events)

    def restart() -> None:
        nonlocal field
        field.stop(events)
        field = field_factory(pygame.display.get_surface().get_rect())
        field.start(events)

    events.add_key_press(pygame.K_r, lambda _: restart())

    clock = pygame.time.Clock()
    try:
        while True:
            events.process_events()
            screen = pygame.display.get_surface()
            should_continue = field.update(screen)
            if not should_continue:
                restart()
                continue

            screen.fill(pygame.Color("black"))
            field.draw(screen)
            pygame.display.flip()

            clock.tick(fps)
    except Done:
        pass
    pygame.quit()


if __name__ == "__main__":
    main()
