
#pragma once

#include <exception>
#include <string>


// ************************************************************************************************************************************
class Error : public std::exception
{
private:
	std::string m_what;

	Error();
	
public:
	Error( const Error& r );
	explicit Error( const char* format, ... );
	virtual const char* what();
};


// ************************************************************************************************************************************
struct BadFormatError : public std::exception
{
	virtual const char* what()
	{
		return "Bad .nut binary file format.";
	}
};
