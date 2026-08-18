from __future__ import annotations

import os
import time
from pathlib import Path

from app.service import ReliefService

ROOT = Path(__file__).resolve().parents[1]
service = ReliefService(
    os.getenv("AFRN_DB_PATH", str(ROOT / "data" / "relief.db")),
    os.getenv("AFRN_RULEPACK", str(ROOT / "config" / "rulepacks" / "tw_dog_cat_pilot.json")),
    os.getenv("AFRN_MISSION", str(ROOT / "config" / "missions" / "animal_feed_security.json")),
)
interval = max(60, int(os.getenv("AFRN_AGENT_INTERVAL_SECONDS", "900")))
once = os.getenv("AFRN_AGENT_ONCE", "0") == "1"
actor = os.getenv("AFRN_AGENT_ACTOR", "public-welfare-agent:scheduler")

while True:
    print(service.agent_tick(actor=actor).model_dump_json())
    if once:
        break
    time.sleep(interval)
