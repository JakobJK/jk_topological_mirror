from typing import Tuple, List, Set, Optional, Dict, Union
from maya import cmds
import maya.api.OpenMaya as om

from jk_topological_mirror.constants import Axis3d, AxisUV 

def get_face_center(mesh_fn: om.MFnMesh, face_index: int) -> Tuple[float, float, float]:
    """Returns the world-space center of all vertices of a face."""
    vert_ids = mesh_fn.getPolygonVertices(face_index)
    points = [mesh_fn.getPoint(v, om.MSpace.kWorld) for v in vert_ids]
    n = len(points)
    if n == 0:
        return (0.0, 0.0, 0.0)
    center = om.MPoint()
    for p in points:
        center += p
    center /= n
    return (center.x, center.y, center.z)

def get_polygon_center_uv(mesh_fn: om.MFnMesh, face_index: int) -> om.MFloatPoint:
    """
    Calculates the average UV coordinate (center) of a specific face.

    Args:
        mesh_fn (om.MFnMesh): The function set for the mesh being queried.
        face_index (int): The index of the polygon face.

    Returns:
        om.MFloatPoint: The average U and V coordinates as an MFloatPoint.
    """
    uv_set_name: str = mesh_fn.currentUVSetName()
    face_it: om.MItMeshPolygon = om.MItMeshPolygon(mesh_fn.object())
    face_it.setIndex(face_index)
    
    u_coords: List[float] = []
    v_coords: List[float] = []
    
    for i in range(face_it.polygonVertexCount()):
        try:
            u, v = face_it.getUV(i, uv_set_name)
            u_coords.append(u)
            v_coords.append(v)
        except:
            continue
            
    if not u_coords:
        return om.MFloatPoint(0.0, 0.0)

    avg_u: float = sum(u_coords) / len(u_coords)
    avg_v: float = sum(v_coords) / len(v_coords)
    
    return om.MFloatPoint(avg_u, avg_v)

def is_uvs_sorted(mesh_fn: om.MFnMesh, face_index_a: int, face_index_b: int, axis: AxisUV = AxisUV.U) -> bool:
    """
    Returns True if face_index_a is 'smaller' than face_index_b on the given UV axis.
    U: True if A is to the Left of B.
    V: True if A is Above B (consistent with your prepare_uvs logic).
    """
    center_a: om.MFloatPoint = get_polygon_center_uv(mesh_fn, face_index_a)
    center_b: om.MFloatPoint = get_polygon_center_uv(mesh_fn, face_index_b)
    
    if axis == AxisUV.U:
        return center_a.x < center_b.x
    
    return center_a.y > center_b.y

def sort_by_world_space(mesh_fn: om.MFnMesh, face_a: int, face_b: int, axis: Axis3d, negative=False) -> bool:
    """
    Determines if face_a is 'greater than' face_b along a specific world axis
    based on the face centers.

    Args:
        mesh_fn (om.MFnMesh): The function set for the mesh being queried.
        face_a (int): The index of the first polygon face.
        face_b (int): The index of the second polygon face.
        axis (Axis3d): The world axis (X, Y, or Z) used for the comparison.
        negative (bool): If True, invert the comparison.

    Returns:
        bool: True if face_a's center is greater than face_b's along the axis, else False.
    """
    center_a = get_face_center(mesh_fn, face_a)
    center_b = get_face_center(mesh_fn, face_b)

    axis_index = {Axis3d.X: 0, Axis3d.Y: 1, Axis3d.Z: 2}[axis]
    a_val = center_a[axis_index]
    b_val = center_b[axis_index]

    return a_val > b_val if not negative else a_val < b_val

def get_camera_vectors(camera: str) -> tuple[om.MVector, om.MVector, om.MVector]:
    """
    Returns camera world-space basis vectors:
    (right, up, forward)

    Note:
        Maya cameras look down -Z in local space.
    """
    matrix = cmds.getAttr(camera + ".worldMatrix[0]")
    m = om.MMatrix(matrix)

    right = om.MVector(m[0], m[1], m[2]).normal()
    up = om.MVector(m[4], m[5], m[6]).normal()

    # Maya forward is -Z
    forward = om.MVector(-m[8], -m[9], -m[10]).normal()

    return right, up, forward

def get_face_uvs(mesh: om.MObject, face_index: int) -> Set[Tuple[float, float]]:
    """
    Returns a set of UV coordinates for a specific face.

    Args:
        mesh (om.MObject): The mesh object to query.
        face_index (int): The index of the polygon face.

    Returns:
        Set[Tuple[float, float]]: A set of (u, v) tuples representing unique UV coordinates for the face.
    """
    uv_set_name: str = om.MFnMesh(mesh).currentUVSetName()
    face_it: om.MItMeshPolygon = om.MItMeshPolygon(mesh)
    face_it.setIndex(face_index)
    return {tuple(face_it.getUV(i, uv_set_name)) for i in range(face_it.polygonVertexCount())}

def get_connect_uvs(mesh: om.MObject, face_index1: int, face_index2: int) -> List[Tuple[float, float]]:
    """
    Returns indices of UVs shared between two faces.
    """
    uvs1: Set[Tuple[float, float]] = get_face_uvs(mesh, face_index1)
    uvs2: Set[Tuple[float, float]] = get_face_uvs(mesh, face_index2)
    return list(uvs1.intersection(uvs2))

def get_shared_vertex_center_world(mesh_fn: om.MFnMesh, face_index1: int, face_index2: int) -> Optional[Tuple[float, float, float]]:
    """
    Returns the UV coordinates shared between two faces.

    Args:
        mesh (om.MObject): The mesh object to query.
        face_index1 (int): The index of the first polygon face.
        face_index2 (int): The index of the second polygon face.

    Returns:
        List[Tuple[float, float]]: A list of (u, v) tuples that are common to both faces.
    """
    face_it1: om.MItMeshPolygon = om.MItMeshPolygon(mesh_fn.object())
    face_it1.setIndex(face_index1)
    verts1: Set[int] = set(face_it1.getVertices())

    face_it2: om.MItMeshPolygon = om.MItMeshPolygon(mesh_fn.object())
    face_it2.setIndex(face_index2)
    verts2: Set[int] = set(face_it2.getVertices())

    shared_verts: Set[int] = verts1.intersection(verts2)

    if shared_verts:
        points: om.MPointArray = mesh_fn.getPoints(om.MSpace.kObject)
        shared_points: List[om.MPoint] = [points[v] for v in shared_verts]

        avg_point: om.MPoint = om.MPoint()
        for pt in shared_points:
            avg_point += pt
        avg_point /= len(shared_points)

        return (avg_point.x, avg_point.y, avg_point.z)
    return None

def get_edge_vector(dag_path: om.MDagPath, component: om.MObject) -> om.MVector:
    """
    Calculates the normalized vector of the specified edge in world space.
    """
    edge_it = om.MItMeshEdge(dag_path, component)
    
    # Get world-space points directly from the iterator
    p1 = edge_it.point(0, om.MSpace.kWorld)
    p2 = edge_it.point(1, om.MSpace.kWorld)
    
    edge_vector = om.MVector(p2 - p1)
    edge_vector.normalize()
    return edge_vector

def get_shared_uv_center(mesh_fn: om.MFnMesh, face_index1: int, face_index2: int) -> Optional[Tuple[float, float]]:
    """
    Returns the average UV center shared between two faces.

    Args:
        mesh_fn (om.MFnMesh): The function set for the mesh being queried.
        face_index1 (int): The index of the first polygon face.
        face_index2 (int): The index of the second polygon face.

    Returns:
        Optional[Tuple[float, float]]: The average (u, v) coordinate of the shared UVs, 
                                       or None if no UVs are shared.
    """
    uv_set_name: str = mesh_fn.currentUVSetName()

    face_it1: om.MItMeshPolygon = om.MItMeshPolygon(mesh_fn.object())
    face_it1.setIndex(face_index1)
    uvs1: Set[int] = {face_it1.getUVIndex(i, uv_set_name) for i in range(face_it1.polygonVertexCount())}

    face_it2: om.MItMeshPolygon = om.MItMeshPolygon(mesh_fn.object())
    face_it2.setIndex(face_index2)
    uvs2: Set[int] = {face_it2.getUVIndex(i, uv_set_name) for i in range(face_it2.polygonVertexCount())}

    shared_uvs: List[int] = list(uvs1.intersection(uvs2))

    if shared_uvs:
        uv_coords: List[Tuple[float, float]] = [mesh_fn.getUV(uv, uv_set_name) for uv in shared_uvs]
        center_u: float = sum(uv[0] for uv in uv_coords) / len(uv_coords)
        center_v: float = sum(uv[1] for uv in uv_coords) / len(uv_coords)
        return center_u, center_v

    return None

def get_active_component() -> Tuple[om.MDagPath, om.MObject]:
    """
    Returns the current selection's DagPath and component MObject.

    Args:
        None

    Returns:
        Tuple[om.MDagPath, om.MObject]: A tuple containing the DAG path to the node 
                                       and the MObject representing the selected components.
    """
    selection: List[str] = cmds.ls(selection=True, fl=True)
    selection_list: om.MSelectionList = om.MSelectionList()
    selection_list.add(selection[0])
    return selection_list.getComponent(0)


def get_intended_mirror_axis(
    edge_vector: om.MVector,
    cam_right: om.MVector,
    cam_up: om.MVector,
) -> tuple[Axis3d, bool]:
    """
    Determine the mirror axis and its direction based on the edge and camera orientation.

    Returns:
        Tuple[Axis3d, bool]: (mirror_axis, is_positive)
    """

    edge = edge_vector.normal()
    right = cam_right.normal()
    up = cam_up.normal()

    edge_axis = get_dominant_axis(edge)
    right_axis = get_dominant_axis(right)
    up_axis = get_dominant_axis(up)

    if edge_axis == right_axis:
        chosen = up
    elif edge_axis == up_axis:
        chosen = right
    else:
        chosen = right if abs(right * edge) < abs(up * edge) else up

    axis_str = get_dominant_axis(chosen)
    axis_vec = chosen

    is_positive = getattr(axis_vec, axis_str.lower()) >= 0

    return Axis3d[axis_str], is_positive

def is_edge_selected() -> bool:
    """
    Checks if a single edge is selected.

    Args:
        None

    Returns:
        bool: True if exactly one edge component is selected, False otherwise.
    """
    selection: List[str] = cmds.ls(selection=True, fl=True)
    if not (len(selection) == 1 and ".e[" in selection[0]):
        cmds.warning("Please select a single edge")
        return False
    return True


def get_dominant_axis(
    vector: Union[om.MVector, om.MFloatVector]
) -> str:
    abs_vec = [abs(vector.x), abs(vector.y), abs(vector.z)]
    index = abs_vec.index(max(abs_vec))
    return ("X", "Y", "Z")[index]


def get_current_active_camera() -> str:
    try:
        raw_panel = cmds.playblast(activeEditor=True)
        active_panel = raw_panel.split('|')[-1]
        camera_transform = cmds.modelEditor(active_panel, query=True, camera=True)
        return cmds.ls(camera_transform, long=True)[0] if camera_transform else ""
    except:
        return ""


def are_uvs_horizontal(uvs: List[Tuple[float, float]]) -> bool:
    """
    Checks if shared UV indices suggest a horizontal split.

    Args:
        uvs (List[Tuple[float, float]]): A list of two (u, v) coordinate tuples.

    Returns:
        bool: True if the horizontal distance (u) between the UVs is greater 
              than the vertical distance (v), suggesting a horizontal orientation.
    """
    (u1, v1), (u2, v2) = uvs
    return abs(u1 - u2) > abs(v1 - v2)
