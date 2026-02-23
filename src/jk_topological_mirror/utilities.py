from typing import Tuple, List, Set, Optional, Dict, Union
from maya import cmds
import maya.api.OpenMaya as om

from jk_topological_mirror.constants import Axis3d, AxisUV, CameraDirection

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

def get_intended_mirror_axis(edge_vector: om.MVector, camera_forward_vector: om.MVector) -> Axis3d:
    """
    Determines the mirror plane axis based on the edge direction and camera view.

    Args:
        edge_center (om.MVector): The world-space vector of the selected edge.
        camera_forward_vector (om.MVector): The forward-looking vector of the active camera.

    Returns:
        Axis3d: The enum member representing the calculated mirror plane axis.
    """
    edge_axis: str = get_dominant_axis(edge_vector)
    forward_axis: str = get_dominant_axis(camera_forward_vector)
    result_str = ({'X', 'Y', 'Z'} - {edge_axis, forward_axis}).pop()
    return Axis3d[result_str]

def is_uvs_sorted(mesh_fn: om.MFnMesh, left_face_index: int, right_face_index: int, axis: AxisUV = AxisUV.U) -> bool:
    """
    Checks if two faces are sorted correctly along a UV axis.

    Args:
        mesh_fn (om.MFnMesh): The function set for the mesh being queried.
        left_face_index (int): The index of the first polygon face.
        right_face_index (int): The index of the second polygon face.
        axis (AxisUV): The UV axis to check alignment against (U or V).

    Returns:
        bool: True if the faces are sorted correctly along the specified axis, False otherwise.
    """
    left_center: om.MFloatPoint = get_polygon_center_uv(mesh_fn, left_face_index)
    right_center: om.MFloatPoint = get_polygon_center_uv(mesh_fn, right_face_index)
    
    return left_center.x < right_center.x if axis == AxisUV.U else left_center.y > right_center.y

def sort_by_world_space(mesh_fn: om.MFnMesh, face_a: int, face_b: int, axis: Axis3d) -> bool:
    """
    Determines if face_a is 'greater than' face_b along a specific world axis.

    Args:
        mesh_fn (om.MFnMesh): The function set for the mesh being queried.
        face_a (int): The index of the first polygon face.
        face_b (int): The index of the second polygon face.
        axis (Axis3d): The world axis (X, Y, or Z) used for the comparison.

    Returns:
        bool: True if face_a's shared center value is greater than face_b's, False otherwise.
    """
    center_a: Optional[Tuple[float, float, float]] = get_shared_vertex_center_world(mesh_fn, face_a, face_b)
    if center_a is None:
        return False  

    center_b: Optional[Tuple[float, float, float]] = get_shared_vertex_center_world(mesh_fn, face_b, face_a)
    if center_b is None:
        return False

    axis_index: int = {Axis3d.X: 0, Axis3d.Y: 1, Axis3d.Z: 2}[axis]
    a_val: float = center_a[axis_index]
    b_val: float = center_b[axis_index]

    return a_val > b_val  

def get_camera_vector(camera: str, direction: CameraDirection) -> om.MVector:
    """
    Extracts normalized world-space vectors from the camera matrix.

    Args:
        camera (str): The name of the camera shape or transform node.
        direction (CameraDirection): The desired direction vector (RIGHT, UP, or FORWARD).

    Returns:
        om.MVector: The normalized world-space vector for the specified direction.

    Raises:
        ValueError: If the direction provided is not a valid CameraDirection.
    """
    matrix: List[float] = cmds.getAttr(camera + ".worldMatrix[0]")
    m: om.MMatrix = om.MMatrix(matrix)

    if direction == CameraDirection.RIGHT:
        vec = om.MVector(m[0], m[1], m[2])
    elif direction == CameraDirection.UP:
        vec = om.MVector(m[4], m[5], m[6])
    elif direction == CameraDirection.FORWARD:
        vec = om.MVector(m[8], m[9], m[10])
    else:
        raise ValueError(f"Unknown camera vector direction: {direction}")

    vec.normalize()
    return vec

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

def get_selected_edge_vector() -> om.MVector:
    """
    Calculates the normalized vector of the currently selected edge in world space.

    Returns:
        om.MVector: The normalized world-space vector of the selected edge.
    """
    sel: om.MSelectionList = om.MGlobal.getActiveSelectionList()
    dag_path, component = sel.getComponent(0)
    mesh_fn: om.MFnMesh = om.MFnMesh(dag_path)

    # Calling next(it) advanced the iterator, but the variable edge_it was unused.
    edges: om.MItMeshEdge = om.MItMeshEdge(dag_path, component)
    next(edges)
    
    v1: om.MVector = om.MVector(mesh_fn.getPoint(edges.vertexId(0), om.MSpace.kWorld))
    v2: om.MVector = om.MVector(mesh_fn.getPoint(edges.vertexId(1), om.MSpace.kWorld))
    
    vec: om.MVector = (v2 - v1)
    vec.normalize()
    return vec

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

def is_edge_aligned_with_camera(camera: str, edge_vector: om.MVector) -> bool:
    """
    Determines if the edge aligns with camera's up or right vector.

    Args:
        camera (str): The name of the camera to check alignment against.
        edge_vector (om.MVector): The world-space vector of the edge.

    Returns:
        bool: True if the edge is aligned with the camera's up or right orientation, 
              or if the alignment is ambiguous.
    """
    camera_alignment: Dict[str, str] = get_camera_axis_alignment(camera)
    edge_axis: str = get_dominant_axis(edge_vector)

    is_vertical: bool = edge_axis == camera_alignment["up"]
    is_horizontal: bool = edge_axis == camera_alignment["right"]

    mirror_type: str = "vertical" if is_vertical else "horizontal" if is_horizontal else "ambiguous"

    if mirror_type == "vertical":
        up_vector: om.MVector = get_camera_vector(camera, CameraDirection.UP)
        axis: str = camera_alignment["up"].lower()
        return (getattr(edge_vector, axis) * getattr(up_vector, axis)) >= 0

    if mirror_type == "horizontal":
        right_vector: om.MVector = get_camera_vector(camera, CameraDirection.RIGHT)
        axis: str = camera_alignment["right"].lower()
        return (getattr(edge_vector, axis) * getattr(right_vector, axis)) >= 0

    return True

def get_dominant_axis(vector: Union[om.MVector, om.MFloatVector]) -> str:
    """
    Returns the Axis3d member name as a string based on the largest absolute component.

    Args:
        vector (Union[om.MVector, om.MFloatVector]): The vector to evaluate.

    Returns:
        str: The string representation of the dominant axis ("X", "Y", or "Z").
    """
    abs_vec: List[float] = [abs(vector.x), abs(vector.y), abs(vector.z)]
    index: int = abs_vec.index(max(abs_vec))
    return [Axis3d.X.value, Axis3d.Y.value, Axis3d.Z.value][index]

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

def get_active_panel_type() -> str:
    """
    Returns the mirror mode based on the currently focused Maya panel.

    Args:
        None

    Returns:
        str: The type of panel focused ("modelPanel", "uvEditor", etc.).
    """
    panel: str = cmds.getPanel(withFocus=True)
    panel_type: str = cmds.getPanel(typeOf=panel)

    if panel_type == "modelPanel":
        return "modelPanel"
    if panel_type == "scriptedPanel":
        ptype: str = cmds.scriptedPanel(panel, query=True, type=True)
        return "uvEditor" if ptype == "polyTexturePlacementPanel" else ptype
    return panel_type

def get_camera_axis_alignment(camera: str) -> Dict[str, str]:
    """
    Maps camera local directions to world dominant axes.

    Args:
        camera (str): The name of the camera node.

    Returns:
        Dict[str, str]: A dictionary mapping 'right', 'up', and 'forward' 
                        to their dominant world axes ('X', 'Y', or 'Z').
    """
    matrix: List[float] = cmds.getAttr(camera + ".worldMatrix[0]")
    m: om.MMatrix = om.MMatrix(matrix)

    right: om.MVector = om.MVector(m[0], m[1], m[2])
    up: om.MVector = om.MVector(m[4], m[5], m[6])
    forward: om.MVector = om.MVector(m[8], m[9], m[10])

    return {
        "right": get_dominant_axis(right),
        "up": get_dominant_axis(up),
        "forward": get_dominant_axis(forward)
    }

def get_dominant_axis_with_sign(vector: Union[om.MVector, om.MFloatVector]) -> Tuple[str, str]:
    """
    Returns the dominant world axis and its direction (sign).

    Args:
        vector (Union[om.MVector, om.MFloatVector]): The vector to evaluate.

    Returns:
        Tuple[str, str]: A tuple containing the axis name ("X", "Y", or "Z") 
                         and the direction ("positive" or "negative").
    """
    dominant: str = get_dominant_axis(vector)
    val: float = getattr(vector, dominant.lower())
    sign: str = 'positive' if val >= 0 else 'negative'
    
    return dominant, sign

def get_current_active_camera() -> str:
    """
    Returns the camera shape from the last active viewport, 
    even if the script UI currently has focus.

    Args:
        None

    Returns:
        str: The full DAG path to the camera's shape node.
    """
    try:
        active_panel = cmds.playblast(query=True, activeEditor=True)
    except RuntimeError:
        return ""

    if not active_panel or cmds.getPanel(typeOf=active_panel) != "modelPanel":
        return ""

    camera_transform = cmds.modelEditor(active_panel, query=True, camera=True)
    
    if not camera_transform:
        return ""
    shapes = cmds.listRelatives(camera_transform, shapes=True, fullPath=True)
    return shapes[0] if shapes else ""


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
