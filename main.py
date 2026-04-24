# main PhantomSprinter game

# imports
import pygame
import sys



def get_screen_ratio():
        screen_size = pygame.display.get_window_size()
        screen_width = screen_size[0]
        screen_height = screen_size[1]
        ratio = [screen_width / 512, screen_height / 288]
        return ratio
def wcoords_translate(x, y):
    return [(camera.wcoord_x * -1 + x) * 32 * get_screen_ratio()[0] , (camera.wcoord_y + y * -1) * 32 * get_screen_ratio()[1]]

class Entity:
    def __init__(self, name, x, y, texture_path, scale_factor, width, height):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.texture = pygame.image.load(texture_path)
        self.texture = pygame.transform.scale_by(self.texture, scale_factor)
    def scoords(self):
        return wcoords_translate(self.x, self.y)
    def rect(self):
        return pygame.Rect(self.scoords(), (self.width, self.height))
player = Entity("hanspeter", -0.5, 2, "assets/debug/player.png", 3.75, 120, 240)

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

ground = Environment(-6, 0, "assets/debug/floor.png", 3.75)
box2x = Environment(1, 2, "assets/debug/box2x.png", 3.75)
box = Environment(-2, 3, "assets/debug/box.png", 3.75)

class Camera:
    def __init__(self):
        self.wcoord_x = -8
        self.wcoord_y = 7

camera = Camera()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1920, 1080))
        self.clock = pygame.time.Clock()
        self.running = True
      
        print(get_screen_ratio())
        
        pygame.display.set_caption("PhantomSprinter") # set window title

        # asset setup
        self.font = pygame.font.Font("assets/font/Saira_Stencil/static/SairaStencil-SemiBold.ttf", 50)
        self.debug = False
        self.noclip = False
        

    def run(self):
        while True:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3:
                        if self.debug == True:
                            self.debug = False
                        elif self.debug == False:
                            self.debug = True
                    if event.key == pygame.K_F4:
                        if self.noclip == True:
                            self.noclip = False
                        elif self.noclip == False:
                            self.noclip = True


            key_pressed=pygame.key.get_pressed()
            if key_pressed[pygame.K_RIGHT]:
                camera.wcoord_x += 0.1
                player.x += 0.1
            if key_pressed[pygame.K_LEFT]:
                camera.wcoord_x -= 0.1
                player.x -= 0.1
            if self.noclip == True:
                if key_pressed[pygame.K_UP]:
                    camera.wcoord_y += 0.1
                    player.y += 0.1
                if key_pressed[pygame.K_DOWN]:
                    camera.wcoord_y -= 0.1
                    player.y -= 0.1

            # fill the screen with a color to wipe away anything from last frame
            self.screen.fill("purple")
            self.debug_menu = self.font.render(f"X: {round(player.x, 1)}    Y: {round(player.y, 1)}", True, "red")
            # RENDER YOUR GAME HERE
            
            if self.debug == True:
                self.screen.blit(self.debug_menu, (0,0))
            


            # flip() the display to put your work on screen
            self.screen.blit(ground.texture, (ground.scoords()))
            self.screen.blit(box2x.texture, (box2x.scoords()))
            self.screen.blit(box.texture, (box.scoords()))
            self.screen.blit(player.texture, (player.scoords()))

            
            if player.rect().colliderect(ground.rect()):
                print("col")
                print(ground.rect())
                print(player.rect())
            pygame.display.flip()


            self.clock.tick(60)  # limits FPS to 60
Game().run()