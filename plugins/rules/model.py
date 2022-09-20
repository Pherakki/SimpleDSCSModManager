import os

from src.Utils.MdlEditImpl import parse_mdledit
from sdmmlib.dscs_model_tools.Utilities.StringHashing import dscs_name_hash


class mdledit_name:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    requires_open_file = True
    
    group = "Model"
    
    def __call__(self, build_data):
        mdledit_data = parse_mdledit(build_data.source, build_data.softcodes, build_data.softcode_lookup)
        
        name_interface = build_data.data
        bone_names = set(name_interface.bone_names)
        for npc_edit_data in mdledit_data.editNPC:
            npc_bone_name = "npc_{:0>4}".format(npc_edit_data["id"])
            if npc_bone_name not in bone_names:
                name_interface.bone_names.append(npc_bone_name)
    
class mdledit_skel:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    requires_open_file = True
    
    group = "Model"
    
    def __call__(self, build_data):
        mdledit_data = parse_mdledit(build_data.source, build_data.softcodes, build_data.softcode_lookup)
        
        skel_interface = build_data.data
        bone_indices = build_data.bone_indices
        for npc_edit_data in mdledit_data.editNPC:
            npc_bone_name = "npc_{:0>4}".format(npc_edit_data["id"])
            idx = bone_indices[npc_bone_name]
                          
            rotation = npc_edit_data.get("rotation", [1., 0., 0., 0])
            assert len(rotation) == 4 and type(rotation) == list, f"MdlEdit \'{os.path.join(build_data.mod, build_data.src)}\' editNPC entry \'{npc_bone_name}\' contains an invalid quaternion: \'{rotation}\'"

            position = npc_edit_data.get("position", [0., 0., 0])
            assert len(position) == 3 and type(position) == list, f"MdlEdit \'{os.path.join(build_data.mod, build_data.src)}\' editNPC entry \'{npc_bone_name}\' contains an invalid position: \'{position}\'"
            
            scale = npc_edit_data.get("scale", [1., 1., 1])
            assert len(scale) == 3 and type(scale) == list, f"MdlEdit \'{os.path.join(build_data.mod, build_data.src)}\' editNPC entry \'{npc_bone_name}\' contains an invalid scale: \'{scale}\'"

            # Swap from WXYZ to XYZW
            rotation = [*rotation[1:], rotation[0]]
            bone_matrix_data = [rotation, [*position, 1], [*scale, 1]]
            
            if idx < len(skel_interface.rest_pose):
                skel_interface.rest_pose[idx] = bone_matrix_data
            else:
                skel_interface.rest_pose.append(bone_matrix_data)
                skel_interface.parent_bones.append((idx, -1))
                skel_interface.bone_name_hashes.append(bytes.fromhex(dscs_name_hash(npc_bone_name)))
    
class mdledit_geom:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    requires_open_file = True
    
    group = "Model"
    
    def __call__(self, build_data):
        mdledit_data = parse_mdledit(build_data.source, build_data.softcodes, build_data.softcode_lookup)
        
        geom_interface = build_data.data
        bone_indices = build_data.bone_indices
        for npc_edit_data in mdledit_data.editNPC:
            npc_bone_name = "npc_{:0>4}".format(npc_edit_data["id"])
            idx = bone_indices[npc_bone_name]
            
            # If the bone already exists, ignore it
            # If it doesn't, then add a new matrix
            if idx < len(geom_interface.inverse_bind_pose_matrices):
                pass
            else:
                geom_interface.inverse_bind_pose_matrices.append([[1., 0., 0., 0.],
                                                                  [0., 1., 0., 0.],
                                                                  [0., 0., 1., 0.],
                                                                  [0., 0., 0., 1.]])
    
class mdledit_anim:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    requires_open_file = True
    
    group = "Model"
    
    def __call__(self, build_data):
        pass
                
class mdledit_phys:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    requires_open_file = True
    
    group = "Model"
    
    def __call__(self, build_data):
        pass
