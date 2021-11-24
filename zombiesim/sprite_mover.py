'''
Created on Dec 8, 2014

@author: bbuxton
'''

import pygame
from zombiesim.event import EventLookup
import zombiesim.util as zutil
from zombiesim.types import Point, EventCallback
from collections.abc import Callable

SpriteCallback = Callable[[pygame.sprite.Sprite], None]
SpriteFinder = Callable[[Point], list[pygame.sprite.Sprite]]


class SpriteMover:
    class Pickup:
        def __init__(self, sprite: pygame.sprite.Sprite, pos: Point, on_pos_change: SpriteCallback):
            self.sprite: pygame.sprite.Sprite = sprite
            self.groups = tuple(sprite.groups())
            center: Point = sprite.rect.center  # type: ignore
            self.offset: Point = zutil.diff_points(center, pos)
            self.on_pos_change: SpriteCallback = on_pos_change

        def up(self) -> None:
            for each in self.groups:
                each.remove(self.sprite)

        def down(self) -> None:
            for each in self.groups:
                each.add(self.sprite)

        def update(self, pos: Point):
            new_center: Point = zutil.add_points(pos, self.offset)
            self.sprite.rect.center = new_center  # type: ignore
            self.on_pos_change(self.sprite)

    def __init__(self, event_lookup: EventLookup, sprite_finder_func: SpriteFinder, on_sprite_change: SpriteCallback = lambda sprite: None):
        self.under_mouse: pygame.sprite.Group = pygame.sprite.Group()
        self.sprite_finder_func: SpriteFinder = sprite_finder_func
        self.on_sprite_change: SpriteCallback = on_sprite_change
        self.on_mouse_up: EventCallback = lambda pos: None
        self.on_mouse_move: EventCallback = lambda pos: None
        self.registry: dict[pygame.sprite.Sprite, SpriteMover.Pickup] = {}
        self.register_events(event_lookup)

    def register_events(self, events: EventLookup) -> None:
        events.add(pygame.MOUSEBUTTONDOWN, self.mouse_down)
        events.add(pygame.MOUSEMOTION, self.mouse_move)
        events.add(pygame.MOUSEBUTTONUP, self.mouse_up)

    def mouse_down(self, event: pygame.event.Event) -> None:
        if event.button != 1:
            return
        pos = event.pos
        sprites = self.sprites_under(pos)
        for each in sprites:
            self.pick_up(each, pos)

        def on_up(pos, sprites=sprites):
            for each in sprites:
                self.put_down(each, pos)
        self.on_mouse_up = on_up

        def on_move(pos, sprites=sprites):
            for each in sprites:
                self.update_pick_up(each, pos)
        self.on_mouse_move = on_move

    def mouse_move(self, event: pygame.event.Event) -> None:
        if not event.buttons[0]:
            return
        pos = event.pos
        self.on_mouse_move(pos)

    def mouse_up(self, event: pygame.event.Event) -> None:
        if event.button != 1:
            return
        pos = event.pos
        self.on_mouse_up(pos)
        self.on_mouse_up = lambda pos: None
        self.on_mouse_move = lambda pos: None

    def pick_up(self, sprite: pygame.sprite.Sprite, pos: Point) -> None:
        info = self.Pickup(sprite, pos, self.on_sprite_change)
        self.registry[sprite] = info
        info.up()
        self.under_mouse.add(sprite)

    def update_pick_up(self, sprite: pygame.sprite.Sprite, pos: Point) -> None:
        self.registry[sprite].update(pos)

    def put_down(self, sprite: pygame.sprite.Sprite, pos: Point) -> None:
        info = self.registry[sprite]
        self.under_mouse.remove(sprite)
        info.down()
        info.update(pos)
        del self.registry[sprite]

    def sprites_under(self, pos: Point):
        return self.sprite_finder_func(pos)

    def draw(self, screen):
        self.under_mouse.draw(screen)
