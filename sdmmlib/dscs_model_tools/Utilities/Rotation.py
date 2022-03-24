import numpy as np


def rotation_matrix_to_quat(matrix, WXYZ=False):
    """
    Ref: http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/
    Order is XYZW by default
    """
    # Will probably be more numerically stable to just pick the largest out of each diag element + trace than checking
    # if Tr > 0
    tr = np.trace(matrix)
    test_array = np.array([*matrix.diagonal(), tr])
    largest_result_idx = test_array.argmax()

    quat = np.zeros(4)
    if largest_result_idx == 3:
        S = np.sqrt(1. + tr) * 2
        quat[3] = 0.25*S  # W
        quat[0] = (matrix[2, 1] - matrix[1, 2]) / S  # X
        quat[1] = (matrix[0, 2] - matrix[2, 0]) / S  # Y
        quat[2] = (matrix[1, 0] - matrix[0, 1]) / S  # Z
    else:
        i = largest_result_idx
        j = (i + 1) % 3
        k = (j + 1) % 3

        S = np.sqrt(1. - tr + 2*matrix[i, i]) * 2
        quat[3] = (matrix[k, j] - matrix[j, k]) / S
        quat[i] = 0.25*S
        quat[j] = (matrix[j, i] + matrix[i, j]) / S
        quat[k] = (matrix[k, i] + matrix[i, k]) / S

    return np.roll(quat, WXYZ)


def quat_to_matrix(quat, WXYZ=False):
    quat = np.roll(quat, -WXYZ)
    x, y, z, w = quat
    x2, y2, z2, _ = quat**2

    return 2*np.array([[.5 - y2 - z2,    x*y - z*w,    x*z + y*w],
                       [   x*y + z*w, .5 - x2 - z2,    y*z - x*w],
                       [   x*z - y*w,    y*z + x*w, .5 - x2 - y2]])


def bone_matrix_from_rotation_location(quaternion, position):
    bone_matrix = np.zeros((4, 4))
    bone_matrix[:3, :3] = quat_to_matrix(quaternion)
    bone_matrix[:3, 3] = position
    bone_matrix[3, 3] = 1

    return bone_matrix


def XYZ_eulers_to_quat(eulers, WXYZ=False):
    phi, theta, psi = eulers
    cphi = np.cos(phi/2)
    sphi = np.sin(phi/2)
    ctheta = np.cos(theta/2)
    stheta = np.sin(theta/2)
    cpsi = np.cos(psi/2)
    spsi = np.sin(psi/2)

    w = cphi * ctheta * cpsi + sphi * stheta * spsi
    x = sphi * ctheta * cpsi - cphi * stheta * spsi
    y = cphi * stheta * cpsi + sphi * ctheta * spsi
    z = cphi * ctheta * spsi - sphi * stheta * cpsi

    return np.roll([x, y, z, w], shift=WXYZ)


def normalise_quaternion(quat):
    magnitude = np.dot(quat, quat)
    return quat / (magnitude**.5)
