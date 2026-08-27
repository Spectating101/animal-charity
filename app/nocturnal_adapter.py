from __future__ import annotations

from typing import Any


def event_to_nocturnal_claim(event: dict[str, Any]) -> dict[str, Any]:
    """Map a relief ledger event into a Nocturnal-compatible claim envelope.

    No network call is made here. The adapter preserves the public repo's ability to
    export into a separately governed Nocturnal deployment without importing its
    private runtime.
    """
    sensitive = event.get("subject_type") in {"recipient"}
    text = f"{event.get('event_type')} for {event.get('subject_type')}:{event.get('subject_id')}"
    return {
        "claim": text,
        "matter_id": f"relief:{event.get('subject_type')}:{event.get('subject_id')}",
        "event_id": event.get("event_id"),
        "observed_at": event.get("occurred_at"),
        "source_url": event.get("source_ref"),
        "substance": "operational_event",
        "risk_level": "high" if sensitive else "medium",
        "review_required": True if sensitive else False,
        "review_reason": "beneficiary_privacy" if sensitive else None,
        "themes": ["animal_welfare", "food_security", "relief_operations"],
        "public_release_allowed": not sensitive,
    }
