'''
Created on Dec 7, 2014

Various utility functions that don't fit into objects yet

@author: bbuxton
'''

import math
import random
import time

import pygame
from zombiesim.types import Bounds, Point, Direction
from collections.abc import Generator


def str_diff_time(begin, time_func=time.time):
    end = int(round(time_func() - begin))
    rest, seconds = divmod(end, 60)
    hours, minutes = divmod(rest, 60)
    return '{0} hours, {1} minutes, {2} seconds'.format(hours, minutes, seconds)


def distance(origin: Point, dest: Point) -> float:
    originx, originy = origin
    destx, desty = dest
    return math.sqrt(((originy - desty) ** 2) + ((originx - destx) ** 2))


def span(rect: Bounds) -> float:
    return distance(rect.topleft, rect.bottomright)


def dir_to(origin: Point, dest: Point) -> Direction:
    angle = angle_to(origin, dest)
    return angle_to_dir(angle)


def angle_to_dir(angle: float) -> Direction:
    return (math.cos(angle), math.sin(angle))


def angle_to(origin: Point, dest: Point) -> float:
    originx, originy = origin
    destx, desty = dest
    diffx, diffy = destx - originx, desty - originy
    return math.atan2(diffy, diffx)


def opposite_dir(direc: Direction) -> Direction:
    negative_one = float(-1)
    return tuple([x * negative_one for x in direc])  # type: ignore


def random_direction() -> Direction:
    angle = random_angle()
    return angle_to_dir(angle)


def random_angle() -> float:
    return math.radians(random.randint(0, 359))


def random_angle_change(angle: float, amount: int):
    change = math.radians(random.randint(-amount, amount))
    return angle + change


def xfrange(start: float, stop: float, step: float) -> Generator[float, None, None]:
    current = start
    while ((step > 0 and current < stop) or (step < 0 and current > stop)):
        yield current
        current = current + step


def diff_points(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def add_points(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def make_full_screen() -> None:
    display_info = pygame.display.Info()
    flags = pygame.display.get_surface().get_flags()
    if not flags & pygame.FULLSCREEN:
        pygame.display.set_mode(
            (display_info.current_w, display_info.current_h), flags | pygame.FULLSCREEN)
