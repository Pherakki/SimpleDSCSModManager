#include "Actions.h"
#include <cstring>

const char* version = "0.03";
const char* nutVersion = "2.2.4 64-bit";

void Usage( void )
{
	std::cout << "NutCracker Squirrel script decompiler, ver " << version << std::endl;
	std::cout << "for binary nut file version " << nutVersion << std::endl;
	std::cout << std::endl;
	std::cout << "  Usage:" << std::endl;
	std::cout << "    nutcracker [options] <file to decompile>" << std::endl;
	std::cout << "    nutcracker -cmp <file1> <file2>" << std::endl;
	std::cout << std::endl;
	std::cout << "  Options:" << std::endl;
	std::cout << "   -h         Display usage info" << std::endl;
	std::cout << "   -cmp       Compare two binary files" << std::endl;
	std::cout << "   -d <name>  Display debug decompilation for function" << std::endl;
	std::cout << std::endl;
	std::cout << std::endl;
}


int stricmpWrapper(char* in, const char* cmp) {
	#ifdef __linux__
		return strncasecmp(in, cmp, sizeof(cmp));
	#elif _WIN32
		return _stricmp(in, cmp);
	#endif
}

int main( int argc, char* argv[] )
{
	const char* debugFunction = NULL;

	for( int i = 1; i < argc; ++i)
	{
		if (0 == stricmpWrapper(argv[i], "-h"))
		{
			Usage();
			return 0;
		}
		else if (0 == stricmpWrapper(argv[i], "-d"))
		{
			if ((argc - i) < 2)
			{
				Usage();
				return -1;
			}
			debugFunction = argv[i + 1];
			i += 1;
		}
		else if (0 == stricmpWrapper(argv[i], "-cmp"))
		{
			if ((argc - i) < 3)
			{
				Usage();
				return -1;
			}
			return Compare(argv[i + 1], argv[i + 2], false);
		}
		else if (0 == stricmpWrapper(argv[i], "-cmpg"))
		{
			if ((argc - i) < 3)
			{
				Usage();
				return -1;
			}
			return Compare(argv[i + 1], argv[i + 2], true);
		}
		else
		{
			return Decompile(argv[i], debugFunction, std::cout);
		}
	}


	Usage();
	return -1;
}
