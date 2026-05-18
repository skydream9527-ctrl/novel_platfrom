import json
from datetime import datetime
from pathlib import Path

from config import EVENTS_FILE, EVENT_CORRELATE_WINDOW_DAYS

TOOL_DEFINITION = {
    "name": "event_correlate",
    "description": "Correlate anomaly dates with business events (version releases, operations)",
    "input_schema": {
        "type": "object",
        "properties": {
            "anomaly_dates": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of anomaly dates in YYYYMMDD format",
            },
        },
        "required": ["anomaly_dates"],
    },
}


def _parse_date(date_str: str) -> datetime:
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def correlate_events(
    anomaly_dates: list[str],
    events: list[dict],
    window_days: int = EVENT_CORRELATE_WINDOW_DAYS,
) -> dict:
    if not anomaly_dates:
        return {"correlations": []}

    correlations = []
    for anomaly_date_str in anomaly_dates:
        anomaly_dt = _parse_date(anomaly_date_str)
        matches = []
        for event in events:
            event_dt = _parse_date(event["date"])
            diff = abs((anomaly_dt - event_dt).days)
            if diff <= window_days:
                matches.append((diff, event))
        matches.sort(key=lambda x: x[0])
        for diff, event in matches:
            correlations.append({
                "anomaly_date": anomaly_date_str,
                "matched_event": event,
                "days_diff": diff,
            })

    return {"correlations": correlations}


def handle_event_correlate(anomaly_dates: list[str]) -> str:
    try:
        events = json.loads(Path(EVENTS_FILE).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        events = []
    result = correlate_events(anomaly_dates, events)
    return json.dumps(result, ensure_ascii=False)
