'''
Created on Dec 7, 2014

@author: bbuxton
'''
import random
import sys
import pygame
import math

import zombiesim.util as zutil

class EntityGroup(pygame.sprite.Group):
    def __init__(self, clazz, color):
        super(self.__class__, self).__init__()
        self.entity_class = clazz
        self.color = color
    
    def create_one(self, point_getter):
        entity = self.entity_class(self.color)
        self.add(entity)
        entity.rect.center = point_getter()
        entity.added_to_group(self)
        return entity
        
    def closest_to(self, other, field, to_include=lambda entity: True):
        span = zutil.span(field.rect)
        span_mid = span / 2.0
        curmin = sys.maxint
        curactor = None
        pos = other.rect.center
        for each in self.sprites():
            if not to_include(each):
                continue
            dist = zutil.distance(pos, each.rect.center)
            if dist > span_mid:
                dist = span - dist
            if dist < curmin:
                curmin = dist
                curactor = each
        return (curactor, curmin)
    
class Entity(pygame.sprite.Sprite):
    @classmethod
    def create_group(clazz, size, color, point_getter):
        all_group = EntityGroup(clazz, color)
        for _ in range(size):
            all_group.create_one(point_getter)
        return all_group
    
    def __init__(self, color):
        super(Entity, self).__init__()
        self.color = color
        self.create_image()
        self._mouse_groups = None
        
    def added_to_group(self, group):
        pass
        
    def create_image(self):
        width = 10
        height = 10
        self.image = pygame.Surface([width, height], flags=pygame.SRCALPHA)
        self.image.fill(pygame.Color(0, 0, 0, 0))
        self.draw_image(self.color)
        self.rect = self.image.get_rect()
        self.radius = min(width, height) / 2
    
    def draw_image(self, color):
        pass
    
    def reset_pos(self):
        pass
    
    def pick_up(self, pos):
        groups = self.groups()
        self._mouse_groups = []
        for group in groups:
            group.remove(self)
            self._mouse_groups.append(group)
        self._mouse_offset = zutil.diff_points(self.rect.center, pos)
    
    def update_pick_up(self, pos):
        self.rect.center = zutil.add_points(pos, self._mouse_offset)
        self.reset_pos()
    
    def put_down(self, pos):
        self.update_pick_up(pos)
        for group in self._mouse_groups:
            group.add(self)
        del self._mouse_groups
        del self._mouse_offset
        
class Actor(Entity):
    def __init__(self, color, default_speed=4.0):
        super(Actor, self).__init__(color)
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
        dirx, diry = direc
        self.x = self.x + (dirx * self.speed)
        self.y = self.y + (diry * self.speed)
        self.rect.x = int(round(self.x))
        self.rect.y = int(round(self.y))
        
    def hit_edge(self, parent_rect):
        if self.rect.centerx < parent_rect.left:
            self.rect.right = parent_rect.right
        if self.rect.centerx > parent_rect.right:
            self.rect.left = parent_rect.left
        if self.rect.centery < parent_rect.top:
            self.rect.bottom = parent_rect.bottom
        if self.rect.centery > parent_rect.bottom:
            self.rect.top = parent_rect.top
        self.reset_pos()
        
    def change_dir(self):
        self.current_dir = zutil.random_direction()
            
    def update(self, field):
        self.update_pos(self.current_dir)
        
class Zombie(Actor):
    VISION = 150
    ATTACK_WAIT_MAX = 50
    def __init__(self, color):
        self.angle = zutil.random_angle()
        super(self.__class__, self).__init__(color, 2.0)
        self.attack_wait = random.randint(self.ATTACK_WAIT_MAX / 2, self.ATTACK_WAIT_MAX)
        
    def update(self, field):
        if self.attack_wait > 0:
            self.attack_wait = self.attack_wait - 1
            return
        goto = self.rect.center
        goto = self.run_to_humans(field, goto)
        goto = (goto[0] + (1 * self.current_dir[0]), goto[1] + (1 * self.current_dir[1]))
        victim_angle = zutil.angle_to(self.rect.center, goto)
        if victim_angle > self.angle:
            self.angle += math.radians(10)
        elif victim_angle < self.angle:
            self.angle -= math.radians(10)
        self.current_dir = zutil.angle_to_dir(self.angle)
        super(self.__class__, self).update(field)
        self.change_dir()

    def run_to_humans(self, field, goto):
        span = zutil.span(field.rect)
        span_mid = span / 2.0
        for human in field.humans.sprites():
            dist = zutil.distance(self.rect.center, human.rect.center)
            rev_dir = False
            if dist > span_mid:
                dist = span - dist
                rev_dir = True
            if dist >= self.VISION:
                continue
            factor_dist = float(self.VISION - dist)
            direc = zutil.dir_to(self.rect.center, human.rect.center)
            if rev_dir: 
                zutil.opposite_dir(direc)
            goto_x, goto_y = goto
            dir_x, dir_y = direc
            goto = (goto_x + (factor_dist * dir_x), goto_y + (factor_dist * dir_y))
        return goto
        
    def change_dir(self):
        self.angle = zutil.random_angle_change(self.angle, 10)
        self.current_dir = zutil.angle_to_dir(self.angle)
    
    #def hit_edge(self, parent_rect):
    #    super(self.__class__, self).hit_edge(parent_rect)
    #    self.aimless = 50
        
class Human(Actor):
    VISION = 100
    def __init__(self, color):
        super(self.__class__, self).__init__(color)
        self.reset_lifetime()
        #self.freeze = 0
        
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
        self.lifetime = zutil.xfrange(2 + (random.random() * 2), 0, -0.0005)
        
    def alpha(self):
        result = self.speed / 2.0
        return min(result, 1)
        
    def update(self, field):
        self.speed = next(self.lifetime, 0)
        if self.is_dead():
            self.kill()
            field.turn(self)
            return
        self.draw_image(map(lambda x: int(x * self.alpha()), self.color))
        goto = self.rect.center
        goto = self.run_from_zombies(field, goto)
        goto = self.run_to_food(field, goto)
        goto = (goto[0] + (1 * self.current_dir[0]), goto[1] + (1 * self.current_dir[1]))
        go_to_dir = zutil.dir_to(self.rect.center, goto)
        self.current_dir = go_to_dir
        super(self.__class__, self).update(field)
        
    def run_from_zombies(self, field, goto):
        span = zutil.span(field.rect)
        span_mid = span / 2.0
        for zombie in field.zombies.sprites():
            dist = zutil.distance(self.rect.center, zombie.rect.center)
            rev_dir = False
            if dist > span_mid:
                dist = span - dist
                rev_dir = True
            if dist >= self.VISION:
                continue
            factor_dist = float(self.VISION - dist) ** 2
            direc = zutil.opposite_dir(zutil.dir_to(self.rect.center, zombie.rect.center))
            if rev_dir: 
                zutil.opposite_dir(direc)
            goto_x, goto_y = goto
            dir_x, dir_y = direc
            goto = (goto_x + (factor_dist * dir_x), goto_y + (factor_dist * dir_y))
        return goto
    
    def run_to_food(self, field, goto):
        if self.is_hungry():
            span = zutil.span(field.rect)
            span_mid = span / 2.0
            food, _ = field.food.closest_to(self, field)
            if food is not None:
                direc = zutil.dir_to(self.rect.center, food.rect.center)
                dist = zutil.distance(self.rect.center, food.rect.center)
                if dist > span_mid:
                    direc = zutil.opposite_dir(direc)
                goto_x, goto_y = goto
                dir_x, dir_y = direc
                factor = (float(self.speed) / 4 * self.VISION) ** 2
                goto = (goto_x + (factor * dir_x), goto_y + (factor * dir_y))
        return  goto
        
class Consumable(Entity):
    def __init__(self, color, amount=5):
        super(Consumable, self).__init__(color)
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
    def __init__(self, color):
        super(self.__class__, self).__init__(color, amount=50)
