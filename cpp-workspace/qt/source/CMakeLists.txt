cmake_minimum_required(VERSION 3.21)

file(GLOB HEADERS CONFIGURE_DEPENDS "${INCLUDE_DIR}/*.h")
file(GLOB SRCS    CONFIGURE_DEPENDS "*.cpp")
file(GLOB UI      CONFIGURE_DEPENDS "ui/*.ui")

qt6_add_executable(
	${PROJECT_NAME}
		${SRCS}
		${HEADERS}
		${UI}
)

target_link_libraries(
	${PROJECT_NAME}
	PRIVATE
		Qt6::Widgets
)

if (WIN32 AND DISABLE_CONSOLE)
	# Disables console window on Windows
	set_target_properties(${PROJECT_NAME} PROPERTIES WIN32_EXECUTABLE ON)
endif()
