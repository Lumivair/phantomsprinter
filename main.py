# =========================
# IMPORTS
# =========================
import pygame
import sys
import datetime
import math

# =========================
# Functions
# =========================
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
                        objects.append(Environment(int(line[1]) + 16 * chunk[0], int(line[2]) + 16 * chunk[1], assets[line[0]]))
                new_chunks = []
            except FileNotFoundError:
                pass
            
def exit():
    print(now.strftime("%y-%m-%d %H:%M:%S:"),"Game successfully closed") # exit with success message
    pygame.quit()
    sys.exit()

def horizontal_collision_check():
    if player.noclip == False:
        for object in objects:
            if player.rect().colliderect(object.rect()):
                return True

def vertical_collision_check():
    for object in objects:
        if player.rect().colliderect(object.rect()):
            global vertical_collide_object
            vertical_collide_object = object
            return True

def get_screen_ratio():
        screen_size = pygame.display.get_window_size()
        screen_width = screen_size[0]
        screen_height = screen_size[1]
        ratio = (screen_width / 512 + screen_height / 288) / 2
        return ratio

def get_screen_ratio_exact():
        screen_size = pygame.display.get_window_size()
        return [screen_size[0] / 512, screen_size[1] / 288]

def wcoords_translate(x, y):
    return [(camera.wcoord_x * -1 + x) * 32 * get_screen_ratio() , (camera.wcoord_y + y * -1) * 32 * get_screen_ratio()]

def chunk_translate(x, y):
    return [math.floor(x / 16), math.floor(y / 16)]

# =========================
# Classes
# =========================
class Entity:
    def __init__(self, name, x, y, texture_path, scale_factor, width, height):
        self.name = name
        self.x = x
        self.y = y
        self.y_velocity = 0
        self.jumping = False
        self.noclip = False
        self.width = width
        self.height = height
        self.texture = pygame.image.load(texture_path)
        self.texture = pygame.transform.scale_by(self.texture, scale_factor)
    def scoords(self):
        return wcoords_translate(self.x, self.y)
    def chunk(self):
        return chunk_translate(self.x, self.y)
    def rect(self):
        # return pygame.Rect(self.scoords(), (self.width, self.height)) # causes vibrations, maybe fix in future for custom hitbox?
        return self.texture.get_rect(topleft=(self.scoords()))

class Environment:
    def __init__(self, x, y, texture):
        self.x = x
        self.y = y
        self.texture = texture
        self.texture = pygame.transform.scale_by(self.texture, get_screen_ratio())
        self.width = self.texture.get_size()[0]
        self.height = self.texture.get_size()[1]
    def scoords(self):
        return wcoords_translate(self.x, self.y)
    def rect(self):
        return self.texture.get_rect(topleft=(self.scoords()))

class Camera:
    def __init__(self):
        self.wcoord_x = 0
        self.wcoord_y = 13
    def update(self):
        self.wcoord_x = player.x - ((pygame.display.get_window_size()[0] / 64 / get_screen_ratio()) - 0.5)
        self.wcoord_y = player.y + ((pygame.display.get_window_size()[1] / 64 / get_screen_ratio()) + 0.5)

# =========================
# Variables & Constants
# =========================
pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("PhantomSprinter") # set window title
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()
now = datetime.datetime.now() # set variable now to time
running = True
debug = False

# =========================
# Game Objects
# =========================
assets = {
    "font": pygame.font.Font("assets/font/Saira_Stencil/static/SairaStencil-SemiBold.ttf", 50),
    "debug_ground": pygame.image.load("assets/debug/floor.png"),
    "box2x": pygame.image.load("assets/debug/box2x.png"),
    "box": pygame.image.load("assets/debug/box.png")
}

player = Entity("hanspeter", 8, 8, "assets/debug/player.png", get_screen_ratio(), 32 * get_screen_ratio(), 64 * get_screen_ratio())
camera = Camera()
objects = []
new_chunks = []
loaded_chunks = []

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
                debug = not debug
            if event.key == pygame.K_F4:
                player.noclip = not player.noclip
    
    key_pressed=pygame.key.get_pressed()
    if key_pressed[pygame.K_RIGHT]:
        player.x += 0.1
        if horizontal_collision_check():
            player.x -= 0.1
    if key_pressed[pygame.K_LEFT]:
        player.x -= 0.1
        if horizontal_collision_check():
            player.x += 0.1
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
    screen.fill("purple")
    debug_menu = [
        f"X: {round(player.x, 1)}    Y: {round(player.y, 1)}",
        f"Chunk: {str(player.chunk())}"
                  ]

    # UPDATE CHUNKS
    update_loaded_chunks()

    # COLLISIONS
    if player.noclip == False:
        player.y += player.y_velocity
        if vertical_collision_check() == True:
            if player.y_velocity < 0: #fall collision
                player.jumping = False
                player.y = vertical_collide_object.y + player.height / (32 * get_screen_ratio())
            elif player.y_velocity > 0: #head hitting
                player.y = vertical_collide_object.y - vertical_collide_object.height / (32 * get_screen_ratio())
            player.y_velocity = 0
        else:
            if player.y_velocity > -1:
                player.y_velocity -= 0.01
                player.jumping = True

    # UPDATE CAMERA
    camera.update() # remove for static cam        

    # RENDERING
    for object in objects:
        screen.blit(object.texture, (object.scoords()))
    screen.blit(player.texture, (player.scoords()))
    if debug == True:
        for line in debug_menu:
            screen.blit(assets["font"].render(line, True, "red"), (0, debug_menu.index(line) * 60))
    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)