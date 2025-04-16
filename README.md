# jkTopologicalMirror – Maya Plugin Command

`jkTopologicalMirror` is a custom Maya command that mirrors components (UVs or vertices) across a centerline defined by a selected edge. It supports both UV and vertex space mirroring, and undo support.

## Installation

1. Copy `/src/jk_topological_mirror/` into Maya's **scripts** folder:

   - **Windows**: `C:/Users/<username>/Documents/maya/<version>/scripts/`
   - **macOS**: `/Users/<username>/Library/Preferences/Autodesk/maya/<version>/scripts/`
   - **Linux**: `/home/<username>/maya/<version>/scripts/`

2. Copy `/src/jk_topological_mirror_cmd.py` into Maya's **plug-ins** folder:

   - **Windows**: `C:/Users/<username>/Documents/maya/<version>/plug-ins/`
   - **macOS**: `/Users/<username>/Library/Preferences/Autodesk/maya/<version>/plug-ins/`
   - **Linux**: `/home/<username>/maya/<version>/plug-ins/`

3. Load the plugin via Maya Plugin Manager or use:
   ```python
   cmds.loadPlugin("jk_topological_mirror_cmd.py")
   ```

## Usage

- Create a Maya Shelf Button that runs either a MEL or Python command.
- Select a single edge that defines a symmetrical axis.
- Press your shelf button.


```mel
// MEL Script
// Mirror UVs
jkTopologicalMirror -m "uvs";

// Mirror vertices
jkTopologicalMirror -m "vertices";
```

```python
# Python
# Mirror UVs
cmds.jkTopologicalMirror(mode="uvs")

# Mirror vertices
cmds.jkTopologicalMirror(mode="vertices")
```

### Flags

- `-m` / `--mode` `<string>`: `"uvs"` or `"vertices"` (required)
- `-a` / `--average`: Average positions across the center
- `-rtl` / `--rightToLeft`: Mirror from right to left (default is left to right)
- `-ttb` / `--topToBottom`: Mirror from top to bottom (default is bottom to top)