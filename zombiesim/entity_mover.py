"""
Created on Dec 8, 2014

@author: bbuxton
"""

from typing import Iterable
from collections.abc import Callable

import pygame
from zombiesim.event import EventLookup
from zombiesim.type_def import Point, EventCallback
from zombiesim.entities import Entity, EntityCallback

SpriteCallback = Callable[[pygame.sprite.Sprite], None]
SpriteFinder = Callable[[Point], Iterable[Entity]]


class EntityMover:
    class Pickup:
        def __init__(self, sprite: Entity, pos: Point, on_pos_change: EntityCallback):
            self.sprite: Entity = sprite
            self.groups = tuple(sprite.groups())
            center: Point = Point(*sprite.rect.center)
            self.offset: Point = center - pos
            self.on_pos_change: EntityCallback = on_pos_change

        def up(self) -> None:
            # pylint: disable=invalid-name
            for each in self.groups:
                each.remove(self.sprite)

        def down(self) -> None:
            for each in self.groups:
                each.add(self.sprite)

        def update(self, pos: Point):
            new_center: Point = pos + self.offset
            self.sprite.rect.center = int(new_center.x), int(new_center.y)
            self.on_pos_change(self.sprite)

    def __init__(
        self,
        event_lookup: EventLookup,
        sprite_finder_func: SpriteFinder,
        on_sprite_change: EntityCallback = lambda sprite: None,
    ):
        self.under_mouse: pygame.sprite.Group = pygame.sprite.Group()
        self.sprite_finder_func: SpriteFinder = sprite_finder_func
        self.on_sprite_change: EntityCallback = on_sprite_change
        self.on_mouse_up: EventCallback = lambda pos: None
        self.on_mouse_move: EventCallback = lambda pos: None
        self.registry: dict[pygame.sprite.Sprite, EntityMover.Pickup] = {}
        self.register_events(event_lookup)

    def register_events(self, events: EventLookup) -> None:
        # pylint: disable=no-member
        events.add(pygame.MOUSEBUTTONDOWN, self.mouse_down)
        events.add(pygame.MOUSEMOTION, self.mouse_move)
        events.add(pygame.MOUSEBUTTONUP, self.mouse_up)

    def mouse_down(self, event: pygame.event.Event) -> None:
        if event.button != 1:
            return
        pos = Point(*event.pos)
        sprites = self.sprites_under(pos)
        for each in sprites:
            self.pick_up(each, pos)

        def on_up(pos: Point, sprites=sprites):
            for each in sprites:
                self.put_down(each, pos)

        self.on_mouse_up = on_up  # type: ignore

        def on_move(pos: Point, sprites=sprites):
            for each in sprites:
                self.update_pick_up(each, pos)

        self.on_mouse_move = on_move  # type: ignore

    def mouse_move(self, event: pygame.event.Event) -> None:
        if not event.buttons[0]:
            return
        pos = Point(*event.pos)
        self.on_mouse_move(pos)  # type: ignore

    def mouse_up(self, event: pygame.event.Event) -> None:
        if event.button != 1:
            return
        pos = Point(*event.pos)
        self.on_mouse_up(pos)  # type: ignore
        self.on_mouse_up = lambda pos: None
        self.on_mouse_move = lambda pos: None

    def pick_up(self, sprite: Entity, pos: Point) -> None:
        info = self.Pickup(sprite, pos, self.on_sprite_change)
        self.registry[sprite] = info
        info.up()
        self.under_mouse.add(sprite)

    def update_pick_up(self, sprite: Entity, pos: Point) -> None:
        self.registry[sprite].update(pos)

    def put_down(self, sprite: Entity, pos: Point) -> None:
        info = self.registry[sprite]
        self.under_mouse.remove(sprite)
        info.down()
        info.update(pos)
        del self.registry[sprite]

    def sprites_under(self, pos: Point) -> Iterable[Entity]:
        return self.sprite_finder_func(pos)

    def draw(self, screen: pygame.surface.Surface) -> None:
        self.under_mouse.draw(screen)
