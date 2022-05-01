'''
Created on Dec 7, 2014

@author: bbuxton
'''
import random
import sys
import pygame
import math
from collections.abc import Callable, Iterator
from typing import Any, Optional, Generic, TypeVar, Type, cast

import zombiesim.util as zutil
from zombiesim.types import Bounds, Food, PointProducer, Point, World

SpritePredicate = Callable[[pygame.sprite.Sprite], bool]
EntityCallback = Callable[['Entity'], None]
T = TypeVar('T', bound='Entity')


class EntityGroup(pygame.sprite.Group, Generic[T]):
    def __init__(self, clazz: type[T], color: pygame.Color):
        super().__init__()
        self.entity_class: type[T] = clazz
        self.color: pygame.Color = color

    def create_one(self) -> T:
        entity: T = self.entity_class(self.color)
        self.add(entity)
        return entity

    def closest_to(self, 
                   other: pygame.sprite.Sprite, 
                   rect: pygame.rect.Rect, 
                   to_include: SpritePredicate = lambda entity: True) -> tuple[Optional[pygame.sprite.Sprite], float]:
        span = zutil.span(rect)
        span_mid = span / 2.0
        curmin: float = sys.maxsize
        curactor = None
        other_rect: Optional[pygame.rect.Rect] = other.rect
        if other_rect is None:
            return (None, 0.0)
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

    def __iter__(self) -> Iterator[T]:
        return cast(Iterator[T],super().__iter__())

ENTITY_WIDTH = 10
ENTITY_HEIGHT = 10

class Entity(pygame.sprite.Sprite):
    @classmethod
    def create_group(cls: Type[T], size: int, color: pygame.Color, point_getter: PointProducer) -> EntityGroup[T]:
        all_group = EntityGroup[T](cls, color)
        for _ in range(size):
            new_entity = all_group.create_one()
            new_entity.rect.center = point_getter()
        return all_group

    def __init__(self, color: pygame.Color):
        super().__init__()
        self.color: pygame.Color = color
        self._mouse_groups: list[pygame.sprite.AbstractGroup] = []
        self.image: pygame.Surface = self.create_image()
        self.rect: pygame.rect.Rect = self.image.get_rect()
        self.radius: Point = cast(Point, min(self.rect.width, self.rect.height) / 2)
        self.draw_image(self.color) # FIXME


    def create_image(self) -> pygame.Surface:
        image = pygame.Surface([ENTITY_WIDTH, ENTITY_HEIGHT], flags=pygame.SRCALPHA)
        image.fill(pygame.Color(0, 0, 0, 0))
        return image   

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

    def update(self, *args, **kwargs) -> None:
        """ Let's be honest - this is to make the typing system happy"""
        self.update_state(args[0])
        super().update(*args, **kwargs)

    def update_state(self, field: World) -> None:
        pass



class Actor(Entity):
    def __init__(self, color: pygame.Color, default_speed: float = 4.0):
        super().__init__(color)
        self.speed = default_speed
        self.change_dir()

    @property
    def x(self) -> int:
        return self.rect.x

    @property
    def y(self) -> int:
        return self.rect.y

    def draw_image(self, color: pygame.Color) -> None:
        pygame.draw.ellipse(self.image, color, self.image.get_rect())

    def update_pos(self, direc: tuple[float, float]) -> None:
        dirx, diry = direc
        new_x = self.x + (dirx * self.speed)
        new_y = self.y + (diry * self.speed)
        self.rect.x = int(round(new_x))
        self.rect.y = int(round(new_y))

    def hit_edge(self, parent_rect: pygame.rect.Rect) -> None:
        if self.rect.left < parent_rect.left:
            self.rect.right = parent_rect.right
        if self.rect.right > parent_rect.right:
            self.rect.left = parent_rect.left
        if self.rect.top < parent_rect.top:
            self.rect.bottom = parent_rect.bottom
        if self.rect.bottom > parent_rect.bottom:
            self.rect.top = parent_rect.top

    def change_dir(self) -> None:
        self.current_dir = zutil.random_direction()

    def update_state(self, field: World) -> None:
        self.update_pos(self.current_dir)
        super().update_state(field)


class ZombieSprite(Actor):
    VISION = 100
    ATTACK_WAIT_MAX = 25

    def __init__(self, color: pygame.Color):
        self.angle = zutil.random_angle()
        super().__init__(color, 2.0)
        self.attack_wait = random.randint(
            int(self.ATTACK_WAIT_MAX / 2), self.ATTACK_WAIT_MAX)

    def update_state(self, field: World) -> None:
        if self.attack_wait > 0:
            self.attack_wait = self.attack_wait - 1
            return
        goto = self.rect.center
        goto = self.run_to_humans(field.humans, field.bounds, goto)
        next_point = (goto[0] + self.current_dir[0], goto[1] + self.current_dir[1])
        victim_angle = zutil.angle_to(self.rect.center, next_point)
        if victim_angle > self.angle:
            self.angle += math.radians(10)
        elif victim_angle < self.angle:
            self.angle -= math.radians(10)
        self.current_dir = zutil.angle_to_dir(self.angle)
        super().update_state(field)

    def run_to_humans(self, humans: Any, bounds: Bounds, goto: Point) -> Point:
        victim, _ = humans.closest_to(self, bounds)
        if victim is None:
            return goto
        victim_rect = victim.rect
        if victim_rect is None:
            return goto
        span = zutil.span(bounds)
        span_mid = span / 2.0
        direc = zutil.dir_to(self.rect.center, victim_rect.center)
        dist = zutil.distance(self.rect.center, victim_rect.center)
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


class HumanSprite(Actor):
    VISION = 50

    def __init__(self, color: pygame.Color):
        super().__init__(color)
        self.reset_lifetime()
        #self.freeze = 0

    def eat_food(self, food: Food) -> None:
        if self.is_hungry():
            food.consume()
            self.reset_lifetime()
            self.change_dir()

    def is_hungry(self) -> bool:
        return self.speed < 2.0

    def is_dead(self) -> bool:
        return self.speed == 0

    def reset_lifetime(self) -> None:
        self.lifetime = zutil.xfrange(2 + (random.random() * 2), 0, -0.0005)

    def alpha(self) -> float:
        result = self.speed / 2.0
        return min(result, 1)

    def update_state(self, field: World) -> None:
        self.speed = next(self.lifetime, 0)
        if self.is_dead():
            self.kill()
            return
        self.color.a = int(255 * self.alpha())
        self.draw_image(self.color)
        goto = self.rect.center
        goto = self.run_from_zombies(field, goto)
        goto = self.run_to_food(field, goto)
        next_pos = (goto[0] + self.current_dir[0], goto[1] + self.current_dir[1])
        go_to_dir = zutil.dir_to(self.rect.center, next_pos)
        self.current_dir = go_to_dir
        super().update_state(field)

    def run_from_zombies(self, field, goto: Point) -> Point:
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

    def run_to_food(self, field, goto: Point) -> Point:
        if self.is_hungry():
            span = zutil.span(field.rect)
            span_mid = span / 2.0
            food, _ = field.food.closest_to(self, field.rect)
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
    def __init__(self, color: pygame.Color, amount: int=5):
        super().__init__(color)
        self.amount: int = amount

    def draw_image(self, color: pygame.Color) -> None:
        pygame.draw.rect(self.image, color, self.image.get_rect())

    def consume(self) -> None:
        self.amount -= 1
        if not self.has_more():
            self.kill()

    def has_more(self) -> bool:
        return self.amount > 0


class FoodSprite(Consumable):
    def __init__(self, color):
        super().__init__(color, amount=50)
