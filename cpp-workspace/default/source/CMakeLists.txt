cmake_minimum_required(VERSION 3.21)

file(GLOB SRCS CONFIGURE_DEPENDS "*.cpp")

add_executable(${PROJECT_NAME} ${SRCS})

# Disables console window on Windows if ENABLE_CONSOLE is set to OFF (Qt Specific)
# if (NOT ${ENABLE_CONSOLE})
# 	set_target_properties(
# 		${PROJECT_NAME}
# 		PROPERTIES
# 			WIN32_EXECUTABLE ON
# 	)
# endif()