from maya.api import OpenMaya as om
from maya import cmds

from jk_topological_mirror.utilities import (
    edge_selected, get_shared_vertex_center_world, get_selected_edge_vector, get_camera_vector,
    get_shared_uv_center, get_connect_uvs, get_camera_axis_alignment, get_mirror_direction,
    get_dominant_axis_with_sign, get_dominant_axis, get_current_active_camera, are_uvs_horizontal,
    sort_by_world_space, get_intended_mirror_axis, is_uvs_sorted,
    get_active_component
)
from jk_topological_mirror.traversal import traverse, get_component_mapping
from jk_topological_mirror.transform import mirror_uvs, mirror_vertices

class JkTopologicalMirrorCommand(om.MPxCommand):
    kPluginCmdName = "jkTopologicalMirror"

    def __init__(self):
        super().__init__()
        self._mode = None
        self._average = False
        self._left_to_right = True
        self._top_to_bottom = True
        self._edge_path = None
        self._mapping = None
        self._center = None
        self._axis = None
        self._original_points = None
        self._original_uvs = None

    @staticmethod
    def cmdCreator():
        return JkTopologicalMirrorCommand()

    def doIt(self, args):
        arg_data = om.MArgParser(self.syntax(), args)
        self._mode = arg_data.flagArgumentString("mode", 0).lower()
        self._average = arg_data.isFlagSet("average")
        self._left_to_right = not arg_data.isFlagSet("rightToLeft")
        self._top_to_bottom = not arg_data.isFlagSet("bottomToTop")

        if self._mode == "uvs":
            self._prepare_uvs()
        elif self._mode == "vertices":
            self._prepare_vertices()
        else:
            om.MGlobal.displayError("Unknown mode. Use 'uvs' or 'vertices'.")
            return

        if not self._edge_path or not self._mapping or not self._center:
            return

        self.redoIt()

    def redoIt(self):
        if self._mode == "uvs":
            mirror_uvs(self._edge_path, self._mapping, self._center, self._average, self._axis)
        elif self._mode == "vertices":
            mirror_vertices(self._edge_path, self._mapping, self._center, self._average, axis=self._axis)

    def undoIt(self):
        if self._mode == "uvs" and self._original_uvs:
            mesh_fn = om.MFnMesh(self._edge_path)
            mesh_fn.setUVs(self._original_uvs[0], self._original_uvs[1], mesh_fn.currentUVSetName())
            mesh_fn.updateSurface()
        elif self._mode == "vertices" and self._original_points:
            mesh_fn = om.MFnMesh(self._edge_path)
            mesh_fn.setPoints(self._original_points, om.MSpace.kWorld)
            mesh_fn.updateSurface()

    def isUndoable(self):
        return True

    def _prepare_uvs(self):
        if not edge_selected():
            self._edge_path = None
            return

        edge_path, edge_component = get_active_component()
        edge_it = om.MItMeshEdge(edge_path, edge_component)
        edge_index = edge_it.index()
        connected_faces = edge_it.getConnectedFaces()
        if len(connected_faces) != 2:
            cmds.warning("Selected edge is not connected to exactly two faces.")
            self._edge_path = None
            return

        mesh_fn = om.MFnMesh(edge_path)
        left_face_index, right_face_index = connected_faces

        connected_uvs = get_connect_uvs(mesh_fn.object(), left_face_index, right_face_index)
        if len(connected_uvs) != 2:
            cmds.warning("The two connected faces must share two UVs!")
            self._edge_path = None
            return

        axis = 'V' if are_uvs_horizontal(connected_uvs) else 'U'
        is_sorted = is_uvs_sorted(mesh_fn, left_face_index, right_face_index, axis)

        if axis == 'U' and (not is_sorted and self._left_to_right):
            left_face_index, right_face_index = right_face_index, left_face_index
        if axis == 'V' and (not is_sorted and self._top_to_bottom):
            left_face_index, right_face_index = right_face_index, left_face_index

        result = traverse(mesh_fn.object(), left_face_index, right_face_index, edge_index, edge_index, True)
        if not result:
            cmds.warning("Could not define symmetry.")
            self._edge_path = None
            return

        visited_left, visited_right = result
        self._mapping = get_component_mapping(mesh_fn.object(), 'uvs', visited_left, visited_right)
        self._center = get_shared_uv_center(mesh_fn, left_face_index, right_face_index)
        self._edge_path = edge_path
        self._original_uvs = mesh_fn.getUVs(mesh_fn.currentUVSetName())
        self._axis = axis

    def _prepare_vertices(self):
        if not edge_selected():
            self._edge_path = None
            return

        edge_path, edge_component = get_active_component()
        edge_it = om.MItMeshEdge(edge_path, edge_component)
        edge_index = edge_it.index()
        connected_faces = edge_it.getConnectedFaces()
        if len(connected_faces) != 2:
            cmds.warning("Selected edge is not connected to exactly two faces.")
            self._edge_path = None
            return

        camera = get_current_active_camera()
        edge_vector = get_selected_edge_vector()
        forward_vector = get_camera_vector(camera, "forward")
        self._axis = get_intended_mirror_axis(edge_vector, forward_vector)

        sign = get_mirror_direction(camera, edge_vector)

        mesh_fn = om.MFnMesh(edge_path)
        face_a, face_b = connected_faces

        if sort_by_world_space(mesh_fn, face_a, face_b, self._axis):
            face_a, face_b = face_b, face_a

        if not sign:
            face_a, face_b = face_b, face_a

        result = traverse(mesh_fn.object(), face_a, face_b, edge_index, edge_index, False)
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
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addFlag("-m", "mode", om.MSyntax.kString)
        syntax.addFlag("-a", "average")
        syntax.addFlag("-rtl", "rightToLeft")
        syntax.addFlag("-ttb", "topToBottom")
        return syntax

def maya_useNewAPI():
    return True

def initializePlugin(plugin):
    plugin_fn = om.MFnPlugin(plugin)
    plugin_fn.registerCommand(JkTopologicalMirrorCommand.kPluginCmdName, JkTopologicalMirrorCommand.cmdCreator, JkTopologicalMirrorCommand.createSyntax)

def uninitializePlugin(plugin):
    plugin_fn = om.MFnPlugin(plugin)
    plugin_fn.deregisterCommand(JkTopologicalMirrorCommand.kPluginCmdName)
