from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.disaster_control import DisasterSnapshot
from app.disaster_evolution import compare_operational_periods


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two disaster operational-period snapshots.")
    parser.add_argument("previous", help="Earlier DisasterSnapshot JSON")
    parser.add_argument("current", help="Later DisasterSnapshot JSON")
    args = parser.parse_args()

    previous = DisasterSnapshot.model_validate_json(Path(args.previous).read_text(encoding="utf-8"))
    current = DisasterSnapshot.model_validate_json(Path(args.current).read_text(encoding="utf-8"))
    result = compare_operational_periods(previous, current)
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
