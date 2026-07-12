from __future__ import annotations

import math

import pytest

from src.evaluation.runtime_summary import RuntimeTracker, summarize_runtime


def test_summarize_runtime_empty_input():
    result = summarize_runtime({})

    assert result["step_count"] == 0
    assert result["total_runtime_seconds"] == 0.0
    assert result["slowest_step"] is None
    assert result["slowest_step_runtime_seconds"] is None
    assert result["step_timings"] == {}


def test_summarize_runtime_with_steps():
    result = summarize_runtime(
        {
            "vienna_rnafold": 0.2,
            "candidate_generation": 0.1,
            "qubo_build": 0.4,
        }
    )

    assert result["step_count"] == 3
    assert math.isclose(result["total_runtime_seconds"], 0.7)
    assert result["slowest_step"] == "qubo_build"
    assert math.isclose(result["slowest_step_runtime_seconds"], 0.4)


def test_runtime_tracker_record_and_summary():
    tracker = RuntimeTracker()
    tracker.record("step_a", 0.25)
    tracker.record("step_b", 0.75)

    result = tracker.summary()

    assert result["step_count"] == 2
    assert math.isclose(result["total_runtime_seconds"], 1.0)
    assert result["slowest_step"] == "step_b"


def test_runtime_tracker_rejects_negative_runtime():
    tracker = RuntimeTracker()

    with pytest.raises(ValueError):
        tracker.record("bad_step", -1.0)


def test_runtime_tracker_start_stop():
    tracker = RuntimeTracker()

    tracker.start("example_step")
    elapsed = tracker.stop()

    assert elapsed >= 0.0
    assert "example_step" in tracker.timings