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
    print(now.strftime("%y-%m-%d %H:%M:%S:"),"Game successfully closed") # exit with success message
    pygame.quit()
    sys.exit()

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
                    for line in level:
                        line = line.strip()
                        line = line.split()
                        collision_objects.append(Environment(int(line[1]) + 16 * chunk[0], int(line[2]) + 16 * chunk[1], textures[line[0]]))

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
        self.texture_raw.use(location=0)

class Environment:
    def __init__(self, x, y, texture):
        self.x = x
        self.y = y
        self.width = texture.width / 32
        self.height = texture.height / 32
        self.texture = texture
        self.uv_x = 1.0
        self.uv_width = 1.0
        self.uv_y = 1.0
        self.uv_height = 1.0
    def scoords(self):
        return wcoords_translate(self.x, self.y)

class Entity:
    def __init__(self, name, x, y, texture, width, height):
        self.name = name
        self.x = x
        self.y = y
        self.y_velocity = 0
        self.jumping = False
        self.noclip = False
        self.width = width
        self.height = height
        self.hitbox_width = width
        self.hitbox_height = height
        self.texture = texture
        self.facing = "right"
        self.frames = 13
        self.uv_x = 1
        self.uv_width = 1
        self.uv_y = 1
        self.uv_height = 1
        self.animation = {
                    #x start, x end, x offset(in world coords), y height, step, frames
            "static" : (0, 23, 0, 59, 23, 1),
            "walking" : (67, 871, -0.67, 53, 67, 12)
        }
        self.currentanimation = ["static", 1]
        self.animation_timer = Timer(0.0833333333333)
    def setuvcoords(self):
        current_animation_type = self.animation[self.currentanimation[0]]
        current_animation_frame = self.currentanimation[1]
        self.uv_x = current_animation_type[0] / self.texture.texture.size[0]
        self.uv_height = current_animation_type[3] / self.texture.texture.size[1] # change this to uv_y for more accurate and no scaling
        self.uv_width = current_animation_type[4] / self.texture.texture.size[0]
        self.width = current_animation_type[4] / 32
        if player.facing == "left":
                self.uv_width = self.uv_width * -1
                self.uv_x = current_animation_type[0] / self.texture.texture.size[0] - self.uv_width
        if current_animation_type[5] > 1:
            self.uv_x = (current_animation_type[0] * current_animation_frame) / self.texture.texture.size[0]
            if current_animation_frame >= 12:
                self.currentanimation[1] = 1
            elif self.animation_timer.time():
                self.currentanimation[1] += 1
            if player.facing == "left":
                self.uv_x = (current_animation_type[0] * current_animation_frame) / self.texture.texture.size[0] - self.uv_width

    def scoords(self):
        return wcoords_translate(self.x + self.animation[self.currentanimation[0]][2], self.y)
        
    def chunk(self):
        return chunk_translate(self.x, self.y)
    def collide(self):
        for object in collision_objects:
            if self.x > object.x - self.hitbox_width and self.x < object.x + object.width and self.y < object.y + self.hitbox_height and self.y > object.y - object.height:
                return [True, object]
        return [False, None]

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
            print("An unknown error ocurred")
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
now = datetime.datetime.now() # set variable now to time
debug_timer = Timer(0.1)

# =========================
# Game Objects
# =========================
assets = {
    "debug_player": "assets/debug/player.png",
    "debug_ground": "assets/debug/floor.png",
    "player": "assets/entities/player/static.png",
    "player_moving": "assets/entities/player/player_atlas.png",
    "box2x": "assets/debug/box2x.png",
    "box": "assets/debug/box.png",
    "compass": "assets/debug/compass.png",
    "floor": "assets/environment/floors/floor1.png",
    "wall1": "assets/environment/walls/wall1.png",
    "wall2": "assets/environment/walls/wall2.png",
    "wall3": "assets/environment/walls/wall3.png",
    "3x2_a": "assets/environment/platforms/3x2_a.png",
    "3x2_b": "assets/environment/platforms/3x2_b.png",
    "lamp": "assets/environment/misc/lamp-spill.png",
}
textures = {}
texture_load()

camera = Camera()
player = Entity("hanspeter", 8, 8, textures["player_moving"], 0.71875, 1.75)

debug = Debug()
collision_objects = []
objects = [player]

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
    player.currentanimation[0] = "static"
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
        player.facing = "right"
        player.x += 0.1
        if player.collide()[0] and not player.noclip:
            player.x = player.collide()[1].x - player.hitbox_width
        else:
            player.currentanimation[0] = "walking"
    if key_pressed[pygame.K_LEFT]:
        player.facing = "left"
        player.x -= 0.1
        if player.collide()[0] and not player.noclip:
            player.x = player.collide()[1].x + player.collide()[1].width
        else:
            player.currentanimation[0] = "walking"

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
    player.setuvcoords()
    
   
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
    for object in objects + collision_objects:
        object.texture.bind()
        program["transform_matrix"].value = np.array([              (object.width * screen_ratio[0]), 0.0, 0.0, 0.0,
                                                                    0.0, (object.height * screen_ratio[1]), 0.0, 0.0,
                                                                    0.0, 0.0, 1.0, 0.0,
                                                                    object.scoords()[0], object.scoords()[1], 0.0, 1.0,
                                                                    ], dtype='f4')
        program["uv_transform_matrix"].value = np.array([object.uv_width, 0.0, 0.0,
                                                         0.0, object.uv_height, 0.0, 
                                                         object.uv_x, object.uv_y, 1.0,
                                                        ], dtype='f4')
        vao.render(mode=moderngl.TRIANGLE_STRIP)
    postprocessing.render()
    debug.render()
    pygame.display.flip()
    dt = clock.tick_busy_loop(60) / 1000 # dt is time it takes for one frame