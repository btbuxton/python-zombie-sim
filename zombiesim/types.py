"""
Basic types used for optional type checking (mypy)
"""
import pygame
from collections.abc import Callable
from typing import Union, Tuple

EventCallback = Callable[[pygame.event.Event], None]
Runnable = Callable[[], None]

Position = Tuple[float, float]
