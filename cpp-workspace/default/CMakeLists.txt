cmake_minimum_required(VERSION 3.21)

# Add hot reload support for MSVC compiler if available.
if (POLICY CMP0141)
	cmake_policy(SET CMP0141 NEW)
	set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()


project("#cpp#" VERSION 1.0 LANGUAGES CXX)

if (MSVC)
	add_compile_options(/source-charset:utf-8)
endif()

file(GLOB SRCS CONFIGURE_DEPENDS "source/*.cpp")

add_executable(${PROJECT_NAME} ${SRCS})
target_include_directories(${PROJECT_NAME} PRIVATE include)

