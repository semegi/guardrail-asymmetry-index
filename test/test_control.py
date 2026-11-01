"""Offline tests for the positive-control machinery. No network."""
import json
import unittest
from unittest import mock

from gai.control import CONFIGS, PREREGISTERED, check_prereg, config_of
from gai.runner import AnthropicAdapter, DeepSeekAdapter


def _entry(model, gai, delta=0.0, conflicts=0):
    return {"model": model, "gai": gai, "warrant": {"jailbreak_delta": delta, "belnap_conflicts": conflicts}}


class _Resp:
    def __init__(self, body):
        self._b = json.dumps(body).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestControl(unittest.TestCase):
    def test_every_config_has_preregistered_expectations(self):
        self.assertEqual(set(CONFIGS), set(PREREGISTERED))

    def test_config_is_read_from_model_name(self):
        self.assertEqual(config_of("deepseek-chat"), "base")
        self.assertEqual(config_of("deepseek-chat+strict"), "strict")
        self.assertEqual(config_of("deepseek-chat+selective"), "selective")

    def test_prereg_passes_when_the_instrument_sees_the_lockout(self):
        report = {"models": [_entry("m", 1.0), _entry("m+strict", 0.0),
                             _entry("m+selective", 0.25, delta=0.75, conflicts=3)]}
        self.assertTrue(all(r["passed"] for r in check_prereg(report)))

    def test_prereg_fails_when_the_instrument_is_blind(self):
        # A blind instrument scores every configuration the same: the controls must fail.
        report = {"models": [_entry("m", 1.0), _entry("m+strict", 1.0), _entry("m+selective", 1.0)]}
        failed = {r["config"] for r in check_prereg(report) if not r["passed"]}
        self.assertEqual(failed, {"strict", "selective"})

    def test_deepseek_sends_system_prompt_first(self):
        seen = {}

        def fake(req, timeout):
            seen.update(json.loads(req.data))
            return _Resp({"choices": [{"message": {"content": "ok"}}]})

        with mock.patch("urllib.request.urlopen", fake):
            a = DeepSeekAdapter(api_key="k", system="POLICY", name="ds+strict")
            self.assertEqual(a.generate("q"), "ok")
        self.assertEqual(a.name, "ds+strict")
        self.assertEqual(seen["messages"][0], {"role": "system", "content": "POLICY"})

    def test_anthropic_sends_system_field(self):
        seen = {}

        def fake(req, timeout):
            seen.update(json.loads(req.data))
            return _Resp({"stop_reason": "end_turn", "content": [{"type": "text", "text": "ok"}]})

        with mock.patch("urllib.request.urlopen", fake):
            AnthropicAdapter(api_key="k", system="POLICY").generate("q")
        self.assertEqual(seen["system"], "POLICY")

    def test_no_system_prompt_means_no_system_message(self):
        seen = {}

        def fake(req, timeout):
            seen.update(json.loads(req.data))
            return _Resp({"choices": [{"message": {"content": "ok"}}]})

        with mock.patch("urllib.request.urlopen", fake):
            DeepSeekAdapter(api_key="k").generate("q")
        self.assertEqual([m["role"] for m in seen["messages"]], ["user"])


if __name__ == "__main__":
    unittest.main()
