# JK Topological Mirror

A Maya plugin for establishing symmetry based on mesh topology.

![jk_topological_mirror symmetry example](./simple_symmetry.gif)

---

## Features

* Three Mirror Modes:
    * Mirror: Mirrors one side to the other.
    * Flip: Swaps sides.
    * Average: Balances both sides using the average of their coordinates.
* Camera-Aware: Mirror based on viewport orientation.
* Vertex & UV Support: Mirror geometry or texture coordinates.
---

## Installation

1. Copy ./src/jk_topological_mirror folder to Maya scripts path.
2. Copy ./src/jk_topological_mirror_cmd.py to Maya plug-in path.
3. Load via Python:

```python
from jk_topological_mirror import MirrorTopologyUI

MirrorTopologyUI.show_ui()
```


---

## Usage

Select an edge, and the mirror will happen perpendicular to that edge. Which means, as an example, if you are selecting an edge that is mostly horizontal, you will mirror vertically from the view of the current active camera. 

The selected edge will also act as a reflection point for the mirror.

You can mirror across any topological centerline. Here is an example of many mirrors across many symmetrical axis:
![mirroring across many multiple axes](./simple2_symmetry.gif)

You can mirror both vertices, or UVs. UVs will be based of UV islands connectivity.
![](./simple_uv_symmetry.gif)

### Author

[**Jakob Kousholt**](https://www.linkedin.com/in/jakobjk/)

### License

JK Topological Mirror is licensed under the [MIT](https://rem.mit-license.org/) License.
