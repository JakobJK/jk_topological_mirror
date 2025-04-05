from maya import cmds
import maya.api.OpenMaya as om

from jk_topological_mirror.utilities import get_active_panel_type, edge_selected, get_shared_vertex_center_world, get_shared_uv_center, get_connect_uvs,get_camera_forward_vector, get_dominant_axis_with_sign, get_current_active_camera, are_uvs_horizontal, get_active_component
from jk_topological_mirror.traversal import traverse, get_component_mapping, not_sorted_left_and_right, get_polygon_center_uv
from jk_topological_mirror.transform import mirror_uvs, mirror_vertices

def main(average=False, left_to_right=True, top_to_bottom=True):
    if not edge_selected():
        return

    panel_type = get_active_panel_type()
    traversal_type = "uvs" if panel_type == "uvEditor" else "verts"

    uv_connectivity = traversal_type == "uvs"

    edge_path, edge_component = get_active_component()
    edge_it = om.MItMeshEdge(edge_path, edge_component)
    edge_index = edge_it.index()
    
    connected_faces = edge_it.getConnectedFaces()
    if len(connected_faces) != 2:
        cmds.warning("Selected edge is not connected to exactly two faces.")
        return

    mesh_fn = om.MFnMesh(edge_path)
    left_face_index, right_face_index = connected_faces
    
    if traversal_type == 'uvs':
        connected_uvs = get_connect_uvs(mesh_fn.object(), left_face_index, right_face_index)
        if len(connected_uvs) != 2:
            cmds.warning("The two connected faces has to share two UVs!")
            return

        axis = 'U' if are_uvs_horizontal(connected_uvs) else 'V'
        is_sorted = not_sorted_left_and_right(mesh_fn, left_face_index, right_face_index, axis)
        
        if axis == 'U' and (not is_sorted and left_to_right):
            left_face_index, right_face_index = right_face_index, left_face_index
        
        if axis == 'V' and (not is_sorted and top_to_bottom):
            left_face_index, right_face_index = right_face_index, left_face_index
        
        
        result = traverse(mesh_fn.object(), left_face_index, right_face_index, edge_index, edge_index, uv_connectivity)
        if not result:
            cmds.warning("Could not define symmetry.")
            return
        
        visited_left, visited_right = result
        uv_mapping = get_component_mapping(mesh_fn.object(), 'uvs', visited_left, visited_right)
        edge_center = get_shared_uv_center(mesh_fn, left_face_index, right_face_index)
        mirror_uvs(edge_path, uv_mapping, edge_center, average, axis)

    else:

        result = traverse(mesh_fn.object(), left_face_index, right_face_index, edge_index, edge_index, uv_connectivity)
        if not result:
            cmds.warning("Could not define symmetry.")
            return
        
        visited_left, visited_right = result
        vertex_mapping = get_component_mapping(mesh_fn.object(), 'verts', visited_left, visited_right)
        camera = get_current_active_camera()
        vector = get_camera_forward_vector(camera)
        dominant, sign = get_dominant_axis_with_sign(vector)

        # Get Edge orientation and Camera Angle
        edge_center = get_shared_vertex_center_world(mesh_fn, left_face_index, right_face_index)

        mirror_vertices(edge_path, vertex_mapping, edge_center, average, axis="X")
