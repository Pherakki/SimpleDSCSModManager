from libc.stdint cimport int16_t, uint16_t, uint32_t
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp cimport bool as bool_t

    
cdef string bytes_to_str(bytes c_str):
    cdef:
        string out = <string>(c_str)
    return out

cdef extern from "DSCSTools/DSCSTools/include/MDB1.h" namespace "dscstools::mdb1":
    cpdef enum CompressMode:
        none,
        normal,
        advanced
        
    cpdef enum ArchiveStatus:
        decrypted,
        encrypted,
        invalid
        
    cdef struct CppFileEntry "dscstools::mdb1::FileEntry":
        int16_t compareBit
        uint16_t dataId
        uint16_t left
        uint16_t right

    cdef struct CppFileNameEntry "dscstools::mdb1::FileNameEntry":
        char extension[4]
        char name[0x3C]
        
        const string toString()
        const string toPath()

    cdef struct CppDataEntry "dscstools::mdb1::DataEntry":
        uint32_t offset
        uint32_t size
        uint32_t compSize
        
    cdef cppclass CppFileInfo "dscstools::mdb1::FileInfo":
        CppFileEntry file
        CppFileNameEntry name
        CppDataEntry data
        
        bool_t operator==(const CppFileInfo &)
        
    cdef cppclass CppArchiveInfo "dscstools::mdb1::ArchiveInfo":
        CppArchiveInfo() except +
        ArchiveStatus status
        uint32_t magicValue
        uint16_t fileCount
        uint32_t dataStart
        vector[CppFileInfo] fileInfo

cdef class FileInfo:
    cdef CppFileInfo thisptr
        
    @property
    def FileName(self):
        return self.thisptr.name.toString().decode('utf8')
    
    @property
    def DataOffset(self):
        return self.thisptr.data.offset
    
    @property
    def DataSize(self):
        return self.thisptr.data.size
    
    @property
    def DataCompressedSize(self):
        return self.thisptr.data.compSize

cdef class ArchiveInfo:
    cdef CppArchiveInfo thisptr
    
    @property
    def ArchiveStatus(self):
        return self.thisptr.status
        
    @property
    def FileCount(self):
        return self.thisptr.fileCount
        
    @property
    def DataStart(self):
        return self.thisptr.dataStart
        
    cdef __make_files(self):
        out = []
        for f in self.thisptr.fileInfo:
            fi = FileInfo()
            fi.thisptr = f
            out.append(fi)
        return out
    
    @property
    def Files(self):
        return self.__make_files()

        
cdef extern from "py/python.h" namespace "dscstools":
    void _py_dobozCompress(const string &, const string &) nogil
    void _py_dobozDecompress(const string &, const string &) nogil

    void _py_extractMDB1    (const string & src, const string & dst, const bool_t decompress) nogil
    void _py_packMDB1       (const string & src, const string & dst, const CompressMode mode, bool_t doCrypt, const bool_t useStdout)  nogil
    void _py_extractMDB1File(const string & src, const string & dst, const string fileName, const bool_t decompress)  nogil
    CppArchiveInfo _py_getArchiveInfo(const string & src) nogil
    void _py_crypt          (const string & src, const string & dst) nogil

    void _py_extractMBE(const string & src, const string & dst) nogil
    void _py_packMBE   (const string & src, const string & dst) nogil

    void _py_extractAFS2(const string & source, const string & target) nogil
    void _py_packAFS2   (const string & source, const string & target) nogil

    void _py_encryptSaveFile(const string src, const string & dst) nogil
    void _py_decryptSaveFile(const string src, const string & dst) nogil

    cdef CppArchiveInfo getArchiveInfoWrapper(const string & src):
        return _py_getArchiveInfo(src)
    

def dobozCompress(str src, str dst) -> None:
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_dobozCompress(str_src, str_dst)

def dobozDecompress(str src, str dst) -> None:
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_dobozDecompress(str_src, str_dst)
        
def extractMDB1(str src, str dst, bool_t decompress=True):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_extractMDB1(str_src, str_dst, decompress)
        
def packMDB1(str src, str dst, CompressMode compress_mode, bool_t doCrypt=True, bool_t use_stdout=True):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_packMDB1(str_src, str_dst, compress_mode, doCrypt, use_stdout)    
        
def getArchiveInfo(str src):
    str_src = bytes_to_str(src.encode("utf8")) 
    out = ArchiveInfo()
    out.thisptr = _py_getArchiveInfo(str_src)
    return out
        
def extractMDB1File(str src, str dst, str fileName, bool_t decompress=True):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    str_fileName = bytes_to_str(fileName.encode("utf8"))
    with nogil:
        _py_extractMDB1File(str_src, str_dst, str_fileName, decompress)
        
def crypt(str src, str dst):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_crypt(str_src, str_dst)  
        
def extractMBE(str src, str dst):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_extractMBE(str_src, str_dst)
        
def packMBE(str src, str dst):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_packMBE(str_src, str_dst)
        
def extractAFS2(str src, str dst):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_extractAFS2(str_src, str_dst)
        
def packAFS2(str src, str dst):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_packAFS2(str_src, str_dst)
        
def encryptSaveFile(str src, str dst):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_encryptSaveFile(str_src, str_dst)
        
def decryptSaveFile(str src, str dst):
    str_src = bytes_to_str(src.encode("utf8"))
    str_dst = bytes_to_str(dst.encode("utf8"))
    with nogil:
        _py_decryptSaveFile(str_src, str_dst)
