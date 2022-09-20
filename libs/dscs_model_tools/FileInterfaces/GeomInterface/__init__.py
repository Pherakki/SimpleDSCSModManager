from ...FileReaders.GeomReader import GeomReader
from .MeshInterface import MeshInterface
from .MaterialInterface import MaterialInterface
from .LightSourceInterface import LightSourceInterface
from .CameraInterface import CameraInterface


class GeomInterface:
    def __init__(self):
        self.meshes = []
        self.material_data = []
        self.texture_data = []
        self.light_sources = []
        self.cameras = []
        self.inverse_bind_pose_matrices = []
        self.unknown_footer_data = []

        self.geom_centre = None
        self.geom_bounding_box_lengths = None

    def add_mesh(self):
        interface = MeshInterface()
        self.meshes.append(interface)
        return interface

    def add_material(self):
        interface = MaterialInterface()
        self.material_data.append(interface)
        return interface

    def add_camera(self):
        interface = CameraInterface()
        self.cameras.append(interface)
        return interface

    def add_light_source(self):
        interface = LightSourceInterface()
        self.light_sources.append(interface)
        return interface

    @classmethod
    def from_file(cls, path, platform):
        with open(path, 'rb') as F:
            readwriter = GeomReader.for_platform(F, platform)
            readwriter.read()

        new_interface = cls()
        new_interface.meshes = [MeshInterface.from_subfile(mesh) for mesh in readwriter.meshes]
        new_interface.material_data = [MaterialInterface.from_subfile(mat) for mat in readwriter.material_data]
        new_interface.texture_data = readwriter.texture_data
        new_interface.light_sources = [LightSourceInterface.from_subfile(light) for light in readwriter.light_sources]
        new_interface.cameras = [CameraInterface.from_subfile(cam) for cam in readwriter.cameras]
        new_interface.inverse_bind_pose_matrices = readwriter.inverse_bind_pose_matrices
        new_interface.unknown_footer_data = readwriter.unknown_footer_data

        new_interface.geom_centre = readwriter.geom_centre
        new_interface.geom_bounding_box_lengths = readwriter.geom_bounding_box_lengths

        return new_interface

    def to_file(self, path, platform):
        with open(path, 'wb') as F:
            geomReader = GeomReader.for_platform(F, platform)

            geomReader.filetype = 100
            geomReader.num_meshes = len(self.meshes)
            geomReader.num_materials = len(self.material_data)
            geomReader.num_light_sources = len(self.light_sources)
            geomReader.num_cameras = len(self.cameras)
            geomReader.num_bones = len(self.inverse_bind_pose_matrices)

            geomReader.num_bytes_in_texture_names_section = 32 * len(self.texture_data)

            vertices = [v['Position'] for mesh in self.meshes for v in mesh.vertices]
            transposed_verts = list(zip(*vertices))
            if len(vertices) > 0:
                minvs = [min(axis) for axis in transposed_verts]
                maxvs = [max(axis) for axis in transposed_verts]
            else:
                minvs = [0, 0, 0]
                maxvs = [0, 0, 0]
            assert len(maxvs) == 3

            if self.geom_centre is None:
                geomReader.geom_centre = [(x + y) / 2 for x, y in zip(maxvs, minvs)]
                geomReader.geom_bounding_box_lengths = [(x - y) / 2 for x, y in zip(maxvs, minvs)]
            else:
                geomReader.geom_centre = self.geom_centre
                geomReader.geom_bounding_box_lengths = self.geom_bounding_box_lengths
            geomReader.padding_0x2C = 0

            # This generates the mesh and material subreaders that we can then populate
            geomReader.prepare_read_op()

            # Header is 112 bytes long
            virtual_pos = 112

            # Dump meshes
            geomReader.meshes_start_ptr = virtual_pos if len(self.meshes) > 0 else 0
            virtual_pos += 104 * geomReader.num_meshes
            for mesh, meshReader in zip(self.meshes, geomReader.meshes):
                virtual_pos = mesh.to_subfile(meshReader, virtual_pos, platform)

            # Dump materials
            geomReader.materials_start_ptr = virtual_pos if len(self.material_data) > 0 else 0
            for material, materialReader in zip(self.material_data, geomReader.material_data):
                virtual_pos = material.to_subfile(materialReader, virtual_pos)

            # Dump textures
            geomReader.texture_names_start_ptr = virtual_pos if len(self.texture_data) > 0 else 0
            for texture in self.texture_data:
                geomReader.texture_data.append(texture)
                virtual_pos += 32

            # Dump lights
            geomReader.light_sources_ptr = virtual_pos if len(self.light_sources) > 0 else 0
            for lightSource, lightSourceReader in zip(self.light_sources, geomReader.light_sources):
                virtual_pos = lightSource.to_subfile(lightSourceReader, virtual_pos)

            # Dump cameras
            geomReader.cameras_ptr = virtual_pos if len(self.cameras) > 0 else 0
            for camera, cameraReader in zip(self.cameras, geomReader.cameras):
                virtual_pos = camera.to_subfile(cameraReader, virtual_pos)

            # Ragged chunk fixing
            virtual_pos += (16 - (virtual_pos % 16)) % 16

            # Dump inverse bind pose matrices
            geomReader.bone_matrices_start_ptr = virtual_pos if len(self.inverse_bind_pose_matrices) > 0 else 0
            geomReader.inverse_bind_pose_matrices = self.inverse_bind_pose_matrices
            virtual_pos += geomReader.num_bones * 12 * 4

            geomReader.padding_0x58 = 0
            # Dump the footer data
            geomReader.unknown_footer_data = self.unknown_footer_data
            geomReader.footer_data_start_offset = virtual_pos if len(geomReader.unknown_footer_data) else 0
            geomReader.write()


