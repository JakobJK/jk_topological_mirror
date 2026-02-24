import maya.api.OpenMaya as om

from typing import Dict

from jk_topological_mirror.constants import Axis3d

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

def mirror_vertices(mesh_path: om.MDagPath, mapping: Dict[int, int], center_point: om.MPoint, flip: bool, axis: Axis3d) -> None:
    mesh_fn: om.MFnMesh = om.MFnMesh(mesh_path)
    
    # We use kObject to match your preferred local-space logic
    points: om.MPointArray = mesh_fn.getPoints(om.MSpace.kObject)

    # Map the Axis3d enum to the integer index
    axis_map = {Axis3d.X: 0, Axis3d.Y: 1, Axis3d.Z: 2}
    axis_index: int = axis_map[axis]
    center_val: float = center_point[axis_index]

    for vert_a, vert_b in mapping.items():
        pos_a: om.MPoint = points[vert_a]
        pos_b: om.MPoint = points[vert_b]

        # Handle center-line vertices (where vert_a is vert_b)
        if vert_a == vert_b:
            for i in range(3):
                if i == axis_index:
                    pos_a[i] = center_val
                else:
                    # Average the other axes to keep the seam clean
                    avg = (pos_a[i] + pos_b[i]) / 2
                    pos_a[i] = avg
            points[vert_a] = pos_a
            continue

        # Standard mirroring logic: Delta reflection
        # We calculate how far vert_a is from the center, then place vert_b on the opposite side
        for i in range(3):
            if i == axis_index:
                delta = pos_a[i] - center_val
                pos_b[i] = center_val - delta
            else:
                # Maintain the same height/depth as the source vertex
                pos_b[i] = pos_a[i]

        points[vert_a] = pos_a
        points[vert_b] = pos_b

    mesh_fn.setPoints(points, om.MSpace.kObject)
    mesh_fn.updateSurface()
