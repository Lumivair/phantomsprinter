import pygame
import moderngl
import sys
import numpy as np

pygame.init()

pygame.display.set_mode(
    (1280, 720),
    pygame.OPENGL | pygame.DOUBLEBUF
)

ctx = moderngl.create_context()
vertice = np.array([ -0.5, -0.5, 0.0, 0.5, 0.0, 1.0,
                      0.5, -0.5, 0.0, 1.0, 0.0, 0.0,
                      0.0,  0.5, 0.0, 0.0, 1.0, 0.0,], dtype='f4')
vertice2 = np.array([ -1.0,  1.0, 0.0, 0.1, 0.0, 0.7, 
                      -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 
                       0.0,  0.0, 0.0, 0.2, 0.5, 0.0, ], dtype='f4')

program = ctx.program(
    vertex_shader='''
    #version 330 core
    in vec3 vector;
    in vec3 colour;
    out vec3 v_colour;
    void main() {
    gl_Position = vec4(vector, 1.0);
    v_colour = colour;
    }
    ''',
    fragment_shader='''
    #version 330 core
    in vec3 v_colour;
    out vec4 Colour;
    void main() {
    Colour = vec4(v_colour, 1.0);
    }
    ''',

)


vbo1 = ctx.buffer(data=vertice)
vbo2 = ctx.buffer(data=vertice2)
vao1 = ctx.vertex_array(program, [(vbo1, '3f 3f', 'vector', 'colour')])
vao2 = ctx.vertex_array(program, [(vbo2, '3f 3f', 'vector', 'colour')])


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    ctx.clear(0.5, 0, 0.5)
    vao1.render()
    vao2.render()
    pygame.display.flip()
    