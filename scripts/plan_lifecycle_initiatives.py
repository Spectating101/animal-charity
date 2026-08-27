from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.lifecycle_initiatives import LifecycleInitiativeLandscape, plan_lifecycle_initiatives


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan generic structural animal-welfare initiatives from repeated transition failures.")
    parser.add_argument("landscape")
    args = parser.parse_args()
    payload = Path(args.landscape).read_text(encoding="utf-8")
    landscape = LifecycleInitiativeLandscape.model_validate_json(payload)
    plans = plan_lifecycle_initiatives(landscape)
    print(json.dumps([p.model_dump(mode="json") for p in plans], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
