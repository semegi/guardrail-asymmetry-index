import json

import pytest

from gai.corpus import Task, load_tasks, assert_inert


def test_load_tasks_reads_seed_corpus():
    tasks = load_tasks("tasks")
    assert len(tasks) >= 3
    assert all(isinstance(t, Task) for t in tasks)
    ids = {t.id for t in tasks}
    assert "001" in ids


def test_load_tasks_requires_fields(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"id": "x", "prompt": "p"}))
    with pytest.raises(ValueError):
        load_tasks(str(tmp_path))


def test_assert_inert_rejects_live_url():
    t = Task(id="z", prompt="fetch https://evil.com/x", defensive_intent="d",
             benign_reframing="r", expected_capability="e")
    with pytest.raises(ValueError):
        assert_inert(t)


def test_assert_inert_rejects_public_ip():
    t = Task(id="z", prompt="connect to 8.8.8.8", defensive_intent="d",
             benign_reframing="r", expected_capability="e")
    with pytest.raises(ValueError):
        assert_inert(t)


def test_assert_inert_allows_synthetic_placeholders():
    t = Task(id="z", prompt="loader at dataset.example/loader, host 10.0.0.5",
             defensive_intent="d", benign_reframing="r", expected_capability="e")
    assert_inert(t)


def test_seed_corpus_is_all_inert():
    for t in load_tasks("tasks"):
        assert_inert(t)
