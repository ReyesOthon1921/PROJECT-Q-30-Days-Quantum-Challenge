from __future__ import annotations

from pathlib import Path

from src.evaluation.run_strict_classical_batch import read_dataset, run_batch


def test_read_dataset_loads_rows(tmp_path: Path):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        "sequence_id,sequence,description,source,expected_use\n"
        "seq_001,GGGAAAUCC,smoke,synthetic,debug\n",
        encoding="utf-8",
    )

    rows = read_dataset(dataset)

    assert len(rows) == 1
    assert rows[0]["sequence_id"] == "seq_001"
    assert rows[0]["sequence"] == "GGGAAAUCC"


def test_run_batch_creates_summary_and_report(tmp_path: Path):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        "sequence_id,sequence,description,source,expected_use\n"
        "seq_001,GGGAAAUCC,smoke,synthetic,debug\n"
        "seq_002,GGGAAACCC,second,synthetic,debug\n",
        encoding="utf-8",
    )

    result = run_batch(
        dataset_path=dataset,
        batch_id="pytest_batch",
        config_path=None,
        output_root=tmp_path / "batch_outputs",
    )

    assert result["success"] is True
    assert result["sequence_count"] == 2
    assert result["completed_count"] == 2
    assert Path(result["batch_summary"]).exists()
    assert Path(result["batch_report"]).exists()

    summary_text = Path(result["batch_summary"]).read_text(encoding="utf-8")
    assert "sequence_id" in summary_text
    assert "f1_score" in summary_text
