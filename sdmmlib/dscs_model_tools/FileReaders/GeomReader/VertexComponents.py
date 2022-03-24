class BaseVertexComponent:
    vertex_type = None
    num_elements = None
    vertex_dtype = None
    flag = None

    def __init__(self, data_start_ptr, flag):
        self.data_start_ptr = data_start_ptr
        self.flag = flag

    @classmethod
    def generator(cls, vtx):
        assert len(vtx[cls.vertex_type]) == cls.num_elements, f"Vertex \'{cls.vertex_type}\' has an invalid number of elements: {len(vtx[cls.vertex_type])}, should have {cls.num_elements}. Full vertex is:\n {vtx}"
        return {cls.vertex_type: vtx[cls.vertex_type]}


class Position(BaseVertexComponent):
    vertex_type = 'Position'
    num_elements = 3
    vertex_dtype = 'f'


class PosWeight(BaseVertexComponent):
    vertex_type = 'Position'
    num_elements = 4
    vertex_dtype = 'f'

    def generator(self, vtx):
        return {'Position': [*vtx['Position'], float(3 * vtx['WeightedBoneID'][0])]}


class Normal(BaseVertexComponent):
    vertex_type = 'Normal'
    num_elements = 3
    vertex_dtype = 'e'


class NormalF(BaseVertexComponent):
    vertex_type = 'Normal'
    num_elements = 3
    vertex_dtype = 'f'


class NormalH(BaseVertexComponent):
    vertex_type = 'Normal'
    num_elements = 3
    vertex_dtype = 'h'


class Tangent4(BaseVertexComponent):
    vertex_type = 'Tangent'
    num_elements = 4
    vertex_dtype = 'e'


class TangentH(BaseVertexComponent):
    vertex_type = 'Tangent'
    num_elements = 4
    vertex_dtype = 'h'


class Binormal(BaseVertexComponent):
    vertex_type = 'Binormal'
    num_elements = 3
    vertex_dtype = 'e'


class BinormalH(BaseVertexComponent):
    vertex_type = 'Binormal'
    num_elements = 3
    vertex_dtype = 'h'


class UV(BaseVertexComponent):
    vertex_type = 'UV'
    num_elements = 2
    vertex_dtype = 'e'


class UVH(BaseVertexComponent):
    vertex_type = 'UV'
    num_elements = 2
    vertex_dtype = 'h'


class UV2(BaseVertexComponent):
    vertex_type = 'UV2'
    num_elements = 2
    vertex_dtype = 'e'


class UV2H(BaseVertexComponent):
    vertex_type = 'UV2'
    num_elements = 2
    vertex_dtype = 'h'


class UV3(BaseVertexComponent):
    vertex_type = 'UV3'
    num_elements = 2
    vertex_dtype = 'e'


class UV3H(BaseVertexComponent):
    vertex_type = 'UV3'
    num_elements = 2
    vertex_dtype = 'h'


class Colour(BaseVertexComponent):
    vertex_type = 'Colour'
    num_elements = 4
    vertex_dtype = 'e'


class ByteColour(BaseVertexComponent):
    vertex_type = 'Colour'
    num_elements = 4
    vertex_dtype = 'B'


class BaseIndexComponent(BaseVertexComponent):
    @classmethod
    def generator(cls, vtx):
        num_missing_items = cls.num_elements - len(vtx[cls.vertex_type])
        current_items = [item*3 for item in vtx[cls.vertex_type]]
        current_items.extend([0] * num_missing_items)
        assert len(current_items) == cls.num_elements, "Something went wrong extending vertex indices."
        return {cls.vertex_type: current_items}


class BaseWeightComponent(BaseVertexComponent):
    @classmethod
    def generator(cls, vtx):
        num_missing_items = cls.num_elements - len(vtx[cls.vertex_type])
        current_items = [item for item in vtx[cls.vertex_type]]
        current_items.extend([0.] * num_missing_items)
        assert len(current_items) == cls.num_elements, "Something went wrong extending vertex weights."
        return {cls.vertex_type: current_items}


class Indices2(BaseIndexComponent):
    vertex_type = 'WeightedBoneID'
    num_elements = 2
    vertex_dtype = 'B'


class Indices3(BaseIndexComponent):
    vertex_type = 'WeightedBoneID'
    num_elements = 3
    vertex_dtype = 'B'


class Indices4(BaseIndexComponent):
    vertex_type = 'WeightedBoneID'
    num_elements = 4
    vertex_dtype = 'B'


class Weights2(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 2
    vertex_dtype = 'e'


class Weights3(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 3
    vertex_dtype = 'e'


class Weights4(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 4
    vertex_dtype = 'e'


class Indices1(BaseIndexComponent):
    vertex_type = 'WeightedBoneID'
    num_elements = 1
    vertex_dtype = 'B'


class ByteWeights1(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 1
    vertex_dtype = 'B'


class ByteWeights2(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 2
    vertex_dtype = 'B'


class ByteWeights3(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 3
    vertex_dtype = 'B'


class ByteWeights4(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 4
    vertex_dtype = 'B'


all_dscs_vtx_components = [Position, PosWeight, Normal, UV, UV2, UV3, Colour, Tangent4, Binormal,
                      Indices2, Indices3, Indices4,
                      Weights2, Weights3, Weights4]

# These dictionaries are how the vertex components are accessed from other files via factory methods
vertex_components_from_names_dscs = {cls.__name__: cls for cls in all_dscs_vtx_components}
vertex_components_from_defn_dscs = {(cls.vertex_type, cls.num_elements, cls.vertex_dtype): cls for cls in all_dscs_vtx_components}

all_megido_vtx_components = [Position, NormalH, NormalF, UVH, UV2H, UV3H, ByteColour, BinormalH,
                             Indices1, Indices2, Indices3, Indices4,
                             ByteWeights1, ByteWeights2, ByteWeights3, ByteWeights4]

# These dictionaries are how the vertex components are accessed from other files via factory methods
vertex_components_from_names_megido = {cls.__name__: cls for cls in all_megido_vtx_components}
vertex_components_from_names_megido["Tangent3"] = TangentH
vertex_components_from_defn_megido = {(cls.vertex_type, cls.num_elements, cls.vertex_dtype): cls for cls in all_megido_vtx_components}
vertex_components_from_defn_megido[(TangentH.vertex_type, 3, TangentH.vertex_dtype)] = TangentH

