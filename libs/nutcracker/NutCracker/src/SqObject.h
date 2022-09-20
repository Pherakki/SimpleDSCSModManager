
#pragma once

#include <string>
#include "Errors.h"
#include "BinaryReader.h"


// ****************************************************************************************************************************
class SqObject
{
public:
	static const int TypeNull = 0x01 | 0x01000000;
	static const int TypeString = 0x10 | 0x08000000;
	static const int TypeInteger = 0x02 | 0x04000000 | 0x01000000;
	static const int TypeFloat = 0x04 | 0x04000000 | 0x01000000;

private:
	int m_type;
	std::string m_string;

	union
	{
		unsigned int m_integer;
		float m_float;
	};

public:
	SqObject()
	{
		m_type = 0;
	}

	void Load( BinaryReader& reader );

	int GetType( void ) const;
	const char* GetTypeName( void ) const;

	const std::string& GetString( void ) const;
	unsigned int GetInteger( void ) const;
	float GetFloat( void ) const;

	bool operator == ( const SqObject& other ) const;
	bool operator != ( const SqObject& other ) const
	{
		return !(operator == (other));
	}

	friend std::ostream& operator << ( std::ostream& os, const SqObject& obj );
};
