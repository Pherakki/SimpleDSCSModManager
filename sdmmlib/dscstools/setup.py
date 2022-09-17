from distutils import sysconfig
import os
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import shutil
from sys import platform
import urllib.request

from Cython.Build import cythonize

package_name = "DSCSTools"
boost_dir = "boost_1_78_0"

# Download and build Boost
if not any(os.path.isfile(f"{package_name}{os.path.extsep}{ext}") for ext in ["pyd", "dylib", "so"]):
    if platform == "win32":
        boost_zip = "boost_1_78_0.zip"
        if not os.path.isdir(boost_dir):
            if not os.path.isfile(boost_zip):
                print("Downloading Boost 1.78.0...")
                urllib.request.urlretrieve("https://boostorg.jfrog.io/artifactory/main/release/1.78.0/source/boost_1_78_0.zip", boost_zip)
        
            print(f"Extracting {boost_zip}...")
            import zipfile
            with zipfile.ZipFile(boost_zip, 'r') as zip_ref:
                zip_ref.extractall(os.curdir)

        print("Building boost...")        
        os.chdir(boost_dir)
        os.system("./bootstrap.bat")
        os.system(f"./b2 -j {os.cpu_count()//2}")
        os.chdir(os.path.pardir)
    else:
        boost_zip = "boost_1_78_0.tar.gz"
        if not os.path.isdir(boost_dir):
            if not os.path.isfile(boost_zip):
                print("Downloading Boost 1.78.0...")
                urllib.request.urlretrieve("https://boostorg.jfrog.io/artifactory/main/release/1.78.0/source/boost_1_78_0.tar.gz", boost_zip)
        
            print(f"Extracting {boost_zip}...")
            import tarfile
            with tarfile.open(boost_zip, "r:gz") as tar:
                tar.extractall()
    
        print("Building boost...")
        os.chdir(boost_dir)
        os.system("./bootstrap.sh")
        os.system(f"./b2 -j {os.cpu_count()//2} cxxflags=-fPIC -a") # Probably going to be required if you use GCC, not just Linux
        os.chdir(os.path.pardir)

# Link the correct libraries
if platform == "linux" or platform == "linux2":
    pysobj_suffix = "so"
    extra_objects = [f"./boost_1_78_0/stage/lib/libboost_filesystem.a"]
elif platform == "darwin":
    pysobj_suffix = "dylib"
    extra_objects = [f"./boost_1_78_0/stage/lib/libboost_filesystem.a"]
elif platform == "win32":
    pysobj_suffix = "pyd"
    extra_objects = []
else:
    raise Exception("Unsupported platform: ", platform)
    
include_dirs = ["./boost_1_78_0"]
library_dirs = ["./boost_1_78_0/stage/lib"]
    
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
           "py/python.cpp",
           "DSCSTools/libs/doboz/Compressor.cpp",
           "DSCSTools/libs/doboz/Decompressor.cpp",
           "DSCSTools/libs/doboz/Dictionary.cpp",
           "DSCSTools/DSCSTools/AFS2.cpp",
           "DSCSTools/DSCSTools/EXPA.cpp",
           "DSCSTools/DSCSTools/MDB1.cpp",
           "DSCSTools/DSCSTools/SaveFile.cpp"
       ],
       language="c++",
       include_dirs=[*include_dirs],
       extra_objects=[*extra_objects]
   )]
)

os.makedirs("dist", exist_ok=True)
compiled_sobj = os.extsep.join((package_name, pysobj_suffix))
dest_path = os.path.join("dist", compiled_sobj)
if os.path.exists(dest_path):
    os.remove(dest_path)
shutil.copy2(compiled_sobj, dest_path)

# Clean up
os.remove(boost_zip)
shutil.rmtree("./boost_1_78_0")

