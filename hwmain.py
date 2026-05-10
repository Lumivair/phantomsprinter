import pygame
import moderngl
import sys
import numpy as np
import math
from PIL import Image

pygame.init()

pygame.display.set_mode(
    (1280, 720),
    pygame.OPENGL | pygame.DOUBLEBUF
)



ctx = moderngl.create_context()
ctx.enable(moderngl.BLEND) # add transparancy

def get_screen_ratio():
        screen_size = pygame.display.get_window_size()
        screen_width = screen_size[0]
        screen_height = screen_size[1]
        ratio_multiplier = math.sqrt(144/(screen_width * screen_height))
        ratio = [(1 / (screen_width * ratio_multiplier) * 2), (1 / (screen_height * ratio_multiplier) * 2)]
        return ratio

def wcoords_translate(x, y):
    return[(x + camera.wcoord_x) * get_screen_ratio()[0] - 1, (y - camera.wcoord_y) * get_screen_ratio()[1] + 1]
    #return [(-1 +((x - camera.wcoord_x) * get_screen_ratio()[0])) / 2 , (1 +((camera.wcoord_y * -1 + y) * get_screen_ratio()[1])) / 2]


class Entity:
    def __init__(self, name, x, y, texture_path, width, height):
        self.name = name
        self.x = x
        self.y = y
        self.y_velocity = 0
        self.jumping = False
        self.noclip = False
        self.width = width
        self.height = height
        self.texture = Image.open(texture_path).convert("RGBA")
        self.texture_raw = ctx.texture((32, 64), 4, self.texture.tobytes())
        self.texture_raw.filter = (ctx.NEAREST, ctx.NEAREST)
        self.texture_raw.use(location=0)
        self.vertex = np.array([self.scoords()[0],  self.scoords()[1], 0.0, 0, 1, #topleft
                                self.scoords()[0], self.scoords()[1] - self.height, 0.0, 0, 0, #bottomleft
                                self.scoords()[0] + self.width, self.scoords()[1], 0.0, 1, 1, #topright
                                self.scoords()[0] + self.width,  self.scoords()[1] - self.height, 0.0, 1, 0, #bottomright
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
        self.wcoord_y = 13

camera = Camera()
player = Entity("hanspeter", 8, 8, "assets/debug/player.png", get_screen_ratio()[0], get_screen_ratio()[1] * 2)

print(get_screen_ratio()[0])
print(wcoords_translate(player.x, player.y))

program = ctx.program(
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
    uniform sampler2D box_texture;
    void main() {
    Colour = texture(box_texture, v_uv);
    }
    ''',

)


vbo = ctx.buffer(data=player.vertex)
vao = ctx.vertex_array(program, [(vbo, '3f 2f', 'vector', 'uv')])

clock = pygame.time.Clock()


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    key_pressed=pygame.key.get_pressed()
    if key_pressed[pygame.K_RIGHT]:
        player.x += 0.1
    if key_pressed[pygame.K_LEFT]:
        player.x -= 0.1
    program['player_position'].value = [player.scoords()[0], player.scoords()[1], 0]
    print([player.scoords()[0], player.scoords()[1], 0])
    ctx.clear(0.5, 0, 0.5)
    vao.render(mode=moderngl.TRIANGLE_STRIP)
    pygame.display.flip()

    clock.tick_busy_loop(60)
    #print(f"fps: {clock.get_fps()}")
    
    