import pygame
import moderngl
import sys
import numpy as np
import math
import datetime
from PIL import Image

# =========================
# Functions
# =========================
def exit():
    print(now.strftime("%y-%m-%d %H:%M:%S:"),"Game successfully closed") # exit with success message
    pygame.quit()
    sys.exit()

def set_screen_ratio():
        global screen_ratio
        global camera_ratio
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
                    for line in level:
                        line = line.strip()
                        line = line.split()
                        objects.append(Environment(int(line[1]) + 16 * chunk[0], int(line[2]) + 16 * chunk[1], textures[line[0]]))
                        # for object in objects:
                        #     print(object.x, object.y, object.texture.width, object.texture.texture)
                new_chunks = []
            except FileNotFoundError:
                pass

def texture_load():
    for texture in assets:
        textures.update({texture : AssetManager(assets[texture])})

# =========================
# Classes
# =========================
class AssetManager:
    def __init__(self, texture_path):
        with Image.open(texture_path) as image:
            self.texture = image.convert("RGBA")
            self.width = self.texture.size[0]
            self.height = self.texture.size[1]
        self.texture_raw = ctx.texture((self.width, self.height), 4, self.texture.tobytes())
        self.texture_raw.filter = (ctx.NEAREST, ctx.NEAREST)
    def bind(self):
        self.texture_raw.use(location=2)

class Environment:
    def __init__(self, x, y, texture):
        self.x = x
        self.y = y
        self.width = texture.width / 32
        self.height = texture.height / 32
        self.texture = texture
    def scoords(self):
        return wcoords_translate(self.x, self.y)
    def rect(self):
        pass # WIP
        # return self.texture.get_rect(topleft=(self.scoords()))

class Entity:
    def __init__(self, name, x, y, texture_path, width, height):
        self.name = name
        self.x = x
        self.y = y
        self.y_velocity = 0
        self.jumping = False
        self.noclip = True
        self.width = width
        self.height = height
        self.texture = Image.open(texture_path).convert("RGBA")
        self.texture_raw = ctx.texture((32, 64), 4, self.texture.tobytes())
        self.texture_raw.filter = (ctx.NEAREST, ctx.NEAREST)
        self.texture_raw.use(location=0)
        self.vertex = np.array([0.0,  0.0, 0.0, 0, 1, #topleft
                                0.0, 0.0 - self.height, 0.0, 0, 0, #bottomleft
                                self.width, 0.0, 0.0, 1, 1, #topright
                                self.width,  0.0 - self.height, 0.0, 1, 0, #bottomright
                                #x, y, z, u = width, v = height
                                ], dtype='f4')
    def scoords(self):
        return wcoords_translate(self.x, self.y)
    def chunk(self):
        return chunk_translate(self.x, self.y)
    def rect(self):
        # return pygame.Rect(self.scoords(), (self.width, self.height)) # causes vibrations, maybe fix in future for custom hitbox?
        return self.texture.get_rect(topleft=(self.scoords()))

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
        self.text_surface = pygame.Surface((pygame.display.get_window_size()), pygame.SRCALPHA)
        self.texture = ctx.texture(pygame.display.get_window_size(), 4)
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
    def update(self):
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
            f"X: {round(player.x, 1)}    Y: {round(player.y, 1)}",
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
            print("An unknown error ocurred")
            exit()

# =========================
# Variables, Constants &  & Game Init
# =========================
pygame.init()

pygame.display.set_mode(
    (2560, 500),
    pygame.OPENGL | pygame.DOUBLEBUF
)
ctx = moderngl.create_context()
ctx.enable(moderngl.BLEND) # add transparancy

set_screen_ratio()
clock = pygame.time.Clock()
now = datetime.datetime.now() # set variable now to time
debug_timer = Timer(0.1)

# =========================
# Game Objects
# =========================
assets = {
    "debug_ground": "assets/debug/floor.png",
    "box2x": "assets/debug/box2x.png",
    "box": "assets/debug/box.png",
    "floor": "assets/environment/floors/floor1.png",
    "wall1": "assets/environment/walls/wall1.png",
    "wall2": "assets/environment/walls/wall2.png"
}
textures = {}
texture_load()

camera = Camera()
player = Entity("hanspeter", 8, 8, "assets/debug/player.png", screen_ratio[0], screen_ratio[1] * 2)
debug = Debug()
objects = []
new_chunks = []
loaded_chunks = []

# =========================
# OpenGL
# =========================
entity_program = ctx.program(
    vertex_shader='''
    #version 330 core
    in vec3 vector;
    in vec2 uv;
    out vec2 v_uv;
    uniform vec3 player_position;
    void main() {
    gl_Position = vec4(vector + player_position, 1.0);
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

player_vbo = ctx.buffer(data=player.vertex)
player_vao = ctx.vertex_array(entity_program, [(player_vbo, '3f 2f', 'vector', 'uv')])
entity_program["tex"] = 0

environment_vertex = np.array([  0.0, 0.0, 0, 1, #topleft
                                 0.0,-1.0, 0, 0, #bottomleft
                                 1.0, 0.0, 1, 1, #topright
                                 1.0,-1.0, 1, 0, #bottomright
                                #x, y, u = width, v = height
                                ], dtype='f4')

environment_program = ctx.program(
    vertex_shader='''
    #version 330 core
    in vec2 position;
    in vec2 uv;
    out vec2 v_uv;
    uniform mat4 transform_matrix;
    void main() {
    gl_Position = transform_matrix * vec4(position, 0.0, 1.0);
    v_uv = uv;
    }
    ''',
    fragment_shader='''
    #version 330 core
    in vec2 v_uv;
    out vec4 Colour;
    uniform sampler2D env_tex;
    void main() {
    Colour = texture(env_tex, v_uv);
    }
    ''',
)

environment_vbo = ctx.buffer(data=environment_vertex)
environment_vao = ctx.vertex_array(environment_program, [(environment_vbo, '2f 2f', 'position', 'uv')])
environment_program["env_tex"] = 2

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
    
    key_pressed=pygame.key.get_pressed()
    if key_pressed[pygame.K_RIGHT]:
        player.x += 0.1
    if key_pressed[pygame.K_LEFT]:
        player.x -= 0.1
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

    # UPDATE CAMERA
    camera.update() # remove for static cam
    # UPDATE PLAYER
    entity_program["player_position"].value = [player.scoords()[0], player.scoords()[1], 0]

    # RENDERING
    ctx.clear(0.5, 0, 0.5)
    player_vao.render(mode=moderngl.TRIANGLE_STRIP)
    
    # to be improved:
    for object in objects:
        object.texture.bind()
        environment_program["transform_matrix"].value = np.array([  (object.width * screen_ratio[0]), 0.0, 0.0, 0.0,
                                                                    0.0, (object.height * screen_ratio[1]), 0.0, 0.0,
                                                                    0.0, 0.0, 1.0, 0.0,
                                                                    object.scoords()[0], object.scoords()[1], 0.0, 1.0,
                                                                    ], dtype='f4')
        environment_vao.render(mode=moderngl.TRIANGLE_STRIP)
    
    debug.update()
    pygame.display.flip()
    dt = clock.tick_busy_loop(60) / 1000 # dt is time it takes for one frame