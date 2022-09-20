from ..BaseRW import BaseRW
from .MeshReader import MeshReaderPC, MeshReaderPS4, MeshReaderMegido
from .MaterialReader import MaterialReader

import typing


class GeomReader(BaseRW):
    """
    A class to read geom files. These files are split into eight main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. A section that describes the geometry of each mesh.
        3. A section that describes each defined material.
        4. A section of file names for texture images.
        5. A section of unknown data that appears in CAM-type files, amongst others.
        6. Another section of unknown data that appears in CAM-type files, amongst others.
        7. A section of bone data which includes bone positions.
        8. A section of unknown data that appears to be largely filler.

    Completion status
    ------
    (o) GeomReader can successfully parse all geom files in DSDB archive within current constraints.
    (x) GeomReader cannot yet fully interpret all data in geom files in DSDB archive.
    (o) GeomReader can write data to geom files.

    Current hypotheses and observations
    ------
    1. unknown_footer_data generally seems to contain every byte value repeated four times with some preceding padding
        bytes plus some (potentially information-carrying) bytes.
    """

    def __init__(self, io_stream):
        super().__init__(io_stream)
        # Header variables
        self.filetype = None
        self.num_meshes = None
        self.num_materials = None
        self.num_light_sources = None
        self.num_cameras = None
        self.num_bones = None

        self.num_bytes_in_texture_names_section = None
        self.geom_centre = None
        self.geom_bounding_box_lengths = None
        self.padding_0x2C = None

        self.meshes_start_ptr = None
        self.materials_start_ptr = None

        self.light_sources_ptr = None
        self.cameras_ptr = None

        self.bone_matrices_start_ptr = None
        self.padding_0x58 = None
        self.texture_names_start_ptr = None
        self.footer_data_start_offset = None

        # Data storage variables
        self.meshes = []
        self.material_data = []
        self.texture_data = []
        self.light_sources = []
        self.cameras = []
        self.inverse_bind_pose_matrices = []
        self.unknown_footer_data = []

        self.subreaders = [self.meshes, self.material_data]

    @staticmethod
    def for_platform(bytestream, platform):
        platform_table = {'PC': GeomReaderPC,
                          'PS4': GeomReaderPS4,
                          'Megido': GeomReaderMegido}
        return platform_table[platform](bytestream)

    def read(self):
        self.read_write(self.read_buffer, 'read', self.read_raw, self.prepare_read_op, self.cleanup_ragged_chunk_read)
        self.interpret_geom_data()

    def write(self):
        self.reinterpret_geom_data()
        self.read_write(self.write_buffer, 'write', self.write_raw, lambda: None, self.cleanup_ragged_chunk_write)

    def read_write(self, rw_operator, rw_method_name, rw_operator_raw, preparation_op, chunk_cleanup_operator):
        self.rw_header(rw_operator)
        preparation_op()
        self.rw_meshes(rw_operator, rw_method_name)
        self.rw_material_data(rw_method_name)
        self.rw_texture_names(rw_operator_raw)
        self.rw_light_sources(rw_method_name, rw_operator)
        self.rw_cameras(rw_method_name, rw_operator)
        chunk_cleanup_operator(self.bytestream.tell(), 16)
        self.rw_bone_data(rw_operator)
        self.rw_footer_data(rw_operator_raw)

    def rw_header(self, rw_operator):
        """

        Returns
        -------
        None.

        """
        # Header
        self.assert_file_pointer_now_at(0)

        rw_operator('filetype', 'I')  # Always 100.
        self.assert_equal('filetype', 100)
        rw_operator('num_meshes', 'H')
        rw_operator('num_materials', 'H')
        rw_operator('num_light_sources', 'H')  # 0, 1, 2, 3, 4 ,5
        rw_operator('num_cameras', 'H')  # 0, 1, 2, 3, 4, 9
        rw_operator('num_bones', 'I')

        rw_operator('num_bytes_in_texture_names_section', 'I')
        rw_operator('geom_centre', 'fff')
        rw_operator('geom_bounding_box_lengths', 'fff')
        rw_operator('padding_0x2C', 'I')  # Always 0
        self.assert_is_zero('padding_0x2C')

        rw_operator('meshes_start_ptr', 'Q')
        rw_operator('materials_start_ptr', 'Q')
        rw_operator('light_sources_ptr', 'Q')
        rw_operator('cameras_ptr', 'Q')

        rw_operator('bone_matrices_start_ptr', 'Q')
        rw_operator('padding_0x58', 'Q')
        self.assert_is_zero("padding_0x58")
        rw_operator('texture_names_start_ptr', 'Q')
        rw_operator('footer_data_start_offset', 'Q')

    def is_ndef(self, offset, numValues):
        """
        A utility function that checks whether a file pointer is 0, and if it is, also checks if the associated count
        is 0. Used to skip sections that have 0 size in the file.

        Arguments
        ------
        offset -- a file pointer
        numValues -- the count of values associated with the file pointer

        Returns
        ------
        True if the file pointer is 0
        False if not
        """
        if offset == 0:
            self.assert_is_zero(numValues)
            return True
        return False

    def rw_meshes(self, rw_operator, rw_method_name):
        if self.is_ndef(self.meshes_start_ptr, 'num_meshes'):
            return
        self.assert_file_pointer_now_at(self.meshes_start_ptr)

        for meshReader in self.meshes:
            getattr(meshReader, f'{rw_method_name}_header')()
        for i, meshReader in enumerate(self.meshes):
            getattr(meshReader, rw_method_name)()

    def rw_material_data(self, rw_method_name):
        if self.is_ndef(self.materials_start_ptr, 'num_materials'):
            return
        self.assert_file_pointer_now_at(self.materials_start_ptr)

        for materialReader in self.material_data:
            getattr(materialReader, rw_method_name)()

    def rw_texture_names(self, rw_operator_raw):
        if self.is_ndef(self.texture_names_start_ptr, 'num_bytes_in_texture_names_section'):
            return
        self.assert_file_pointer_now_at(self.texture_names_start_ptr)

        rw_operator_raw('texture_data', self.num_bytes_in_texture_names_section)

    def rw_light_sources(self, rw_method_name, rw_operator):
        if self.is_ndef(self.light_sources_ptr, 'num_light_sources'):
            return
        self.assert_file_pointer_now_at(self.light_sources_ptr)

        for lightSrcReader in self.light_sources:
            getattr(lightSrcReader, rw_method_name)()

    def rw_cameras(self, rw_method_name, rw_operator):
        if self.is_ndef(self.cameras_ptr, 'num_cameras'):
            return
        self.assert_file_pointer_now_at(self.cameras_ptr)

        for camReader in self.cameras:
            getattr(camReader, rw_method_name)()

    def rw_bone_data(self, rw_operator):
        if self.is_ndef(self.bone_matrices_start_ptr, 'num_bones'):
            return
        self.assert_file_pointer_now_at(self.bone_matrices_start_ptr)

        rw_operator('inverse_bind_pose_matrices', 'f'*12*self.num_bones)

    def rw_footer_data(self, rw_operator_raw):
        if self.footer_data_start_offset == 0:
            rw_operator_raw('unknown_footer_data')
            assert len(self.unknown_footer_data) == 0, \
                f"File assumed complete, {len(self.unknown_footer_data)} bytes left to go"
            return
        self.assert_file_pointer_now_at(self.footer_data_start_offset)
        rw_operator_raw('unknown_footer_data')
        # This data appears to be 16 (potentially useful?) bytes followed by every byte value repeated x4,
        # then 12 \x00 bytes

    def prepare_read_op(self):
        self.meshes = [self.new_meshreader()(self.bytestream) for _ in range(self.num_meshes)]
        self.material_data = [MaterialReader(self.bytestream) for _ in range(self.num_materials)]

        self.light_sources = [LightSource(self.bytestream) for _ in range(self.num_light_sources)]
        self.cameras = [CameraData(self.bytestream) for _ in range(self.num_cameras)]

    def interpret_geom_data(self):
        texture_data = self.chunk_list(self.texture_data, 32)
        self.texture_data = [datum.rstrip(self.pad_byte).decode('ascii') for datum in texture_data]

        self.inverse_bind_pose_matrices = self.chunk_list(self.inverse_bind_pose_matrices, 12)
        # Can probably vectorise this loop away, but is it worth it?
        for i, data in enumerate(self.inverse_bind_pose_matrices):
            bone_matrix = [data[0:4], data[4:8], data[8:12], [0., 0., 0., 1.]]

            self.inverse_bind_pose_matrices[i] = bone_matrix

    def reinterpret_geom_data(self):
        self.texture_data: typing.List[str]

        for texture_name in self.texture_data:
            assert len(texture_name) < 32, f"Texture name {texture_name} is longer than 32 characters; please shorten the filename."
        texture_data = [texture_name.encode('ascii') + self.pad_byte * (32 - len(texture_name))
                        for texture_name in self.texture_data]
        self.texture_data = b''.join(texture_data)
        for i, data in enumerate(self.inverse_bind_pose_matrices):

            data = data[:3]  # Cut out the [0, 0, 0, 1] row

            self.inverse_bind_pose_matrices[i] = self.flatten_list(data)

        self.inverse_bind_pose_matrices = self.flatten_list(self.inverse_bind_pose_matrices)
        self.inverse_bind_pose_matrices = [elem if elem != -0 else 0 for elem in self.inverse_bind_pose_matrices]


    def new_meshreader(self):
        raise NotImplementedError


class GeomReaderPC(GeomReader):
    def __init__(self, bytestream):
        super().__init__(bytestream)

    def new_meshreader(self):
        return MeshReaderPC


class GeomReaderPS4(GeomReader):
    def __init__(self, bytestream):
        super().__init__(bytestream)

    def new_meshreader(self):
        return MeshReaderPS4


class GeomReaderMegido(GeomReader):
    def __init__(self, bytestream):
        super().__init__(bytestream)

    def new_meshreader(self):
        return MeshReaderMegido


class LightSource(BaseRW):
    def __init__(self, io_stream):
        super().__init__(io_stream)

        self.bone_name_hash = None
        self.mode = None
        self.light_id = None
        self.intensity = None
        self.unknown_fog_param = None
        self.red = None
        self.blue = None
        self.green = None
        self.alpha = None

        self.unknown_0x20 = None
        self.unknown_0x24 = None
        self.unknown_0x28 = None

        self.padding_0x2C = None
        self.padding_0x30 = None
        self.padding_0x38 = None

    def read(self):
        self.rw_header(self.read_buffer)

    def write(self):
        self.rw_header(self.write_buffer)

    def rw_header(self, rw_operator):
        rw_operator('bone_name_hash', 'I')
        rw_operator('mode', 'H')  # 0 = POINT, 2 = AMBIENT, 3 = DIRECTIONAL, 4 = UNKNOWN: Fog?
        rw_operator('light_id', 'H')  # Runs from 0 - 4

        rw_operator('intensity', 'f')
        rw_operator('unknown_fog_param', 'f')  # Fog height?

        rw_operator('red', 'f')
        rw_operator('blue', 'f')
        rw_operator('green', 'f')
        rw_operator('alpha', 'f')

        # Not sure.
        rw_operator('unknown_0x20', 'i')
        rw_operator('unknown_0x24', 'i')
        rw_operator('unknown_0x28', 'i')

        rw_operator('padding_0x2C', 'I')
        rw_operator('padding_0x30', 'Q')
        rw_operator('padding_0x38', 'Q')


class CameraData(BaseRW):
    def __init__(self, io_stream):
        super().__init__(io_stream)

        self.bone_name_hash = None
        self.fov = None
        self.maybe_aspect_ratio = None
        self.zNear = None

        self.zFar = None
        self.orthographic_scale = None
        self.projection = None
        self.padding_0x1C = None

        self.padding_0x20 = None
        self.padding_0x28 = None

    def read(self):
        self.rw_header(self.read_buffer)

    def write(self):
        self.rw_header(self.write_buffer)

    def rw_header(self, rw_operator):
        rw_operator('bone_name_hash', 'I')

        # Some parameters...
        rw_operator('fov', 'f')
        rw_operator('maybe_aspect_ratio', 'f')
        rw_operator('zNear', 'f')

        rw_operator('zFar', 'f')
        rw_operator('orthographic_scale', 'f')
        rw_operator('projection', 'I')  # 0 = Perspective, 1 = Ortho
        rw_operator('padding_0x1C', 'I')

        rw_operator('padding_0x20', 'Q')
        rw_operator('padding_0x28', 'Q')
