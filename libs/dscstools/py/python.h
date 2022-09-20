#include <iostream>

#include "../DSCSTools/DSCSTools/include/MDB1.h"

namespace dscstools
{
    // doboz
    void _py_dobozCompress(const std::string source, const std::string target);
    void _py_dobozDecompress(const std::string source, const std::string target);

    // MDB1
    void _py_extractMDB1(const std::string source, const std::string target, const bool decompress = true);
    void _py_extractMDB1File(const std::string source, const std::string target, const std::string fileName, const bool decompress = true);
    mdb1::ArchiveInfo _py_getArchiveInfo(const std::string source);
    void _py_packMDB1(const std::string source, const std::string target, const mdb1::CompressMode mode = mdb1::CompressMode::normal, bool doCrypt = true, const bool useStdout = true);
    void _py_crypt(const std::string source, const std::string target);

    // MBE
    void _py_extractMBE(const std::string source, const std::string target);
    void _py_packMBE(const std::string source, const std::string target);

    // AFS2
    void _py_extractAFS2(const std::string source, const std::string target);
    void _py_packAFS2(const std::string source, const std::string target);

    // SaveFile
    void _py_encryptSaveFile(const std::string source, const std::string target);
    void _py_decryptSaveFile(const std::string source, const std::string target);
}