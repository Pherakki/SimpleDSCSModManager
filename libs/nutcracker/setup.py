from distutils import sysconfig
import os
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import shutil
from sys import platform

from Cython.Build import cythonize

# Link the correct libraries
if platform == "linux" or platform == "linux2":
    pysobj_suffix = "so"
elif platform == "darwin":
    pysobj_suffix = "dylib"
elif platform == "win32":
    pysobj_suffix = "pyd"
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
package_name = "NutCracker"
setup(
    name=package_name,
    cmdclass={ 'build_ext': CustomBuildExt },
    ext_modules = [Extension(
        package_name,
        sources=[
            "NutCracker.pyx",
            "py/python.cpp",
            "NutCracker/src/Actions.cpp",
            "NutCracker/src/Errors.cpp",
            "NutCracker/src/main.cpp",
            "NutCracker/src/NutDecompiler.cpp",
            "NutCracker/src/NutScript.cpp",
            "NutCracker/src/SqObject.cpp",
            "NutCracker/src/Statements.cpp"
       ],
       language="c++"
   )]
)

os.makedirs("dist", exist_ok=True)
compiled_sobj = os.extsep.join((package_name, pysobj_suffix))
dest_path = os.path.join("dist", compiled_sobj)
if os.path.exists(dest_path):
    os.remove(dest_path)
shutil.copy2(compiled_sobj, dest_path)
