from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.domain import AnimalGroup, InventoryLot, Recipient, SupplyBatch
from app.service import ReliefService

ROOT = Path(__file__).resolve().parents[1]
service = ReliefService(
    os.getenv("AFRN_DB_PATH", str(ROOT / "data" / "relief.db")),
    os.getenv("AFRN_RULEPACK", str(ROOT / "config" / "rulepacks" / "tw_dog_cat_pilot.json")),
    os.getenv("AFRN_MISSION", str(ROOT / "config" / "missions" / "animal_feed_security.json")),
)

recipient = service.save(
    Recipient(name="Demo Shelter A", region="Taoyuan", reliability=0.8, source_ref="demo://recipient"),
    actor="demo-seed",
    event_type="recipient.recorded",
    source_ref="demo://recipient",
)
group = service.save(
    AnimalGroup(recipient_id=recipient.recipient_id, species="dog", count=40, daily_feed_kg=12, source_ref="demo://weekly-inventory"),
    actor="demo-seed",
    event_type="animal_group.recorded",
)
service.save(
    InventoryLot(recipient_id=recipient.recipient_id, group_id=group.group_id, product_name="Existing Complete Feed", quantity_kg=24, source_ref="demo://weekly-inventory"),
    actor="demo-seed",
    event_type="inventory.observed",
)
service.save(
    SupplyBatch(
        donor_name="Demo Pet Food Distributor",
        product_name="Sealed Complete Dog Feed",
        quantity_kg=120,
        expires_at=datetime.now(timezone.utc) + timedelta(days=20),
        location="Taoyuan",
        species=["dog"],
        source_ref="demo://donor-lot",
        evidence_refs=["demo://label-photo"],
    ),
    actor="demo-seed",
    event_type="supply.observed",
)
print(service.agent_tick(actor="public-welfare-agent:demo"))
