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
find_package(Qt6 REQUIRED COMPONENTS Widgets)
qt6_standard_project_setup()

if(CMAKE_BUILD_TYPE STREQUAL "Release")
	set(DISABLE_CONSOLE ON)
endif()

set(INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include")
include_directories(include)
add_subdirectory(source)
