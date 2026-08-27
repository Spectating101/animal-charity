from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.public_good_control import assess_public_good_case, dump_public_good_assessment, load_public_good_case


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess a case through the registered public-good domain router.")
    parser.add_argument("case", help="Path to a PublicGoodCase JSON envelope")
    args = parser.parse_args()
    print(dump_public_good_assessment(assess_public_good_case(load_public_good_case(args.case))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
