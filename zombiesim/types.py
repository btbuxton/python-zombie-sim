"""
Basic types used for optional type checking (mypy)
"""
from dataclasses import dataclass
import pygame
from math import atan2, sin, cos, sqrt
from collections.abc import Callable, Iterable
from typing import NamedTuple, Protocol, Tuple

EventCallback = Callable[[pygame.event.Event], None]
Runnable = Callable[[], None]

class Point(NamedTuple):
    x: float
    y: float

PointProducer = Callable[[], Point]


class Bounds(Protocol):
    topleft: Tuple[int, int]
    bottomright: Tuple[int, int]


class KnowsCenter(Protocol):
    center: Point


class Zombie(KnowsCenter):
    pass


class Human(KnowsCenter):
    def eat_food(self, food: 'Food') -> None: ...


class Food(KnowsCenter):
    def has_more(self) -> bool: ...
    def consume(self) -> None: ...


class World(Protocol):
    zombies: Iterable[Zombie]
    humans: Iterable[Human]
    food: Iterable[Food]
    bounds: Bounds

@dataclass(frozen=True)
class Direction:
    x: float
    y: float

    @classmethod
    def from_angle(cls, angle: float) -> 'Direction':
        return cls(cos(angle), sin(angle))

    @classmethod
    def from_points(cls, src: Point, dest: Point) -> 'Direction':
        #TODO FIX
        return cls(dest.x - src.x, dest.y - src.y).normalize()

    def normalize(self) -> 'Direction':
        dist = sqrt(self.x ** 2 + self.y ** 2)
        return Direction(self.x / dist, self.y / dist)

    def to_angle(self) -> float:
        return atan2(self.y, self.x)

    def reverse(self) -> 'Direction':
        negative_one = float(-1)
        return self.__class__(self.x * negative_one, self.y * negative_one)