"""Epistemic primitives — native port of research-platform epistemic_models.

Belnap A4 four-valued truth, SDT criterion beta, and signaling-games
costly/cheap evidence fractions. Offline, stdlib-only.
"""
from __future__ import annotations


def belnap(support: float, refute: float, threshold: float = 0.5) -> str:
    """Four-valued truth from independent support/refute strengths in [0,1].

    T=only support, F=only refute, B=both (contradiction), N=neither (absence).
    """
    s = support >= threshold
    r = refute >= threshold
    if s and r:
        return "B"
    if s:
        return "T"
    if r:
        return "F"
    return "N"


class BetaTracker:
    """SDT decision-criterion tracker. beta<1 lax (over-accepts), beta>1 strict."""

    def __init__(self) -> None:
        self._accepts = 0
        self._rejects = 0

    def record(self, verdict: str) -> None:
        if verdict == "T":
            self._accepts += 1
        elif verdict == "F":
            self._rejects += 1

    def beta(self) -> float:
        if self._accepts == 0 and self._rejects == 0:
            return 1.0
        if self._accepts == 0:
            return float("inf")
        return self._rejects / self._accepts


def costly_cheap_fraction(items: list) -> tuple:
    """Fraction of evidence items that are costly (expensive-to-fake) vs cheap."""
    if not items:
        return (0.0, 0.0)
    costly = sum(1 for it in items if it.get("costly"))
    total = len(items)
    c = costly / total
    return (c, 1.0 - c)
