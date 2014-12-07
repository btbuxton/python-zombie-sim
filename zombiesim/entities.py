'''
Created on Dec 7, 2014

@author: bbuxton
'''
import pygame
import random
import sys
import zombiesim.util as zutil
import zombiesim.colors as zcolors

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
            dist = zutil.distance(pos, each.rect.center)
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
    
    def __init__(self, color=zcolors.WHITE):
        pygame.sprite.Sprite.__init__(self)
        self.create_image(color)
        
    def added_to_group(self, group):
        pass
        
    def create_image(self, color):
        width = 10
        height = 10
        self.image = pygame.Surface([width, height],flags = pygame.SRCALPHA)
        self.image.fill(zcolors.CLEAR)
        self.draw_image(color)
        self.rect = self.image.get_rect()
    
    def draw_image(self, color):
        pass
    
    def reset_pos(self):
        pass
        
class Actor(Entity):
    def __init__(self, color=zcolors.WHITE, default_speed=4.0):
        Entity.__init__(self, color)
        self.speed = default_speed
        self.change_dir()
    
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
        self.rect.x = int(round(self.x))
        self.rect.y = int(round(self.y))
        
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
        
    def change_dir(self):
        self.current_dir = zutil.random_direction()
            
    def update(self, field):
        self.update_pos(self.current_dir)
        
class Zombie(Actor):
    VISION = 250
    ATTACK_WAIT_MAX = 50
    def __init__(self):
        Actor.__init__(self, zcolors.RED, 2.0)
        self.attack_wait = random.randint(self.ATTACK_WAIT_MAX / 2,self.ATTACK_WAIT_MAX)
        self.aimless = 0
        
    def update(self, field):
        if self.aimless > 0:
            self.aimless = self.aimless - 1
            Actor.update(self,field)
            return
        if self.attack_wait > 0:
            self.attack_wait = self.attack_wait - 1
            return
        if not field.killzone.contains(self):
            x = random.randint(field.killzone.left, field.killzone.right)
            y = random.randint(field.killzone.top, field.killzone.bottom)
            self.current_dir = zutil.dir_to(self.rect.center, (x,y))
            #self.current_dir = dir_to(self.rect.center, field.killzone.center)
            Actor.update(self,field)
            self.aimless = Zombie.VISION
            self.attack_wait = self.ATTACK_WAIT_MAX
            return
        victim,dist = field.humans.closest_to(self) #, field.killzone.contains)
        do_change = lambda: None
        if victim is not None and dist < self.VISION:
            direc = zutil.dir_to(self.rect.center, victim.rect.center)
            if  not field.rect.contains(victim):
                direc = zutil.opposite_dir(direc)
            self.current_dir = direc
            do_change = self.change_dir
        Actor.update(self,field)
        do_change() #this is so zombie changes directions when there is no longer a human
            
class Human(Actor):
    VISION = 100
    def __init__(self):
        Actor.__init__(self, zcolors.PINK)
        self.reset_lifetime()
        self.freeze = 0
        
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
        self.lifetime = zutil.xfrange(2 + (random.random() * 2),0,-0.0005)
        
    def alpha(self):
        result = self.speed / 2.0
        return min(result, 1)
        
    def update(self, field):
        #if self.freeze > 0:
        #    self.freeze = self.freeze - 1
        #    return
        self.speed = next(self.lifetime, 0)
        if self.is_dead():
            self.kill()
            field.turn(self)
            return
        self.draw_image(map(lambda x: int(x * self.alpha()), zcolors.PINK))
        goto = self.rect.center
        goto = self.run_from_zombies(field, goto)
        goto = self.run_to_food(field, goto)
        goto = (goto[0] + (1 * self.current_dir[0]), goto[1] + (1 * self.current_dir[1]))
        go_to_dir = zutil.dir_to(self.rect.center, goto)
        self.current_dir = go_to_dir
        Actor.update(self,field)
        
    def run_from_zombies(self, field, goto):
        for zombie in field.zombies.sprites():
            dist = zutil.distance(self.rect.center, zombie.rect.center)
            if dist >= self.VISION:
                continue
            factor_dist = float(self.VISION - dist)
            direc = zutil.opposite_dir(zutil.dir_to(self.rect.center, zombie.rect.center))
            goto_x, goto_y = goto
            dir_x, dir_y = direc
            goto = (goto_x + (factor_dist * dir_x), goto_y + (factor_dist * dir_y))
        return goto
    
    def run_to_food(self, field, goto):
        if self.is_hungry():
            food, _ = field.food.closest_to(self)
            if food is not None:
                direc = zutil.dir_to(self.rect.center, food.rect.center)
                goto_x, goto_y = goto
                dir_x, dir_y = direc
                factor = float(self.speed) / 4 * self.VISION
                goto = (goto_x + (factor * dir_x), goto_y + (factor * dir_y))
        return  goto
        
    def hit_edge(self, parent_rect):
        if self.rect.left < parent_rect.left:
            self.rect.left = parent_rect.left
        if self.rect.right > parent_rect.right:
            self.rect.right = parent_rect.right
        if self.rect.top < parent_rect.top:
            self.rect.top = parent_rect.top
        if self.rect.bottom > parent_rect.bottom:
            self.rect.bottom = parent_rect.bottom
        self.reset_pos()
        #Actor.hit_edge(self, parent_rect)
        #self.current_dir = dir_to(self.rect.center, parent_rect.center)
        self.current_dir = zutil.opposite_dir(self.current_dir)
        self.freeze = 50
        #x = random.randint(parent_rect.left, parent_rect.right)
        #y = random.randint(parent_rect.top, parent_rect.bottom)
        #self.current_dir = dir_to(self.rect.center, (x,y))
        #self.current_dir = (0,0)

class Consumable(Entity):
    def __init__(self, color=zcolors.GREEN, amount=5):
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
        Consumable.__init__(self, zcolors.GREEN, amount=50)