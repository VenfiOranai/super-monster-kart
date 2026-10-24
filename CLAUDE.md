# Super Monster Kart

A SNES-era kart racer in the idiom of *Super Mario Kart* — flat Mode 7 track, behind-the-kart camera, pixel sprites — where racers have **health bars**. Zero HP means elimination.

A racer is a **loadout**: a **monster** (what you drive) plus a **rider** (who's driving it), picked separately. Monsters have multiple built-in attacks; riders add a passive and one activatable ability. Items heal, buff, and amplify what the loadout already does.

## Content is undesigned — do not invent it

This project has a **designed systems layer** and an **unwritten content layer**, and the split is deliberate.

**Designed — build against it:** simulation architecture, the damage pipeline, the targeting-mode vocabulary, stat-to-physics mappings, loadout resolution, netcode model, data formats, art spec.

**Undesigned — the owner's to author:** every monster and rider (their stats, traits, attacks, passives, actives), the item set, track layouts, all naming, and any story or setting. The GDD carries authoring templates with `TBD` in place of values.

`MONSTER_A`, `RIDER_B`, `TRACK_3`, `A1`, `RA1` are slot IDs, not names.

**Rules:**

- **Never invent content.** A `TBD` is a decision waiting for the owner, not a gap to helpfully fill. If code needs a monster before the roster exists, use an obviously-fake fixture (`TEST_MONSTER`, round numbers) and label it as a fixture — never something that could be mistaken for a real design.
- **Never invent names**, in code, comments, tests, or sample data.
- **Keep identifiers mechanical.** Traits, passives, and modifiers are named for their effect (`dot`, `proj_immune`), not their flavour. Fiction goes in `display_name` only — that is what keeps naming the cast a data edit instead of a refactor.
- **Content-shaped work is blocked, not yours to unblock.** If a task needs the roster, say so and stop rather than designing around it.

## Read this first

**`docs/GDD.md` is the authoritative design document.** Before implementing anything, read the relevant section. It contains the mechanics, the numbers, the data formats, the module layout, and the milestone order. If the GDD and this file ever disagree, the GDD wins.

If something you need isn't specified there, it's probably in **§18 Open Questions** — check before inventing an answer, and ask rather than silently deciding.

## Stack

- Python 3.11
- pygame-ce (windowing, input, blitting, audio)
- numpy (Mode 7 transform, per-pixel work)
- pytest

## Non-negotiable architectural rules

These exist because networking and testability depend on them. Breaking them is expensive to undo later.

1. **`smk/sim/` is pure.** No `pygame` import anywhere under it — not for vectors, not for rects, not for anything. No wall-clock reads. No module-level `random`. `tests/test_sim_purity.py` enforces this.
2. **Simulation is deterministic.** All randomness goes through the seeded RNG in sim state. Iterate racers by stable ID, never by dict/set order. Same seed + same inputs must produce an identical state hash (`tests/test_determinism.py`).
3. **Fixed 60 Hz tick, decoupled from render.** The sim never varies with framerate; the renderer interpolates between snapshots.
4. **Dependency direction is one-way:** `render` → `sim`, `ai` → `sim`, `net` → `sim`. Nothing imports `render`. `sim` imports nothing from the rest of the project.
5. **AI uses the same input interface as a human.** AI produces `InputFrame`s. The simulation cannot tell AI from player.
6. **Content is data, not code.** Monsters, riders, attacks, items, and tracks are JSON (`content/monsters.json`, `content/riders.json`, …). Adding a monster or rider must require zero new attack-resolution code — compose from the six targeting modes in GDD §8.1. If a new attack doesn't fit, add a *mode*, not a special case.
7. **Loadout is resolved once, at race start.** `resolve_loadout(monster, rider) -> RacerStats` in `smk/sim/loadout.py` is pure and never runs per tick. Temporary modifiers apply on top of the resolved block; they never re-resolve it.
8. **Monsters and riders never share a stat axis.** Monster = HP, speed, accel, handling, weight. Rider = power, focus, luck, guard, precision. A rider must never affect how a monster drives. `tests/test_loadout.py` enforces this plus the 250-point rider budget — if that test fails, someone made a rider a straight upgrade rather than a sidegrade.
9. **The host is authoritative** for damage, HP, KO, kill credit, item rolls, rider actives, checkpoints, and race start/end. Clients predict their own kart only.

## Workflow: one branch per feature

Every new feature or change follows this flow:

1. The owner requests the work.
2. **Before writing any code, create a new branch off an up-to-date `main`** (e.g. `feature/<short-description>`).
3. Write the code on that branch and leave it **uncommitted**.
4. The owner reviews the uncommitted changes in their IDE.
5. The owner commits and merges into `main` if it looks good.

**Never commit, push, merge, or open PRs** — review happens pre-commit in the IDE, and committing is the owner's call.

## Code style: object-oriented

The owner prefers OOP. Write new code that way:

- **Put behaviour and the state it works on in classes.** For example, `Game` owns the loop and `Screen` owns the window and buffer. Avoid loose module-level functions that pass state around.
- **Use small, focused classes and composition, not deep inheritance.** Use `@dataclass(frozen=True)` for value objects such as stat blocks, snapshots, and `InputFrame`, and ordinary classes for things with behaviour.
- **Put pure calculations in methods on the relevant class** (a `classmethod`/`staticmethod` is fine), so they stay testable without a window (see `Viewport.fit`).
- **OOP never overrides the architectural rules below.** Sim objects stay pure and deterministic, and keep the public names the GDD specifies (`Simulation.step`, `resolve_loadout`, …).

## Visual constraints

**This is a modern game that looks like an old one.** The pixel aesthetic comes from a small render buffer; everything around it is contemporary.

- **320×180 internal buffer** (16:9, square pixels), integer-scaled to the display — 4× to 720p, 6× to 1080p, 12× to 4K. Nearest-neighbour only. Non-integer scaling is never acceptable; letterbox instead.
- The buffer size is **fixed** and never adapts to the window — a wider display must not grant a wider field of view (GDD §12.1).
- **60 Hz simulation, uncapped interpolated rendering.** These are different numbers and must never be conflated: 60 Hz is a fixed design constant, not a framerate target. A 144 Hz display gets 144 frames from 60 ticks (GDD §12.2).
- No true 3D, ever — the track is a Mode 7 plane.

When in doubt about *gameplay or art direction*, do what Super Mario Kart did. When in doubt about *presentation technology* — resolution, framerate, scaling, display support — do what a modern game does. SNES palette and sprite limits are art-direction guidelines, not hardware constraints to honour.

Riders are **composited over monsters at runtime** using per-monster mount points, never pre-combined into per-pair sprites — see GDD §16.2. Pre-combining is a 6× art-budget multiplier and is the wrong answer.

## Current status

Pre-production, **M0 — Mode 7 Spike** (GDD §17) nearly done on `feature/mode7-spike` (not yet merged to `main`). There is no `smk/sim/`, no content, and no fixed-tick loop yet.

**What exists:**

- `smk/app/` — entrypoint (`python -m smk`). `bootstrap.setup()` sets Windows per-monitor DPI awareness and must run before `pygame.init()`; `Game` owns the loop (events + blank frame only).
- `smk/render/screen.py` — `Screen` owns the window and the fixed 320×180 buffer; `Viewport.fit` does integer-scale + letterbox. Scaling happens on the GPU via `pygame._sdl2.video` `Renderer`/`Texture` (nearest-neighbour, vsync on by default) — CPU scaling blew the budget at 1440p+, so don't regress to it.
- `smk/render/mode7/` — pure-numpy Mode 7 (GDD §14.4): `Mode7Camera` (frozen), `Mode7Plane` (square power-of-two RGB texture with a box-filtered mip chain, packed 10 bits per channel in `uint32`), `RowPlan` (per-row samples and mip levels; cached, depends only on camera height/horizon/FOV), `Mode7Renderer` (writes RGB into `surfarray.pixels3d`, indexed `[x, y, channel]`). Distant rows are averaged over up to 4 depth samples so thin lines don't flicker when driving forward — the one exception to nearest-neighbour (GDD §14.4, §16.1). Rows covering ≤ `sharp_span` texels of depth (default 2) stay sharp; `sharp_span = math.inf` turns filtering off. `world_coordinates` is the plain GDD transform kept as the test oracle; `render` uses a faster equivalent.
- `smk/consts.py` — hand-tunable configuration (display, Mode 7 camera, distance filtering), grouped under comment headers. New knobs go here; implementation facts such as `Mode7Plane`'s colour packing stay next to their code. `smk/sim/` must not import it (rule 4), so sim tuning will need its own home.
- `smk/reporting.py` — a global no-op `Reporter` with `measure(name)` / `end_frame()` hooks. Always call through the module (`reporting.reporter.measure(...)`); dev tools install a listening subclass.
- `tools/` — dev-only, not part of the game: `mode7_spike` (interactive free camera; `M` toggles distance filtering, `[` / `]` move where it starts), `mode7_benchmark` (pass/fail against the M0 budget), `calibration` (generated placeholder texture — a fixture, not a track), `performance` (`PerformanceReporter`).

**Commands:** setup `py -3.12 -m venv .venv` then `.venv/Scripts/python -m pip install -e ".[dev]"`; tests `.venv/Scripts/python -m pytest` (CI runs them headless on 3.11); benchmark `python -m tools.mode7_benchmark`; spike `python -m tools.mode7_spike [--vsync]`.

**M0 result:** numpy passes — with distance filtering on, whole frame p99 ≈ 2.3–3.1 ms against a 4.17 ms budget (144 fps, 40% spare) at 720p, 1080p, 1440p, 4K and an awkward 1000×700 window (measured 2026-09-26; ≈ 1 ms before filtering was added). moderngl is not needed yet, but the margin is now modest: Mode 7 is ~1.6–1.7 ms of it, so watch it as sprites and HUD land, and moderngl is the fallback if it gets tight.

**Remaining before M0 exit:** the owner's visual check in the spike — blur / non-integer stretch at 1080p and 4K, and distant flicker when driving forward (compare with `M`) — and recording the numpy decision in GDD §18 (Open Question 3). Then merge and start **M1 — Core Driving**, which begins by creating `smk/sim/` with `tests/test_sim_purity.py`.
