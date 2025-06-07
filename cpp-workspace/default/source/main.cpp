#include "header.hpp"

#ifdef _WIN32
#include <Windows.h>
static struct CodePageSetter
{
	UINT OG_InputCP;
	UINT OG_OutputCP;

	CodePageSetter()
		: OG_InputCP{ GetConsoleCP() }
		, OG_OutputCP{ GetConsoleOutputCP() }
	{
		SetConsoleCP(CP_UTF8);
		SetConsoleOutputCP(CP_UTF8);
	}
	~CodePageSetter()
	{
		SetConsoleCP(OG_InputCP);
		SetConsoleOutputCP(OG_OutputCP);
	}
} win32_console_codepage_setter{};
#endif

int main(int argc, char* argv[])
{
	print("Hello, World!\n");

	return 0;
}