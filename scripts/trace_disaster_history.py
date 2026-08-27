from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.disaster_control import DisasterSnapshot
from app.disaster_evolution import trace_operational_history


def main() -> int:
    parser = argparse.ArgumentParser(description="Trace explicit disaster operational state across multiple snapshots.")
    parser.add_argument("snapshots", nargs="+", help="Ordered DisasterSnapshot JSON files")
    args = parser.parse_args()

    snapshots = [
        DisasterSnapshot.model_validate_json(Path(path).read_text(encoding="utf-8"))
        for path in args.snapshots
    ]
    result = trace_operational_history(snapshots)
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
