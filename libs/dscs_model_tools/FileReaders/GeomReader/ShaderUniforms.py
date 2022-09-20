class BaseUniform:
    num_floats = None

    def __init__(self, data):
        self.data = data


class ColorSampler(BaseUniform): num_floats = 0
class DiffuseColor(BaseUniform): num_floats = 4  # FP uniform
class DiffuseAlpha(BaseUniform): num_floats = 1  # FP uniform
class NormalSampler(BaseUniform): num_floats = 0
class Bumpiness(BaseUniform): num_floats = 1  # FP Uniform,
class SpecularParams(BaseUniform): num_floats = 2  # FP Uniform
class SpecularStrength(BaseUniform): num_floats = 1  # FP Uniform
class SpecularPower(BaseUniform): num_floats = 1  # FP Uniform
class EnvSampler(BaseUniform): num_floats = 0
class ReflectionStrength(BaseUniform): num_floats = 1  # FP Uniform
class FresnelExp(BaseUniform): num_floats = 1  # FP Uniform
class FresnelMin(BaseUniform): num_floats = 1  # FP Uniform
class FuzzySpecColor(BaseUniform): num_floats = 3
class SubColor(BaseUniform): num_floats = 3  #
class SurfaceColor(BaseUniform): num_floats = 3
class Rolloff(BaseUniform): num_floats = 1
class VelvetStrength(BaseUniform): num_floats = 1
class LightSampler(BaseUniform): num_floats = 0
class OverlayColorSampler(BaseUniform): num_floats = 0
class OverlayNormalSampler(BaseUniform): num_floats = 0
class OverlayBumpiness(BaseUniform): num_floats = 1  # FP Uniform
class OverlayStrength(BaseUniform): num_floats = 1  # FP Uniform
class CLUTSampler(BaseUniform): num_floats = 0  # idx 0 is texture id, rest are...?
class GlassParams(BaseUniform): num_floats = 3
class Curvature(BaseUniform): num_floats = 1
class GlassStrength(BaseUniform): num_floats = 1
class UpsideDown(BaseUniform): num_floats = 1
class ParallaxBias(BaseUniform): num_floats = 2
class ParallaxBiasX(BaseUniform): num_floats = 1
class ParallaxBiasY(BaseUniform): num_floats = 1
class Time(BaseUniform): num_floats = 1  # VP uniform
class ScrollSpeedSet1(BaseUniform): num_floats = 2  # VP uniform
class ScrollSpeedSet2(BaseUniform): num_floats = 2  # VP uniform
class ScrollSpeedSet2U(BaseUniform): num_floats = 1  # VP uniform
class ScrollSpeedSet2V(BaseUniform): num_floats = 1  # VP uniform
class ScrollSpeedSet3(BaseUniform): num_floats = 2  # VP uniform
class ScrollSpeedSet3U(BaseUniform): num_floats = 1  # VP uniform
class ScrollSpeedSet3V(BaseUniform): num_floats = 1  # VP uniform
class OffsetSet1(BaseUniform): num_floats = 2  # VP uniform
class OffsetSet1U(BaseUniform): num_floats = 1  # VP uniform
class OffsetSet1V(BaseUniform): num_floats = 1  # VP uniform
class OffsetSet2(BaseUniform): num_floats = 2  # VP uniform # c.f. Meramon
class OffsetSet2U(BaseUniform): num_floats = 1  # VP uniform
class OffsetSet2V(BaseUniform): num_floats = 1  # VP uniform
class DistortionStrength(BaseUniform): num_floats = 1  # FP uniform
class MipBias(BaseUniform): num_floats = 1  # FP uniform
class LightMapStrength(BaseUniform): num_floats = 1  # FP Uniform
class LightMapPower(BaseUniform): num_floats = 1  # FP Uniform
class Saturation(BaseUniform): num_floats = 1  # FP Uniform
class OffsetSet3(BaseUniform): num_floats = 2  # VP uniform
class OffsetSet3U(BaseUniform): num_floats = 1  # VP uniform
class OffsetSet3V(BaseUniform): num_floats = 1  # VP uniform
class Fat(BaseUniform): num_floats = 1  # VP uniform
class RotationSet1(BaseUniform): num_floats = 1  # VP uniform
class RotationSet2(BaseUniform): num_floats = 1  # VP uniform
class RotationSet3(BaseUniform): num_floats = 1  # VP uniform
class ScaleSet1(BaseUniform): num_floats = 2  # VP uniform
class ScaleSet1U(BaseUniform): num_floats = 1  # VP uniform
class ScaleSet1V(BaseUniform): num_floats = 1  # VP uniform
class ScaleSet2(BaseUniform): num_floats = 2  # VP uniform
class ScaleSet2U(BaseUniform): num_floats = 1  # VP uniform
class ScaleSet2V(BaseUniform): num_floats = 1  # VP uniform
class ScaleSet3(BaseUniform): num_floats = 2  # VP uniform
class ScaleSet3U(BaseUniform): num_floats = 1  # VP uniform
class ScaleSet3V(BaseUniform): num_floats = 1  # VP uniform
class ZBias(BaseUniform): num_floats = 1  # VP uniform
class EnvsSampler(BaseUniform): num_floats = 0
class InnerGrowAValue(BaseUniform): num_floats = 3
class InnerGrowAPower(BaseUniform): num_floats = 1
class InnerGrowAStrength(BaseUniform): num_floats = 1
class InnerGrowALimit(BaseUniform): num_floats = 1
class GlowACLUTSampler(BaseUniform): num_floats = 0
class InnerGrowBValue(BaseUniform): num_floats = 3
class InnerGrowBPower(BaseUniform): num_floats = 1
class InnerGrowBStrength(BaseUniform): num_floats = 1
class InnerGrowBLimit(BaseUniform): num_floats = 1
class GlowBCLUTSampler(BaseUniform): num_floats = 0
class InnerGrowAColor(BaseUniform): num_floats = 4
class InnerGrowBColor(BaseUniform): num_floats = 4


texture_nodes = [ColorSampler, NormalSampler, EnvSampler, LightSampler,
                 OverlayColorSampler, OverlayNormalSampler, CLUTSampler, EnvsSampler,
                 GlowACLUTSampler, GlowBCLUTSampler]
# VP_uniforms = [Time, ScrollSpeedSet1, ScrollSpeedSet2, ScrollSpeedSet3, OffsetSet1, OffsetSet2, OffsetSet3,
#                Fat, RotationSet1, RotationSet2, ScaleSet1, ZBias]
# FP_uniforms = [DiffuseColour, Bumpiness, SpecularStrength, SpecularPower, ReflectionStrength, FresnelExp, FresnelMin,
#                FuzzySpecColor, SubColor, SurfaceColor, Rolloff, VelvetStrength, OverlayBumpiness, OverlayStrength,
#                Curvature, GlassStrength, UpsideDown, ParallaxBiasX, ParallaxBiasY, DistortionStrength,
#                LightMapStrength, LightMapPower]

shader_uniforms_vp_fp = [DiffuseColor, DiffuseAlpha, Bumpiness, SpecularParams, SpecularStrength, SpecularPower,
                         ReflectionStrength, FresnelExp, FresnelMin, FuzzySpecColor, SubColor, SurfaceColor, Rolloff,
                         VelvetStrength, OverlayBumpiness, OverlayStrength, GlassParams, Curvature, GlassStrength,
                         UpsideDown, ParallaxBias, ParallaxBiasX, ParallaxBiasY, Time, ScrollSpeedSet1, ScrollSpeedSet2,
                         ScrollSpeedSet2U, ScrollSpeedSet2V, ScrollSpeedSet3, ScrollSpeedSet3U, ScrollSpeedSet3V,
                         OffsetSet1, OffsetSet1U, OffsetSet1V, OffsetSet2, OffsetSet2U, OffsetSet2V, DistortionStrength,
                         MipBias, LightMapStrength, LightMapPower, Saturation, OffsetSet3, OffsetSet3U, OffsetSet3V,
                         Fat, RotationSet1, RotationSet2, RotationSet3, ScaleSet1, ScaleSet1U, ScaleSet1V, ScaleSet2,
                         ScaleSet2U, ScaleSet2V, ScaleSet3, ScaleSet3U, ScaleSet3V, ZBias, InnerGrowAValue,
                         InnerGrowAPower, InnerGrowAStrength, InnerGrowALimit, InnerGrowBValue, InnerGrowBPower,
                         InnerGrowBStrength, InnerGrowBLimit, InnerGrowAColor, InnerGrowBColor]

all_shader_uniforms = [*texture_nodes, *shader_uniforms_vp_fp]


# These dictionaries are how the shader uniforms are accessed from other files via factory methods
shader_uniforms_from_names = {cls.__name__: cls for cls in all_shader_uniforms}
shader_uniforms_from_defn = {(cls.__name__, cls.num_floats): cls for cls in all_shader_uniforms}
shader_textures = {cls.__name__: cls for cls in texture_nodes}
shader_uniforms_vp_fp_from_names = {cls.__name__: cls for cls in shader_uniforms_vp_fp}