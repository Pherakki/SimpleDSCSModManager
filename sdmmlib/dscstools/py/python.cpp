#include <iostream>

#include "../DSCSTools/DSCSTools/include/MDB1.h"
#include "../DSCSTools/DSCSTools/include/EXPA.h"
#include "../DSCSTools/DSCSTools/include/AFS2.h"
#include "../DSCSTools/DSCSTools/include/SaveFile.h"

namespace dscstools
{
    // doboz
    void _py_dobozCompress(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        mdb1::dobozCompress(_source, _target);
    }

    void _py_dobozDecompress(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        mdb1::dobozDecompress(_source, _target);
    }

    // MDB1
    void _py_extractMDB1(const std::string source, const std::string target, const bool decompress = true) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        mdb1::extractMDB1(_source, _target, decompress);
    }

    void _py_extractMDB1File(const std::string source, const std::string target, const std::string fileName, const bool decompress = true) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        mdb1::extractMDB1File(_source, _target, fileName, decompress);
    }

    mdb1::ArchiveInfo _py_getArchiveInfo(const std::string source) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        return mdb1::getArchiveInfo(_source);
    }

    void _py_packMDB1(const std::string source, const std::string target, const mdb1::CompressMode mode = mdb1::CompressMode::normal, bool doCrypt = true, const bool useStdout = true) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        if(useStdout)
            mdb1::packMDB1(_source, _target, mode, doCrypt, std::cout);
        else
            mdb1::packMDB1(_source, _target, mode, doCrypt);
    }

    void _py_crypt(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        mdb1::cryptFile(_source, _target);
    }

    // MBE
    void _py_extractMBE(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        mbe::extractMBE(_source, _target);
    }

    void _py_packMBE(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        mbe::packMBE(_source, _target);
    }

    // AFS2
    void _py_extractAFS2(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        afs2::extractAFS2(_source, _target);
    }

    void _py_packAFS2(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        afs2::packAFS2(_source, _target);
    }

    // SaveFile
    void _py_encryptSaveFile(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        savefile::encryptSaveFile(_source, _target);
    }

    void _py_decryptSaveFile(const std::string source, const std::string target) {
        boost::filesystem::path _source = boost::filesystem::exists(source) ? source : boost::filesystem::current_path().append(source);
        boost::filesystem::path _target = target;
        savefile::decryptSaveFile(_source, _target);
    }
}
