import pygame
import moderngl
import sys
import numpy as np
import math
import datetime
import random
from PIL import Image

# =========================
# Functions
# =========================
def debug_attack_hitbox_render():
    if object.facing == "right":
        program["transform_matrix"].value = np.array([(object.attack_hitbox_width * screen_ratio[0]), 0.0, 0.0, 0.0,
                                                0.0, (object.attack_hitbox_height * screen_ratio[1]), 0.0, 0.0,
                                                0.0, 0.0, 1.0, 0.0,
                                                wcoords_translate(object.x, object.y, 1)[0], wcoords_translate(object.x, object.y, 1)[1], 0.0, 1.0,
                                                ], dtype='f4')   
    else:
        program["transform_matrix"].value = np.array([(- object.attack_hitbox_width * screen_ratio[0]), 0.0, 0.0, 0.0,
                                                0.0, (object.attack_hitbox_height * screen_ratio[1]), 0.0, 0.0,
                                                0.0, 0.0, 1.0, 0.0,
                                                wcoords_translate(object.x + object.hitbox_width, object.y, 1)[0], wcoords_translate(object.x, object.y, 1)[1], 0.0, 1.0,
                                                ], dtype='f4')   
    vao.render(mode=moderngl.TRIANGLE_STRIP)
    
def exit():
    print("[Info]", datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S:"),"Game successfully closed") # exit with success message
    pygame.quit()
    sys.exit()

def layer_sort(object):
    return object.attributes["layer"]

def reset_game():
    global player, objects, loaded_chunks, camera, debug, attack_timer, new_chunks, debug_sky, debug_towers, debug_mountains, unticked_chunks
    player = Player(7, 5, textures["player_atlas"], 0.6, 1.84375, "hanspeter")
    debug_sky = Background(0, 0, textures["debug_sky"], {"layer":"4","collision":"false","parallax":"0"}, None)
    debug_towers = Background(0, 0.25, textures["debug_towers"], {"layer":"4","collision":"false","parallax":"0.05"}, None)
    debug_mountains = Background(0, 0.25, textures["debug_mountains"], {"layer":"4","collision":"false","parallax":"0.06"}, None)
    objects = [player, debug_sky, debug_towers, debug_mountains]
    loaded_chunks = []
    unticked_chunks = []
    camera = Camera()
    debug = Debug()
    attack_timer = Timer(0.3)
    new_chunks = [] 
    postprocessing.target_brightness = 1.0

def set_screen_ratio(view):
        global screen_ratio, camera_ratio, screen_width, screen_height
        screen_size = pygame.display.get_window_size()
        screen_width = screen_size[0]
        screen_height = screen_size[1]
        ratio_multiplier = math.sqrt(view/(screen_width * screen_height))
        screen_ratio = [(1 / (screen_width * ratio_multiplier) * 2), (1 / (screen_height * ratio_multiplier) * 2)]
        camera_ratio = [(screen_width * ratio_multiplier) / 2, (screen_height * ratio_multiplier) / 2]

def wcoords_translate(x, y, parallax_factor):
    return[((x - camera.wcoord_x * float(parallax_factor)) * screen_ratio[0]) - 1, ((y - camera.wcoord_y * float(parallax_factor)) * screen_ratio[1]) + 1]

def chunk_translate(x, y):
    return [math.floor(x / 16), math.floor(y / 16)]

def get_parameters(parameters):
        parameters = parameters.strip("{}")
        parameters = parameters.split(";")
        parameter_dict = {}
        for i in range(len(parameters)):
            parameter_dict.update({parameters[i].split("=")[0]: parameters[i].split("=")[1]})
        return parameter_dict

def update_loaded_chunks():
    new_chunks = []
    for width in range(-1, 2):
        for height in range(-1, 2):
            new_chunks.append([player.chunk()[0] + width, player.chunk()[1] + height]) # TODO if bored, make it smarter and not just all chunks next to player

    # chunk unloader:
    for object in objects:
        if isinstance(object, Entity):
            if object.chunk()[0] >= player.chunk()[0] + 2 or object.chunk()[0] <= player.chunk()[0] - 2 or object.chunk()[1] >= player.chunk()[1] + 2 or object.chunk()[1] <= player.chunk()[1] - 2:
                object.ticking = False
            else:
                object.ticking = True
        if object.__class__ == Environment:
            if object.chunk[0] >= player.chunk()[0] + 2 or object.chunk[0] <= player.chunk()[0] - 2 or object.chunk[1] >= player.chunk()[1] + 2 or object.chunk[1] <= player.chunk()[1] - 2:
                try:
                    loaded_chunks.remove(object.chunk)
                    unticked_chunks.append(object.chunk)
                except ValueError:
                    pass
                objects.remove(object)
    # print("new:", new_chunks)
    # print("loaded:", loaded_chunks)
    for chunk in new_chunks:
        if chunk not in loaded_chunks:
            loaded_chunks.append(chunk)
            try: 
                with open(f"level/1/{chunk[0]}.{chunk[1]}.pms") as level:
                    for i, line in enumerate(level):
                        line = line.strip()
                        line = line.split()
                        try:
                            parameter_dict = get_parameters(line[3])
                            if not "parallax" in parameter_dict:
                                parameter_dict["parallax"] = "1"
                        except IndexError:
                            parameter_dict = {"layer": "1", "parallax": "1"} # default parameters
                        try:
                            if line[0] in enemies:
                                if chunk not in unticked_chunks:
                                    objects.append(enemies[line[0]][0](float(line[1]) + 16 * chunk[0], float(line[2]) + 16 * chunk[1], *enemies[line[0]][1], parameter_dict))
                            else:
                                objects.append(Environment(float(line[1]) + 16 * chunk[0], float(line[2]) + 16 * chunk[1], textures[line[0]], parameter_dict, chunk))   
                        except:
                            if len(line) == 0 or line[0].startswith("#"):
                                pass
                            else: 
                                print("\033[91m[Error]", datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S:"),f"Line {i + 1} in PhantomSprinter Mapping System chunk [{chunk[0]},{chunk[1]}] is corrupted.\033[0m")
                new_chunks = []
            except FileNotFoundError:
                pass
            try:
                unticked_chunks.remove(chunk)
            except ValueError:
                pass

def texture_load():
    for texture in assets:
        textures.update({texture : AssetManager(assets[texture])})

def get_uv_coords(parameter_list):
    #is not fullscreen texture?, start x coord of texture, width/step of x, frames, total_width, current animation frame, animation timer, height, total height, facing, offset x
    if parameter_list[0] == False:
        #return uv_x, uv_width, uv_y, uv_height
        return [1.0, 1.0, 1.0, 1.0]
    elif parameter_list[0] == True:
        uv_x = parameter_list[1] / parameter_list[4]
        uv_width = parameter_list[2] / parameter_list[4]
        uv_height = parameter_list[7] / parameter_list[8]
        frames = parameter_list[3]
        left_multi = 1
        left_add = 0
        try:
            if parameter_list[9] == "left":
                left_multi = -1
                left_add = uv_width
        except:
            pass
        try: 
            if parameter_list[6].time():
                parameter_list[5] += 1
            if parameter_list[5] >= frames: #TODO fix this whole thing where all the first frames in animation are not actually the first and are completely cooked
                parameter_list[5] = 0
        except AttributeError:
            pass
        if frames == 1:
            return [uv_x + left_add, uv_width * left_multi, 1.0, uv_height]
        else:
            return [(left_add + uv_x + uv_width * parameter_list[5] + 0.000005), uv_width * left_multi, 0.0, uv_height] # change uv_heigth for non stretched texture

# =========================
# Classes
# =========================
class AssetManager:
    def __init__(self, texture_properties):
        self.texture_path= texture_properties[0]
        with Image.open(self.texture_path) as image:
            self.texture = image.convert("RGBA")
            self.width = self.texture.size[0]
            self.height = self.texture.size[1]
        self.texture_raw = ctx.texture((self.width, self.height), 4, self.texture.tobytes())
        self.texture_raw.filter = (ctx.NEAREST, ctx.NEAREST)
        self.custom_hitbox = None
        try:
            self.frames = texture_properties[1]
            self.fps = texture_properties[2]
            self.animated = True
            try:
                self.custom_hitbox = texture_properties [3]
                self.animated = False
            except IndexError:
                pass
        except IndexError:
            self.frames = 1
            self.fps = 0
            self.animated = False
        
    def bind(self):
        self.texture_raw.use(location=0)

class Environment:
    def __init__(self, x, y, texture, attribute_dict, chunk):
        self.x = x
        self.y = y
        self.width = texture.width / 32 / texture.frames + 0.005
        self.height = texture.height / 32 + 0.005
        self.rotation = 0
        self.texture = texture
        self.attributes = attribute_dict
        self.chunk = chunk
        try:
            self.animation_timer = Timer(1 / self.texture.fps)
            self.current_animation_frame = 0
            #is not fullscreen texture?, start x coord of texture, width/step of x, frames, total_width, current animation frame, animation timer, height, total height, facing, offset x
            self.animation = [self.texture.animated, 0, self.texture.width / self.texture.frames, self.texture.frames, self.texture.width, self.current_animation_frame, self.animation_timer, self.texture.height, self.texture.height]
        except:
            self.animation = [self.texture.animated]
    def scoords(self):
        return wcoords_translate(self.x, self.y, self.attributes["parallax"])
    def uv_coords(self):
        return get_uv_coords(self.animation)

class Background(Environment):
    def __init__(self, x, y, texture, attribute_dict, chunk):
        super().__init__(x, y, texture, attribute_dict, chunk)
    
class Entity:
    def __init__(self, x, y, texture, width, height):
        self.x = x
        self.y = y
        self.y_velocity = 0
        self.jumping = False
        self.noclip = False
        self.health = 1
        self.ticking = True
        self.width = width
        self.height = height
        self.rotation = 0
        self.hitbox_width = width
        self.hitbox_height = height
        self.attack_hitbox_width = 2.2
        self.attack_hitbox_height = 1.2
        self.texture = texture
        self.facing = "right"
        self.attributes = {"collision": "false", "layer" : "2", "gravity": "true"}
        self.currentanimation = "static"

    def uv_coords(self):
        if self.currentanimation == "static_attack":
            if self.animation[self.currentanimation][5] == 0:
                self.animation[self.currentanimation][5] = 1
                self.currentanimation = "static"
        self.animation[self.currentanimation][9] = self.facing
        if self.facing == "left": # <---- this is shit
            self.animation["static"][10] = -0.1
        else:
            self.animation["static"][10] = -0.6
        self.width = self.animation[self.currentanimation][2] / 32
        self.height = ((self.animation[self.currentanimation][7] / 32) / self.hitbox_height) * self.hitbox_height
        return get_uv_coords(self.animation[self.currentanimation])
        
    def scoords(self):
        return wcoords_translate(self.x + self.animation[self.currentanimation][10], self.y + self.animation[self.currentanimation][11], 1)
        
    def chunk(self):
        return chunk_translate(self.x, self.y)
    def collide(self):
        for object in objects:
            if object.attributes.get("collision") == "true" or object.attributes.get("collision") == None:
                if not object.texture.custom_hitbox == None:
                    with open(object.texture.custom_hitbox) as custom_hitbox:
                        for line in custom_hitbox:
                            line = line.strip()
                            line = line.split()
                            #line: x1, y1 -> x2, y2
                            if self.x + self.hitbox_width > object.x + float(line[0]) and self.x < object.x + float(line[2]) and self.y < object.y + self.hitbox_height - float(line[1]) and self.y > object.y - float(line[3]):
                                return [True, object.x + float(line[0]), object.x + float(line[2]), object.y - float(line[1]), object.y - float(line[3])]
                elif self.x + self.hitbox_width > object.x and self.x < object.x + object.width and self.y < object.y + self.hitbox_height and self.y > object.y - object.height:
                    return [True, object.x, object.x + object.width, object.y, object.y - object.height]
        return [False, None]
    def damage_collide(self):
        for object in objects:
            if object.attributes.get("damage") == "true":
                if self.x + self.hitbox_width > object.x and self.x < object.x + object.width and self.y < object.y + self.hitbox_height and self.y > object.y - object.height:
                    return True
    def attack(self):
        if self.facing == "right":
            for object in objects:
                if isinstance(object, Entity) and not object.__class__ == self.__class__:
                    if self.x + self.attack_hitbox_width > object.x and self.x < object.x + object.hitbox_width and self.y - self.attack_hitbox_height < object.y and self.y > object.y - object.hitbox_height:
                        object.damage(1)
        if self.facing == "left":
            for object in objects:
                if isinstance(object, Entity) and not object.__class__ == self.__class__:
                    if self.x - self.attack_hitbox_width < object.x and self.x > object.x + object.hitbox_width and self.y - self.attack_hitbox_height < object.y and self.y > object.y - object.hitbox_height:
                        object.damage(1)

class Player(Entity):
    def __init__(self, x, y, texture, width, height, name):
        super().__init__(x, y, texture, width, height) 
        self.name = name
        self.animation = {
            #is not fullscreen texture?, start x coord of texture, width/step of x, frames, total_width, current animation frame, animation timer, height, total height, facing, offset x, offset y
            "static" : [True, 0, 42, 1, self.texture.width, 0, None, 59, 69, self.facing, 0, 0],
            "walking" : [True, 67, 67, 12, self.texture.width, 0, Timer(1 / 16), 53, 69, self.facing, -0.75, -6/32],
            "static_attack" : [True, 871, 119, 8, self.texture.width, 1, Timer(1 / 24), 59, 69, self.facing, -1.5, 0],
            "walking_attack" : [True, 1823, 106, 6, self.texture.width, 1, Timer(1 / 12), 69, 69, self.facing, -1.4, 10/32],
        }
        self.brightness_timer = Timer(1)
    def damage(self, amount):
        self.health -= amount
    def death_update(self):
        if player.health <= 0:
            postprocessing.target_brightness = 0
            if self.brightness_timer.time():
                reset_game()
            
    def uv_coords(self):
        if self.currentanimation == "static_attack":
            if self.animation[self.currentanimation][5] == 0:
                self.animation[self.currentanimation][5] = 1
                self.currentanimation = "static"
        elif self.currentanimation == "walking_attack":
            if self.animation[self.currentanimation][5] == 0:
                self.animation[self.currentanimation][5] = 1
                self.currentanimation = "walking"
        self.animation[self.currentanimation][9] = self.facing
        if self.facing == "left": # <---- this is shit
            self.animation["static"][10] = -0.1
            self.animation["walking_attack"][10] = -1.62
        else:
            self.animation["static"][10] = -0.6
            self.animation["walking_attack"][10] = -1.095
        self.width = self.animation[self.currentanimation][2] / 32
        self.height = ((self.animation[self.currentanimation][7] / 32) / self.hitbox_height) * self.hitbox_height
        return get_uv_coords(self.animation[self.currentanimation])

class Enemy(Entity):
    def __init__(self, x, y, texture, width, height, attributes):
        super().__init__(x, y, texture, width, height) 
        self.attributes = attributes
        self.animation = {
            #is not fullscreen texture?, start x coord of texture, width/step of x, frames, total_width, current animation frame, animation timer, height, total height, facing, offset x,
            "static" : [True, 0, 42, 1, self.texture.width, 0, Timer(5), 59, 69, self.facing, 0, 0],
            "walking" : [True, 67, 67, 12, self.texture.width, 0, Timer(1 / 12), 53, 69, self.facing, -0.75, -6/32],
            "static_attack" : [True, 871, 119, 8, self.texture.width, 1, Timer(1 / 24), 59, 69, self.facing, -1.5, 0],
        }
    def damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            objects.remove(self)

class PistolEnemy(Enemy):
    def __init__(self, x, y, texture, width, height, attributes):
        super().__init__(x, y, texture, width, height, attributes) 
        self.angle = 0
        self.distance = 0
        self.activation_range = 8
        self.shooting_range = 5
        self.shooting_timer = Timer(1)
        self.animation = {
            #is not fullscreen texture?, start x coord of texture, width/step of x, frames, total_width, current animation frame, animation timer, height, total height, facing, offset x,
            "static" : [True, 444, 34, 1, self.texture.width, 0, None, 60, 60, self.facing, 0, 0],
            "walking" : [True, 0, 37, 12, self.texture.width, 0, Timer(1 / 12), 59, 60, self.facing, -0.3, -2/32],
            "draw" : [True, 444, 34, 5, self.texture.width, 0, Timer(1 / 12), 60, 60, self.facing, 0, 0],
            "aim" : [True, 614, 34, 6, self.texture.width, 0, None, 60, 60, self.facing, 0, 0],
        }
        self.angle_list = [
                        (-0.3, -2, 0, 0.7, 0.7),
                        (-0.1, -0.3, 1, 0.7, 0.62),
                        (0.1, -0.1, 2, 0.8, 0.4),
                        (0.6, 0.1, 3, 0.8, 0.32),
                        (1, 0.6, 4, 0.7, 0.22),
                        (2, 1, 5, 0.62, 0.15)
                        ]

    def uv_coords(self):
        self.animation[self.currentanimation][9] = self.facing
        if self.facing == "left": # <---- this is shit
            self.animation["static"][10] = -0.4
            self.animation["aim"][10] = -0.4
            self.animation["draw"][10] = -0.4
        else:
            self.animation["static"][10] = -0.06
            self.animation["aim"][10] = -0.06
            self.animation["draw"][10] = -0.06
        self.width = self.animation[self.currentanimation][2] / 32
        self.height = ((self.animation[self.currentanimation][7] / 32) / self.hitbox_height) * self.hitbox_height
        return get_uv_coords(self.animation[self.currentanimation])
    
    def ai(self):
        if self.ticking == False:
            return
        self.distance = abs(math.sqrt((object.x - player.x) ** 2 + (object.y - player.y) ** 2))
        try:
            self.angle = math.atan((player.y - self.y) / abs(player.x - self.x))
        except ZeroDivisionError:
            pass
        if self.distance <= self.activation_range:
            if self.x > player.x:
                self.facing = "left"
                if self.x > player.x + self.shooting_range:
                    self.x -= 0.03
                    if self.collide()[0]:
                        self.x = object.collide()[2]
                        self.currentanimation = "static"
                    else:
                        self.currentanimation = "walking"
            elif self.x < player.x:
                self.facing = "right"
                if self.x < player.x - self.shooting_range:
                    self.x += 0.03
                    if self.collide()[0]:
                        self.x = object.collide()[1] - self.hitbox_width
                        self.currentanimation = "static"
                    else:
                        self.currentanimation = "walking"
            if not self.currentanimation == "walking":
                self.currentanimation = "draw"
                if self.animation["draw"][5] >= 4:
                    self.currentanimation = "aim"
                    for list in self.angle_list:
                        if self.angle < list[0] and self.angle > list[1]:
                            self.animation["aim"][5] = list[2]
                    if self.shooting_timer.time() and self.angle > -0.7 and self.angle < 1.3:
                        self.shoot()
            else:
                object.animation["draw"][5] = 0
                self.shooting_timer.timer = 0.8
    def shoot(self):
        pygame.mixer.Sound.play(bullet_sfx)
        if self.facing == "right":
            objects.append(Projectile(self.x + self.angle_list[self.animation["aim"][5]][3], self.y - self.angle_list[self.animation["aim"][5]][4], self.angle, 0.1, textures["bullet"]))
        else:
            objects.append(Projectile(self.x + 0.5 - self.angle_list[self.animation["aim"][5]][3], self.y - self.angle_list[self.animation["aim"][5]][4], -self.angle + math.pi, 0.1, textures["bullet"])) # radians done with chatgpt

class Projectile:
    def __init__(self, x, y, angle, speed, texture):
        self.x = x
        self.y = y 
        self.angle = angle
        self.speed = speed
        self.texture = texture 
        self.width = texture.width / 32
        self.height = texture.height / 32
        self.rotation = angle
        self.hitbox_width = 1/ 32
        self.hitbox_height = 1 / 32
        self.attributes = {"layer" : "3", "collision" : "false"}
        self.despawn_timer = Timer(10)

    def scoords(self):
        return wcoords_translate(self.x, self.y, 1)

    def uv_coords(self):
        return get_uv_coords([False])
    
    def collide(self):
        for object in objects:
            if object.attributes.get("collision") == "true" or object.attributes.get("collision") == None:
                if not object.texture.custom_hitbox == None:
                    with open(object.texture.custom_hitbox) as custom_hitbox:
                        for line in custom_hitbox:
                            line = line.strip()
                            line = line.split()
                            #line: x1, y1 -> x2, y2
                            if self.x + self.hitbox_width > object.x + float(line[0]) and self.x < object.x + float(line[2]) and self.y < object.y + self.hitbox_height - float(line[1]) and self.y > object.y - float(line[3]):
                                return [True, False]
                elif self.x + self.hitbox_width > object.x and self.x < object.x + object.width and self.y < object.y + self.hitbox_height and self.y > object.y - object.height:
                    return [True, False]
            elif object.__class__ == Player:
                if self.x + self.hitbox_width > object.x and self.x < object.x + object.hitbox_width and self.y < object.y + self.hitbox_height and self.y > object.y - object.hitbox_height:
                    return [True, True]
        return [False, False]
    
    def move(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        if self.collide()[0]:
            if self.collide()[1]:
                player.damage(1)
            objects.remove(self)
        if self.despawn_timer.time():
            objects.remove(self)

class Camera:
    def __init__(self):
        self.wcoord_x = player.x - camera_ratio[0]
        self.wcoord_y = player.y + camera_ratio[1]
        self.target_x = player.x - camera_ratio[0]
        self.target_y = player.y + camera_ratio[1]
    def update(self):
        if abs(self.wcoord_x - self.target_x) < 0.05:
            self.wcoord_x = self.wcoord_x - (self.wcoord_x - self.target_x) * 0.25
        else:
            self.wcoord_x = self.wcoord_x - (self.wcoord_x - self.target_x) * 0.1
        if abs(self.wcoord_x - self.target_x) < 0.05:
            self.wcoord_y = self.wcoord_y - (self.wcoord_y - self.target_y) * 0.35
        else:
            self.wcoord_y = self.wcoord_y - (self.wcoord_y - self.target_y) * 0.2
        self.target_x = player.x - camera_ratio[0]
        self.target_y = player.y + camera_ratio[1]
        #x,y -> x,y
        border_list = [(0, 16, 0, 0), (16, 16, 56, 16), (0, 0, 80, 1), (80, 32, 80, 0)]
        for t in border_list:
            blocked = []
            if self.target_y > t[3]:
                blocked.append("up")
            if self.target_y < t[1] + 2 * camera_ratio[1]:
                blocked.append("down")
            if self.target_x + 2 * camera_ratio[0] > t[0]:
                blocked.append("left")
            if self.target_x < t[2]:
                blocked.append("right")

            if "left" in blocked and "right" in blocked and self.target_y > t[3] and self.target_y < t[3] + camera_ratio[1]:
                self.target_y = t[3]
            elif "left" in blocked and "right" in blocked and self.target_y < t[1] + 2 * camera_ratio[1] and self.target_y > t[1] + camera_ratio[1]:
                self.target_y = t[1] + 2 * camera_ratio[1]

            elif "up" in blocked and "down" in blocked and self.target_x + 2 * camera_ratio[0] > t[0] and self.target_x < t[0] - camera_ratio[0]:
                self.target_x = t[0] - 2 * camera_ratio[0]
            elif "up" in blocked and "down" in blocked and self.target_x < t[2] and self.target_x > t[2] - camera_ratio[0]:
                self.target_x = t[2]

            # print(blocked)
            if debug.enabled:
                self.target_x = player.x - camera_ratio[0]
                self.target_y = player.y + camera_ratio[1]

class Debug:
    def __init__(self):
        self.enabled = False
        self.fps = 62.5
        self.font = pygame.font.Font("assets/font/Saira_Stencil/static/SairaStencil-SemiBold.ttf",50)
        self.vertex = np.array([-1.0,  1.0, 0.0, 0, 1, #topleft
                                -1.0, -1.0, 0.0, 0, 0, #bottomleft
                                 1.0,  1.0, 0.0, 1, 1, #topright
                                 1.0, -1.0, 0.0, 1, 0, #bottomright
                                #x, y, z, u = width, v = height
                                ], dtype='f4')
        self.text_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.texture = ctx.texture((screen_width, screen_height), 4)
        self.texture.filter = (ctx.NEAREST, ctx.NEAREST)
        self.texture.use(location=1)
        self.program = ctx.program(
            vertex_shader='''
                #version 330 core
                in vec3 vector;
                in vec2 uv;
                out vec2 v_uv;
                void main() {
                gl_Position = vec4(vector, 1.0);
                v_uv = uv;
                }
                ''',
                fragment_shader='''
                #version 330 core
                in vec2 v_uv;
                out vec4 Colour;
                uniform sampler2D tex;
                void main() {
                Colour = texture(tex, v_uv);
                }
                ''',
        )
        self.program["tex"] = 1
        self.vbo = ctx.buffer(data=self.vertex)
        self.vao = ctx.vertex_array(self.program, [(self.vbo, '3f 2f', 'vector', 'uv')])
    def render(self):
        if self.enabled == True:
            if debug_timer.time():
                self.fps = clock.get_fps()
            for line in self.menu():
                self.text_surface.blit(self.font.render(line, True, "red"), (0, self.menu().index(line) * 60))
            self.texture.write(pygame.image.tobytes(self.text_surface, "RGBA", True))
            self.text_surface.fill((0, 0, 0, 0))
            self.vao.render(mode=moderngl.TRIANGLE_STRIP)
    def menu(self):
        return [
            f"FPS: {round(self.fps)}",
            f"X: {round(player.x, 3)}    Y: {round(player.y, 3)}",
            f"CHUNK: {str(player.chunk())}",
                  ]
class Timer:
    def __init__(self, amount):
        self.timer = 0
        self.amount = amount
    def time(self):
        try:
            self.timer += dt
        except NameError:
            pass
        if self.timer >= self.amount:
            self.timer = 0
            return True
        elif self.timer < self.amount:
            return False
        else:
            print("\033[91m[Error]", datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S:"), "An unknown error ocurred.\033[0m")
            exit()
class PostProcessing:
    def __init__(self):
        self.quad = np.array([ -1.0, 1.0, 0.0, 1.0, #topleft
                               -1.0,-1.0, 0.0, 0.0, #bottomleft
                                1.0, 1.0, 1.0, 1.0, #topright
                                1.0,-1.0, 1.0, 0.0, #bottomright
                                #x, y,
                                ], dtype='f4')
        self.vbo = ctx.buffer(data=self.quad)
        self.brightness = 1.0
        self.target_brightness = 1.0
        self.program = ctx.program(
            vertex_shader='''
            #version 330 core
            in vec2 vector;
            in vec2 uv;
            out vec2 v_uv;

            void main() {
            gl_Position = vec4(vector, 0.0, 1.0);
            v_uv = uv;
            }
            ''',
            fragment_shader='''
            #version 330 core
            uniform vec2 center;
            uniform float radius;
            uniform float smoothness;
            uniform sampler2D tex;
            uniform float brightness;
            in vec2 v_uv;

            void main() {
            float dist = distance(gl_FragCoord.xy, center);
            float noise = fract(sin(dot(gl_FragCoord.xy / dist, vec2(12.9898, 78.233))) * 43758.5453);
            float alpha = mix(0.0, 0.5, (dist / smoothness)) + (0.005 * noise);
            vec3 screen_color = texture(tex, v_uv).rgb;
            vec3 vignette_color = vec3(alpha, alpha, alpha);
            gl_FragColor = vec4((screen_color - vignette_color), 1.0) * vec4(brightness, brightness, brightness, 1.0);
            }
            ''',
            )
        self.vao = ctx.vertex_array(self.program, [(self.vbo, '2f 2f', 'vector', 'uv')])

    def render(self):
        ctx.screen.use()
        fbo.color_attachments[0].use(location=2)
        self.program['tex'] = 2
        self.program["center"].value = screen_width / 2, screen_height / 2
        if screen_width > screen_height:
            self.program["smoothness"].value = 1.78125 * screen_width
        else: 
            self.program["smoothness"].value = 1.78125 * screen_height
        
        self.brightness += (self.target_brightness - self.brightness) * 0.05
        self.program["brightness"].value = self.brightness
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)

# =========================
# Variables, Constants &  & Game Init
# =========================
pygame.init()

pygame.display.set_mode(
    (1280, 720),
    pygame.OPENGL | pygame.DOUBLEBUF
)
pygame.display.set_caption('PhantomSprinter')
pygame.mouse.set_visible(False)
pygame.display.set_icon(pygame.image.load("assets/debug/icon.png"))

ctx = moderngl.create_context()
ctx.enable(moderngl.BLEND) # add transparancy
set_screen_ratio(144)
fbo = ctx.framebuffer(color_attachments=[ctx.texture((screen_width, screen_height), 4)])
postprocessing = PostProcessing()

clock = pygame.time.Clock()
debug_timer = Timer(5)
ctrl = False

pygame.mixer.music.load("assets/sound/music/background_music.ogg")
pygame.mixer.music.play(loops=1, fade_ms=2000)
pygame.mixer.music.set_volume(0.1)

# =========================
# Game Objects
# =========================
assets = {
    #name         : texture path, total frames, animation speed(in fps)
    #debug
    "debug_player": ("assets/debug/player.png",),
    "debug_ground": ("assets/debug/floor.png",),
    "debug_background" : ("assets/debug/bg.png",),
    "debug_sky": ("assets/debug/bg/sky_moon.png",),
    "debug_towers": ("assets/debug/bg/towers.png",),
    "debug_mountains": ("assets/debug/bg/mountains.png",),
    "debug_attack": ("assets/debug/attack.png",),
    "debug_enemy_atlas": ("assets/debug/debug_enemy_atlas.png",),
    "debug_compass": ("assets/debug/compass.png",),
    "debug_box2x": ("assets/debug/box2x.png",),
    "debug_box": ("assets/debug/box.png",),

    #entities
    "player_atlas": ("assets/entities/player/player_atlas_test.png",),
    "pistol_enemy_atlas": ("assets/entities/enemies/pistol_enemy_atlas.png",),
    "bullet": ("assets/entities/projectiles/bullet.png",),

    #terrain
    "brick_16x1": ("assets/environment/terrain/brick_16x1.png",),
    "brick_2x1": ("assets/environment/terrain/brick_2x1.png",),
    "brick_4x1": ("assets/environment/terrain/brick_4x1.png",),
    "stone_2x1_1": ("assets/environment/terrain/stone_2x1_1.png",),
    "stone_2x1_2": ("assets/environment/terrain/stone_2x1_2.png",),
    "stone_3x1": ("assets/environment/terrain/stone_3x1.png",),
    "stone_4x1": ("assets/environment/terrain/stone_4x1.png",),
    "stone_4x2_1": ("assets/environment/terrain/stone_4x2_1.png",),
    "stone_4x2_2": ("assets/environment/terrain/stone_4x2_2.png",),
    "stone_7x2": ("assets/environment/terrain/stone_7x2.png",),
    "stone_6x2": ("assets/environment/terrain/stone_6x2.png",),
    "stone_2x2": ("assets/environment/terrain/stone_2x2.png",),
    "stone_5x1": ("assets/environment/terrain/stone_5x1.png",),
    "wall_1x11": ("assets/environment/terrain/wall_1x11.png",),
    "wall_1x13": ("assets/environment/terrain/wall_1x13.png",),
    "wall_2x11": ("assets/environment/terrain/wall_2x11.png",),
    "wall_2x15": ("assets/environment/terrain/wall_2x15.png",),
    "metal_cargo_2x2": ("assets/environment/terrain/metal_cargo_2x2.png",),
    "rusted_metal_1x1_1": ("assets/environment/terrain/rusted_metal_1x1_1.png",),
    "rusted_metal_1x1_2": ("assets/environment/terrain/rusted_metal_1x1_2.png",),
    
    #custom hitbox
    "stone_9x9": ("assets/environment/terrain/stone_9x9.png", 1, 0, "assets/environment/terrain/stone_9x9.col"),
    "stone_3x2": ("assets/environment/terrain/stone_3x2.png", 1, 0, "assets/environment/terrain/stone_3x2.col"),
    "stone_stair_2x2": ("assets/environment/terrain/stone_stair_2x2.png", 1, 0, "assets/environment/terrain/stone_stair_2x2.col"),
    "wall_11x3": ("assets/environment/terrain/wall_11x3.png", 1, 0, "assets/environment/terrain/wall_11x3.col"),

    #decoration
    "lamp": ("assets/environment/decoration/lamp.png",),
    "block_8": ("assets/environment/decoration/block_8.png",),
    "warning_sign": ("assets/environment/decoration/warning_sign.png",),
    "warning_signpost": ("assets/environment/decoration/warning_signpost.png",),
    #animated
    "rubbish_bin": ("assets/environment/decoration/rubbish_bin_atlas.png", 5, 5),
    "aircon_1x1": ("assets/environment/decoration/aircon_1x1_atlas.png", 3, 30),
    "aircon_2x1": ("assets/environment/decoration/aircon_2x1_atlas.png", 3, 30),
    "burning_barrel_black": ("assets/environment/decoration/burning_barrel_black_atlas.png", 3, 6),
    "burning_barrel_red": ("assets/environment/decoration/burning_barrel_red_atlas.png", 3, 6),
    
    #misc
    "electricity": ("assets/environment/misc/electricity.png", 2, 4),

    #background
    "default_back_wall": ("assets/environment/background/default_back_wall.png",),
    "lightmap_test": ("assets/environment/background/lightmap_test.png",),
}

textures = {}
texture_load()

bullet_sfx = pygame.mixer.Sound("assets/sound/sfx/pulse-shot.wav")

enemies = {
    "debug_enemy" : [Enemy, (textures["debug_enemy_atlas"], 0.6, 1.75,)],
    "pistol_enemy" : [PistolEnemy, (textures["pistol_enemy_atlas"], 0.6, 1.875,)]
}

reset_game()



# =========================
# OpenGL main renderer
# =========================
vertex = np.array([ -1.0, 1.0, 0, 0, #topleft
                    -1.0,-1.0, 0, 1, #bottomleft
                     1.0, 1.0, 1, 0, #topright
                     1.0,-1.0, 1, 1, #bottomright
                    #x, y, u = width, v = height
                    ], dtype='f4')

program = ctx.program(
    vertex_shader='''
    #version 330 core
    in vec2 position;
    in vec2 uv;
    out vec2 v_uv;
    uniform mat4 transform_matrix;
    uniform mat3 uv_transform_matrix;
    void main() {
    gl_Position = vec4(position, 0.0, 1.0) * transform_matrix;
    v_uv = (uv_transform_matrix * vec3(uv, 1.0)).xy;
    }
    ''',
    fragment_shader='''
    #version 330 core
    in vec2 v_uv;
    uniform sampler2D tex;
    void main() {
    gl_FragColor = texture(tex, v_uv);
    }
    ''',
)

vbo = ctx.buffer(data=vertex)
vao = ctx.vertex_array(program, [(vbo, '2f 2f', 'position', 'uv')])
program["tex"] = 0

debug_view = 144

# =========================
# Game Loop
# =========================
while True:

    # INPUT
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.MOUSEWHEEL and debug.enabled:
            debug_view += event.y * -50
            set_screen_ratio(debug_view)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                debug.enabled = not debug.enabled
            if event.key == pygame.K_F4:
                player.noclip = not player.noclip
            if event.key == pygame.K_r and ctrl:
                print("Reloading...")
                objects = [player, debug_sky, debug_towers, debug_mountains]
                loaded_chunks = []

            if event.key == pygame.K_SPACE and player.currentanimation == "static":
                    player.currentanimation = "static_attack"
                    player.attack()
            if event.key == pygame.K_SPACE and player.currentanimation == "walking":
                player.currentanimation = "walking_attack"
                player.attack()

    for object in objects:
        if isinstance(object, Entity):
            if object.currentanimation == "walking":
                object.currentanimation = "static"
            
    key_pressed=pygame.key.get_pressed()
    if key_pressed[pygame.K_LCTRL]:
        ctrl = True
    else:
        ctrl = False
    if key_pressed[pygame.K_RIGHT] and key_pressed[pygame.K_LEFT]:
        pass
    elif key_pressed[pygame.K_RIGHT]:
        player.x += 0.1
        if player.collide()[0] and not player.noclip:
            player.x = player.collide()[1] - player.hitbox_width
        elif player.currentanimation == "static":
            player.facing = "right"
            player.currentanimation = "walking"
        elif player.currentanimation == "walking_attack" and player.animation["walking_attack"][5] > 3 and player.facing == "left":
            player.facing = "right"
            player.currentanimation = "walking"
            player.animation["walking_attack"][5] = 1
    elif key_pressed[pygame.K_LEFT]:
        player.x -= 0.1
        if player.collide()[0] and not player.noclip:
            player.x = player.collide()[2]
        elif player.currentanimation == "static":
            player.facing = "left"
            player.currentanimation = "walking"
            # player.animation["static_attack"][5] = 1
        elif player.currentanimation == "walking_attack" and player.animation["walking_attack"][5] > 3 and player.facing == "right":
            player.facing = "left"
            player.currentanimation = "walking"
            player.animation["walking_attack"][5] = 1
    elif player.currentanimation == "walking_attack" and player.animation["walking_attack"][5] > 3:
            player.currentanimation = "static"
            player.animation["walking_attack"][5] = 1
    if key_pressed[pygame.K_UP] and player.jumping == False and player.noclip == False:
        player.jumping = True
        player.y_velocity = 0.25
    if player.noclip == True:
        if key_pressed[pygame.K_UP]:
            player.y += 0.1
        if key_pressed[pygame.K_DOWN]:
            player.y -= 0.1
            
    # DEBUG
    if player.y < -25:
        exit()

    if debug.enabled == False:
        debug_view = 144
        set_screen_ratio(debug_view)

    

    # UPDATE CHUNKS
    update_loaded_chunks()

    # ENEMY AI (debug)
    for object in objects:
        if object.__class__ == Enemy:
            if abs(object.x - player.x) < 6:
                if object.x > player.x and attack_timer.timer == 0:
                    object.facing = "left"
                    if object.x > player.x + 1.5:
                        object.x -= 0.05
                        if object.collide()[0] and not object.noclip:
                            object.x = object.collide()[2]
                        elif not object.currentanimation == "static_attack":
                            object.currentanimation = "walking"
                            object.animation["static_attack"][5] = 1
                            attack_timer.timer = 0
                elif object.x < player.x and attack_timer.timer == 0:
                    object.facing = "right"
                    if object.x < player.x - 1.5:
                        object.x += 0.05
                        if object.collide()[0] and not object.noclip:
                            object.x = object.collide()[1] - object.hitbox_width
                        elif not object.currentanimation == "static_attack":
                            object.currentanimation = "walking"
                            object.animation["static_attack"][5] = 1
                            attack_timer.timer = 0
                if abs(object.x - player.x) <= 1.5 and object.currentanimation == "static" or not attack_timer.timer == 0:
                    if attack_timer.time():
                        object.currentanimation = "static_attack"
                        object.attack()
    
    for object in objects:
        if object.__class__ == PistolEnemy:
            object.ai()
        if object.__class__ == Projectile:
            object.move()
            

    # COLLISIONS
    for object in objects:
        if isinstance(object, Entity):
            if object.noclip == False and object.ticking:
                object.y += object.y_velocity
                if object.damage_collide():
                    player.damage(1)
                if object.collide()[0] == True:
                    if object.y_velocity < 0: #fall collision
                        object.jumping = False
                        object.y = object.collide()[3] + object.hitbox_height
                    elif player.y_velocity > 0: #head hitting
                        player.y = object.collide()[4]
                    object.y_velocity = 0
                else:
                    if object.y_velocity > -1:
                        object.y_velocity -= 0.01
                        object.jumping = True

    # UPDATE CAMERA
    camera.update() # remove for static cam

    # UPDATE PLAYER
    player.death_update()

    # RENDERING
    fbo.use()
    ctx.clear(0.5, 0, 0.5)
    objects.sort(key=layer_sort, reverse=True)
    for object in objects:
            object.texture.bind()
            uv_coords = object.uv_coords()
            program["uv_transform_matrix"].value = np.array([uv_coords[1], 0.0, 0.0,
                                                            0.0, uv_coords[3], 0.0, 
                                                            uv_coords[0], uv_coords[2], 1.0,
                                                            ], dtype='f4')
            scoords = object.scoords()
            program["transform_matrix"].value = np.array([object.width * screen_ratio[0] * 0.5 * math.cos(object.rotation), -object.height * screen_ratio[0] * 0.5 * math.sin(object.rotation), 0.0, scoords[0] + (object.width * screen_ratio[0] / 2),
                                                          object.width * screen_ratio[1] * 0.5 * math.sin(object.rotation), object.height * screen_ratio[1] * 0.5 * math.cos(object.rotation), 0.0, scoords[1] - (object.height * screen_ratio[1] / 2),
                                                          0.0, 0.0, 1.0, 0.0,
                                                          0.0, 0.0, 0.0, 1.0,
                                                        ], dtype='f4')

            vao.render(mode=moderngl.TRIANGLE_STRIP)

    if debug.enabled: # this whole thing is ugly as fuck:
        for object in objects:
            if isinstance(object, Entity):
                program["uv_transform_matrix"].value = np.array([1.0, 0.0, 0.0,
                                                                0.0, 1.0, 0.0, 
                                                                0.0, 0.0, 1.0,
                                                            ], dtype='f4')
                program["transform_matrix"].value = np.array([object.hitbox_width * screen_ratio[0] * 0.5, 0.0, 0.0, wcoords_translate(object.x, object.y, 1)[0] + (object.hitbox_width * screen_ratio[0] / 2),
                                                        0.0, object.hitbox_height * screen_ratio[1] * 0.5, 0.0, wcoords_translate(object.x, object.y, 1)[1] - (object.hitbox_height * screen_ratio[1] / 2),
                                                        0.0, 0.0, 1.0, 0.0,
                                                        0.0, 0.0, 0.0, 1.0,
                                                        ], dtype='f4')   
                textures["debug_player"].bind()
                vao.render(mode=moderngl.TRIANGLE_STRIP)

                textures["debug_attack"].bind()

                try:
                    if not object.animation["walking_attack"][5] == 1:
                        debug_attack_hitbox_render()
                except:
                    pass
                try:
                    if not object.animation.get["static_attack"][5] == 1:
                        debug_attack_hitbox_render()
                except:
                    pass

    postprocessing.render()
    debug.render()
    pygame.display.flip()
    dt = clock.tick_busy_loop(60) / 1000 # dt is time it takes for one frame