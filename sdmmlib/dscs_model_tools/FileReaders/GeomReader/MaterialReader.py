from ..BaseRW import BaseRW
import struct
from ...FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_defn


class MaterialReader(BaseRW):
    """
    A class to read material data within geom files. These files are split into three main sections:
        1. The header, which is mostly unknown, but does contain counts of further data.
        2. A section of shader uniforms and their values.
        3. A section containing codes for OpenGL functions and the data to pass into them.

    Completion status
    ------
    (o) MaterialReader can successfully parse all meshes in geom files in DSDB archive within current constraints.
    (0) MaterialReader can fully interpret all material data in geom files in DSDB archive.
    (o) MaterialReader can write data to geom files.

    """

    shader_uniform_from_ids = {
                        #        Name              numfloats
                        0x32: 'ColorSampler',          # 0,  # Diffuse Map Texture ID
                        0x33: 'DiffuseColor',          # 4,  # FP uniform
                        0x34: 'DiffuseAlpha',          # 1
                        0x35: 'NormalSampler',         # 0,  # Normal Map Texture ID
                        0x36: 'Bumpiness',             # 1,  # FP Uniform
                        0x37: 'SpecularParams',        # 2
                        0x38: 'SpecularStrength',      # 1,  # FP Uniform
                        0x39: 'SpecularPower',         # 1,  # FP Uniform
                        0x3a: 'EnvSampler',            # 0,  # Cube Map Texture ID
                        0x3b: 'ReflectionStrength',    # 1,  # FP Uniform
                        0x3c: 'FresnelMin',            # 1,  # FP Uniform
                        0x3d: 'FresnelExp',            # 1,  # FP Uniform
                        0x3e: 'FuzzySpecColor',        # 3,  # FP uniform
                        0x3f: 'SurfaceColor',          # 3,  # FP uniform
                        0x40: 'SubColor',             # 3,  # FP uniform
                        0x41: 'Rolloff',               # 1,  # FP uniform
                        0x42: 'VelvetStrength',        # 1,  # FP uniform
                        0x43: 'LightSampler',          # 0,  # Texture ID
                        0x44: 'OverlayColorSampler',   # 0,  # Overlay Diffuse Texture ID
                        0x45: 'OverlayNormalSampler',  # 0,  # Overlay normal texture ID?
                        0x46: 'OverlayBumpiness',      # 1,  # FP Uniform
                        0x47: 'OverlayStrength',       # 1,  # FP Uniform, Blend ratio of 1st and 2nd texture
                        0x48: 'CLUTSampler',           # 0,  # Toon Texture UD
                        # Missing
                        0x4a: 'GlassParams',           # 3
                        0x4b: 'GlassStrength',         # 1,  # FP uniform
                        0x4c: 'Curvature',             # 1,  # FP uniform
                        0x4d: 'UpsideDown',            # 1,  # FP uniform
                        0x4e: 'ParallaxBias',          # 2
                        0x4f: 'ParallaxBiasX',         # 1,  # FP uniform
                        0x50: 'ParallaxBiasY',         # 1,  # FP uniform
                        # Missing
                        # Missing
                        # Missing
                        0x54: 'Time',                  # 1,  # VP uniform
                        0x55: 'ScrollSpeedSet1',       # 2,  # VP uniform
                        # Missing
                        # Missing
                        0x58: 'ScrollSpeedSet2',       # 2,  # VP uniform
                        0x59: "ScrollSpeedSet2U",      # 1
                        0x5a: "ScrollSpeedSet2V",      # 1
                        0x5b: 'ScrollSpeedSet3',       # 2,  # VP uniform
                        0x5c: "ScrollSpeedSet3U",      # 1
                        0x5d: "ScrollSpeedSet3V",      # 1
                        0x5e: 'OffsetSet1',            # 2,  # VP uniform
                        0x5f: "OffsetSet1U",           # 1
                        0x60: "OffsetSet1V",           # 1
                        0x61: 'OffsetSet2',            # 2,  # VP uniform # c.f. Meramon
                        0x62: "OffsetSet2U",           # 1
                        0x63: "OffsetSet2V",           # 1
                        0x64: 'DistortionStrength',    # 1,  # FP uniform
                        # Several missing
                        0x70: 'MipBias',               # 1,  # FP uniform
                        0x71: 'LightMapPower',         # 1,  # FP uniform
                        0x72: 'LightMapStrength',      # 1,  # FP uniform
                        0x73: "Saturation",            # 1,  # FP uniform
                        0x74: 'OffsetSet3',            # 2,  # VP uniform
                        0x75: 'OffsetSet3U',           # 1,  # VP uniform
                        0x76: 'OffsetSet3V',           # 1,  # VP uniform
                        0x77: 'Fat',                   # 1,  # VP uniform
                        0x78: 'RotationSet1',          # 1,  # VP uniform
                        # Missing
                        # Missing
                        0x7b: 'RotationSet2',          # 1,  # VP uniform
                        # Missing
                        # Missing
                        0x7e: 'RotationSet3',          # 1,  VP uniform
                        # Missing
                        # Missing
                        0x81: 'ScaleSet1',             # 2,  # VP uniform
                        0x82: 'ScaleSet1U',            # 1,  # VP uniform
                        0x83: 'ScaleSet1V',            # 1,  # VP uniform
                        0x84: 'ScaleSet2',             # 2,  # VP uniform
                        0x85: 'ScaleSet2U',            # 1,  # VP uniform
                        0x86: 'ScaleSet2V',            # 1,  # VP uniform
                        0x87: 'ScaleSet3',             # 2,  # VP uniform
                        0x88: 'ScaleSet3U',            # 1,  # VP uniform
                        0x89: 'ScaleSet3V',            # 1,  # VP uniform
                        0x8d: 'ZBias',                 # 1,  # VP uniform
                        0x8e: 'EnvsSampler',           # 0   # Texture ID
                        0x8f: 'InnerGrowAValue',       # 3,  # FP uniform
                        0x90: 'InnerGrowAPower',       # 1,  # FP uniform
                        0x91: 'InnerGrowAStrength',    # 1,  # FP uniform
                        0x92: 'InnerGrowALimit',       # 1,  # FP uniform
                        0x93: 'GlowACLUTSampler',      # 0, # Texture ID
                        0x94: 'InnerGrowBValue',       # 3,  # FP uniform
                        0x95: 'InnerGrowBPower',       # 1,  # FP uniform
                        0x96: 'InnerGrowBStrength',    # 1,  # FP uniform
                        0x97: 'InnerGrowBLimit',       # 1,  # FP uniform
                        0x98: 'GlowBCLUTSampler',      # 0,  # Texture ID,
                        # Missing
                        0x9a: 'InnerGrowAColor',       # 1
                        0x9b: 'InnerGrowBColor',       # 1
                      }

    shader_uniform_from_names = dict([reversed(i) for i in shader_uniform_from_ids.items()])

    def __init__(self, io_stream):
        super().__init__(io_stream)

        # Header variables
        self.name_hash = None
        self.shader_hex = None
        self.num_shader_uniforms = None
        self.num_unknown_data = None
        self.enable_shadows = None

        # Data variables
        self.shader_uniforms = []
        self.unknown_data = []

        self.subreaders = [self.unknown_data]

    def read(self):
        self.read_write(self.read_buffer, self.read_raw)
        self.interpret_material()
        self.interpret_unknown_material_components()

    def write(self):
        self.reinterpret_unknown_material_components()
        self.reinterpret_material()
        self.read_write(self.write_buffer, self.write_raw)

    def read_write(self, rw_operator, rw_operator_raw):
        self.rw_header(rw_operator, rw_operator_raw)
        self.rw_material_components(rw_operator_raw)
        self.rw_unknown_data(rw_operator_raw)

    def rw_header(self, rw_operator, rw_operator_raw):
        rw_operator_raw('name_hash', 4)
        rw_operator_raw('shader_hex', 16)
        rw_operator('num_shader_uniforms', 'B')  # Known
        rw_operator('num_unknown_data', 'B')  # Known
        rw_operator('enable_shadows', 'H')  # 3 turns on shadows; what's the difference between 1 and 5?

    def rw_material_components(self, rw_operator_raw):
        rw_operator_raw("shader_uniforms", 24 * self.num_shader_uniforms)

    def rw_unknown_data(self, rw_operator_raw):
        rw_operator_raw("unknown_data", 24 * self.num_unknown_data)

    def interpret_material(self):
        self.name_hash: bytes
        self.name_hash = self.name_hash.hex()

        self.shader_hex: bytes
        shader_hex_pt_1 = self.shader_hex[0:4][::-1].hex()
        shader_hex_pt_2 = self.shader_hex[4:8][::-1].hex()
        shader_hex_pt_3 = self.shader_hex[8:12][::-1].hex()
        shader_hex_pt_4 = self.shader_hex[12:16][::-1].hex()

        self.shader_hex = '_'.join((shader_hex_pt_1, shader_hex_pt_2, shader_hex_pt_3, shader_hex_pt_4))

        self.shader_uniforms = [self.shader_uniform_factory(data) for data in self.chunk_list(self.shader_uniforms, 24)]
        self.shader_uniforms = {elem[0]: elem[1] for elem in self.shader_uniforms}

    def reinterpret_material(self):
        self.name_hash: str
        self.name_hash = bytes.fromhex(self.name_hash)

        self.shader_hex: str
        hex_parts = self.shader_hex.split('_')
        shader_hex_pt_1 = bytes.fromhex(hex_parts[0])[::-1]
        shader_hex_pt_2 = bytes.fromhex(hex_parts[1])[::-1]
        shader_hex_pt_3 = bytes.fromhex(hex_parts[2])[::-1]
        shader_hex_pt_4 = bytes.fromhex(hex_parts[3])[::-1]

        self.shader_hex = b''.join((shader_hex_pt_1, shader_hex_pt_2, shader_hex_pt_3, shader_hex_pt_4))
        self.shader_uniforms = b''.join([self.shader_uniform_data_factory(uniform_name, uniform) for uniform_name, uniform in self.shader_uniforms.items()])

    def shader_uniform_factory(self, data):
        payload = data[:16]
        uniform_type = MaterialReader.shader_uniform_from_ids[data[16]]
        num_floats = data[17]
        always_65280 = struct.unpack('H', data[18:20])[0]
        padding_0x14 = struct.unpack('I', data[20:])[0]

        assert always_65280 == 65280, f"Shader uniform variable always_65280 was {always_65280}, not 65280."
        assert padding_0x14 == 0, f"Shader padding_0x14 was {padding_0x14}, not 0."

        if num_floats == 0:
            payload = struct.unpack('H'*8, payload)
            for i, datum in enumerate(payload[1:6]):
                assert datum == 0, f"Element {i + num_floats} is not pad bytes!"
            payload = [payload[0], *payload[6:]]
        else:
            payload = struct.unpack('f'*num_floats, payload[:num_floats*4])
            for i, datum in enumerate(payload[num_floats:]):
                assert datum == 0, f"Element {i+num_floats} is not pad bytes!"
            payload = payload[:num_floats]

        return uniform_type, shader_uniforms_from_defn[(uniform_type, num_floats)](payload)

    def shader_uniform_data_factory(self, uniform_type, shader_uniform):
        if shader_uniform.num_floats == 0:
            data = struct.pack('H', shader_uniform.data[0]) + 10*self.pad_byte + struct.pack('HH', *shader_uniform.data[1:])
        else:
            data = struct.pack(f'{shader_uniform.num_floats}f', *shader_uniform.data)
            data += 4*self.pad_byte*(4 - shader_uniform.num_floats)

        data += struct.pack('B', self.shader_uniform_from_names[uniform_type])
        data += struct.pack('B', shader_uniform.num_floats)
        data += struct.pack('H', 65280)
        data += struct.pack('I', 0)

        return data

    def interpret_unknown_material_components(self):
        self.unknown_data : bytes
        self.unknown_data = [self.umc_factory(data) for data in self.chunk_list(self.unknown_data, 24)]
        self.unknown_data = {elem[0]: elem[1] for elem in self.unknown_data}

    def reinterpret_unknown_material_components(self):
        self.unknown_data: dict
        self.unknown_data = [self.umc_data_factory(key, value) for key, value in self.unknown_data.items()]
        self.unknown_data = b''.join(self.unknown_data)

    def umc_factory(self, data):
        # If you index a single byte from a bytestring, Python automatically turns it into an integer...
        maybe_component_type = data[16]   # Few values, 160 - 169 + 172 # Presumably the component type?
        always_100 = data[17]
        always_65280 = struct.unpack('H', data[18:20])[0]
        padding_0x14 = struct.unpack('I', data[20:24])[0]
        assert always_100 == 100, f"always_100 is {always_100}, not 100"
        assert always_65280 == 65280, f"always_65280 is {always_65280}, not 65280"
        assert padding_0x14 == 0, f"padding_0x14 is {padding_0x14}, not 0"

        return maybe_component_type, struct.unpack(possibly_umc_types[maybe_component_type], data[0:16])

    def umc_data_factory(self, maybe_component_type, data):
        if maybe_component_type == 160:
            data = [int(data[0]), data[1], data[2], data[3]]
        out = struct.pack(possibly_umc_types[maybe_component_type], *data)
        out += struct.pack('B', maybe_component_type)
        out += struct.pack('B', 100)
        out += struct.pack('H', 65280)
        out += struct.pack('I', 0)
        assert len(out) == 24
        return out


possibly_umc_types = {
                  0xa0: 'Ifff', #  516, float between 0 and 1, 0, 0
                  0xa1: 'IIII',  # (1, 0, 0, 0)
                  0xa2: 'IIII',  # (770, 0, 0, 0), (770, 1, 0, 0)
                  0xa3: 'IIII',  # (32779, 0, 0, 0) or (32774, 0, 0, 0)
                  0xa4: 'IIII',  # (1, 0, 0, 0)
                  0xa6: 'IIII',  # (0, 0, 0, 0)  Disables backface culling
                  0xa7: 'IIII',  # Always (516, 0, 0, 0)
                  0xa8: 'IIII',  # Always (0, 0, 0, 0)
                  0xa9: 'IIII',  # Always (0, 0, 0, 0)
                  0xac: 'IIII',  # Always (0, 0, 0, 0)
                  }
