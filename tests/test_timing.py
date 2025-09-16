import math
from cosmicanimator.adapters.transitions.timing import Timing, schedule_items


def test_simultaneous_two_items():
    items = ["A", "B"]
    pairs = schedule_items(items, Timing(mode="simultaneous", offset=0.5))
    assert pairs == [("A", 0.5), ("B", 0.5)]


def test_sequential_intervals():
    items = list("ABC")
    pairs = schedule_items(items, Timing(mode="sequential", interval=0.3, order="forward"))
    assert pairs == [("A", 0.0), ("B", 0.3), ("C", 0.6)]


def test_total_normalization_even_spacing():
    items = list("ABCDE")
    t = Timing(mode="sequential", total=2.0, order="forward")
    pairs = schedule_items(items, t)
    starts = [s for _, s in pairs]
    assert starts == [0.0, 0.5, 1.0, 1.5, 2.0]


def test_reverse_flag_set():
    t = Timing(mode="sequential", order="reverse")
    assert t.mode == "sequential"
    assert getattr(t, "order", None) == "reverse" or getattr(t, "reverse", True)

