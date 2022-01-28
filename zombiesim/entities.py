'''
Created on Dec 7, 2014

@author: bbuxton
'''
import random
import sys
import pygame
import math
from collections.abc import Callable, Iterator
from typing import Optional, Generic, TypeVar, Type

import zombiesim.util as zutil
from zombiesim.types import PointProducer, Point

SpritePredicate = Callable[[pygame.sprite.Sprite], bool]
EntityCallback = Callable[['Entity'], None]
T = TypeVar('T', bound='Entity')


class EntityGroup(pygame.sprite.Group, Generic[T]):
    def __init__(self, clazz: type[T], color: pygame.Color):
        super().__init__()
        self.entity_class: type[T] = clazz
        self.color: pygame.Color = color

    def create_one(self, point_getter: PointProducer) -> T:
        entity: T = self.entity_class(self.color)
        self.add(entity)
        entity.rect.center = point_getter()
        entity.added_to_group(self)
        return entity

    def closest_to(self, other: pygame.sprite.Sprite, field, to_include: SpritePredicate = lambda entity: True) -> tuple[Optional[pygame.sprite.Sprite], float]:
        span = zutil.span(field.rect)
        span_mid = span / 2.0
        curmin: float = sys.maxsize
        curactor = None
        other_rect: pygame.rect.Rect = other.rect  # type: ignore
        pos = other_rect.center
        for each in self.sprites():
            if not to_include(each):
                continue
            each_rect: pygame.rect.Rect = each.rect  # type: ignore
            dist = zutil.distance(pos, each_rect.center)
            if dist > span_mid:
                dist = span - dist
            if dist < curmin:
                curmin = dist
                curactor = each
        return (curactor, curmin)

    def __iter__(self) -> Iterator[T]:  # type: ignore
        return super().__iter__()  # type: ignore


class Entity(pygame.sprite.Sprite):
    _mouse_groups: list[pygame.sprite.AbstractGroup]
    rect: pygame.rect.Rect
    image: pygame.Surface

    @classmethod
    def create_group(cls: Type[T], size: int, color: pygame.Color, point_getter: PointProducer) -> EntityGroup[T]:
        all_group = EntityGroup[T](cls, color)
        for _ in range(size):
            all_group.create_one(point_getter)
        return all_group

    def __init__(self, color: pygame.Color):
        super().__init__()
        self.color = color
        self.create_image()
        self._mouse_groups = []

    def added_to_group(self, group: EntityGroup) -> None:
        pass

    def create_image(self) -> None:
        width = 10
        height = 10
        self.image = pygame.Surface([width, height], flags=pygame.SRCALPHA)
        self.image.fill(pygame.Color(0, 0, 0, 0))
        self.draw_image(self.color)
        self.rect = self.image.get_rect()
        self.radius = min(width, height) / 2

    def draw_image(self, color: pygame.Color) -> None:
        pass

    def reset_pos(self) -> None:
        pass

    def pick_up(self, pos: Point) -> None:
        groups = self.groups()
        self._mouse_groups = []
        for group in groups:
            group.remove(self)
            self._mouse_groups.append(group)
        self_rect: pygame.rect.Rect = self.rect  # type: ignore
        self._mouse_offset = zutil.diff_points(self_rect.center, pos)

    def update_pick_up(self, pos: Point) -> None:
        self.rect.center = zutil.add_points(pos, self._mouse_offset)
        self.reset_pos()

    def put_down(self, pos: Point):
        self.update_pick_up(pos)
        for group in self._mouse_groups:
            group.add(self)
        del self._mouse_groups
        del self._mouse_offset


class Actor(Entity):
    def __init__(self, color: pygame.Color, default_speed: float = 4.0) -> None:
        super().__init__(color)
        self.speed = default_speed
        self.change_dir()

    def added_to_group(self, group: EntityGroup['Actor']) -> None:
        self.reset_pos()

    def draw_image(self, color: pygame.Color) -> None:
        pygame.draw.ellipse(self.image, color, self.image.get_rect())

    def reset_pos(self) -> None:
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def update_pos(self, direc: tuple[float, float]) -> None:
        dirx, diry = direc
        self.x = self.x + (dirx * self.speed)
        self.y = self.y + (diry * self.speed)
        self.rect.x = int(round(self.x))
        self.rect.y = int(round(self.y))

    def hit_edge(self, parent_rect: pygame.rect.Rect) -> None:
        if self.rect.left < parent_rect.left:
            self.rect.right = parent_rect.right
        if self.rect.right > parent_rect.right:
            self.rect.left = parent_rect.left
        if self.rect.top < parent_rect.top:
            self.rect.bottom = parent_rect.bottom
        if self.rect.bottom > parent_rect.bottom:
            self.rect.top = parent_rect.top
        self.reset_pos()

    def change_dir(self) -> None:
        self.current_dir = zutil.random_direction()

    def update(self, field):
        self.update_pos(self.current_dir)


class Zombie(Actor):
    VISION = 100
    ATTACK_WAIT_MAX = 25

    def __init__(self, color: pygame.Color):
        self.angle = zutil.random_angle()
        super().__init__(color, 2.0)
        self.attack_wait = random.randint(
            int(self.ATTACK_WAIT_MAX / 2), self.ATTACK_WAIT_MAX)

    def update(self, field):
        if self.attack_wait > 0:
            self.attack_wait = self.attack_wait - 1
            return
        goto = self.rect.center
        goto = self.run_to_humans(field, goto)
        goto = (goto[0] + (self.current_dir[0]),
                goto[1] + (self.current_dir[1]))
        victim_angle = zutil.angle_to(self.rect.center, goto)
        if victim_angle > self.angle:
            self.angle += math.radians(10)
        elif victim_angle < self.angle:
            self.angle -= math.radians(10)
        self.current_dir = zutil.angle_to_dir(self.angle)
        super().update(field)
        # self.change_dir()

    def run_to_humans(self, field, goto: Point) -> Point:
        span = zutil.span(field.rect)
        span_mid = span / 2.0
        victim, _ = field.humans.closest_to(self, field)
        if victim is not None:
            direc = zutil.dir_to(self.rect.center, victim.rect.center)
            dist = zutil.distance(self.rect.center, victim.rect.center)
            if dist > span_mid:
                dist = span - dist
                direc = zutil.opposite_dir(direc)
            if dist < self.VISION:
                factor_dist = float(self.VISION - dist)
                goto_x, goto_y = goto
                dir_x, dir_y = direc
                goto = (int(goto_x + (factor_dist * dir_x)),
                        int(goto_y + (factor_dist * dir_y)))
        return goto

    def change_dir(self) -> None:
        self.angle = zutil.random_angle_change(self.angle, 10)
        self.current_dir = zutil.angle_to_dir(self.angle)


class Human(Actor):
    VISION = 50

    def __init__(self, color):
        super().__init__(color)
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
            # field.turn(self)
            return
        self.color.a = int(255 * self.alpha())
        self.draw_image(self.color)
        goto = self.rect.center
        goto = self.run_from_zombies(field, goto)
        goto = self.run_to_food(field, goto)
        goto = (goto[0] + (self.current_dir[0]),
                goto[1] + (self.current_dir[1]))
        go_to_dir = zutil.dir_to(self.rect.center, goto)
        self.current_dir = go_to_dir
        super().update(field)

    def run_from_zombies(self, field, goto):
        span = zutil.span(field.rect)
        span_mid = span / 2.0
        for zombie in field.zombies.sprites():
            dist = zutil.distance(self.rect.center, zombie.rect.center)
            if dist >= self.VISION:
                continue
            rev_dir = False
            if dist > span_mid:
                dist = span - dist
                rev_dir = True
            factor_dist = float(self.VISION - dist) ** 2
            direc = zutil.dir_to(self.rect.center, zombie.rect.center)
            if not rev_dir:
                direc = zutil.opposite_dir(direc)
            goto_x, goto_y = goto
            dir_x, dir_y = direc
            goto = (goto_x + (factor_dist * dir_x),
                    goto_y + (factor_dist * dir_y))
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
        return goto


class Consumable(Entity):
    def __init__(self, color, amount=5):
        super().__init__(color)
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
        super().__init__(color, amount=50)
