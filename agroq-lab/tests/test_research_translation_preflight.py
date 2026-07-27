from pathlib import Path
from research_translation_preflight import run
def test_q26_q30_preflight(): assert run(Path(__file__).resolve().parents[2])==[]
