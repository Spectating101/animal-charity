from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.disaster_safety import assess_disaster_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess a bounded disaster-response snapshot.")
    parser.add_argument("path", help="Path to a DisasterSnapshot JSON file")
    args = parser.parse_args()

    payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
    assessment = assess_disaster_payload(payload)
    print(json.dumps(assessment.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
