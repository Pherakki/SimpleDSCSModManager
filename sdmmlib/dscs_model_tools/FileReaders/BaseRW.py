import struct
import io


class ViolatedAssumptionError(Exception):
    pass


class BaseRW:
    """
    This is a base class for bytestream parsing, intended to be able to read/write (RW) these bytestreams to/from files.
    """

    def __init__(self, io_object=None):
        """
        Inputs
        ------
        A filestream opened with 'read-binary' (rb) or 'write-binary' (wb) permissions.
        """
        self.bytestream = None
        self.subreaders = []
        self.set_file_rw(io_object)
        self.header = []
        self.endianness = '<'

        self.pad_byte = b'\x00'

        self.type_buffers = {
            'x': 1,  # pad byte
            'c': 1,  # char
            'b': 1,  # int8
            'B': 1,  # uint8
            '?': 1,  # bool
            'h': 2,  # int16
            'H': 2,  # uint16
            'i': 4,  # int32
            'I': 4,  # uint32
            'l': 4,  # int32
            'L': 4,  # uint32
            'q': 8,  # int64
            'Q': 8,  # uint64
            'e': 2,  # half-float
            'f': 4,  # float
            'd': 8  # double
        }

    def set_file_rw(self, io_object):
        assert (type(io_object) == io.BufferedReader) or (type(io_object) == io.BufferedWriter), \
            f"Read-write object was instantiated with a {type(io_object)}, not a {io.BufferedReader} or " \
            f"{io.BufferedWriter}. Ensure you are instantiating this object with a file opened in 'rb' or 'wb' mode."
        self.bytestream = io_object
        for lst in self.subreaders:
            for subreader in lst:
                subreader.set_file_rw(io_object)

    def unset_file_rw(self):
        self.bytestream = None
        for lst in self.subreaders:
            for subreader in lst:
                subreader.unset_file_rw()

    def old_unpack(self, dtype, endianness=None, force_1d=False):
        """
        Takes a requested number of data types as a 'dtype' argument, adds up the number of bytes these data
        required to store them, then reads this number of bytes from the bytestream and interprets them as those
        data.

        Returns a single value if a single-element dtype is specified, else returns a tuple. Also appends the result to
        the BaseRW 'header' for easy printing of all unpacked variables.

        Arguments
        ------
        dtype -- a string of characters that correspond to data types in BaseRW.type_buffers.
        endianness -- the data type endianness (default: self.endianness).
        force_1d -- if true, return a single-element list instead of the element itself

        Returns
        ------
        The appropriate number of bytes from the bytestream interpreted as the requested data types.
        """
        if endianness is None:
            endianness = self.endianness

        buf = sum([self.type_buffers[dt] for dt in dtype])
        result = struct.unpack(endianness + dtype, self.bytestream.read(buf))

        if len(result) == 1 and not force_1d:
            result = result[0]

        self.header.append(result)
        return result

    def unpack(self, dtype, endianness=None):
        """
        Takes a requested number of data types as a 'dtype' argument, adds up the number of bytes these data
        required to store them, then reads this number of bytes from the bytestream and interprets them as those
        data.

        Arguments
        ------
        dtype -- a string of characters that correspond to data types in BaseRW.type_buffers.
        endianness -- the data type endianness (default: self.endianness).

        Returns
        ------
        The appropriate number of bytes from the bytestream interpreted as the requested data types.
        """
        if endianness is None:
            endianness = self.endianness

        buf = sum([self.type_buffers[dt] for dt in dtype])
        result = struct.unpack(endianness + dtype, self.bytestream.read(buf))

        return result

    def read_buffer(self, variable, dtype, endianness=None, force_1d=False):
        """
        deprecated
        """
        val = self.old_unpack(dtype, endianness, force_1d)
        setattr(self, variable, val)

    def read_single(self, variable, dtype, endianness=None):
        val = self.unpack(dtype, endianness)[0]
        setattr(self, variable, val)

    def read_list(self, variable, dtype, endianness=None):
        val = self.unpack(dtype, endianness)
        setattr(self, variable, val)

    def read_listoflists(self, variable, dtype, item_size, endianness=None):
        val = self.chunk_list(self.unpack(dtype, endianness), item_size)
        setattr(self, variable, val)

    def read_ascii(self, variable, num_bytes=None):
        bytes_to_read = [] if num_bytes is None else [num_bytes]
        val = self.bytestream.read(*bytes_to_read).decode('ascii')
        setattr(self, variable, val)

    def read_raw(self, variable, num_bytes=None):
        bytes_to_read = [] if num_bytes is None else [num_bytes]
        val = self.bytestream.read(*bytes_to_read)
        setattr(self, variable, val)

    def pack(self, value, dtype, endianness=None):
        if endianness is None:
            endianness = self.endianness
        return struct.pack(endianness + dtype, *value)

    def write_buffer(self, variable, dtype, endianness=None, force_1d=False):
        """
        deprecated
        """
        val = getattr(self, variable)
        # If it's not a tuple/list/, turn it into a tuple
        if not (hasattr(val, '__len__') and not isinstance(val, str)):
            val = (val,)
        to_write = self.pack(val, dtype, endianness)
        self.bytestream.write(to_write)

    def write_single(self, variable, dtype, endianness=None):
        val = getattr(self, variable)
        to_write = self.pack((val,), dtype, endianness)
        self.bytestream.write(to_write)

    def write_list(self, variable, dtype, endianness=None):
        val = getattr(self, variable)
        to_write = self.pack(val, dtype, endianness)
        self.bytestream.write(to_write)

    def write_listoflists(self, variable, dtype, item_size, endianness=None):
        val = getattr(self, variable)
        to_write = self.pack(self.flatten_list(val), dtype, endianness)
        self.bytestream.write(to_write)

    def write_ascii(self, variable, num_bytes=None):
        val = getattr(self, variable)
        if num_bytes is not None:
            assert len(val) == num_bytes, f"String to write [{val}] is not equal to the number of bytes [{num_bytes}]."
        self.bytestream.write(val.encode('ascii'))

    def write_raw(self, variable, num_bytes=None):
        val = getattr(self, variable)
        if num_bytes is not None:
            assert len(val) == num_bytes, "String to write is not equal to the number of bytes."
        self.bytestream.write(val)


    def cleanup_ragged_chunk_read(self, position, chunksize, stepsize=1, bytevalue=b'\x00'):
        """
        If 'position' is partially through a chunk, this function will check that the remaining bytes in the chunk
        are pad bytes.
        """
        bytes_read_from_final_chunk = position % chunksize
        # The modulo maps {bytes_read_from_final_chunk == 0} to {0} rather than {chunksize}
        num_bytes_left_to_read = (chunksize - bytes_read_from_final_chunk) % chunksize
        should_be_value_bytes = self.bytestream.read(num_bytes_left_to_read)
        assert should_be_value_bytes == bytevalue * (num_bytes_left_to_read // stepsize),\
            f"Assumed padding data was not {bytevalue * (num_bytes_left_to_read // stepsize)}: {should_be_value_bytes}"

    def cleanup_ragged_chunk_write(self, position, chunksize, stepsize=1, bytevalue=b'\x00'):
        """
        If 'position' is partially through a chunk, this function will complete the chunk with pad bytes.
        """
        bytes_read_from_final_chunk = position % chunksize
        # The modulo maps {bytes_read_from_final_chunk == 0} to {0} rather than {chunksize}
        num_bytes_left_to_read = (chunksize - bytes_read_from_final_chunk) % chunksize
        self.bytestream.write(bytevalue * (num_bytes_left_to_read // stepsize))

    def chunk_list(self, lst, chunksize):
        """
        Splits a 1D list into sub-lists of size 'chunksize', return returns those sub-lists inside a new 2D list.

        Inputs
        ------
        lst -- a 1D list
        chunksize -- the size of each sub-list of the result

        Returns
        ------
        The 1D input 'lst' converted to a 2D list, where each sub-list has length 'chunksize'.
        """
        return [lst[i:i + chunksize] for i in range(0, len(lst), chunksize)]

    def flatten_list(self, lst):
        return [subitem for item in lst for subitem in item]

    def read(self):
        """
        An abstract method to be implemented by children of this class. It is called to fully parse the section of
        a bytestream a particular BaseRW class presides over.
        """
        raise NotImplementedError

    def write(self):
        """
        An abstract method to be implemented by children of this class. It is called to fully write the section of
        a bytestream a particular BaseRW class presides over.
        """
        raise NotImplementedError

    # Stream validation functions
    # Should add a context arg to these
    def assert_file_pointer_now_at(self, location):
        self.check_assertion_now(lambda location: self.bytestream.tell() == location,
                                 lambda location: f"File pointer at {self.bytestream.tell()}, not at {location}.",
                                 location)

    def assert_equal(self, varname, value):
        self.make_assertion(lambda varname, value: getattr(self, varname) == value,
                            lambda varname, value: f"{varname} == {value}, value is {getattr(self, varname)}",
                            varname, value)

    def assert_is_zero(self, varname):
        self.assert_equal(varname, 0)

    def assert_equal_to_any(self, varname, *values):
        for value in values:
            self.assert_equal(varname, value)

    def make_assertion(self, check, message, *args):
        # self.assumptions_CT.append((check, message, args))
        self.check_assertion_now(check, message, *args)

    def check_assertion_now(self, check, message, *args):
        if not check(*args):
            raise ViolatedAssumptionError(f"Violation of data structure assumption '{message(*args)}'.")
