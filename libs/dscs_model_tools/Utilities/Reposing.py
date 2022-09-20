import bpy
import numpy as np


def set_new_rest_pose(armature_name, bone_names, rest_pose_delta):
    """
    This function implements the instructions of this [1] exceptionally useful blog post in Python script form.
    The steps of this blog post are pointed out in the code with comments.
    It takes an armature with a given rest pose and deforms the meshes attached to that armature such that a pose
    becomes a new rest pose. It should be relatively general.

    [1] https://nixart.wordpress.com/2013/03/28/modifying-the-rest-pose-in-blender/
    """
    # 1) Select your armature and go in “Pose Mode”.
    model_armature = bpy.data.objects[armature_name]
    bpy.context.view_layer.objects.active = model_armature
    bpy.ops.object.mode_set(mode="POSE")

    # 2) Pose your object in your new rest pose.
    for i, (bone_name, (rest_quat, rest_pos, rest_scl)) in enumerate(zip(bone_names, rest_pose_delta)):
        model_armature.pose.bones[bone_name].rotation_quaternion = np.roll(rest_quat, 1)
        model_armature.pose.bones[bone_name].location = rest_pos
        if rest_scl != (0., 0., 0.):
            model_armature.pose.bones[bone_name].scale = rest_scl

    # 3) Go in “Object Mode” and select your deformed object.
    bpy.ops.object.mode_set(mode="OBJECT")
    for ob in model_armature.children:
        bpy.context.view_layer.objects.active = ob
        # 4) In the object’s “Object Modifiers” stack, copy the “Armature Modifier” by pressing the “Copy” button. You should have two “Armature Modifiers”, one above the other in the stack, with the same parameters. This will deform your object twice, but it is ok. If you go in “Edit Mode”, you will see that the mesh has been deformed in your new rest pose.
        first_armature_modifier = [m for m in ob.modifiers if m.type == 'ARMATURE'][0]
        bpy.ops.object.modifier_copy(modifier=first_armature_modifier.name)
        # 5) Apply the first “Armature Modifier” (the top one), but keep the bottom one. The latter will replace the old “Armature Modifier” and will allow to pose your object with respect to your new rest pose. At this point, the object will still be deformed twice. That is because we need to apply the current pose as the new rest pose.
        bpy.ops.object.modifier_apply(modifier=first_armature_modifier.name)
    # 6) Select your armature and go in “Pose Mode”.
    bpy.context.view_layer.objects.active = model_armature
    bpy.ops.object.mode_set(mode="POSE")
    # 7) “Apply Pose as Rest Pose” in the “Pose” menu. This will clear the double deformation and put your object in your new rest pose.
    bpy.ops.pose.armature_apply()
