cmake_minimum_required(VERSION 3.21)

add_executable(example main.cpp)

target_link_libraries(example ${PROJECT_NAME}::#cpp#)
