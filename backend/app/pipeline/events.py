"""In-process progress event bus (one list of events per analysis)."""
from __future__ import annotations

import threading
from datetime import datetime, timezone

from app.schemas.analysis import ProgressEvent
from app.schemas.records import SourceSystem


class EventBus:
    def __init__(self) -> None:
        self._events: dict[str, list[ProgressEvent]] = {}
        self._done: dict[str, bool] = {}
        self._lock = threading.Lock()

    def open(self, analysis_id: str) -> None:
        with self._lock:
            self._events[analysis_id] = []
            self._done[analysis_id] = False

    def emit(self, analysis_id: str, stage: str, status: str, label: str, detail: str | None = None,
             source: SourceSystem | None = None, data: dict | None = None) -> ProgressEvent:
        with self._lock:
            events = self._events.setdefault(analysis_id, [])
            ev = ProgressEvent(seq=len(events), stage=stage, status=status, label=label, detail=detail, source=source,
                               data=data or {}, at=datetime.now(timezone.utc))
            events.append(ev)
            return ev

    def close(self, analysis_id: str) -> None:
        with self._lock:
            self._done[analysis_id] = True

    def since(self, analysis_id: str, seq: int) -> tuple[list[ProgressEvent], bool, bool]:
        """Returns (events after seq, done, known)."""
        with self._lock:
            if analysis_id not in self._events:
                return [], True, False
            return self._events[analysis_id][seq:], self._done.get(analysis_id, False), True

    def all(self, analysis_id: str) -> list[ProgressEvent]:
        with self._lock:
            return list(self._events.get(analysis_id, []))


bus = EventBus()
