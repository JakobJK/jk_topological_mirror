from maya import cmds
import maya.api.OpenMaya as om

import maya.api.OpenMaya as om

def mirror_uvs(mesh, uvs_mapping, edge_center, symmetrice=False, axis='U'):
    uv_set_name = om.MFnMesh(mesh).currentUVSetName()
    mesh_fn = om.MFnMesh(mesh)
    uv_array_u, uv_array_v = mesh_fn.getUVs(uv_set_name)

    center = edge_center[0] if axis == 'U' else edge_center[1]

    for uv_a, uv_b in uvs_mapping.items():
        u_a, v_a = uv_array_u[uv_a], uv_array_v[uv_a]
        u_b, v_b = uv_array_u[uv_b], uv_array_v[uv_b]

        if symmetrice:
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

from maya import cmds
import maya.api.OpenMaya as om

def mirror_vertices(mesh, verts_mapping, edge_center, symmetrice=False, axis='X'):
    mesh_fn = om.MFnMesh(mesh)
    points = mesh_fn.getPoints(om.MSpace.kObject)

    axis_index = {'X': 0, 'Y': 1, 'Z': 2}[axis.upper()]
    center = edge_center[axis_index]

    for vert_a, vert_b in verts_mapping.items():
        pos_a = points[vert_a]
        pos_b = points[vert_b]

        coord_a = pos_a[axis_index]
        coord_b = pos_b[axis_index]

        if symmetrice:
            avg_distance = (abs(coord_a - center) + abs(coord_b - center)) / 2
            mirrored_a = center + avg_distance if center < coord_a else center - avg_distance
            mirrored_b = center - avg_distance if center < coord_a else center + avg_distance

            pos_a[axis_index] = mirrored_a
            pos_b[axis_index] = mirrored_b

            for idx in {0, 1, 2} - {axis_index}:
                avg_coord = (pos_a[idx] + pos_b[idx]) / 2
                pos_a[idx] = avg_coord
                pos_b[idx] = avg_coord
        else:
            distance = abs(coord_a - center)
            mirrored_coord = center - distance if center < coord_a else center + distance
            pos_b[axis_index] = mirrored_coord

            for idx in {0, 1, 2} - {axis_index}:
                pos_b[idx] = pos_a[idx]

        if vert_a == vert_b:
            pos_a[axis_index] = center

        points[vert_a] = pos_a
        points[vert_b] = pos_b

    mesh_fn.setPoints(points, om.MSpace.kObject)
    mesh_fn.updateSurface()
