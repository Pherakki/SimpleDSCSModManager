from distutils import sysconfig
import math
import os
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import shutil
from sys import platform
import urllib.request

package_name = "DSCSTools"
boost_ver = "boost_1_78_0"
boost_dir = os.path.join(os.path.curdir, boost_ver)
boost_inc_dir = boost_dir
boost_lib_dir = os.path.join(os.path.curdir, boost_dir, "stage", "lib")

def download(message, from_url, to_file):
    with urllib.request.urlopen(from_url) as req, open(to_file, 'ab') as f:
        chunk_size = 1024 * 256
        total_size = int(req.info()['Content-Length'])

        chunk = None
        total_read = 0
        num_packets = int(math.ceil(total_size / chunk_size))
        
        display_size = f"{total_size/(1024*1024):> 5.1f}"
        while chunk != b'':
            display_read = f"{total_read/(1024*1024):> 5.1f}"
            chunk = req.read(chunk_size)
            f.write(chunk)
            
            print(f"\r{message}... [{display_read}/{display_size} MiB]", end="")
            
            total_read += len(chunk)

if platform == "win32":
    boost_zip = "boost_1_78_0.zip"
else:
    boost_zip = "boost_1_78_0.tar.gz"
    
# Download and build Boost
if not any(os.path.isfile(f"{package_name}{os.path.extsep}{ext}") for ext in ["pyd", "dylib", "so"]):
    if platform == "win32":
        if not os.path.isdir(boost_dir):
            if not os.path.isfile(boost_zip):
                download("Downloading Boost 1.78.0...",
                         "https://boostorg.jfrog.io/artifactory/main/release/1.78.0/source/boost_1_78_0.zip",
                         boost_zip)
        
            print(f"Extracting {boost_zip}...")
            import zipfile
            with zipfile.ZipFile(boost_zip, 'r') as zip_ref:
                zip_ref.extractall(os.curdir)

        if not os.path.isdir(boost_lib_dir):
            print("Building boost...")        
            os.chdir(boost_dir)
            os.system("bootstrap.bat")
            os.system(f"b2 -j {os.cpu_count()}")
            os.chdir(os.path.pardir)
    else:
        if not os.path.isdir(boost_dir):
            if not os.path.isfile(boost_zip):
                download("Downloading Boost 1.78.0...",
                         "https://boostorg.jfrog.io/artifactory/main/release/1.78.0/source/boost_1_78_0.tar.gz",
                         boost_zip)
        
            print(f"Extracting {boost_zip}...")
            import tarfile
            with tarfile.open(boost_zip, "r:gz") as tar:
                tar.extractall()
    
        if not os.path.isdir(boost_lib_dir):
            print("Building boost...")
            os.chdir(boost_dir)
            os.system("./bootstrap.sh")
            os.system(f"./b2 -j {os.cpu_count()} cxxflags=-fPIC -a") # Probably going to be required if you use GCC, not just Linux
            os.chdir(os.path.pardir)

# Clean up
if os.path.isfile(boost_zip):
    os.remove(boost_zip)

include_dirs = [boost_inc_dir]
library_dirs = [boost_lib_dir]

# Link the correct libraries
if platform == "linux" or platform == "linux2":
    pysobj_suffix = "so"
    extra_objects = [os.path.join(boost_lib_dir, "libboost_filesystem.a")]
    extra_link_args = []
elif platform == "darwin":
    pysobj_suffix = "dylib"
    extra_objects = [os.path.join(boost_lib_dir, "libboost_filesystem.a")]
    extra_link_args = []
elif platform == "win32":
    pysobj_suffix = "pyd"
    extra_objects = []
    extra_link_args = [rf"/LIBPATH:{boost_lib_dir}"] # This is an MSVC command..! Needs to be detected by COMPILER, not platform!
else:
    raise Exception("Unsupported platform: ", platform)
    
    
# Generate dict of compiler args for different compiler versions
BUILD_ARGS = {}
for compiler, args in [
        ('msvc', ['/std:c++14']),
        ('gcc', ['-std=c++14']),
        ('g++', ['-std=c++14']),
        ('clang', ['-std=c++14']),
        ('clang++', ['-std=c++14']),
        ('unix', ['-std=c++14'])]:
    BUILD_ARGS[compiler] = args
    
# https://stackoverflow.com/a/40193040
def get_ext_filename_without_platform_suffix(filename):
    name, ext = os.path.splitext(filename)
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')

    if ext_suffix == ext:
        return filename

    ext_suffix = ext_suffix.replace(ext, '')
    idx = name.find(ext_suffix)

    if idx == -1:
        return filename
    else:
        return name[:idx] + ext

class CustomBuildExt(build_ext):
    def build_extensions(self):
        compiler = self.compiler.compiler_type
        args = BUILD_ARGS[compiler]
        for ext in self.extensions:
            ext.extra_compile_args = args
        build_ext.build_extensions(self)

    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        return get_ext_filename_without_platform_suffix(filename)

# Now compile
setup(
    name=package_name,
    cmdclass={ 'build_ext': CustomBuildExt },
    ext_modules = [Extension(
       package_name,
       sources=[
           "DSCSTools.pyx",
           os.path.join("py", "python.cpp"),
           os.path.join("DSCSTools", "libs", "doboz", "Compressor.cpp"),
           os.path.join("DSCSTools", "libs", "doboz", "Decompressor.cpp"),
           os.path.join("DSCSTools", "libs", "doboz", "Dictionary.cpp"),
           os.path.join("DSCSTools", "DSCSTools", "AFS2.cpp"),
           os.path.join("DSCSTools", "DSCSTools", "EXPA.cpp"),
           os.path.join("DSCSTools", "DSCSTools", "MDB1.cpp"),
           os.path.join("DSCSTools", "DSCSTools", "SaveFile.cpp")
       ],
       language="c++",
       include_dirs=[*include_dirs],
       extra_objects=[*extra_objects],
       extra_link_args=[*extra_link_args]
   )]
)

os.makedirs("dist", exist_ok=True)
compiled_sobj = os.extsep.join((package_name, pysobj_suffix))
dest_path = os.path.join("dist", compiled_sobj)
if os.path.exists(dest_path):
    os.remove(dest_path)
shutil.copy2(compiled_sobj, dest_path)
