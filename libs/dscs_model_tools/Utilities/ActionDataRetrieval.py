import numpy as np

from .Interpolation import lerp, slerp, produce_interpolation_method
from .Rotation import XYZ_eulers_to_quat


#############################
# STUFF THAT SHOULD BE USED #
#############################
def get_action_data(action, curve_defaults):
    animation_data = {}
    fcurve_groups = group_fcurves_by_bone_and_type(action)
    for bone_name, group in fcurve_groups.items():
        animation_data[bone_name] = {'rotation_quaternion': {},
                                     'location': {},
                                     'scale': {},
                                     'rotation_euler': {}}
        # Get whether any of the locations, rotations, and scales are animated; plus the f-curves for those
        # that are
        elements_used, bone_data = get_used_animation_elements_in_group(group)
        # For each set that is animated, interpolate missing keyframes for each component of the relevant vector
        # on each keyframe where at least one element is used
        for curve_type, isUsed in elements_used.items():
            if isUsed:
                curve_data = interpolate_missing_frame_elements(bone_data[curve_type], curve_defaults[curve_type], lerp)
                zipped_data = zip_vector_elements(curve_data)
                animation_data[bone_name][curve_type] = zipped_data
        convert_eulers_to_quats(animation_data[bone_name])
    return animation_data


#####################
# UTILITY FUNCTIONS #
#####################
def convert_eulers_to_quats(group):
    if 'rotation_euler' in group:
        euler_data = group.pop("rotation_euler")
        for frame_idx, frame_value in euler_data.items():
            group['rotation_quaternion'][frame_idx] = XYZ_eulers_to_quat(frame_value, WXYZ=True)


def get_bone_name_from_fcurve(fcurve):
    return fcurve.data_path.split('[')[1].split(']')[0][1:-1]


def get_fcurve_type(fcurve):
    return fcurve.data_path.split('.')[-1]


def group_fcurves_by_bone_and_type(action):
    res = {}
    for fcurve in action.fcurves:
        if fcurve.data_path[:10] == 'pose.bones':
            bone_name = get_bone_name_from_fcurve(fcurve)
            if bone_name not in res:
                res[bone_name] = {'rotation_quaternion': [None, None, None, None],
                                  'location':            [None, None, None],
                                  'scale':               [None, None, None],
                                  'rotation_euler':      [None, None, None]}
            curve_type = get_fcurve_type(fcurve)
            array_index = fcurve.array_index

            res[bone_name][curve_type][array_index] = fcurve
    return res


def get_used_animation_elements_in_group(group):
    """
    Summary
    -------
    Takes a list of f-curves and assigns the keyframe point co-ordinates in each f-curve to the appropriate transform
    and array index of a returned dictionary.

    The animation export module should probably be refactored so that the groups that get passed into this function
    are either locations, rotations, or scales, so that all three are not handled simultaneously, but rather by three
    separate function calls.

    Parameters
    ----------
    :parameters:
    group -- A list of Blender f-curve objects.

    Returns
    -------
    :returns:
    A two-element tuple:
    - The first element is a dictionary in the shape {'location': bool, 'rotation_quaternion': bool, 'scale': bool} that
      states whether any of the input f-curves are of any of those types
    - The second element is a dictionary in the shape
                {'location': {0: {}, 1: {}, 2: {}},
                 'rotation_quaternion': {0: {}, 1: {}, 2: {}, 3: {}},
                 'scale': {0: {}, 1: {}, 2: {}}},
      where the integers are the array indices of the appropriate f-curves. Each array index is also given a dictionary
      as above, which contains the frame index and the f-curve value as key-value pairs.
    """
    elements_used = {'location': False,
                     'rotation_quaternion': False,
                     'scale': False,
                     'rotation_euler': False}

    bone_data = {'rotation_quaternion': [{}, {}, {}, {}],
                 'location':            [{}, {}, {}],
                 'scale':               [{}, {}, {}],
                 'rotation_euler': [{}, {}, {}]}
    for curve_type in group:
        for curve_idx, f_curve in enumerate(group[curve_type]):
            if f_curve is None:
                continue
            elements_used[curve_type] = True
            bone_data[curve_type][curve_idx] = {k-1: v for k, v in [kfp.co for kfp in f_curve.keyframe_points]}

    return elements_used, bone_data


def get_all_required_frames(curve_data):
    """
    Returns all keys in a list of dictionaries as a sorted list of rounded integers plus the rounded-up final key,
    assuming all keys are floating-point values.
    """
    res = set()
    for dct in curve_data:
        iter_keys = tuple(dct.keys())
        for key in iter_keys:
            res.add(key)
            # res.add(int(round(key)))
        res.add(np.ceil(iter_keys[-1]))
        # res.add(int(np.ceil(iter_keys[-1])))
    return sorted(list(res))


def interpolate_missing_frame_elements(curve_data, default_values, interpolation_function):
    """
    DSCS requires animations to be stored as whole quaternions, locations, and scales.
    This function ensures that every passed f-curve has a value at every frame referenced by all f-curves - e.g. if
    a location has values at frame 30 on its X f-curve but not on its Y and Z f-curves, the Y and Z values at frame 30
    will be interpolated from the nearest frames on the Y and Z f-curves respectively and stored in the result.
    """
    # First get every frame required by the vector and which will be passed on to DSCS
    # The returned frames are integers, even if the input frames are floats, because DSCS only likes integer frames
    all_frame_idxs = get_all_required_frames(curve_data)
    for (component_idx, framedata), default_value in zip(enumerate(curve_data), default_values):
        # Get all the frames at which the curve has data
        component_frame_idxs = list(framedata.keys())
        # Produce a function that will return the value for the frame, based on how many frames are available
        interp_method = produce_interpolation_method(component_frame_idxs, framedata, default_value, interpolation_function)
        new_framedata = {}
        # Generate the DSCS-compatible data
        for frame_idx in all_frame_idxs:
            if frame_idx not in component_frame_idxs:
                new_framedata[frame_idx] = interp_method(frame_idx)
            else:
                new_framedata[frame_idx] = framedata[frame_idx]

        curve_data[component_idx] = new_framedata

    return curve_data


def zip_vector_elements(curve_data):
    """
    Takes n dictionaries in a list, with each dictionary containing the frame indices (as keys) and values (as values)
    of a single component of a vector. All dictionaries must have exactly the same keys (frame indices).
    Returns a single dictionary with the frame indices as keys, and the vector components for that frame stored in a
    list as the value for that key.
    """
    new_curve_data = {}
    for frame_idxs in zip(*[list(e.keys()) for e in curve_data]):
        for frame_idx in frame_idxs:
            assert frame_idx == frame_idxs[0]
        frame_idx = frame_idxs[0]
        new_curve_data[frame_idx] = np.array([e[frame_idx] for e in curve_data])
    return new_curve_data
