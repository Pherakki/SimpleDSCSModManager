from libcpp.string cimport string

cdef extern from "py/python.h":
    void _py_Decompile(const string &, const string &) nogil
    void _py_DecompileFunction(const string &, const string &, const string &) nogil
    
cdef string bytes_to_str(bytes c_str):
    cdef:
        string out = <string>(c_str)
    return out

def decompile(str src, str dst) -> None:
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_Decompile(str_src, str_dst)

def decompileFunction(str src, str dst, str debug_dst) -> None:
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    str_debug_dst = bytes_to_str(debug_dst.encode("utf8"))
    with nogil:
        _py_DecompileFunction(str_src, str_dst, str_debug_dst)
