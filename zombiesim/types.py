"""
Basic types used for optional type checking (mypy)
"""
import pygame
from collections.abc import Callable
from typing import TypeVar

EventCallback = Callable[[pygame.event.Event], None]
Runnable = Callable[[], None]

Part = TypeVar('Part', int, float)
Point = tuple[Part, Part]
Direction = tuple[float, float]

PointProducer = Callable[[], Point]
