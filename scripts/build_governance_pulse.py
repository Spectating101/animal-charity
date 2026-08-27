from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.governance_pulse import GovernancePulseInput, build_governance_pulse


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/build_governance_pulse.py <pulse.json>")
    payload = GovernancePulseInput.model_validate_json(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = build_governance_pulse(payload)
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
