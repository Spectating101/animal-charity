from __future__ import annotations

import hmac
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ActorRecord(BaseModel):
    actor_id: str
    display_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    token_env: str | None = None
    active: bool = True


class ActorRegistry(BaseModel):
    version: str
    roles: dict[str, list[str]]
    actors: dict[str, ActorRecord]


class ActorContext(BaseModel):
    actor_id: str
    roles: list[str]
    permissions: list[str]
    auth_mode: str

    def can(self, permission: str) -> bool:
        return "*" in self.permissions or permission in self.permissions


def load_actor_registry(path: str | Path) -> ActorRegistry:
    return ActorRegistry.model_validate_json(Path(path).read_text(encoding="utf-8"))


def registry_from_env() -> ActorRegistry | None:
    path = os.getenv("AFRN_ACTOR_REGISTRY", "").strip()
    if not path:
        return None
    return load_actor_registry(path)


def _permissions(registry: ActorRegistry, actor: ActorRecord) -> list[str]:
    permissions: set[str] = set()
    for role in actor.roles:
        permissions.update(registry.roles.get(role, []))
    return sorted(permissions)


def authenticate_actor(
    *,
    authorization: str | None,
    actor_id: str | None,
    demo_mode: bool,
    legacy_operator_token: str | None = None,
    registry: ActorRegistry | None = None,
) -> ActorContext:
    """Authenticate one attributable actor and derive permissions server-side.

    Production pilot mode may point AFRN_ACTOR_REGISTRY at a registry that maps
    actor ids to roles and token environment-variable names. The client supplies
    only X-Actor and a bearer token; it cannot assert its own role.

    When no registry is configured, the historical AFRN_OPERATOR_TOKEN path is
    retained for backwards-compatible bounded pilots. Demo mode remains explicit.
    """
    actor_id = (actor_id or "").strip()

    if demo_mode:
        return ActorContext(
            actor_id=actor_id or "demo-operator",
            roles=["demo"],
            permissions=["*"],
            auth_mode="demo",
        )

    if not actor_id:
        raise ValueError("X-Actor is required for attributable actions")

    if registry is not None:
        actor = registry.actors.get(actor_id)
        if actor is None or not actor.active:
            raise PermissionError("actor is not active in the configured registry")
        if not actor.token_env:
            raise RuntimeError("configured actor has no token_env")
        expected_token = os.getenv(actor.token_env, "")
        if not expected_token:
            raise RuntimeError(f"token environment variable {actor.token_env} is not configured")
        expected = f"Bearer {expected_token}"
        if not authorization or not hmac.compare_digest(authorization, expected):
            raise PermissionError("actor authorization failed")
        return ActorContext(
            actor_id=actor.actor_id,
            roles=actor.roles,
            permissions=_permissions(registry, actor),
            auth_mode="actor_registry",
        )

    token = (legacy_operator_token or "").strip()
    if not token:
        raise RuntimeError("operator token or actor registry not configured")
    expected = f"Bearer {token}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise PermissionError("operator authorization failed")
    return ActorContext(
        actor_id=actor_id,
        roles=["legacy_operator"],
        permissions=["*"],
        auth_mode="legacy_operator_token",
    )


def public_registry_summary(registry: ActorRegistry | None) -> dict[str, Any]:
    if registry is None:
        return {"mode": "legacy_or_demo", "version": None, "roles": []}
    return {
        "mode": "actor_registry",
        "version": registry.version,
        "roles": sorted(registry.roles),
        "actor_count": sum(1 for actor in registry.actors.values() if actor.active),
    }
