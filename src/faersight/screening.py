"""Descriptive screening conventions; no causal or clinical validation claim."""

import math

from faersight.disproportionality import Counts, metrics


def screening_metrics(counts: Counts) -> dict:
    """Keep raw cells; zero-cell log-Wald intervals are unavailable, never imputed.

    PRR convention: a >= 3, PRR >= 2, Yates-corrected chi-square >= 4.
    Pearson is also retained to make the correction choice inspectable.
    These unadjusted descriptive screens do not address multiplicity/confounding.
    """
    a, b, c, d = counts.a, counts.b, counts.c, counts.d
    values = metrics(counts)
    denominator = (a + b) * (c + d) * (a + c) * (b + d)
    determinant = abs(a * d - b * c)
    pearson = counts.n * determinant**2 / denominator if denominator else None
    yates = (
        counts.n * max(0, determinant - counts.n / 2) ** 2 / denominator if denominator else None
    )
    lo = hi = None
    status = "unavailable_zero_cell"
    if min(a, b, c, d) > 0:
        se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
        log_ror = math.log(a) + math.log(d) - math.log(b) - math.log(c)
        lo, hi = math.exp(log_ror - 1.96 * se), math.exp(log_ror + 1.96 * se)
        status = "log_wald_95"
    prr = values["prr"]
    screen = a >= 3 and not math.isnan(prr) and prr >= 2 and yates is not None and yates >= 4
    return {
        **values,
        "ror_ci95_lower": lo,
        "ror_ci95_upper": hi,
        "ror_ci_status": status,
        "chi_square_pearson": pearson,
        "chi_square_yates": yates,
        "chi_square_status": "defined" if denominator else "unavailable_zero_margin",
        "prr_screen_convention": screen,
    }
