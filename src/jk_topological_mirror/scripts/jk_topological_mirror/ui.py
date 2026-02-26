import traceback

from PySide6 import QtWidgets
from shiboken6 import wrapInstance

import maya.OpenMayaUI as omui
from maya import cmds

from jk_topological_mirror.constants import TITLE, VERSION

def get_main_maya_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    return main_window

class MirrorTopologyUI(QtWidgets.QMainWindow):
    _instance = None

    @classmethod
    def show_ui(cls):
        if not cls._instance:
            cls._instance = MirrorTopologyUI()

        if cls._instance.isHidden():
            cls._instance.show()
        else:
            cls._instance.raise_()
        cls._instance.activateWindow()

        return cls._instance

    def __init__(self, parent=get_main_maya_window()):
        super().__init__()
        self.setWindowTitle(f"{TITLE} [{VERSION}]")
        self.build_ui()

    @property
    def settings(self):
        mode_id = self.mirror_mode_group.checkedId()
        mode_map = {0: "mirror", 1: "flip", 2: "average"}

        left_to_right = self.left_to_right_checkbox.isChecked()
        top_to_bottom = self.top_to_bottom_checkbox.isChecked()

        return {
            "mirrorMode": mode_map[mode_id],
            "leftToRight": left_to_right,
            "topToBottom": top_to_bottom,
        }

    def build_ui(self):
        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(main_widget)

        settings_widget = QtWidgets.QGroupBox("Mirror Settings")
        settings_layout = QtWidgets.QVBoxLayout(settings_widget)
        
        mirror_mode_groupbox = QtWidgets.QGroupBox("Mirror Mode")
        self.mirror_mode_group = QtWidgets.QButtonGroup(mirror_mode_groupbox)
        mirror_mode_layout = QtWidgets.QVBoxLayout(mirror_mode_groupbox)

        mirror_radio = QtWidgets.QRadioButton("Mirror")
        flip_radio   = QtWidgets.QRadioButton("Flip")
        average_radio= QtWidgets.QRadioButton("Average")

        mirror_radio.setChecked(True)

        mirror_mode_layout.addWidget(mirror_radio)
        mirror_mode_layout.addWidget(flip_radio)
        mirror_mode_layout.addWidget(average_radio)

        self.mirror_mode_group.addButton(mirror_radio, 0)
        self.mirror_mode_group.addButton(flip_radio, 1)
        self.mirror_mode_group.addButton(average_radio, 2)

        self.left_to_right_checkbox = QtWidgets.QCheckBox("Left to Right")
        self.left_to_right_checkbox.setChecked(True)

        self.top_to_bottom_checkbox = QtWidgets.QCheckBox("Top to Bottom")
        self.top_to_bottom_checkbox.setChecked(True)

        
        settings_layout.addWidget(self.left_to_right_checkbox)
        settings_layout.addWidget(self.top_to_bottom_checkbox)

        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)

        mirror_world_button = QtWidgets.QPushButton("World")
        mirror_uv_button = QtWidgets.QPushButton("UV")

        mirror_world_button.clicked.connect(lambda: self.run_command(mirror_space="world"))
        mirror_uv_button.clicked.connect(lambda: self.run_command(mirror_space="uv"))

        buttons_layout.addWidget(mirror_world_button)
        buttons_layout.addWidget(mirror_uv_button)
        
        layout.addWidget(mirror_mode_groupbox)
        layout.addWidget(settings_widget)
        layout.addWidget(buttons_widget)

        self.setCentralWidget(main_widget)

        self.mirror_mode_group.buttonClicked.connect(self.on_mirror_mode_changed)

    def on_mirror_mode_changed(self, _):
        """
        Handles when the mirror mode changes. The mirror settings are irrelevant for the mirror modes: Flip, and Average.
        """
        mode_id = self.mirror_mode_group.checkedId()
        enabled = mode_id == 0
        self.left_to_right_checkbox.setEnabled(enabled)
        self.top_to_bottom_checkbox.setEnabled(enabled)

    def run_command(self, mirror_space):
        try:
            cmds.jkTopologicalMirror(mirrorSpace=mirror_space, **self.settings)
        except Exception as e:
            tb = traceback.format_exc()
            cmds.warning(f"Mirror failed: {e}\n{tb}")


