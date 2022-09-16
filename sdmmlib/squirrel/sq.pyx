from libcpp.string cimport string

cdef extern from "py/python.h":
    void _py_Compile(const string &, const string &) nogil
    
cdef string bytes_to_str(bytes c_str):
    cdef:
        string out = <string>(c_str)
    return out

def compile(str src, str dst) -> None:
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_Compile(str_src, str_dst)
