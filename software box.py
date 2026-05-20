import pygame
import sys
import numpy as np
from PIL import Image

pygame.init()
screen = pygame.display.set_mode((1000, 1000))
box = pygame.image.load("assets/debug/box.png")
box = pygame.transform.scale_by(box, 10)
clock = pygame.time.Clock()
box_x, box_y = 300, 300

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    key_pressed=pygame.key.get_pressed()
    if key_pressed[pygame.K_RIGHT]:
         box_x += 1
    if key_pressed[pygame.K_LEFT]:
         box_x -= 1
    screen.fill("purple")
    screen.blit(box, (box_x, box_y))
    pygame.display.flip()

    clock.tick_busy_loop()
    print(f"fps: {clock.get_fps()}")