#include <stdio.h>
#include <stdlib.h>

#define GLFW_INCLUDE_NONE
#include <glad/glad.h>
#include <GLFW/glfw3.h>

void error_callback(int error, const char* description)
{
    fprintf(stderr, "Error: %s\n", description);
}


int main () {
    printf("hello world\n");
    printf("nvim");
    
    glfwSetErrorCallback(error_callback);
    if (!glfwInit()) {
        printf("\033[91m[Error] An unknown error ocurred. code=67\033[0m\n");
        exit(1);
    }

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_RESIZABLE, GL_FALSE);
    
    GLFWwindow* window = glfwCreateWindow(800, 800, "test", NULL, NULL);
    if (!window) {
        printf("\033[91m[Error] An unknown error ocurred. code=69\033[0m\n");
        exit(1);
    }

    glfwMakeContextCurrent(window);
    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        printf("Failed to initialize GLAD\n");
        return -1;
        }
    
    
    glClearColor(0.5f, 0.0f, 0.5f, 1.0f);
    // glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_HIDDEN);

    while (!glfwWindowShouldClose(window)) {
        glClear(GL_COLOR_BUFFER_BIT);
        glfwPollEvents();
        glfwSwapBuffers(window);
    }

    
    glfwDestroyWindow(window);
    glfwTerminate();
    return 0;
}
