'''
Created on Dec 7, 2014

@author: bbuxton
'''

import pygame


class EventLookup(object):
    def __init__(self):
        self._mapping = {}
        self._keys = {}
        self.next_event_id = pygame.USEREVENT
        
    def add(self, event_type, func=lambda event: None):
        self._mapping[event_type] = func
        
    def add_key_press(self, key, func=lambda event: None):
        def key_func(event):
            evt_key = event.key
            self._keys.get(evt_key, lambda event: None)(event)
        self._keys[key] = func
        self.add(pygame.KEYDOWN, key_func)
        
    def func_for(self, event_type):
        return self._mapping.get(event_type, lambda event: None)
            
    def next_event_type(self):
        self.next_event_id = self.next_event_id + 1
        return self.next_event_id
    
    def every_do(self, millis, func=lambda: None):
        event_id = self.next_event_type()
        pygame.time.set_timer(event_id, millis)
        self.add(event_id,lambda _: func())
        
    def process_events(self):
        for event in pygame.event.get():
            self._mapping.get(event.type, lambda event: None)(event)