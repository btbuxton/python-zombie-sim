'''
Created on Dec 7, 2014

@author: bbuxton
'''

import itertools
import time
import random
import pygame
from typing import Optional, cast

from zombiesim.entities import Food, Human, Zombie, EntityGroup
from zombiesim.event import EventLookup
from zombiesim.entity_mover import EntityMover
from zombiesim.types import Point
import zombiesim.util as zutil


class Field:
    ZOMBIE_UPDATE_MS: int = 200
    HUMAN_UPDATE_MS: int = 100
    SEC: int = 1000
    MINUTE: int = 60 * SEC

    def __init__(self, start_zombies: int = 5, start_humans: int = 250, max_food: int = 2):
        self.mover: Optional[EntityMover] = None
        self.start_zombies: int = start_zombies
        self.start_humans: int = start_humans
        self.max_food: int = max_food

    def start(self, rect: pygame.rect.Rect) -> None:
        self.rect: pygame.rect.Rect = rect
        self.zombies:EntityGroup[Zombie] = Zombie.create_group(
            self.start_zombies, pygame.Color('red'), self.point_creator)
        self.humans:EntityGroup[Human] = Human.create_group(
            self.start_humans, pygame.Color('pink'), self.point_creator)
        self.food:EntityGroup[Food] = Food.create_group(
            self.max_food, pygame.Color('green'), self.point_creator)
        self.started = time.time()

    def point_creator(self) -> Point:
        x = random.randrange(self.rect.left, self.rect.right)
        y = random.randrange(self.rect.top, self.rect.bottom)
        return (x, y)

    def stop(self) -> None:
        print("To all die: " + zutil.str_diff_time(self.started))

    def restart(self) -> None:
        self.stop()
        self.start(self.rect)

    def register_events(self, events: EventLookup) -> None:
        events.every_do(self.ZOMBIE_UPDATE_MS,
                        lambda: self.zombies.update(self))
        events.every_do(self.HUMAN_UPDATE_MS, lambda: self.humans.update(self))
        events.every_do(5 * self.MINUTE, self.print_status)
        events.add_key_press(pygame.K_r, lambda _: self.restart())
        self.mover = EntityMover(
            events, self.entities_under, on_sprite_change=lambda entity: entity.reset_pos())

    def print_status(self):
        print('Update: humans: {0} zombies: {1}'.format(
            len(self.humans), len(self.zombies)))

    def update(self, screen)->None:
        self.rect = screen.get_rect()
        #self.killzone = self.create_killzone()
        all_dead:list[Human] = []
        for zombie in self.zombies:
            dead:list[Human] = cast(list[Human], pygame.sprite.spritecollide(
                zombie, self.humans, True, collided=pygame.sprite.collide_circle))
            all_dead.extend(dead)
        for human in all_dead:
            self.turn(human)
        for food in self.food:
            eaten:list[Human] = cast(list[Human], pygame.sprite.spritecollide(
                food, self.humans, False, collided=pygame.sprite.collide_rect))
            for human in eaten:
                if food.has_more():
                    human.eat_food(food)
        self.check_and_fix_edges()
        self.check_food()
        if self.all_dead():
            self.stop()
            self.start(self.rect)

    def all_dead(self) -> bool:
        no_humans = not self.humans
        if self.mover:
            return no_humans and not self.mover.under_mouse
        return no_humans

    def check_food(self):
        num_under_mouse = 0
        if self.mover:
            num_under_mouse = len(self.mover.under_mouse)
        while (len(self.food) + num_under_mouse) < self.max_food:
            self.food.create_one(self.point_creator)

    def draw(self, screen) -> None:
        self.food.draw(screen)
        self.humans.draw(screen)
        self.zombies.draw(screen)
        if self.mover:
            self.mover.draw(screen)

    def turn(self, human: Human) -> None:
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
