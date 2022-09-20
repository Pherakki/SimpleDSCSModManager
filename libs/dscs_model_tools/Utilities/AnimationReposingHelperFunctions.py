

def try_replace_rest_pose_elements(transform_elements, idx, fcurve, rotation=False, location=False):
    """
    If the input fcurve has a value on its first frame, replace the appropriate value in transform_elements with it.
    """
    if len(fcurve.frames):
        assert fcurve.frames[0] == 0, "First frame was not at frame 0."
        print(fcurve.values[0])
        # transform_elements[idx] = fcurve.values[0]
        transform_elements[idx] = (1., 0., 0., 0) if rotation else ((0., 0., 0.) if location else (1., 1., 1.))
    return transform_elements
