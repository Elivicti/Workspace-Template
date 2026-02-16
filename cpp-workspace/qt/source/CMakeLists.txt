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


# --- install rules --- #
if (WIN32)
	install(TARGETS ${PROJECT_NAME}
		BUNDLE  DESTINATION .
		RUNTIME DESTINATION .
	)
	qt6_generate_deploy_script(
		TARGET ${PROJECT_NAME}
		OUTPUT_SCRIPT deploy_script
		CONTENT "
set(QT_DEPLOY_BIN_DIR .)
qt_deploy_runtime_dependencies(
	EXECUTABLE $<TARGET_FILE_NAME:${PROJECT_NAME}>
)
"
	)
else()
	install(TARGETS ${PROJECT_NAME}
		BUNDLE  DESTINATION .
		RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
	)
	qt6_generate_deploy_app_script(
		TARGET ${PROJECT_NAME}
		OUTPUT_SCRIPT deploy_script
		NO_UNSUPPORTED_PLATFORM_ERROR
	)
endif()

install(SCRIPT ${deploy_script})
