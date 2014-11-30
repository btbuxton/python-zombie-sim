'''
Created on Nov 29, 2014

@author: btbuxton
'''
import pygame
import random
import math
import sys

CLEAR = (0,   0,   0, 0)
RED =   (255, 0,   0)
BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
PINK = (255, 192, 192)

def distance(origin, dest):
    originx,originy = origin
    destx,desty = dest
    return math.sqrt(((originy - desty) ** 2) + ((originx - destx) **2))

def dir_to(origin, dest):
    originx,originy = origin
    destx,desty = dest
    diffx, diffy = destx - originx, desty - originy
    angle = math.atan2(diffy, diffx)
    return (math.cos(angle), math.sin(angle))
    
class ActorGroup(pygame.sprite.Group):
    def closest_to(self, other):
        curmin = sys.maxint
        curactor = None
        pos = other.rect.center
        for each in self.sprites():
            dist = distance(pos, each.rect.center)
            if dist < curmin:
                curmin = dist
                curactor = each
        return (curactor, curmin)
            
class Actor(pygame.sprite.Sprite):
    @classmethod
    def create_group(clazz, size, width, height):
        all_group = ActorGroup()
        for _ in range(size):
            actor = clazz()
            all_group.add(actor)
            actor.rect.x = random.randrange(width - actor.rect.width)
            actor.rect.y = random.randrange(height - actor.rect.height)
        return all_group
    def __init__(self, color=WHITE):
        pygame.sprite.Sprite.__init__(self)
        width = 10
        height = 10
        self.image = pygame.Surface([width, height],flags = pygame.SRCALPHA)
        self.image.fill(CLEAR)
        pygame.draw.ellipse(self.image, color, self.image.get_rect())
        self.rect = self.image.get_rect()
        self.speed = 5
        
    def update_pos(self, direc):
        dirx,diry = direc
        self.rect.x = self.rect.x + (dirx * self.speed)
        self.rect.y = self.rect.y + (diry * self.speed)
        
class Zombie(Actor):
    def __init__(self):
        Actor.__init__(self, RED)
    def update(self, field):
        victim,_ = field.humans.closest_to(self)
        if victim is None:
            self.rect.x = self.rect.x + random.randint(-1,1)
            self.rect.y = self.rect.y + random.randint(-1,1)
        else:
            self.update_pos(dir_to(self.rect.center, victim.rect.center))

class Human(Actor):
    def __init__(self):
        Actor.__init__(self, PINK)
    def update(self, field):
        self.rect.x = self.rect.x + random.randint(-1,1)
        self.rect.y = self.rect.y + random.randint(-1,1)

class Field(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.zombies = Zombie.create_group(5, width, height)
        self.humans = Human.create_group(200, width, height)
    def update(self):
        #These two lines will eventually be done by clocks means
        #self.zombies.update(self)
        self.humans.update(self)
        
        for zombie in self.zombies:
            dead = pygame.sprite.spritecollide(zombie, self.humans, True, collided = pygame.sprite.collide_circle)
            for human in dead:
                self.turn(human)
    def draw(self, screen):
        self.zombies.draw(screen)
        self.humans.draw(screen)
    def turn(self, human):
        zombie = Zombie()
        zombie.rect = human.rect
        self.zombies.add(zombie)
    def register_events(self, events):
        events.every_do(250, lambda: self.zombies.update(self))

class EventLookup(object):
    def __init__(self):
        self.__mapping__= {}
        self.next_event_id = pygame.USEREVENT
    def add(self, event_type, func=lambda event: None):
        self.__mapping__[event_type] = func
    def next_event_type(self):
        self.next_event_id = self.next_event_id + 1
        return self.next_event_id
    def every_do(self, millis, func=lambda: None):
        event_id = self.next_event_type()
        pygame.time.set_timer(event_id, millis)
        self.add(event_id,lambda _: func())
    def process_events(self):
        for event in pygame.event.get():
            self.__mapping__.get(event.type, lambda event: None)(event)

def main():
    pygame.init()
    screen_width = 960
    screen_height = 720
    screen = pygame.display.set_mode([screen_width, screen_height])
    pygame.display.set_caption("Zombie Simulation")
    clock = pygame.time.Clock()
    field = Field(screen_width, screen_height)
    events = EventLookup()
    field.register_events(events)
    def mark_done(event):
        main.done = True
    main.done = False
    events.add(pygame.QUIT, mark_done)
    while not main.done:
        events.process_events()
        field.update()
        screen.fill(BLACK)
        field.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    
if __name__ == '__main__':
    main()