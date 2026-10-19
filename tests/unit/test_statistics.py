import math

import pytest

from faersight.disproportionality import Counts, count_pair, metrics


def test_hand_computed_statistics():
    values = metrics(Counts(3, 1, 1, 5))
    assert values["n"] == 10
    assert values["support"] == pytest.approx(0.3)
    assert values["confidence"] == pytest.approx(0.75)
    assert values["lift_python_check"] == pytest.approx(1.875)
    assert values["prr"] == pytest.approx(4.5)
    assert values["ror"] == pytest.approx(15)
    assert values["score_flags"] == ""


def test_counts_use_background_cases(transactions):
    assert count_pair(transactions, "alpha", "REACTION X") == Counts(3, 1, 1, 5)


def test_zero_cells_are_explicit_and_uncorrected():
    values = metrics(Counts(3, 1, 0, 6))
    assert math.isinf(values["prr"]) and math.isinf(values["ror"])
    assert values["zero_cell"]
    assert "prr_infinite" in values["score_flags"]
    assert values["a"] == 3 and values["c"] == 0


def test_undefined_scores():
    values = metrics(Counts(0, 0, 1, 9))
    assert math.isnan(values["confidence"])
    assert math.isnan(values["prr"])
    assert "ror_undefined" in values["score_flags"]


@pytest.mark.parametrize("cells", [(-1, 1, 2, 3), (0.5, 1, 2, 3), (True, 1, 2, 3)])
def test_invalid_cells(cells):
    with pytest.raises(ValueError):
        Counts(*cells)


def test_duplicate_universe_is_rejected(transactions):
    with pytest.raises(ValueError, match="Duplicate"):
        count_pair(transactions + transactions[:1], "alpha", "REACTION X")
