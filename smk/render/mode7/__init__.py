"""The Mode 7 ground plane: a per-row affine texture lookup (GDD §14.4).

Pure numpy. Pixels are packed 32-bit values in the target surface's format,
indexed ``[x, y]`` like ``pygame.surfarray`` so the result can be written
straight into ``pixels2d`` with no transpose.

Coordinates are texture space: x right, y down, in texels. ``angle`` 0 faces
+x; positive angles turn clockwise on screen (towards +y).
"""

from smk.render.mode7.camera import Mode7Camera
from smk.render.mode7.plane import Mode7Plane
from smk.render.mode7.renderer import Mode7Renderer

__all__ = ["Mode7Camera", "Mode7Plane", "Mode7Renderer"]
