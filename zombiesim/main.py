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

def opposite_dir(direc):
    x,y = direc
    return (float(-1) * x, float(-1) * y)
    
def random_direction():
    angle = math.radians(random.randrange(0, 360))
    return (math.cos(angle), math.sin(angle))

def xfrange(start, stop, step):
    current = start
    while ((step > 0 and current < stop) or (step < 0 and current > stop)):
        yield current
        current = current + step
    
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
    def create_group(clazz, size, rect):
        all_group = ActorGroup()
        for _ in range(size):
            actor = clazz()
            all_group.add(actor)
            actor.rect.x = random.randrange(rect.x, rect.width - actor.rect.width)
            actor.rect.y = random.randrange(rect.y, rect.height - actor.rect.height)
        return all_group
    
    def __init__(self, color=WHITE, default_speed=4.0):
        pygame.sprite.Sprite.__init__(self)
        self.create_image(color)
        self.speed = default_speed
        
    def create_image(self, color):
        width = 10
        height = 10
        self.image = pygame.Surface([width, height],flags = pygame.SRCALPHA)
        self.image.fill(CLEAR)
        pygame.draw.ellipse(self.image, color, self.image.get_rect())
        self.rect = self.image.get_rect()
        
    def update_pos(self, direc):
        dirx,diry = direc
        self.rect.x = round(self.rect.x + (dirx * self.speed))
        self.rect.y = round(self.rect.y + (diry * self.speed))
        
    def hit_edge(self, parent_rect):
        if self.rect.left < parent_rect.left:
            self.rect.right = parent_rect.right
        if self.rect.right > parent_rect.right:
            self.rect.left = parent_rect.left
        if self.rect.top < parent_rect.top:
            self.rect.bottom = parent_rect.bottom
        if self.rect.bottom > parent_rect.bottom:
            self.rect.top = parent_rect.top
            
    def update(self, field):
        pass
        
class Zombie(Actor):
    def __init__(self):
        Actor.__init__(self, RED)
    def update(self, field):
        victim,dist = field.humans.closest_to(self)
        if victim is not None and dist < 200:
            self.update_pos(dir_to(self.rect.center, victim.rect.center))
        else:
            self.update_pos(random_direction())
            
class Human(Actor):
    def __init__(self):
        Actor.__init__(self, PINK)
        self.current_dir = random_direction()
        self.lifetime = xfrange(2 + (random.random() * 4),0,-0.0005)
        
    def change_dir(self):
        self.current_dir = random_direction()
        
    def update(self, field):
        self.speed = next(self.lifetime, 0)
        if 0 == self.speed:
            self.kill()
            field.turn(self)
            return
        goto = self.rect.center
        factor = float(1)
        use_dir = True
        for zombie in field.zombies.sprites():
            dist = distance(self.rect.center, zombie.rect.center)
            if dist > 50:
                continue
            use_dir = False
            factor_dist = 50 - dist
            direc = opposite_dir(dir_to(self.rect.center, zombie.rect.center))
            goto_x, goto_y = goto
            dir_x, dir_y = direc
            goto = (goto_x + (factor_dist * factor * dir_x), goto_y + (factor_dist * factor * dir_y))
        
        go_to_dir = dir_to(self.rect.center, goto)
        if not use_dir:
            self.current_dir = go_to_dir
        self.update_pos(self.current_dir)
    

class Field(object):
    def __init__(self, rect):
        self.zombies = Zombie.create_group(5, rect)
        self.humans = Human.create_group(200, rect)
        
    def register_events(self, events):
        events.every_do(200, lambda: self.zombies.update(self))
        events.every_do(100, lambda: self.humans.update(self))
        
    def update(self, screen):
        for zombie in self.zombies:
            dead = pygame.sprite.spritecollide(zombie, self.humans, True, collided = pygame.sprite.collide_circle)
            for human in dead:
                self.turn(human)
        self.check_and_fix_edges(screen)
        
    def draw(self, screen):
        self.zombies.draw(screen)
        self.humans.draw(screen)
        
    def turn(self, human):
        zombie = Zombie()
        zombie.rect = human.rect
        self.zombies.add(zombie)
        
    def check_and_fix_edges(self, screen):
        def check_and_fix(actor, parent_rect):
            if not parent_rect.contains(actor.rect):
                actor.hit_edge(parent_rect)
        rect = screen.get_rect()
        for each in self.zombies.sprites():
            check_and_fix(each, rect)
        for each in self.humans.sprites():
            check_and_fix(each, rect)
        
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
    fps = 60
    screen_width = 960
    screen_height = 720
    screen = pygame.display.set_mode([screen_width, screen_height])
    pygame.display.set_caption("Zombie Simulation")
    clock = pygame.time.Clock()
    field = Field(screen.get_rect())
    events = EventLookup()
    field.register_events(events)
    def mark_done(event):
        main.done = True
    main.done = False
    events.add(pygame.QUIT, mark_done)
    while not main.done:
        events.process_events()
        field.update(screen)
        
        screen.fill(BLACK)
        field.draw(screen)
        pygame.display.flip()
        
        clock.tick(fps)
    pygame.quit()
    
if __name__ == '__main__':
    main()