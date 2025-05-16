cmake_minimum_required(VERSION 3.21)

file(GLOB HEADERS CONFIGURE_DEPENDS "${INCLUDE_DIR}/*.h")
file(GLOB SRCS    CONFIGURE_DEPENDS "*.cpp")

qt_add_executable(
	${PROJECT_NAME}
		${SRCS}
		${HEADERS}
)

target_link_libraries(
	${PROJECT_NAME}
	PRIVATE
		Qt6::Widgets
)

# Disables console window on Windows if ENABLE_CONSOLE is set to OFF (Qt Specific)
if (NOT ${ENABLE_CONSOLE})
	set_target_properties(
		${PROJECT_NAME}
		PROPERTIES
			WIN32_EXECUTABLE ON
	)
endif()
