#pragma once

#include "NutScript.h"
#include <iostream>
#include <fstream>

int Compare(const char* file1, const char* file2, bool general);
void DebugFunctionPrint(const NutFunction& function, std::ostream& out);
int Decompile(const char* file, const char* debugFunction, std::ostream& out);
