from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.replay import ReplayPacket, run_replay, score_replay


class ReplayCorpusCaseSpec(BaseModel):
    case_id: str
    packet_path: str
    evidence_level: Literal["R0", "R1", "R2"]
    required_problem_classes: list[str] = Field(default_factory=list)
    forbidden_problem_classes: list[str] = Field(default_factory=list)
    forbidden_stages: list[str] = Field(default_factory=list)
    max_resource_reservations: int | None = Field(default=None, ge=0)
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
    problem_classes: list[str]
    stages: list[str]
    resource_reservation_count: int
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
        problem_classes = [finding.problem_class for finding in findings]
        stages = [finding.stage for finding in findings]
        reservations = run.assessment.domain_result.get("proposed_reservations", [])
        reservation_count = len(reservations) if isinstance(reservations, list) else 0
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

        if (
            case_spec.max_resource_reservations is not None
            and reservation_count > case_spec.max_resource_reservations
        ):
            violations.append(
                f"resource reservations {reservation_count} exceed maximum {case_spec.max_resource_reservations}"
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
                problem_classes=problem_classes,
                stages=stages,
                resource_reservation_count=reservation_count,
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
