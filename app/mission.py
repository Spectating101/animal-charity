from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MissionPolicy:
    mission_id: str
    version: str
    purpose: str
    autonomous_actions: frozenset[str]
    human_only_actions: frozenset[str]
    prohibited_actions: frozenset[str]
    stop_conditions: tuple[str, ...]

    @classmethod
    def load(cls, path: str | Path) -> "MissionPolicy":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            mission_id=data["mission_id"],
            version=data["version"],
            purpose=data["purpose"],
            autonomous_actions=frozenset(data["autonomous_actions"]),
            human_only_actions=frozenset(data["human_only_actions"]),
            prohibited_actions=frozenset(data["prohibited_actions"]),
            stop_conditions=tuple(data["stop_conditions"]),
        )

    def require_autonomous(self, action: str) -> None:
        if action not in self.autonomous_actions:
            raise PermissionError(f"mission constitution forbids autonomous action: {action}")

    def require_human(self, action: str) -> None:
        if action not in self.human_only_actions:
            raise PermissionError(f"action is not declared human-only: {action}")
