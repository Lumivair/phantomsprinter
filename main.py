# main PhantomSprinter game

# imports
import pygame


# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
pygame.display.set_caption("PhantomSprinter") # set windows title to learning_python

# asset setup
font = pygame.font.Font("assets/font/Saira_Stencil/static/SairaStencil-SemiBold.ttf", 50)
ground = pygame.image.load("assets/debug/floor.png")
ground = pygame.transform.scale_by(ground, 4)
player = pygame.image.load("assets/debug/player.png")
player = pygame.transform.scale_by(player, 4)

# reset variables
debug = False
player_x = 0
player_y = 0
ground_x = 0

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                if debug == True:
                    debug = False
                elif debug == False:
                    debug = True


    key=pygame.key.get_pressed()
    if key[pygame.K_RIGHT]:
        player_x += 0.1
        ground_x -= 6
    if key[pygame.K_LEFT]:
        player_x -= 0.1
        ground_x += 6

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")
    debug_menu = font.render(f"X: {round(player_x, 1)}    Y: {round(player_y, 1)}", True, "red")
    # RENDER YOUR GAME HERE
    
    if debug == True:
        screen.blit(debug_menu, (0,0))
        
    # flip() the display to put your work on screen
    screen.blit(ground, (ground_x,552))
    screen.blit(player, (100,100))
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()