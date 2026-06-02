import pygame
import moderngl
import sys
import numpy as np

pygame.init()
pygame.display.set_mode((500, 500), pygame.OPENGL | pygame.DOUBLEBUF| pygame.RESIZABLE, vsync=1)
ctx = moderngl.create_context()
ctx.enable(moderngl.BLEND)

fullscreen_quad = np.array([ -1.0, 1.0, #topleft
                               -1.0,-1.0, #bottomleft
                                1.0, 1.0, #topright
                                1.0,-1.0, #bottomright
                                #x, y,
                                ], dtype='f4')
vbo = ctx.buffer(data=fullscreen_quad)


program = ctx.program(
    vertex_shader='''
    #version 330 core
    in vec2 position;

    void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    }
    ''',
    fragment_shader='''
    #version 330 core
    uniform vec2 center;
    uniform float radius;
    uniform float smoothness;
    out vec4 fragColor;

    void main() {
    float dist = distance(gl_FragCoord.xy, center);
    float noise = fract(sin(dot(gl_FragCoord.xy / floor(dist), vec2(12.9898, 78.233))) * 43758.5453);
    float alpha = mix(0.0, 1.0, (dist / smoothness)) + (0.05 * noise);
    fragColor = vec4(0.0, 0.0, 0.0, alpha);

    }
    ''',
)

vao = ctx.vertex_array(program, vbo, 'position')


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    ctx.clear(0.4, 0, 0.6)
    program["center"].value = pygame.display.get_window_size()[0] / 2, pygame.display.get_window_size()[1] / 2
    if pygame.display.get_window_size()[0] > pygame.display.get_window_size()[1]:
        program["smoothness"].value = 0.78125 * pygame.display.get_window_size()[0]
    else: 
        program["smoothness"].value = 0.78125 * pygame.display.get_window_size()[1]

    vao.render(mode=moderngl.TRIANGLE_STRIP)



    pygame.display.flip()
