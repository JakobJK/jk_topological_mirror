from maya.api import OpenMaya as om
from maya import cmds
from typing import Optional, Dict, List, Tuple, Union

# Import constants
from jk_topological_mirror.constants import CameraDirection, MirrorSpace, Axis3d, AxisUV
from jk_topological_mirror.utilities import (
    is_edge_selected, get_shared_vertex_center_world, get_selected_edge_vector, get_camera_vector,
    get_shared_uv_center, get_connect_uvs, is_edge_aligned_with_camera, get_current_active_camera, 
    are_uvs_horizontal, sort_by_world_space, get_intended_mirror_axis, is_uvs_sorted,
    get_active_component
)
from jk_topological_mirror.traversal import traverse, get_component_mapping
from jk_topological_mirror.transform import mirror_uvs, mirror_vertices

class JkTopologicalMirrorCommand(om.MPxCommand):
    kPluginCmdName: str = "jkTopologicalMirror"

    def __init__(self) -> None:
        super().__init__()
        self._mode: Optional[MirrorSpace] = None
        self._average: bool = False
        self._left_to_right: bool = True
        self._top_to_bottom: bool = True
        self._edge_path: Optional[om.MDagPath] = None
        self._mapping: Optional[Dict[int, int]] = None
        self._center: Optional[Union[om.MPoint, om.MFloatPoint]] = None
        self._uv_axis: AxisUV = AxisUV.U
        self._world_axis: Axis3d = Axis3d.X
        self._original_points: Optional[om.MPointArray] = None
        self._original_uvs: Optional[Tuple[List[float], List[float]]] = None

    @staticmethod
    def cmdCreator() -> 'JkTopologicalMirrorCommand':
        return JkTopologicalMirrorCommand()

    def doIt(self, args: om.MArgList) -> None:
        arg_data: om.MArgParser = om.MArgParser(self.syntax(), args)
        
        mode_str: str = arg_data.flagArgumentString("mirrorSpace", 0).lower()
        if mode_str == MirrorSpace.UV.value:
            self._mode = MirrorSpace.UV
        elif mode_str == "world":
            self._mode = MirrorSpace.WORLD
        else:
            om.MGlobal.displayError("Unknown mode. Use 'uv' or 'world'.")
            return

        self._average = arg_data.isFlagSet("average")
        self._left_to_right = not arg_data.isFlagSet("rightToLeft")
        self._top_to_bottom = not arg_data.isFlagSet("bottomToTop")

        if self._mode == MirrorSpace.UV:
            self._prepare_uvs()
        elif self._mode == MirrorSpace.WORLD:
            self._prepare_vertices()

        if not self._edge_path or not self._mapping or self._center is None:
            return

        self.redoIt()

    def redoIt(self) -> None:
        if self._mode == MirrorSpace.UV:
            mirror_uvs(self._edge_path, self._mapping, self._center, self._average, self._uv_axis)
        elif self._mode == MirrorSpace.WORLD:
            mirror_vertices(self._edge_path, self._mapping, self._center, self._average, axis=self._world_axis)

    def undoIt(self) -> None:
        if not self._edge_path:
            return
            
        mesh_fn: om.MFnMesh = om.MFnMesh(self._edge_path)
        if self._mode == MirrorSpace.UV and self._original_uvs:
            mesh_fn.setUVs(self._original_uvs[0], self._original_uvs[1], mesh_fn.currentUVSetName())
            mesh_fn.updateSurface()
        elif self._mode == MirrorSpace.WORLD and self._original_points:
            mesh_fn.setPoints(self._original_points, om.MSpace.kWorld)
            mesh_fn.updateSurface()

    def isUndoable(self) -> bool:
        return True

    def _prepare_uvs(self) -> None:
        if not is_edge_selected():
            self._edge_path = None
            return

        edge_path, edge_component = get_active_component()
        edge_it: om.MItMeshEdge = om.MItMeshEdge(edge_path, edge_component)
        edge_index: int = edge_it.index()
        connected_faces: List[int] = list(edge_it.getConnectedFaces())

        if len(connected_faces) != 2:
            cmds.warning("Selected edge is not connected to exactly two faces.")
            self._edge_path = None
            return

        mesh_fn: om.MFnMesh = om.MFnMesh(edge_path)
        left_face_index: int = connected_faces[0]
        right_face_index: int = connected_faces[1]

        connected_uvs: List[int] = get_connect_uvs(mesh_fn.object(), left_face_index, right_face_index)
        if len(connected_uvs) != 2:
            cmds.warning("The two connected faces must share two UVs!")
            self._edge_path = None
            return

        # Map logic to AxisUV enum
        self._uv_axis = AxisUV.V if are_uvs_horizontal(connected_uvs) else AxisUV.U
        is_sorted: bool = is_uvs_sorted(mesh_fn, left_face_index, right_face_index, self._uv_axis.value)

        if self._uv_axis == AxisUV.U and (not is_sorted and self._left_to_right):
            left_face_index, right_face_index = right_face_index, left_face_index
        if self._uv_axis == AxisUV.V and (not is_sorted and self._top_to_bottom):
            left_face_index, right_face_index = right_face_index, left_face_index

        result: Optional[Tuple[Dict[int, int], Dict[int, int]]] = traverse(
            mesh_fn.object(), left_face_index, right_face_index, edge_index, edge_index, True
        )
        
        if not result:
            cmds.warning("Could not define symmetry.")
            self._edge_path = None
            return

        visited_left, visited_right = result
        self._mapping = get_component_mapping(mesh_fn.object(), 'uvs', visited_left, visited_right)
        self._center = get_shared_uv_center(mesh_fn, left_face_index, right_face_index)
        self._edge_path = edge_path
        self._original_uvs = mesh_fn.getUVs(mesh_fn.currentUVSetName())


    def _prepare_vertices(self) -> None:
        if not is_edge_selected():
            self._edge_path = None
            return

        edge_path, edge_component = get_active_component()
        edge_it: om.MItMeshEdge = om.MItMeshEdge(edge_path, edge_component)
        edge_index: int = edge_it.index()
        connected_faces: List[int] = list(edge_it.getConnectedFaces())
        
        if len(connected_faces) != 2:
            cmds.warning("Selected edge is not connected to exactly two faces.")
            self._edge_path = None
            return

        camera: om.MDagPath = get_current_active_camera()
        edge_vector: om.MVector = get_selected_edge_vector()
        forward_vector: om.MVector = get_camera_vector(camera, CameraDirection.FORWARD)
        
        # Get intended axis and map to Axis3d enum
        self._world_axis = get_intended_mirror_axis(edge_vector, forward_vector)

        aligned: bool = is_edge_aligned_with_camera(camera, edge_vector)

        mesh_fn: om.MFnMesh = om.MFnMesh(edge_path)
        face_a: int = connected_faces[0]
        face_b: int = connected_faces[1]

        if sort_by_world_space(mesh_fn, face_a, face_b, self._world_axis):
            face_a, face_b = face_b, face_a

        if not aligned:
            face_a, face_b = face_b, face_a

        result: Optional[Tuple[Dict[int, int], Dict[int, int]]] = traverse(
            mesh_fn.object(), face_a, face_b, edge_index, edge_index, False
        )
        
        if not result:
            cmds.warning("Could not define symmetry.")
            self._edge_path = None
            return

        visited_left, visited_right = result
        self._mapping = get_component_mapping(mesh_fn.object(), 'verts', visited_left, visited_right)
        self._center = get_shared_vertex_center_world(mesh_fn, face_a, face_b)
        self._edge_path = edge_path
        self._original_points = mesh_fn.getPoints(om.MSpace.kWorld)

    @staticmethod
    def createSyntax() -> om.MSyntax:
        syntax: om.MSyntax = om.MSyntax()
        syntax.addFlag("-m", "mirrorSpace", om.MSyntax.kString)
        syntax.addFlag("-a", "average")
        syntax.addFlag("-rtl", "rightToLeft")
        syntax.addFlag("-ttb", "topToBottom")
        return syntax

def maya_useNewAPI() -> bool:
    return True

def initializePlugin(plugin: om.MObject) -> None:
    plugin_fn: om.MFnPlugin = om.MFnPlugin(plugin)
    plugin_fn.registerCommand(
        JkTopologicalMirrorCommand.kPluginCmdName, 
        JkTopologicalMirrorCommand.cmdCreator, 
        JkTopologicalMirrorCommand.createSyntax
    )

def uninitializePlugin(plugin: om.MObject) -> None:
    plugin_fn: om.MFnPlugin = om.MFnPlugin(plugin)
    plugin_fn.deregisterCommand(JkTopologicalMirrorCommand.kPluginCmdName)
