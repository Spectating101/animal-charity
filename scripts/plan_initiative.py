from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.structural_initiatives import dump_plan, load_structural_landscape, plan_structural_initiative


parser = argparse.ArgumentParser(description="Plan the smallest defensible structural public-good initiative for a welfare landscape.")
parser.add_argument("landscape", help="Path to a StructuralLandscape JSON file")
args = parser.parse_args()

landscape = load_structural_landscape(args.landscape)
print(dump_plan(plan_structural_initiative(landscape)))
