from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.disaster_control import DisasterSnapshot
from app.disaster_evolution import compare_operational_periods


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two disaster operational-period snapshots.")
    parser.add_argument("previous", help="Earlier DisasterSnapshot JSON")
    parser.add_argument("current", help="Later DisasterSnapshot JSON")
    args = parser.parse_args()

    previous = DisasterSnapshot.model_validate_json(Path(args.previous).read_text(encoding="utf-8"))
    current = DisasterSnapshot.model_validate_json(Path(args.current).read_text(encoding="utf-8"))
    result = compare_operational_periods(previous, current)
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
