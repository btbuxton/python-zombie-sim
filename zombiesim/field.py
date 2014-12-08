'''
Created on Dec 7, 2014

@author: bbuxton
'''

import pygame
import time
import itertools
import util as zutil
import colors as zcolors
from entities import Human
from entities import Zombie
from entities import Food

class Field(object):
    MAX_FOOD = 2
    START_ZOMBIES = 1
    START_HUMANS = 250
    ZOMBIE_UPDATE_MS = 200
    HUMAN_UPDATE_MS = 100
    SEC = 1000
    MINUTE = 60 * SEC
    
    def __init__(self):
        self.under_mouse = pygame.sprite.Group()
        self.on_mouse_up = lambda pos: None
        self.on_mouse_move = lambda pos: None
    
    def start(self, rect):
        self.rect = rect
        self.killzone = self.create_killzone()
        self.zombies = Zombie.create_group(self.START_ZOMBIES, self.killzone)
        self.humans = Human.create_group(self.START_HUMANS, self.killzone)
        self.food = Food.create_group(self.MAX_FOOD, self.killzone)
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
        events.add(pygame.MOUSEBUTTONDOWN, self.mouse_down)
        events.add(pygame.MOUSEMOTION, self.mouse_move)
        events.add(pygame.MOUSEBUTTONUP, self.mouse_up)
        
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
        return not self.humans and not self.under_mouse
    
    def check_food(self):
        while (len(self.food) + len(self.under_mouse)) < self.MAX_FOOD:
            self.food.create_one(self.killzone)
        
    def draw(self, screen):
        screen.fill(zcolors.DARK_GREEN, self.killzone)
        self.food.draw(screen)
        self.humans.draw(screen)
        self.zombies.draw(screen)
        self.under_mouse.draw(screen)
        
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
            
    def create_killzone(self):
        return self.rect.inflate(0 - Human.VISION * 1.5, 0 - Human.VISION * 1.5)
    
    def mouse_down(self,event):
        if event.button is not 1:
            return
        pos = event.pos
        entities = self.entities_under(pos)
        for entity in entities:
            entity.pick_up(pos)
            self.under_mouse.add(entity)
        def on_up(pos, entities = entities):
            for entity in entities:
                self.under_mouse.remove(entity)
                entity.put_down(pos)
        self.on_mouse_up = on_up
        def on_move(pos, entities = entities):
            for entity in entities:
                entity.update_pick_up(pos)
        self.on_mouse_move = on_move
        
    def mouse_move(self, event):
        if not event.buttons[0]:
            return
        pos = event.pos
        self.on_mouse_move(pos)
    
    def mouse_up(self, event):
        if event.button is not 1:
            return
        pos = event.pos
        self.on_mouse_up(pos)
        self.on_mouse_up = lambda pos: None
        self.on_mouse_move = lambda pos: None
    
    def entities_under(self, pos):
        return [each for each in itertools.chain(self.humans, self.zombies, self.food)
            if each.rect.collidepoint(pos)]