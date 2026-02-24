from enum import Enum

class MirrorSpace(Enum):
    WORLD = "world" 
    UV = "uv"

class MirrorMode(Enum):
    MIRROR = "mirror"
    FLIP = "flip"
    AVERAGE = "average"

class Axis3d(Enum):
    X = "X"
    Y = "Y"
    Z = "Z"

class AxisUV(Enum):
    U = "U"
    V = "V"
