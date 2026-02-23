import maya.api.OpenMaya as om
from typing import Dict, Union

from jk_topological_mirror.constants import Axis3d, AxisUV

def mirror_uvs(
    mesh_dag: om.MDagPath, 
    uv_mapping: Dict[int, int], 
    edge_center: Union[om.MPoint, om.MFloatPoint], 
    average: bool = False, 
    axis: AxisUV = AxisUV.U
) -> None:
    """
    Mirrors UV coordinates across a specified UV axis based on topological mapping.

    Args:
        mesh_dag: DAG path of the mesh to modify.
        uv_mapping: Dictionary mapping source UV IDs to target UV IDs.
        edge_center: Reference center point for the mirror operation.
        average: If True, averages position between source and target.
        axis: AxisUV enum member (U or V).
    """
    mesh_function: om.MFnMesh = om.MFnMesh(mesh_dag)
    uv_set_name: str = mesh_function.currentUVSetName()
    uv_array_u, uv_array_v = mesh_function.getUVs(uv_set_name)

    center_value: float = edge_center[0] if axis == AxisUV.U else edge_center[1]

    for uv_source, uv_target in uv_mapping.items():
        u_source: float = uv_array_u[uv_source]
        v_source: float = uv_array_v[uv_source]
        u_target: float = uv_array_u[uv_target]
        v_target: float = uv_array_v[uv_target]

        if average:
            if axis == AxisUV.U:
                dist_a: float = abs(u_source - center_value)
                dist_b: float = abs(u_target - center_value)
                avg_dist: float = (dist_a + dist_b) / 2.0
                
                uv_array_u[uv_source] = center_value + avg_dist if center_value < u_source else center_value - avg_dist
                uv_array_u[uv_target] = center_value - avg_dist if center_value < u_source else center_value + avg_dist
                
                avg_v: float = (v_source + v_target) / 2.0
                uv_array_v[uv_source], uv_array_v[uv_target] = avg_v, avg_v
            else:
                dist_a = abs(v_source - center_value)
                dist_b = abs(v_target - center_value)
                avg_dist = (dist_a + dist_b) / 2.0
                
                uv_array_v[uv_source] = center_value + avg_dist if center_value < v_source else center_value - avg_dist
                uv_array_v[uv_target] = center_value - avg_dist if center_value < v_source else center_value + avg_dist
                
                avg_u: float = (u_source + u_target) / 2.0
                uv_array_u[uv_source], uv_array_u[uv_target] = avg_u, avg_u
        else:
            if axis == AxisUV.U:
                dist: float = abs(u_source - center_value)
                mirrored_u: float = center_value - dist if center_value < u_source else center_value + dist
                uv_array_u[uv_target] = mirrored_u
                uv_array_v[uv_target] = v_source
            else:
                dist = abs(v_source - center_value)
                mirrored_v: float = center_value - dist if center_value < v_source else center_value + dist
                uv_array_v[uv_target] = mirrored_v
                uv_array_u[uv_target] = u_source

        if uv_source == uv_target:
            if axis == AxisUV.U:
                uv_array_u[uv_source] = center_value
            else:
                uv_array_v[uv_source] = center_value

    mesh_function.setUVs(uv_array_u, uv_array_v, uv_set_name)
    mesh_function.updateSurface()

def mirror_vertices(
    mesh_dag: om.MDagPath, 
    vertex_mapping: Dict[int, int], 
    edge_center: om.MPoint, 
    average: bool = False, 
    axis: Axis3d = Axis3d.X
) -> None:
    """
    Mirrors vertex positions across a specified 3D axis.

    Args:
        mesh_dag: DAG path of the mesh to modify.
        vertex_mapping: Dictionary mapping source vertex IDs to target vertex IDs.
        edge_center: Reference center point for the mirror operation.
        average: If True, averages position between source and target.
        axis: Axis3d enum member (X, Y, or Z).
    """
    mesh_function: om.MFnMesh = om.MFnMesh(mesh_dag)
    points: om.MPointArray = mesh_function.getPoints(om.MSpace.kObject)

    axis_index_map: Dict[Axis3d, int] = {Axis3d.X: 0, Axis3d.Y: 1, Axis3d.Z: 2}
    axis_idx: int = axis_index_map[axis]
    center_val: float = edge_center[axis_idx]

    for v_src, v_tgt in vertex_mapping.items():
        pos_src: om.MPoint = om.MPoint(points[v_src])
        pos_tgt: om.MPoint = om.MPoint(points[v_tgt])

        if v_src == v_tgt:
            for i in range(3):
                if i == axis_idx:
                    pos_src[i] = pos_tgt[i] = center_val
                else:
                    avg: float = (pos_src[i] + pos_tgt[i]) / 2.0
                    pos_src[i] = pos_tgt[i] = avg
            points[v_src], points[v_tgt] = pos_src, pos_tgt
            continue

        if average:
            for i in range(3):
                if i == axis_idx:
                    d_src: float = pos_src[i] - center_val
                    d_tgt: float = pos_tgt[i] - center_val
                    avg_d: float = (abs(d_src) + abs(d_tgt)) / 2.0
                    pos_src[i] = center_val + avg_d * (1.0 if d_src >= 0 else -1.0)
                    pos_tgt[i] = center_val + avg_d * (1.0 if d_tgt >= 0 else -1.0)
                else:
                    avg = (pos_src[i] + pos_tgt[i]) / 2.0
                    pos_src[i] = pos_tgt[i] = avg
        else:
            for i in range(3):
                if i == axis_idx:
                    pos_tgt[i] = center_val - (pos_src[i] - center_val)
                else:
                    pos_tgt[i] = pos_src[i]

        points[v_src], points[v_tgt] = pos_src, pos_tgt

    mesh_function.setPoints(points, om.MSpace.kObject)
    mesh_function.updateSurface()
