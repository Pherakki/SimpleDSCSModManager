/*	see copyright notice in squirrel.h */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdexcept>

#if defined(_MSC_VER) && defined(_DEBUG)
#include <crtdbg.h>
#include <conio.h>
#endif
#include "python.h"
#include "../Squirrel/include/squirrel.h"
#include "../Squirrel/include/sqstdblob.h"
#include "../Squirrel/include/sqstdsystem.h"
#include "../Squirrel/include/sqstdio.h"
#include "../Squirrel/include/sqstdmath.h"
#include "../Squirrel/include/sqstdstring.h"
#include "../Squirrel/include/sqstdaux.h"

#include <cstdarg>

#ifdef SQUNICODE
#define scfprintf fwprintf
#define scfopen	_wfopen
#define scvprintf vwprintf
#else
#define scfprintf fprintf
#define scfopen	fopen
#define scvprintf vprintf
#endif


class VMManager
{
public:
	HSQUIRRELVM v;
	VMManager()  { v = sq_open(1024); }
	~VMManager() { sq_close(v); }
};

#if defined(_MSC_VER) && defined(_DEBUG)
int MemAllocHook( int allocType, void *userData, size_t size, int blockType, 
   long requestNumber, const unsigned char *filename, int lineNumber)
{
//	if(requestNumber==585)_asm int 3;
	return 1;
}
#endif

void printfunc_sq(HSQUIRRELVM v,const SQChar *s,...)
{
	va_list vl;
	va_start(vl, s);
	scvprintf( s, vl);
	va_end(vl);
}


#define _DONE 2

int _py_Compile(const std::string& src, const std::string& dst)
{
	VMManager vmmgr;
	HSQUIRRELVM& v = vmmgr.v;
	
#if defined(_MSC_VER) && defined(_DEBUG)
	_CrtSetAllocHook(MemAllocHook);
#endif
	
	sq_setprintfunc(v, printfunc_sq);

	sq_pushroottable(v);

	sqstd_register_bloblib(v);
	sqstd_register_iolib(v);
	sqstd_register_systemlib(v);
	sqstd_register_mathlib(v);
	sqstd_register_stringlib(v);

	//aux library
	//sets error handlers
	sqstd_seterrorhandlers(v);

	if (SQ_SUCCEEDED(sqstd_loadfile(v, src.c_str(), SQTrue)))
	{
		const SQChar* outfile = _SC(dst.c_str());
		if (SQ_SUCCEEDED(sqstd_writeclosuretofile(v, outfile))) // <- Memory leak if early return
		{
			return _DONE;
		}
	}
	// if this point is reached an error occured
	{
		const SQChar* err;
		sq_getlasterror(v);
		if (SQ_SUCCEEDED(sq_getstring(v, -1, &err))) 
		{
			throw std::runtime_error((std::string(_SC("Error [%s]\n")) + std::string(err)).c_str());
			return _DONE;
		}
	}
	
#if defined(_MSC_VER) && defined(_DEBUG)
	_getch();
	_CrtMemDumpAllObjectsSince( NULL );
#endif
	return 0;
}
