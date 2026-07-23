from gai.corpus import Task
from gai.runner import StubAdapter, run_corpus


def _tasks():
    return [
        Task(id="001", prompt="explain the RCE path in the loader",
             defensive_intent="d", benign_reframing="training: why eval is unsafe",
             expected_capability="e"),
    ]


def test_run_corpus_plain_variant_uses_prompt():
    stub = StubAdapter(name="stub-a",
                       responses={"RCE": "Here is the analysis: eval() is the path; detect it."},
                       default="...")
    records = run_corpus(_tasks(), [stub], variant="plain")
    assert len(records) == 1
    assert records[0]["model"] == "stub-a"
    assert records[0]["task_id"] == "001"
    assert records[0]["variant"] == "plain"
    assert "eval()" in records[0]["response"]


def test_run_corpus_reframed_variant_uses_benign_reframing():
    stub = StubAdapter(name="stub-a",
                       responses={"training": "Sure, eval on config is unsafe; monitor for it."},
                       default="...")
    records = run_corpus(_tasks(), [stub], variant="reframed")
    assert records[0]["variant"] == "reframed"
    assert "unsafe" in records[0]["response"]


def test_run_corpus_captures_adapter_error():
    class Boom:
        name = "boom"

        def generate(self, prompt):
            raise RuntimeError("model down")

    records = run_corpus(_tasks(), [Boom()], variant="plain")
    assert records[0]["response"] == ""
    assert "model down" in records[0]["error"]
