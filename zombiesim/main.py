'''
Created on Nov 29, 2014

@author: btbuxton
'''

import pygame

from zombiesim.event import EventLookup
from zombiesim.field import Field
import zombiesim.util as zutil


class Done(Exception):
    @classmethod
    def raise_it(cls):
        raise cls()


def main():
    pygame.init()
    fps = 60
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h

    pygame.display.set_mode((screen_width, screen_height), pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Zombie Simulation")

    events = EventLookup()
    events.add(pygame.QUIT, lambda _: Done.raise_it())

    def set_screen(event):
        pygame.display.set_mode(event.dict['size'], pygame.DOUBLEBUF | pygame.RESIZABLE)

    events.add(pygame.VIDEORESIZE, set_screen)
    events.add_key_press(pygame.K_ESCAPE, events.func_for(pygame.QUIT))
    events.add_key_press(pygame.K_f, lambda _: zutil.make_full_screen())

    max_w = 1440
    ratio = float(screen_width) / max_w
    start_zombies = int(ratio * 5)
    start_humans = int(ratio * 250)
    max_food = max(1, int(ratio * 2))
    field = Field(start_zombies=start_zombies, start_humans=start_humans, max_food=max_food)
    field.register_events(events)
    field.start(pygame.display.get_surface().get_rect())

    clock = pygame.time.Clock()
    try:
        while True:
            events.process_events()
            screen = pygame.display.get_surface()
            field.update(screen)

            screen.fill(pygame.Color('black'))
            field.draw(screen)
            pygame.display.flip()

            clock.tick(fps)
    except Done:
        pass
    pygame.quit()


if __name__ == '__main__':
    main()
