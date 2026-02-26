from enum import Enum

TITLE = "jkTopologicalMirror"
VERSION = "1.0.0"

class MirrorSpace(Enum):
    """Defines the coordinate space in which the mirror operation is performed."""
    WORLD = "world"  
    UV = "uv"

class MirrorMode(Enum):
    """Defines how positions are handled between mirrored components."""
    MIRROR = "mirror"   # Source position is copied to the target across the axis.
    FLIP = "flip"       # Source and target positions are swapped across the axis.
    AVERAGE = "average" # Moves both components to be symmetrical relative to each other.

class Axis3d(Enum):
    """3D Cartesian axes for world-space mirroring."""
    X = "X"
    Y = "Y"
    Z = "Z"

class AxisUV(Enum):
    """2D texture axes for UV-space mirroring."""
    U = "U"
    V = "V"
