from maya.api import OpenMaya as om
from maya import cmds
from typing import Optional, Dict, List, Tuple, Union

from jk_topological_mirror.constants import MirrorSpace, MirrorMode, Axis3d, AxisUV, AUTHOR, VERSION
from jk_topological_mirror.utilities import (
    is_edge_selected, get_shared_vertex_center_world, get_edge_vector, get_camera_vectors,
    get_shared_uv_center, get_connect_uvs, get_current_active_camera, get_dominant_axis,
    are_uvs_horizontal, sort_by_world_space, get_intended_mirror_axis, is_uvs_sorted,
    get_active_component
)
from jk_topological_mirror.traversal import traverse, get_component_mapping
from jk_topological_mirror.transform import mirror_uvs, mirror_vertices

class JkTopologicalMirrorCommand(om.MPxCommand):
    kPluginCmdName: str = "jkTopologicalMirror"

    def __init__(self) -> None:
        super().__init__()
        self._mirror_space = MirrorSpace.WORLD
        self._mirror_mode = MirrorMode.MIRROR 
        self._left_to_right: bool = True
        self._top_to_bottom: bool = True
        self._edge_path: Optional[om.MDagPath] = None
        self._mapping: Dict[int, int] = {}
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
        if arg_data.isFlagSet("mirrorMode"):
            mode_str = arg_data.flagArgumentString("mirrorMode", 0).lower()
            
            mode_lookup = {
                "mirror": MirrorMode.MIRROR,
                "flip": MirrorMode.FLIP,
                "average": MirrorMode.AVERAGE
            }

            self._mirror_mode = mode_lookup.get(mode_str, MirrorMode.MIRROR)
        space_str: str = arg_data.flagArgumentString("mirrorSpace", 0).lower()
        if space_str == MirrorSpace.UV.value:
            self._mirror_space = MirrorSpace.UV
        elif space_str == "world":
            self._mirror_space = MirrorSpace.WORLD
        else:
            om.MGlobal.displayError("Unknown mode. Use 'uv' or 'world'.")
            return

        self._flip = arg_data.isFlagSet("flip")
        self._left_to_right = arg_data.isFlagSet("leftToRight")
        self._top_to_bottom = arg_data.isFlagSet("topToBottom")

        if self._mirror_space == MirrorSpace.UV:
            self._prepare_uvs()
        elif self._mirror_space == MirrorSpace.WORLD:
            self._prepare_vertices()

        if not self._edge_path or not self._mapping or self._center is None:
            return

        self.redoIt()

    def redoIt(self) -> None:
        if self._mirror_space == MirrorSpace.UV:
            mirror_uvs(self._edge_path, self._mapping, self._center, self._mirror_mode, self._uv_axis)

        elif self._mirror_space == MirrorSpace.WORLD:
            mirror_vertices(self._edge_path, self._mapping, self._center, self._mirror_mode, self._world_axis)

    def undoIt(self) -> None:
        if not self._edge_path:
            return
            
        mesh_fn: om.MFnMesh = om.MFnMesh(self._edge_path)
        if self._mirror_space == MirrorSpace.UV and self._original_uvs:
            mesh_fn.setUVs(self._original_uvs[0], self._original_uvs[1], mesh_fn.currentUVSetName())
            mesh_fn.updateSurface()
        elif self._mirror_space == MirrorSpace.WORLD and self._original_points:
            mesh_fn.setPoints(self._original_points, om.MSpace.kWorld)
            mesh_fn.updateSurface()

    def isUndoable(self) -> bool:
        return True

    def _prepare_uvs(self) -> None:
        if not is_edge_selected():
            self._edge_path = None
            return

        edge_path, edge_component = get_active_component()
        edge_it = om.MItMeshEdge(edge_path, edge_component)
        edge_index = edge_it.index()
        faces = list(edge_it.getConnectedFaces())

        if len(faces) != 2:
            self._edge_path = None
            return

        mesh_fn = om.MFnMesh(edge_path)
        face_a, face_b = faces
        
        connected_uvs = get_connect_uvs(mesh_fn.object(), face_a, face_b)
        self._uv_axis = AxisUV.V if are_uvs_horizontal(connected_uvs) else AxisUV.U

        if not is_uvs_sorted(mesh_fn, face_a, face_b, self._uv_axis):
            face_a, face_b = face_b, face_a

        should_flip = (not self._left_to_right) if self._uv_axis == AxisUV.U else (not self._top_to_bottom)
        if should_flip:
            face_a, face_b = face_b, face_a

        result = traverse(mesh_fn.object(), face_a, face_b, edge_index, edge_index, True)
        if not result:
            self._edge_path = None
            return

        self._mapping = get_component_mapping(mesh_fn.object(), self._mirror_space, result[0], result[1])
        self._center = get_shared_uv_center(mesh_fn, face_a, face_b)
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

        camera = get_current_active_camera()
        edge_vector: om.MVector = get_edge_vector(edge_path, edge_component)
        cam_right, cam_up, _ = get_camera_vectors(camera)

        self._mirror_direction_is_vertical = get_dominant_axis(edge_vector) == get_dominant_axis(cam_right)
        self._world_axis, is_positive = get_intended_mirror_axis(edge_vector, cam_right = cam_right, cam_up=cam_up)
        
        
        mesh_fn: om.MFnMesh = om.MFnMesh(edge_path)
        face_a, face_b = connected_faces[0], connected_faces[1]


        if sort_by_world_space(mesh_fn, face_a, face_b, self._world_axis, is_positive):
            face_a, face_b = face_b, face_a


        if self._mirror_direction_is_vertical:
            # _top_to_bottom is: Positive -> Negative
            # _left_to_right is: Negative -> Positive
            if not self._top_to_bottom:
                face_a, face_b = face_b, face_a
        else:
            if self._left_to_right:
                face_a, face_b = face_b, face_a

        result = traverse(mesh_fn.object(), face_a, face_b, edge_index, edge_index, False)
        
        if not result:
            cmds.warning("Could not define symmetry.")
            self._edge_path = None
            return

        self._mapping = get_component_mapping(mesh_fn.object(), self._mirror_space, result[0], result[1])
        self._center = get_shared_vertex_center_world(mesh_fn, face_a, face_b)
        self._edge_path = edge_path
        self._original_points = mesh_fn.getPoints(om.MSpace.kWorld)


    @staticmethod
    def createSyntax() -> om.MSyntax:
        syntax: om.MSyntax = om.MSyntax()
        syntax.addFlag("-m", "mirrorMode", om.MSyntax.kString)
        syntax.addFlag("-s", "mirrorSpace", om.MSyntax.kString)
        syntax.addFlag("-f", "flip")
        syntax.addFlag("-ltr", "leftToRight")
        syntax.addFlag("-ttb", "topToBottom")
        return syntax

def maya_useNewAPI() -> bool:
    return True

def initializePlugin(plugin: om.MObject) -> None:
    plugin_fn: om.MFnPlugin = om.MFnPlugin(plugin, AUTHOR, VERSION, "any")
    plugin_fn.registerCommand(
        JkTopologicalMirrorCommand.kPluginCmdName, 
        JkTopologicalMirrorCommand.cmdCreator, 
        JkTopologicalMirrorCommand.createSyntax
    )

def uninitializePlugin(plugin: om.MObject) -> None:
    plugin_fn: om.MFnPlugin = om.MFnPlugin(plugin)
    plugin_fn.deregisterCommand(JkTopologicalMirrorCommand.kPluginCmdName)
