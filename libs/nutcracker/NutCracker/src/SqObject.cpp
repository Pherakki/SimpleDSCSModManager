
#include "SqObject.h"
#include <string>
using namespace std;


// ***********************************************************************************************************************
void PrintEscapedString( std::ostream& out, const std::string& str )
{
	for( basic_string <char>::const_iterator i = str.begin(); i != str.end(); ++i )
	{
		switch(*i)
		{
			case '\r':	out << "\\r";			break;
			case '\n':	out << "\\n";			break;
			case '\t':	out << "\\t";			break;
			case '\v':	out << "\\v";			break;
			case '\a':	out << "\\a";			break;
			case '\0':	out << "\\0";			break;
			case '\\':	out << "\\\\";			break;
			
			default:
				out << *i;
				break;
		}
	}
}

// ***********************************************************************************************************************
void SqObject::Load( BinaryReader& reader )
{
	int type = reader.ReadInt32();
	switch(type)
	{
		default:
			throw Error("Unknown type of object in source binary file: 0x%08X", type);

		case TypeNull:
			m_string.clear();
			m_integer = 0;
			break;

		case TypeString:
			reader.ReadSQString(m_string);
			break;

		case TypeInteger:
			m_integer = reader.ReadUInt32();
			break;

		case TypeFloat:
			m_float = reader.ReadFloat32();
			break;
	}

	m_type = type;
}


// ***********************************************************************************************************************
int SqObject::GetType( void ) const
{
	return m_type;
}


// ***********************************************************************************************************************
const char* SqObject::GetTypeName( void ) const
{
	switch(m_type)
	{
		case 0:				return "Empty";
		case TypeNull:		return "NULL";
		case TypeString:	return "String";
		case TypeInteger:	return "Integer";
		case TypeFloat:		return "Float";
		default:			return "Unknown";
	}
}


// ***********************************************************************************************************************
const std::string& SqObject::GetString( void ) const
{
	if (m_type != TypeString && m_type != TypeNull)
		throw Error("Request of String in object of type %s.", GetTypeName());

	return m_string;
}


// ***********************************************************************************************************************
unsigned int SqObject::GetInteger( void ) const
{
	if (m_type != TypeInteger && m_type != TypeNull)
		throw Error("Request of Integer in object of type %s.", GetTypeName());

	return m_integer;
}


// ***********************************************************************************************************************
float SqObject::GetFloat( void ) const
{
	if (m_type != TypeFloat && m_type != TypeNull)
		throw Error("Request of Float in object of type %s.", GetTypeName());

	return m_float;
}

// ***********************************************************************************************************************
bool SqObject::operator == ( const SqObject& other ) const
{
	if (m_type != other.m_type)
		return false;

	switch(m_type)
	{
	case 0:
	case SqObject::TypeNull:
		return true;

	case SqObject::TypeString:
		return m_string == other.m_string;
		
	case SqObject::TypeInteger:
		return m_integer == other.m_integer;

	case SqObject::TypeFloat:
		return std::abs(m_float - other.m_float) < 0.00001f;
	}

	return false;
}

// ***********************************************************************************************************************
std::ostream& operator << ( std::ostream& os, const SqObject& obj )
{
	switch(obj.m_type)
	{
	default:
		os << "<Unknown>";
		break;

	case 0:
		os << "<Empty>";
		break;

	case SqObject::TypeNull:
		os << "NULL";
		break;

	case SqObject::TypeString:
		os << '\"';
		PrintEscapedString(os, obj.m_string);
		os << '\"';
		break;

	case SqObject::TypeInteger:
		os << obj.m_integer;
		break;

	case SqObject::TypeFloat:
		os << std::showpoint << obj.m_float;
		break;

	}

	return os;
}
