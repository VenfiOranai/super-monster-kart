# Super Monster Kart — Game Design Document

**Version:** 0.2 (pre-production)
**Status:** Living document. Sections marked *TUNING* hold provisional numbers meant to be changed once the game is playable.
**Audience:** The designer/owner, and coding agents implementing from this document.

**Changes in 0.2:** Riders added as a first-class system (§7). A racer is now a **monster + rider** loadout. Sections 7–18 renumbered to 8–19.
**Changes in 0.3:** Presentation moved to 320×180 / 16:9 / modern framerates (§12). All monster, rider, track, item, and attack **names are now placeholders** — see immediately below.

---

## What is designed, and what isn't

This document deliberately stops short of the game's **content**. Two layers, and the line between them is the most important thing to understand before working from this doc:

| Layer | Status |
|---|---|
| **Systems, architecture, data formats, constraints** | Designed. Specified in detail. Build against it. |
| **The cast and its abilities** — monsters, riders, their stats, traits, attacks, passives, actives; the item set; track layouts; all naming; any story or setting | **Undesigned. The owner's to author.** |

Wherever content belongs, this document carries an **authoring template** — the fields, the constraints, and a design checklist — with `TBD` in place of values (§6.2, §6.3, §7.5, §9.2, §10.5).

`MONSTER_A`, `RIDER_B`, `TRACK_3`, `A1`, `RA1` are slot IDs, not names. There is currently no story, setting, or premise, and that is intentional (§18 #7).

**Two rules for anyone — human or agent — working from this:**

1. **Do not invent content to fill the gaps.** A `TBD` is a decision waiting for the owner, not an oversight to be helpfully patched. If code needs a monster to exist before the roster does, use an obviously-fake fixture and label it as one.
2. **Keep identifiers mechanical.** Traits, passives, and modifiers are named for their effect (`dot`, `proj_immune`), never their fiction. Fiction lives in `display_name` only — which is what keeps naming the cast a data edit rather than a refactor (§14.7).

Some scaffolding sits on the boundary and is **offered, not imposed** — keep or discard it as the content design demands: the six targeting modes (§8.1), the status-modifier vocabulary (§8.4), and the 250-point rider budget (§7.1). Each is flagged where it appears.

---

## 1. Vision & Pillars

### Pitch

**Super Monster Kart** is a SNES-era kart racer in the exact visual and mechanical idiom of *Super Mario Kart* (SMK) — flat Mode 7 track, behind-the-kart camera, chunky pixel sprites — with one fundamental change: **racers have health bars, and a depleted health bar means you're out of the race.** You don't drive a plumber; you ride a monster, and monsters come with their own attacks. Items don't just inconvenience your rivals, they help you kill them.

You pick two things: a **monster**, which is what you drive, and a **rider**, which is who's driving it. The monster decides how you move; the rider decides how you fight.

The result is a racer where the leader isn't safe, the pack isn't harmless, and finishing first is only one of two ways to win — the other is being the only one left.

### Pillars

1. **SMK's feel is sacred.** The camera, the flat track, the 8×8 tile world, the sprite scaling, the hop-and-drift, the horizon band — all of it stays. If a design choice would make this look or feel like a modern kart racer, it is the wrong choice.
2. **Every monster fights differently — and every rider changes how.** A monster is not a stat block with a hat. Each has multiple built-in attacks with distinct targeting behaviour. Riders sit on a completely separate stat axis, so a loadout is a genuine build, not a sum.
3. **Elimination makes every hit matter.** Health is a persistent resource across a whole race, not a per-incident stun. Damage you take on lap 1 is still gone on lap 3. This is the tension the whole design hangs on.
4. **Readable chaos at 320×180.** Eight racers, projectiles, and health states must be legible in a buffer that small — however large the display scaling it up. If a mechanic can't be read at a glance in that space, it doesn't ship.

### Non-goals

- **No true 3D.** No polygonal track, no free camera, no verticality beyond visual flourish. Mode 7 plane only.
- **No open world / hub.** Menus lead to races. That's it.
- **No live service.** No seasons, no battle pass, no server-side accounts. The game is a binary you run.
- **No physics simulation beyond what SMK needed.** Arcade handling, not vehicle dynamics.
- **No dedicated servers.** Multiplayer is peer-to-peer by design (see §15).
- **No hardware-fidelity retro affectations.** This is a modern game with a pixel-art presentation, not an emulation. It is 16:9, it runs at whatever framerate the display allows, and it scales to 4K. Sprite counts, palette limits, and scanline timing are art-direction guidelines (§16.1), not hardware constraints to honour — if a limit costs clarity, break the limit.

---

## 2. Reference & Deltas from SMK

This table exists so implementers don't accidentally import conventions from *Mario Kart 8* or *Crash Team Racing*. When in doubt, do what SMK did.

| System | SMK (1992) | Super Monster Kart | Delta |
|---|---|---|---|
| Track rendering | Mode 7 affine plane, 128×128 tilemap of 8×8 tiles | **Same** | — |
| Camera | Fixed-height chase cam behind kart, looking at horizon | **Same** | — |
| Resolution | 256×224, 8:7 buffer shown at 4:3 | **320×180 internal (16:9, square pixels), integer-scaled to modern displays** | **Changed** |
| Framerate | 60 Hz fixed, tied to the simulation | 60 Hz fixed **simulation**, render uncapped and interpolated (120/144/240 Hz) | **Changed** |
| Field of view | Narrow — 256 px wide | Wider: 320 px at the same sprite scale means you see rivals alongside you sooner | **Changed** |
| Sprites | Pre-rendered rotation frames, scaled by distance | **Same**, plus a layered rider (§16.2) | Extended |
| Character choice | One driver, fixed stats | **Monster + rider, picked separately** | **Core change** |
| Racers | 8 | 8 standard / 4–6 arena, lobby-configurable | Mode-dependent |
| Failure state | Spin-out, squash, temporary slowdown | **Health bar; 0 HP = eliminated** | **Core change** |
| Attacks | Items only | **Monster built-in attacks (multiple each) + a rider active + items** | **Core change** |
| Item effect | Hinder rivals | Damage, heal, buff, and *modify your built-in attacks* | **Core change** |
| Item targeting | Forward/back throw | **Per-attack targeting** (cone, drop, lock-on, aura, arc) | **Core change** |
| Win condition | First across finish after N laps | First across finish **OR** last one standing | **Core change** |
| Track topology | Closed circuits only | Closed circuits **and** point-to-point A→B | **New** |
| Modes | GP, Time Trial, VS, Battle | Single Race → Cups; Battle: Last Standing; Battle: Deathmatch | Restructured |
| Coins | Speed-scaling coin pickups | **Cut.** Health replaces the resource role coins played | Removed |
| Multiplayer | Local split-screen | **LAN, then online P2P.** No split-screen. | Changed |

**Note on split-screen:** SMK's iconic two-view layout is *not* being reproduced. Multiplayer is networked. The single-player screen layout therefore has more vertical room than SMK's top half — see §12.

---

## 3. Core Loop & Modes

### Moment-to-moment loop

Drive → read the pack → pick a target or a threat → spend an attack (limited by cooldown) or an item → take/avoid damage → adjust between "race for the line" and "survive the pack" → repeat.

The central tension: **pushing for position exposes you.** Being in front means eating everything the field can throw forward. Being in back means low threat but a losing position. The design should keep both from being dominant.

### 3.1 Standard Race (MVP mode)

The primary mode. Runs on a **circuit** (looping, N laps) or a **point-to-point** track (single run, start → finish).

**Win conditions — whichever happens first:**
- A racer crosses the finish line having completed the required distance, **or**
- Only one racer remains alive.

**Rules:**
- KO is permanent for the race. No respawn.
- Final standings: survivors ranked by race progress (lap + checkpoint + distance-to-next-checkpoint) at the moment the race ends. KO'd racers rank below all survivors, ordered by **reverse KO order** — the last to die places highest among the dead.
- A human player who is KO'd enters **spectator mode** (§5.6) and can leave to the results screen at any time.

**Edge cases (implementers: handle these explicitly):**
- **Everybody dies.** If the final two racers KO on the same tick, or the last survivor drives into a pit, the race ends immediately and standings are pure reverse-KO order. First place goes to the last racer alive.
- **Point-to-point has no laps.** Lap counters are hidden; the HUD shows progress-to-finish as a percentage bar instead. Total race distance replaces "laps × circuit length" for all progress math.
- **Point-to-point + last-standing.** Fully valid: if everyone else dies before the finish, the survivor wins on the spot without driving the rest of the course.
- **Lone survivor still drives.** If a survivor wins by elimination, play a short victory beat, then cut to results. Don't force them to complete the course.

*TUNING:* Default laps = 4 for circuits (SMK used 5; our races run longer because combat slows the pace — start at 4 and measure). Target race length: **2:30–4:00**.

### 3.2 Battle: Last Standing (post-MVP, M7)

Arena map, no finish line, no laps. 4–6 racers. Elimination is permanent. Last alive wins.

- Arenas are small, enclosed Mode 7 planes with dense item boxes and hazards.
- **Shrinking pressure:** to prevent stalemates, after a time threshold apply escalating pressure. *Default proposal:* item boxes stop respawning and all racers take small periodic damage from a closing hazard ring. *TUNING* — the exact pressure mechanic is an open question (§18).

### 3.3 Battle: Deathmatch (post-MVP, M7)

Arena map, fixed time limit, **respawn on death**. Score-based rather than survival-based.

**Scoring (starting formula, *TUNING*):**

```
score = (kills * 100) + (assists * 40) + (damage_dealt / 10) - (deaths * 50)
```

- **Kill:** landed the killing blow.
- **Assist:** dealt damage to the victim within the last 5 seconds before their death, and wasn't the killer.
- **Damage dealt:** raw HP removed from rivals. Overkill does not count.
- **Death:** any HP-zero event, including environmental (drove into a pit, killed by a hazard). Self-inflicted deaths still cost 50.
- Respawn delay: 3 s, at the spawn point furthest from the nearest live enemy, with 2 s of spawn invulnerability that breaks on your first attack.

Highest score at time limit wins. Ties broken by fewest deaths, then by damage dealt.

### 3.4 Time Trial (post-MVP)

No combat, no rivals, no items. Single loadout, single track, best lap and best total time recorded. Ghost replay of your best run. Exists to make the driving model provable in isolation. Because riders don't affect driving (§7.1), Time Trial records are per-**monster**, not per-loadout.

### 3.5 Mode / racer count matrix

| Mode | Default racers | Range | Track type |
|---|---|---|---|
| Standard Race | 8 | 2–8 | Circuit or point-to-point |
| Battle: Last Standing | 6 | 2–6 | Arena |
| Battle: Deathmatch | 6 | 2–6 | Arena |
| Time Trial | 1 | 1 | Circuit or point-to-point |

Lobby exposes racer count and the AI/human split. Empty human slots fill with AI.

---

## 4. Driving Model

Arcade handling in the SMK idiom. The kart is a point with a facing angle and a velocity, resolved on a 2D plane. No suspension, no weight transfer, no tyre model.

**Riders do not appear in this section at all.** Driving is entirely a function of the monster (§7.1 explains why).

### 4.1 State

Each racer's driving state:

| Field | Type | Notes |
|---|---|---|
| `pos` | vec2 (world units) | World is 1024×1024 units = the track texture, 1 unit = 1 texel |
| `angle` | radians | Facing. Sprite rotation frame derives from this minus camera angle |
| `speed` | scalar | Along facing. Can go negative (reverse) |
| `lateral_slip` | scalar | Sideways drift velocity, decays toward 0 |
| `hop_t` | scalar | Hop timer; >0 means airborne, immune to surface effects |
| `drift_dir` | -1 / 0 / +1 | Active drift direction, set on hop+turn |
| `surface` | enum | Sampled from the tile under `pos` each tick |

### 4.2 Base constants (*TUNING* — starting values)

Units: world-units per tick at 60 Hz unless noted.

| Constant | Value | Meaning |
|---|---|---|
| `TICK_RATE` | 60 Hz | Fixed simulation step |
| `BASE_TOP_SPEED` | 5.0 | Reference top speed (a 50-rated monster) |
| `BASE_ACCEL` | 0.06 | Speed gained per tick at full throttle |
| `BRAKE_DECEL` | 0.15 | Speed lost per tick braking |
| `COAST_DECEL` | 0.02 | Speed lost per tick with no input |
| `BASE_TURN_RATE` | 0.045 rad | Max yaw per tick at speed |
| `TURN_SPEED_FALLOFF` | 0.5 | Turn rate multiplier at top speed vs. at rest |
| `DRIFT_SLIP_GAIN` | 0.08 | Lateral velocity gained per tick while drifting |
| `SLIP_DECAY` | 0.85 | Per-tick lateral velocity retention |
| `HOP_DURATION` | 18 ticks | 0.3 s |
| `REVERSE_TOP_SPEED` | 1.5 | |

### 4.3 Monster stat mapping

Monsters are authored with 0–100 ratings, mapped to physical constants so designers tune readable numbers, not floats:

```
top_speed   = BASE_TOP_SPEED  * (0.75 + 0.005 * speed_rating)      # 50 -> 1.0x
accel       = BASE_ACCEL      * (0.60 + 0.008 * accel_rating)      # 50 -> 1.0x
turn_rate   = BASE_TURN_RATE  * (0.70 + 0.006 * handling_rating)   # 50 -> 1.0x
```

**Weight** (0–100) does not affect speed. It governs collision resolution only (§4.6) and ram damage (§5.2).

### 4.4 Surfaces

Surface type is a property of the tile, read from the tile palette (§10.2). While `hop_t > 0` the racer is airborne and the surface has no effect.

| Surface | Effect |
|---|---|
| `ROAD` | Baseline. No modifier. |
| `DIRT` | Top speed ×0.75, plus small random steering jitter. |
| `GRASS` | Top speed ×0.55, heavy deceleration until at that cap. |
| `ICE` | Normal speed, but `SLIP_DECAY` → 0.97 and turn authority ×0.5. |
| `BOOST` | Sets speed to `top_speed * 1.4` for 30 ticks, decaying back. Does not stack with itself. |
| `WALL` | Impassable. Collision response: speed ×0.35, reflect heading off the wall normal, apply `WALL_DAMAGE`. |
| `PIT` | Fall-out. Racer is recovered to the last checkpoint after 90 ticks, taking `PIT_DAMAGE`. In Deathmatch, counts as a death. |
| `WATER` | Same as `PIT` with a different animation. Optional per-track. |

Wall normals are derived from the tile-edge the racer crossed, not from geometry — SMK-simple. Corner cases resolve to the axis of greater penetration.

### 4.5 Hop & drift

Reproduce SMK's feel: **hop** button makes the kart hop; hopping while turning initiates a drift that builds `lateral_slip` in the turn direction. Drift gives a tighter effective radius at the cost of lateral scrub. There is **no mini-turbo charge** (that's a Mario Kart 64+ invention) — drifting is for cornering line, not for boost. Hop is also the i-frame-free dodge tool: airborne racers pass over ground-level traps (§9) but are still hit by projectiles.

### 4.6 Collisions & shunts

Racer-vs-racer contact resolves as an impulse exchange weighted by `weight`:

```
mass_ratio  = other.weight / (self.weight + other.weight)
self.pos   += separation_normal * -overlap * (1 - mass_ratio)
other.pos  += separation_normal *  overlap * mass_ratio
# both bleed speed proportional to the head-on component of the impact
```

Heavier monsters push lighter ones around; identical weights split the shunt evenly. A shunt into a `WALL` or `PIT` is a legitimate and intended kill vector — the tile damage is credited to the racer who caused the shunt if the shunt happened within the last 60 ticks (this matters for kill attribution in §3.3).

---

## 5. Health & Damage

This is the system that makes the game not-SMK. It deserves the most tuning attention.

### 5.1 The health bar

- Base health scale: **100 HP** for a 50-rated monster. Monster `health_rating` maps: `max_hp = 40 + 1.2 * health_rating` (so 0→40, 50→100, 100→160).
- **Max HP comes from the monster alone.** Riders never modify it — they reduce damage taken instead (§7.1).
- HP does not regenerate passively. The **only** ways to heal are healing items (§9), monster abilities, and rider passives.
- HP persists across the whole race. There is no per-lap reset.

**Time-to-kill target:** a racer under sustained, competent focus from one rival should die in roughly **one lap** (~40–60 s at MVP track lengths). This is the single most important tuning target in the document. Too fast and races end in the first 20 seconds; too slow and health stops mattering and the game degenerates into SMK-without-items.

### 5.2 Damage sources

| Source | Base damage (*TUNING*) | Notes |
|---|---|---|
| Monster attack | TBD | Per-attack (§6.3). Sized against the §5.1 TTK target. |
| Rider active | TBD | Per-rider (§7.5). |
| Item attack | TBD | One-shot; conventionally higher than a built-in (§9.2). |
| Contact / ram | `8 * (self.weight / 50) * impact_speed_factor` | Only monsters whose trait grants contact damage (§6.1). Formula is scaffolding; tune with the roster. |
| `WALL` impact | 3 | Scales with impact speed; capped |
| `PIT` / `WATER` | 12 | Plus the recovery time cost |
| Hazard (track object) | 10–20 | Per-hazard |
| Arena pressure ring | 2 per second | Battle: Last Standing only |

### 5.3 The damage pipeline

Every damage event resolves through this exact ordered pipeline. Implement it once, in one function, and route everything through it.

```
1. damage = attack.base_damage
2. damage *= attacker.rider.power_mult          # §7.1
3. damage *= attacker active `amp` modifiers    # attack-modifier items, rider actives
4. damage *= attacker passive multipliers       # monster traits, rider passives
5. damage *= target.rider.guard_mult            # §7.1 — reduction
6. damage -= target `shield` absorption         # remainder carries to HP
7. target.hp -= damage
```

**Order matters and is not arbitrary:** attacker-side multipliers all resolve before defender-side ones, and `shield` is last so it always absorbs the *final* number the target would have taken. Environmental damage (wall, pit, hazard, pressure ring) enters at step 5 — it is not amplified by the attacker's stats, because there isn't one, but it *is* reduced by guard and absorbed by shields.

### 5.4 Invulnerability frames

After taking damage from an **attack, rider active, or item** source, a racer gets **20 ticks (0.33 s)** of i-frames against further damage from those sources. Environmental damage (wall, pit, hazard) **ignores and does not grant** i-frames — otherwise scraping a wall would make you immune to weapons.

This exists to stop a single multi-hit attack or a chain of simultaneous projectiles from instantly deleting someone.

### 5.5 KO sequence

When HP reaches 0:

1. Racer is flagged `KO` on the authoritative sim (see §15 — the host always decides this).
2. Kill credit assigned: the racer whose damage brought HP to 0, or the shunt-credited racer for environmental deaths (§4.6). Environmental deaths with no credit are unattributed.
3. Monster plays a destruction animation over ~45 ticks while the rider plays a separate tumble (§16.2); during it, the racer is non-colliding and non-targetable.
4. Racer is removed from the track. Its minimap dot is removed.
5. Standings recompute. If one racer remains, the race ends.

In **Deathmatch**, step 4 becomes a respawn timer instead.

### 5.6 Eliminated players

A KO'd human is not kicked to a menu. They enter **spectator mode**:

- Free camera cycling between surviving racers (left/right to switch).
- Full HUD of the spectated racer.
- A prominent "Leave to results" prompt.

They stay in the P2P session and their client keeps receiving state, so the results screen is synchronised.

*Design note:* early elimination is the biggest boredom risk in the whole game. The mitigations are: short races (2:30–4:00), fast rematch flow, and — if playtesting shows it's still a problem — the ghost-harassment mechanic listed in §18.

### 5.7 Low-health handicap (*TUNING lever, default OFF*)

Optional rule: below 25% HP, a kart smokes visibly and loses 10% top speed. Makes finishing kills easier and reads clearly at a glance.

**Default off for MVP** — it's a death spiral amplifier and elimination is already punishing. Implement it behind a flag so it can be tested, not shipped blind.

---

## 6. Monsters

**The monster roster is undesigned.** This section defines the *shape* of a monster, the constraints any design has to satisfy, and the slots to fill. The creatures, their stats, their attacks, and their traits are the owner's to author.

### 6.1 What a monster is

Every monster provides exactly three things:

| Part | Detail |
|---|---|
| **Chassis stats** | Five 0–100 ratings: HP, top speed, acceleration, handling, weight. Mapped to physics constants by §4.3. |
| **Built-in attacks** | Two or three, each an attack record (§8.2) composed from the targeting vocabulary (§8.1). |
| **Passive trait** | One always-on effect. Named for what it does, not for its fiction (§"Naming placeholders"). |

**Locked constraints** — these come from decisions already made and are not open:

- Monsters own the **chassis axes only**. A monster never carries a crew stat (power, focus, luck, guard, precision); those belong exclusively to riders. This separation is load-bearing — see §7.1.
- `max_hp = 40 + 1.2 * health_rating`, so a 0–100 rating spans 40–160 HP (§5.1).
- Every monster's attacks must be expressible in the §8.1 targeting modes. If a design needs something that isn't there, **add a mode to §8.1** — never a special case in monster code (§14.7).
- At least one monster should carry a **contact-damage trait** (bumping deals damage). The engine supports it — §4.6 shunts and the ram row in §5.2 exist for it — and it was an explicit requirement.

### 6.2 Roster slots (to author)

Six monsters at MVP (§17, M4). Slot IDs are placeholders.

| Monster | Role | HP | Speed | Accel | Handling | Weight | Trait |
|---|---|---|---|---|---|---|---|
| `MONSTER_A` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `MONSTER_B` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `MONSTER_C` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `MONSTER_D` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `MONSTER_E` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `MONSTER_F` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

### 6.3 Attack slots (to author)

Two or three per monster, 14–18 total. Each row is one attack record (§8.2).

| Monster | ID | Function | TGT (§8.1) | Dmg | CD | Notes |
|---|---|---|---|---|---|---|
| `MONSTER_A` | `A1` | TBD | TBD | TBD | TBD | TBD |
| | `A2` | TBD | TBD | TBD | TBD | TBD |
| `MONSTER_B` | `B1` | TBD | TBD | TBD | TBD | TBD |
| | `B2` | TBD | TBD | TBD | TBD | TBD |
| … | | | | | | |

### 6.4 Design checklist

Questions the finished roster should be able to answer. These are prompts, not prescriptions — the answers are yours.

1. **Does each monster deal damage in a distinct way?** If two monsters both mainly fire a homing projectile, one of them is redundant regardless of stat differences.
2. **Does the roster cover a spread of chassis extremes?** A field where every monster is 45–55 across the board makes the monster pick cosmetic. HP and weight in particular are the axes that most change how a race feels.
3. **Are there deliberate counter-relationships?** Whether that's a triangle, a web, or something looser is a design call — but *some* structure means picking a monster is a read on the field rather than a preference. Decide this on purpose; it will not emerge on its own.
4. **Is there a forgiving entry-point monster?** Something with no sharp edges, for a first race.
5. **Does at least one monster use the contact-damage trait?** Required (§6.1).
6. **Does every attack pass the readability test?** At 320×180 with eight racers on screen, can a player tell what just hit them (§1, pillar 4)?
7. **Does the kit hold up under the damage pipeline?** Check each attack against §5.3 — particularly how it interacts with i-frames (§5.4), since multi-hit and damage-over-time effects behave very differently there.

**Balance target to design against:** the TTK goal in §5.1 — sustained competent focus from one rival should kill in roughly one lap. That number constrains attack damage and cooldowns more than anything else in this document.

---

## 7. Riders

A racer is a **loadout**: one monster and one rider, picked separately. All monster+rider combinations are legal — there are no class restrictions to learn or enforce.

### 7.1 The separation rule

**Monsters own the chassis axes. Riders own the crew axes. They never overlap.**

| | Axes |
|---|---|
| **Monster (chassis)** | HP · top speed · acceleration · handling · weight |
| **Rider (crew)** | power · focus · luck · guard · precision |

This is the most important rule in the section, and it is what makes the second pick worth making. Because no rider can improve how a monster *drives*, picking a rider is never the question "which rider is best?" — it is always "how do I want to fight?" A rider that made you faster would collapse into a strict-upgrade problem within a week of tuning.

**Sidegrade budget:** every rider's five crew axes sum to exactly **250** (out of a possible 500), so riders are sidegrades by arithmetic rather than by balance luck. Any new rider respects the budget.

*This one is scaffolding, not doctrine.* It guarantees equal **totals**, not equal **value** — if guard turns out to be worth twice what luck is, the budget won't save you (§18 #5). Keep it as a first-pass guardrail; replace it with weighted axis costs if tuning shows it isn't doing its job.

### 7.2 The crew axes

| Axis | Governs | Mapping (50 → 1.0×) |
|---|---|---|
| **power** | Outgoing damage from all sources you control | `damage_mult = 0.70 + 0.006 * power` |
| **focus** | How fast your monster's attack cooldowns tick | `cooldown_rate = 0.75 + 0.005 * focus` |
| **guard** | Incoming damage reduction | `damage_taken_mult = 1.30 - 0.006 * guard` |
| **precision** | Targeting generosity — cone half-angle, lock-on range and acquire angle, `aimed_arc` blast radius | `targeting_mult = 0.80 + 0.004 * precision` |
| **luck** | Item roll quality | Position-band shift, see §7.3 |

Notes for implementers:

- **`power` multiplies damage, never adds it.** It applies at step 2 of the damage pipeline (§5.3), so it stacks multiplicatively with `amp` effects rather than double-dipping.
- **`focus` applies to monster attack cooldowns and item effects only — not to the rider's own active.** A high-focus rider should not also spam its signature ability; the rider active cooldown is a fixed constant.
- **`precision` never touches damage.** It only widens or narrows the window in which an attack connects. A low-precision rider on a `forward_cone` monster has to aim properly; a high-precision one gets a forgiving cone.
- **`guard` is a multiplier on damage taken, not a flat max-HP increase.** This keeps HP squarely a monster stat and means guard scales with the size of the hit rather than flattening small ones.

### 7.3 Luck and the item table

Luck does **not** get its own table. It shifts which **position band** you roll on in the existing item table (§9.2):

| Luck | Effect |
|---|---|
| ≥ 75 | Roll one band further **back** than your actual position (better items) |
| 26–74 | Roll on your actual position band |
| ≤ 25 | Roll one band further **forward** than your actual position (worse items) |

Shifts clamp at the ends of the table. This reuses all existing data, adds no new tuning surface, and means a lucky racer in 1st rolls like a mid-pack racer rather than getting a bespoke privileged table.

### 7.4 What a rider is

**The rider roster is undesigned.** Every rider provides exactly three things:

| Part | Detail |
|---|---|
| **Crew stats** | Five 0–100 ratings: power, focus, luck, guard, precision (§7.2). |
| **Passive** | One always-on effect. |
| **Active** | One activatable ability, on its own button and its own fixed cooldown, expressed as an attack record (§8.2). |

**Locked constraints:**

- Riders own the **crew axes only** — never HP, speed, acceleration, handling, or weight (§7.1).
- Crew axes sum to **250** per rider (§7.1). See §18 #5 — this is a guardrail, not a guarantee.
- The active must be expressible in the §8.1 targeting vocabulary. Add a mode there if needed; never special-case rider code.
- `focus` does **not** accelerate the rider's own active (§7.2). Its cooldown is a fixed constant.

### 7.5 Roster slots (to author)

Three riders at MVP (§17, M4), expanding later — riders are the cheapest content in the game (§17, M10).

| Rider | Role | Power | Focus | Luck | Guard | Precision | Σ |
|---|---|---|---|---|---|---|---|
| `RIDER_A` | TBD | TBD | TBD | TBD | TBD | TBD | 250 |
| `RIDER_B` | TBD | TBD | TBD | TBD | TBD | TBD | 250 |
| `RIDER_C` | TBD | TBD | TBD | TBD | TBD | TBD | 250 |

| Rider | Passive | Active ID | Active function | TGT (§8.1) | CD |
|---|---|---|---|---|---|
| `RIDER_A` | TBD | `RA1` | TBD | TBD | TBD |
| `RIDER_B` | TBD | `RB1` | TBD | TBD | TBD |
| `RIDER_C` | TBD | `RC1` | TBD | TBD | TBD |

**Author a use-condition alongside each active** — a plain-language rule for when it is correct to press. The AI reads that condition (§11.5) rather than hard-coding behaviour per rider, so an unauthored condition means an AI that never uses the ability.

### 7.6 Design checklist

1. **Does each rider change how the *same* monster plays?** That is the entire test of the two-pick system. If swapping riders only changes numbers, the second pick is not earning its place.
2. **Is any rider a strict upgrade?** The 250 budget prevents equal-total dominance, not equal-*value* dominance — see §18 #5.
3. **Do the three cover distinct crew profiles?** Three riders all clustered around 50/50/50/50/50 is three copies.
4. **Does any passive create a death spiral?** Effects that scale *up* against wounded targets are the classic offender — they convert "losing" into "already lost", and they interact badly with the optional low-health handicap (§5.7). See §18 #10.
5. **Do the actives cover different targeting modes?** Three `self_buff` actives is a missed opportunity and makes the rider button feel samey.
6. **Is the active's cooldown long enough to be a decision?** A short cooldown makes it a fourth attack; a long one makes it a moment. The second is the intent.

### 7.7 Loadout resolution

At race start, the pair is resolved **once** into a flat stat block by a pure function (§14.6):

```
resolve_loadout(monster, rider) -> RacerStats
```

The result is stored in racer state and **never recomputed mid-race**. This keeps loadout math out of the per-tick hot path, keeps it out of the determinism surface, and means the netcode transmits a resolved stat block rather than re-deriving it on every peer.

---

## 8. Attacks & Targeting

Attacks are **data, not code**. Each attack is a record specifying a targeting mode plus parameters. Implementers should build the six targeting modes once and compose all attacks — monster attacks, rider actives, and items alike — from them. Adding a monster or a rider should require **zero** new attack-resolution code.

### 8.1 Targeting modes

*Starting palette — offered, not imposed.* Forward-cone, drop-behind and lock-on were specified up front; the other three are proposals. **Extend this list freely as the roster is designed** — adding a mode here is the correct response to an ability that doesn't fit, and is much cheaper than special-casing it later.


| Mode | Behaviour | Key params |
|---|---|---|
| `forward_cone` | Instant hitscan within a cone in front of the attacker. All valid targets in the cone are hit. | `range`, `half_angle`, `max_targets` |
| `drop_behind` | Spawns a persistent entity at the attacker's position, optionally with backward velocity. Damages on contact. | `lifetime`, `initial_velocity`, `count`, `spread` |
| `lock_on` | Acquires the nearest valid target within `range` and inside `acquire_angle` of facing, then spawns a homing projectile. Fails (and refunds half the cooldown) if no target. | `range`, `acquire_angle`, `turn_rate`, `speed` |
| `aimed_arc` | Lobbed projectile along the attacker's facing with a fixed travel distance. Passes over ground-level entities. Damages on landing (small AoE) or on direct contact. | `travel_distance`, `blast_radius`, `speed` |
| `aura` | Instant radial effect centred on the attacker. Optionally leaves a lingering zone at the cast position. | `radius`, `linger_duration` |
| `self_buff` | Applies a timed modifier to the attacker. No targeting. May carry a self-cost. | `duration`, `modifiers`, `self_cost` |

The rider `precision` stat (§7.2) scales `half_angle`, `range`, `acquire_angle`, and `blast_radius` — the *generosity* params — and nothing else.

### 8.2 Shared attack fields

Every attack record carries:

```
id, display_name, targeting_mode, damage, cooldown_s,
params: { ...mode-specific... },
modifiers: [ ...status effects applied on hit... ],
vfx_id, sfx_id
```

Monster attacks, rider actives, and item effects all use this same record type. There is one attack table, not three.

### 8.3 Resolution rules

- **Friendly fire:** always on. There are no teams in MVP.
- **Self-damage:** attacks never damage their owner unless the attack explicitly declares `self_cost`. A lingering zone is the exception worth stating: its owner *is* immune to their own zone, but other racers' zones hurt them.
- **Cooldowns are independent per attack.** No global cooldown, no ammo. A monster with three attacks can fire all three back to back, and the rider active is on a fourth independent timer.
- **i-frames gate the hit, not the cast.** An attack that lands during a target's i-frames deals 0 and does not consume its own effect (a lingering zone will hit again when i-frames expire).
- **KO'd and destructing racers are not valid targets** for anything, including `lock_on` acquisition.
- **Attack ownership persists past owner death.** A projectile in flight when its owner is KO'd still resolves and still credits the kill to the (now dead) owner. This matters for Deathmatch scoring.

### 8.4 Status modifiers

A small, closed vocabulary. Modifiers stack additively unless noted; re-applying refreshes duration. **These identifiers are mechanical, not flavour** — `dot` rather than `burn`, `proj_immune` rather than `phase` — so the vocabulary survives whatever fiction the cast ends up with.

| Modifier | Effect |
|---|---|
| `dot` | HP/s damage over time. **Ignores i-frames.** |
| `slow` | Multiplier on top speed (<1). |
| `unwieldy` | Multiplier on turn rate. |
| `stagger` | Zeroes throttle input for a short duration. Use sparingly — losing control is unfun. |
| `shield` | Absorbs a flat amount of incoming damage before HP. Applies at step 6 of §5.3. |
| `amp` | Multiplier on outgoing damage. Applies at step 3 of §5.3. |
| `proj_immune` | Immune to projectiles. Does not block `aura` or contact. |
| `haste` | Multiplier on top speed (>1). |

---

## 9. Items

Items are the SMK layer sitting on top of monster attacks and rider abilities. They do two jobs: **catch-up balancing** and **giving every loadout access to effects it doesn't natively have.**

### 9.1 Item boxes

- Placed in the track object layer (§10.3), typically in rows across the road.
- Respawn **5 s** after being collected. **This timer is per-racer, not global** — a rider passive may shorten it (§7.4), so a box that is spent for one racer may be live for another. Implement box availability as a per-racer cooldown, not a single world flag.
- Collecting fills the racer's **single item slot**. A racer holding an item cannot pick up another until they use it. (One slot, SMK-style. No item queue.)
- Airborne racers (hopping) **can** collect boxes.

### 9.2 The item set (to author)

**The item set is undesigned.** What is fixed is the *shape*: a small set of one-slot pickups, rolled from a position-weighted table so the roll favours racers who are behind.

**Required categories** — these came from the brief and must be covered:

| Category | Requirement |
|---|---|
| **Heal** | Restore HP. The only counter to permanent chip damage besides monster and rider abilities. |
| **Attack modifier** | Boost or modify *the loadout's own attacks* rather than replacing them. This is the design pattern to follow for every future modifier item — a damage multiplier plays completely differently on a damage-over-time monster than on a burst one, and does so for free. |
| **One-off attack** | Grant a single-use attack the monster doesn't natively have, expressed through the §8.1 targeting vocabulary. |

Anything beyond those three is open. Target roughly **6 items** at MVP (§17, M4).

**Roll table (to author).** Weights are relative within a position band; the rider's `luck` shifts which band is rolled on (§7.3).

| Item | 1st | 2nd–3rd | Mid | Last 2 |
|---|---|---|---|---|
| `ITEM_1` | TBD | TBD | TBD | TBD |
| `ITEM_2` | TBD | TBD | TBD | TBD |
| … | | | | |

**Design notes:**

- The catch-up gradient is the point of the band structure — a leader and a straggler should not roll the same distribution.
- An item that is *only* good in 1st or *only* good in last is fine and often better than a bland universal one.
- Every offensive item resolves through the same §8 machinery as monster attacks. No bespoke item combat code.

### 9.3 Usage rules

- One button uses the held item. `self_buff`-shaped items apply instantly; offensive items resolve through the same §8 targeting machinery as monster attacks and rider actives.
- Items cannot be dropped or held indefinitely to deny others — but there is deliberately **no** hold-behind-you shield mechanic (that's a Mario Kart convention, not an SMK one).

---

## 10. Tracks

### 10.1 Overall format

A track is a directory of data, not code:

```
content/tracks/<track_id>/
  track.json        # metadata + object layer + waypoints
  tilemap.bin       # 128*128 bytes, one tile ID per cell
  tiles.png         # tile atlas, 8x8 tiles
  palette.json      # tile ID -> surface type + flags
```

The tilemap composites into a **1024×1024** track texture (128 tiles × 8 px), which is what the Mode 7 renderer samples. World units map 1:1 to texture texels.

### 10.2 Tile palette

Each tile ID maps to:

```
{ "id": 17, "surface": "GRASS", "solid": false, "damage": 0, "anim": null }
```

`surface` drives §4.4. Two tiles can share a surface but differ visually. Animated tiles cycle a frame list — used for water, lava, and finish-line checkers.

### 10.3 Object layer

In `track.json`:

- `spawn_grid`: ordered list of 8 start positions + facing, staggered SMK-style.
- `checkpoints`: ordered list of line segments across the road. Used for progress, position ranking, and pit/off-track recovery. **A racer must cross checkpoints in order** — this is the anti-shortcut-abuse mechanism, exactly as SMK did it.
- `finish_line`: which checkpoint is the finish (circuits) or the terminal checkpoint (point-to-point).
- `item_boxes`: positions.
- `hazards`: typed static or moving obstacles with damage values.
- `topology`: `"circuit"` or `"point_to_point"`.
- `laps`: integer for circuits; ignored (and hidden in HUD) for point-to-point.

### 10.4 AI waypoint graph

Also in `track.json`. A list of nodes:

```
{ "pos": [x, y], "width": 90, "target_speed": 0.85, "next": [id, ...] }
```

- `width` — usable road half-width at this node; the AI treats it as its lane budget.
- `target_speed` — fraction of the AI's top speed it should aim for here. Corners get low values.
- `next` — supports branching for alternate routes. Point-to-point tracks have a terminal node with an empty `next`.

**Authoring rule:** the waypoint line is the *racing* line, not the road centreline. Put it where a good driver would drive.

### 10.5 Track slots (to author)

**Track designs are undesigned.** Four tracks at MVP (§17, M4). What is fixed is the topology split and what each slot has to prove.

| # | ID | Topology | Laps | Must exercise | Design |
|---|---|---|---|---|---|
| 1 | `TRACK_1` | Circuit | 4 | Basic driving, lap counting, item box rows | TBD |
| 2 | `TRACK_2` | Circuit | 4 | Hazards, `PIT` recovery, shunt kills | TBD |
| 3 | `TRACK_3` | Circuit | 4 | Surface variety, a branching alternate route | TBD |
| 4 | `TRACK_4` | **Point-to-point** | — | The whole no-laps path: progress bar, terminal checkpoint, last-standing finish | TBD |

**Locked constraints:**

- **At least one track must be point-to-point.** Circuits alone would leave a whole code path untested, and the topology split was an explicit requirement (§2).
- Between them the four tracks should exercise **every surface type in §4.4** and at least one branching route, so the systems are proven before M5 rather than after.
- Every track needs a waypoint graph authored on the *racing* line, not the centreline (§10.4).

**Design notes:**

- Track width is the main lever on how much combat happens. Narrow forces contact; wide lets the field spread and turns it into a race. Vary it deliberately across the four.
- A point-to-point track that narrows toward the end pushes the field together for the finish, which makes a last-standing win more likely — worth considering for `TRACK_4`, since that is the outcome it exists to prove.

---

## 11. AI

### 11.1 Core rule

**AI drives through the exact same input interface as a human.** An AI produces an input frame and hands it to the simulation. The simulation cannot tell the difference.

```
InputFrame: throttle, brake, steer, hop, attack_1..3, rider_active, use_item
```

This is non-negotiable: it's what makes AI headlessly testable, keeps the sim pure (§14), and means the netcode doesn't need a special path for bots.

AI racers are assigned a full loadout (monster + rider) exactly like humans, and the lobby can constrain or randomise it.

### 11.2 Steering

Standard lookahead pursuit against the waypoint graph:

1. Find the nearest waypoint ahead on the racer's route.
2. Pick a lookahead target `L` units further along, where `L` scales with current speed.
3. Offset the target laterally within `width` based on a per-AI **line bias** and local avoidance.
4. Steer toward it, proportional to angle error, clamped to the monster's turn rate.
5. Throttle toward the `target_speed` of the upcoming node, braking early for tight corners.

### 11.3 Difficulty knobs

One set of knobs, three presets. Never give AI abilities a human doesn't have (no extra top speed, no perfect aim through walls).

| Knob | Easy | Normal | Hard |
|---|---|---|---|
| `reaction_delay` (ticks) | 20 | 10 | 4 |
| `line_error` (units of lateral wander) | 45 | 20 | 6 |
| `corner_skill` (0–1, closeness to optimal braking) | 0.5 | 0.75 | 0.95 |
| `aim_error` (radians) | 0.35 | 0.15 | 0.04 |
| `threat_awareness` (0–1, chance to react to an incoming projectile) | 0.2 | 0.6 | 0.9 |
| `ability_timing` (0–1, quality of item **and rider active** decisions) | 0.3 | 0.65 | 0.9 |

### 11.4 Rubber-banding

Bounded and honest. AI top speed is scaled by distance to the human player's race progress:

```
scale = clamp(1.0 + k * (player_progress - ai_progress), 0.92, 1.08)
```

Hard caps at ±8%. AI never gets a speed the monster couldn't reach. **Rubber-banding is disabled entirely in multiplayer** — with multiple humans there's no single reference point, and it would feel arbitrary.

### 11.5 Combat behaviour

Every `AI_COMBAT_INTERVAL` (default 15 ticks), an AI evaluates:

- **Target selection** — score each rival by `(1 / distance) * (1 / their_hp_fraction) * targeting_feasibility`. Low-HP nearby rivals are attractive; kill-securing is correct play. If a rider passive rewards attacking wounded targets, that rider's AI weights them higher still.
- **Fire decision** — fire an attack if its targeting mode can plausibly connect (a `forward_cone` needs the target in cone; a `lock_on` needs lock). Never fire blind — wasted cooldowns look stupid. Cone and lock feasibility must use the AI's *own* precision-scaled params, so a low-precision AI correctly holds fire in situations a high-precision one would take.
- **Self-preservation** — below 30% HP, weight avoidance over aggression: prefer open road, break from the pack, hold healing items rather than trading.
- **Item usage** — heuristics by item *category*, not by item: healing below an HP threshold; defensive items when 2+ rivals are within threat range; attack modifiers immediately before a planned attack window; speed items on a straight. Each item authored in §9.2 declares which heuristic it uses.
- **Rider active usage** — the AI reads the **use-condition authored alongside each active** (§7.5) rather than hard-coding one branch per rider, gated by `ability_timing`. An active with no authored condition is never used by AI — treat a missing condition as an incomplete rider, and assert on it at content-load time.
- **Ramming** — an AI whose monster has a contact-damage trait (§6.1) actively steers into rivals when within a short radius and roughly alongside. Every other AI mildly avoids contact.

---

## 12. Camera, HUD & Presentation

### 12.1 Render target

**This is a modern game that looks like an old one.** The pixel aesthetic comes from a small internal render buffer; everything else — aspect ratio, output resolution, framerate — is contemporary. We are not reproducing SNES output specs, and we are not emulating SNES hardware.

- **Internal resolution: 320×180.** Exactly 16:9, square pixels.
- **Output:** integer-scaled to the display. Nearest-neighbour only, always.
- Optional post filter for a CRT look — **post-MVP, off by default.**

**Why 320×180.** It integer-scales exactly onto every common modern display, which is the whole reason to pick a low internal resolution in the first place — a non-integer scale factor destroys the pixel grid that the art style depends on:

| Output | Scale | Exact? |
|---|---|---|
| 1280×720 | 4× | yes |
| 1920×1080 | 6× | yes |
| 2560×1440 | 8× | yes |
| 3840×2160 (4K) | 12× | yes |

No other sensible 16:9 pixel resolution hits all four. (384×216 is exact at 1080p and 4K but not at 720p or 1440p; 480×270 is exact at 1080p and 4K only.)

**Pixel scale vs SMK.** 320×180 is *wider* and *shorter* than SMK's 256×224. Both differences are deliberate and both are fine:

- **Wider** — 320 px at the same sprite sizes means more peripheral vision than SMK had. For a combat racer this is an improvement, not a compromise: you can see the rival drawing alongside you before they hit you. Note it as a genuine gameplay difference from SMK, not just a framing one (§2).
- **Shorter** — 180 rows sounds like a big loss against 224, but SMK spent roughly half its screen on the map/HUD panel in single-player, leaving only ~112 rows of 3D view. We use nearly the whole frame, so we end up with *more* Mode 7 rows than SMK, not fewer.

**Square pixels.** The SNES displayed a 256×224 buffer at 4:3, so its pixels were non-square (~1.14:1). We use square pixels throughout. Do not attempt to reproduce SNES pixel aspect ratio — art authored on a square grid is what everything in §16 assumes.

**Fitting the window.** The internal buffer is a fixed 320×180 regardless of window size. To present it:

1. Pick the largest integer scale that fits the drawable area.
2. Centre it and **letterbox/pillarbox the remainder** with a flat colour. Never stretch to a non-integer factor, and never blur.
3. Fullscreen on an odd resolution uses the same rule — bars are correct, a smeared pixel grid is not.
4. Windows smaller than 320×180 are simply not supported; enforce a minimum window size.

**The internal buffer never changes size with the window.** This is a fairness requirement, not just a rendering convenience: if the buffer widened on wider displays, a player on an ultrawide would see rivals sooner than a player on a laptop. **Ultrawide (21:9) and 4:3 displays get pillarbox/letterbox bars, not extra or less field of view.**

### 12.2 Framerate

Two rates, deliberately decoupled. Confusing them is the most likely mistake in this section.

| | Rate | Fixed? |
|---|---|---|
| **Simulation** | 60 Hz | **Fixed. Never changes.** |
| **Render** | Display refresh (60 / 120 / 144 / 240 …) | Variable |

- **The 60 Hz simulation tick is a design constant, not a performance target.** Every duration in this document is expressed in ticks, the netcode budgets (§15.7) assume it, and determinism (§14.8) depends on it. It does not get raised to match a 144 Hz monitor, and it does not drop on a slow machine — a slow machine renders fewer frames, it does not simulate fewer ticks.
- **Rendering is uncapped and interpolated** (§14.3). At 144 Hz the renderer draws 144 interpolated frames from 60 simulated ticks and motion is genuinely smooth — this is not a 60 fps game with extra steps.
- **60 fps is the floor, not the ceiling.** The M0 spike (§17) budgets against 60; anything above is free.
- **Settings:** vsync on by default, with an optional framerate cap (60 / 120 / 144 / uncapped) for people who would rather not render 240 frames a second on a laptop battery.
- **Frame pacing matters at high refresh.** Use a monotonic clock for the accumulator and clamp `frame_dt` to avoid a spiral of death after a stall (a long hitch must drop ticks, not try to catch up all of them at once).

### 12.3 Camera

Chase camera in SMK's configuration:

- Fixed height above the plane (`CAM_HEIGHT`, *TUNING* start: 48 units).
- Fixed distance behind the kart (`CAM_DISTANCE`, start: 90 units), with mild lag so the view swings on hard turns.
- Camera yaw follows kart yaw with a short smoothing window — SMK's camera does not snap.
- Horizon line at a fixed screen row; the sky band above it is a scrolling gradient/backdrop that pans with camera yaw.
- **Horizontal field of view is authored explicitly** (*TUNING* start: **68°**) and the Mode 7 focal length is derived from it and the 320 px buffer width — not the reverse. Fixing the FOV rather than the focal length means the framing stays correct if the internal resolution is ever revisited (§18).

### 12.4 Screen layout

Because there's no split-screen (§2), the Mode 7 view occupies nearly the whole frame. 16:9 gives generous horizontal room and tight vertical room, so the HUD lives in the left and right margins rather than in a bottom band.

```
+----------------------------------------------------------------+  y=0
|  sky band + horizon                                            |
|                                                     [minimap]  |
|                    MODE 7 TRACK VIEW                           |
|                                                                |
|                                                    [item slot] |
|  [HP bar]                                                      |
|  [pos/lap]                       [atk cds] [rider cd]          |
+----------------------------------------------------------------+  y=179
```

HUD is overlaid on the 3D view, not a separate panel. All HUD elements sit in the outer ~20% of the frame so the driving line stays clear. **With only 180 rows, vertical HUD space is the scarce resource** — prefer widening an element over stacking a new row.

### 12.5 HUD elements

| Element | Position | Notes |
|---|---|---|
| **Own HP bar** | Bottom-left | Large, segmented, colour-shifts green→amber→red. The most important element on screen. |
| **Position** | Bottom-left, under HP | `3rd / 8`. Counts only living racers in the denominator, plus a small "×2 down" eliminated counter. |
| **Lap / progress** | Bottom-left | Circuits: `LAP 2/4`. Point-to-point: a horizontal progress bar. |
| **Minimap** | Top-right | Track outline + dots. **Rival dots are tinted by their HP** — this is how you find wounded targets. Own dot is white and larger. |
| **Item slot** | Right, mid | Single slot with the held item icon. Flashes when rolling. |
| **Attack cooldowns** | Bottom-centre | Two or three small radial/bar indicators, one per monster attack, mapped to their buttons. |
| **Rider active cooldown** | Bottom-centre, right of the attack row | **Visually distinct** from the monster attacks — different shape and accent colour, separated by a gap. The player must never confuse "my monster attack is ready" with "my rider ability is ready". |
| **Damage feedback** | Full-screen | Brief red vignette flash on taking damage; short screen shake on heavy hits. |
| **Kill feed** | Top-left | Two-line max, small text. Names the **monster**, not the rider: `<monster> KO'd <monster>`. Revisit once the cast exists — if riders end up with stronger identities than monsters, this should flip. |

### 12.6 Select and results screens

- **Select is two-stage:** monster first, then rider, with a live composite preview (§16.2) so the player sees the actual pairing before confirming. Back from rider select returns to monster select without losing the pick.
- The rider stage shows the five crew axes as bars and a one-line description of the passive and active.
- **Results screen** shows both portraits per racer, monster above rider.

### 12.7 Sprite rendering

- Racers are billboard sprites scaled by distance from camera, sampled from a rotation-frame set (§16).
- The rider is composited onto the monster **before** distance scaling, so the pair scales as a single unit and never separates.
- **Draw order:** far-to-near. Racers and projectiles share one sorted list.
- Sprites clamp to a minimum on-screen size so a distant rival is still a visible pixel cluster, not a single pixel. At the smallest sizes the rider layer is dropped entirely — it's sub-pixel and only muddies the silhouette.
- Projectiles use the same billboard-and-scale path; ground-level entities (traps, lingering zones) render as **flat decals composited into the Mode 7 plane** before the affine transform, so they perspective-warp correctly with the road.

---

## 13. Audio

Specification only. Sourcing deferred (§18).

### 13.1 Constraints

- Target an SNES-adjacent palette: sample-based instruments, tight loops. Not chiptune, not orchestral.
- Channel budget: **8 simultaneous SFX voices** + 1 music stream. Voice stealing by priority when exceeded (own-damage and KO sounds have top priority).
- All SFX mono; music stereo.

### 13.2 SFX event list (MVP)

Engine loop (pitch-scaled by speed) · hop · drift scrub · surface change (road/dirt/grass/ice) · wall impact · racer-racer shunt · boost pad · item box collect · item roll tick · item use (per item) · attack cast (per attack) · **rider active cast (per rider)** · attack hit · attack whiff · damage taken (own) · heal · shield break · low-HP warning loop · KO (own) · KO (other) · lap complete · final lap fanfare · countdown 3-2-1-GO · race win · race loss · spectator camera switch.

### 13.3 Music

- One track per course (4 for MVP), one for arenas, one for the menu, one for results.
- A **final lap / last-two-alive** variation: same track, raised tempo and pitch. Cheap, effective, very SNES.

---

## 14. Technical Architecture

Written for implementers. These rules are structural — violating them makes networking and testing much harder later.

### 14.1 Stack

- **Python 3.11**
- **pygame-ce** (Community Edition) for windowing, input, blitting, audio
- **numpy** for the Mode 7 transform and any per-pixel work
- Possibly **moderngl** for GPU-assisted Mode 7 — decided by the M0 spike (§17)
- `pytest` for tests

### 14.2 The core rule: pure simulation

The simulation is a **pure, deterministic, engine-free object.**

```python
class Simulation:
    def step(self, inputs: dict[RacerId, InputFrame]) -> None: ...
    def snapshot(self) -> WorldState: ...
```

- **No pygame import anywhere under `smk/sim/`.** Not for vectors, not for rects, not for anything. Enforce this with a test that walks the module imports.
- No wall-clock reads, no `random.random()` — all randomness goes through a seeded RNG stored in sim state.
- `step()` advances exactly one fixed 60 Hz tick.

This buys three things at once: headless testing, replay recording (seed + loadouts + input stream = the entire race), and a netcode that can re-simulate.

### 14.3 Loop structure

Fixed timestep, decoupled render:

```
accumulator += frame_dt
while accumulator >= TICK_DURATION:
    sim.step(gather_inputs())
    accumulator -= TICK_DURATION
render(sim.snapshot(), alpha=accumulator / TICK_DURATION)
```

Rendering interpolates between the previous and current snapshot by `alpha`. The sim never varies with framerate: on a 144 Hz display this draws 144 interpolated frames from 60 simulated ticks, and on a struggling machine it draws fewer frames from the same 60 ticks.

Two requirements that matter once the render rate is uncapped (§12.2):

- **Monotonic clock** for `frame_dt`. Never a wall-clock read — a system time adjustment must not inject or swallow ticks.
- **Clamp `frame_dt`** (cap it at ~5 ticks' worth) before adding it to the accumulator. Without this, one long hitch — a load stall, a dragged window, a laptop resuming from sleep — queues a huge backlog of ticks, which takes longer to simulate than real time, which grows the backlog further. A hitch must drop simulation time, not try to replay all of it.

### 14.4 Mode 7 renderer

The core visual. For each screen row `y` below the horizon, the world-space sampling of that row is an affine function of screen `x`:

```
For row y:
  distance      = (cam_height * focal) / (y - horizon_y)
  scale         = distance / focal
  world_start   = cam_pos + rotate(forward * distance - right * (screen_w/2) * scale, cam_angle)
  world_step    = rotate(right * scale, cam_angle)
  # sample track_texture along world_start + x * world_step for x in 0..255
```

**Implementation:** build the full 320×(180−horizon) sample coordinate array with numpy broadcasting, then index the 1024×1024 track texture in one vectorised gather. Do **not** write a per-pixel Python loop — it will not hit 60 fps.

The M0 spike (§17) determines whether the numpy gather is fast enough at 320×~110 px (roughly 35k samples/frame — it should be, and note this must hold at the *render* rate, so budget against 144 Hz rather than 60) or whether the transform moves to a moderngl fragment shader.

Ground-level decals (traps, lingering zones, animated boost pads) are blitted into a **copy of the track texture region** before sampling, so they warp with the plane. Keep a dirty-rect list to avoid recopying 1 MB per frame.

### 14.5 Module layout

```
smk/
  sim/            # PURE. No pygame, no I/O, no clock.
    simulation.py   # Simulation, tick order
    loadout.py      # resolve_loadout(monster, rider) -> RacerStats (§7.7)
    racer.py        # driving state + physics (§4)
    combat.py       # the damage pipeline, i-frames, KO (§5)
    attacks.py      # the six targeting modes (§8)
    items.py        # roll table, luck band shift, item effects (§9)
    track.py        # runtime track: tiles, checkpoints, progress
    standings.py    # position ranking, race-end conditions (§3)
    rng.py          # seeded deterministic RNG
  ai/             # produces InputFrames. Imports sim types only.
    driver.py       # steering/throttle (§11.2)
    combat_brain.py # target selection, firing, rider actives (§11.5)
    difficulty.py   # knob presets
  render/         # pygame-ce + numpy. Imports sim, never the reverse.
    mode7.py        # the affine plane renderer (§14.4)
    sprites.py      # billboard scaling, rotation frames, rider compositing, draw order
    hud.py          # §12.5
    screen.py       # 320x180 target, integer scaling + letterbox
  net/            # §15
    transport.py    # UDP + reliability layer
    host.py         # authoritative host loop
    client.py       # prediction + reconciliation
    discovery.py    # LAN broadcast
    lobby.py        # loadout selection and exchange
  content/        # data loaders + the data itself
    monsters.json
    riders.json
    attacks.json   # monster attacks, rider actives, and item effects share this table
    items.json
    tracks/<track_id>/...
    loader.py
  app/            # entry point, scenes, menus
    main.py
    scenes/
tests/
  test_sim_purity.py   # asserts smk.sim imports nothing from pygame
  test_determinism.py  # same seed + loadouts + inputs => identical state hash
  test_loadout.py      # axis separation + budget invariants (§14.6)
  test_physics.py
  test_combat.py
  test_standings.py
```

**Dependency direction:** `render` → `sim`, `ai` → `sim`, `net` → `sim`. **Nothing** imports `render`. `sim` imports nothing from the rest of the project.

### 14.6 Loadout resolution

`smk/sim/loadout.py` holds one pure function:

```python
def resolve_loadout(monster: MonsterDef, rider: RiderDef) -> RacerStats: ...
```

It applies §4.3 (chassis mapping) and §7.2 (crew mapping) and returns a flat, immutable stat block. Rules:

- Called **once per racer at race start.** Never per tick, never on stat change — temporary modifiers (§8.4) are applied on top of the resolved block at use time, not by re-resolving it.
- Pure: same inputs, same output, no RNG, no I/O.
- `test_loadout.py` asserts the two structural invariants that keep the design honest:
  1. **Axis separation** — no rider field influences HP, top speed, accel, handling, or weight; no monster field influences power, focus, luck, guard, or precision.
  2. **Budget** — every rider in `riders.json` has crew axes summing to exactly 250.

Invariant 2 failing means someone added a rider that is a straight upgrade. That test is the design's guardrail, not a formality.

### 14.7 Data-driven content

Monsters, riders, attacks, items, and tracks are **JSON, loaded at startup and validated against a schema.** Adding a monster or a rider is a data edit plus art. If adding content requires touching `smk/sim/`, the targeting vocabulary (§8.1) is missing a mode — add the mode, not a special case.

### 14.8 Determinism

Required for replays and helpful for netcode:

- Fixed tick order, documented and stable: `inputs → physics → collisions → attacks → damage → items → KO/standings`.
- Seeded RNG in sim state; every consumer draws from it in a deterministic order.
- Iterate over racers by stable ID, never over a dict/set in insertion or hash order.
- Loadouts are resolved once, before tick 0, and are part of the replay header — a replay is `(seed, loadouts, input stream)`.
- Avoid accumulating float error across ticks where it affects gameplay outcomes (prefer recomputing from state over integrating).

`test_determinism.py` runs a fixed input stream twice and compares a state hash. This test failing is always a real bug.

---

## 15. Networking

### 15.1 Order of work

**LAN first, internet second.** LAN discovery removes NAT traversal from the problem entirely, which lets the netcode model be proven before connectivity engineering starts. See M5/M6 in §17.

### 15.2 Model: host-authoritative with client prediction

One peer is the **host**. It runs the authoritative simulation. Others are **clients**.

- Clients send **input frames** with tick numbers.
- Host simulates and broadcasts **state snapshots** (~20 Hz, delta-compressed).
- Clients **predict their own kart** locally at full 60 Hz by running the same sim forward from the last authoritative snapshot with their own unacknowledged inputs.
- On receiving a snapshot, a client **reconciles**: rewind own kart to the authoritative state, replay unacknowledged inputs. If the resulting position differs from what was displayed, smooth the correction over ~6 ticks rather than snapping.
- **Remote karts are interpolated**, not predicted — render them ~100 ms in the past between two known snapshots. Smooth is more important than current for karts you don't control.

### 15.3 Loadouts on the wire

Loadouts are **lobby state, not gameplay state.**

- Each client sends its monster+rider choice during lobby; the host echoes the full roster to everyone.
- Before tick 0, the host resolves every racer's loadout (§14.6) and includes the resolved stat blocks in the race-start handshake. **Peers use the host's resolved blocks rather than re-deriving them** — this removes an entire class of desync where two peers disagree about a stat because one has stale content JSON.
- A content-hash check on `monsters.json` / `riders.json` / `attacks.json` runs at handshake. Mismatch is reported clearly and refuses the connection; it does not silently proceed.

### 15.4 What is always host-authoritative

Non-negotiable, because these determine who wins:

- **Damage application and HP values.**
- **KO events and kill credit.**
- **Item box collection and item rolls** (including luck band shifts).
- **Rider active activation and its effects.**
- **Checkpoint crossings, lap counts, and standings.**
- **Race start and race end.**

Clients may show *predicted* feedback for responsiveness (a flash, a hit sound, a cooldown starting) but must never advance their own HP number. HP on screen always reflects the last host value.

### 15.5 Why not deterministic lockstep

Lockstep (every peer simulates everything, only inputs are exchanged) is attractive — the sim is already deterministic (§14.8) and bandwidth would be trivial. It's rejected as the default because:

- Every peer's input latency becomes the **worst** peer's latency; one bad connection degrades everyone.
- Any float divergence between platforms desyncs the entire race with no recovery path.
- Late joins and reconnects are effectively impossible.

The determinism work is still worth doing — it powers replays and makes host reconciliation cheap — but the network model is snapshot-based.

### 15.6 Transport

- **UDP** via `asyncio`, with a thin reliability layer: sequence numbers, acks, and reliable-ordered delivery only for lobby/control messages (loadout exchange included). Gameplay snapshots and inputs are unreliable — a dropped snapshot is superseded by the next one.
- Input frames are sent with **redundancy**: each packet carries the last 3 input frames, so a single drop doesn't stall the host.

### 15.7 Budget targets

| Metric | Target |
|---|---|
| Snapshot rate | 20 Hz |
| Snapshot size, 8 racers | < 400 bytes delta-compressed |
| Client → host input rate | 60 Hz, < 40 bytes/packet |
| Playable RTT ceiling | 150 ms |
| Target RTT | ≤ 100 ms |

Loadout data costs nothing per-tick — it is sent once at race start, not in snapshots.

### 15.8 LAN discovery (M5)

Host broadcasts a UDP beacon on a fixed port with `{game, version, host_name, mode, track, players, max_players}`. Clients listen and populate a server list. Version mismatch is shown, not hidden.

### 15.9 Internet P2P (M6)

- **NAT traversal:** UDP hole punching, coordinated through a lightweight rendezvous. Given the "no dedicated servers" non-goal, the rendezvous should be as thin as possible — ideally a small static coordination endpoint, or manual IP entry as a guaranteed fallback.
- **Relay fallback:** for symmetric NATs where punching fails. Document this as a known limitation for the first online release rather than solving it immediately; **manual direct-IP connection must always work** as the escape hatch.
- **Connection UX:** show connecting state, RTT, and a clear failure reason. Never a silent hang.

### 15.10 Disconnects

- A disconnected **client** has its racer converted to AI control for the remainder of the race, keeping its loadout. The race does not pause.
- A disconnected **host** ends the race for everyone; results are reported from the last known state. **Host migration is out of scope** — mid-race migration of an authoritative sim is a large project for a rare case. Revisit only if playtesting shows host drops are common.

---

## 16. Art Spec

Sourcing is deliberately undecided (§18). This section specifies what must be true of the art **regardless of where it comes from**, so any sourcing route can be validated against it.

### 16.1 Global constraints

| Constraint | Value |
|---|---|
| Internal resolution | 320×180 (16:9, square pixels) |
| Palette | Max 256 colours globally; per-sprite max 16 including transparency |
| Colour depth feel | SNES-adjacent. No gradients, no anti-aliasing, no soft alpha. |
| Alpha | 1-bit (on/off) only. No partial transparency in sprites. |
| Filtering | Nearest-neighbour everywhere, always |

### 16.2 Racers: layered monster + rider

**Riders are composited over monsters at runtime. They are never pre-combined.**

This is a budget decision with a large multiplier behind it. Pre-combining every pair costs 6 × 3 × 9 = **162** authored frames today and **54 more per new rider**. Layering costs **27** today and **9 per new rider**. At 6 riders the gap is 324 frames versus 54.

| Property | Monster | Rider |
|---|---|---|
| Base sprite size | 32×32 px | 16×16 px |
| Share of screen width at base size | 10% of 320 px | — |
| Rotation frames | 16 covering 360°, at 22.5° | **Same convention** — 16 at 22.5° |
| Authored frames | **9** (0°–180°); the other 7 are horizontal mirrors | **9**, same mirroring |
| Idle animation | 2-frame sway | 2-frame sway |
| KO animation | 6-frame destruction, non-rotating | 4-frame tumble, non-rotating |
| Portrait | 48×48 | 48×48 |
| Minimap dot | Yes | No — the monster owns the dot |

**Mount points.** Each monster declares, for each of its 9 authored rotation frames, a mount:

```
"mounts": [ { "x": 15, "y": 6, "scale": 1.0 }, ... ]   # one per authored frame
```

`x, y` position the rider's anchor on the monster sprite; `scale` sizes the rider to the monster, so one rider art set sits believably on both the smallest monster (`scale` ~0.85) and the largest (`scale` ~1.15) with no per-pair authoring. Mirrored frames mirror the mount `x` automatically.

**Compositing rules:**

- Rider draws **on top of** the monster, into a combined billboard, **before** distance scaling — the pair must scale as one unit and never separate or shear apart.
- **Authoring rule:** monster frames must leave the mount area unoccluded. The rider always draws on top, and we are explicitly not building per-frame occlusion masks. If a monster's silhouette would swallow the rider from behind, redesign the frame or move the mount.
- Below a threshold on-screen size, drop the rider layer entirely — at that scale it is sub-pixel noise that only muddies the monster's silhouette.
- Damage state: one damaged overlay (smoke/cracks) on the monster plus a palette shift toward red at low HP. Per-frame damage variants are too expensive. The rider gets no damage state.

**Per-monster art budget:** 9 rotation frames × 2 idle = 18 sprites + 1 damage overlay + 6 destruction frames + 1 portrait + 1 minimap dot + a 9-entry mount table.

**Per-rider art budget:** 9 rotation frames × 2 idle = 18 sprites + 4 tumble frames + 1 portrait. **No mount table** — mounts belong to monsters.

### 16.3 Track tiles

| Property | Value |
|---|---|
| Tile size | 8×8 px |
| Tilemap | 128×128 tiles → 1024×1024 px track texture |
| Atlas | Single PNG per track, max 256 tiles |
| Animated tiles | Max 4 frames, shared timer |

### 16.4 Projectiles, effects, decals

| Type | Size | Frames |
|---|---|---|
| Billboard projectile | 16×16 | 2–4 loop |
| Ground decal (trap, lingering zone) | 32×32, drawn into the plane pre-transform | 2–4 loop |
| Impact burst | 24×24 | 5, one-shot |
| Aura ring | 64×64 ground decal | 6, one-shot |

### 16.5 UI

- Font: 8×8 fixed-width bitmap, plus a 16×16 display face for headings and countdown. At 320×180 the 8×8 face gives **40 columns × 22 rows** — comfortable horizontally, tight vertically, which is why the HUD spreads sideways rather than stacking (§12.4).
- HP bar: segmented, 3 palette states (green/amber/red), authored as a 9-slice or a tiled fill.
- Item icons: 16×16, one per item.
- Cooldown indicators: 12×12 for monster attacks; a visually distinct 12×12 for the rider active (§12.5).
- Crew-axis bars for the rider select screen.
- Minimap: rendered procedurally from the tilemap (downsampled road mask), not hand-authored per track.

### 16.6 Placeholder policy

Until real art exists, every asset type has a **generated placeholder**: flat-colour shapes with the right dimensions and frame counts. Placeholders must match the final spec exactly in size and frame count — including the rider layer and mount tables — so swapping in real art is a file replacement with no code change.

---

## 17. Milestones

Each milestone has a goal, deliverables, and an **exit criterion** — something observable, not a feeling. Do not start milestone N+1 until N's exit criterion is demonstrably met.

### M0 — Mode 7 Spike

**Goal:** de-risk the single hardest technical assumption before building anything on top of it.

- Load a 1024×1024 track texture.
- Implement the affine per-scanline transform (§14.4) with numpy.
- Free camera: pan, rotate, zoom the horizon.
- Benchmark at 320×180. If numpy misses the target with headroom, port the transform to a moderngl fragment shader and benchmark again.
- Verify integer scaling and letterboxing to 720p, 1080p, 1440p and 4K, and to a deliberately awkward window size.
- **Write down the decision** (numpy vs moderngl) in §18 of this document.

**Exit:** a scrollable, rotatable Mode 7 plane at 320×180 holding a locked **144 fps** with at least 40% frame budget to spare, scaling cleanly to 1080p and 4K with no blurred pixels and no non-integer stretch. (144, not 60 — the renderer runs at display refresh, so 60 is the floor.)

### M1 — Core Driving

**Goal:** the driving feels like SMK.

- `sim` / `render` split established, with `test_sim_purity.py` passing.
- Fixed-timestep loop with render interpolation (§14.3).
- Kart physics: accel, top speed, turning, hop, drift, reverse (§4).
- Surface types with per-tile lookup (§4.4).
- Track loading from the §10.1 data format; one hand-made test circuit.
- Checkpoints, laps, off-track recovery.
- Chase camera (§12.3) with an explicit horizontal FOV, and a minimal HUD (speed, lap, position).
- Presentation layer: 320×180 buffer, integer scaling with letterbox, vsync, and the clamped-accumulator fixed-timestep loop (§14.3).

**Exit:** one monster drives 3 laps of a real track, the game correctly counts them, driving off-road slows you, and hitting a wall bounces you.

### M2 — Combat, Health & Loadouts

**Goal:** the core mechanical difference from SMK exists and works, including the two-part racer identity.

- HP, the §5.3 damage pipeline, i-frames, KO sequence.
- All six targeting modes implemented as composable data-driven attacks (§8.1).
- **`resolve_loadout` (§14.6) with `test_loadout.py` green** — axis separation and the 250-point budget enforced from the start, not retrofitted.
- Two monsters with full attack kits; **one rider** with its passive and active, proving the rider plumbing end to end.
- Item boxes with per-racer respawn timers, roll table with the luck band shift, and three items — one per required category in §9.2.
- Elimination and the last-standing race-end condition (§3.1).
- Damage HUD: HP bar, damage flash, kill feed, rider cooldown indicator.

**Exit:** two loadouts on a track can damage and KO each other; swapping the rider on the same monster visibly changes how the racer fights without changing how it drives; a race correctly ends both by last-standing and by finish line with survivors ranked properly.

### M3 — AI Opponents

**Goal:** a full grid without another human.

- Waypoint graph authoring for the test track (§10.4).
- AI steering, throttle, and cornering (§11.2).
- Difficulty presets (§11.3) and bounded rubber-banding (§11.4).
- Combat AI: target selection, firing, self-preservation, item usage, **rider active usage** (§11.5).
- AI loadout assignment, including randomised pairings.
- Headless test: N AI race M laps without getting stuck, going backwards, or falling off.

**Exit:** a grid of 7 AI + 1 human completes a full race, the AI fight each other and the player, they use their rider actives at sensible moments, and finishing positions look plausible across difficulties.

### M4 — MVP ★

**Goal:** a complete, playable, shippable single-player game.

- **All 6 monsters** with full kits and traits (§6).
- **All 3 riders** with passives and actives (§7) — 18 legal loadouts.
- **All 4 MVP tracks** (§10.5), including the point-to-point one — with all point-to-point logic (no laps, progress bar, terminal checkpoint).
- **Full item set** (§9.2).
- Front-end: title, **two-stage monster→rider select with live composite preview** (§12.6), track select, racer count / difficulty options, results screen with both portraits, rematch flow that remembers the loadout.
- Spectator mode for eliminated players (§5.6).
- Placeholder art meeting the §16 spec exactly, including rider layers and mount tables; placeholder audio covering the §13.2 event list.
- Settings: window size / fullscreen / scale factor, **vsync and framerate cap (60 / 120 / 144 / uncapped)**, volume, key bindings (including the rider active button).
- First real balance pass against the §5.1 TTK target, and a first read on whether the 250-point budget actually produces sidegrades.

**Exit:** a person who has never seen the game can launch it, pick a monster and a rider, finish a race, and understand why they won or lost — with no explanation from you.

### M5 — LAN Multiplayer

**Goal:** two machines, one race.

- Determinism cleanup; `test_determinism.py` green (§14.8).
- UDP transport with the reliability layer (§15.6).
- Host-authoritative loop, client prediction, reconciliation, remote interpolation (§15.2).
- **Loadout exchange and host-resolved stat blocks in the race-start handshake, with content-hash validation** (§15.3).
- LAN discovery beacon + server browser (§15.8).
- Lobby: monster and rider select, racer count, AI fill, ready-up.
- Disconnect → AI takeover, preserving loadout (§15.10).

**Exit:** two machines on the same LAN complete a full race together with no desync, no rubber-band snapping, matching loadouts on both screens, and correct synchronised results.

### M6 — Online P2P

**Goal:** race someone who isn't in the room.

- NAT traversal / hole punching with rendezvous (§15.9).
- Manual direct-IP connection as the guaranteed fallback.
- Latency compensation tuning against the §15.7 budgets.
- Connection UX: state, ping display, explicit failure reasons.
- Artificial latency/loss testing harness.

**Exit:** a full race between two peers over the internet at 100 ms simulated RTT with 2% packet loss is playable and correct.

### M7 — Battle Modes

**Goal:** the game away from the track.

- Arena map format and 2 arena maps.
- Battle: Last Standing, including the anti-stalemate pressure mechanic (§3.2).
- Battle: Deathmatch: respawns, spawn selection, spawn invulnerability, scoring (§3.3).
- Kill/assist/death attribution, verified against §8.3's ownership rules.
- Scoreboard UI showing loadouts.

**Exit:** both battle modes are playable vs AI and over the network, and scoring is correct including assists and environmental deaths.

### M8 — Cups

**Goal:** a reason to play more than one race.

- Grand Prix structure: cups of 4 tracks.
- Points per finishing position, cumulative standings, cup results.
- Difficulty classes (SMK's engine classes, reframed for monsters).
- Track, monster, **and rider** unlocks tied to cup completion.
- Save file for unlocks and records.

**Exit:** a 4-track cup can be played start to finish, standings accumulate correctly, and winning it unlocks something.

### M9 — Art & Audio Pass

**Goal:** it looks and sounds like the game it's pretending to be.

- Real monster sprites against the §16.2 spec.
- **Real rider sprites, and hand-tuned mount tables for every monster** — the mounts are art work, not code work, and getting a rider to sit right on six very differently shaped monsters is the fiddly part of this milestone.
- Real tilesets for all tracks.
- Real effects, UI, and font.
- Music per track + final-lap variation; full SFX set (§13).
- Optional CRT filter.

**Exit:** zero placeholder assets remain in the build, and every monster+rider pairing looks deliberate rather than accidental.

### M10 — Progression & Meta

**Goal:** long-tail engagement. **Deliberately last and deliberately underspecified** — design it when M8 has shipped and you know what the game actually is.

**Additional riders are the cheapest content lever the game has** — 9 authored frames plus a passive and an active, with no mount-table work and no new sim code — so expanding the rider roster is the natural first move here.

Other candidate directions (do not commit yet): per-loadout progression, cosmetic variants, unlockable alternate attacks, track records and ghosts, a challenge/achievement layer.

**Exit:** TBD at design time.

---

## 18. Open Questions

Tracked honestly so they don't ossify into unexamined defaults.

| # | Question | Blocks | Notes |
|---|---|---|---|
| 1 | **Art sourcing** — hand-authored, generated, or asset packs? | M9 | The §16 spec is written to be sourcing-agnostic. Decide before M9, not before M4 (placeholders cover MVP). |
| 2 | **Audio sourcing** — same question. | M9 | Same reasoning. |
| 3 | **Mode 7: numpy or moderngl?** | M0 exit | The M0 spike answers this. Record the answer here. |
| 4 | **TTK tuning** — is one lap right? | M4 balance pass | The single highest-risk design number in the document (§5.1). Only playtesting answers it. |
| 5 | **Does the 250-point rider budget actually produce sidegrades?** | M4 | It guarantees equal *totals*, not equal *value*. If guard is worth twice what luck is, the high-guard rider dominates regardless of arithmetic. Watch pick rates; the fix is weighting the axes, not raising a rider's total. |
| 6 | **Is 320×180 tall enough?** | M1 | 180 rows is the cost of exact integer scaling to every common display, and it is the tightest constraint in the presentation layer. If the Mode 7 view plus HUD proves cramped once M1 is drivable, the fallback is 384×216 — which keeps 16:9 and exact 1080p/4K scaling but loses exact 720p and 1440p. Decide from a real driving build, not from the spec. |
| 7 | **All content is undesigned** — the cast, their abilities and stats, the item set, the track layouts, the setting, and all naming. | M2 (first real content), M4 (full roster), M9 (art) | Deliberate: the systems were specified first so the content has somewhere to land. The authoring templates are §6.2, §6.3, §7.5, §9.2, §10.5. This is the single largest open item in the document, and it gates M2 onward — M0 and M1 need no content at all, which is why they come first. |
| 8 | **Is 3 riders enough variety at MVP?** | M4 playtest | Three is the agreed MVP count. If loadout choice feels thin once the roster exists, riders are the cheapest thing in the game to add (§17, M10). |
| 9 | **Should a rider active ever share a cooldown with monster attacks?** | M4 | Currently fully independent, and `focus` deliberately doesn't accelerate it. If having four independent buttons proves too busy at 320×180, coupling them is the first lever. |
| 10 | **Execute-style effects and the death spiral** | M4 | If the roster ends up with any effect that scales *up* against wounded targets, it is exactly the mechanic that turns "losing" into "already lost", and it compounds with the low-health handicap (#11). Not a decision yet — a trap to watch for while authoring (§7.6). |
| 11 | **Low-health handicap** — ship it or not? | M4 | §5.7. Implemented behind a flag, default off. Test both. Interacts badly with #10. |
| 12 | **Early-elimination boredom** — are short races + spectator + fast rematch enough? | M4 playtest | If not, the fallback is a ghost-harassment mechanic: KO'd players become a spectral hazard that can briefly interfere with the living. Designed but not committed. |
| 13 | **Battle: Last Standing anti-stalemate** — closing ring, or something less generic? | M7 | §3.2. A shrinking-arena ring is the obvious answer and also the least interesting one. |
| 14 | **Rubber-banding in single-player** — right call at all? | M4 | Currently bounded to ±8% and off in multiplayer. An elimination racer may not want catch-up at all. |
| 15 | **Progression design** | M10 | Intentionally deferred. |
| 16 | **NAT traversal rendezvous hosting** — conflicts with "no dedicated servers"? | M6 | A rendezvous is not a game server, but it is infrastructure. Direct-IP fallback must always work. |
| 17 | **Point-to-point track count** — one is enough to prove it; is it enough to be interesting? | Post-M4 | Depends on whether `TRACK_4` plays well. |
| 18 | **Friendly fire / teams** | Post-M7 | Currently no teams at all. Team battle is a natural extension, unscoped — and riders like RIDER_B would gain obvious support-shaped design room. |

---

## 19. Glossary

| Term | Meaning |
|---|---|
| **Mode 7** | The SNES graphics mode that applies a per-scanline affine transform to a background layer, producing a pseudo-3D ground plane. We reproduce the effect in software; we are not emulating SNES hardware. |
| **Affine transform** | A linear transform plus a translation. Applied per scanline, it produces the perspective-like floor of Mode 7. |
| **Monster** | What you drive. Provides the chassis axes, 2–3 built-in attacks, and a passive trait. |
| **Rider** | Who's driving. Provides the crew axes, a passive, and one activatable ability. Has its own model, composited over the monster. |
| **Loadout** | A monster + rider pair. The complete definition of a racer. |
| **Chassis axes** | HP, top speed, acceleration, handling, weight. Monster-only (§7.1). |
| **Crew axes** | Power, focus, luck, guard, precision. Rider-only (§7.1). |
| **Mount point** | A per-monster, per-rotation-frame `(x, y, scale)` anchor describing where and how large the rider sprite draws (§16.2). |
| **Internal resolution** | The 320×180 buffer everything is rendered into. Fixed — it never changes with window size or display (§12.1). |
| **Integer scaling** | Presenting the internal buffer at a whole-number multiple (4× to 720p, 6× to 1080p, 12× to 4K) so every source pixel becomes an exact square block. Non-integer scaling smears the pixel grid and is never used. |
| **Letterbox / pillarbox** | The flat-colour bars filling whatever the largest integer scale doesn't cover. Correct behaviour, not a bug — including on ultrawide displays, where the alternative would hand those players extra field of view. |
| **Simulation rate vs render rate** | 60 Hz fixed and display-refresh-variable respectively (§12.2). Distinct, and never conflated: a 144 Hz display gets 144 interpolated frames from 60 ticks. |
| **Billboard** | A 2D sprite always drawn facing the camera, scaled by distance. All racers and projectiles are billboards. |
| **Rotation frame** | One of the 16 pre-authored views of a sprite, selected by the angle between the racer's facing and the camera. Monsters and riders use the same 16-frame convention. |
| **KO** | Health reduced to zero. In Standard Race and Last Standing this means permanent elimination; in Deathmatch it means a respawn. |
| **Shunt** | A collision between two racers that displaces them. Weight-weighted (§4.6). Shunting someone into a wall or pit is intended play. |
| **Checkpoint** | An ordered line segment across the road, used for progress tracking, position ranking, and off-track recovery. Must be crossed in order. |
| **Waypoint** | A node in the AI's racing-line graph. Distinct from a checkpoint: waypoints guide AI, checkpoints measure progress. |
| **Tick** | One fixed simulation step, 1/60 s. All gameplay durations in this document are expressible in ticks. |
| **i-frames** | Invulnerability frames — a short window after taking attack damage during which further attack damage is ignored (§5.4). |
| **Damage pipeline** | The fixed ordered sequence every damage event passes through (§5.3). |
| **Snapshot** | A serialised world state sent from host to clients (§15.2). |
| **Reconciliation** | A client correcting its predicted state after receiving an authoritative snapshot. |
| **Circuit** | A looping track raced for N laps. |
| **Point-to-point** | A track raced once from start to finish, with no laps. |
| **TTK** | Time to kill — how long sustained focus takes to eliminate a racer. Target ≈ one lap (§5.1). |
| **Trait** | A monster's always-on passive (§6.1). A rider's equivalent is its **passive** (§7.4). |
