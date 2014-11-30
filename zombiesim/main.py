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
        
class Zombie(Actor):
    def __init__(self):
        Actor.__init__(self, RED)
    def update(self, field):
        victim,_ = field.humans.closest_to(self)
        if victim is None:
            self.rect.x = self.rect.x + random.randint(-1,1)
            self.rect.y = self.rect.y + random.randint(-1,1)
        else:
            dirx,diry = dir_to(self.rect.center, victim.rect.center)
            self.rect.x = self.rect.x + (dirx * 5)
            self.rect.y = self.rect.y + (diry * 5)

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
        self.zombies.update(self)
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

def main():
    pygame.init()
    screen_width = 960
    screen_height = 720
    screen = pygame.display.set_mode([screen_width, screen_height])
    pygame.display.set_caption("Zombie Simulation")
    field = Field(screen_width, screen_height)
    done = False
    clock = pygame.time.Clock()
    while not done:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                done = True
        field.update()
        screen.fill(BLACK)
        field.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    
if __name__ == '__main__':
    main()