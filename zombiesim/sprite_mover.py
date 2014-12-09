'''
Created on Dec 8, 2014

@author: bbuxton
'''

import pygame
import zombiesim.util as zutil

class SpriteMover(object):
    class Pickup(object):
        def __init__(self, sprite, pos, on_pos_change):
            self.sprite = sprite
            self.groups = tuple(sprite.groups())
            self.offset = zutil.diff_points(sprite.rect.center, pos)
            self.on_pos_change = on_pos_change
        
        def up(self):
            for each in self.groups:
                each.remove(self.sprite)
        
        def down(self):
            for each in self.groups:
                each.add(self.sprite)
                
        def update(self, pos):
            self.sprite.rect.center = zutil.add_points(pos, self.offset)
            self.on_pos_change(self.sprite)
        
    def __init__(self, event_lookup, sprite_finder_func, on_sprite_change = lambda sprite: None):
        self.under_mouse = pygame.sprite.Group()
        self.sprite_finder_func = sprite_finder_func
        self.on_sprite_change = on_sprite_change
        self.on_mouse_up = lambda pos: None
        self.on_mouse_move = lambda pos: None
        self.registry = {}
        self.register_events(event_lookup)
        
    def register_events(self, events):
        events.add(pygame.MOUSEBUTTONDOWN, self.mouse_down)
        events.add(pygame.MOUSEMOTION, self.mouse_move)
        events.add(pygame.MOUSEBUTTONUP, self.mouse_up)
        
    def mouse_down(self,event):
        if event.button is not 1:
            return
        pos = event.pos
        sprites = self.sprites_under(pos)
        for each in sprites:
            self.pick_up(each, pos)
        def on_up(pos, sprites = sprites):
            for each in sprites:
                self.put_down(each, pos)
        self.on_mouse_up = on_up
        def on_move(pos, sprites = sprites):
            for each in sprites:
                self.update_pick_up(each, pos)
        self.on_mouse_move = on_move
        
    def mouse_move(self, event):
        if not event.buttons[0]:
            return
        pos = event.pos
        self.on_mouse_move(pos)
    
    def mouse_up(self, event):
        if event.button is not 1:
            return
        pos = event.pos
        self.on_mouse_up(pos)
        self.on_mouse_up = lambda pos: None
        self.on_mouse_move = lambda pos: None
    
    def pick_up(self, sprite, pos):
        info = self.Pickup(sprite, pos, self.on_sprite_change)
        self.registry[sprite] = info
        info.up()
        self.under_mouse.add(sprite)
    
    def update_pick_up(self, sprite, pos):
        self.registry[sprite].update(pos)
    
    def put_down(self, sprite, pos):
        info = self.registry[sprite]
        self.under_mouse.remove(sprite)
        info.down()
        info.update(pos)
        del self.registry[sprite]
        
    def sprites_under(self, pos):
        return self.sprite_finder_func(pos)
    
    def draw(self, screen):
        self.under_mouse.draw(screen)