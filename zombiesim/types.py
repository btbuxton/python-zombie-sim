"""
Basic types used for optional type checking (mypy)
"""
import pygame
from collections.abc import Callable, Iterable
from typing import Protocol, TypeVar

EventCallback = Callable[[pygame.event.Event], None]
Runnable = Callable[[], None]

Part = TypeVar('Part', int, float)
Point = tuple[Part, Part]
Direction = tuple[float, float]
PointProducer = Callable[[], Point]


class Bounds(Protocol):
    topleft: Point
    bottomright: Point


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
