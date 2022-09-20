from .BaseRW import BaseRW


class SkelReader(BaseRW):
    """
    A class to read skel files. These files are split into eight main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. Pairs of bone indices that create parent-bone relationships procedurally, 8 int16s per element
        3. A section of 12 floats per bone
        4. A section of 1 int16 per bone that gives the parent of each bone
        5. A section of one-multiple-of-8 per shader uniform channel
        6. A section of 4 bytes per bone
        7. A section of 1 uint32 per user channel, identifying which shader uniform the channel is for.
        8. A section of material/camera/light name hashes for the shader uniform channels.

    Completion status
    ------
    (o) SkelReader can successfully parse all name files in DSDB archive within current constraints.
    (x) SkelReader cannot yet fully interpret all data in name files in DSDB archive.
    (o) SkelReader can write data to skel files.

    Current hypotheses and observations
    ------
    1. Currently not 100% clear what the 0/8/16 per shader uniform channel is for, but is connected to the type...
       could be a flag?
    """
    def __init__(self, io_stream):
        super().__init__(io_stream)

        # Variables that appear in the file header
        self.filetype = None
        self.total_bytes = None
        self.remaining_bytes_after_parent_bones_chunk = None
        self.num_bones = None
        self.num_uv_channels = None
        self.num_bone_hierarchy_data_lines = None

        self.rel_ptr_to_end_of_bone_hierarchy_data = None
        self.rel_ptr_to_end_of_bone_defs = None
        self.rel_ptr_to_end_of_parent_bones_chunk = None
        self.rel_ptr_bone_name_hashes = None
        self.unknown_rel_ptr_3 = None
        self.rel_ptr_to_end_of_parent_bones = None

        self.padding_0x26 = None
        self.padding_0x2A = None
        self.padding_0x2E = None
        self.padding_0x32 = None

        # These hold the data stored within the file
        self.bone_hierarchy_data = None
        self.bone_data = None
        self.parent_bones = None
        self.unknown_data_1 = None
        self.bone_name_hashes = None
        self.unknown_data_3 = None
        self.uv_channel_material_name_hashes = None

        # Utility variables
        self.filesize = None

        self.abs_ptr_bone_hierarchy_data = None
        self.abs_ptr_bone_defs = None
        self.abs_ptr_parent_bones = None
        self.abs_ptr_end_of_parent_bones_chunk = None
        self.abs_ptr_bone_name_hashes = None
        self.abs_ptr_unknown_3 = None
        self.abs_ptr_unknown_4 = None

    def read(self):
        self.read_write(self.read_buffer, self.read_ascii, self.read_raw, self.cleanup_ragged_chunk_read)
        self.interpret_skel_data()

    def write(self):
        self.reinterpret_skel_data()
        self.read_write(self.write_buffer, self.write_ascii, self.write_raw, self.cleanup_ragged_chunk_write)

    def read_write(self, rw_operator, rw_operator_ascii, rw_operator_raw, chunk_cleanup):
        self.rw_header(rw_operator, rw_operator_ascii)
        self.rw_bone_hierarchy(rw_operator)
        self.rw_bone_data(rw_operator)
        self.rw_parent_bones(rw_operator)
        self.rw_unknown_data_1(rw_operator)
        chunk_cleanup(self.bytestream.tell(), 16)
        self.rw_bone_name_hashes(rw_operator_raw)
        self.rw_unknown_data_3(rw_operator)
        self.rw_uv_channel_material_name_hashes(rw_operator_raw)
        chunk_cleanup(self.bytestream.tell() - self.remaining_bytes_after_parent_bones_chunk, 16)

    def rw_header(self, rw_operator, rw_operator_ascii):
        self.assert_file_pointer_now_at(0)

        rw_operator_ascii('filetype', 4)
        self.assert_equal("filetype", "20SE")
        rw_operator('total_bytes', 'Q')
        rw_operator('remaining_bytes_after_parent_bones_chunk', 'I')
        rw_operator('num_bones',  'H')
        rw_operator('num_uv_channels', 'H')
        rw_operator('num_bone_hierarchy_data_lines', 'I')

        upcd_pos = self.bytestream.tell()  # 24
        rw_operator('rel_ptr_to_end_of_bone_hierarchy_data', 'I')
        bonedefs_pos = self.bytestream.tell()  # 28
        rw_operator('rel_ptr_to_end_of_bone_defs', 'I')
        pb_chunk_ptr_pos = self.bytestream.tell()  # 32
        rw_operator('rel_ptr_to_end_of_parent_bones_chunk', 'I')
        unk2_pos = self.bytestream.tell()  # 36
        rw_operator('rel_ptr_bone_name_hashes', 'I')
        unk3_pos = self.bytestream.tell()  # 40
        rw_operator('unknown_rel_ptr_3', 'I')
        pcp_pos = self.bytestream.tell()  # 44
        rw_operator('rel_ptr_to_end_of_parent_bones', 'I')

        rw_operator('padding_0x26', 'I')
        self.assert_is_zero("padding_0x26")
        rw_operator('padding_0x2A', 'I')
        self.assert_is_zero("padding_0x2A")
        rw_operator('padding_0x2E', 'I')
        self.assert_is_zero("padding_0x2E")
        rw_operator('padding_0x32', 'I')
        self.assert_is_zero("padding_0x32")

        # Would be nice to refactor this to be in terms of the start of sections, but... it works...
        self.abs_ptr_bone_hierarchy_data = upcd_pos + self.rel_ptr_to_end_of_bone_hierarchy_data - (self.num_bone_hierarchy_data_lines * 16)
        self.abs_ptr_bone_defs = bonedefs_pos + self.rel_ptr_to_end_of_bone_defs - (self.num_bones * 12 * 4)
        self.abs_ptr_parent_bones = pcp_pos + self.rel_ptr_to_end_of_parent_bones - self.num_bones * 2
        self.abs_ptr_end_of_parent_bones_chunk = pb_chunk_ptr_pos + self.rel_ptr_to_end_of_parent_bones_chunk
        self.abs_ptr_bone_name_hashes = unk2_pos + self.rel_ptr_bone_name_hashes - self.num_bones * 4
        self.abs_ptr_unknown_3 = unk3_pos + self.unknown_rel_ptr_3 - self.num_uv_channels * 4
        self.assert_equal("total_bytes", self.abs_ptr_bone_name_hashes + self.remaining_bytes_after_parent_bones_chunk)

    def rw_bone_hierarchy(self, rw_operator):
        # Seems to contain the same info as the parent_bones with repeats and bugs..?
        self.assert_file_pointer_now_at(self.abs_ptr_bone_hierarchy_data)
        int16s_to_read = self.num_bone_hierarchy_data_lines * 8
        rw_operator('bone_hierarchy_data', 'h'*int16s_to_read)

    def rw_bone_data(self, rw_operator):
        # Rotation, position, scale as quaternions and affine vectors
        self.assert_file_pointer_now_at(self.abs_ptr_bone_defs)
        floats_to_read = self.num_bones * 12  # * 4
        rw_operator('bone_data', 'f'*floats_to_read)

    def rw_parent_bones(self, rw_operator):
        self.assert_file_pointer_now_at(self.abs_ptr_parent_bones)
        rw_operator('parent_bones', 'h'*self.num_bones, force_1d=True)

    def rw_unknown_data_1(self, rw_operator):
        """
        No idea what this one is..!
        Seems to differentiate uniforms, cameras, ..?
        """
        #self.assert_file_pointer_now_at()
        rw_operator('unknown_data_1', 'B' * self.num_uv_channels, force_1d=True)

    def rw_bone_name_hashes(self, rw_operator_raw):
        self.assert_file_pointer_now_at(self.abs_ptr_bone_name_hashes)
        bytes_to_read = self.num_bones * 4
        rw_operator_raw('bone_name_hashes', bytes_to_read)

    def rw_unknown_data_3(self, rw_operator):
        """
        This is an array offset: (shader key * 16) + array_index.
        E.g. to access DiffuseColor item 1, the required value is (0x33 * 16) + 0x01 = 0x331
        """
        self.assert_file_pointer_now_at(self.abs_ptr_unknown_3)
        rw_operator('unknown_data_3', 'I' * self.num_uv_channels, force_1d=True)

    def rw_uv_channel_material_name_hashes(self, rw_operator_raw):
        rw_operator_raw('uv_channel_material_name_hashes', 4 * self.num_uv_channels)

    def interpret_skel_data(self):
        self.bone_hierarchy_data = self.chunk_list(self.bone_hierarchy_data, 8)
        self.bone_data = self.chunk_list(self.chunk_list(self.bone_data, 4), 3)
        self.bone_name_hashes = self.chunk_list(self.bone_name_hashes, 4)
        self.parent_bones = [(i, idx) for i, idx in enumerate(self.parent_bones)]
        self.uv_channel_material_name_hashes = self.chunk_list(self.uv_channel_material_name_hashes, 4)
        self.uv_channel_material_name_hashes = [item.hex() for item in self.uv_channel_material_name_hashes]
        # Basic error checking - make sure no bone idx exceeds the known number of bones
        if len(self.parent_bones) != 0:
            max_idx = max([subitem for item in self.parent_bones for subitem in item])
        else:
            max_idx = -1
        assert max_idx == self.num_bones - 1, f'{max_idx}, {self.num_bones - 1}'
        
        # final elem of 'pos' and 'scale' always 1 - these are nominally 4-vectors,
        # so the final elem is presumably either unused or part of an affine transform
        for i, bone_set in enumerate(self.bone_data):
            assert bone_set[1][-1] == 1., bone_set
            assert bone_set[2][-1] == 1., bone_set

    def reinterpret_skel_data(self):
        self.bone_hierarchy_data = self.flatten_list(self.bone_hierarchy_data)
        self.bone_data = self.flatten_list(self.flatten_list(self.bone_data))
        self.bone_name_hashes = b''.join(self.bone_name_hashes)
        self.parent_bones = [parent for child, parent in self.parent_bones]
        self.uv_channel_material_name_hashes = [bytes.fromhex(item) for item in self.uv_channel_material_name_hashes]
        self.uv_channel_material_name_hashes = b''.join(self.uv_channel_material_name_hashes)
