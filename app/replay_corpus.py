from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.replay import ReplayPacket, run_replay, score_replay


InventoryCoverage = Literal["complete_for_scope", "partial", "unknown"]


class ReplayCorpusCaseSpec(BaseModel):
    case_id: str
    packet_path: str
    evidence_level: Literal["R0", "R1", "R2"]
    required_problem_classes: list[str] = Field(default_factory=list)
    forbidden_problem_classes: list[str] = Field(default_factory=list)
    forbidden_stages: list[str] = Field(default_factory=list)
    required_data_gap_substrings: list[str] = Field(default_factory=list)
    max_findings: int | None = Field(default=None, ge=0)
    max_resource_reservations: int | None = Field(default=None, ge=0)
    expected_command_context_present: bool | None = None
    expected_resource_inventory_scope: InventoryCoverage | None = None
    expected_service_registry_scope: InventoryCoverage | None = None
    expected_structural_candidate: bool | None = None
    notes: list[str] = Field(default_factory=list)


class ReplayCorpusSpec(BaseModel):
    corpus_id: str
    cases: list[ReplayCorpusCaseSpec]


class ReplayCorpusCaseResult(BaseModel):
    case_id: str
    packet_path: str
    evidence_level: str
    domain: str
    predicted_primary_stage: str | None
    primary_stage_match: bool | None
    predicted_structural_candidate: bool
    finding_count: int
    problem_classes: list[str]
    stages: list[str]
    resource_reservation_count: int
    command_context_present: bool | None = None
    resource_inventory_scope: str | None = None
    service_registry_scope: str | None = None
    data_gaps: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    passed: bool


class ReplayCorpusResult(BaseModel):
    corpus_id: str
    case_count: int
    passed_count: int
    failed_count: int
    by_evidence_level: dict[str, int]
    results: list[ReplayCorpusCaseResult]


def load_corpus(path: str | Path) -> ReplayCorpusSpec:
    return ReplayCorpusSpec.model_validate_json(Path(path).read_text(encoding="utf-8"))


def evaluate_corpus(spec: ReplayCorpusSpec, root: str | Path) -> ReplayCorpusResult:
    root_path = Path(root)
    results: list[ReplayCorpusCaseResult] = []

    for case_spec in spec.cases:
        packet_file = root_path / case_spec.packet_path
        packet = ReplayPacket.model_validate_json(packet_file.read_text(encoding="utf-8"))
        run = run_replay(packet)
        score = score_replay(packet) if packet.reference is not None else None

        findings = run.assessment.normalized_findings
        finding_count = len(findings)
        problem_classes = [finding.problem_class for finding in findings]
        stages = [finding.stage for finding in findings]
        structural_candidate = (
            score.predicted_structural_candidate
            if score is not None
            else any(finding.structural_candidate for finding in findings)
        )
        domain_result = run.assessment.domain_result
        reservations = domain_result.get("proposed_reservations", [])
        reservation_count = len(reservations) if isinstance(reservations, list) else 0
        data_gaps = list(run.assessment.data_gaps)

        command_context = domain_result.get("command_context_present")
        command_context_present = command_context if isinstance(command_context, bool) else None
        interop = domain_result.get("interoperability")
        interop_dict = interop if isinstance(interop, dict) else {}
        resource_scope = interop_dict.get("resource_inventory_scope")
        service_scope = interop_dict.get("service_registry_scope")

        violations: list[str] = []

        if score is not None and score.primary_stage_match is False:
            violations.append(
                f"primary stage {score.predicted_primary_stage!r} did not match expected {score.expected_primary_stages!r}"
            )

        for required in case_spec.required_problem_classes:
            if required not in problem_classes:
                violations.append(f"required problem class missing: {required}")

        for forbidden in case_spec.forbidden_problem_classes:
            if forbidden in problem_classes:
                violations.append(f"forbidden problem class present: {forbidden}")

        for forbidden_stage in case_spec.forbidden_stages:
            if forbidden_stage in stages:
                violations.append(f"forbidden stage present: {forbidden_stage}")

        for required_gap in case_spec.required_data_gap_substrings:
            if not any(required_gap in gap for gap in data_gaps):
                violations.append(f"required data-gap text missing: {required_gap}")

        if case_spec.max_findings is not None and finding_count > case_spec.max_findings:
            violations.append(f"findings {finding_count} exceed maximum {case_spec.max_findings}")

        if (
            case_spec.max_resource_reservations is not None
            and reservation_count > case_spec.max_resource_reservations
        ):
            violations.append(
                f"resource reservations {reservation_count} exceed maximum {case_spec.max_resource_reservations}"
            )

        if (
            case_spec.expected_command_context_present is not None
            and command_context_present is not case_spec.expected_command_context_present
        ):
            violations.append(
                "command-context expectation mismatch: "
                f"expected {case_spec.expected_command_context_present}, got {command_context_present}"
            )

        if (
            case_spec.expected_resource_inventory_scope is not None
            and resource_scope != case_spec.expected_resource_inventory_scope
        ):
            violations.append(
                "resource-inventory scope mismatch: "
                f"expected {case_spec.expected_resource_inventory_scope!r}, got {resource_scope!r}"
            )

        if (
            case_spec.expected_service_registry_scope is not None
            and service_scope != case_spec.expected_service_registry_scope
        ):
            violations.append(
                "service-registry scope mismatch: "
                f"expected {case_spec.expected_service_registry_scope!r}, got {service_scope!r}"
            )

        if (
            case_spec.expected_structural_candidate is not None
            and structural_candidate is not case_spec.expected_structural_candidate
        ):
            violations.append(
                "structural-candidate expectation mismatch: "
                f"expected {case_spec.expected_structural_candidate}, got {structural_candidate}"
            )

        results.append(
            ReplayCorpusCaseResult(
                case_id=case_spec.case_id,
                packet_path=case_spec.packet_path,
                evidence_level=case_spec.evidence_level,
                domain=run.assessment.domain.value,
                predicted_primary_stage=score.predicted_primary_stage if score is not None else (
                    stages[0] if stages else None
                ),
                primary_stage_match=score.primary_stage_match if score is not None else None,
                predicted_structural_candidate=structural_candidate,
                finding_count=finding_count,
                problem_classes=problem_classes,
                stages=stages,
                resource_reservation_count=reservation_count,
                command_context_present=command_context_present,
                resource_inventory_scope=str(resource_scope) if resource_scope is not None else None,
                service_registry_scope=str(service_scope) if service_scope is not None else None,
                data_gaps=data_gaps,
                violations=violations,
                passed=not violations,
            )
        )

    counts = Counter(result.evidence_level for result in results)
    passed_count = sum(1 for result in results if result.passed)
    return ReplayCorpusResult(
        corpus_id=spec.corpus_id,
        case_count=len(results),
        passed_count=passed_count,
        failed_count=len(results) - passed_count,
        by_evidence_level=dict(sorted(counts.items())),
        results=results,
    )


def dump_corpus_result(result: ReplayCorpusResult) -> str:
    return json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False)
