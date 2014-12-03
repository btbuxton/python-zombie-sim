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
PINK =  (255, 192, 192)
GREEN = (0,   255,   0)

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
    negative_one = float(-1)
    return map(lambda x: x * negative_one, direc)
    
def random_direction():
    angle = math.radians(random.randrange(0, 360))
    return (math.cos(angle), math.sin(angle))

def xfrange(start, stop, step):
    current = start
    while ((step > 0 and current < stop) or (step < 0 and current > stop)):
        yield current
        current = current + step
    
class EntityGroup(pygame.sprite.Group):
    def __init__(self, clazz):
        pygame.sprite.Group.__init__(self)
        self.entity_class = clazz
    
    def create_one(self, rect):
        entity = self.entity_class()
        self.add(entity)
        entity.rect.x = random.randrange(rect.x, rect.width - entity.rect.width)
        entity.rect.y = random.randrange(rect.y, rect.height - entity.rect.height)
        entity.added_to_group(self)
        
    def closest_to(self, other, to_include=lambda entity: True):
        curmin = sys.maxint
        curactor = None
        pos = other.rect.center
        for each in self.sprites():
            if not to_include(each):
                continue
            dist = distance(pos, each.rect.center)
            if dist < curmin:
                curmin = dist
                curactor = each
        return (curactor, curmin)
    
class Entity(pygame.sprite.Sprite):
    @classmethod
    def create_group(clazz, size, rect):
        all_group = EntityGroup(clazz)
        for _ in range(size):
            all_group.create_one(rect)
        return all_group
    
    def __init__(self, color=WHITE):
        pygame.sprite.Sprite.__init__(self)
        self.create_image(color)
        
    def added_to_group(self, group):
        pass
        
    def create_image(self, color):
        width = 10
        height = 10
        self.image = pygame.Surface([width, height],flags = pygame.SRCALPHA)
        self.image.fill(CLEAR)
        self.draw_image(color)
        self.rect = self.image.get_rect()
    
    def draw_image(self, color):
        pass
        
class Actor(Entity):
    def __init__(self, color=WHITE, default_speed=4.0):
        Entity.__init__(self, color)
        self.speed = default_speed
    
    def added_to_group(self, group):
        self.reset_pos()
    
    def draw_image(self, color):
        pygame.draw.ellipse(self.image, color, self.image.get_rect())
        
    def reset_pos(self):
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
      
    def update_pos(self, direc):
        dirx,diry = direc
        self.x = self.x + (dirx * self.speed)
        self.y = self.y + (diry * self.speed)
        self.rect.x = round(self.x)
        self.rect.y = round(self.y)
        
    def hit_edge(self, parent_rect):
        if self.rect.left < parent_rect.left:
            self.rect.right = parent_rect.right
        if self.rect.right > parent_rect.right:
            self.rect.left = parent_rect.left
        if self.rect.top < parent_rect.top:
            self.rect.bottom = parent_rect.bottom
        if self.rect.bottom > parent_rect.bottom:
            self.rect.top = parent_rect.top
        self.reset_pos()
            
    def update(self, field):
        pass
        
class Zombie(Actor):
    def __init__(self):
        Actor.__init__(self, RED, 2.0)
        self.attack_wait = random.randint(25,50)
    def update(self, field):
        if self.attack_wait > 0:
            self.attack_wait = self.attack_wait - 1
            return
        victim,dist = field.humans.closest_to(self ,field.killzone().contains)
        if victim is not None and dist < 200:
            direc = dir_to(self.rect.center, victim.rect.center)
            if  not field.rect.contains(victim):
                direc = opposite_dir(direc)
            self.update_pos(direc)
        else:
            self.update_pos(random_direction())
            
class Human(Actor):
    VISION = 50
    def __init__(self):
        Actor.__init__(self, PINK)
        self.change_dir()
        self.reset_lifetime()
        
    def change_dir(self):
        self.current_dir = random_direction()
        
    def eat_food(self, food):
        if self.is_hungry():
            food.consume()
            self.reset_lifetime()
            self.change_dir()
    
    def is_hungry(self):
        return self.speed < 2.0
    
    def is_dead(self):
        return self.speed == 0
        
    def reset_lifetime(self):
        self.lifetime = xfrange(2 + (random.random() * 2),0,-0.0005)
        
    def alpha(self):
        result = self.speed / 2.0
        return min(result, 1)
        
    def update(self, field):
        self.speed = next(self.lifetime, 0)
        if self.is_dead():
            self.kill()
            field.turn(self)
            return
        self.draw_image(map(lambda x: int(x * self.alpha()), PINK))
        goto = self.rect.center
        factor = float(1)
        #use_dir = True
        for zombie in field.zombies.sprites():
            dist = distance(self.rect.center, zombie.rect.center)
            if dist > self.VISION:
                continue
            #use_dir = False
            factor_dist = self.VISION - dist
            direc = opposite_dir(dir_to(self.rect.center, zombie.rect.center))
            goto_x, goto_y = goto
            dir_x, dir_y = direc
            goto = (goto_x + (factor_dist * factor * dir_x), goto_y + (factor_dist * factor * dir_y))
        if self.is_hungry():
            food, _ = field.food.closest_to(self)
            if food is not None:
                #use_dir = False
                direc = dir_to(self.rect.center, food.rect.center)
                goto_x, goto_y = goto
                dir_x, dir_y = direc
                factor = (self.speed / 4) * self.VISION
                goto = (goto_x + (factor * dir_x), goto_y + (factor * dir_y))
        
        goto = (goto[0] + (4.0 * self.current_dir[0]), goto[1] + (4.0 * self.current_dir[1]))
        go_to_dir = dir_to(self.rect.center, goto)
        self.current_dir = go_to_dir
        self.update_pos(self.current_dir)
        
    def hit_edge(self, parent_rect):
        x = random.randint(parent_rect.left, parent_rect.right)
        y = random.randint(parent_rect.top, parent_rect.bottom)
        self.current_dir = dir_to(self.rect.center, (x,y))

class Consumable(Entity):
    def __init__(self, color=GREEN, amount=5):
        Entity.__init__(self, color)
        self.amount = amount
        
    def draw_image(self, color):
        pygame.draw.rect(self.image, color, self.image.get_rect())
    
    def consume(self):
        self.amount = self.amount - 1
        if not self.has_more():
            self.kill()
    
    def has_more(self):
        return self.amount > 0
        
class Food(Consumable):
    def __init__(self):
        Consumable.__init__(self, GREEN, amount=100)
    
class Field(object):
    MAX_FOOD = 1
    START_ZOMBIES = 5
    START_HUMANS = 250
    ZOMBIE_UPDATE_MS = 200
    HUMAN_UPDATE_MS = 100
    
    def __init__(self, rect):
        self.zombies = Zombie.create_group(self.START_ZOMBIES, rect)
        self.humans = Human.create_group(self.START_HUMANS, rect)
        self.food = Food.create_group(self.MAX_FOOD, rect)
        self.rect = rect
        
    def register_events(self, events):
        events.every_do(self.ZOMBIE_UPDATE_MS, lambda: self.zombies.update(self))
        events.every_do(self.HUMAN_UPDATE_MS, lambda: self.humans.update(self))
        
    def update(self, screen):
        self.rect = screen.get_rect()
        all_dead = []
        for zombie in self.zombies:
            dead = pygame.sprite.spritecollide(zombie, self.humans, True, collided = pygame.sprite.collide_circle)
            all_dead.extend(dead)
        for human in all_dead:
                self.turn(human)
        for food in self.food:
            eaten = pygame.sprite.spritecollide(food, self.humans, False, collided = pygame.sprite.collide_rect)
            for human in eaten:
                if food.has_more():
                    human.eat_food(food)
        self.check_and_fix_edges()
        self.check_food()
        if self.all_dead():
            self.__init__(self.rect)
    
    def all_dead(self):
        return not self.humans
    
    def check_food(self):
        while len(self.food) < self.MAX_FOOD:
            self.food.create_one(self.rect)
        
    def draw(self, screen):
        self.food.draw(screen)
        self.humans.draw(screen)
        self.zombies.draw(screen)
        
    def turn(self, human):
        zombie = Zombie()
        zombie.rect = human.rect
        self.zombies.add(zombie)
        zombie.added_to_group(self.zombies)
        
    def check_and_fix_edges(self):
        def check_and_fix(actor, parent_rect):
            if not parent_rect.contains(actor.rect):
                actor.hit_edge(parent_rect)
        for each in self.zombies.sprites():
            check_and_fix(each, self.rect)
        for each in self.humans.sprites():
            check_and_fix(each, self.rect)
            
    def killzone(self):
        return self.rect.inflate(0 - Human.VISION - 25, 0 - Human.VISION - 25)
        
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