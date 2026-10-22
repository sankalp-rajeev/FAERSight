import math

import pytest

from faersight.disproportionality import Counts
from faersight.screening import screening_metrics


def test_hand_calculated_ror_interval_and_chi_square():
    row = screening_metrics(Counts(3, 1, 1, 5))
    # ROR=15; variance(log ROR)=1/3+1+1+1/5=38/15.
    assert row["ror_ci95_lower"] == pytest.approx(15 * math.exp(-1.96 * math.sqrt(38 / 15)))
    assert row["ror_ci95_upper"] == pytest.approx(15 * math.exp(1.96 * math.sqrt(38 / 15)))
    assert row["chi_square_pearson"] == pytest.approx(10 * 14**2 / 576)
    assert row["chi_square_yates"] == pytest.approx(10 * 9**2 / 576)
    assert not row["prr_screen_convention"]  # a and PRR pass, chi-square fails.


def test_prr_screen_requires_all_three_conditions():
    assert screening_metrics(Counts(10, 10, 10, 970))["prr_screen_convention"]
    assert not screening_metrics(Counts(2, 1, 1, 996))["prr_screen_convention"]
    assert not screening_metrics(Counts(100, 100, 400, 400))["prr_screen_convention"]


@pytest.mark.parametrize("cells", [(0, 1, 2, 3), (3, 1, 0, 6), (0, 0, 0, 0)])
def test_zero_cells_have_no_imputed_interval(cells):
    row = screening_metrics(Counts(*cells))
    assert row["ror_ci95_lower"] is None and row["ror_ci95_upper"] is None
    assert row["ror_ci_status"] == "unavailable_zero_cell"
    assert tuple(row[k] for k in "abcd") == cells


def test_degenerate_margin_and_small_yates_determinant():
    row = screening_metrics(Counts(0, 0, 1, 9))
    assert row["chi_square_yates"] is None
    assert not row["prr_screen_convention"]
    assert screening_metrics(Counts(1, 1, 1, 1))["chi_square_yates"] == 0


def test_sparse_infinite_prr_is_explicit_but_can_pass_convention():
    row = screening_metrics(Counts(5, 5, 0, 990))
    assert math.isinf(row["prr"])
    assert row["prr_screen_convention"]
    assert row["ror_ci95_lower"] is None
