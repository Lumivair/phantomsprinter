#ifndef WINDOW_H
#define WINDOW_H

#include <GLFW/glfw3.h>

int window_init(int width, int height, char* title);



int window_init(int width, int height, char* title) {
    if (!glfwInit()) {
        return 0;
    }
}

#endif // WINDOW_H