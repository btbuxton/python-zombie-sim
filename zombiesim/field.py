'''
Created on Dec 7, 2014

@author: bbuxton
'''

import itertools
import time
import random
from typing import Optional, cast, Iterable

import pygame
from zombiesim.entities import Actor, Entity, FoodSprite, HumanSprite, ZombieSprite, EntityGroup
from zombiesim.event import EventLookup
from zombiesim.entity_mover import EntityMover
from zombiesim.types import Point, Bounds
import zombiesim.util as zutil

SEC: int = 1000
MINUTE: int = 60 * SEC
ZOMBIE_UPDATE_MS: int = 200
HUMAN_UPDATE_MS: int = 100

class Field:
    def __init__(self, start_zombies: int = 5, start_humans: int = 250, max_food: int = 2):
        self.mover: Optional[EntityMover] = None
        self.start_zombies: int = start_zombies
        self.start_humans: int = start_humans
        self.max_food: int = max_food

    @property
    def bounds(self) -> Bounds:
        return self.rect

    def start(self, rect: pygame.rect.Rect) -> None:
        self.rect: pygame.rect.Rect = rect
        self.zombies:EntityGroup[ZombieSprite] = ZombieSprite.create_group(
            self.start_zombies, pygame.Color('red'), self.point_creator)
        self.humans:EntityGroup[HumanSprite] = HumanSprite.create_group(
            self.start_humans, pygame.Color('pink'), self.point_creator)
        self.food:EntityGroup[FoodSprite] = FoodSprite.create_group(
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
        events.every_do(ZOMBIE_UPDATE_MS,lambda: self.zombies.update(self))
        events.every_do(HUMAN_UPDATE_MS, lambda: self.humans.update(self))
        events.every_do(5 * MINUTE, self.print_status)
        events.add_key_press(pygame.K_r, lambda _: self.restart())
        self.mover = EntityMover(
            events, self.entities_under, on_sprite_change=lambda entity: entity.reset_pos())

    def print_status(self):
        print('Update: humans: {0} zombies: {1}'.format(
            len(self.humans), len(self.zombies)))

    def update(self, screen: pygame.surface.Surface) -> None:
        self.rect = screen.get_rect()
        self.update_humans_to_zombies()
        self.update_eaten_food()
        self.check_and_fix_edges()
        self.check_food()
        self.restart_if_all_dead()

    def restart_if_all_dead(self) -> None:
        if self.all_dead():
            self.stop()
            self.start(self.rect)

    def update_eaten_food(self):
        for food in self.food:
            eaten:list[HumanSprite] = cast(list[HumanSprite], pygame.sprite.spritecollide(
                food, self.humans, False, collided=pygame.sprite.collide_rect))
            for human in eaten:
                if food.has_more():
                    human.eat_food(food)

    def update_humans_to_zombies(self) -> None:
        dead_list:list[HumanSprite] = []
        for zombie in self.zombies:
            dead:list[HumanSprite] = cast(list[HumanSprite], pygame.sprite.spritecollide(
                zombie, self.humans, True, collided=pygame.sprite.collide_circle))
            dead_list += dead
        for human in dead_list:
            self.turn(human)

    def all_dead(self) -> bool:
        no_humans = not self.humans
        if self.mover:
            return no_humans and not self.mover.under_mouse
        return no_humans

    def check_food(self) -> None:
        num_under_mouse = 0
        if self.mover:
            num_under_mouse = len(self.mover.under_mouse)
        while (len(self.food) + num_under_mouse) < self.max_food:
            new_food = self.food.create_one()
            new_food.rect.center = self.point_creator()

    def draw(self, screen: pygame.surface.Surface) -> None:
        self.food.draw(screen)
        self.humans.draw(screen)
        self.zombies.draw(screen)
        if self.mover:
            self.mover.draw(screen)

    def turn(self, human: HumanSprite) -> None:
        new_zombie = self.zombies.create_one()
        new_zombie.rect.center = human.rect.center

    def check_and_fix_edges(self) -> None:
        def check_and_fix(actor: Actor, parent_rect: pygame.rect.Rect):
            if not parent_rect.contains(actor.rect):
                actor.hit_edge(parent_rect)
        for each_zombie in self.zombies:
            check_and_fix(each_zombie, self.rect)
        for each_human in self.humans:
            check_and_fix(each_human, self.rect)

    def entities_under(self, pos: Point) -> Iterable[Entity]:
        return [each for each in itertools.chain(self.humans, self.zombies, self.food)
                if each.rect.collidepoint(pos)]
