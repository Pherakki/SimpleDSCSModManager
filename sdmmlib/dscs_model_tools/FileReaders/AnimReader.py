import math
import struct

from .BaseRW import BaseRW
from ..Utilities.Exceptions import BadAnimationBoneCount, BadAnimationUVChannels
from ..Utilities.Rounding import roundup


class AnimReader(BaseRW):
    """
    A class to read anim files. These files are split into eight main sections:
        1.  The header, which gives file pointers to split the file into its major sections, plus counts of what appears
            in each section.
        2.  A section that contains up to eight lists of bone indices, depending on non-zero counts in the header.
        3.  A section that defines static rotations of bones.
        4.  A section that defines static locations of bones.
        5.  A section that defines static scales of bones.
        6.  A section that 1 float (?)  per unknown_0x1C.
        7.  A section that contains lengths and start pointers for a set of keyframe chunks.
        8.  A section that contains cumulative frame counts and number of frames per Keyframe chunk.
        9.  A section of 0s and -1s, marking which bones (if any) are not animated.
        10. A list of keyframe chunks, which contain data very similar to sections 3-6.

    Completion status
    ------
    (o) AnimReader can successfully parse all anim files in DSDB archive within current constraints.
    (x) AnimReader cannot yet fully interpret all anim data in DSDB archive.
    (o) AnimReader can write data to anim files.

    Current hypotheses and observations
    ------
    1.  The fourth data type - other than rotations, locations, and bones - looks like it might be UV coord shifts
    """

    def __init__(self, bytestream, num_uv_channels, num_bones):
        super().__init__(bytestream)

        # Header variables
        self.filetype = None
        self.animation_duration = None  # Seconds
        self.playback_rate = None  # Keyframes per second

        self.setup_and_static_data_size = None  # Specifies the end of the initial data chunks
        self.num_bones = None
        self.total_frames = None  # 1 more than the final count in part 6: total frames in animation?
        self.num_keyframe_chunks = None  # part 5 is 8x this count, part 6 is 4x this count: count of KeyframeChunks.
        self.always_16384 = None  # Always 16384; maybe a section terminator, maybe the precision of the rotations

        self.static_pose_bone_rotations_count = None  # part 1 is 6x this count, counts bone idxs
        self.static_pose_bone_locations_count = None  # part 2 is 12x this count, counts bone idxs
        self.static_pose_bone_scales_count = None  # part 3 is 12x this count, counts bone idxs
        self.static_pose_shader_uniform_channels_count = None  # part 4 is 4x this count, counts shader uniform channels
        self.animated_bone_rotations_count = None  # part 1 of subreaders is 6x this count, counts bone idxs
        self.animated_bone_locations_count = None  # part 2 of subreaders is 12x this count,counts bone idxs
        self.animated_bone_scales_count = None  # part 3 of subreaders is 12x this count,counts bone idxs
        self.animated_shader_uniform_channels_count = None  # part 4 of subreaders is 4x this count, counts shader uniform channels
        self.padding_0x26 = None  # Always 0
        self.bone_mask_bytes = None  # Specifies size of the bone mask
        self.abs_ptr_bone_mask = None

        self.rel_ptr_keyframe_chunks_ptrs = None  # Relative ptr
        self.rel_ptr_keyframe_chunks_counts = None  # Relative ptr
        self.rel_ptr_static_pose_bone_rotations = None  # Relative ptr
        self.rel_ptr_static_pose_bone_locations = None  # Relative ptr
        self.rel_ptr_static_pose_bone_scales = None  # Relative ptr
        self.rel_ptr_static_unknown_4 = None  # Relative ptr

        self.padding_0x48 = None
        self.padding_0x4C = None
        self.padding_0x50 = None
        self.padding_0x54 = None
        self.padding_0x58 = None
        self.padding_0x5C = None

        # Utility variables
        self.abs_ptr_keyframe_chunks_ptrs = None
        self.abs_ptr_keyframe_chunks_counts = None
        self.abs_ptr_static_pose_bone_rotations = None
        self.abs_ptr_static_pose_bone_locations = None
        self.abs_ptr_static_pose_bone_scales = None
        self.abs_ptr_static_shader_uniform_values = None
        self.num_uv_channels = num_uv_channels
        self.sk_num_bones = num_bones

        # Data holders
        self.static_pose_rotations_bone_idxs = None
        self.static_pose_locations_bone_idxs = None
        self.static_pose_scales_bone_idxs = None
        self.static_pose_shader_uniform_channels_idxs = None
        self.animated_rotations_bone_idxs = None
        self.animated_locations_bone_idxs = None
        self.animated_scales_bone_idxs = None
        self.animated_shader_uniform_channels_idxs = None

        self.static_pose_bone_rotations = None
        self.static_pose_bone_locations = None
        self.static_pose_bone_scales = None
        self.static_pose_shader_uniform_channels = None
        self.keyframe_chunks_ptrs = None
        self.keyframe_counts = None
        self.bone_masks = None
        self.shader_uniform_channel_masks = None
        self.keyframe_chunks = None

    def read(self):
        self.read_write(self.read_buffer, self.read_raw, self.read_ascii, "read", self.prepare_read_op, self.cleanup_ragged_chunk_read)
        self.interpret_animdata()

    def write(self):
        self.reinterpret_animdata()
        self.read_write(self.write_buffer, self.write_raw, self.write_ascii, "write", lambda: None, self.cleanup_ragged_chunk_write)

    def read_write(self, rw_operator, rw_operator_raw, rw_operator_ascii, rw_method_name, preparation_op, chunk_cleanup_operator):
        self.rw_header(rw_operator, rw_operator_ascii)
        preparation_op()
        self.rw_bone_idx_lists(rw_operator, chunk_cleanup_operator)
        self.rw_initial_pose_bone_rotations(rw_operator_raw, chunk_cleanup_operator)
        self.rw_initial_pose_bone_locations(rw_operator, chunk_cleanup_operator)
        self.rw_initial_pose_bone_scales(rw_operator)
        self.rw_initial_pose_shader_uniform_values(rw_operator, chunk_cleanup_operator)
        self.rw_keyframe_chunks_pointers(rw_operator)
        self.rw_keyframes_per_substructure(rw_operator, chunk_cleanup_operator)
        self.rw_unused_channel_masks(rw_operator, chunk_cleanup_operator)
        self.rw_keyframe_chunks(rw_method_name)

    def rw_header(self, rw_operator, rw_operator_ascii):
        self.assert_file_pointer_now_at(0)
        rw_operator_ascii('filetype', 4)

        rw_operator('animation_duration', 'f')
        rw_operator('playback_rate', 'f')

        rw_operator('setup_and_static_data_size', 'H')
        rw_operator('num_bones', 'H')
        rw_operator('total_frames', 'H')
        rw_operator('num_keyframe_chunks', 'H')
        rw_operator('always_16384', 'H')  # Maybe this is the precision of the quaternions?
        self.assert_equal('always_16384', 16384)
        assert self.always_16384 == 16384, self.always_16384
        if self.num_bones != self.sk_num_bones:
            raise BadAnimationBoneCount("BadAnimationBoneCount")

        rw_operator('static_pose_bone_rotations_count', 'H')
        rw_operator('static_pose_bone_locations_count', 'H')
        rw_operator('static_pose_bone_scales_count', 'H')
        rw_operator('static_pose_shader_uniform_channels_count', 'H')
        rw_operator('animated_bone_rotations_count', 'H')
        rw_operator('animated_bone_locations_count', 'H')
        rw_operator('animated_bone_scales_count', 'H')
        rw_operator('animated_shader_uniform_channels_count', 'H')
        rw_operator('padding_0x26', 'H')
        self.assert_is_zero('padding_0x26')

        rw_operator('bone_mask_bytes', 'I')
        rw_operator('abs_ptr_bone_mask', 'I')
        if self.bone_mask_bytes != 0:
            self.assert_equal('abs_ptr_bone_mask', self.setup_and_static_data_size)

        pos = self.bytestream.tell()
        rw_operator('rel_ptr_keyframe_chunks_ptrs', 'I')
        self.abs_ptr_keyframe_chunks_ptrs = pos + self.rel_ptr_keyframe_chunks_ptrs
        pos = self.bytestream.tell()
        rw_operator('rel_ptr_keyframe_chunks_counts', 'I')
        self.abs_ptr_keyframe_chunks_counts = pos + self.rel_ptr_keyframe_chunks_counts
        pos = self.bytestream.tell()
        rw_operator('rel_ptr_static_pose_bone_rotations', 'I')
        self.abs_ptr_static_pose_bone_rotations = pos + self.rel_ptr_static_pose_bone_rotations
        pos = self.bytestream.tell()
        rw_operator('rel_ptr_static_pose_bone_locations', 'I')
        self.abs_ptr_static_pose_bone_locations = pos + self.rel_ptr_static_pose_bone_locations
        pos = self.bytestream.tell()
        rw_operator('rel_ptr_static_pose_bone_scales', 'I')
        self.abs_ptr_static_pose_bone_scales = pos + self.rel_ptr_static_pose_bone_scales
        pos = self.bytestream.tell()
        rw_operator('rel_ptr_static_unknown_4', 'I')
        self.abs_ptr_static_shader_uniform_values = pos + self.rel_ptr_static_unknown_4

        rw_operator('padding_0x48', 'I')
        rw_operator('padding_0x4C', 'I')
        rw_operator('padding_0x50', 'I')
        rw_operator('padding_0x54', 'I')
        rw_operator('padding_0x58', 'I')
        rw_operator('padding_0x5C', 'I')

    def rw_bone_idx_lists(self, rw_operator, chunk_cleanup_operator):
        """
        # Eight lists of indices
        # First three are bone indices that correspond to entries in unknown_data_1-3
        # Fourth is the count of an unknown variable; total number is the sum of two counts and also 0x0C in the skel file
        # Next three are bone indices corresponding to sections of data analogous to unknown_data_1-3, but in each
        # UnknownAnimSubstructure
        # Eighth is similar to #4 but in every UnknownAnimSubstructure
        """
        rw_operator('static_pose_rotations_bone_idxs', self.static_pose_bone_rotations_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.static_pose_bone_rotations_count * 2, 16, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('static_pose_locations_bone_idxs', self.static_pose_bone_locations_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.static_pose_bone_locations_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('static_pose_scales_bone_idxs', self.static_pose_bone_scales_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.static_pose_bone_scales_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('static_pose_shader_uniform_channels_idxs', self.static_pose_shader_uniform_channels_count * 'H', force_1d=True)
        try:
            chunk_cleanup_operator(self.static_pose_shader_uniform_channels_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_uv_channels))
        except AssertionError as e:
            raise BadAnimationUVChannels("BadAnimationUVChannels") from e

        rw_operator('animated_rotations_bone_idxs', self.animated_bone_rotations_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.animated_bone_rotations_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('animated_locations_bone_idxs', self.animated_bone_locations_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.animated_bone_locations_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('animated_scales_bone_idxs', self.animated_bone_scales_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.animated_bone_scales_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('animated_shader_uniform_channels_idxs', self.animated_shader_uniform_channels_count * 'H', force_1d=True)
        try:
            chunk_cleanup_operator(self.animated_shader_uniform_channels_count*2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_uv_channels))
        except AssertionError as e:
            raise BadAnimationUVChannels("BadAnimationUVChannels") from e

        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_initial_pose_bone_rotations(self, rw_operator_raw, chunk_cleanup_operator):
        self.assert_file_pointer_now_at(self.abs_ptr_static_pose_bone_rotations)
        rw_operator_raw('static_pose_bone_rotations', 6 * self.static_pose_bone_rotations_count)
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_initial_pose_bone_locations(self, rw_operator, chunk_cleanup_operator):
        """
        # 12 bytes assigned to each bone in unknown_bone_idxs_2
        # this is a triplet of floats
        """
        self.assert_file_pointer_now_at(self.abs_ptr_static_pose_bone_locations)
        rw_operator('static_pose_bone_locations', 'fff' * self.static_pose_bone_locations_count)
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_initial_pose_bone_scales(self, rw_operator):
        """
        # 12 bytes assigned to each bone in unknown_bone_idxs_3
        # this is a triplet of floats
        """
        self.assert_file_pointer_now_at(self.abs_ptr_static_pose_bone_scales)
        rw_operator('static_pose_bone_scales', 'fff' * self.static_pose_bone_scales_count)

    def rw_initial_pose_shader_uniform_values(self, rw_operator, chunk_cleanup_operator):
        """
        # 4 bytes assigned to each idx in unknown_bone_idxs_4
        """
        self.assert_file_pointer_now_at(self.abs_ptr_static_shader_uniform_values)
        rw_operator('static_pose_shader_uniform_channels', 'f' * self.static_pose_shader_uniform_channels_count, force_1d=True)
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_keyframe_chunks_pointers(self, rw_operator):
        """
        # Says where the UnknownDataReaders start
        # Format is (0, length, pointer)
        # pointer is the absolute pointer to the start of the UnknownDataReader
        # 'length' is the number of bytes the UnknownDataReader contains, plus the number of bytes from the end of the
        # final data reader to the end of the file (WHY?!!?!)
        """
        self.assert_file_pointer_now_at(self.abs_ptr_keyframe_chunks_ptrs)
        rw_operator('keyframe_chunks_ptrs', 'HHI' * self.num_keyframe_chunks)

    def rw_keyframes_per_substructure(self, rw_operator, chunk_cleanup_operator):
        """
        In the format (cumulative_count, increment).
        'Increment' is the number of frames in the second half of the keyframe chunks datastructure
        This doesn't count the initial frame defined in the first half of the datastructure, meaning that there are
        increment + 1 frames per keyframe chunk.
        """
        self.assert_file_pointer_now_at(self.abs_ptr_keyframe_chunks_counts)
        rw_operator('keyframe_counts', 'HH' * self.num_keyframe_chunks)
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_unused_channel_masks(self, rw_operator, chunk_cleanup_operator):
        """
        Contains 0 or -1 for each bone: If 0, that bone isn't given any animation data in the file
        """
        self.assert_file_pointer_now_at(self.setup_and_static_data_size)
        there_are_bone_masks = self.bone_mask_bytes != 0
        if there_are_bone_masks:  # Equivalently, if any of the loc, rot, scl static + anim counts are < num_bones...
            rw_operator('bone_masks', 'b'*(self.num_bones), force_1d=True)
            chunk_cleanup_operator(self.bytestream.tell(), 4)

            rw_operator('shader_uniform_channel_masks', 'b'*self.num_uv_channels, force_1d=True)
            chunk_cleanup_operator(self.bytestream.tell(), 4)
        if self.bone_mask_bytes != 0:
            chunk_cleanup_operator(self.bytestream.tell(), 16)

        # Check that we've read everything we were supposed to and no more
        self.assert_file_pointer_now_at(self.setup_and_static_data_size + self.bone_mask_bytes)

    def rw_keyframe_chunks(self, rw_method_name):
        for i, (kfchunkreader, d5, d6) in enumerate(zip(self.keyframe_chunks, self.chunk_list(self.keyframe_chunks_ptrs, 3),
                                                        self.chunk_list(self.keyframe_counts, 2))):
            always_zero, chunk_length, chunk_pointer = d5
            cumulative_frames, frames_in_chunk = d6
            assert always_zero == 0
            scale_factor = (self.animated_bone_rotations_count + self.animated_bone_locations_count + self.animated_bone_scales_count + self.animated_shader_uniform_channels_count) / 8
            part5_size = int(math.ceil(scale_factor * frames_in_chunk))
            kfchunkreader.initialise_variables(chunk_pointer, part5_size, frames_in_chunk)
            getattr(kfchunkreader, rw_method_name)()

    def prepare_read_op(self):
        self.keyframe_chunks = [KeyframeChunk(self.bytestream) for _ in range(self.num_keyframe_chunks)]

    def interpret_animdata(self):
        self.static_pose_bone_rotations = self.chunk_list(self.static_pose_bone_rotations, 6)
        self.static_pose_bone_rotations = [deserialise_quaternion(elem) for elem in self.static_pose_bone_rotations]
        self.static_pose_bone_locations = self.chunk_list(self.static_pose_bone_locations, 3)
        self.static_pose_bone_scales = self.chunk_list(self.static_pose_bone_scales, 3)

        self.keyframe_chunks_ptrs = self.chunk_list(self.keyframe_chunks_ptrs, 3)
        self.keyframe_counts = self.chunk_list(self.keyframe_counts, 2)
        fix_integer_overflows_in_sorted_uint16s(self.keyframe_counts)
        # In case there is a bug in here, hide it behind an if...
        if self.keyframe_counts[-1][0] > 2**16 - 1:
            self.total_frames = self.keyframe_counts[-1][0] + 1

    def reinterpret_animdata(self):
        self.static_pose_bone_rotations = [serialise_quaternion(elem) for elem in self.static_pose_bone_rotations]
        self.static_pose_bone_rotations = b''.join(self.static_pose_bone_rotations)
        self.static_pose_bone_locations = self.flatten_list(self.static_pose_bone_locations)
        self.static_pose_bone_scales = self.flatten_list(self.static_pose_bone_scales)

        self.keyframe_chunks_ptrs = self.flatten_list(self.keyframe_chunks_ptrs)
        # In case there is a bug in here, hide it behind an if...
        if self.keyframe_counts[-1][0] > 2**16 - 1:
            self.total_frames = self.keyframe_counts[-1][0] % (2**16) + 1
        make_integer_overflows_for_sorted_uint16s(self.keyframe_counts)
        self.keyframe_counts = self.flatten_list(self.keyframe_counts)


def fix_integer_overflows_in_sorted_uint16s(list_):
    interval = 2**16
    accumulator = 0
    previous_frames = -1
    for i, (cumulative_frames, _) in enumerate(list_):
        accumulator += cumulative_frames < previous_frames
        list_[i] = (cumulative_frames + interval*accumulator, _)
        previous_frames = cumulative_frames


def make_integer_overflows_for_sorted_uint16s(list_):
    interval = 2**16
    # To introduce integer overflows, we're gonna use modulo
    # Modulo is expensive, so let's so a check first to figure out how many we actually need to modulo
    division_idx = None
    # First check if we can do an early exit, for the case where no overflows exist
    if list_[-1][0] < interval:
        return
    # If there are overflows... let's figure out how many frames we don't have to spend expensive modulo ops on
    for i, (cumulative_frames, _) in enumerate(list_):
        if cumulative_frames > interval:
            division_idx = i
            break
    # Now implement the overflow
    if division_idx is not None:
        for i, (cumulative_frames, _) in enumerate(list_[division_idx:]):
            list_[i + division_idx] = (cumulative_frames % interval, _)


class KeyframeChunk(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)

        # Header variables
        self.frame_0_rotations_bytecount = None  # Size of part 1; divisible by 6
        self.frame_0_locations_bytecount = None  # Size of part 2; divisible by 12
        self.frame_0_scales_bytecount = None  # Size of part 3; divisible by 12 + enough bytes to make total so far divisible by 4
        self.frame_0_shader_uniform_channels_bytecount = None  # Size of part 4; divisible by 4
        self.keyframed_rotations_bytecount = None  # Size of part 6; divisible by 6
        self.keyframed_locations_bytecount = None  # Size of part 7; divisible by 12
        self.keyframed_scales_bytecount = None  # Size of part 8; divisible by 12 + enough bytes to make total so far divisible by 4
        self.keyframed_shader_uniform_channels_bytecount = None  # Size of part 9; divisible by 4

        # Data holders
        self.frame_0_rotations = None  # Contains 6 bytes per entry, dtype smallest-3 quaternion with uint15s. Count in parent header.
        self.frame_0_locations = None  # Contains 12 bytes per entry, dtype fff. Count in parent header.
        self.frame_0_scales = None  # Contains 12 bytes per entry, dtype fff. Count in parent header.
        self.frame_0_shader_uniform_values = None  # Contains 4 bytes per entry, dtype f(?). Count in parent header.
        self.keyframes_in_use = None  # Bit-packed booleans stating which keyframes are in use
        self.keyframed_rotations = None  # Contains 6 bytes per entry, dtype smallest-3 quaternion with uint15s. Count in parent header.
        self.keyframed_locations = None  # Contains 12 bytes per entry, dtype fff. Count unknown.
        self.keyframed_scales = None  # Contains 12 bytes per entry, dtype fff. Count unknown.
        self.keyframed_shader_uniform_values = None  # Contains 4 bytes per entry, dtype f(?). Count unknown.

        # Utility variables
        self.bytes_read = 0

    def initialise_variables(self, start_pointer, part5_size, nframes):
        self.start_pointer = start_pointer
        # Temp variable
        self.part5_size = part5_size
        self.nframes = nframes

    def read(self):
        self.read_write(self.read_buffer, self.read_raw, self.cleanup_ragged_chunk_read)
        self.interpret_keyframe_chunk()

    def write(self):
        self.reinterpret_keyframe_chunk()
        self.read_write(self.write_buffer, self.write_raw, self.cleanup_ragged_chunk_write)

    def read_write(self, rw_operator, rw_operator_raw, cleanup_chunk_operator):
        self.rw_header(rw_operator)
        self.rw_frame_0_rotations(rw_operator_raw)
        self.rw_frame_0_locations(rw_operator)
        self.rw_frame_0_scales(rw_operator, cleanup_chunk_operator)
        self.rw_frame_0_shader_uniform_values(rw_operator)
        self.rw_keyframes_in_use(rw_operator_raw)

        self.rw_keyframed_rotations(rw_operator_raw)
        self.rw_keyframed_locations(rw_operator)
        self.rw_keyframed_scales(rw_operator, cleanup_chunk_operator)
        self.rw_keyframed_shader_uniform_values(rw_operator)

        cleanup_chunk_operator(self.bytestream.tell(), 16)

    def rw_header(self, rw_operator):
        self.assert_file_pointer_now_at(self.start_pointer)
        rw_operator('frame_0_rotations_bytecount', 'H')
        rw_operator('frame_0_locations_bytecount', 'H')
        rw_operator('frame_0_scales_bytecount', 'H')
        rw_operator('frame_0_shader_uniform_channels_bytecount', 'H')

        rw_operator('keyframed_rotations_bytecount', 'H')
        rw_operator('keyframed_locations_bytecount', 'H')
        rw_operator('keyframed_scales_bytecount', 'H')
        rw_operator('keyframed_shader_uniform_channels_bytecount', 'H')

        self.bytes_read += 16

    def rw_frame_0_rotations(self, rw_operator):
        rw_operator('frame_0_rotations', self.frame_0_rotations_bytecount)
        self.bytes_read += self.frame_0_rotations_bytecount

    def rw_frame_0_locations(self, rw_operator):
        rw_operator('frame_0_locations', 'fff'*(self.frame_0_locations_bytecount // 12))

        self.bytes_read += self.frame_0_locations_bytecount

    def rw_frame_0_scales(self, rw_operator, cleanup_chunk_operator):
        rw_operator('frame_0_scales', 'fff'*(self.frame_0_scales_bytecount // 12))
        if self.frame_0_scales_bytecount != 0:
            cleanup_chunk_operator(self.bytes_read, 4)

        self.bytes_read += self.frame_0_scales_bytecount

    def rw_frame_0_shader_uniform_values(self, rw_operator):
        rw_operator('frame_0_shader_uniform_values', 'f' * (self.frame_0_shader_uniform_channels_bytecount // 4), force_1d=True)

        self.bytes_read += self.frame_0_shader_uniform_channels_bytecount

    def rw_keyframes_in_use(self, rw_operator_raw):
        """
        This is a bit-string denoting keyframes
        """
        rw_operator_raw('keyframes_in_use', self.part5_size)

        self.bytes_read += self.part5_size

    def rw_keyframed_rotations(self, rw_operator_raw):
        rw_operator_raw('keyframed_rotations', self.keyframed_rotations_bytecount)

        self.bytes_read += self.keyframed_rotations_bytecount

    def rw_keyframed_locations(self, rw_operator):
        rw_operator('keyframed_locations', 'fff' * (self.keyframed_locations_bytecount // 12))

        self.bytes_read += self.keyframed_locations_bytecount

    def rw_keyframed_scales(self, rw_operator, cleanup_chunk_operator):
        rw_operator('keyframed_scales', 'fff' * (self.keyframed_scales_bytecount // 12))
        if self.keyframed_scales_bytecount != 0:
            cleanup_chunk_operator(self.bytes_read, 4)

        self.bytes_read += self.keyframed_scales_bytecount

    def rw_keyframed_shader_uniform_values(self, rw_operator):
        rw_operator('keyframed_shader_uniform_values', 'f' * (self.keyframed_shader_uniform_channels_bytecount // 4), force_1d=True)
        self.bytes_read += self.keyframed_shader_uniform_channels_bytecount

    def interpret_keyframe_chunk(self):
        self.keyframes_in_use: bytes

        self.frame_0_rotations = self.chunk_list(self.frame_0_rotations, 6)
        self.frame_0_rotations = [deserialise_quaternion(elem) for elem in self.frame_0_rotations]
        self.frame_0_locations = self.chunk_list(self.frame_0_locations, 3)
        self.frame_0_scales = self.chunk_list(self.frame_0_scales, 3)
        if len(self.keyframes_in_use):
            self.keyframes_in_use = bytes_to_bits(self.keyframes_in_use)
            # Chop off padding bits
            self.keyframes_in_use = self.keyframes_in_use[:self.nframes * (len(self.keyframes_in_use) // self.nframes)]
        else:
            self.keyframes_in_use = ''

        self.keyframed_rotations = self.chunk_list(self.keyframed_rotations, 6)
        self.keyframed_rotations = [deserialise_quaternion(elem) for elem in self.keyframed_rotations]
        self.keyframed_locations = self.chunk_list(self.keyframed_locations, 3)
        self.keyframed_scales = self.chunk_list(self.keyframed_scales, 3)

    def reinterpret_keyframe_chunk(self):
        self.keyframes_in_use: str
        self.frame_0_rotations = [serialise_quaternion(elem) for elem in self.frame_0_rotations]
        self.frame_0_rotations = b''.join(self.frame_0_rotations)
        self.frame_0_locations = self.flatten_list(self.frame_0_locations)
        self.frame_0_scales = self.flatten_list(self.frame_0_scales)

        if len(self.keyframes_in_use):
            # Add back padding bits
            self.keyframes_in_use += '0' * ((8 - len(self.keyframes_in_use) % 8) % 8)
            self.keyframes_in_use = bits_to_bytes(self.keyframes_in_use)
        else:
            self.keyframes_in_use = b''
        self.keyframed_rotations = [serialise_quaternion(elem) for elem in self.keyframed_rotations]
        self.keyframed_rotations = b''.join(self.keyframed_rotations)
        self.keyframed_locations = self.flatten_list(self.keyframed_locations)
        self.keyframed_scales = self.flatten_list(self.keyframed_scales)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def bytes_to_bits(bytelist):
    return ("{:0" + str(len(bytelist) * 8) + "b}").format(int(bytelist.hex(), 16))


def bits_to_bytes(bitstring):
    return b''.join([struct.pack('B', (int(elem, 2))) for elem in chunks(bitstring, 8)])


def deserialise_quaternion(dscs_rotation):
    bit_representation = bytes_to_bits(dscs_rotation)
    largest_index = struct.unpack('B', bits_to_bytes('000000' + bit_representation[46:48]))
    component_bits = bit_representation[1:46]
    component_bits = ''.join(['0'+component_bits[15*i:15*(i+1)] for i in range(3)])
    components = struct.unpack('>HHH', bits_to_bytes(component_bits))

    components = [(comp - 16383)/(16384*(2**.5)) for comp in components]

    square_vector_length = sum([comp**2 for comp in components])
    largest_component = (1 - square_vector_length)**.5

    # This is in the XYZW ordering
    components = components.insert(largest_index, largest_component)

    # Now it's in the WXYZ ordering
    quaternion = components[3:] + components[:3]

    return quaternion


def serialise_quaternion(quat):
    # Start from WXYZ ordering, put it into XYZW
    components = quat[1:] + quat[:1]
    abs_components = [abs(comp) for comp in components]
    abs_largest_component = max(abs_components)
    largest_index = abs_components.index(abs_largest_component)
    largest_component = components[largest_index]
    largest_component_sign = largest_component // abs_largest_component

    # Get rid of the largest component
    # No need to store the sign of the largest component, because
    # (W, X, Y, Z) = (-W, -X, -Y, -Z)
    # So just multiply through by the sign of the removed component to create an equivalent quaternion
    # In this way, the largest component is always +ve
    components.pop(largest_index)
    components = [largest_component_sign*comp for comp in components]

    # No other component can be larger than 1/sqrt(2) due to normalisation
    # So map the remaining components from the interval [-1/sqrt(2), 1/sqrt(2)] to [0, 32767] to gain ~1.4x precision
    components = [int(round(comp*(2**.5)*16384))+16383 for comp in components]

    for i, elem in enumerate(components):
        if elem < 0:
            components[i] = 0
        elif elem > 32767:
            components[i] = 32767

    # Now convert to big-endian uint15s
    component_bits = bytes_to_bits(struct.pack('>HHH', *components))
    component_bits = ''.join([component_bits[16*i + 1:16*(i+1)] for i in range(3)])

    # Store the largest index as a uint2
    largest_index_bits = bytes_to_bits(struct.pack('B', largest_index))[6:]

    # Put everything together
    component_bits = '0' + component_bits + largest_index_bits

    return bits_to_bytes(component_bits)
