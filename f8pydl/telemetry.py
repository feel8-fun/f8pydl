"""Windowed inference metrics shared by the DL services (data channel only)."""
from __future__ import annotations
from collections import deque
from typing import Any
from .model_config import ModelSpec
from .video_frame_source import video_source_metadata

class RollingWindow:
    def __init__(self, *, window_ms: int) -> None:
        self.window_ms = int(window_ms)
        self._q: deque[tuple[int, float]] = deque()
        self._sum = 0.0

    def push(self, ts_ms: int, v: float) -> None:
        self._q.append((int(ts_ms), float(v)))
        self._sum += float(v)
        self.prune(ts_ms)

    def prune(self, now_ms: int) -> None:
        win = int(self.window_ms)
        if win <= 0:
            self._q.clear()
            self._sum = 0.0
            return
        cutoff = int(now_ms) - win
        while self._q and int(self._q[0][0]) < cutoff:
            _, v = self._q.popleft()
            self._sum -= float(v)

    def mean(self, now_ms: int) -> float | None:
        self.prune(now_ms)
        n = len(self._q)
        if n <= 0:
            return None
        return float(self._sum) / float(n)

    def count(self, now_ms: int) -> int:
        self.prune(now_ms)
        return int(len(self._q))


class InferenceTelemetry:
    def __init__(self) -> None:
        self.interval_ms = 1000
        self.window_ms = 2000
        self._last_emit_ms = 0
        self._frames = RollingWindow(window_ms=self.window_ms)
        self._infer_ms = RollingWindow(window_ms=self.window_ms)
        self._total_ms = RollingWindow(window_ms=self.window_ms)
        self._dup_skipped = RollingWindow(window_ms=self.window_ms)

    def set_config(self, *, interval_ms: int, window_ms: int) -> None:
        self.interval_ms = max(0, int(interval_ms))
        self.window_ms = max(100, int(window_ms))
        self._frames.window_ms = self.window_ms
        self._infer_ms.window_ms = self.window_ms
        self._total_ms.window_ms = self.window_ms
        self._dup_skipped.window_ms = self.window_ms

    def observe_frame(self, *, ts_ms: int, infer_ms: float, total_ms: float, dup_skipped: int) -> None:
        self._frames.push(ts_ms, 1.0)
        self._infer_ms.push(ts_ms, float(infer_ms))
        self._total_ms.push(ts_ms, float(total_ms))
        self._dup_skipped.push(ts_ms, float(dup_skipped))

    def should_emit(self, now_ms: int) -> bool:
        if int(self.interval_ms) <= 0:
            return False
        last = int(self._last_emit_ms or 0)
        return last <= 0 or (int(now_ms) - last) >= int(self.interval_ms)

    def mark_emitted(self, now_ms: int) -> None:
        self._last_emit_ms = int(now_ms)

    def summary(
        self,
        *,
        now_ms: int,
        node_id: str,
        service_class: str,
        model: ModelSpec | None,
        ort_provider: str,
        frame_id_last_seen: int | None,
        frame_id_last_processed: int | None,
    ) -> dict[str, Any]:
        win_ms = int(self.window_ms)
        frames = self._frames.count(now_ms)
        fps = (float(frames) * 1000.0 / float(win_ms)) if win_ms > 0 else None
        return {
            "schemaVersion": "f8dlTelemetry/1",
            "tsMs": int(now_ms),
            "nodeId": str(node_id),
            "serviceClass": str(service_class),
            "model": {
                "id": (model.model_id if model else ""),
                "task": (model.task if model else ""),
                "provider": (model.provider if model else ""),
            },
            "windowMs": int(win_ms),
            "source": video_source_metadata(),
            "frameId": {
                "lastSeen": int(frame_id_last_seen) if frame_id_last_seen is not None else None,
                "lastProcessed": int(frame_id_last_processed) if frame_id_last_processed is not None else None,
                "duplicatesSkippedAvg": self._dup_skipped.mean(now_ms),
            },
            "rates": {"fps": float(fps) if fps is not None else None},
            "timingsMsAvg": {
                "infer": self._infer_ms.mean(now_ms),
                "total": self._total_ms.mean(now_ms),
            },
            "runtime": {"ortProvider": str(ort_provider)},
        }

