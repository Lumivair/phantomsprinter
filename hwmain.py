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
def exit():
    print("[Info]", datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S:"),"Game successfully closed") # exit with success message
    pygame.quit()
    sys.exit()

def layer_sort(object):
    return object.attributes["layer"]

def set_screen_ratio():
        global screen_ratio
        global camera_ratio
        global screen_width
        global screen_height
        screen_size = pygame.display.get_window_size()
        screen_width = screen_size[0]
        screen_height = screen_size[1]
        ratio_multiplier = math.sqrt(144/(screen_width * screen_height))
        screen_ratio = [(1 / (screen_width * ratio_multiplier) * 2), (1 / (screen_height * ratio_multiplier) * 2)]
        camera_ratio = [(screen_width * ratio_multiplier) / 2 - 0.5, (screen_height * ratio_multiplier) / 2 + 0.5]

def wcoords_translate(x, y):
    return[(x - camera.wcoord_x) * screen_ratio[0] - 1, (y - camera.wcoord_y) * screen_ratio[1] + 1]

def chunk_translate(x, y):
    return [math.floor(x / 16), math.floor(y / 16)]

def update_loaded_chunks():
    new_chunks = []
    new_chunks.append(player.chunk())
    new_chunks.append([player.chunk()[0] + 1, player.chunk()[1]])
    new_chunks.append([player.chunk()[0] -1 , player.chunk()[1]]) # FIX if bored, make it smarter and not just all chunks next to player
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
                            parameters = line[3]
                            parameters = parameters.strip("{}")
                            parameters = parameters.split(";")
                            parameter_dict = {}
                            for i in range(len(parameters)):
                                parameter_dict.update({parameters[i].split("=")[0]: parameters[i].split("=")[1]})
                            objects.append(Environment(int(line[1]) + 16 * chunk[0], int(line[2]) + 16 * chunk[1], textures[line[0]], parameter_dict))
                        except IndexError:
                            try:
                                objects.append(Environment(int(line[1]) + 16 * chunk[0], int(line[2]) + 16 * chunk[1], textures[line[0]], {"layer": "1"}))
                            except:
                                print("\033[91m[Error]", datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S:"),f"Line {i + 1} in PhantomSprinter Mapping System chunk [{chunk[0]},{chunk[1]}] is corrupted.\033[0m")
                new_chunks = []
            except FileNotFoundError:
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
        if parameter_list[6].time():
            parameter_list[5] += 1
        if parameter_list[5] >= frames: #TODO fix this whole thing where all the first frames in animation are not actually the first and are completely cooked
            parameter_list[5] = 0
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
        try:
            self.frames = texture_properties[1]
            self.fps = texture_properties[2]
            self.animated = True
        except IndexError:
            self.frames = 1
            self.fps = 0
            self.animated = False
    def bind(self):
        self.texture_raw.use(location=0)

class Environment:
    def __init__(self, x, y, texture, attribute_dict):
        self.x = x
        self.y = y
        self.width = texture.width / 32 / texture.frames + 0.005
        self.height = texture.height / 32 + 0.005
        self.texture = texture
        self.attributes = attribute_dict
        try:
            self.animation_timer = Timer(1 / self.texture.fps)
            self.current_animation_frame = 0
            #is not fullscreen texture?, start x coord of texture, width/step of x, frames, total_width, current animation frame, animation timer, height, total height, facing, offset x
            self.animation = [self.texture.animated, 0, self.texture.width / self.texture.frames, self.texture.frames, self.texture.width, self.current_animation_frame, self.animation_timer, self.texture.height, self.texture.height]
        except:
            self.animation = [self.texture.animated]
    def scoords(self):
        return wcoords_translate(self.x, self.y)
    def uv_coords(self):
        return get_uv_coords(self.animation)

class Entity:
    def __init__(self, x, y, texture, width, height):
        self.x = x
        self.y = y
        self.y_velocity = 0
        self.jumping = False
        self.noclip = False
        self.health = 1
        self.width = width
        self.height = height
        self.hitbox_width = width
        self.hitbox_height = height
        self.attack_hitbox_width = 2.2
        self.attack_hitbox_height = 1.2
        self.texture = texture
        self.facing = "right"
        self.attributes = {"collision": "false", "layer" : "2", "gravity": "true"}
        self.currentanimation = "static"
        self.animation = {
            #is not fullscreen texture?, start x coord of texture, width/step of x, frames, total_width, current animation frame, animation timer, height, total height, facing, offset x, repeating
            "static" : [True, 0, 42, 1, self.texture.width, 0, Timer(5), 59, 59, self.facing, 0,],
            "walking" : [True, 67, 67, 12, self.texture.width, 0, Timer(1 / 12), 53, 59, self.facing, -0.75,],
            "attack" : [True, 871, 119, 8, self.texture.width, 1, Timer(1 / 24), 59, 59, self.facing, -1.5,],
        }

    def uv_coords(self):
        if self.currentanimation == "attack":
            if self.animation[self.currentanimation][5] == 0:
                self.animation[self.currentanimation][5] = 1
                self.currentanimation = "static"
        self.animation[self.currentanimation][9] = self.facing
        if self.facing == "left": # <---- this is shit
            self.animation["static"][10] = -0.1
        else:
            self.animation["static"][10] = -0.6
        self.width = self.animation[self.currentanimation][2] / 32
        return get_uv_coords(self.animation[self.currentanimation])
        
    def scoords(self):
        return wcoords_translate(self.x + self.animation[self.currentanimation][10], self.y)
        
    def chunk(self):
        return chunk_translate(self.x, self.y)
    def collide(self):
        for object in objects:
            try:
                if object.attributes["collision"] == "true":
                    if self.x > object.x - self.hitbox_width and self.x < object.x + object.width and self.y < object.y + self.hitbox_height and self.y > object.y - object.height:
                        return [True, object]
            except KeyError:
                if self.x > object.x - self.hitbox_width and self.x < object.x + object.width and self.y < object.y + self.hitbox_height and self.y > object.y - object.height:
                        return [True, object]
        return [False, None]
    def attack(self):
        if self.facing == "right":
            for object in objects:
                if not object.__class__ == self.__class__ and not object.__class__ == Environment:
                    if self.x + self.attack_hitbox_width > object.x and self.x < object.x + object.hitbox_width and self.y - self.attack_hitbox_height < object.y and self.y > object.y - object.hitbox_height:
                        object.damage(1)
        if self.facing == "left":
            for object in objects:
                if not object.__class__ == self.__class__ and not object.__class__ == Environment:
                    if self.x - self.attack_hitbox_width < object.x and self.x > object.x + object.hitbox_width and self.y - self.attack_hitbox_height < object.y and self.y > object.y - object.hitbox_height:
                        object.damage(1)

class Player(Entity):
    def __init__(self, x, y, texture, width, height, name):
        super().__init__(x, y, texture, width, height) 
        self.name = name
    def damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            exit()
class Enemy(Entity):
    def __init__(self, x, y, texture, width, height):
        super().__init__(x, y, texture, width, height) 
    def damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            global debug_enemy
            debug_enemy = None
            objects.remove(self)
class Camera:
    def __init__(self):
        self.wcoord_x = 0
        self.wcoord_y = 0
    def update(self):
        self.wcoord_x = player.x - camera_ratio[0]
        self.wcoord_y = player.y + camera_ratio[1]
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
            in vec2 v_uv;
            out vec4 fragColor;

            void main() {
            float dist = distance(gl_FragCoord.xy, center);
            float noise = fract(sin(dot(gl_FragCoord.xy / dist, vec2(12.9898, 78.233))) * 43758.5453);
            float alpha = mix(0.0, 1.0, (dist / smoothness)) + (0.005 * noise);
            vec3 screen_color = texture(tex, v_uv).rgb;
            vec3 vignette_color = vec3(alpha, alpha, alpha);
            fragColor = vec4((screen_color - vignette_color), 1.0);
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
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)

# =========================
# Variables, Constants &  & Game Init
# =========================
pygame.init()

pygame.display.set_mode(
    (1280, 720),
    pygame.OPENGL | pygame.DOUBLEBUF
)
ctx = moderngl.create_context()
ctx.enable(moderngl.BLEND) # add transparancy
set_screen_ratio()
fbo = ctx.framebuffer(color_attachments=[ctx.texture((screen_width, screen_height), 4)])
postprocessing = PostProcessing()

pygame.mouse.set_visible(False)
clock = pygame.time.Clock()
debug_timer = Timer(0.1)

# =========================
# Game Objects
# =========================
assets = {
    #name         : texture path, total frames, animation speed(in fps)
    "debug_player": ("assets/debug/player.png",),
    "debug_ground": ("assets/debug/floor.png",),
    "debug_attack": ("assets/debug/attack.png",),
    "debug_enemy_atlas": ("assets/debug/debug_enemy_atlas.png",),
    "compass": ("assets/debug/compass.png",),
    "player_static": ("assets/entities/player/static.png",),
    "player_atlas": ("assets/entities/player/player_atlas.png",),
    "box2x": ("assets/debug/box2x.png",),
    "box": ("assets/debug/box.png",),
    "floor": ("assets/environment/floors/floor1.png",),
    "wall1": ("assets/environment/walls/wall1.png",),
    "wall2": ("assets/environment/walls/wall2.png",),
    "wall3": ("assets/environment/walls/wall3.png",),
    "3x2_a": ("assets/environment/platforms/3x2_a.png",),
    "3x2_b": ("assets/environment/platforms/3x2_b.png",),
    "lamp": ("assets/environment/misc/lamp-spill.png",),
    "rubbish_bin": ("assets/environment/misc/rubbish_bin.png", 5, 5),
}
textures = {}
texture_load()

camera = Camera()
player = Player(26, 3, textures["player_atlas"], 0.6, 1.75, "hanspeter")
debug_enemy = Enemy(8, 2.75, textures["debug_enemy_atlas"], 0.6, 1.75)

debug = Debug()
objects = [player, debug_enemy]

new_chunks = []
loaded_chunks = []

# =========================
# OpenGL main renderer
# =========================
vertex = np.array([ 0.0, 0.0, 0, 0, #topleft
                    0.0,-1.0, 0, 1, #bottomleft
                    1.0, 0.0, 1, 0, #topright
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
    gl_Position = transform_matrix * vec4(position, 0.0, 1.0);
    v_uv = (uv_transform_matrix * vec3(uv, 1.0)).xy;
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

vbo = ctx.buffer(data=vertex)
vao = ctx.vertex_array(program, [(vbo, '2f 2f', 'position', 'uv')])
program["tex"] = 0

# =========================
# Game Loop
# =========================
while True:

    # INPUT
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                debug.enabled = not debug.enabled
            if event.key == pygame.K_F4:
                player.noclip = not player.noclip
            if event.key == pygame.K_SPACE and player.currentanimation == "static":
                    player.currentanimation = "attack"
                    player.attack()
            if event.key == pygame.K_f and debug_enemy.currentanimation == "static":
                debug_enemy.currentanimation = "attack"
                debug_enemy.attack()

    if not player.currentanimation == "attack":
        player.currentanimation = "static"
    key_pressed=pygame.key.get_pressed()
    if key_pressed[pygame.K_RIGHT]:
        player.x += 0.1
        if player.collide()[0] and not player.noclip:
            player.x = player.collide()[1].x - player.hitbox_width
        elif not player.currentanimation == "attack":
            player.facing = "right"
            player.currentanimation = "walking"
            player.animation["attack"][5] = 1
    if key_pressed[pygame.K_LEFT]:
        player.x -= 0.1
        if player.collide()[0] and not player.noclip:
            player.x = player.collide()[1].x + player.collide()[1].width
        elif not player.currentanimation == "attack":
            player.facing = "left"
            player.currentanimation = "walking"
            player.animation["attack"][5] = 1
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

    # UPDATE CHUNKS
    update_loaded_chunks()

    # COLLISIONS
    if player.noclip == False:
        player.y += player.y_velocity
        if player.collide()[0] == True:
            if player.y_velocity < 0: #fall collision
                player.jumping = False
                player.y = player.collide()[1].y + player.hitbox_height
            elif player.y_velocity > 0: #head hitting
                player.y = player.collide()[1].y - player.collide()[1].height
            player.y_velocity = 0
        else:
            if player.y_velocity > -1:
                player.y_velocity -= 0.01
                player.jumping = True

    # UPDATE CAMERA
    camera.update() # remove for static cam

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
            program["transform_matrix"].value = np.array([(object.width * screen_ratio[0]), 0.0, 0.0, 0.0,
                                                        0.0, (object.height * screen_ratio[1]), 0.0, 0.0,
                                                        0.0, 0.0, 1.0, 0.0,
                                                        scoords[0], scoords[1], 0.0, 1.0,
                                                        ], dtype='f4')

            vao.render(mode=moderngl.TRIANGLE_STRIP)

    if debug.enabled: # this whole thing is ugly as fuck:
        for object in objects:
            if object.__class__ == Player or object.__class__ == Enemy:
                program["uv_transform_matrix"].value = np.array([1.0, 0.0, 0.0,
                                                                0.0, 1.0, 0.0, 
                                                                0.0, 0.0, 1.0,
                                                            ], dtype='f4')
                program["transform_matrix"].value = np.array([(object.hitbox_width * screen_ratio[0]), 0.0, 0.0, 0.0,
                                                        0.0, (object.hitbox_height * screen_ratio[1]), 0.0, 0.0,
                                                        0.0, 0.0, 1.0, 0.0,
                                                        wcoords_translate(object.x, object.y)[0], wcoords_translate(object.x, object.y)[1], 0.0, 1.0,
                                                        ], dtype='f4')   
                textures["debug_player"].bind()
                vao.render(mode=moderngl.TRIANGLE_STRIP)

                textures["debug_attack"].bind()
                if not object.animation["attack"][5] == 1:
                    if object.facing == "right":
                        program["transform_matrix"].value = np.array([(object.attack_hitbox_width * screen_ratio[0]), 0.0, 0.0, 0.0,
                                                                0.0, (object.attack_hitbox_height * screen_ratio[1]), 0.0, 0.0,
                                                                0.0, 0.0, 1.0, 0.0,
                                                                wcoords_translate(object.x, object.y)[0], wcoords_translate(object.x, object.y)[1], 0.0, 1.0,
                                                                ], dtype='f4')   
                    else:
                        program["transform_matrix"].value = np.array([(- object.attack_hitbox_width * screen_ratio[0]), 0.0, 0.0, 0.0,
                                                                0.0, (object.attack_hitbox_height * screen_ratio[1]), 0.0, 0.0,
                                                                0.0, 0.0, 1.0, 0.0,
                                                                wcoords_translate(object.x + object.hitbox_width, object.y)[0], wcoords_translate(object.x, object.y)[1], 0.0, 1.0,
                                                                ], dtype='f4')   
                    vao.render(mode=moderngl.TRIANGLE_STRIP)

    postprocessing.render()
    debug.render()
    pygame.display.flip()
    dt = clock.tick_busy_loop(60) / 1000 # dt is time it takes for one frame