"""_summary_
"""

from maya import cmds
import maya.api.OpenMaya as om


def get_face_uvs(mesh, face_index):
    uv_set_name = om.MFnMesh(mesh).currentUVSetName()
    face_it = om.MItMeshPolygon(mesh)
    face_it.setIndex(face_index)
    return {tuple(face_it.getUV(i, uv_set_name)) for i in range(face_it.polygonVertexCount())}

def get_connect_uvs(mesh, face_index1, face_index2):
    uvs1 = get_face_uvs(mesh, face_index1)
    uvs2 = get_face_uvs(mesh, face_index2)
    return list(uvs1.intersection(uvs2))

def get_shared_vertex_center_world(mesh_fn, face_index1, face_index2):
    face_it1 = om.MItMeshPolygon(mesh_fn.dagPath())
    face_it1.setIndex(face_index1)
    verts1 = set(face_it1.getVertices())

    face_it2 = om.MItMeshPolygon(mesh_fn.dagPath())
    face_it2.setIndex(face_index2)
    verts2 = set(face_it2.getVertices())

    shared_verts = verts1.intersection(verts2)

    if shared_verts:
        points = mesh_fn.getPoints(om.MSpace.kWorld)
        shared_points = [points[v] for v in shared_verts]

        avg_point = om.MPoint()
        for pt in shared_points:
            avg_point += pt
        avg_point /= len(shared_points)

        return (avg_point.x, avg_point.y, avg_point.z)

    return None


def get_shared_uv_center(mesh_fn, face_index1, face_index2):
    """
    Get the center value of the UVs shared by two faces.
    """
    uv_set_name = mesh_fn.currentUVSetName()

    face_it1 = om.MItMeshPolygon(mesh_fn.dagPath())
    face_it1.setIndex(face_index1)
    uvs1 = {face_it1.getUVIndex(i, uv_set_name) for i in range(face_it1.polygonVertexCount())}

    face_it2 = om.MItMeshPolygon(mesh_fn.dagPath())
    face_it2.setIndex(face_index2)
    uvs2 = {face_it2.getUVIndex(i, uv_set_name) for i in range(face_it2.polygonVertexCount())}

    shared_uvs = list(uvs1.intersection(uvs2))

    if shared_uvs:
        uv_coords = [mesh_fn.getUV(uv, uv_set_name) for uv in shared_uvs]
        center_u = sum(uv[0] for uv in uv_coords) / len(uv_coords)
        center_v = sum(uv[1] for uv in uv_coords) / len(uv_coords)
        return (center_u, center_v)

    return None

def get_active_component():
    selection = cmds.ls(selection=True, fl=True)
    selection_list = om.MSelectionList()
    selection_list.add(selection[0])
    return selection_list.getComponent(0)

def edge_selected():
    selection = cmds.ls(selection=True, fl=True)
    if not (len(selection) == 1 and ".e[" in selection[0]):
        cmds.warning("Please select a single edge")
        return False
    return True

def get_active_panel_type():
    panel = cmds.getPanel(withFocus=True)
    panel_type = cmds.getPanel(typeOf=panel)

    if panel_type == "modelPanel":
        return "modelPanel"
    if panel_type == "scriptedPanel":
        ptype = cmds.scriptedPanel(panel, q=True, type=True)
        return "uvEditor" if ptype == "polyTexturePlacementPanel" else ptype
    return panel_type

def get_camera_forward_vector(camera):
    matrix = cmds.getAttr(camera + ".worldMatrix[0]")
    m = om.MMatrix(matrix)
    forward = om.MVector(m[8], m[9], m[10])
    forward.normalize()
    return forward

def get_dominant_axis_with_sign(vector):
    components = {'X': vector.x, 'Y': vector.y, 'Z': vector.z}
    dominant = max(components, key=lambda k: abs(components[k]))
    sign = 'positive' if components[dominant] >= 0 else 'negative'
    return dominant, sign

def get_current_active_camera():
    panel = cmds.getPanel(withFocus=True)
    camera = cmds.modelEditor(panel, query=True, camera=True)
    return cmds.listRelatives(camera, shapes=True, fullPath=True)[0]

def are_uvs_horizontal(uvs):
    uv1, uv2 = uvs[0], uvs[1]

    u1, v1 = uv1
    u2, v2 = uv2

    horizontal_distance = abs(u1 - u2)
    vertical_distance = abs(v1 - v2)

    return horizontal_distance < vertical_distance