'''
Created on Dec 7, 2014

@author: bbuxton
'''

import itertools
import time
import random
import pygame

from zombiesim.entities import Food
from zombiesim.entities import Human
from zombiesim.entities import Zombie

from zombiesim.sprite_mover import SpriteMover

import zombiesim.util as zutil

class Field(object):
    ZOMBIE_UPDATE_MS = 200
    HUMAN_UPDATE_MS = 100
    SEC = 1000
    MINUTE = 60 * SEC
    
    def __init__(self, start_zombies = 5, start_humans = 250, max_food = 2):
        self.mover = None
        self.start_zombies = start_zombies
        self.start_humans = start_humans
        self.max_food = max_food 
    
    def start(self, rect):
        self.rect = rect
        self.zombies = Zombie.create_group(self.start_zombies, pygame.Color('red'), self.point_creator)
        self.humans = Human.create_group(self.start_humans, pygame.Color('pink'), self.point_creator)
        self.food = Food.create_group(self.max_food, pygame.Color('green'), self.point_creator)
        self.started = time.time()
        
    def point_creator(self):
        x = random.randrange(self.rect.left, self.rect.right)
        y = random.randrange(self.rect.top, self.rect.bottom)
        return (x,y)
        
    def stop(self):
        print("To all die: " + zutil.str_diff_time(self.started))
        
    def restart(self):
        self.stop()
        self.start(self.rect)
        
    def register_events(self, events):
        events.every_do(self.ZOMBIE_UPDATE_MS, lambda: self.zombies.update(self))
        events.every_do(self.HUMAN_UPDATE_MS, lambda: self.humans.update(self))
        events.every_do(5 * self.MINUTE, self.print_status)
        events.add_key_press(pygame.K_r, lambda _: self.restart())
        self.mover = SpriteMover(events, self.entities_under, on_sprite_change = lambda entity: entity.reset_pos())
        
    def print_status(self):
        print 'Update: humans: {0} zombies: {1}'.format(len(self.humans), len(self.zombies))
        
    def update(self, screen):
        self.rect = screen.get_rect()
        #self.killzone = self.create_killzone()
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
            self.stop()
            self.start(self.rect)
    
    def all_dead(self):
        return not self.humans and not self.mover.under_mouse
    
    def check_food(self):
        while (len(self.food) + len(self.mover.under_mouse)) < self.max_food:
            self.food.create_one(self.point_creator)
        
    def draw(self, screen):
        self.food.draw(screen)
        self.humans.draw(screen)
        self.zombies.draw(screen)
        self.mover.draw(screen)
        
    def turn(self, human):
        self.zombies.create_one(lambda: human.rect.center)
        
    def check_and_fix_edges(self):
        def check_and_fix(actor, parent_rect):
            if not parent_rect.contains(actor.rect):
                actor.hit_edge(parent_rect)
        for each in self.zombies.sprites():
            check_and_fix(each, self.rect)
        for each in self.humans.sprites():
            check_and_fix(each, self.rect)
    
    def entities_under(self, pos):
        return [each for each in itertools.chain(self.humans, self.zombies, self.food)
            if each.rect.collidepoint(pos)]