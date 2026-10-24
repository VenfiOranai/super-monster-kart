"""Same seed + same inputs must give an identical state hash (GDD §14.8).

A failure here is always a real bug. The input stream grows teeth as racers
arrive in later M1 slices; the shape of the check stays the same.
"""

from smk.sim.input import InputFrame
from smk.sim.simulation import RacerId, Simulation

TICKS = 600  # ten seconds of race


def input_stream(tick: int) -> dict[RacerId, InputFrame]:
    """A fixed, varied script: throttle on, weaving, hopping every second."""
    steer = ((tick // 30) % 3) - 1
    return {RacerId(0): InputFrame(throttle=True, steer=float(steer), hop=tick % 60 == 0)}


def run(seed: int, ticks: int = TICKS) -> str:
    simulation = Simulation(seed)
    for tick in range(ticks):
        simulation.step(input_stream(tick))
    return simulation.snapshot().state_hash()


def test_same_seed_and_inputs_give_identical_hash():
    assert run(seed=1234) == run(seed=1234)


def test_different_seeds_give_different_hashes():
    assert run(seed=1234) != run(seed=4321)


def test_hash_changes_as_ticks_pass():
    assert run(seed=1234, ticks=TICKS) != run(seed=1234, ticks=TICKS + 1)


def test_step_advances_one_tick():
    simulation = Simulation(seed=0)
    simulation.step({})
    assert simulation.tick == 1
    assert simulation.snapshot().tick == 1
