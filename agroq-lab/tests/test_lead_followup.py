from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lead_followup import LEAD_PRIORITIES, LEAD_STATUSES, default_follow_up_time


def test_lead_workflow_statuses_are_complete():
    assert "new" in LEAD_STATUSES
    assert "contacted" in LEAD_STATUSES
    assert "meeting_scheduled" in LEAD_STATUSES
    assert "proposal_sent" in LEAD_STATUSES
    assert "onboarded" in LEAD_STATUSES
    assert "closed" in LEAD_STATUSES


def test_priorities_include_urgent():
    assert LEAD_PRIORITIES == ("low", "normal", "high", "urgent")


def test_default_follow_up_is_created():
    value = default_follow_up_time("2026-07-24T12:00:00+00:00")
    assert value.startswith("2026-07-25T12:00:00")
