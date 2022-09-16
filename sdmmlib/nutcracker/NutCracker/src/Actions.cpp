#include "Actions.h"


int Compare(const char* file1, const char* file2, bool general)
{
	try
	{
		NutScript s1, s2;
		s1.LoadFromFile(file1);
		s2.LoadFromFile(file2);

		if (general)
		{
			std::ofstream nullStream("null");
			bool result = s1.GetMain().DoCompare(s2.GetMain(), "", nullStream);

			if (result)
				std::cout << "[         ]";
			else
				std::cout << "[! ERROR !]";

			std::cout << " : " << file1 << std::endl;

			return result ? 0 : -1;
		}
		else
		{
			bool result = s1.GetMain().DoCompare(s2.GetMain(), "", std::cout);
			std::cout << std::endl << "Result: " << (result ? "Ok" : "ERROR") << std::endl;

			return result ? 0 : -1;
		}
	}
	catch (std::exception& ex)
	{
		std::cout << "Error: " << ex.what() << std::endl;
		return -1;
	}
}


void DebugFunctionPrint(const NutFunction& function, std::ostream& out)
{
	g_DebugMode = true;
	function.GenerateFunctionSource(0, out);
}


int Decompile(const char* file, const char* debugFunction, std::ostream& out)
{
	try
	{
		NutScript script;
		script.LoadFromFile(file);

		if (debugFunction)
		{
			if (0 == strcmp(debugFunction, "main"))
			{
				DebugFunctionPrint(script.GetMain(), out);
				return 0;
			}
			else
			{
				const NutFunction* func = script.GetMain().FindFunction(debugFunction);
				if (!func)
				{
					throw std::exception(("Unable to find function \"" + std::string(debugFunction) + "\".").c_str());
					return -2;
				}

				DebugFunctionPrint(*func, out);
				return 0;
			}
		}

		script.GetMain().GenerateBodySource(0, out);
	}
	catch (std::exception& ex)
	{
		out << "Error: " << ex.what() << std::endl;
		return -1;
	}

	return 0;
}
