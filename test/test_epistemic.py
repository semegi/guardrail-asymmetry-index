from gai.epistemic import belnap, BetaTracker, costly_cheap_fraction


def test_belnap_true_when_only_support():
    assert belnap(support=0.9, refute=0.1) == "T"


def test_belnap_false_when_only_refute():
    assert belnap(support=0.1, refute=0.9) == "F"


def test_belnap_both_when_support_and_refute():
    assert belnap(support=0.8, refute=0.8) == "B"


def test_belnap_neither_when_absent():
    assert belnap(support=0.1, refute=0.1) == "N"


def test_beta_lax_below_one_when_over_accepting():
    t = BetaTracker()
    for _ in range(9):
        t.record("T")
    t.record("F")
    assert t.beta() < 1.0


def test_beta_strict_above_one_when_over_rejecting():
    t = BetaTracker()
    for _ in range(9):
        t.record("F")
    t.record("T")
    assert t.beta() > 1.0


def test_beta_neutral_when_empty():
    assert BetaTracker().beta() == 1.0


def test_costly_cheap_fraction():
    items = [{"costly": True}, {"costly": True}, {"costly": False}, {"costly": False}]
    costly, cheap = costly_cheap_fraction(items)
    assert costly == 0.5 and cheap == 0.5


def test_costly_cheap_fraction_empty():
    assert costly_cheap_fraction([]) == (0.0, 0.0)
