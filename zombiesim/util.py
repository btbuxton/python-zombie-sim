"""
Created on Dec 7, 2014

Various utility functions that don't fit into objects yet

@author: bbuxton
"""

from functools import wraps
import math
import random
from threading import RLock
import time
import weakref
from typing import Any, Callable, TypeVar

import pygame
from zombiesim.type_def import Bounds, Point, Direction
from collections.abc import Generator


def str_diff_time(begin: float,
                  time_func: Callable[[], float] = time.time) -> str:
    end = int(round(time_func() - begin))
    rest, seconds = divmod(end, 60)
    hours, minutes = divmod(rest, 60)
    return f'{hours} hours, {minutes} minutes, {seconds} seconds'


def span(rect: Bounds) -> float:
    return Point(*rect.topleft).distance(Point(*rect.bottomright))


def random_direction() -> Direction:
    return Direction.from_angle(random_angle())


def random_angle() -> float:
    return math.radians(random.randint(0, 359))


def random_angle_change(angle: float, amount: int) -> float:
    change = math.radians(random.randint(-amount, amount))
    return angle + change


def xfrange(start: float,
            stop: float,
            step: float) -> Generator[float, None, None]:
    current = start
    while ((step > 0 and current < stop) or (step < 0 and current > stop)):
        yield current
        current = current + step


def make_full_screen() -> None:
    display_info = pygame.display.Info()
    flags = pygame.display.get_surface().get_flags()
    if not flags & pygame.FULLSCREEN:
        pygame.display.set_mode(
            (display_info.current_w, display_info.current_h),
            flags | pygame.FULLSCREEN)


ReturnT = TypeVar('ReturnT', bound=Any)
CacheableFunc = Callable[..., ReturnT]


def cache_for(times: int = 1) -> Callable[[CacheableFunc], CacheableFunc]:
    lock: RLock = RLock()
    inst_cache: dict[int, Any] = dict()

    def decorator(method: CacheableFunc) -> CacheableFunc:
        @wraps(method)
        def wrapper(ref, *args, **kargs) -> ReturnT:
            id_ref: int = id(ref)
            with lock:
                called: int
                value: ReturnT
                called, value = inst_cache.get(id_ref, (0, None))
                if called % times == 0:
                    value = method(ref, *args, **kargs)
                called += 1
                inst_cache[id_ref] = called, value
                if called == 1:
                    def finalizer() -> None:
                        with lock:
                            del inst_cache[id_ref]
                    weakref.finalize(ref, finalizer)
                return value
        return wrapper
    return decorator
