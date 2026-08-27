from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.welfare_landscape import assess_landscape, dump_assessment, load_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess a bounded welfare landscape from evidence + capability observations.")
    parser.add_argument("snapshot", help="Path to LandscapeSnapshot JSON")
    args = parser.parse_args()
    assessment = assess_landscape(load_snapshot(args.snapshot))
    print(dump_assessment(assessment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
