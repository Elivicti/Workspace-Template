cmake_minimum_required(VERSION 3.21)

# Add hot reload support for MSVC compiler if available.
if (POLICY CMP0141)
	cmake_policy(SET CMP0141 NEW)
	set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()


project("#cpp#" VERSION 1.0 LANGUAGES CXX)

set(CMAKE_INCLUDE_CURRENT_DIR ON)

# Qt project required settings
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
find_package(Qt6 REQUIRED COMPONENTS Widgets LinguistTools)

set(QT6_I18N_SOURCE_LANGUAGE en)
set(QT6_I18N_TRANSLATED_LANGUAGES zh_CN)

if(Qt6_VERSION VERSION_GREATER_EQUAL "6.9.0")
	qt6_standard_project_setup(
		I18N_SOURCE_LANGUAGE      ${QT6_I18N_SOURCE_LANGUAGE}
		I18N_TRANSLATED_LANGUAGES ${QT6_I18N_TRANSLATED_LANGUAGES}
	)
else()
	qt6_standard_project_setup()
endif()

if(CMAKE_BUILD_TYPE STREQUAL "Release")
	set(DISABLE_CONSOLE ON)
endif()

set(INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include")
include_directories(include)
add_subdirectory(source)
add_subdirectory(resources)
