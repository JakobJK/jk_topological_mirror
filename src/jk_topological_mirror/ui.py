from PySide6 import QtWidgets
from shiboken6 import wrapInstance

import maya.OpenMayaUI as omui
from maya import cmds


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
        super().__init__(parent)

        self.build_ui()

    @property
    def settings(self):
        flip = self.flip_checkbox.isChecked()
        left_to_right = self.left_to_right_checkbox.isChecked()
        top_to_bottom = self.top_to_bottom_checkbox.isChecked()

        return {
            "flip": flip,
            "leftToRight": left_to_right,
            "topToBottom": top_to_bottom,
        }

    def build_ui(self):
        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(main_widget)

        settings_widget = QtWidgets.QGroupBox("Mirror Settings")
        settings_layout = QtWidgets.QVBoxLayout(settings_widget)

        self.flip_checkbox = QtWidgets.QCheckBox("Flip")
        self.left_to_right_checkbox = QtWidgets.QCheckBox("Left to Right")
        self.top_to_bottom_checkbox = QtWidgets.QCheckBox("Top to Bottom")

        settings_layout.addWidget(self.flip_checkbox)
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

        layout.addWidget(settings_widget)
        layout.addWidget(buttons_widget)

        self.setCentralWidget(main_widget)

    def run_command(self, mirror_space):

        import traceback
        try:
            cmds.jkTopologicalMirror(mirrorSpace=mirror_space, **self.settings)
        except Exception as e:
            tb = traceback.format_exc()
            cmds.warning(f"Mirror failed: {e}\n{tb}")
