"""
Created on Dec 7, 2014

@author: bbuxton
"""
import random
import sys
import pygame
import math
from collections.abc import Callable, Iterator
from typing import Generator, Iterable, Optional, Generic, Tuple, TypeVar, Type, cast

import zombiesim.util as zutil
from zombiesim.type_def import Bounds, Direction, Food, Human, HasPosition,\
                            PointProducer, Point, World, Zombie

SpritePredicate = Callable[[pygame.sprite.Sprite], bool]
EntityCallback = Callable[['Entity'], None]
T = TypeVar('T', bound='Entity')
C = TypeVar('C', bound=HasPosition)


class EntityGroup(pygame.sprite.Group, Generic[T]):
    def __init__(self, clazz: type[T]):
        super().__init__()
        self.entity_class: type[T] = clazz

    def create_one(self) -> T:
        entity: T = self.entity_class()
        self.add(entity)
        return entity

    def __iter__(self) -> Iterator[T]:
        return cast(Iterator[T], super().__iter__())


ENTITY_WIDTH = 10
ENTITY_HEIGHT = 10


class Entity(pygame.sprite.Sprite):
    @classmethod
    def create_group(cls: Type[T],
                     size: int,
                     point_getter: PointProducer) -> EntityGroup[T]:
        all_group = EntityGroup[T](cls)
        for _ in range(size):
            new_entity = all_group.create_one()
            pos = point_getter()
            new_entity.rect.center = int(pos.x), int(pos.y)
        return all_group

    def __init__(self, color: pygame.Color = pygame.Color('black')):
        super().__init__()
        self.color: pygame.Color = color
        self._mouse_groups: list[pygame.sprite.AbstractGroup] = []
        self.image: pygame.Surface = self.create_image()
        self.rect: pygame.rect.Rect = self.image.get_rect()
        self.radius: float = min(self.rect.width, self.rect.height) / 2
        self.draw_image(self.color)  # FIXME

    @property
    def center(self) -> Tuple[int,int]:
        return self.rect.center

    @property
    def position(self) -> Point:
        return Point(*self.center)

    def create_image(self) -> pygame.Surface:
        image = pygame.Surface(
            [ENTITY_WIDTH, ENTITY_HEIGHT], flags=pygame.SRCALPHA)
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
        self._mouse_offset = self.position - pos

    def update_pick_up(self, pos: Point) -> None:
        new_point = pos + self._mouse_offset
        self.rect.center = int(new_point.x), int(new_point.y)
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

    def closest_to(self,
                   other: Iterable[C],
                   bounds: Bounds,
                   to_include: Callable[[C], bool] = lambda _: True) \
            -> tuple[Optional[C], float]:
        self_rect: Optional[pygame.rect.Rect] = self.rect
        if self_rect is None:
            return (None, 0.0)
        span = zutil.span(bounds)
        span_mid = span / 2.0
        curmin: float = sys.maxsize
        curactor: Optional[C] = None
        pos = self.position
        for each in other:
            if not to_include(each):
                continue
            dist = pos.distance(each.position)
            if dist > span_mid:
                dist = span - dist
            if dist < curmin:
                curmin = dist
                curactor = each
        return (curactor, curmin)

    def update_state(self, field: World) -> None:
        pass


class Actor(Entity):
    def __init__(self, color: pygame.Color, default_energy: float = 0.0):
        super().__init__(color)
        self.energy: float = default_energy
        self.change_dir()

    @property
    def x(self) -> int:
        return self.rect.x

    @property
    def y(self) -> int:
        return self.rect.y

    def draw_image(self, color: pygame.Color) -> None:
        pygame.draw.ellipse(self.image, color, self.image.get_rect())

    def update_pos(self, direc: Direction) -> None:
        new_x = self.x + (direc.x * self.energy)
        new_y = self.y + (direc.y * self.energy)
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


ZOMBIE_VISION: int = 100
ZOMBIE_ATTACK_WAIT_MAX: int = 25
ZOMBIE_COLOR: pygame.Color = pygame.Color('red')
ZOMBIE_ENERGY: float = 2.0
RECALCULATE_HUMANS_SEEN: int = 10


class ZombieSprite(Actor):
    def __init__(self):
        self.angle = zutil.random_angle()
        super().__init__(ZOMBIE_COLOR, ZOMBIE_ENERGY)
        self.attack_wait = random.randint(
            int(ZOMBIE_ATTACK_WAIT_MAX / 2), ZOMBIE_ATTACK_WAIT_MAX)

    def update_state(self, field: World) -> None:
        if self.attack_wait > 0:
            self.attack_wait -= 1
            return
        goto = Point(*self.rect.center)
        goto = self.run_to_humans(field, goto)
        next_point = Point(goto.x + self.current_dir.x,
                      goto.y + self.current_dir.y)
        # TODO Revisit
        victim_angle = Direction.from_points(Point(*self.rect.center), next_point).to_angle()
        if victim_angle > self.angle:
            self.angle += math.radians(10)
        elif victim_angle < self.angle:
            self.angle -= math.radians(10)
        self.current_dir = Direction.from_angle(self.angle)
        super().update_state(field)

    @zutil.cache_for(times=RECALCULATE_HUMANS_SEEN)
    def humans_in_vision(self, field: World) -> Iterable[Human]:
        return [human for human in field.humans
                if self.position.distance(human.position) < ZOMBIE_VISION]

    def run_to_humans(self, field: World, goto: Point) -> Point:
        humans = self.humans_in_vision(field)
        bounds = field.bounds
        victim, _ = self.closest_to(humans, bounds)
        if victim is None:
            return goto
        span = zutil.span(bounds)
        span_mid = span / 2.0
        direc = Direction.from_points(self.position, victim.position)
        dist = self.position.distance(victim.position)
        if dist > span_mid:
            dist = span - dist
            direc = -direc

        factor_dist = float(ZOMBIE_VISION - dist)
        goto = Point(int(goto.x + (factor_dist * direc.x)),
                int(goto.y + (factor_dist * direc.y)))
        return goto

    def change_dir(self) -> None:
        self.angle = zutil.random_angle_change(self.angle, 10)
        self.current_dir = Direction.from_angle(self.angle)


HUMAN_VISION: int = 50
HUMAN_COLOR: pygame.Color = pygame.Color('pink')
HUMAN_ENERGY_LEVEL: float = 4.0
HUMAN_HUNGRY_LEVEL: float = HUMAN_ENERGY_LEVEL / 2
RECALCULATE_ZOMBIES_SEEN: int = 5


class HumanSprite(Actor):
    def __init__(self):
        super().__init__(HUMAN_COLOR)
        self.lifetime: Generator[float, None, None] = self.new_lifetime()

    def eat_food(self, food: Food) -> None:
        if self.is_hungry():
            food.consume()
            self.lifetime = self.new_lifetime()
            self.change_dir()

    def is_hungry(self) -> bool:
        return self.energy < HUMAN_HUNGRY_LEVEL

    def is_dead(self) -> bool:
        return self.energy == 0

    def new_lifetime(self) -> Generator[float, None, None]:
        return zutil.xfrange(2 + (random.random() * 2), 0, -0.0005)

    def alpha(self) -> float:
        result = self.energy / 2.0
        return min(result, 1)

    def update_state(self, field: World) -> None:
        self.energy = next(self.lifetime, 0)
        if self.is_dead():
            self.kill()
            return
        self.color.a = int(255 * self.alpha())
        self.draw_image(self.color)
        goto = Point(*self.rect.center)
        goto = self.run_from_zombies(field, goto)
        goto = self.run_to_food(field, goto)
        next_pos = Point(goto.x + self.current_dir.x,
                    goto.y + self.current_dir.y)
        go_to_dir = Direction.from_points(Point(*self.rect.center), next_pos)
        self.current_dir = go_to_dir
        super().update_state(field)

    @zutil.cache_for(times=RECALCULATE_ZOMBIES_SEEN)
    def zombies_in_vision(self, field: World) -> Iterable[Zombie]:
        return [zombie for zombie in field.zombies
                if self.position.distance(zombie.position) <= HUMAN_VISION]

    def run_from_zombies(self, field: World, goto: Point) -> Point:
        span = zutil.span(field.bounds)
        span_mid = span / 2.0
        for zombie in self.zombies_in_vision(field):
            dist = self.position.distance(zombie.position)
            rev_dir = False
            if dist > span_mid:
                dist = span - dist
                rev_dir = True
            factor_dist = float(HUMAN_VISION - dist) ** 2
            direc = Direction.from_points(self.position, zombie.position)
            if not rev_dir:
                direc = -direc
            goto = Point(goto.x + (factor_dist * direc.x),
                    goto.y + (factor_dist * direc.y))
        return goto

    def run_to_food(self, field: World, goto: Point) -> Point:
        if self.is_hungry():
            span = zutil.span(field.bounds)
            span_mid = span / 2.0
            food, _ = self.closest_to(field.food, field.bounds)
            if food is not None:
                direc = Direction.from_points(self.position, food.position)
                dist = self.position.distance(food.position)
                if dist > span_mid:
                    direc = -direc
                factor = (float(self.energy) / 4 * HUMAN_VISION) ** 2
                goto = Point(goto.x + (factor * direc.x), goto.y + (factor * direc.y))
        return goto


class Consumable(Entity):
    def __init__(self, color: pygame.Color, amount: int = 5):
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


FOOD_COLOR: pygame.Color = pygame.Color('green')
DEFAULT_FOOD_AMOUNT: int = 25


class FoodSprite(Consumable):
    def __init__(self):
        super().__init__(FOOD_COLOR, amount=DEFAULT_FOOD_AMOUNT)
