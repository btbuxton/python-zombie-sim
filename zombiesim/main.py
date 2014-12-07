'''
Created on Nov 29, 2014

@author: btbuxton
'''
import pygame
import zombiesim.util as zutil
import zombiesim.colors as zcolors
from zombiesim.event import EventLookup
from zombiesim.field import Field


def main():
    pygame.init()
    fps = 60
    display_info = pygame.display.Info()
    screen_width = int(display_info.current_w * 0.75)
    screen_height = int(display_info.current_h * 0.75)
    
    pygame.display.set_mode((screen_width, screen_height), pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Zombie Simulation")

    events = EventLookup()
    def mark_done(event):
        main.done = True
    main.done = False
    events.add(pygame.QUIT, mark_done)
    def set_screen(event):
        pygame.display.set_mode(event.dict['size'], pygame.DOUBLEBUF | pygame.RESIZABLE)
    events.add(pygame.VIDEORESIZE, set_screen)
    events.add_key_press(pygame.K_ESCAPE, events.func_for(pygame.QUIT))
    events.add_key_press(pygame.K_f, lambda _: zutil.make_full_screen())
    
    field = Field()
    field.register_events(events)
    field.start(pygame.display.get_surface().get_rect())
    
    clock = pygame.time.Clock()
    while not main.done:
        events.process_events()
        screen = pygame.display.get_surface()
        field.update(screen)
        
        screen.fill(zcolors.BLACK)
        field.draw(screen)
        pygame.display.flip()
        
        clock.tick(fps)
    pygame.quit()
    
if __name__ == '__main__':
    main()