import maya.api.OpenMaya as om

from typing import Dict, Tuple

from jk_topological_mirror.constants import Axis3d, MirrorMode

def mirror_uvs(mesh, uvs_mapping, edge_center, average=False, axis='U'):
    uv_set_name = om.MFnMesh(mesh).currentUVSetName()
    mesh_fn = om.MFnMesh(mesh)
    uv_array_u, uv_array_v = mesh_fn.getUVs(uv_set_name)

    center = edge_center[0] if axis == 'U' else edge_center[1]

    for uv_a, uv_b in uvs_mapping.items():
        u_a, v_a = uv_array_u[uv_a], uv_array_v[uv_a]
        u_b, v_b = uv_array_u[uv_b], uv_array_v[uv_b]

        if average:
            if axis == 'U':
                avg_distance = (abs(u_a - center) + abs(u_b - center)) / 2
                mirrored_u_a = center + avg_distance if center < u_a else center - avg_distance
                mirrored_u_b = center - avg_distance if center < u_a else center + avg_distance
                uv_array_u[uv_a], uv_array_u[uv_b] = mirrored_u_a, mirrored_u_b
                avg_v = (v_a + v_b) / 2
                uv_array_v[uv_a], uv_array_v[uv_b] = avg_v, avg_v
            else:
                avg_distance = (abs(v_a - center) + abs(v_b - center)) / 2
                mirrored_v_a = center + avg_distance if center < v_a else center - avg_distance
                mirrored_v_b = center - avg_distance if center < v_a else center + avg_distance
                uv_array_v[uv_a], uv_array_v[uv_b] = mirrored_v_a, mirrored_v_b
                avg_u = (u_a + u_b) / 2
                uv_array_u[uv_a], uv_array_u[uv_b] = avg_u, avg_u
        else:
            if axis == 'U':
                distance = abs(u_a - center)
                mirrored_u = center - distance if center < u_a else center + distance
                uv_array_u[uv_b] = mirrored_u
                uv_array_v[uv_b] = v_a
            else:
                distance = abs(v_a - center)
                mirrored_v = center - distance if center < v_a else center + distance
                uv_array_v[uv_b] = mirrored_v
                uv_array_u[uv_b] = u_a

        if uv_a == uv_b:
            if axis == 'U':
                uv_array_u[uv_a] = center
            else:
                uv_array_v[uv_a] = center

    mesh_fn.setUVs(uv_array_u, uv_array_v, uv_set_name)
    mesh_fn.updateSurface()


def mirror_pos(
    vertex_index_a: int, 
    vertex_index_b: int, 
    points: om.MPointArray, 
    center_point: om.MPoint, 
    axis_index: int
) -> Tuple[om.MPoint, om.MPoint]:
    """
    Copies position from vertex_a to vertex_b across the reflection plane.
    Returns: Tuple[om.MPoint, om.MPoint] (pos_a, pos_b)
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
    """
    Reflects both vertices across the center point. 
    If a vertex is on the center, the reflection results in the same position.
    """
    pos_a: om.MPoint = points[vertex_index_a]
    pos_b: om.MPoint = points[vertex_index_b]
    center_val: float = center_point[axis_index]

    # Capture original state of A before modification
    old_pos_a: om.MPoint = om.MPoint(pos_a)
    
    # Vertex A reflects to where B was (relative to center)
    for i in range(3):
        if i == axis_index:
            pos_a[i] = center_val - (pos_b[i] - center_val)
        else:
            pos_a[i] = pos_b[i]

    # Vertex B reflects to where A was (relative to center)
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
) -> Tuple[om.MPoint, om.MPoint]:
    """
    Averages the positions of vertex_a and vertex_b across the reflection plane.
    Returns: Tuple[om.MPoint, om.MPoint] (pos_a, pos_b)
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
    axis: Axis3d
) -> None:
    """
    Applies vertex mirroring to a mesh based on the provided mapping and mode.
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
