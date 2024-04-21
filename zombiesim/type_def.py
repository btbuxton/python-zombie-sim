"""
Basic types used for optional type checking (mypy)
"""

from dataclasses import dataclass
import pygame
from math import atan2, radians, sin, cos, sqrt
from collections.abc import Callable, Iterable
from typing import NamedTuple, Protocol, Tuple

EventCallback = Callable[[pygame.event.Event], None]
Runnable = Callable[[], None]


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def distance(self, dest: "Point") -> float:
        return sqrt(((self.x - dest.x) ** 2) + ((self.y - dest.y) ** 2))

    def __add__(self, another: "Point") -> "Point":
        return self.__class__(self.x + another.x, self.y + another.y)

    def __sub__(self, another: "Point") -> "Point":
        return self.__class__(self.x - another.x, self.y - another.y)


PointProducer = Callable[[], Point]


class Bounds(Protocol):
    topleft: Tuple[int, int]
    bottomright: Tuple[int, int]


class HasPosition(Protocol):
    position: Point


class Zombie(HasPosition):
    pass


class Human(HasPosition):
    def eat_food(self, food: "Food") -> None: ...


class Food(HasPosition):
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
    def from_angle(cls, angle_radians: float) -> "Direction":
        return cls(cos(angle_radians), sin(angle_radians))

    @classmethod
    def from_points(cls, src: Point, dest: Point) -> "Direction":
        # TODO FIX
        return cls(dest.x - src.x, dest.y - src.y).normalize()

    def normalize(self) -> "Direction":
        dist = sqrt(self.x**2 + self.y**2)
        if dist == 0:
            return self
        return Direction(self.x / dist, self.y / dist)

    def add_angle(self, angle_degrees: float):
        angle_radians = radians(angle_degrees)
        return self.__class__(
            self.x + cos(angle_radians), self.y + sin(angle_radians)
        ).normalize()

    def to_angle(self) -> float:
        return atan2(self.y, self.x)

    def __neg__(self) -> "Direction":
        negative_one = float(-1)
        return self.__class__(self.x * negative_one, self.y * negative_one)
