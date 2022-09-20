import os
import struct
from src.CoreOperations.PluginLoaders.FiletypesPluginLoader import BaseBuildElement, BaseFiletype

def make_model_file_elements(ext):
    class MdlFileBuildElement(BaseBuildElement):
        __slots__ = tuple()
        
        build_element_id = ext + "file"
        default_rule = "overwrite"
        enable_softcodes = False
            
        @staticmethod
        def get_target(filepath):
            return filepath
        
        @classmethod
        def get_rule(cls, filepath):
            return cls.default_rule
    
        @staticmethod
        def get_pack_name(filepath):
            return os.path.splitext(filepath)[0]
        
        @classmethod
        def get_filetype_cls(cls):
            return MdlFile
        
    
    class MdlFile(BaseFiletype):
        build_elements = [MdlFileBuildElement]
        filetype_id = ext + "file"
        filepack = "Model"
        
        @staticmethod
        def checkIfMatch(path, filename):
            if os.path.splitext(filename)[-1] == f'.{ext}':
                return True
            else:
                return False
    
    return MdlFile
        
NameFile = make_model_file_elements("name")
SkelFile = make_model_file_elements("skel")
GeomFile = make_model_file_elements("geom")
AnimFile = make_model_file_elements("anim")
# PhysFile = make_model_file_elements("phys")

# Monkey-patch in the shader getters for the Geom file
# This is ugly, but this is also Python, so there's no nice templating features
@staticmethod
def find_shader_names(filepath):
    res = set()
    if os.path.splitext(filepath)[1] == ".geom":
        # Very quick grabber for the shader filenames
        with open(filepath, 'rb') as F:
            F.seek(0x06)
            num_materials = struct.unpack("H", F.read(2))[0]
            
            F.seek(0x38)
            materials_ptr = struct.unpack("Q", F.read(8))[0]
            
            F.seek(materials_ptr)
            for i in range(num_materials):
                # Find the shader name
                F.seek(0x04, os.SEEK_CUR)
                shader_name = struct.unpack('IIII', F.read(0x10))
                shader_name = "_".join([hex(elem)[2:].rjust(8, '0') for elem in shader_name])
                res.add(shader_name)
                
                # Seek to next material
                num_shader_uniforms = struct.unpack('B', F.read(1))[0]
                num_opengl_settings = struct.unpack('B', F.read(1))[0]
                F.seek(0x02 + 0x18 * (num_shader_uniforms + num_opengl_settings), os.SEEK_CUR)
    
    out = set()
    path_stem = os.path.split(filepath)[0]
    for item in res:
        out.add(os.path.join(path_stem, "shaders", item + "_vp.shad.request"))
        out.add(os.path.join(path_stem, "shaders", item + "_fp.shad.request"))
    
    return out
    
setattr(GeomFile.build_elements[0], "get_autorequests", find_shader_names)
