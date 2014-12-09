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
    MAX_FOOD = 2
    START_ZOMBIES = 1
    START_HUMANS = 250
    ZOMBIE_UPDATE_MS = 200
    HUMAN_UPDATE_MS = 100
    SEC = 1000
    MINUTE = 60 * SEC
    
    def __init__(self):
        self.mover = None
    
    def start(self, rect):
        self.rect = rect
        self.killzone = self.create_killzone()
        def point_creator():
                x = random.randrange(self.killzone.left, self.killzone.right)
                y = random.randrange(self.killzone.top, self.killzone.bottom)
                return (x,y)
        self.zombies = Zombie.create_group(self.START_ZOMBIES, pygame.Color('red'), point_creator)
        self.humans = Human.create_group(self.START_HUMANS, pygame.Color('pink'), point_creator)
        self.food = Food.create_group(self.MAX_FOOD, pygame.Color('green'), point_creator)
        self.started = time.time()
        
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
        self.killzone = self.create_killzone()
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
        while (len(self.food) + len(self.mover.under_mouse)) < self.MAX_FOOD:
            self.food.create_one(self.killzone)
        
    def draw(self, screen):
        screen.fill(pygame.Color(0, 32, 0), self.killzone)
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
            
    def create_killzone(self):
        return self.rect.inflate(0 - Human.VISION * 1.5, 0 - Human.VISION * 1.5)
    
    def entities_under(self, pos):
        return [each for each in itertools.chain(self.humans, self.zombies, self.food)
            if each.rect.collidepoint(pos)]