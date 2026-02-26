import maya.api.OpenMaya as om

from typing import Dict, Tuple, List, Union

from jk_topological_mirror.constants import Axis3d, AxisUV, MirrorMode

def mirror_uv_pos(
    uv_index_a: int, 
    uv_index_b: int, 
    u_list: List[float], 
    v_list: List[float], 
    center: float, 
    is_u_axis: bool):
    """Copies UV position from A to B across the center line.

    Args:
        uv_index_a (int): The index of the source UV coordinate.
        uv_index_b (int): The index of the target UV coordinate.
        u_list (List[float]): The list of U-coordinate values.
        v_list (List[float]): The list of V-coordinate values.
        center (float): The coordinate value of the axis of symmetry.
        is_u_axis (bool): If True, mirrors across the U-axis; otherwise, mirrors across the V-axis.
    """
    if uv_index_a == uv_index_b:
        if is_u_axis: u_list[uv_index_a] = center
        else: v_list[uv_index_a] = center
        return

    if is_u_axis:
        delta = u_list[uv_index_a] - center
        u_list[uv_index_b] = center - delta
        v_list[uv_index_b] = v_list[uv_index_a]
    else:
        delta = v_list[uv_index_a] - center
        v_list[uv_index_b] = center - delta
        u_list[uv_index_b] = u_list[uv_index_a]


def mirror_uv_flip(
    uv_index_a: int, 
    uv_index_b: int, 
    u_list: List[float], 
    v_list: List[float], 
    center: float, 
    is_u_axis: bool):
    """Copies UV position from A to B across the center line.

    Args:
        uv_index_a (int): The index of the source UV coordinate.
        uv_index_b (int): The index of the target UV coordinate.
        u_list (List[float]): The list of U-coordinate values.
        v_list (List[float]): The list of V-coordinate values.
        center (float): The coordinate value of the axis of symmetry.
        is_u_axis (bool): If True, mirrors across the U-axis; otherwise, mirrors across the V-axis.
    """
    old_u_a, old_v_a = u_list[uv_index_a], v_list[uv_index_a]
    u_b, v_b = u_list[uv_index_b], v_list[uv_index_b]

    if is_u_axis:
        u_list[uv_index_a] = center - (u_b - center)
        v_list[uv_index_a] = v_b
        u_list[uv_index_b] = center - (old_u_a - center)
        v_list[uv_index_b] = old_v_a
    else:
        v_list[uv_index_a] = center - (v_b - center)
        u_list[uv_index_a] = u_b
        v_list[uv_index_b] = center - (old_v_a - center)
        u_list[uv_index_b] = old_u_a


def mirror_uv_average(
    uv_index_a: int, 
    uv_index_b: int, 
    u_list: List[float], 
    v_list: List[float], 
    center: float, 
    is_u_axis: bool):
    """Averages UV positions of A and B across the center line.

    Args:
        uv_index_a (int): The index of the first UV coordinate.
        uv_index_b (int): The index of the second UV coordinate to be mirrored with the first.
        u_list (List[float]): The list of U-coordinate values to be modified.
        v_list (List[float]): The list of V-coordinate values to be modified.
        center (float): The coordinate value of the axis of symmetry.
        is_u_axis (bool): If True, performs averaging across the U-axis; otherwise, across the V-axis.
    """
    u_a, v_a = u_list[uv_index_a], v_list[uv_index_a]
    u_b, v_b = u_list[uv_index_b], v_list[uv_index_b]

    if uv_index_a == uv_index_b:
        if is_u_axis: u_list[uv_index_a] = center
        else: v_list[uv_index_a] = center
        return

    if is_u_axis:
        dist_a = u_a - center
        dist_b = center - u_b
        avg_dist = (dist_a + dist_b) / 2.0
        u_list[uv_index_a] = center + avg_dist
        u_list[uv_index_b] = center - avg_dist
        avg_v = (v_a + v_b) / 2.0
        v_list[uv_index_a] = v_list[uv_index_b] = avg_v
    else:
        dist_a = v_a - center
        dist_b = center - v_b
        avg_dist = (dist_a + dist_b) / 2.0
        v_list[uv_index_a] = center + avg_dist
        v_list[uv_index_b] = center - avg_dist
        avg_u = (u_a + u_b) / 2.0
        u_list[uv_index_a] = u_list[uv_index_b] = avg_u

def mirror_uvs(
    mesh_path: om.MDagPath, 
    uvs_mapping: Dict[int, int], 
    edge_center: Union[om.MPoint, Tuple[float, float]], 
    mode: MirrorMode, 
    axis: AxisUV):
    """Applies UV mirroring to a mesh based on the provided mapping and mode.

    Args:
        mesh_path (om.MDagPath): The DAG path to the mesh node.
        uvs_mapping (Dict[int, int]): A dictionary mapping source UV indices to target UV indices.
        edge_center (Union[om.MPoint, Tuple[float, float]]): The reference center point for the mirror operation.
        mode (MirrorMode): The mirroring strategy to apply (MIRROR, FLIP, or AVERAGE).
        axis (AxisUV): The UV axis (U or V) across which the mirroring occurs.
    """
    mesh_fn: om.MFnMesh = om.MFnMesh(mesh_path)
    uv_set_name: str = mesh_fn.currentUVSetName()
    uv_array_u, uv_array_v = mesh_fn.getUVs(uv_set_name)

    is_u_axis: bool = (axis == AxisUV.U)
    center: float = edge_center[0] if is_u_axis else edge_center[1]

    mode_map = {
        MirrorMode.MIRROR: mirror_uv_pos,
        MirrorMode.FLIP: mirror_uv_flip,
        MirrorMode.AVERAGE: mirror_uv_average
    }
    
    selected_func = mode_map[mode]

    for uv_a, uv_b in uvs_mapping.items():
        selected_func(
            uv_a, 
            uv_b, 
            uv_array_u, 
            uv_array_v, 
            center, 
            is_u_axis
        )

    mesh_fn.setUVs(uv_array_u, uv_array_v, uv_set_name)
    mesh_fn.updateSurface()


def mirror_pos(
    vertex_index_a: int, 
    vertex_index_b: int, 
    points: om.MPointArray, 
    center_point: om.MPoint, 
    axis_index: int
    ) -> Tuple[om.MPoint, om.MPoint]:
    """Copies position from vertex_a to vertex_b across the reflection plane.

    Args:
        vertex_index_a (int): The index of the source vertex.
        vertex_index_b (int): The index of the target vertex.
        points (om.MPointArray): The array of vertex positions.
        center_point (om.MPoint): The point defining the center of the reflection plane.
        axis_index (int): The index of the axis (0=X, 1=Y, 2=Z) to mirror across.

    Returns:
        Tuple[om.MPoint, om.MPoint]: A tuple containing the updated position for vertex A and vertex B.
    """
    pos_a: om.MPoint = points[vertex_index_a]
    pos_b: om.MPoint = points[vertex_index_b]
    center_val: float = center_point[axis_index]

    if vertex_index_a == vertex_index_b:
        pos_a[axis_index] = center_val
        return pos_a, pos_a

    for i in range(3):
        if i == axis_index:
            delta: float = pos_a[i] - center_val
            pos_b[i] = center_val - delta
        else:
            pos_b[i] = pos_a[i]

    return pos_a, pos_b

def mirror_flip(
    vertex_index_a: int, 
    vertex_index_b: int, 
    points: om.MPointArray, 
    center_point: om.MPoint, 
    axis_index: int
    ) -> Tuple[om.MPoint, om.MPoint]:
    """Reflects both vertices across the center point.

    Args:
        vertex_index_a (int): The index of the first vertex to be flipped.
        vertex_index_b (int): The index of the second vertex to be flipped.
        points (om.MPointArray): The array of vertex positions.
        center_point (om.MPoint): The point defining the reflection plane.
        axis_index (int): The index of the axis (0=X, 1=Y, 2=Z) to flip across.

    Returns:
        Tuple[om.MPoint, om.MPoint]: A tuple containing the new position for vertex A and vertex B.
    """
    pos_a: om.MPoint = points[vertex_index_a]
    pos_b: om.MPoint = points[vertex_index_b]
    center_val: float = center_point[axis_index]

    old_pos_a: om.MPoint = om.MPoint(pos_a)
    
    for i in range(3):
        if i == axis_index:
            pos_a[i] = center_val - (pos_b[i] - center_val)
        else:
            pos_a[i] = pos_b[i]

    for i in range(3):
        if i == axis_index:
            pos_b[i] = center_val - (old_pos_a[i] - center_val)
        else:
            pos_b[i] = old_pos_a[i]

    return pos_a, pos_b


def mirror_average(
    vertex_index_a: int, 
    vertex_index_b: int, 
    points: om.MPointArray, 
    center_point: om.MPoint, 
    axis_index: int
    )-> Tuple[om.MPoint, om.MPoint]:
    """Averages the positions of vertex_a and vertex_b across the reflection plane.

    Args:
        vertex_index_a (int): The index of the first vertex to be averaged.
        vertex_index_b (int): The index of the second vertex to be averaged.
        points (om.MPointArray): The array of vertex positions.
        center_point (om.MPoint): The point defining the reflection plane.
        axis_index (int): The index of the axis (0=X, 1=Y, 2=Z) to average across.

    Returns:
        Tuple[om.MPoint, om.MPoint]: A tuple containing the averaged position for vertex A and vertex B.
    """
    pos_a: om.MPoint = points[vertex_index_a]
    pos_b: om.MPoint = points[vertex_index_b]
    center_val: float = center_point[axis_index]

    if vertex_index_a == vertex_index_b:
        pos_a[axis_index] = center_val
        for i in range(3):
            if i != axis_index:
                pos_a[i] = (pos_a[i] + pos_b[i]) / 2.0
        return pos_a, pos_a

    for i in range(3):
        if i == axis_index:
            dist_a: float = pos_a[i] - center_val
            dist_b: float = center_val - pos_b[i]
            avg_dist: float = (dist_a + dist_b) / 2.0
            pos_a[i] = center_val + avg_dist
            pos_b[i] = center_val - avg_dist
        else:
            avg_val: float = (pos_a[i] + pos_b[i]) / 2.0
            pos_a[i] = avg_val
            pos_b[i] = avg_val

    return pos_a, pos_b


def mirror_vertices(
    mesh_path: om.MDagPath, 
    mapping: Dict[int, int], 
    center_point: om.MPoint, 
    mode: MirrorMode, 
    axis: Axis3d):
    """Applies vertex mirroring to a mesh based on the provided mapping and mode.

    Args:
        mesh_path (om.MDagPath): The DAG path to the mesh node.
        mapping (Dict[int, int]): A dictionary mapping source vertex indices to target vertex indices.
        center_point (om.MPoint): The reference center point for the reflection plane.
        mode (MirrorMode): The mirroring strategy to apply (MIRROR, FLIP, or AVERAGE).
        axis (Axis3d): The 3D axis (X, Y, or Z) across which the mirroring occurs.
    """
    mesh_fn: om.MFnMesh = om.MFnMesh(mesh_path)
    points: om.MPointArray = mesh_fn.getPoints(om.MSpace.kObject)

    axis_map = {Axis3d.X: 0, Axis3d.Y: 1, Axis3d.Z: 2}
    axis_index: int = axis_map[axis]

    mode_map = {
        MirrorMode.MIRROR: mirror_pos,
        MirrorMode.FLIP: mirror_flip,
        MirrorMode.AVERAGE: mirror_average
    }
    
    selected_func = mode_map[mode]

    for vert_a, vert_b in mapping.items():
        res_a, res_b = selected_func(
            vert_a, 
            vert_b, 
            points, 
            center_point, 
            axis_index
        )
        points[vert_a] = res_a
        points[vert_b] = res_b

    mesh_fn.setPoints(points, om.MSpace.kObject)
    mesh_fn.updateSurface()
