'''
Created on Dec 7, 2014

Various utility functions that don't fit into objects yet

@author: bbuxton
'''

import math
import time
import random

def str_diff_time(begin):
    end = int(round(time.time() - begin))
    rest, seconds = divmod(end, 60)
    hours, minutes = divmod(rest, 60)
    return '{0} hours, {1} minutes, {2} seconds'.format(hours, minutes, seconds)
    
def distance(origin, dest):
    originx,originy = origin
    destx,desty = dest
    return math.sqrt(((originy - desty) ** 2) + ((originx - destx) **2))

def dir_to(origin, dest):
    originx,originy = origin
    destx,desty = dest
    diffx, diffy = destx - originx, desty - originy
    angle = math.atan2(diffy, diffx)
    return (math.cos(angle), math.sin(angle))

def opposite_dir(direc):
    negative_one = float(-1)
    return map(lambda x: x * negative_one, direc)
    
def random_direction():
    angle = math.radians(random.randrange(0, 360))
    return (math.cos(angle), math.sin(angle))

def xfrange(start, stop, step):
    current = start
    while ((step > 0 and current < stop) or (step < 0 and current > stop)):
        yield current
        current = current + step