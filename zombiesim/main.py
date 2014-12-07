'''
Created on Nov 29, 2014

@author: btbuxton
'''
import pygame
import random
import sys
import time
import zombiesim.util as zutil
import zombiesim.colors as zcolors

class EntityGroup(pygame.sprite.Group):
    def __init__(self, clazz):
        pygame.sprite.Group.__init__(self)
        self.entity_class = clazz
    
    def create_one(self, rect):
        entity = self.entity_class()
        self.add(entity)
        entity.rect.x = random.randrange(rect.x, rect.width - entity.rect.width)
        entity.rect.y = random.randrange(rect.y, rect.height - entity.rect.height)
        entity.added_to_group(self)
        
    def closest_to(self, other, to_include=lambda entity: True):
        curmin = sys.maxint
        curactor = None
        pos = other.rect.center
        for each in self.sprites():
            if not to_include(each):
                continue
            dist = zutil.distance(pos, each.rect.center)
            if dist < curmin:
                curmin = dist
                curactor = each
        return (curactor, curmin)
    
class Entity(pygame.sprite.Sprite):
    @classmethod
    def create_group(clazz, size, rect):
        all_group = EntityGroup(clazz)
        for _ in range(size):
            all_group.create_one(rect)
        return all_group
    
    def __init__(self, color=zcolors.WHITE):
        pygame.sprite.Sprite.__init__(self)
        self.create_image(color)
        
    def added_to_group(self, group):
        pass
        
    def create_image(self, color):
        width = 10
        height = 10
        self.image = pygame.Surface([width, height],flags = pygame.SRCALPHA)
        self.image.fill(zcolors.CLEAR)
        self.draw_image(color)
        self.rect = self.image.get_rect()
    
    def draw_image(self, color):
        pass
        
class Actor(Entity):
    def __init__(self, color=zcolors.WHITE, default_speed=4.0):
        Entity.__init__(self, color)
        self.speed = default_speed
        self.change_dir()
    
    def added_to_group(self, group):
        self.reset_pos()
    
    def draw_image(self, color):
        pygame.draw.ellipse(self.image, color, self.image.get_rect())
        
    def reset_pos(self):
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
      
    def update_pos(self, direc):
        dirx,diry = direc
        self.x = self.x + (dirx * self.speed)
        self.y = self.y + (diry * self.speed)
        self.rect.x = int(round(self.x))
        self.rect.y = int(round(self.y))
        
    def hit_edge(self, parent_rect):
        if self.rect.left < parent_rect.left:
            self.rect.right = parent_rect.right
        if self.rect.right > parent_rect.right:
            self.rect.left = parent_rect.left
        if self.rect.top < parent_rect.top:
            self.rect.bottom = parent_rect.bottom
        if self.rect.bottom > parent_rect.bottom:
            self.rect.top = parent_rect.top
        self.reset_pos()
        
    def change_dir(self):
        self.current_dir = zutil.random_direction()
            
    def update(self, field):
        self.update_pos(self.current_dir)
        
class Zombie(Actor):
    VISION = 250
    ATTACK_WAIT_MAX = 50
    def __init__(self):
        Actor.__init__(self, zcolors.RED, 2.0)
        self.attack_wait = random.randint(self.ATTACK_WAIT_MAX / 2,self.ATTACK_WAIT_MAX)
        self.aimless = 0
        
    def update(self, field):
        if self.aimless > 0:
            self.aimless = self.aimless - 1
            Actor.update(self,field)
            return
        if self.attack_wait > 0:
            self.attack_wait = self.attack_wait - 1
            return
        if not field.killzone.contains(self):
            x = random.randint(field.killzone.left, field.killzone.right)
            y = random.randint(field.killzone.top, field.killzone.bottom)
            self.current_dir = zutil.dir_to(self.rect.center, (x,y))
            #self.current_dir = dir_to(self.rect.center, field.killzone.center)
            Actor.update(self,field)
            self.aimless = Zombie.VISION
            self.attack_wait = self.ATTACK_WAIT_MAX
            return
        victim,dist = field.humans.closest_to(self) #, field.killzone.contains)
        do_change = lambda: None
        if victim is not None and dist < self.VISION:
            direc = zutil.dir_to(self.rect.center, victim.rect.center)
            if  not field.rect.contains(victim):
                direc = zutil.opposite_dir(direc)
            self.current_dir = direc
            do_change = self.change_dir
        Actor.update(self,field)
        do_change() #this is so zombie changes directions when there is no longer a human
            
class Human(Actor):
    VISION = 100
    def __init__(self):
        Actor.__init__(self, zcolors.PINK)
        self.reset_lifetime()
        self.freeze = 0
        
    def eat_food(self, food):
        if self.is_hungry():
            food.consume()
            self.reset_lifetime()
            self.change_dir()
    
    def is_hungry(self):
        return self.speed < 2.0
    
    def is_dead(self):
        return self.speed == 0
        
    def reset_lifetime(self):
        self.lifetime = zutil.xfrange(2 + (random.random() * 2),0,-0.0005)
        
    def alpha(self):
        result = self.speed / 2.0
        return min(result, 1)
        
    def update(self, field):
        #if self.freeze > 0:
        #    self.freeze = self.freeze - 1
        #    return
        self.speed = next(self.lifetime, 0)
        if self.is_dead():
            self.kill()
            field.turn(self)
            return
        self.draw_image(map(lambda x: int(x * self.alpha()), zcolors.PINK))
        goto = self.rect.center
        goto = self.run_from_zombies(field, goto)
        goto = self.run_to_food(field, goto)
        goto = (goto[0] + (1 * self.current_dir[0]), goto[1] + (1 * self.current_dir[1]))
        go_to_dir = zutil.dir_to(self.rect.center, goto)
        self.current_dir = go_to_dir
        Actor.update(self,field)
        
    def run_from_zombies(self, field, goto):
        for zombie in field.zombies.sprites():
            dist = zutil.distance(self.rect.center, zombie.rect.center)
            if dist >= self.VISION:
                continue
            factor_dist = float(self.VISION - dist)
            direc = zutil.opposite_dir(zutil.dir_to(self.rect.center, zombie.rect.center))
            goto_x, goto_y = goto
            dir_x, dir_y = direc
            goto = (goto_x + (factor_dist * dir_x), goto_y + (factor_dist * dir_y))
        return goto
    
    def run_to_food(self, field, goto):
        if self.is_hungry():
            food, _ = field.food.closest_to(self)
            if food is not None:
                direc = zutil.dir_to(self.rect.center, food.rect.center)
                goto_x, goto_y = goto
                dir_x, dir_y = direc
                factor = float(self.speed) / 4 * self.VISION
                goto = (goto_x + (factor * dir_x), goto_y + (factor * dir_y))
        return  goto
        
    def hit_edge(self, parent_rect):
        if self.rect.left < parent_rect.left:
            self.rect.left = parent_rect.left
        if self.rect.right > parent_rect.right:
            self.rect.right = parent_rect.right
        if self.rect.top < parent_rect.top:
            self.rect.top = parent_rect.top
        if self.rect.bottom > parent_rect.bottom:
            self.rect.bottom = parent_rect.bottom
        self.reset_pos()
        #Actor.hit_edge(self, parent_rect)
        #self.current_dir = dir_to(self.rect.center, parent_rect.center)
        self.current_dir = zutil.opposite_dir(self.current_dir)
        self.freeze = 50
        #x = random.randint(parent_rect.left, parent_rect.right)
        #y = random.randint(parent_rect.top, parent_rect.bottom)
        #self.current_dir = dir_to(self.rect.center, (x,y))
        #self.current_dir = (0,0)

class Consumable(Entity):
    def __init__(self, color=zcolors.GREEN, amount=5):
        Entity.__init__(self, color)
        self.amount = amount
        
    def draw_image(self, color):
        pygame.draw.rect(self.image, color, self.image.get_rect())
    
    def consume(self):
        self.amount = self.amount - 1
        if not self.has_more():
            self.kill()
    
    def has_more(self):
        return self.amount > 0
        
class Food(Consumable):
    def __init__(self):
        Consumable.__init__(self, zcolors.GREEN, amount=50)
    
class Field(object):
    MAX_FOOD = 2
    START_ZOMBIES = 1
    START_HUMANS = 250
    ZOMBIE_UPDATE_MS = 200
    HUMAN_UPDATE_MS = 100
    SEC = 1000
    MINUTE = 60 * SEC
    
    def __init__(self):
        self.under_mouse = pygame.sprite.Group()
        self.on_mouse_up = lambda pos: None
        self.on_mouse_move = lambda pos: None
    
    def start(self, rect):
        self.rect = rect
        self.killzone = self.create_killzone()
        self.zombies = Zombie.create_group(self.START_ZOMBIES, self.killzone)
        self.humans = Human.create_group(self.START_HUMANS, self.killzone)
        self.food = Food.create_group(self.MAX_FOOD, self.killzone)
        self.started = time.time()
        
    def stop(self):
        print("To all die: " + zutil.str_diff_time(self.started))
        
    def restart(self):
        self.stop()
        self.start(self.rect)
        
    def register_events(self, events):
        events.every_do(self.ZOMBIE_UPDATE_MS, lambda: self.zombies.update(self))
        events.every_do(self.HUMAN_UPDATE_MS, lambda: self.humans.update(self))
        events.every_do(5 * self.MINUTE, self.print_status)
        
    def print_status(self):
        print 'Update: humans: {0} zombies: {1}'.format(len(self.humans), len(self.zombies))
        
    def update(self, screen):
        self.rect = screen.get_rect()
        self.killzone = self.create_killzone()
        all_dead = []
        for zombie in self.zombies:
            dead = pygame.sprite.spritecollide(zombie, self.humans, True, collided = pygame.sprite.collide_circle)
            all_dead.extend(dead)
        for human in all_dead:
                self.turn(human)
        for food in self.food:
            eaten = pygame.sprite.spritecollide(food, self.humans, False, collided = pygame.sprite.collide_rect)
            for human in eaten:
                if food.has_more():
                    human.eat_food(food)
        self.check_and_fix_edges()
        self.check_food()
        if self.all_dead():
            self.stop()
            self.start(self.rect)
    
    def all_dead(self):
        return not self.humans
    
    def check_food(self):
        while len(self.food) < self.MAX_FOOD:
            self.food.create_one(self.killzone)
        
    def draw(self, screen):
        screen.fill(zcolors.DARK_GREEN, self.killzone)
        self.food.draw(screen)
        self.humans.draw(screen)
        self.zombies.draw(screen)
        self.under_mouse.draw(screen)
        
    def turn(self, human):
        zombie = Zombie()
        zombie.rect = human.rect
        self.zombies.add(zombie)
        zombie.added_to_group(self.zombies)
        
    def check_and_fix_edges(self):
        def check_and_fix(actor, parent_rect):
            if not parent_rect.contains(actor.rect):
                actor.hit_edge(parent_rect)
        for each in self.zombies.sprites():
            check_and_fix(each, self.rect)
        for each in self.humans.sprites():
            check_and_fix(each, self.rect)
            
    def create_killzone(self):
        return self.rect.inflate(0 - Human.VISION * 1.5, 0 - Human.VISION * 1.5)
    
    def mouse_down(self,event):
        if event.button is not 1:
            return
        pos = event.pos
        actor = self.actor_under(pos)
        if actor is None:
            return
        groups = actor.groups()
        for group in groups:
            group.remove(actor)
        self.under_mouse.add(actor)
        def on_up(pos, groups = groups, actor = actor):
            actor.rect.center = pos 
            actor.reset_pos()
            self.under_mouse.remove(actor)
            for groups in groups:
                groups.add(actor)
        self.on_mouse_up = on_up
        def on_move(pos, actor = actor):
            actor.rect.center = pos
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
    
    def actor_under(self, pos):
        for each in self.humans:
            if each.rect.collidepoint(pos):
                return each
        for each in self.zombies:
            if each.rect.collidepoint(pos):
                return each
        return None
    
class EventLookup(object):
    def __init__(self):
        self.__mapping__= {}
        self.next_event_id = pygame.USEREVENT
        
    def add(self, event_type, func=lambda event: None):
        self.__mapping__[event_type] = func
        
    def func_for(self, event_type):
        return self.__mapping__.get(event_type, lambda event: None)
            
    def next_event_type(self):
        self.next_event_id = self.next_event_id + 1
        return self.next_event_id
    
    def every_do(self, millis, func=lambda: None):
        event_id = self.next_event_type()
        pygame.time.set_timer(event_id, millis)
        self.add(event_id,lambda _: func())
        
    def process_events(self):
        for event in pygame.event.get():
            self.__mapping__.get(event.type, lambda event: None)(event)

def main():
    pygame.init()
    fps = 60
    display_info = pygame.display.Info()
    screen_width = int(display_info.current_w * 0.75)
    screen_height = int(display_info.current_h * 0.75)
    
    pygame.display.set_mode((screen_width, screen_height), pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Zombie Simulation")
    clock = pygame.time.Clock()
    field = Field()
    events = EventLookup()
    field.register_events(events)
    def set_screen(event):
        pygame.display.set_mode(event.dict['size'], pygame.DOUBLEBUF | pygame.RESIZABLE)
    events.add(pygame.VIDEORESIZE, set_screen)
    def key_pressed(event):
        if pygame.K_ESCAPE is event.key:
            events.func_for(pygame.QUIT)(event)
        if pygame.K_f is event.key:
            flags = pygame.display.get_surface().get_flags()
            if not flags & pygame.FULLSCREEN:
                pygame.display.set_mode((display_info.current_w, display_info.current_h), flags | pygame.FULLSCREEN)
        if pygame.K_r is event.key:
            field.restart()
    events.add(pygame.KEYDOWN, key_pressed)
    def mouse_down(event):
        field.mouse_down(event)
    events.add(pygame.MOUSEBUTTONDOWN, mouse_down)
    def mouse_move(event):
        field.mouse_move(event)
    events.add(pygame.MOUSEMOTION, mouse_move)
    def mouse_up(event):
        field.mouse_up(event)
    events.add(pygame.MOUSEBUTTONUP, mouse_up)
    def mark_done(event):
        main.done = True
    main.done = False
    events.add(pygame.QUIT, mark_done)
    
    field.start(pygame.display.get_surface().get_rect())
    while not main.done:
        events.process_events()
        screen = pygame.display.get_surface()
        field.update(screen)
        
        screen.fill(zcolors.BLACK)
        field.draw(screen)
        pygame.display.flip()
        
        clock.tick(fps)
    pygame.quit()
    
if __name__ == '__main__':
    main()