import json
import pytest
from tools.anomaly_detect import handle_anomaly_detect, detect_anomalies


def make_csv(values: list[int], start_date: int = 20260401) -> str:
    rows = ["date,dau"]
    for i, v in enumerate(values):
        date = start_date + i
        rows.append(f"{date},{v}")
    return "\n".join(rows)


def test_no_anomaly_in_flat_series():
    csv = make_csv([1000000] * 10)
    result = detect_anomalies(csv, "dau", "date", sigma=2.0)
    assert result["anomalies"] == []


def test_detects_single_spike_down():
    values = [1000000] * 9 + [500000]  # last point is a big drop
    csv = make_csv(values)
    result = detect_anomalies(csv, "dau", "date", sigma=2.0)
    assert len(result["anomalies"]) == 1
    assert result["anomalies"][0]["direction"] == "down"
    assert result["anomalies"][0]["severity"] in ("mild", "moderate", "severe")


def test_detects_single_spike_up():
    values = [1000000] * 9 + [3000000]  # last point is a big spike up
    csv = make_csv(values)
    result = detect_anomalies(csv, "dau", "date", sigma=2.0)
    assert len(result["anomalies"]) == 1
    assert result["anomalies"][0]["direction"] == "up"


def test_handle_returns_json_string():
    csv = make_csv([1000000] * 10)
    result = handle_anomaly_detect(csv, "dau", "date")
    data = json.loads(result)
    assert "anomalies" in data


def test_insufficient_data_returns_empty():
    csv = make_csv([1000000, 1100000])  # only 2 points
    result = detect_anomalies(csv, "dau", "date", sigma=2.0)
    assert result["anomalies"] == []
