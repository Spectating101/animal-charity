from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.access_control import ActorContext, authenticate_actor, public_registry_summary, registry_from_env
from app.animal_welfare_control import WelfareLandscape, assess_area
from app.domain import AnimalGroup, Event, InventoryLot, Recipient, ResolutionEvidence, SupplyBatch
from app.nocturnal_adapter import event_to_nocturnal_claim
from app.preventive_welfare import PreventiveWelfareSnapshot, assess_preventive_system
from app.public_good_control import PublicGoodCase, assess_public_good_case
from app.service import ReliefService
from app.welfare_outcomes import WelfareOutcome, summarize_outcomes

BASE = Path(__file__).resolve().parents[1]
DB_PATH = os.getenv("AFRN_DB_PATH", str(BASE / "data" / "relief.db"))
RULEPACK = os.getenv("AFRN_RULEPACK", str(BASE / "config" / "rulepacks" / "tw_dog_cat_pilot.json"))
MISSION = os.getenv("AFRN_MISSION", str(BASE / "config" / "missions" / "animal_feed_security.json"))
OPERATOR_TOKEN = os.getenv("AFRN_OPERATOR_TOKEN", "")
DEMO_MODE = os.getenv("AFRN_DEMO_MODE", "0") == "1"
ACTOR_REGISTRY = registry_from_env()

app = FastAPI(
    title="Public-Good Control Plane / AFRN",
    version="0.4.0",
    description=(
        "Evidence-bounded public-good governance decision support with domain-specific constitutions, "
        "preventive animal-welfare routing, MBG case assessment, outcome evaluation and bounded feed-relief actuation."
    ),
)
service = ReliefService(DB_PATH, RULEPACK, MISSION)


def _auth_context(authorization: str | None, x_actor: str | None) -> ActorContext:
    try:
        return authenticate_actor(
            authorization=authorization,
            actor_id=x_actor,
            demo_mode=DEMO_MODE,
            legacy_operator_token=OPERATOR_TOKEN,
            registry=ACTOR_REGISTRY,
        )
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(401, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def require_permission(permission: str) -> Callable[..., ActorContext]:
    def dependency(
        authorization: str | None = Header(default=None),
        x_actor: str | None = Header(default=None, alias="X-Actor"),
    ) -> ActorContext:
        actor = _auth_context(authorization, x_actor)
        if not actor.can(permission):
            raise HTTPException(403, f"actor lacks permission: {permission}")
        return actor

    return dependency


def _case_digest(case: PublicGoodCase) -> str:
    canonical = json.dumps(case.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return (BASE / "app" / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    ok, count, bad = service.store.verify_ledger()
    return {
        "ok": ok,
        "ledger_events": count,
        "bad_event": bad,
        "rulepack": service.rules.version,
        "mission": service.mission.version,
        "access": public_registry_summary(ACTOR_REGISTRY),
    }


@app.get("/v1/summary")
def summary():
    cases = service.store.list("case")
    proposals = service.store.list("proposal")
    return {
        "recipients": len(service.store.list("recipient")),
        "animal_groups": len(service.store.list("group")),
        "supply_batches": len(service.store.list("supply")),
        "open_cases": sum(1 for c in cases if c["status"] != "resolved"),
        "resolved_cases": sum(1 for c in cases if c["status"] == "resolved"),
        "pending_proposals": sum(1 for p in proposals if p["review_state"] == "pending"),
        **service.impact_summary(),
        "mission_id": service.mission.mission_id,
        "agent_authority": sorted(service.mission.autonomous_actions),
        "human_only_authority": sorted(service.mission.human_only_actions),
        "prohibited_agent_actions": sorted(service.mission.prohibited_actions),
    }


@app.get("/v1/access/me")
def access_me(actor: ActorContext = Depends(require_permission("summary.read"))):
    return actor.model_dump(mode="json")


@app.post("/v1/public-good/assess")
def assess_public_good(
    case: PublicGoodCase,
    strict_evidence: bool = Query(default=False),
    actor: ActorContext = Depends(require_permission("public_good.assess")),
):
    """Run the selected domain constitution through the shared public-good router.

    strict_evidence requires every source_ref cited by the recommendation to be
    registered in the case evidence manifest. The audit event stores only a case
    hash and decision/provenance summary, not the full potentially sensitive payload.
    """
    assessment = assess_public_good_case(case)
    if strict_evidence and assessment.evidence_manifest.status != "complete":
        raise HTTPException(
            422,
            {
                "error": "strict evidence provenance failed",
                "manifest_status": assessment.evidence_manifest.status,
                "missing_refs": assessment.evidence_manifest.missing_refs,
            },
        )

    event = Event(
        event_type="public_good.assessed",
        subject_type="public_good_case",
        subject_id=case.case_id,
        actor=actor.actor_id,
        source_ref=str(case.metadata.get("source_ref")) if case.metadata.get("source_ref") else None,
        payload={
            "domain": case.domain.value,
            "input_sha256": _case_digest(case),
            "normalized_stages": [finding.stage for finding in assessment.normalized_findings],
            "problem_classes": [finding.problem_class for finding in assessment.normalized_findings],
            "structural_candidate_count": sum(1 for finding in assessment.normalized_findings if finding.structural_candidate),
            "data_gap_count": len(assessment.data_gaps),
            "constitution_ref": assessment.constitution_ref,
            "evidence_manifest_status": assessment.evidence_manifest.status,
            "registered_evidence_refs": assessment.evidence_manifest.registered_ref_count,
            "cited_evidence_refs": assessment.evidence_manifest.cited_ref_count,
            "strict_evidence": strict_evidence,
        },
    )
    event_hash = service.store.append_event(event)
    return assessment.model_dump(mode="json") | {
        "assessed_by": actor.actor_id,
        "auth_mode": actor.auth_mode,
        "audit_event_id": event.event_id,
        "audit_event_hash": event_hash,
    }


@app.post("/v1/welfare/assess")
def assess_welfare_landscape(
    landscape: WelfareLandscape,
    actor: ActorContext = Depends(require_permission("welfare.assess")),
):
    """Run the evidence-bounded lifecycle router.

    This endpoint proposes welfare transitions only. It never authorizes capture,
    treatment, sterilization, adoption, community return, dangerousness findings,
    specialist acceptance or any irreversible welfare decision.
    """
    assessment = assess_area(landscape)
    return assessment.model_dump(mode="json") | {"assessed_by": actor.actor_id}


@app.post("/v1/welfare/system/assess")
def assess_preventive_welfare_system(
    snapshot: PreventiveWelfareSnapshot,
    actor: ActorContext = Depends(require_permission("welfare.assess")),
):
    """Assess preventable bad-state transitions with determinant/access context."""
    try:
        assessment = assess_preventive_system(snapshot)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return assessment.model_dump(mode="json") | {"assessed_by": actor.actor_id}


@app.post("/v1/welfare/outcomes/summarize")
def summarize_welfare_outcomes(
    outcomes: list[WelfareOutcome],
    actor: ActorContext = Depends(require_permission("welfare.assess")),
):
    """Summarize verified welfare outcomes without treating handoff as success."""
    summary = summarize_outcomes(outcomes)
    return summary.model_dump(mode="json") | {"assessed_by": actor.actor_id}


@app.post("/v1/recipients")
def create_recipient(
    recipient: Recipient,
    actor: ActorContext = Depends(require_permission("operations.write")),
):
    recipient.status = "pending"
    recipient.welfare_review_ref = None
    return service.save(recipient, actor=actor.actor_id, event_type="recipient.recorded", source_ref=recipient.source_ref)


@app.post("/v1/recipients/{recipient_id}/review")
def review_recipient(
    recipient_id: str,
    approve: bool,
    review_ref: str,
    emergency_only: bool = False,
    actor: ActorContext = Depends(require_permission("review.write")),
):
    try:
        return service.review_recipient(
            recipient_id,
            approve=approve,
            actor=actor.actor_id,
            review_ref=review_ref,
            emergency_only=emergency_only,
        )
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/v1/groups")
def create_group(
    group: AnimalGroup,
    actor: ActorContext = Depends(require_permission("operations.write")),
):
    return service.save(group, actor=actor.actor_id, event_type="animal_group.recorded", source_ref=group.source_ref)


@app.post("/v1/inventory")
def create_inventory(
    item: InventoryLot,
    actor: ActorContext = Depends(require_permission("operations.write")),
):
    return service.save(item, actor=actor.actor_id, event_type="inventory.observed", source_ref=item.source_ref)


@app.post("/v1/supplies")
def create_supply(
    batch: SupplyBatch,
    actor: ActorContext = Depends(require_permission("operations.write")),
):
    return service.save(batch, actor=actor.actor_id, event_type="supply.observed", source_ref=batch.source_ref)


@app.get("/v1/cases")
def cases(actor: ActorContext = Depends(require_permission("audit.read"))):
    return service.store.list("case")


@app.get("/v1/proposals")
def proposals(actor: ActorContext = Depends(require_permission("audit.read"))):
    return service.store.list("proposal")


@app.post("/v1/agent/tick")
def agent_tick(
    horizon_days: float = Query(default=7, gt=0, le=30),
    target_buffer_days: float = Query(default=14, gt=0, le=60),
    actor: ActorContext = Depends(require_permission("operations.write")),
):
    try:
        return service.agent_tick(
            actor=f"public-welfare-agent:{actor.actor_id}",
            horizon_days=horizon_days,
            target_buffer_days=target_buffer_days,
        )
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc


@app.post("/v1/proposals/{proposal_id}/review")
def review_proposal(
    proposal_id: str,
    approve: bool,
    note: str | None = None,
    actor: ActorContext = Depends(require_permission("review.write")),
):
    try:
        return service.review_proposal(proposal_id, approve=approve, actor=actor.actor_id, note=note)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/v1/cases/{case_id}/resolve")
def resolve_case(
    case_id: str,
    evidence: ResolutionEvidence,
    actor: ActorContext = Depends(require_permission("review.write")),
):
    if evidence.case_id != case_id:
        raise HTTPException(400, "case id mismatch")
    evidence.actor = actor.actor_id
    try:
        return service.resolve_case(evidence)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/v1/audit/events")
def audit_events(actor: ActorContext = Depends(require_permission("audit.read"))):
    return service.store.events()


@app.get("/v1/audit/nocturnal-export")
def nocturnal_export(actor: ActorContext = Depends(require_permission("audit.read"))):
    return [event_to_nocturnal_claim(event) for event in service.store.events()]
