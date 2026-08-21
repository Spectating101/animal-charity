from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.disaster_actuators import propose_wildfire_uas_intents
from app.disaster_control import DisasterSnapshot, assess_disaster


def main() -> None:
    parser = argparse.ArgumentParser(description="Propose bounded disaster actuator intents from an assessed incident snapshot.")
    parser.add_argument("snapshot", help="Path to DisasterSnapshot JSON")
    args = parser.parse_args()

    snapshot = DisasterSnapshot.model_validate_json(Path(args.snapshot).read_text(encoding="utf-8"))
    assessment = assess_disaster(snapshot)
    plan = propose_wildfire_uas_intents(snapshot, assessment)
    print(json.dumps(plan.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
