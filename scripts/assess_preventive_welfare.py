from __future__ import annotations

import sys

from app.preventive_welfare import (
    assess_preventive_system,
    dump_preventive_assessment,
    load_preventive_snapshot,
)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/assess_preventive_welfare.py <snapshot.json>")
    snapshot = load_preventive_snapshot(sys.argv[1])
    print(dump_preventive_assessment(assess_preventive_system(snapshot)))


if __name__ == "__main__":
    main()
