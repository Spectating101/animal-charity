from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.domain import (
    AgentTickResult,
    AnimalGroup,
    Event,
    InventoryLot,
    MatchProposal,
    NeedCase,
    Recipient,
    ResolutionEvidence,
    ReviewState,
    SupplyBatch,
)
from app.engine import need_case_for_group, propose_match
from app.mission import MissionPolicy
from app.rules import RulePack
from app.store import Store


KINDS = {
    Recipient: ("recipient", "recipient_id"),
    AnimalGroup: ("group", "group_id"),
    InventoryLot: ("inventory", "inventory_id"),
    SupplyBatch: ("supply", "batch_id"),
    NeedCase: ("case", "case_id"),
    MatchProposal: ("proposal", "proposal_id"),
}


class ReliefService:
    def __init__(self, db_path: str, rulepack_path: str | Path, mission_path: str | Path | None = None):
        self.store = Store(db_path)
        self.rules = RulePack.load(rulepack_path)
        mission_path = mission_path or Path(rulepack_path).parents[1] / "missions" / "animal_feed_security.json"
        self.mission = MissionPolicy.load(mission_path)

    def save(self, obj, *, actor: str, event_type: str, source_ref: str | None = None):
        kind, id_field = KINDS[type(obj)]
        obj_id = getattr(obj, id_field)
        event = Event(
            event_type=event_type,
            subject_type=kind,
            subject_id=obj_id,
            actor=actor,
            source_ref=source_ref,
            payload=obj.model_dump(mode="json"),
        )
        self.store.put_with_event(kind, obj, id_field=id_field, event=event)
        return obj

    def list_model(self, kind: str, model):
        return [model.model_validate(x) for x in self.store.list(kind)]

    def get_model(self, kind: str, obj_id: str, model):
        raw = self.store.get(kind, obj_id)
        return model.model_validate(raw) if raw else None

    def review_recipient(
        self,
        recipient_id: str,
        *,
        approve: bool,
        actor: str,
        review_ref: str,
        emergency_only: bool = False,
    ) -> Recipient:
        self.mission.require_human("approve_recipient")
        recipient = self.get_model("recipient", recipient_id, Recipient)
        if not recipient:
            raise KeyError("recipient_not_found")
        recipient.welfare_review_ref = review_ref
        if approve:
            recipient.status = "emergency_only" if emergency_only else "active"
            event_type = "recipient.emergency_only" if emergency_only else "recipient.approved"
        else:
            recipient.status = "suspended"
            event_type = "recipient.rejected"
        return self.save(recipient, actor=actor, event_type=event_type, source_ref=review_ref)

    def agent_tick(self, *, actor: str = "welfare-agent", horizon_days: float = 7, target_buffer_days: float = 14) -> AgentTickResult:
        """Run one bounded autonomous welfare cycle.

        Autonomous permissions: observe, forecast, open/update cases, propose, escalate.
        Forbidden here: recipient/diet approval, match approval, dispatch, resolution.
        """
        for action in ("observe", "forecast", "open_case", "propose_match", "escalate"):
            self.mission.require_autonomous(action)

        ok, _, bad = self.store.verify_ledger()
        if not ok:
            raise RuntimeError(f"audit_integrity_failure:{bad}")

        result = AgentTickResult()
        groups = self.list_model("group", AnimalGroup)
        inventory = self.list_model("inventory", InventoryLot)
        recipients = {x.recipient_id: x for x in self.list_model("recipient", Recipient)}
        supplies = self.list_model("supply", SupplyBatch)
        existing_cases = self.list_model("case", NeedCase)
        proposals = self.list_model("proposal", MatchProposal)
        now = datetime.now(timezone.utc)

        open_by_group = {c.group_id: c for c in existing_cases if c.status in {"open", "proposal_ready", "approved"}}
        resolved_case_ids = {c.case_id for c in existing_cases if c.status == "resolved"}
        proposal_keys = {(p.case_id, p.batch_id) for p in proposals if p.review_state != ReviewState.rejected and p.case_id not in resolved_case_ids}
        reserved_by_batch: dict[str, float] = {}
        for p in proposals:
            if p.review_state != ReviewState.rejected and p.case_id not in resolved_case_ids:
                reserved_by_batch[p.batch_id] = reserved_by_batch.get(p.batch_id, 0.0) + p.proposed_kg

        for group in groups:
            computed = need_case_for_group(
                group=group,
                inventory=inventory,
                horizon_days=horizon_days,
                target_buffer_days=target_buffer_days,
                now=now,
            )
            if not computed:
                continue
            case = open_by_group.get(group.group_id)
            if case is None:
                case = self.save(computed, actor=actor, event_type="need_case.opened", source_ref=group.source_ref)
                result.opened_cases.append(case.case_id)
                open_by_group[group.group_id] = case

            recipient = recipients.get(group.recipient_id)
            if not recipient:
                msg = f"{case.case_id}:recipient_missing"
                result.escalations.append(msg)
                self.store.append_event(Event(event_type="need_case.escalated", subject_type="case", subject_id=case.case_id, actor=actor, payload={"reason": "recipient_missing"}))
                continue

            ranked: list[MatchProposal] = []
            for batch in supplies:
                if (case.case_id, batch.batch_id) in proposal_keys:
                    continue
                available = max(0.0, batch.quantity_kg - reserved_by_batch.get(batch.batch_id, 0.0))
                if available <= 0:
                    continue
                candidate = batch.model_copy(update={"quantity_kg": available})
                proposal = propose_match(case=case, recipient=recipient, group=group, batch=candidate, rules=self.rules, now=now)
                if proposal:
                    ranked.append(proposal)
            ranked.sort(key=lambda p: p.score, reverse=True)
            if ranked:
                top = self.save(ranked[0], actor=actor, event_type="match.proposed", source_ref=recipient.source_ref)
                proposal_keys.add((top.case_id, top.batch_id))
                reserved_by_batch[top.batch_id] = reserved_by_batch.get(top.batch_id, 0.0) + top.proposed_kg
                result.proposals_created.append(top.proposal_id)
                case.status = "proposal_ready"
                self.save(case, actor=actor, event_type="need_case.proposal_ready")
            elif not any(p.case_id == case.case_id and p.review_state != ReviewState.rejected for p in proposals):
                msg = f"{case.case_id}:no_eligible_supply"
                result.escalations.append(msg)
                self.store.append_event(Event(event_type="need_case.escalated", subject_type="case", subject_id=case.case_id, actor=actor, payload={"reason": "no_eligible_supply"}))

        if not (result.opened_cases or result.proposals_created or result.escalations):
            result.notes.append("no_action_required")
        return result

    def review_proposal(self, proposal_id: str, *, approve: bool, actor: str, note: str | None = None) -> MatchProposal:
        self.mission.require_human("approve_match")
        proposal = self.get_model("proposal", proposal_id, MatchProposal)
        if not proposal:
            raise KeyError("proposal_not_found")
        proposal.review_state = ReviewState.approved if approve else ReviewState.rejected
        self.save(proposal, actor=actor, event_type="match.approved" if approve else "match.rejected")
        case = self.get_model("case", proposal.case_id, NeedCase)
        if case and approve:
            case.status = "approved"
            self.save(case, actor=actor, event_type="need_case.approved")
        if note:
            self.store.append_event(Event(event_type="review.note", subject_type="proposal", subject_id=proposal_id, actor=actor, payload={"note": note}))
        return proposal

    def resolve_case(self, evidence: ResolutionEvidence) -> NeedCase:
        self.mission.require_human("resolve_case")
        case = self.get_model("case", evidence.case_id, NeedCase)
        if not case:
            raise KeyError("case_not_found")
        if case.status != "approved":
            raise ValueError("case_must_be_approved_before_resolution")
        proposals = [p for p in self.list_model("proposal", MatchProposal) if p.case_id == case.case_id and p.review_state == ReviewState.approved]
        if not proposals:
            raise ValueError("approved_proposal_required")
        proposal = proposals[-1]
        batch = self.get_model("supply", proposal.batch_id, SupplyBatch)
        group = self.get_model("group", case.group_id, AnimalGroup)
        if not batch or not group:
            raise ValueError("resolution_dependencies_missing")
        if evidence.delivered_kg > proposal.proposed_kg + 1e-9:
            raise ValueError("delivered_quantity_exceeds_approved_proposal")
        if evidence.delivered_kg > batch.quantity_kg + 1e-9:
            raise ValueError("delivered_quantity_exceeds_batch_balance")

        batch.quantity_kg = round(batch.quantity_kg - evidence.delivered_kg, 6)
        received = InventoryLot(
            recipient_id=case.recipient_id,
            group_id=case.group_id,
            product_name=batch.product_name,
            quantity_kg=evidence.delivered_kg,
            diet_class=batch.diet_class,
            expires_at=batch.expires_at,
            source_ref=evidence.evidence_ref,
        )
        animal_days = round((evidence.delivered_kg / group.daily_feed_kg) * group.count, 3)
        case.status = "resolved"
        payload = evidence.model_dump(mode="json") | {"animal_days_supported": animal_days, "batch_id": batch.batch_id, "proposal_id": proposal.proposal_id}

        self.store.put_many_with_events(
            [
                (
                    "supply", batch, "batch_id",
                    Event(event_type="supply.consumed", subject_type="supply", subject_id=batch.batch_id, actor=evidence.actor, source_ref=evidence.evidence_ref, payload=batch.model_dump(mode="json")),
                ),
                (
                    "inventory", received, "inventory_id",
                    Event(event_type="inventory.received", subject_type="inventory", subject_id=received.inventory_id, actor=evidence.actor, source_ref=evidence.evidence_ref, payload=received.model_dump(mode="json")),
                ),
                (
                    "case", case, "case_id",
                    Event(event_type="need_case.resolved", subject_type="case", subject_id=case.case_id, actor=evidence.actor, source_ref=evidence.evidence_ref, payload=case.model_dump(mode="json")),
                ),
            ],
            extra_events=[
                Event(event_type="delivery.confirmed", subject_type="case", subject_id=case.case_id, actor=evidence.actor, source_ref=evidence.evidence_ref, payload=payload)
            ],
        )
        return case

    def impact_summary(self) -> dict[str, float | int]:
        delivery_events = [e for e in self.store.events() if e["event_type"] == "delivery.confirmed"]
        return {
            "verified_deliveries": len(delivery_events),
            "verified_animal_days_supported": round(sum(float(e["payload"].get("animal_days_supported", 0)) for e in delivery_events), 3),
        }
