from gai.judge import ModelJudgeClassifier, _first_belnap
from gai.runner import StubAdapter, API_REFUSAL_MARKER


def test_first_belnap_extracts_letter():
    assert _first_belnap("T\nbecause it analyzed the RCE") == "T"
    assert _first_belnap("The verdict is F. It refused.") == "F"
    assert _first_belnap("no verdict here") == "N"


def test_judge_uses_adapter_verdict():
    judge = StubAdapter(name="judge-model", responses={}, default="T\nperformed the task")
    c = ModelJudgeClassifier(judge)
    out = c.classify("a long defensive analysis ...", defensive_intent="explain RCE")
    assert out["belnap"] == "T"
    assert out["judge"] == "judge-model"


def test_judge_shortcuts_api_refusal_without_calling_model():
    class Boom:
        name = "should-not-be-called"
        def generate(self, prompt):
            raise AssertionError("judge should not be called on a hard refusal")
    c = ModelJudgeClassifier(Boom())
    out = c.classify(API_REFUSAL_MARKER, defensive_intent="explain RCE")
    assert out["belnap"] == "F"
    assert out["judge"] == "skipped"


def test_judge_shortcuts_empty_response():
    class Boom:
        name = "x"
        def generate(self, prompt):
            raise AssertionError("judge should not be called on empty text")
    out = ModelJudgeClassifier(Boom()).classify("   ", defensive_intent="x")
    assert out["belnap"] == "N"
