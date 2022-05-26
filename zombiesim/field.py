"""
Created on Dec 7, 2014

@author: bbuxton
"""

from dataclasses import dataclass, field
import itertools
import functools
import time
import random
from typing import Callable, Optional, cast, Iterable

import pygame
from zombiesim.entities import Actor, Entity, FoodSprite, HumanSprite, ZombieSprite, EntityGroup
from zombiesim.event import EventLookup
from zombiesim.entity_mover import EntityMover
from zombiesim.types import Food, Human, Point, Bounds
import zombiesim.util as zutil

SEC: int = 1000
MINUTE: int = 60 * SEC
ZOMBIE_UPDATE_MS: int = 200
HUMAN_UPDATE_MS: int = 100

INITIAL_ZOMBIES: int = 5
INITIAL_HUMANS: int = 250
MAX_FOOD: int = 5


def random_point(rect: pygame.rect.Rect) -> Point:
    x = random.randrange(rect.left, rect.right)
    y = random.randrange(rect.top, rect.bottom)
    return (x, y)

@dataclass
class Field:
    zombies: EntityGroup[ZombieSprite]
    humans: EntityGroup[HumanSprite]
    food: EntityGroup[FoodSprite]
    rect: pygame.rect.Rect = pygame.Rect((0,0), (0,0))
    started: float = field(init=False)
    mover: Optional[EntityMover] = None
    registered_ids: list[int] = field(default_factory=list)
    max_food: int = field(init=False)

    def __post_init__(self):
        self.started = time.time()
        self.max_food = len(self.food)

    @property
    def bounds(self) -> Bounds:
        return self.rect

    def start(self, events: EventLookup) -> None:
        id = events.every_do(ZOMBIE_UPDATE_MS,lambda: self.zombies.update(self))
        self.registered_ids.append(id)
        id = events.every_do(HUMAN_UPDATE_MS, lambda: self.humans.update(self))
        self.registered_ids.append(id)
        id = events.every_do(5 * MINUTE, self.print_status)
        self.registered_ids.append(id)
        self.mover = EntityMover(
            events, self.entities_under, on_sprite_change=lambda entity: entity.reset_pos())

    def stop(self, events: EventLookup) -> None:
        print("To all die: " + zutil.str_diff_time(self.started))
        for each_id in self.registered_ids:
            events.remove(each_id)

    def print_status(self):
        print('Update: humans: {0} zombies: {1}'.format(
            len(self.humans), len(self.zombies)))

    def update(self, screen: pygame.surface.Surface) -> bool:
        self.rect = screen.get_rect()
        self.update_humans_to_zombies()
        self.update_eaten_food()
        self.check_and_fix_edges()
        self.check_food()
        return not self.all_dead()

    def update_humans_to_zombies(self) -> None:
        dead_list: list[HumanSprite] = []
        for zombie in self.zombies:
            died: list[HumanSprite] = self.find_if_biten(zombie)
            dead_list += died
        for human in dead_list:
            self.turn(human)

    def update_eaten_food(self):
        for food in self.food:
            eaten:list[Human] = self.find_who_can_eat(food)
            for human in eaten:
                if food.has_more():
                    human.eat_food(cast(Food, food))

    def check_and_fix_edges(self) -> None:
        def check_and_fix(actor: Actor, parent_rect: pygame.rect.Rect):
            if not parent_rect.contains(actor.rect):
                actor.hit_edge(parent_rect)
        for each_zombie in self.zombies:
            check_and_fix(each_zombie, self.rect)
        for each_human in self.humans:
            check_and_fix(each_human, self.rect)

    def check_food(self) -> None:
        num_under_mouse = 0
        if self.mover:
            num_under_mouse = len(self.mover.under_mouse)
        while (len(self.food) + num_under_mouse) < self.max_food:
            new_food = self.food.create_one()
            new_food.rect.center = random_point(self.rect)

    def all_dead(self) -> bool:
        no_humans = not self.humans
        if self.mover:
            return no_humans and not self.mover.under_mouse
        return no_humans

    def draw(self, screen: pygame.surface.Surface) -> None:
        self.food.draw(screen)
        self.humans.draw(screen)
        self.zombies.draw(screen)
        if self.mover:
            self.mover.draw(screen)

    def turn(self, human: HumanSprite) -> None:
        new_zombie = self.zombies.create_one()
        new_zombie.rect.center = human.rect.center

    def entities_under(self, pos: Point) -> Iterable[Entity]:
        return [each for each in itertools.chain(self.humans, self.zombies, self.food)
                if each.rect.collidepoint(pos)]
    
    def find_who_can_eat(self, food: FoodSprite) -> list[Human]:
        humans = pygame.sprite.spritecollide(
                sprite=food, 
                group=self.humans, 
                dokill=False, 
                collided=pygame.sprite.collide_rect)
        return cast(list[Human], humans)

    def find_if_biten(self, zombie: ZombieSprite) -> list[HumanSprite]:
        biten = pygame.sprite.spritecollide(
                sprite=zombie, 
                group=self.humans, 
                dokill=True, 
                collided=pygame.sprite.collide_circle)
        return cast(list[HumanSprite], biten)


def field_creator(start_zombies: int = INITIAL_ZOMBIES, 
                  start_humans: int = INITIAL_HUMANS, 
                  max_food: int = MAX_FOOD) -> Callable[[pygame.rect.Rect], Field]:
    def creator(rect: pygame.rect.Rect) -> Field:
        point_creator = functools.partial(random_point, rect)
        zombies = ZombieSprite.create_group(start_zombies, point_creator)
        humans = HumanSprite.create_group(start_humans, point_creator)
        food = FoodSprite.create_group(max_food, point_creator)
        return Field(zombies=zombies, humans=humans, food=food, rect=rect)
    return creator