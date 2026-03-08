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

target_compile_definitions(
	${PROJECT_NAME}
	PRIVATE
		PROJECT_NAME="${PROJECT_NAME}"
		PROJECT_VERSION="${PROJECT_VERSION}"
)

set(QT6_LUPDATE_OPTIONS -no-obsolete)
if(Qt6_VERSION VERSION_GREATER_EQUAL "6.9.0")
	qt6_add_translations(
		${PROJECT_NAME}
		TS_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/translations
		LUPDATE_OPTIONS ${QT6_LUPDATE_OPTIONS}
	)
else()
	set(TS_FILES)
	foreach(lang IN LISTS QT6_I18N_TRANSLATED_LANGUAGES)
		list(APPEND TS_FILES ${CMAKE_CURRENT_SOURCE_DIR}/translations/${PROJECT_NAME}_${lang}.ts)
	endforeach()
	qt6_add_translations(${PROJECT_NAME}
		TS_FILES ${TS_FILES}
		LUPDATE_OPTIONS ${QT6_LUPDATE_OPTIONS}
	)
endif()

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
