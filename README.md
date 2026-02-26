# JK Topological Mirror

A Maya plugin for establishing symmetry based on mesh topology.

![jk_topological_mirror symmetry example](./docs/simple_symmetry.gif)

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

1. Download and extract the contents of [jk_topological_mirror.zip](https://github.com/JakobJK/jk_topological_mirror/archive/main.zip) to a temporary location.
2. Unzip, and copy the content of the `./src` directory to a Maya Module Folder. If the folder doesn't already exists, create it.
    - **Windows:** `%USERPROFILE%\Documents\maya\modules`
    - **macOS:** `~/Library/Preferences/Autodesk/maya/modules`
    - **Linux:** `~/maya/modules`
    - ![](./docs/module-folder.png)

3. Load the Plug-in. 
    - Open Maya and navigate to **Windows > Settings/Preferences > Plug-in Manager**.
    - Find `jk_topological_mirror.py` and check **Loaded** (and **Auto Load** if desired). 
    - ![Plugin manager](./docs/plugin-manager.png)
4. Load the UI via Python:

```python
from jk_topological_mirror import MirrorTopologyUI

MirrorTopologyUI.show_ui()
```

---

## Usage

Select an edge, and the mirror will happen perpendicular to that edge. Which means, as an example, if you are selecting an edge that is mostly horizontal, you will mirror vertically from the view of the current active camera. 

The selected edge will also act as a reflection point for the mirror.

You can mirror across any topological centerline. Here is an example of many mirrors across many symmetrical axis:
![mirroring across many multiple axes](./docs/simple2_symmetry.gif)

You can mirror both vertices, or UVs. UVs will be based of UV islands connectivity.
![](./docs/simple_uv_symmetry.gif)

### Author

[**Jakob Kousholt**](https://www.linkedin.com/in/jakobjk/)

### License

JK Topological Mirror is licensed under the [MIT](https://rem.mit-license.org/) License.
