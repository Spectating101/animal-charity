from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.mbg_case_study import assess_mbg_case, dump_mbg_assessment, load_mbg_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assess an MBG public-good case without promoting anomalies to corruption findings."
    )
    parser.add_argument("snapshot", help="Path to MBGCaseSnapshot JSON")
    args = parser.parse_args()
    print(dump_mbg_assessment(assess_mbg_case(load_mbg_snapshot(args.snapshot))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
