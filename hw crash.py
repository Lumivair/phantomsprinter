import moderngl
from PIL import Image

ctx = moderngl.create_context(standalone=True)


box = Image.open("assets/debug/box.png").convert("RGBA")
box_width, box_height = box.size

for i in range(10000000):
    print(i)
    i = ctx.texture((box_width, box_height), 4, box.tobytes())
    print(i.size)
    

input("Press Enter to continue...")


# program = ctx.program(
#     fragment_shader='''
#     #version 330 core
#     uniform sampler2D box_texture;

#     ''',

# )