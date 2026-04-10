# main PhantomSprinter game

# imports
import pygame


# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True

# asset setup
font = pygame.font.Font("assets/font/Saira_Stencil/static/SairaStencil-SemiBold.ttf", 50)


# reset variables
debug = False
player_x = 0
player_y = 0

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
    if key[pygame.K_LEFT]:
        player_x -= 0.1

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")
    debug_menu = font.render(f"X: {round(player_x, 1)}    Y: {round(player_y, 1)}", True, "red")
    # RENDER YOUR GAME HERE
    
    if debug == True:
        screen.blit(debug_menu, (0,0))
    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()