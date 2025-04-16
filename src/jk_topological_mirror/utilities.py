from maya import cmds
import maya.api.OpenMaya as om


def get_intended_mirror_axis(edge_vector, camera_forward_vector):
    edge_axis = get_dominant_axis(edge_vector)
    forward_axis = get_dominant_axis(camera_forward_vector)
    return ({'X', 'Y', 'Z'} - {edge_axis, forward_axis}).pop()

def is_uvs_sorted(mesh_fn, left_face_index, right_face_index, axis = 'U'):
    left_center = get_polygon_center_uv(mesh_fn, left_face_index)
    right_center = get_polygon_center_uv(mesh_fn, right_face_index)
    return left_center.x < right_center.x if axis == 'U' else left_center.y > right_center.y

def sort_by_world_space(mesh_fn, face_a, face_b, axis):
    center_a = get_shared_vertex_center_world(mesh_fn, face_a, face_b)
    if center_a is None:
        return False  

    center_b = get_shared_vertex_center_world(mesh_fn, face_b, face_a)
    if center_b is None:
        return False

    axis_index = {'X': 0, 'Y': 1, 'Z': 2}[axis]
    a_val = center_a[axis_index]
    b_val = center_b[axis_index]

    return a_val > b_val  


def get_camera_vector(camera, direction):
    matrix = cmds.getAttr(camera + ".worldMatrix[0]")
    m = om.MMatrix(matrix)

    if direction == "right":
        vec = om.MVector(m[0], m[1], m[2])
    elif direction == "up":
        vec = om.MVector(m[4], m[5], m[6])
    elif direction == "forward":
        vec = om.MVector(m[8], m[9], m[10])
    else:
        raise ValueError(f"Unknown camera vector direction: {direction}")

    vec.normalize()
    return vec

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
        points = mesh_fn.getPoints(om.MSpace.kObject)
        shared_points = [points[v] for v in shared_verts]

        avg_point = om.MPoint()
        for pt in shared_points:
            avg_point += pt
        avg_point /= len(shared_points)

        return (avg_point.x, avg_point.y, avg_point.z)

    return None


def get_selected_edge_vector():
    sel = om.MGlobal.getActiveSelectionList()
    dag_path, component = sel.getComponent(0)
    mesh_fn = om.MFnMesh(dag_path)

    edges = om.MItMeshEdge(dag_path, component)
    edge = next(edges)
    
    v1 = om.MVector(mesh_fn.getPoint(edge.vertexId(0), om.MSpace.kWorld))
    v2 = om.MVector(mesh_fn.getPoint(edge.vertexId(1), om.MSpace.kWorld))
    
    vec = (v2 - v1)
    vec.normalize()
    return vec

def get_shared_uv_center(mesh_fn, face_index1, face_index2):
    uv_set_name = mesh_fn.currentUVSetName()

    face_it1 = om.MItMeshPolygon(mesh_fn.object())
    face_it1.setIndex(face_index1)
    uvs1 = {face_it1.getUVIndex(i, uv_set_name) for i in range(face_it1.polygonVertexCount())}

    face_it2 = om.MItMeshPolygon(mesh_fn.object())
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

    
def get_mirror_direction(camera, edge_vector):
    camera_alignment = get_camera_axis_alignment(camera)
    edge_axis = get_dominant_axis(edge_vector)

    is_vertical = edge_axis == camera_alignment["up"]  # Up vector = horizontal edge → vertical mirror
    is_horizontal = edge_axis == camera_alignment["right"]  # Right vector = vertical edge → horizontal mirror

    mirror_type = "vertical" if is_vertical else "horizontal" if is_horizontal else "ambiguous"

    if mirror_type == "vertical":
        up_vector = get_camera_vector(camera, "up")
        axis = camera_alignment["up"].lower()
        return (getattr(edge_vector, axis) * getattr(up_vector, axis)) >= 0

    if mirror_type == "horizontal":
        right_vector = get_camera_vector(camera, "right")
        axis = camera_alignment["right"].lower()
        return (getattr(edge_vector, axis) * getattr(right_vector, axis)) >= 0

    return True  # fallback


def get_dominant_axis(vector):
    abs_vec = [abs(vector.x), abs(vector.y), abs(vector.z)]
    index = abs_vec.index(max(abs_vec))
    return ['X', 'Y', 'Z'][index]

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

def get_camera_axis_alignment(camera):
    matrix = cmds.getAttr(camera + ".worldMatrix[0]")
    m = om.MMatrix(matrix)

    right = om.MVector(m[0], m[1], m[2])
    up = om.MVector(m[4], m[5], m[6])
    forward = om.MVector(m[8], m[9], m[10])

    def dominant_axis(vec):
        components = {'X': abs(vec.x), 'Y': abs(vec.y), 'Z': abs(vec.z)}
        return max(components, key=components.get)

    return {
        "right": dominant_axis(right),
        "up": dominant_axis(up),
        "forward": dominant_axis(forward)
    }


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
    (u1, v1), (u2, v2) = uvs
    return abs(u1 - u2) > abs(v1 - v2)
