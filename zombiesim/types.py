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

class Zombie(Protocol):
    pass

class Human(Protocol):
    pass

class Food(Protocol):
    def consume(self) -> None:
        return

class World(Protocol):
    zombies: Iterable[Zombie]
    humans: Iterable[Human]
    food: Iterable[Food]
    bounds: Bounds