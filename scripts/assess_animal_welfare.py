from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.animal_welfare_control import assess_area, dump_assessment, load_landscape


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess an animal-welfare landscape and route evidence-bounded lifecycle interventions.")
    parser.add_argument("landscape", help="Path to WelfareLandscape JSON")
    args = parser.parse_args()
    assessment = assess_area(load_landscape(args.landscape))
    print(dump_assessment(assessment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
