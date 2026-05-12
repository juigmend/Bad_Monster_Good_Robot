# Final assignment for the Advanced Course in Programming 
# at the University of Helsinki, Open University.
# Assignment completed in May of 2026.

# Author: Juan Ignacio Mendoza Garay

# Instructions:
  # Get rich or get eaten by monsters.
  # Robots can take your coins and save them for you.
  # Through a door you can escape to a clear space.
  # You are at the center of the screen and see the action from above.
  # Move with the arrow keys.
  # Change the game parameters to adjust difficulty and visualisation.

# GAME PARAMETERS:
monster_speed = 1
initial_number_of_monsters = 1
robot_speed = 1
number_of_robots = 3
window_size = (640, 480)
fps = 60

#==========================================================================#

import math
from random import randint, uniform, sample

import pygame

pygame.init()

def initcoord(window_size:list, img_size:list, scale:float=1.01)->list:
    '''random point just outside of a centered circle'''
    window_size = [v*scale for v in window_size]
    orig = [v/2 for v in window_size]
    r = min(orig)
    angle = uniform(0,2*math.pi)
    x = orig[0] + math.cos(angle) * r - img_size[0]/2
    y = orig[1] + math.sin(angle) * r - img_size[1]/2
    return [x,y]

def xy2xxyy( xy_orig:list, size:list)-> list:
    '''
    Get coordinates of the four corners of a rectangular object.
    Args:
        xy_orig: [x, y] of the upper left corner
        size: [width, height] of the object
    Returns:
        [x_left, x_right, y_top, y_bottom]
    '''
    return [xy_orig[0], xy_orig[0] + size[0],
            xy_orig[1], xy_orig[1] + size[1]]

def check_overlap(a:list, b:list)-> bool:
    ''' 
    Check if two rectangles overlap.
    Args:
        a, b: [x_left, x_right, y_top, y_bottom]
    '''
    return sum([a[1] < b[0], a[0] > b[1], a[3] < b[2], a[2] > b[3]]) == 0

class CircBuff:
    '''
    Circular buffer.
    Init Args:
        nvar: number of variables
        npt: number of points (e.g., time-samples)
    '''
    def __init__(self, nvar:int=2, npt:int=2):
        self.nvar = nvar
        self.npt = npt
        self.buffer = [[0 for _ in range(npt)] for _ in range(nvar)]

    def mean(self, ptin:list)-> list:
        r = [0 for _ in range(self.nvar)]
        for i,v in enumerate(self.buffer):
            v.pop(0)
            v.append(ptin[i])
            r[i] = sum([f for f in v]) / self.npt
        return(r)

class SpawningObject:
    def __init__(self, param:dict):
        self.window = param['window']
        self.window_size = param['window_size']
        self.wait_range = param['wait_range']
        self.wait = randint(self.wait_range[0], self.wait_range[1])
        self.xy = [None,None]
        self.load_img()
        self.compute_img_size()
        self.initcoord()

    def load_img(self):
        self.img = pygame.image.load('my_image.png')

    def compute_img_size(self):
        self.img_size = (self.img.get_width(), self.img.get_height())
        self.img_size_half = [v/2 for v in self.img_size]

    def initcoord(self):
        self.xy = initcoord(self.window_size, self.img_size)

    def get_size(self):
        return {'full' : self.img_size, 'half' : self.img_size_half}

    def move(self, hv:list):
        self.xy[0] += hv[0]
        self.xy[1] += hv[1]

    def next(self, hv:list):
        if self.wait == 0:
            self.move(hv)
            self.window.blit(self.img, self.xy)
        else: 
            self.wait -= 1
        return self.xy

class Coin(SpawningObject):
    def load_img(self):
        self.img = pygame.image.load('coin.png')

    def reset(self):
        self.wait = randint(self.wait_range[0], self.wait_range[1])
        self.initcoord()

class Monster(SpawningObject):
    def __init__(self, param:dict):
        self.window = param['window']
        self.window_size = param['window_size']
        
        self.xy = [None,None]
        self.load_img()
        self.compute_img_size()
        self.initcoord()
        
        # local:
        self.speed = param['speed']
        self.make_step()
        self.other_step = False
        self.glow_r = self.img_size_half[0]*2
        self.orig_xy = [a/2-b for a,b in zip(self.window_size, self.img_size_half)]

    def make_step(self):
        self.step = self.speed * uniform(0.2,1) / 2

    def load_img(self):
        self.img = pygame.image.load('monster.png')

    def get_size(self):
        return {
            'full' : self.img_size,
            'half' : [v*2 for v in self.img_size_half]
        }
    
    def make_glow(self):
        self.circle_xy = [(a+b) for a,b in zip(self.xy, self.img_size_half)]
        for r in range(int(self.glow_r), 0, -2):
            c = int(255-(r / self.glow_r) * 255)
            if self.other_step:
                colour = [c, 32, 32]
            else:
                colour = [c, c, c]
            pygame.draw.circle(self.window, colour, self.circle_xy, r)

    def alt_step(self, new_step=None):
        if new_step:
            self.step = new_step
            self.other_step = True
        else:
            self.make_step()
            self.other_step = False

    def move(self, hv:list):
        self.xy[0] += hv[0]
        self.xy[1] += hv[1]

        # own displacement towards the center:
        diffs = [a-b for a,b in zip(self.xy, self.orig_xy)]
        if diffs[0] < 0:
            self.xy[0] += self.step
        elif diffs[0] > 0:
            self.xy[0] -= self.step
        if diffs[1] < 0:
            self.xy[1] += self.step
        elif diffs[1] > 0:
            self.xy[1] -= self.step

    def next(self, app: 'GameApp'):
        self.move(app)
        self.make_glow()
        self.window.blit(self.img, self.xy)
        return self.xy

class Robot(SpawningObject):
    def __init__(self, param:dict):
        self.window = param['window']
        self.window_size = param['window_size']
        self.wait_range = param['wait_range']
        
        self.xy = [None,None]
        self.load_img()
        self.compute_img_size()
        self.initcoord()
        
        # local:
        self.step = param['speed'] * uniform(0.2,1)
        self.orig_xy = [a/2-b for a,b in zip(self.window_size, self.img_size_half)]
        self.directions = ['L','R','U','D']
        self.new_wait_direction()

    def load_img(self):
        self.img = pygame.image.load('robot.png')
        
    def new_wait_direction(self):   
        self.wait = randint(self.wait_range[0], self.wait_range[1])
        self.direction = sample(self.directions,1)[0]

    def move(self, hv:list):
        self.xy[0] += hv[0]
        self.xy[1] += hv[1]

        # own independent displacement:
        if self.direction == 'L':
            self.xy[0] -= self.step
        if self.direction == 'R':
            self.xy[0] += self.step
        if self.direction == 'U':
            self.xy[1] -= self.step
        if self.direction == 'D':
            self.xy[1] += self.step
        self.wait -= 1
        if self.wait == 0:
            self.new_wait_direction()

    def next(self, app: 'GameApp'):
        self.move(app)
        self.window.blit(self.img, self.xy)
        return self.xy
    
class Door(SpawningObject):
    def __init__(self, param:dict):        
        self.window = param['window']
        self.window_size = param['window_size']

        self.xy = [None,None]
        self.load_img()
        self.compute_img_size()
        self.initcoord()

        # local:
        wait_factor = 20 # wait longer to spawn
        self.wait_range = [v*wait_factor for v in param['wait_range']]
        self.wait = randint(self.wait_range[0], self.wait_range[1])

    def load_img(self):
        self.img = pygame.image.load('door.png')

class GameApp:
    def __init__(self, metaparam:dict):
        self.mparam = metaparam
        self.__set_pic()
        self.reset_points = True
        self.__set_defaults()
        
    def __set_pic(self):
        self.window = pygame.display.set_mode(self.mparam['window_size'])
        self.center_xy = [v/2 for v in self.mparam['window_size']]
        self.center_r = 8
        self.center_half_size = [self.center_r, self.center_r]
        self.center_size = [v*2 for v in self.center_half_size]
        center_orig = [v-self.center_r for v in self.center_xy]
        self.center_xxyy = xy2xxyy(center_orig, self.center_size)
        self.game_over_pos = self.center_xy.copy()
        self.game_over_pos[0] -= 162
        self.game_over_pos[1] -= 34

        self.rad_mask_r = min(self.center_xy)

        self.texts_pos = (self.mparam['window_size'][0]*0.03, self.mparam['window_size'][1]*0.03)
        self.texts_colour = (150, 250, 220)

        self.text_fonts = {'big' : pygame.font.SysFont("Verdana", 52),
                           'small' : pygame.font.SysFont("Verdana", 18)} 
        pygame.display.set_caption('Bad Monster, Good Robot')

    def __init_spobj(self, object_class):
        '''init spawning objects'''
        name = object_class.__name__
        n = self.spobj_param[name]['n']
        param = self.spobj_param[name]
        self.spobj[name] = {}
        self.spobj[name]['list'] = [object_class(param) for _ in range(n)]
        if param['init_one']:
            self.spobj[name]['list'][0].wait = 0 # so always one spawns immediately
        self.spobj[name]['size'] = self.spobj[name]['list'][0].get_size()

    def __set_defaults(self):
        '''set or reset to initial state'''
        self.spobj = {}
        self.spobj_param = {}
        spobj_param_common = { 
            'window' : self.window,
            'window_size' : self.mparam['window_size'],
            'wait_range' : self.mparam['wait_range'],
            'init_one': True,
            }
        
        self.spobj_param['Coin'] = dict(spobj_param_common)
        self.spobj_param['Coin']['n'] = self.mparam['n_coins']
        self.__init_spobj(Coin)

        self.spobj_param['Monster'] = dict(spobj_param_common)
        self.spobj_param['Monster']['speed'] = self.mparam['monster_speed']
        self.spobj_param['Monster']['n'] = self.mparam['n_monsters_init']
        self.__init_spobj(Monster)

        self.spobj_param['Robot'] = dict(spobj_param_common)
        self.spobj_param['Robot']['speed'] = self.mparam['robot_speed']
        self.spobj_param['Robot']['n'] = self.mparam['n_robots']
        self.__init_spobj(Robot)

        self.spobj_param['Door'] = dict(spobj_param_common)
        self.spobj_param['Door']['init_one'] = False
        self.spobj_param['Door']['n'] = self.mparam['n_doors']
        self.__init_spobj(Door)

        self.hv = [0,0] # [vertical, horizontal] step (0,step,-step)
        self.step = self.mparam['step_length']
        self.disp_speed = 100
        self.game_over = False
        self.restart = False
        if self.reset_points:
            self.coins = 0
            self.time_nocoins = 0
        self.moster_unleashed = False
        self.coins_add_monster = self.mparam['coins_add_monster']
        self.cbuff = CircBuff(2,self.step*6)

    def __monster_addition(self):
        if self.coins > self.coins_add_monster:
            param = self.spobj_param['Monster']
            self.spobj['Monster']['list'].append(Monster(param))
            self.coins_add_monster += self.mparam['coins_add_monster']

    def __check_arrowkeys(self, event: 'pygame.event'):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.hv[0] = self.step
            elif event.key == pygame.K_RIGHT:
                self.hv[0] = -self.step
            if event.key == pygame.K_DOWN:
                self.hv[1] = -self.step
            elif event.key == pygame.K_UP:
                self.hv[1] = self.step
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.hv[0] = 0
            elif event.key == pygame.K_RIGHT:
                self.hv[0] = 0
            if event.key == pygame.K_DOWN:
                self.hv[1] = 0
            elif event.key == pygame.K_UP:
                self.hv[1] = 0

    def __get_events(self):
        for event in pygame.event.get():
            if self.game_over:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.__init__(self.mparam)
            else:
                self.__check_arrowkeys(event)
            if event.type == pygame.QUIT:
                exit()
    
    def __make_rad_mask(self):
        self.rad_mask = pygame.Surface(self.mparam['window_size'])
        for r in range(int(self.rad_mask_r), 0, -1):
            rad_mask_colour = [int(255 - (r / self.rad_mask_r) * 255) for _ in range(3)]
            pygame.draw.circle(self.rad_mask, rad_mask_colour, self.center_xy, r)

    def __display_texts(self):
        s = f'coins: {self.coins}'
        s += f'\nspeed: {self.disp_speed}%'
        text = self.text_fonts['small'].render(s, True, self.texts_colour)
        self.window.blit(text, self.texts_pos)

    def __display_center(self):
        '''display circle at the center and the line that indicates direction and speed'''
        center_colour = (225, 200, 110)
        pygame.draw.circle(self.window, center_colour, self.center_xy, self.center_r)
        nose_xy = [(1.5*a*-(self.center_r))+b for a,b in zip(self.cbuff.mean(self.hv),self.center_xy)]        
        if any(nose_xy):
            pygame.draw.line(self.window, center_colour, self.center_xy, 
                             nose_xy, width=int(self.center_r/4))

    def __display_fixed_elements(self):
        self.window.blit(self.rad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        self.__display_center()

    def __game_over_manager(self):
        if self.game_over:
            texts = {
                0:{'text': self.text_fonts['big'].render(f'GAME OVER', True, (255,0,0)),
                'pos' : self.game_over_pos},
                1:{'text': self.text_fonts['small'].render(
                    f'press the space bar to restart', True, (200,200,200)),
                    'pos': (self.game_over_pos[0] + 30,
                            self.game_over_pos[1] + 80)}
            }
            for t in texts.values():
                self.window.blit(t['text'], t['pos'])
            self.hv = [0,0]
            self.reset_points = True

    def __action_at_center(self, name:str, o: 'SpawningObject'):
        if name == 'Coin':
            self.coins += 1
            self.step *= 0.9
            self.disp_speed = round(100 * self.step / self.mparam['step_length'])
            o.reset()
            self.time_nocoins = 0
        elif name == 'Monster':
            self.game_over = True
        elif name == 'Robot':
            self.step = self.mparam['step_length']
            self.disp_speed = 100
            self.__display_texts()
        elif name == 'Door':
            self.reset_points = False
            self.__set_defaults()
    
    def __nocoins_manager(self):
        '''
        Unleash a monster (goes faster) if no coins collected for a given time.
        Leash it back by collecting a coin.
        '''
        if self.time_nocoins == 0 and self.moster_unleashed:
            obj = self.spobj['Monster']['list'][0]
            obj.alt_step(new_step=None)
        elif self.time_nocoins > self.mparam['time_nocoins']:
            step_ratio = 0.6 # speed of the unleashed monster relative to the player's speed
            obj = self.spobj['Monster']['list'][0]
            obj.alt_step(new_step= self.step * step_ratio)
            self.moster_unleashed = True
        self.time_nocoins += 1
            
    def __update_spobjects(self):
        for name in self.spobj:
            for obj in self.spobj[name]['list']:
                obj_xy = obj.next(self.hv)
                obj_xxyy = xy2xxyy(obj_xy, self.spobj[name]['size']['full'])
                if check_overlap(obj_xxyy, self.center_xxyy):
                    self.__action_at_center(name, obj)

    def run(self):
        clock = pygame.time.Clock()
        self.__make_rad_mask()
        while True: # main loop
            self.window.fill((0, 0, 0))

            self.__get_events()
            self.__update_spobjects()
            self.__display_fixed_elements()
            self.__display_texts()
            self.__nocoins_manager()
            self.__monster_addition()
            self.__game_over_manager()

            pygame.display.flip()
            clock.tick(self.mparam['fps'])

mparam = {
    'window_size' : window_size,
    'step_length' : 2, # speed of the player
                       # decreases with carried coins, resets by giving coins to a robot
    'n_monsters_init' : initial_number_of_monsters,
    'monster_speed' : monster_speed,
    'n_robots' : number_of_robots,
    'robot_speed' : robot_speed,
    'n_coins' : 8,
    'coins_add_monster' : 20, # at every increment of this much coins a monster is added
    'n_doors' : 1,
    'wait_range' : [fps, fps*8], # coins: respawn, robots: change direction
    'time_nocoins' : fps * 10, # time without collecting a coin before a monster goes faster
    'fps' : fps,
}

GameApp(mparam).run()