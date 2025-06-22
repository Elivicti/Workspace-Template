#pragma once

#include <iostream>
#include <format>

template<typename... Args>
void print(std::ostream& os, std::format_string<Args...> fmt, Args&&... args)
{
	std::format_to(std::ostreambuf_iterator{ os }, fmt, std::forward<Args>(args)...);
}

template<typename... Args>
void print(std::format_string<Args...> fmt, Args&&... args)
{
	print(std::cout, fmt, std::forward<Args>(args)...);
}

#ifdef _WIN32
#include <Windows.h>
#define WIN32_ENSURE_CODEPAGE(cp)    \
static struct Win32_CodePageSetter { \
	UINT OG_InputCP;  \
	UINT OG_OutputCP; \
	Win32_CodePageSetter()  \
		: OG_InputCP{ GetConsoleCP() }        \
		, OG_OutputCP{ GetConsoleOutputCP() } \
	{ SetConsoleCP(cp); SetConsoleOutputCP(cp); } \
	~Win32_CodePageSetter() { SetConsoleCP(OG_InputCP); SetConsoleOutputCP(OG_OutputCP); } \
} win32_console_codepage_setter{}
#else
#define WIN32_ENSURE_CODEPAGE(cp) // only useful on windows
#endif

