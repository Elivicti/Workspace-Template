cmake_minimum_required(VERSION 3.21)

# Add hot reload support for MSVC compiler if available.
if (POLICY CMP0141)
	cmake_policy(SET CMP0141 NEW)
	set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()

project("#cpp#" VERSION 1.0 LANGUAGES CXX)

option(BUILD_EXAMPLE "build examples" ${PROJECT_IS_TOP_LEVEL})

if (MSVC)
	add_compile_options(/source-charset:utf-8)
	set(CMAKE_DEBUG_POSTFIX d)
endif()

include(GenerateExportHeader)
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)
include(cmake/helpers.cmake)

set(PROJECT_NAMESPACE ${PROJECT_NAME})
set(PROJECT_COMPONENTS)

add_subdirectory(#cpp#)

foreach(comp ${PROJECT_COMPONENTS})
	add_library(${PROJECT_NAMESPACE}::${comp} ALIAS ${comp})
	target_compile_options(${comp} PUBLIC $<$<CXX_COMPILER_ID:MSVC>:/Zc:preprocessor>)

	if(NOT MSVC)
		continue()
	endif()

	get_target_property(comp_type ${comp} TYPE)
	if (comp_type STREQUAL "SHARED_LIBRARY")
		install(
			FILES $<TARGET_PDB_FILE:${comp}>
			DESTINATION ${CMAKE_INSTALL_BINDIR}
			CONFIGURATIONS Debug RelWithDebInfo
			OPTIONAL
		)
	endif()
endforeach()

if (BUILD_EXAMPLE)
	add_subdirectory(example)
endif()


# --- install rules --- #
configure_package_config_file(
	${CMAKE_CURRENT_SOURCE_DIR}/cmake/config.cmake.in
	${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake
	INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
	PATH_VARS CMAKE_INSTALL_INCLUDEDIR
)
write_basic_package_version_file(
	${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake
	VERSION       ${PROJECT_VERSION}
	COMPATIBILITY SameMajorVersion
)

install(TARGETS ${PROJECT_COMPONENTS}
	EXPORT ${PROJECT_NAME}Targets
	LIBRARY DESTINATION ${CMAKE_INSTALL_BINDIR}
	RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
	ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
	PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
install(EXPORT ${PROJECT_NAME}Targets
	FILE ${PROJECT_NAME}Targets.cmake
	NAMESPACE   ${PROJECT_NAMESPACE}::
	DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
)
install(FILES
	${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake
	${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake
	DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
)
