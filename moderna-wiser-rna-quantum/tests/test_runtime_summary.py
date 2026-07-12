from __future__ import annotations

import math
import pytest
from src.evaluation.runtime_summary import RuntimeTracker, summarize_runtime


def test_summarize_runtime_empty_input():
    result = summarize_runtime({})
    assert result["step_count"] == 0


def test_summarize_runtime_with_steps():
    result = summarize_runtime({"a": 0.2, "b": 0.4})
    assert result["step_count"] == 2
    assert math.isclose(result["total_runtime_seconds"], 0.6)
    assert result["slowest_step"] == "b"


def test_runtime_tracker_record_and_summary():
    tracker = RuntimeTracker()
    tracker.record("step_a", 0.25)
    tracker.record("step_b", 0.75)
    result = tracker.summary()
    assert math.isclose(result["total_runtime_seconds"], 1.0)


def test_runtime_tracker_rejects_negative_runtime():
    tracker = RuntimeTracker()
    with pytest.raises(ValueError):
        tracker.record("bad", -1.0)
