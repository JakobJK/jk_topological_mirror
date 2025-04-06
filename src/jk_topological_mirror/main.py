from maya import cmds
import maya.api.OpenMaya as om

from jk_topological_mirror.utilities import edge_selected, get_shared_vertex_center_world, get_selected_edge_vector, get_shared_uv_center, get_connect_uvs,get_camera_forward_vector, get_dominant_axis_with_sign, get_current_active_camera, are_uvs_horizontal, get_active_component
from jk_topological_mirror.traversal import traverse, get_component_mapping, not_sorted_left_and_right
from jk_topological_mirror.transform import mirror_uvs, mirror_vertices

def uvs(average=False, left_to_right=True, top_to_bottom=True):
    if not edge_selected():
        return

    edge_path, edge_component = get_active_component()
    edge_it = om.MItMeshEdge(edge_path, edge_component)
    edge_index = edge_it.index()
    
    connected_faces = edge_it.getConnectedFaces()
    if len(connected_faces) != 2:
        cmds.warning("Selected edge is not connected to exactly two faces.")
        return

    mesh_fn = om.MFnMesh(edge_path)
    left_face_index, right_face_index = connected_faces

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
    
    
    result = traverse(mesh_fn.object(), left_face_index, right_face_index, edge_index, edge_index, True)
    if not result:
        cmds.warning("Could not define symmetry.")
        return
    
    visited_left, visited_right = result
    uv_mapping = get_component_mapping(mesh_fn.object(), 'uvs', visited_left, visited_right)
    edge_center = get_shared_uv_center(mesh_fn, left_face_index, right_face_index)
    mirror_uvs(edge_path, uv_mapping, edge_center, average, axis)

def vertices(average=False, left_to_right=True, top_to_bottom=True):
    if not edge_selected():
        return

    edge_path, edge_component = get_active_component()
    edge_it = om.MItMeshEdge(edge_path, edge_component)
    edge_index = edge_it.index()
    
    connected_faces = edge_it.getConnectedFaces()
    if len(connected_faces) != 2:
        cmds.warning("Selected edge is not connected to exactly two faces.")
        return

    mesh_fn = om.MFnMesh(edge_path)
    left_face_index, right_face_index = connected_faces

    result = traverse(mesh_fn.object(), left_face_index, right_face_index, edge_index, edge_index, False)
    if not result:
        cmds.warning("Could not define symmetry.")
        return
    
    visited_left, visited_right = result
    vertex_mapping = get_component_mapping(mesh_fn.object(), 'verts', visited_left, visited_right)
    camera = get_current_active_camera()
    vector = get_camera_forward_vector(camera)
    dominant, sign = get_dominant_axis_with_sign(vector)

    print(f"[Camera] Forward vector: {vector}")
    print(f"[Camera] Dominant axis: {dominant}, Sign: {sign}")

    edge_vector = get_selected_edge_vector()
    print(f"[Edge] Direction vector: {edge_vector}")

    other_axes = {'X', 'Y', 'Z'} - {dominant}
    closest = max(other_axes, key=lambda a: abs(getattr(edge_vector, a.lower())))
    axis = ({'X', 'Y', 'Z'} - {dominant, closest}).pop()

    print(f"[Axis] Closest to edge: {closest}")
    print(f"[Axis] Selected mirror axis: {axis}")

    edge_center = get_shared_vertex_center_world(mesh_fn, left_face_index, right_face_index)
    print(f"[Edge] Shared center (world): {edge_center}")

    mirror_vertices(edge_path, vertex_mapping, edge_center, average, axis=axis)
