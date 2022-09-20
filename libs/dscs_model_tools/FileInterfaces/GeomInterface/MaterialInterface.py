from ...CustomExceptions.MaterialExceptions import MissingShaderUniformError
from ...FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names


class MaterialInterface:
    def __init__(self):
        self.name_hash = None
        self.shader_hex = None
        self.enable_shadows = None

        self.shader_uniforms = {}
        self.unknown_material_components = {}

    @classmethod
    def from_subfile(cls, materialReader):
        interface = cls()

        interface.name_hash = materialReader.name_hash
        interface.shader_hex = materialReader.shader_hex
        interface.enable_shadows = materialReader.enable_shadows

        interface.shader_uniforms = materialReader.shader_uniforms
        interface.unknown_material_components = materialReader.unknown_data

        return interface

    def to_subfile(self, materialReader, virtual_pos):
        materialReader.name_hash = self.name_hash
        materialReader.shader_hex = self.shader_hex
        materialReader.enable_shadows = self.enable_shadows

        materialReader.shader_uniforms = self.shader_uniforms
        virtual_pos += 24*len(self.shader_uniforms)
        materialReader.unknown_data = self.unknown_material_components
        virtual_pos += 24*len(self.unknown_material_components)

        materialReader.num_shader_uniforms = len(materialReader.shader_uniforms)
        materialReader.num_unknown_data = len(materialReader.unknown_data)

        virtual_pos += 24

        return virtual_pos

    def get_required_shader_uniforms(self):
        pass
