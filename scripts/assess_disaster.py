from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.disaster_control import DisasterSnapshot, assess_disaster


def main() -> None:
    parser = argparse.ArgumentParser(description="Assess a bounded disaster-response snapshot.")
    parser.add_argument("path", help="Path to a DisasterSnapshot JSON file")
    args = parser.parse_args()

    snapshot = DisasterSnapshot.model_validate_json(Path(args.path).read_text(encoding="utf-8"))
    assessment = assess_disaster(snapshot)
    print(json.dumps(assessment.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
