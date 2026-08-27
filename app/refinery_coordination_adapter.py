from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.coordination_control import (
    CoordinationAssessment,
    CoordinationLandscape,
    PublicGoodInitiative,
    ResourceProgram,
    assess_coordination_landscape,
)


class RefineryProjectionAuthority(BaseModel):
    semantic_admission: Literal["reviewed_fixture_only", "reviewed_registry"]
    evidence_maturity_change: Literal["none"] = "none"
    external_submission: bool = False
    funding_commitment: bool = False
    intervention_effectiveness: bool = False
    recommendation: bool = False

    @model_validator(mode="after")
    def consequential_authority_must_remain_false(self) -> "RefineryProjectionAuthority":
        if any(
            (
                self.external_submission,
                self.funding_commitment,
                self.intervention_effectiveness,
                self.recommendation,
            )
        ):
            raise ValueError("Refinery coordination projection cannot carry consequential decision authority")
        return self


class RefineryCoordinationProjection(BaseModel):
    schema_version: Literal["refinery.coordination-projection.v0"]
    landscape_id: str
    refinery_case_id: str
    refinery_schema_version: str
    as_of: datetime | None = None
    claim_boundary: str
    source_refs: list[str] = Field(default_factory=list)
    projection_authority: RefineryProjectionAuthority
    initiatives: list[PublicGoodInitiative] = Field(default_factory=list)
    resources: list[ResourceProgram] = Field(default_factory=list)

    @model_validator(mode="after")
    def assessment_time_is_valid(self) -> "RefineryCoordinationProjection":
        if self.as_of is not None and self.as_of.tzinfo is None:
            raise ValueError("Refinery coordination projection as_of must be timezone-aware")
        return self


class RefineryCoordinationBridgePacket(BaseModel):
    projection: RefineryCoordinationProjection
    declared_initiatives: list[PublicGoodInitiative] = Field(default_factory=list)

    @model_validator(mode="after")
    def initiative_ids_must_remain_unique(self) -> "RefineryCoordinationBridgePacket":
        ids = [item.initiative_id for item in self.projection.initiatives + self.declared_initiatives]
        if len(ids) != len(set(ids)):
            raise ValueError("Refinery-observed and declared initiative IDs must be unique")
        return self


class RefineryCoordinationBridgeAssessment(BaseModel):
    refinery_case_id: str
    refinery_source_count: int
    observed_initiative_count: int
    declared_initiative_count: int
    resource_count: int
    coordination: CoordinationAssessment
    bridge_boundary: str


def assess_refinery_coordination_bridge(
    packet: RefineryCoordinationBridgePacket,
) -> RefineryCoordinationBridgeAssessment:
    landscape = CoordinationLandscape(
        landscape_id=packet.projection.landscape_id,
        as_of=packet.projection.as_of,
        initiatives=packet.projection.initiatives + packet.declared_initiatives,
        resources=packet.projection.resources,
    )
    result = assess_coordination_landscape(landscape)
    return RefineryCoordinationBridgeAssessment(
        refinery_case_id=packet.projection.refinery_case_id,
        refinery_source_count=len(packet.projection.source_refs),
        observed_initiative_count=len(packet.projection.initiatives),
        declared_initiative_count=len(packet.declared_initiatives),
        resource_count=len(packet.projection.resources),
        coordination=result,
        bridge_boundary=(
            "Refinery contributes reviewed observations and a bounded coordination projection; declared project needs remain explicit inputs. "
            "The bridge cannot upgrade evidence maturity, invent need, submit applications, promise funding, establish intervention effectiveness, or recommend an intervention."
        ),
    )
