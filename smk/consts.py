"""Tunable configuration: values meant to be adjusted by hand, in one place.

Only knobs live here. Constants that are facts of an implementation (such
as how ``Mode7Plane`` packs colours) stay next to the code that relies on them.

This is the one project module ``smk.sim`` may import, so it must stay pure
itself: no imports at all (``tests/test_sim_purity.py``). It mixes game rules
that every peer must share with per-player preferences; splitting the two is
GDD §18 #19.
"""

# --- Simulation timing (GDD §4.2, §14.3) -----------------------------------

TICK_RATE = 60
"""Simulation steps per second. A fixed design constant, not a framerate."""

TICK_DURATION = 1 / TICK_RATE
"""Seconds of game time one ``Simulation.step`` advances."""

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

# --- Main loop (GDD §14.3) -------------------------------------------------

MAX_FRAME_TICKS = 5
"""Most ticks' worth of time one frame may bank.

A longer hitch drops game time instead of queueing a backlog.
"""

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
