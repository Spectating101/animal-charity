from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


VerificationStatus = Literal["reported", "corroborated", "verified"]
MatchStatus = Literal["qualified_candidate", "requires_verification", "blocked"]
ApplicationStatus = Literal["open", "closed", "not_public", "unknown"]


class CoordinationNeed(BaseModel):
    need_id: str
    kind: Literal["funding", "equipment", "expertise", "monitoring", "logistics", "partnership", "other"]
    priority: Literal["watch", "urgent", "critical"] = "watch"
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = None
    notes: str | None = None


class PublicGoodInitiative(BaseModel):
    initiative_id: str
    name: str
    actor_type: Literal["ngo", "community_group", "business", "social_enterprise", "government", "academic", "corporate", "other"]
    geographies: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    needs: list[CoordinationNeed] = Field(default_factory=list)
    source_ref: str
    verification_status: VerificationStatus = "reported"
    evidence_mode: Literal["observed", "synthetic_probe"] = "observed"
    notes: str | None = None

    @model_validator(mode="after")
    def unique_need_ids(self) -> "PublicGoodInitiative":
        ids = [need.need_id for need in self.needs]
        if len(ids) != len(set(ids)):
            raise ValueError("initiative need_id values must be unique")
        return self


class ResourceProgram(BaseModel):
    resource_id: str
    name: str
    provider: str
    resource_kind: Literal["grant", "csr", "impact_investment", "technical_assistance", "partnership", "in_kind", "other"]
    support_kinds: list[Literal["funding", "equipment", "expertise", "monitoring", "logistics", "partnership", "other"]] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    eligible_actor_types: list[str] = Field(default_factory=list)
    application_status: ApplicationStatus = "unknown"
    min_amount: float | None = Field(default=None, ge=0)
    max_amount: float | None = Field(default=None, gt=0)
    currency: str | None = None
    source_ref: str
    verification_status: VerificationStatus = "reported"
    notes: str | None = None

    @model_validator(mode="after")
    def amount_range_is_valid(self) -> "ResourceProgram":
        if self.min_amount is not None and self.max_amount is not None and self.min_amount > self.max_amount:
            raise ValueError("resource min_amount cannot exceed max_amount")
        return self


class CoordinationLandscape(BaseModel):
    landscape_id: str
    initiatives: list[PublicGoodInitiative] = Field(default_factory=list)
    resources: list[ResourceProgram] = Field(default_factory=list)

    @model_validator(mode="after")
    def ids_are_unique(self) -> "CoordinationLandscape":
        initiative_ids = [item.initiative_id for item in self.initiatives]
        resource_ids = [item.resource_id for item in self.resources]
        if len(initiative_ids) != len(set(initiative_ids)):
            raise ValueError("initiative_id values must be unique")
        if len(resource_ids) != len(set(resource_ids)):
            raise ValueError("resource_id values must be unique")
        return self


class CoordinationMatch(BaseModel):
    initiative_id: str
    need_id: str
    resource_id: str
    status: MatchStatus
    matched_dimensions: list[str] = Field(default_factory=list)
    unresolved_dimensions: list[str] = Field(default_factory=list)
    blocking_dimensions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class CoordinationFinding(BaseModel):
    initiative_id: str
    need_id: str
    resource_id: str
    stage: Literal["route", "evidence"]
    problem_class: str
    priority: Literal["watch", "urgent", "critical"]
    recommended_action: str
    evidence_refs: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
    human_authority_required: bool = True
    structural_candidate: bool = False


class CoordinationAssessment(BaseModel):
    landscape_id: str
    matches: list[CoordinationMatch] = Field(default_factory=list)
    findings: list[CoordinationFinding] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    safe_conclusion: str


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _strong(status: VerificationStatus) -> bool:
    return status in {"corroborated", "verified"}


def _overlap(left: list[str], right: list[str]) -> set[str]:
    return {item.casefold() for item in left}.intersection(item.casefold() for item in right)


def _evaluate(initiative: PublicGoodInitiative, need: CoordinationNeed, resource: ResourceProgram) -> CoordinationMatch:
    matched: list[str] = []
    unresolved: list[str] = []
    blocking: list[str] = []
    reasons: list[str] = []

    if need.kind in resource.support_kinds:
        matched.append("support_kind")
    else:
        blocking.append("support_kind")
        reasons.append(f"Resource does not establish support for need kind '{need.kind}'.")

    if initiative.themes and resource.themes:
        if _overlap(initiative.themes, resource.themes):
            matched.append("theme")
        else:
            blocking.append("theme")
            reasons.append("Initiative and resource themes do not overlap.")
    else:
        unresolved.append("theme")
        reasons.append("Theme coverage is incomplete and requires verification.")

    if resource.geographies:
        if _overlap(initiative.geographies, resource.geographies):
            matched.append("geography")
        else:
            blocking.append("geography")
            reasons.append("Initiative geography is outside the resource's stated geography.")
    else:
        unresolved.append("geography")
        reasons.append("Resource geography is not established.")

    if resource.eligible_actor_types:
        if initiative.actor_type in resource.eligible_actor_types:
            matched.append("actor_type")
        else:
            blocking.append("actor_type")
            reasons.append(f"Actor type '{initiative.actor_type}' is not in the stated eligible set.")
    else:
        unresolved.append("actor_type")
        reasons.append("Applicant/recipient actor eligibility is not established.")

    if need.amount is not None:
        if resource.currency and need.currency and resource.currency != need.currency:
            unresolved.append("amount_currency")
            reasons.append("Amount range cannot be compared without currency normalization.")
        elif resource.max_amount is not None and need.amount > resource.max_amount:
            blocking.append("amount")
            reasons.append("Requested amount exceeds the resource's stated maximum.")
        elif resource.min_amount is not None and need.amount < resource.min_amount:
            blocking.append("amount")
            reasons.append("Requested amount is below the resource's stated minimum.")
        elif resource.min_amount is not None or resource.max_amount is not None:
            matched.append("amount")
        else:
            unresolved.append("amount")
            reasons.append("Resource amount range is not established.")

    if resource.application_status == "closed":
        blocking.append("application_status")
        reasons.append("The evidenced call/program access path is closed; thematic fit does not make it currently actionable.")
    elif resource.application_status == "open":
        matched.append("application_status")
    elif resource.application_status == "not_public":
        unresolved.append("application_status")
        reasons.append("The program exists, but the source does not establish a public application path.")
    else:
        unresolved.append("application_status")
        reasons.append("Current application/access status is unknown.")

    if not _strong(initiative.verification_status):
        unresolved.append("initiative_verification")
        reasons.append("Initiative facts are only reported and need corroboration before consequential routing.")
    if not _strong(resource.verification_status):
        unresolved.append("resource_verification")
        reasons.append("Resource facts are only reported and need corroboration before consequential routing.")

    if blocking:
        status: MatchStatus = "blocked"
    elif unresolved:
        status = "requires_verification"
    else:
        status = "qualified_candidate"

    return CoordinationMatch(
        initiative_id=initiative.initiative_id,
        need_id=need.need_id,
        resource_id=resource.resource_id,
        status=status,
        matched_dimensions=_dedupe(matched),
        unresolved_dimensions=_dedupe(unresolved),
        blocking_dimensions=_dedupe(blocking),
        evidence_refs=_dedupe([initiative.source_ref, resource.source_ref]),
        reasons=reasons,
    )


def assess_coordination_landscape(landscape: CoordinationLandscape) -> CoordinationAssessment:
    matches: list[CoordinationMatch] = []
    findings: list[CoordinationFinding] = []
    data_gaps: list[str] = []

    for initiative in landscape.initiatives:
        for need in initiative.needs:
            for resource in landscape.resources:
                match = _evaluate(initiative, need, resource)
                matches.append(match)
                if match.status == "qualified_candidate":
                    findings.append(
                        CoordinationFinding(
                            initiative_id=initiative.initiative_id,
                            need_id=need.need_id,
                            resource_id=resource.resource_id,
                            stage="route",
                            problem_class="qualified_resource_match_candidate",
                            priority=need.priority,
                            recommended_action=(
                                "Route this evidence-backed candidate for human eligibility review and, if still valid, application/partnership preparation. "
                                "A qualified match is not an award, commitment, procurement decision, or authorization to submit automatically."
                            ),
                            evidence_refs=match.evidence_refs,
                            rationale=match.reasons or ["All represented matching dimensions are satisfied by sufficiently strong evidence."],
                        )
                    )
                elif match.status == "requires_verification":
                    findings.append(
                        CoordinationFinding(
                            initiative_id=initiative.initiative_id,
                            need_id=need.need_id,
                            resource_id=resource.resource_id,
                            stage="evidence",
                            problem_class="resource_match_requires_verification",
                            priority=need.priority,
                            recommended_action=(
                                "Verify the unresolved eligibility, availability, amount, geography, or evidence dimensions before treating this as an actionable funding/resource opportunity."
                            ),
                            evidence_refs=match.evidence_refs,
                            rationale=match.reasons,
                        )
                    )

    if not landscape.initiatives:
        data_gaps.append("No initiatives are represented in the coordination landscape.")
    if not landscape.resources:
        data_gaps.append("No funding/resource programs are represented in the coordination landscape.")

    qualified = sum(1 for item in matches if item.status == "qualified_candidate")
    verify = sum(1 for item in matches if item.status == "requires_verification")
    blocked = sum(1 for item in matches if item.status == "blocked")
    safe_conclusion = (
        f"Coordination assessment produced {qualified} qualified candidate(s), {verify} candidate(s) requiring verification, and {blocked} blocked pairing(s). "
        "Thematic similarity is never treated as proof of eligibility, current availability, application readiness, funding commitment, or intervention effectiveness."
    )
    return CoordinationAssessment(
        landscape_id=landscape.landscape_id,
        matches=matches,
        findings=findings,
        data_gaps=data_gaps,
        safe_conclusion=safe_conclusion,
    )
