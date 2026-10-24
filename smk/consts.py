"""Tunable configuration: values meant to be adjusted by hand, in one place.

Only knobs live here. Constants that are facts of an implementation (such
as how ``Mode7Plane`` packs colours) stay next to the code that relies on them.
"""

# --- Display (GDD §12.1) ---------------------------------------------------

INTERNAL_SIZE = (320, 180)
"""The fixed render buffer, in pixels. Never adapts to the window.

384x216 is the fallback if 320x180 proves cramped (GDD §18 #6).
"""

DEFAULT_DESKTOP_FRACTION = 0.75
"""Largest share of the desktop the starting window may take, per side."""

LETTERBOX_COLOUR = (0, 0, 0)
"""RGB of the bars around the integer-scaled buffer."""

VSYNC = True
"""Lock presentation to the display refresh. Off renders uncapped."""

# --- Mode 7 camera (GDD §12.3) ---------------------------------------------

CAMERA_HEIGHT = 48.0
"""Height of the camera above the plane, in texels."""

HORIZON_Y = 70
"""Buffer row of the horizon. The plane is drawn below it, the sky above."""

FOV_DEGREES = 68.0
"""Horizontal field of view. The focal length is derived from it, never the reverse."""

# --- Mode 7 distance filtering (GDD §14.4) ---------------------------------

SHARP_SPAN = 2.0
"""Texels of depth a row can cover before it is filtered.

Higher keeps more of the ground sharp; ``math.inf`` turns filtering off
(SMK-style shimmer).
"""

MAX_DISTANCE_SAMPLES = 4
"""Samples averaged per distant pixel, 1 to 4.

Fewer is sharper but flickers more; above 4 would overflow ``Mode7Plane``'s
10-bit colour packing.
"""
