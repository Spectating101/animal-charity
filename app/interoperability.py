from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.public_good_control import EvidenceManifestEntry


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationRole(str, Enum):
    evidence_source = "evidence_source"
    capability_registry = "capability_registry"
    integrity_standard = "integrity_standard"
    authority_framework = "authority_framework"
    operations_platform = "operations_platform"
    memory_archive = "memory_archive"


class ExternalRecordKind(str, Enum):
    hazard_observation = "hazard_observation"
    capability_resource = "capability_resource"
    service_presence = "service_presence"
    contracting_process = "contracting_process"
    command_context = "command_context"
    outcome_observation = "outcome_observation"


class ExternalRecord(BaseModel):
    record_id: str
    system_id: str
    integration_role: IntegrationRole
    kind: ExternalRecordKind
    source_ref: str
    source_kind: Literal[
        "official", "partner", "professional", "operator", "public", "transaction", "sensor", "synthetic", "other"
    ] = "other"
    observed_at: datetime
    ingested_at: datetime = Field(default_factory=utcnow)
    valid_until: datetime | None = None
    jurisdiction: str | None = None
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    sensitivity: Literal["public", "internal", "sensitive", "restricted"] = "internal"
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_boundaries(self) -> "ExternalRecord":
        allowed = {
            ExternalRecordKind.hazard_observation: {IntegrationRole.evidence_source},
            ExternalRecordKind.capability_resource: {
                IntegrationRole.capability_registry,
                IntegrationRole.operations_platform,
            },
            ExternalRecordKind.service_presence: {
                IntegrationRole.capability_registry,
                IntegrationRole.operations_platform,
            },
            ExternalRecordKind.contracting_process: {IntegrationRole.integrity_standard},
            ExternalRecordKind.command_context: {IntegrationRole.authority_framework},
            ExternalRecordKind.outcome_observation: {
                IntegrationRole.evidence_source,
                IntegrationRole.operations_platform,
                IntegrationRole.memory_archive,
            },
        }
        if self.integration_role not in allowed[self.kind]:
            raise ValueError(
                f"record kind {self.kind.value} cannot be supplied by role {self.integration_role.value}; "
                "keep evidence, capability, integrity, authority, execution and memory boundaries explicit"
            )
        for field_name, value in (
            ("observed_at", self.observed_at),
            ("ingested_at", self.ingested_at),
            ("valid_until", self.valid_until),
        ):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
        if self.valid_until is not None and self.valid_until < self.observed_at:
            raise ValueError("valid_until cannot precede observed_at")
        return self


class InteroperabilityBundle(BaseModel):
    bundle_id: str
    as_of: datetime
    records: list[ExternalRecord] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def record_ids_must_be_unique(self) -> "InteroperabilityBundle":
        ids = [record.record_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("interoperability record_id values must be unique")
        return self


class HazardSignal(BaseModel):
    record_id: str
    system_id: str
    hazard_type: str
    location_ref: str
    severity: str | None = None
    observed_at: datetime
    valid_until: datetime | None = None
    verification_status: str
    source_ref: str


class DeployableResource(BaseModel):
    record_id: str
    system_id: str
    resource_type: str
    capabilities: list[str] = Field(default_factory=list)
    quantity: float = 1.0
    unit: str = "unit"
    location_ref: str | None = None
    owner_ref: str | None = None
    availability: Literal["available", "committed", "unavailable", "unknown"] = "unknown"
    deployment_state: str | None = None
    verification_status: str
    source_ref: str


class ServicePresenceSignal(BaseModel):
    record_id: str
    system_id: str
    organization_ref: str
    service_type: str
    location_ref: str
    access_status: Literal["open", "constrained", "closed", "unknown"] = "unknown"
    capacity_status: Literal["spare", "normal", "constrained", "full", "unknown"] = "unknown"
    source_ref: str


class IntegrityProcessRef(BaseModel):
    record_id: str
    system_id: str
    ocid: str | None = None
    stage: str | None = None
    implementation_status: str | None = None
    source_ref: str


class CommandContextSignal(BaseModel):
    record_id: str
    system_id: str
    incident_id: str
    authority_ref: str
    operational_period: str | None = None
    objectives: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    source_ref: str


class ControlPlaneInteropPacket(BaseModel):
    bundle_id: str
    as_of: datetime
    hazards: list[HazardSignal] = Field(default_factory=list)
    deployable_resources: list[DeployableResource] = Field(default_factory=list)
    resource_candidates_requiring_verification: list[DeployableResource] = Field(default_factory=list)
    services: list[ServicePresenceSignal] = Field(default_factory=list)
    integrity_processes: list[IntegrityProcessRef] = Field(default_factory=list)
    command_contexts: list[CommandContextSignal] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    stale_record_ids: list[str] = Field(default_factory=list)
    restricted_source_refs: list[str] = Field(default_factory=list)
    evidence_manifest: list[EvidenceManifestEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    ownership_boundary: str = (
        "The public-good control plane owns diagnosis and bounded intervention reasoning. External systems retain "
        "their own sensing, registries, contracting semantics, command authority, execution and public-memory roles."
    )


def _fresh(record: ExternalRecord, as_of: datetime) -> bool:
    return record.valid_until is None or record.valid_until >= as_of


def _resource(record: ExternalRecord) -> DeployableResource:
    attrs = record.attributes
    return DeployableResource(
        record_id=record.record_id,
        system_id=record.system_id,
        resource_type=str(attrs.get("resource_type", "unknown")),
        capabilities=[str(value) for value in attrs.get("capabilities", [])],
        quantity=float(attrs.get("quantity", 1.0)),
        unit=str(attrs.get("unit", "unit")),
        location_ref=str(attrs["location_ref"]) if attrs.get("location_ref") is not None else None,
        owner_ref=str(attrs["owner_ref"]) if attrs.get("owner_ref") is not None else None,
        availability=attrs.get("availability", "unknown"),
        deployment_state=str(attrs["deployment_state"]) if attrs.get("deployment_state") is not None else None,
        verification_status=record.verification_status,
        source_ref=record.source_ref,
    )


def build_control_plane_packet(bundle: InteroperabilityBundle) -> ControlPlaneInteropPacket:
    if bundle.as_of.tzinfo is None:
        raise ValueError("bundle.as_of must be timezone-aware")

    hazards: list[HazardSignal] = []
    deployable_resources: list[DeployableResource] = []
    candidates: list[DeployableResource] = []
    services: list[ServicePresenceSignal] = []
    integrity: list[IntegrityProcessRef] = []
    command: list[CommandContextSignal] = []
    outcomes: list[str] = []
    stale: list[str] = []
    restricted: list[str] = []
    manifest_by_ref: dict[str, EvidenceManifestEntry] = {}
    warnings: list[str] = []

    for record in bundle.records:
        if record.sensitivity in {"sensitive", "restricted"}:
            restricted.append(record.source_ref)
        entry = EvidenceManifestEntry(
            source_ref=record.source_ref,
            source_kind=record.source_kind,
            verification_status=record.verification_status,
            sensitivity=record.sensitivity,
            observed_at=record.observed_at,
            content_sha256=record.content_sha256,
            notes=f"interop:{record.system_id}:{record.kind.value}",
        )
        if record.source_ref not in manifest_by_ref:
            manifest_by_ref[record.source_ref] = entry
        else:
            warnings.append(
                f"source_ref {record.source_ref} appears on multiple interoperability records; evidence manifest is deduplicated"
            )

        is_fresh = _fresh(record, bundle.as_of)
        if not is_fresh:
            stale.append(record.record_id)
            warnings.append(
                f"{record.record_id} is stale at bundle as_of and must not be treated as current operational state"
            )

        attrs = record.attributes
        if record.kind == ExternalRecordKind.hazard_observation:
            if is_fresh:
                hazards.append(
                    HazardSignal(
                        record_id=record.record_id,
                        system_id=record.system_id,
                        hazard_type=str(attrs.get("hazard_type", "unknown")),
                        location_ref=str(attrs.get("location_ref", "unknown")),
                        severity=str(attrs["severity"]) if attrs.get("severity") is not None else None,
                        observed_at=record.observed_at,
                        valid_until=record.valid_until,
                        verification_status=record.verification_status,
                        source_ref=record.source_ref,
                    )
                )
            else:
                warnings.append("stale hazard evidence may support history but cannot establish current hazard state")

        elif record.kind == ExternalRecordKind.capability_resource:
            resource = _resource(record)
            verified_enough = record.verification_status in {"corroborated", "verified"}
            if is_fresh and resource.availability == "available" and verified_enough:
                deployable_resources.append(resource)
            elif is_fresh and resource.availability == "available":
                candidates.append(resource)
                warnings.append(
                    f"{record.record_id} is reportedly available but requires verification before operational routing"
                )

        elif record.kind == ExternalRecordKind.service_presence:
            if is_fresh:
                services.append(
                    ServicePresenceSignal(
                        record_id=record.record_id,
                        system_id=record.system_id,
                        organization_ref=str(attrs.get("organization_ref", "unknown")),
                        service_type=str(attrs.get("service_type", "unknown")),
                        location_ref=str(attrs.get("location_ref", "unknown")),
                        access_status=attrs.get("access_status", "unknown"),
                        capacity_status=attrs.get("capacity_status", "unknown"),
                        source_ref=record.source_ref,
                    )
                )
            else:
                warnings.append("stale service-presence evidence cannot establish current access or capacity")

        elif record.kind == ExternalRecordKind.contracting_process:
            integrity.append(
                IntegrityProcessRef(
                    record_id=record.record_id,
                    system_id=record.system_id,
                    ocid=str(attrs["ocid"]) if attrs.get("ocid") is not None else None,
                    stage=str(attrs["stage"]) if attrs.get("stage") is not None else None,
                    implementation_status=(
                        str(attrs["implementation_status"]) if attrs.get("implementation_status") is not None else None
                    ),
                    source_ref=record.source_ref,
                )
            )
            warnings.append(
                f"{record.record_id} is contracting/integrity evidence only; it cannot by itself establish corruption or culpability"
            )

        elif record.kind == ExternalRecordKind.command_context:
            if is_fresh:
                command.append(
                    CommandContextSignal(
                        record_id=record.record_id,
                        system_id=record.system_id,
                        incident_id=str(attrs.get("incident_id", "unknown")),
                        authority_ref=str(attrs.get("authority_ref", "unknown")),
                        operational_period=(
                            str(attrs["operational_period"]) if attrs.get("operational_period") is not None else None
                        ),
                        objectives=[str(value) for value in attrs.get("objectives", [])],
                        constraints=[str(value) for value in attrs.get("constraints", [])],
                        source_ref=record.source_ref,
                    )
                )
            else:
                warnings.append("stale command context cannot establish current operational authority")

        elif record.kind == ExternalRecordKind.outcome_observation:
            outcomes.append(record.source_ref)

    if not command:
        warnings.append(
            "No current command/authority context supplied: recommendations may be analyzed, but no consequential action should be treated as authorized"
        )

    if not hazards and not services and not integrity and not outcomes:
        warnings.append("Bundle contains capability/authority data but no current condition or outcome evidence")

    return ControlPlaneInteropPacket(
        bundle_id=bundle.bundle_id,
        as_of=bundle.as_of,
        hazards=hazards,
        deployable_resources=deployable_resources,
        resource_candidates_requiring_verification=candidates,
        services=services,
        integrity_processes=integrity,
        command_contexts=command,
        outcome_refs=outcomes,
        stale_record_ids=sorted(set(stale)),
        restricted_source_refs=sorted(set(restricted)),
        evidence_manifest=list(manifest_by_ref.values()),
        warnings=warnings,
    )
