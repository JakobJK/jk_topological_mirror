from enum import Enum

class MirrorSpace(Enum):
    WORLD = "world" 
    UV = "uv"

class CameraDirection(Enum):
    FORWARD = "forward"
    UP = "up"
    RIGHT = "right"

class Axis3d(Enum):
    X = "X"
    Y = "Y"
    Z = "Z"

class AxisUV(Enum):
    U = "U"
    V = "V"
