"""
Basic types used for optional type checking (mypy)
"""
import pygame
from collections.abc import Callable

EventCallback = Callable[[pygame.event.Event], None]
Runnable = Callable[[], None]

Point = tuple[float, float]
Direction = tuple[float, float]
