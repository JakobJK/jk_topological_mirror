import maya.api.OpenMaya as om
from collections import deque

from jk_topological_mirror.constants import MirrorSpace
from typing import List, Dict, Tuple, Optional

def _get_face_edges_ordered(
    poly_iterator: om.MItMeshPolygon, 
    face_index: int, 
    start_edge_index: int, 
    reverse: bool = False
    ) -> List[int]:
    """Retrieves an ordered list of edge IDs for a face starting from a specific edge.

    Args:
        poly_iterator (om.MItMeshPolygon): Pre-instantiated polygon iterator used to query mesh data.
        face_index (int): The index of the polygon face to query.
        start_edge_index (int): The edge ID to be used as the first element in the ordered list.
        reverse (bool): If True, reverses the topological winding order of the returned edges.

    Returns:
        List[int]: A list of edge IDs ordered according to the face winding.
    """
    poly_iterator.setIndex(face_index)
    edges: List[int] = list(poly_iterator.getEdges())
    
    try:
        index: int = edges.index(start_edge_index)
    except ValueError:
        return []
        
    ordered_edges: List[int] = edges[index:] + edges[:index]
    
    if reverse:
        ordered_edges = ordered_edges[:1] + ordered_edges[1:][::-1]
        
    return ordered_edges

def _faces_connected_in_uv(
    poly_iterator: om.MItMeshPolygon, 
    edge_iterator: om.MItMeshEdge, 
    face_index_1: int, 
    face_index_2: int, 
    edge_index: int, 
    uv_set_name: str
    ) -> bool:
    """Determines if two faces share a continuous (seam-less) connection in UV space.

    Args:
        poly_iterator (om.MItMeshPolygon): Pre-instantiated polygon iterator for querying UV indices.
        edge_iterator (om.MItMeshEdge): Pre-instantiated edge iterator for querying vertex IDs.
        face_index_1 (int): The index of the first polygon face.
        face_index_2 (int): The index of the second polygon face.
        edge_index (int): The index of the shared edge between the two faces.
        uv_set_name (str): The name of the UV set to evaluate.

    Returns:
        bool: True if the UV indices for both vertices of the shared edge match across both faces.
    """
    edge_iterator.setIndex(edge_index)
    vertex_0: int = edge_iterator.vertexId(0)
    vertex_1: int = edge_iterator.vertexId(1)

    def get_uv_id(target_face_index: int, target_vertex_index: int) -> int:
        poly_iterator.setIndex(target_face_index)
        for i in range(poly_iterator.polygonVertexCount()):
            if poly_iterator.vertexIndex(i) == target_vertex_index:
                return poly_iterator.getUVIndex(i, uv_set_name)
        return -1

    uv_id_face_1_v0: int = get_uv_id(face_index_1, vertex_0)
    uv_id_face_1_v1: int = get_uv_id(face_index_1, vertex_1)
    uv_id_face_2_v0: int = get_uv_id(face_index_2, vertex_0)
    uv_id_face_2_v1: int = get_uv_id(face_index_2, vertex_1)

    return (uv_id_face_1_v0 == uv_id_face_2_v0 and uv_id_face_1_v1 == uv_id_face_2_v1)

def _get_adjacent_faces_with_edges(
    poly_iterator: om.MItMeshPolygon, 
    edge_iterator: om.MItMeshEdge, 
    face_index: int, 
    start_edge_index: int, 
    uv_set_name: str, 
    reverse: bool = False, 
    uv_connectivity: bool = False
) -> List[Tuple[int, int]]:
    """Retrieves adjacent faces and their connecting edges in topological order.

    Args:
        poly_iterator (om.MItMeshPolygon): Pre-instantiated polygon iterator for querying face data.
        edge_iterator (om.MItMeshEdge): Pre-instantiated edge iterator for querying connected faces.
        face_index (int): The index of the current face being evaluated.
        start_edge_index (int): The edge ID used as the starting reference for ordering.
        uv_set_name (str): The name of the active UV set for connectivity checks.
        reverse (bool): If True, processes the edges in reverse topological winding order.
        uv_connectivity (bool): If True, skips adjacent faces that are separated by a UV seam.

    Returns:
        List[Tuple[int, int]]: A list of tuples containing (adjacent_face_index, connecting_edge_index).
    """
    connected_faces_with_edges: List[Tuple[int, int]] = []
    ordered_edges: List[int] = _get_face_edges_ordered(poly_iterator, face_index, start_edge_index, reverse)
    
    for edge_index in ordered_edges:
        edge_iterator.setIndex(edge_index)
        for adjacent_face_index in edge_iterator.getConnectedFaces():
            if adjacent_face_index != face_index:
                if uv_connectivity:
                    if not _faces_connected_in_uv(poly_iterator, edge_iterator, face_index, adjacent_face_index, edge_index, uv_set_name):
                        continue
                connected_faces_with_edges.append((adjacent_face_index, edge_index))
    return connected_faces_with_edges

def traverse(
    mesh_dag: om.MDagPath, 
    start_left_face: int, 
    start_right_face: int, 
    start_left_edge: int, 
    start_right_edge: int, 
    uv_connectivity: bool
    ) -> Optional[Tuple[Dict[int, int], Dict[int, int]]]:
    """Performs a dual Breadth-First Search (BFS) to map topological symmetry between two mesh sides.

    Args:
        mesh_dag (om.MDagPath): The DAG path of the mesh to be traversed.
        start_left_face (int): The starting face index for the left-side traversal.
        start_right_face (int): The starting face index for the right-side traversal.
        start_left_edge (int): The initial reference edge index on the left face to define winding.
        start_right_edge (int): The initial reference edge index on the right face to define winding.
        uv_connectivity (bool): If True, the traversal is restricted to connected UV shells.

    Returns:
        Optional[Tuple[Dict[int, int], Dict[int, int]]]: A tuple containing two dictionaries 
            mapping visited face indices to their entry edge indices for the left and right sides, 
            or None if a topological asymmetry is detected.
    """ 
    left_queue: deque = deque([(start_left_face, start_left_edge)])
    right_queue: deque = deque([(start_right_face, start_right_edge)])
    
    visited_left: Dict[int, int] = {start_left_face: start_left_edge}
    visited_right: Dict[int, int] = {start_right_face: start_right_edge}
    
    poly_iterator: om.MItMeshPolygon = om.MItMeshPolygon(mesh_dag)
    edge_iterator: om.MItMeshEdge = om.MItMeshEdge(mesh_dag)
    mesh_function: om.MFnMesh = om.MFnMesh(mesh_dag)
    uv_set_name: str = mesh_function.currentUVSetName()
    
    while left_queue and right_queue:
        current_face_left, current_edge_left = left_queue.popleft()
        left_adjacents: List[Tuple[int, int]] = _get_adjacent_faces_with_edges(
            poly_iterator, edge_iterator, current_face_left, current_edge_left, 
            uv_set_name, False, uv_connectivity
        )
        
        current_face_right, current_edge_right = right_queue.popleft()
        right_adjacents: List[Tuple[int, int]] = _get_adjacent_faces_with_edges(
            poly_iterator, edge_iterator, current_face_right, current_edge_right, 
            uv_set_name, True, uv_connectivity
        )
        
        if len(left_adjacents) != len(right_adjacents):
            return None

        for (left_adj_face, left_adj_edge), (right_adj_face, right_adj_edge) in zip(left_adjacents, right_adjacents):
            if left_adj_face not in visited_left and left_adj_face not in visited_right:
                visited_left[left_adj_face] = left_adj_edge
                visited_right[right_adj_face] = right_adj_edge
                left_queue.append((left_adj_face, left_adj_edge))
                right_queue.append((right_adj_face, right_adj_edge))

        if len(left_queue) != len(right_queue):
            return None
                
    return visited_left, visited_right

def _get_ordered_verts(edge_iterator: om.MItMeshEdge, ordered_edges: List[int]) -> List[int]:
    """Extracts vertex IDs in winding order by comparing consecutive edges in a sequence.

    Args:
        edge_iterator (om.MItMeshEdge): Pre-instantiated edge iterator used to query vertex IDs.
        ordered_edges (List[int]): A list of edge IDs arranged in topological winding order.

    Returns:
        List[int]: A list of vertex IDs ordered to match the topological winding of the edges.
    """
    vertices: List[int] = []
    num_edges: int = len(ordered_edges)
    for i in range(num_edges):
        edge_iterator.setIndex(ordered_edges[i])
        edge_1_verts: set = {edge_iterator.vertexId(0), edge_iterator.vertexId(1)}
        
        edge_iterator.setIndex(ordered_edges[(i + 1) % num_edges])
        edge_2_verts: set = {edge_iterator.vertexId(0), edge_iterator.vertexId(1)}
        
        start_vert: List[int] = list(edge_1_verts.difference(edge_2_verts))
        if start_vert:
            vertices.append(start_vert[0])
        else:
            vertices.append(list(edge_1_verts)[0])
    return vertices

def get_component_mapping(
    mesh_dag: om.MDagPath, 
    mirror_space: MirrorSpace, 
    visited_left: Dict[int, int], 
    visited_right: Dict[int, int]
    ) -> Dict[int, int]:
    """Generates a mapping of component IDs between two sides based on traversal results.

    Args:
        mesh_dag (om.MDagPath): The DAG path of the mesh being processed.
        mirror_space (MirrorSpace): The coordinate space (WORLD for vertices, UV for UV indices).
        visited_left (Dict[int, int]): Mapping of face indices to entry edge indices for the left side.
        visited_right (Dict[int, int]): Mapping of face indices to entry edge indices for the right side.

    Returns:
        Dict[int, int]: A dictionary where keys are source component IDs (left) and values are target component IDs (right).
    """
    mapping: Dict[int, int] = {}
    poly_iterator: om.MItMeshPolygon = om.MItMeshPolygon(mesh_dag)
    edge_iterator: om.MItMeshEdge = om.MItMeshEdge(mesh_dag)
    mesh_function: om.MFnMesh = om.MFnMesh(mesh_dag)
    uv_set_name: str = mesh_function.currentUVSetName()
    
    for (left_face, left_edge), (right_face, right_edge) in zip(visited_left.items(), visited_right.items()):
        left_ordered_edges: List[int] = _get_face_edges_ordered(poly_iterator, left_face, left_edge, False)
        right_ordered_edges: List[int] = _get_face_edges_ordered(poly_iterator, right_face, right_edge, True)
        
        left_v_ordered: List[int] = _get_ordered_verts(edge_iterator, left_ordered_edges)
        right_v_ordered: List[int] = _get_ordered_verts(edge_iterator, right_ordered_edges)

        left_components: List[int]
        right_components: List[int]

        if mirror_space == MirrorSpace.WORLD:
            left_components = left_v_ordered
            right_components = right_v_ordered
        
        elif mirror_space == MirrorSpace.UV:
            poly_iterator.setIndex(left_face)
            left_uv_lookup: Dict[int, int] = {
                poly_iterator.vertexIndex(i): poly_iterator.getUVIndex(i, uv_set_name) 
                for i in range(poly_iterator.polygonVertexCount())
            }
            
            poly_iterator.setIndex(right_face)
            right_uv_lookup: Dict[int, int] = {
                poly_iterator.vertexIndex(i): poly_iterator.getUVIndex(i, uv_set_name) 
                for i in range(poly_iterator.polygonVertexCount())
            }
            
            left_components = [left_uv_lookup[v] for v in left_v_ordered]
            right_components = [right_uv_lookup[v] for v in right_v_ordered]
            
        mapping.update(zip(left_components, right_components))
        
    return mapping
