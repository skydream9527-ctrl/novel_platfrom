from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TraceRecord:
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    run_mode: str = ""
    matched_skills: list[str] = field(default_factory=list)
    used_tools: list[str] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    total_latency_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "timestamp": self.timestamp,
            "run_mode": self.run_mode,
            "matched_skills": self.matched_skills,
            "used_tools": self.used_tools,
            "tool_results": self.tool_results,
            "model": self.model,
            "total_latency_ms": self.total_latency_ms,
            "error": self.error,
        }


class TraceCollector:
    def __init__(self, log_dir: Path | None = None):
        self._log_dir = log_dir
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)

    def new_trace(self, model: str = "") -> TraceRecord:
        return TraceRecord(model=model)

    def finalize(self, trace: TraceRecord) -> None:
        trace.total_latency_ms = (time.time() - trace.timestamp) * 1000
        logger.info(
            "Trace[%s] mode=%s skills=%s tools=%s latency=%.0fms",
            trace.turn_id[:8],
            trace.run_mode,
            trace.matched_skills,
            trace.used_tools,
            trace.total_latency_ms,
        )
        if self._log_dir:
            self._persist(trace)

    def _persist(self, trace: TraceRecord) -> None:
        path = self._log_dir / f"{trace.turn_id}.json"
        path.write_text(json.dumps(trace.to_dict(), ensure_ascii=False, indent=2))
