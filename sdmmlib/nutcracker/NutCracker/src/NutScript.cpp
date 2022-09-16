
#include <iostream>
#include <sstream>
#include <fstream>
#include <string>

#include <stdint.h>

#include "Errors.h"
#include "NutScript.h"
#include "BinaryReader.h"

using namespace std;

bool g_DebugMode = false;

// ***************************************************************************************************************
const NutFunction* NutFunction::FindFunction( const std::string& name ) const
{
	string localName, subName;
	unsigned int p = name.find("::");

	if (p == std::string::npos)
	{
		localName = name;
	}
	else
	{
		localName = name.substr(0, p);
		subName = name.substr(p + 2);
	}

	if (localName.empty())
		return NULL;

	int pos = -1;

	if (localName[0] >= '0' && localName[0] <= '9')
	{
		pos = atoi(localName.c_str());
	}
	else
	{
		for(size_t i = 0; i < m_Functions.size(); ++i)
			if (m_Functions[i].m_Name == name)
			{
				pos = (int)i;
				break;
			}
	}

	if (pos < 0 || pos >= (int)m_Functions.size())
		return NULL;

	if (subName.empty())
		return &m_Functions[pos];
	else
		return m_Functions[pos].FindFunction(subName);
}


// ***************************************************************************************************************
const NutFunction& NutFunction::GetFunction( int i ) const
{
	if (i < 0 || i >= (int)m_Functions.size())
		throw Error("Invalid index in GetFunction.");

	return m_Functions[i];
}


// ***************************************************************************************************************
void NutFunction::Load( BinaryReader& reader )
{
	reader.ConfirmOnPart();

	reader.ReadSQStringObject(m_SourceName);
	reader.ReadSQStringObject(m_Name);

	reader.ConfirmOnPart();
	
	int64_t nLiterals = reader.ReadInt64();
	int64_t nParameters = reader.ReadInt64();
	int64_t nOuterValues = reader.ReadInt64();
	int64_t nLocalVarInfos = reader.ReadInt64();
	int64_t nLineInfos = reader.ReadInt64();
	int64_t nDefaultParams = reader.ReadInt64();
	int64_t nInstructions = reader.ReadInt64();
	int64_t nFunctions = reader.ReadInt64();
	
	reader.ConfirmOnPart();

	m_Literals.resize((size_t) nLiterals);
	for(int i = 0; i < nLiterals; ++i)
		m_Literals[i].Load(reader);

	reader.ConfirmOnPart();
	
	m_Parameters.resize((size_t) nParameters);
	for(int i = 0; i < nParameters; ++i)
		reader.ReadSQStringObject(m_Parameters[i]);

	reader.ConfirmOnPart();

	m_OuterValues.resize((size_t) nOuterValues);
	for(int i = 0; i < nOuterValues; ++i)
	{
		m_OuterValues[i].type = reader.ReadInt32();
		m_OuterValues[i].src.Load(reader);
		m_OuterValues[i].name.Load(reader);
	}

	reader.ConfirmOnPart();

	m_Locals.resize((size_t) nLocalVarInfos);
	for(int i = 0; i < nLocalVarInfos; ++i)
	{
		reader.ReadSQStringObject(m_Locals[i].name);
		m_Locals[i].pos = reader.ReadInt64();
		m_Locals[i].start_op = reader.ReadInt64();
		m_Locals[i].end_op = reader.ReadInt64();
		m_Locals[i].foreachLoopState = false;
	}

	reader.ConfirmOnPart();

	m_LineInfos.resize((size_t) nLineInfos);
	reader.Read(&(m_LineInfos.front()), nLineInfos * sizeof(LineInfo));

	reader.ConfirmOnPart();
	
	m_DefaultParams.resize((size_t) nDefaultParams);
	if (nDefaultParams)
	{
		reader.Read(&(m_DefaultParams.at(0)), nDefaultParams * sizeof(int));
	}

	reader.ConfirmOnPart();

	m_Instructions.resize((size_t) nInstructions);
	if (nInstructions)
	{
		reader.Read(&(m_Instructions.at(0)), nInstructions * sizeof(Instruction));
	}

	reader.ConfirmOnPart();
	
	m_Functions.resize((size_t) nFunctions);
	for(int i = 0; i < nFunctions; ++i)
	{
		m_Functions[i].Load(reader);
		m_Functions[i].SetIndex(i);
	}

	m_StackSize = reader.ReadInt64();
	m_IsGenerator = reader.ReadBool();
	m_GotVarParams = reader.ReadBool();

	// Preprocess local variables
	int f = 0;

	for(vector<LocalVarInfo>::iterator i = m_Locals.begin(); i != m_Locals.end(); ++i)
	{
		if (i->name == "@ITERATOR@")
		{
			// Hack - sq will push three local variables for every foreach loop, last one is named @ITERATOR@,
			// we are searching for that triples and mark, because their scopes are badly set

			i->foreachLoopState = true;
			f = 2;
		}
		else if (f > 0)
		{
			i->foreachLoopState = true;
			--f;
		}
	}
}


// ***************************************************************************************************************
void NutScript::LoadFromFile( const char* fileName )
{
	std::ifstream file;

	file.open(fileName, std::ios_base::binary | std::ios_base::in);
	if (file.fail())
		throw Error("Unable to open file: \"%s\"", fileName);

	try
	{
		LoadFromStream(file);
	}
	catch(...)
	{
		file.close();
		throw;
	}

	file.close();
}


// ***************************************************************************************************************
void NutScript::LoadFromStream( std::istream& in )
{
	BinaryReader reader(in);

	// Magic
	if (reader.ReadUInt16() != 0xFAFA) 
		throw BadFormatError();

	if (reader.ReadInt64() != 'SQIR') 
		throw BadFormatError();
	
	if (reader.ReadInt64() != sizeof(char))
		throw Error("NUT file compiled for different size of char that expected.");

	m_main.Load(reader);

	if (reader.ReadUInt64() != 'TAIL') 
		throw BadFormatError();
}


bool Eq( const NutFunction::Instruction& a, const NutFunction::Instruction& b )
{
	if (a.op != b.op)
		return false;

	if (a.op == 3)	// OP_LOADFLOAT
	{
		return a.arg0 == b.arg0 && (std::abs(a.arg1_float - b.arg1_float) < 0.00001) && a.arg2 == b.arg2 && a.arg3 == b.arg3;
	}
	else
	{
		return a.arg0 == b.arg0 && a.arg1 == b.arg1 && a.arg2 == b.arg2 && a.arg3 == b.arg3;
	}
}

// ***************************************************************************************************************
bool NutFunction::DoCompare( const NutFunction& other, const std::string parentName, std::ostream& out ) const
{
	bool functionsOk = true;
	bool literalsOk = true;
	bool parametersOk = true;
	bool outerValuesOk = true;
	bool instructionsOk = true;


	std::ostringstream nameFormatter;
	
	if (!parentName.empty())
		nameFormatter << parentName << "::";

	if (!m_Name.empty())
		nameFormatter << m_Name;
	else
		nameFormatter << '[' << m_FunctionIndex << ']';

	std::string name = nameFormatter.str();

	if (m_Functions.size() != other.m_Functions.size())
	{
		out << name << ':' << std::endl;
		out << "    - different number of subfunctions: " << m_Functions.size() << " to " << other.m_Functions.size() << std::endl;
		functionsOk = false;
	}
	else
	{
		for(size_t i = 0; i < m_Functions.size(); ++i)
			if (!m_Functions[i].DoCompare(other.m_Functions[i], name, out))
				functionsOk = false;

		out << name << ':' << std::endl;
	}

	if (m_Literals.size() != other.m_Literals.size())
	{
		out << "    - different number of literals: " << m_Literals.size() << " to " << other.m_Literals.size() << std::endl;
		literalsOk = false;
	}
	else
	{
		for(size_t i = 0; i < m_Literals.size(); ++i)
			if (m_Literals[i] != other.m_Literals[i])
			{
				out << "    - different literals @ " << i << ": \"" << m_Literals[i] << "\" and \"" << other.m_Literals[i] << "\"" << std::endl;
				literalsOk = false;
			}
	}

	if (m_Parameters.size() != other.m_Parameters.size())
	{
		out << "    - different number of parameters: " << m_Parameters.size() << " to " << other.m_Parameters.size() << std::endl;
		parametersOk = false;
	}

	if (m_OuterValues.size() != other.m_OuterValues.size())
	{
		out << "    - different number of outer values: " << m_OuterValues.size() << " to " << other.m_OuterValues.size() << std::endl;
		outerValuesOk = false;
	}
	else
	{
		for(size_t i = 0; i < m_OuterValues.size(); ++i)
			if (m_OuterValues[i].src != other.m_OuterValues[i].src)
			{
				out << "    - different outer value source @ " << i << ": " << m_OuterValues[i].src << " and " << other.m_OuterValues[i].src << std::endl;
				outerValuesOk = false;
			}
	}

	if (m_Instructions.size() != other.m_Instructions.size())
	{
		out << "    - different number of instructions: " << m_Instructions.size() << " to " << other.m_Instructions.size() << std::endl;
		instructionsOk = false;
	}
	
	
	for(size_t i = 0, j = 0; i < m_Instructions.size() && j < other.m_Instructions.size(); ++i, ++j)
	{
		const Instruction& a = m_Instructions[i];
		const Instruction& b = other.m_Instructions[j];

		if (!Eq(a, b))
		{
			instructionsOk = false;

			if ((i + 1) < m_Instructions.size() && Eq(m_Instructions[i + 1], b))
			{
				out << "    - instruction missing in second @ [" << i  << "]<->[" << j << "]:" << std::endl;
				out << "          ";
				PrintOpcode(out, i, a);
				out << std::endl;
				--j;
			}
			else if ((j + 1) < other.m_Instructions.size() && Eq(other.m_Instructions[j + 1], a))
			{
				out << "    - instruction missing in first @ [" << i  << "]<->[" << j << "]:" << std::endl;
				out << "          ";
				other.PrintOpcode(out, i, b);
				out << std::endl;
				--i;
			}
			else
			{
				out << "    - different instructions @ [" << i  << "]<->[" << j << "]:" << std::endl;
				
				out << "          ";
				PrintOpcode(out, i, a);
				out << std::endl;

				out << "          ";
				other.PrintOpcode(out, i, b);
				out << std::endl;

				if (a.op != b.op)
					break;
			}
		}
	}

	return functionsOk && literalsOk && parametersOk && outerValuesOk && instructionsOk;
}