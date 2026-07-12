from types import SimpleNamespace
import subprocess
import sys

from src.classical import vienna_rnafold


def test_missing_backends_return_clear_failure(monkeypatch) -> None:
    monkeypatch.setattr(vienna_rnafold.shutil, "which", lambda _: None)
    monkeypatch.delitem(sys.modules, "RNA", raising=False)
    result = vienna_rnafold.run_rnafold(
        "GGGAAAUCC",
        executable="missing_rnafold",
        allow_python_fallback=False,
    )
    assert result["success"] is False
    assert result["status"] == "unavailable"
    assert "not found" in result["error"].lower()


def test_cli_output_is_parsed(monkeypatch) -> None:
    monkeypatch.setattr(vienna_rnafold.shutil, "which", lambda _: "RNAfold")
    completed = subprocess.CompletedProcess(
        args=["RNAfold", "--noPS"],
        returncode=0,
        stdout="GGGAAAUCC\n(((...))) ( -3.40)\n",
        stderr="",
    )
    monkeypatch.setattr(vienna_rnafold.subprocess, "run", lambda *a, **k: completed)
    result = vienna_rnafold.run_rnafold("GGGAAAUCC")
    assert result["success"] is True
    assert result["backend"] == "RNAfold CLI"
    assert result["reference_structure"] == "(((...)))"
    assert result["reference_energy"] == -3.4


def test_python_binding_fallback(monkeypatch) -> None:
    monkeypatch.setattr(vienna_rnafold.shutil, "which", lambda _: None)
    monkeypatch.setitem(
        sys.modules,
        "RNA",
        SimpleNamespace(fold=lambda sequence: ("(((...)))", -3.4)),
    )
    result = vienna_rnafold.run_rnafold("GGGAAAUCC")
    assert result["success"] is True
    assert result["status"] == "success_with_fallback"
    assert result["backend"] == "ViennaRNA Python RNA.fold"
