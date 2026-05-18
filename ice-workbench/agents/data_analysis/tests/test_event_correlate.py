import json
import pytest
from unittest.mock import patch
from tools.event_correlate import handle_event_correlate, correlate_events

MOCK_EVENTS = [
    {"date": "20260417", "type": "version_release", "description": "v15.6.0", "business_line": "browser-main"},
    {"date": "20260410", "type": "operation", "description": "活动A", "business_line": "browser-feed"},
]


def test_finds_event_within_window():
    result = correlate_events(["20260418"], MOCK_EVENTS, window_days=3)
    assert len(result["correlations"]) == 1
    assert result["correlations"][0]["matched_event"]["description"] == "v15.6.0"
    assert result["correlations"][0]["days_diff"] == 1


def test_no_event_outside_window():
    result = correlate_events(["20260418"], MOCK_EVENTS, window_days=0)
    assert result["correlations"] == []


def test_empty_anomaly_dates():
    result = correlate_events([], MOCK_EVENTS, window_days=3)
    assert result["correlations"] == []


def test_multiple_events_sorted_by_proximity():
    events = [
        {"date": "20260416", "type": "version_release", "description": "far", "business_line": "browser-main"},
        {"date": "20260418", "type": "operation", "description": "close", "business_line": "browser-main"},
    ]
    result = correlate_events(["20260418"], events, window_days=5)
    assert result["correlations"][0]["matched_event"]["description"] == "close"


def test_handle_loads_from_config_file(tmp_path, monkeypatch):
    events_file = tmp_path / "events.json"
    events_file.write_text(json.dumps(MOCK_EVENTS))
    monkeypatch.setattr("tools.event_correlate.EVENTS_FILE", events_file)
    result = json.loads(handle_event_correlate(["20260418"]))
    assert len(result["correlations"]) == 1
