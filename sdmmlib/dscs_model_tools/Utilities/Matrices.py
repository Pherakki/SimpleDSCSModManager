import numpy as np
from .Rotation import quat_to_matrix, rotation_matrix_to_quat


def get_total_transform(idx, parent_bones, bone_data):
    if idx == -1:
        rot = np.eye(3)
        loc = np.zeros(3)
        return rot, loc
    else:
        parent_idx = parent_bones[idx]
        parent_rot, parent_loc = get_total_transform(parent_idx, parent_bones, bone_data)

        rot = np.dot(parent_rot.T, quat_to_matrix(bone_data[idx][0]))
        loc = np.dot(parent_rot, np.array(bone_data[idx][1][:3])) + parent_loc

        return rot, loc


def get_total_transform_matrix(idx, parent_bones, bone_data, WXYZ=False):
    if idx == -1:
        bone_matrix = np.eye(4)
        return bone_matrix
    else:
        parent_idx = parent_bones[idx]
        parent_bone_matrix = get_total_transform_matrix(parent_idx, parent_bones, bone_data)
        diff_bone_matrix = generate_transform_matrix(*bone_data[idx], WXYZ)

        return np.dot(parent_bone_matrix, diff_bone_matrix)


def calculate_bone_matrix_relative_to_parent_inverted(idx, parent_bones, inv_bind_pose_matrices):
    par = parent_bones[idx]
    if par == -1:
        pbm = np.eye(4)
    else:
        pbm = inv_bind_pose_matrices[par]
    bm = inv_bind_pose_matrices[idx]

    # Remember that bm is the inverse of the bone matrix, and pbm is the inverse of the parent's bone matrix,
    # so what we're really doing here is multiplying the inverse parent matrix by the ordinary child matrix.
    # This leaves us with just the transform of the child relative to the parent, since all the parent's contribution
    # to the child's transform has been taken off
    diff = np.dot(pbm, np.linalg.inv(bm))

    return diff


def calculate_bone_matrix_relative_to_parent(idx, parent_bones, bone_matrices):
    par = parent_bones[idx]
    if par == -1:
        pbm = np.eye(4)
    else:
        pbm = bone_matrices[par]
    bm = bone_matrices[idx]

    diff = np.dot(np.linalg.inv(pbm), bm)

    return diff


def generate_transform_delta(parent_bones, rest_pose, inverse_bind_pose_matrices):
    result = []
    for i, (inverse_matrix, (quat, loc, scl)) in enumerate(zip(inverse_bind_pose_matrices, rest_pose)):
        bone_matrix = np.zeros((4, 4))
        bone_matrix[:3, :3] = quat_to_matrix(quat)
        bone_matrix[:3, 3] = loc[:3]
        bone_matrix[3, 3] = 1

        bm = calculate_bone_matrix_relative_to_parent_inverted(i, parent_bones, inverse_bind_pose_matrices)
        diff = np.dot(np.linalg.inv(bm), bone_matrix)
        diff_quat = rotation_matrix_to_quat(diff[:3, :3])
        diff_pos = diff[:3, 3]
        result.append([diff_quat, diff_pos, scl[:3]])
    return result


def generate_transform_matrix(quat, location, scale, WXYZ=False):
    translation_matrix = generate_translation_matrix(location[:3])
    rotation_matrix = generate_rotation_matrix(quat, WXYZ)
    scale_matrix = generate_scale_matrix(scale[:3])

    return np.dot(translation_matrix, np.dot(rotation_matrix, scale_matrix))


def generate_translation_matrix(location):
    matrix = np.eye(4)
    matrix[:3, 3] = location
    return matrix


def generate_rotation_matrix(quat, WXYZ=False):
    matrix = np.eye(4)
    matrix[:3, :3] = quat_to_matrix(quat, WXYZ)
    return matrix


def generate_scale_matrix(scale):
    return np.diag([*scale, 1])


def decompose_matrix(transform, WXYZ=False):
    scale_x = np.sqrt(np.sum(transform[:3, 0]**2))
    scale_y = np.sqrt(np.sum(transform[:3, 1]**2))
    scale_z = np.sqrt(np.sum(transform[:3, 2]**2))

    translation = transform[:3, 3]

    rotation = transform[:3, :3]
    rotation[:3, 0] /= scale_x
    rotation[:3, 1] /= scale_y
    rotation[:3, 2] /= scale_z
    quat = rotation_matrix_to_quat(rotation, WXYZ)

    return translation, quat, np.array([scale_x, scale_y, scale_z])


def apply_transform_to_keyframe(transform, index, rotations, rotation_interpolator, locations, location_interpolator, scales, scale_interpolator, flipped_order=False):
    quat = rotations.get(index, rotation_interpolator(index))
    trans = locations.get(index, location_interpolator(index))
    scale = scales.get(index, scale_interpolator(index))

    if np.any(np.isnan(quat)) or np.any(np.isnan(trans)) or np.any(np.isnan(scale)):
        print("Interpolated values:", quat, trans, scale)
        assert 0

    transformation_matrix = generate_transform_matrix(quat, trans, scale, WXYZ=True)
    if flipped_order:
        total_transformation = np.dot(transformation_matrix, transform)
    else:
        total_transformation = np.dot(transform, transformation_matrix)
    return decompose_matrix(total_transformation, WXYZ=True)
