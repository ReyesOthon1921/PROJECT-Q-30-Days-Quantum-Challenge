from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RuntimeTracker:
    timings: Dict[str, float] = field(default_factory=dict)
    _active_step: Optional[str] = None
    _start_time: Optional[float] = None

    def start(self, step_name: str) -> None:
        if self._active_step is not None:
            raise RuntimeError(f"Timer already running for step: {self._active_step}")
        self._active_step = step_name
        self._start_time = time.perf_counter()

    def stop(self) -> float:
        if self._active_step is None or self._start_time is None:
            raise RuntimeError("No active timer to stop.")
        elapsed = time.perf_counter() - self._start_time
        self.timings[self._active_step] = elapsed
        self._active_step = None
        self._start_time = None
        return elapsed

    def record(self, step_name: str, runtime_seconds: float) -> None:
        if runtime_seconds < 0:
            raise ValueError("Runtime cannot be negative.")
        self.timings[step_name] = float(runtime_seconds)

    def summary(self) -> Dict[str, object]:
        return summarize_runtime(self.timings)


def summarize_runtime(step_timings: Dict[str, float]) -> Dict[str, object]:
    cleaned_timings = {step: float(runtime) for step, runtime in step_timings.items()}
    if not cleaned_timings:
        return {
            "step_count": 0,
            "total_runtime_seconds": 0.0,
            "slowest_step": None,
            "slowest_step_runtime_seconds": None,
            "step_timings": {},
        }
    total_runtime = sum(cleaned_timings.values())
    slowest_step = max(cleaned_timings, key=cleaned_timings.get)
    return {
        "step_count": len(cleaned_timings),
        "total_runtime_seconds": total_runtime,
        "slowest_step": slowest_step,
        "slowest_step_runtime_seconds": cleaned_timings[slowest_step],
        "step_timings": cleaned_timings,
    }


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Create runtime summary from step=seconds entries.")
    parser.add_argument("--step", action="append", default=[])
    args = parser.parse_args()
    timings: Dict[str, float] = {}
    for item in args.step:
        if "=" not in item:
            raise ValueError(f"Invalid step format: {item}")
        name, value = item.split("=", 1)
        timings[name] = float(value)
    print(json.dumps(summarize_runtime(timings), indent=2))
