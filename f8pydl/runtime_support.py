"""Explicit model selection and deduplicated runtime boundary diagnostics."""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from pathlib import Path

from .model_config import ModelTask, build_model_index
from .service_paths import resolve_user_path


def resolve_model_yaml(*, weights_dir: Path, explicit_path: str,
                       model_id: str, allowed_tasks: set[ModelTask]) -> Path:
    if explicit_path:
        return resolve_user_path(explicit_path)
    index = build_model_index(weights_dir, allowed_tasks=allowed_tasks)
    for item in index:
        if model_id and item.model_id == model_id:
            return item.yaml_path.resolve()
    if index:
        return index[0].yaml_path.resolve()
    raise FileNotFoundError(f"No model yamls found in {weights_dir} for allowedTasks={sorted(allowed_tasks)!r}")


@dataclass
class RepeatedErrorReporter:
    signature: str = ""
    repeats: int = 0

    def format(self, *, where: str, exc: Exception) -> str | None:
        signature = f"{where}:{type(exc).__name__}:{exc}"
        self.repeats = self.repeats + 1 if signature == self.signature else 1
        self.signature = signature
        if self.repeats != 1 and self.repeats % 100 != 0:
            return None
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        return f"{where} failed with {type(exc).__name__}: {exc}\nrepeat={self.repeats}\ntraceback:\n{details}"
