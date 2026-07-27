cmake_minimum_required(VERSION 3.23)
project(phantomsprinter)


find_package(OpenGL REQUIRED)
find_package(glfw3 REQUIRED)

add_executable(PhantomSprinter
	main.c
	glad.c
)

target_include_directories(PhantomSprinter PRIVATE include)

target_link_libraries(PhantomSprinter PRIVATE
	glfw
	OpenGL::GL
)
