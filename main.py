# main PhantomSprinter game

# imports
import pygame
import sys
import datetime


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

class Entity:
    def __init__(self, name, x, y, texture_path, scale_factor, width, height):
        self.name = name
        self.x = x
        self.y = y
        self.y_velocity = 0
        self.standing = False
        self.width = width
        self.height = height
        self.texture = pygame.image.load(texture_path)
        self.texture = pygame.transform.scale_by(self.texture, scale_factor)
    def scoords(self):
        return wcoords_translate(self.x, self.y)
    def rect(self):
        return pygame.Rect(self.scoords(), (self.width, self.height))


class Environment:
    def __init__(self, x, y, texture_path, scale_factor):
        self.x = x
        self.y = y
        self.texture = pygame.image.load(texture_path)
        self.texture = pygame.transform.scale_by(self.texture, scale_factor)
        self.width = self.texture.get_size()[0]
        self.height = self.texture.get_size()[1]
    def scoords(self):
        return wcoords_translate(self.x, self.y)
    def rect(self):
        return self.texture.get_rect(topleft=(self.scoords()))



class Camera:
    def __init__(self):
        self.wcoord_x = -8
        self.wcoord_y = 7

pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
now = datetime.datetime.now() # set variable now to time

print(get_screen_ratio())

pygame.display.set_caption("PhantomSprinter") # set window title

# asset setup
font = pygame.font.Font("assets/font/Saira_Stencil/static/SairaStencil-SemiBold.ttf", 50)
debug = False
noclip = False

# class setup:
ground = Environment(-6, 0, "assets/debug/floor.png", get_screen_ratio())
box2x = Environment(1, 2, "assets/debug/box2x.png", get_screen_ratio())
box = Environment(-2, 3, "assets/debug/box.png", get_screen_ratio())

player = Entity("hanspeter", -0.5, 2, "assets/debug/player.png", get_screen_ratio(), 32 * get_screen_ratio(), 64 * get_screen_ratio())
camera = Camera()
objects = [ground, box, box2x]



while True:
    
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit(print(now.strftime("%y-%m-%d %H:%M:%S:"),"Game successfully closed")) # exit with success message
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                if debug == True:
                    debug = False
                elif debug == False:
                    debug = True
            if event.key == pygame.K_F4:
                if noclip == True:
                    noclip = False
                elif noclip == False:
                    noclip = True
                    player.standing = False


    key_pressed=pygame.key.get_pressed()
    if key_pressed[pygame.K_RIGHT]:
        player.x += 0.1
    if key_pressed[pygame.K_LEFT]:
        player.x -= 0.1
    if noclip == True:
        if key_pressed[pygame.K_UP]:
            player.y += 0.2
        if key_pressed[pygame.K_DOWN]:
            player.y -= 0.2
    
    
    

    camera.wcoord_x = player.x - ((pygame.display.get_window_size()[0] / 64 / get_screen_ratio()) - 0.5)
    camera.wcoord_y = player.y + ((pygame.display.get_window_size()[1] / 64 / get_screen_ratio()) + 0.5)
    print((pygame.display.get_window_size()[0] / 64 / get_screen_ratio_exact()[0]) - 0.5)
    print(player.width)
    print(get_screen_ratio_exact()[0])
    print(pygame.display.get_window_size()[0])
    # camera.wcoord_x = -7 #static camera
    # camera.wcoord_y = 5 
    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")
    debug_menu = font.render(f"X: {round(player.x, 1)}    Y: {round(player.y, 1)}", True, "red")
    # RENDER YOUR GAME HERE
    
    if debug == True:
        screen.blit(debug_menu, (0,0))
    


    # flip() the display to put your work on screen
    screen.blit(ground.texture, (ground.scoords()))
    screen.blit(box2x.texture, (box2x.scoords()))
    screen.blit(box.texture, (box.scoords()))
    screen.blit(player.texture, (player.scoords()))

    if not player.rect().colliderect(ground.rect()) and noclip == False and player.standing == False:
        player.y -= player.y_velocity
        if player.y_velocity < 1:
            player.y_velocity += 0.01
    if player.rect().colliderect(ground.rect()) and noclip == False:
        player.y_velocity = 0
        player.y = ground.y + player.height / (32 * get_screen_ratio())
        player.standing = True
    
    pygame.display.flip()
    clock.tick(60)  # limits FPS to 60

