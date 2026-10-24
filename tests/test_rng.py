import pytest

from smk.sim.rng import Rng


def test_matches_reference_splitmix64():
    # First output of the reference SplitMix64 for seed 0.
    assert Rng(0).next_u64() == 0xE220A8397B1DCDAF


def test_same_seed_gives_same_sequence():
    a, b = Rng(99), Rng(99)
    assert [a.next_u64() for _ in range(100)] == [b.next_u64() for _ in range(100)]


def test_state_reproduces_the_sequence():
    rng = Rng(7)
    rng.next_u64()
    # The state is a valid seed, so a captured state resumes the sequence exactly.
    resumed = Rng(rng.state)
    assert [resumed.next_u64() for _ in range(10)] == [rng.next_u64() for _ in range(10)]


def test_random_stays_in_unit_interval():
    rng = Rng(1)
    values = [rng.random() for _ in range(10_000)]
    assert all(0.0 <= v < 1.0 for v in values)
    assert 0.45 < sum(values) / len(values) < 0.55


@pytest.mark.parametrize(("low", "high"), [(-1.0, 1.0), (10.0, 20.0)])
def test_uniform_stays_in_range(low, high):
    rng = Rng(2)
    assert all(low <= rng.uniform(low, high) < high for _ in range(1_000))
