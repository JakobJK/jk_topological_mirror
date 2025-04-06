import maya.api.OpenMaya as om

from collections import OrderedDict, deque



def _get_uv_ids_from_ordered_edges(mesh, edges, face_idx):
    """ Given a list of edges, return a list of UV IDs in the correct order. """
    uv_set_name = om.MFnMesh(mesh).currentUVSetName()
    face_it = om.MItMeshPolygon(mesh)
    face_it.setIndex(face_idx)
    ordered_uv_ids = OrderedDict()

    edge_it = om.MItMeshEdge(mesh)

    edge_it.setIndex(edges[0])
    first_edge_vertices = [edge_it.vertexId(0), edge_it.vertexId(1)]

    edge_it.setIndex(edges[1])
    second_edge_vertices = [edge_it.vertexId(0), edge_it.vertexId(1)]

    uv_ids = {}
    for i in range(face_it.polygonVertexCount()):
        uv_id = face_it.getUVIndex(i, uv_set_name)
        vertex_id = face_it.vertexIndex(i)
        uv_ids[vertex_id] = uv_id

    if first_edge_vertices[0] not in second_edge_vertices:
        ordered_uv_ids[first_edge_vertices[0]] = uv_ids[first_edge_vertices[0]]
    else:
        ordered_uv_ids[first_edge_vertices[1]] = uv_ids[first_edge_vertices[1]]

    ordered_uv_ids[first_edge_vertices[0]] = uv_ids[first_edge_vertices[0]]
    ordered_uv_ids[first_edge_vertices[1]] = uv_ids[first_edge_vertices[1]]

    for edge_index in edges[1:]:
        edge_it.setIndex(edge_index)
        edge_vertices = [edge_it.vertexId(0), edge_it.vertexId(1)]
        for vertex in edge_vertices:
            if vertex not in ordered_uv_ids:
                ordered_uv_ids[vertex] = uv_ids[vertex]

    return list(ordered_uv_ids.values())

    
def _get_verts_from_ordered_edges(mesh, edges, face_idx):
    """ Given a list of edges, return a list of vertices in the correct order. """
    face_it = om.MItMeshPolygon(mesh)
    face_it.setIndex(face_idx)
    ordered_vertices = OrderedDict()  

    edge_it = om.MItMeshEdge(mesh)

    edge_it.setIndex(edges[0])
    first_edge_vertices = [edge_it.vertexId(0), edge_it.vertexId(1)  ]
    
    edge_it.setIndex(edges[1])
    second_edge_vertices = [edge_it.vertexId(0), edge_it.vertexId(1)  ]

    if first_edge_vertices[0] not in second_edge_vertices:
        ordered_vertices[first_edge_vertices[0]] = None
    else:
        ordered_vertices[first_edge_vertices[1]] = None

    ordered_vertices[first_edge_vertices[0]] = None
    ordered_vertices[first_edge_vertices[1]] = None

    for edge_index in edges[1:]:
        edge_it.setIndex(edge_index)
        edge_vertices = [edge_it.vertexId(0), edge_it.vertexId(1)]
        for vertex in edge_vertices:
            if vertex not in ordered_vertices:
                ordered_vertices[vertex] = None

    return list(ordered_vertices.keys())

def _get_face_edges_from_start_edge(mesh, face_index, start_edge_index, reverse=False):
    """
    Get the edges of a face in proper order.
    """
    face_it = om.MItMeshPolygon(mesh)
    face_it.setIndex(face_index)
    
    edges = list(face_it.getEdges())
    
    if start_edge_index not in edges:
        return []
    edge_idx = edges.index(start_edge_index)
    edges = edges[edge_idx:] + edges[:edge_idx]
    
    if reverse:
        edges = edges[:1] + edges[1:][::-1]
        
    return edges

def _get_face_uvs(mesh, face_index):
    uv_set_name = om.MFnMesh(mesh).currentUVSetName()
    face_it = om.MItMeshPolygon(mesh)
    face_it.setIndex(face_index)
    return {tuple(face_it.getUV(i, uv_set_name)) for i in range(face_it.polygonVertexCount())}

def _faces_connected_in_uv(mesh, face_index1, face_index2):
    uvs1 = _get_face_uvs(mesh, face_index1)
    uvs2 = _get_face_uvs(mesh, face_index2)
    return len(uvs1 & uvs2) >= 2

def _get_adjacent_faces_with_edges(mesh, face_index, start_edge_index, reverse=False, uv_connectivity = False):
    """ Get adjacent faces and their connecting edges of a given face index in a mesh starting from a specified edge index. """
    connected_faces_with_edges = []
    edges = _get_face_edges_from_start_edge(mesh, face_index, start_edge_index, reverse)
    
    for edge_index in edges:
        edge_it = om.MItMeshEdge(mesh)
        edge_it.setIndex(edge_index)
        for adjacent_face_index in edge_it.getConnectedFaces():
            if adjacent_face_index != face_index:
                if uv_connectivity and not _faces_connected_in_uv(mesh, adjacent_face_index, face_index):
                    continue
                connected_faces_with_edges.append((adjacent_face_index, edge_index))
    
    return connected_faces_with_edges


def traverse(mesh, start_left_face, start_right_face, start_left_edge, start_right_edge, uv_connectivity):
    """ Perform a bfs traversal from both left and right starting faces. """
    left_queue = deque([(start_left_face, start_left_edge)])
    right_queue = deque([(start_right_face, start_right_edge)])
    
    visited_left = OrderedDict()
    visited_right = OrderedDict()
    
    visited_left[start_left_face] = start_left_edge
    visited_right[start_right_face] = start_right_edge
    
    while left_queue and right_queue:
        if left_queue:
            current_face_left, current_edge_left = left_queue.popleft()
            left_adjacents = _get_adjacent_faces_with_edges(mesh, current_face_left, current_edge_left, False, uv_connectivity)
            for left_adj_face, left_adj_edge in left_adjacents:
                if left_adj_face not in visited_left and left_adj_face not in visited_right:
                    visited_left[left_adj_face] = left_adj_edge
                    left_queue.append((left_adj_face, left_adj_edge))
        
        if right_queue:
            current_face_right, current_edge_right = right_queue.popleft()
            right_adjacents = _get_adjacent_faces_with_edges(mesh, current_face_right, current_edge_right, True, uv_connectivity)
            for right_adj_face, right_adj_edge in right_adjacents:
                if right_adj_face not in visited_right and right_adj_face not in visited_left:
                    visited_right[right_adj_face] = right_adj_edge
                    right_queue.append((right_adj_face, right_adj_edge))

        if len(left_queue) != len(right_queue):
            return None
    
    return visited_left, visited_right

def get_polygon_center_uv(mesh_fn, face_index):
    uv_set_name = mesh_fn.currentUVSetName()
    face_it = om.MItMeshPolygon(mesh_fn.dagPath())
    face_it.setIndex(face_index)
    
    uvs = []
    for i in range(face_it.polygonVertexCount()):
        uv = face_it.getUV(i, uv_set_name)
        uvs.append(om.MFloatPoint(uv[0], uv[1], 0.0))  
    
    center = om.MFloatPoint()
    for uv in uvs:
        center += uv
    
    center /= len(uvs)
    return center

def not_sorted_left_and_right(mesh_fn, left_face_index, right_face_index, axis = 'U'):
    left_center = get_polygon_center_uv(mesh_fn, left_face_index)
    right_center = get_polygon_center_uv(mesh_fn, right_face_index)
    return left_center.x < right_center.x if axis == 'U' else left_center.y > right_center.y


def get_component_mapping(mesh, component_type, visited_left, visited_right):
    """. Maps the left side to the right side of components. """
    left_to_right = {}
    for left_face, right_face in zip(visited_left, visited_right):
        left_edge = visited_left[left_face]
        left_components = _get_face_edges_from_start_edge(mesh, left_face, left_edge, False)
        
        right_edge = visited_right[right_face]        
        right_components = _get_face_edges_from_start_edge(mesh, right_face, right_edge, True)
        
        if component_type == "verts":
            left_components = _get_verts_from_ordered_edges(mesh, left_components, left_face)
            right_components = _get_verts_from_ordered_edges(mesh, right_components, right_face)
        
        if component_type == 'uvs':            
            left_components = _get_uv_ids_from_ordered_edges(mesh, left_components, left_face)
            right_components = _get_uv_ids_from_ordered_edges(mesh, right_components, right_face)

        for i in range(len(left_components)):
            left_to_right[left_components[i]] = right_components[i]
    return left_to_right

