#include "../NutCracker/src/Actions.h"

void _py_Decompile(const std::string& source, const std::string& dest)
{
	std::ofstream stream;
	stream.open(dest);
	if (!stream)
		throw std::runtime_error("Failed to open file");
	Decompile(source.c_str(), NULL, stream);
}

void _py_DecompileFunction(const std::string& source, const std::string& dest, const std::string& debug_function)
{

	std::ofstream stream;
	stream.open(dest);
	if (!stream)
		throw std::runtime_error("Failed to open file");
	Decompile(source.c_str(), debug_function.c_str(), stream);
}
