from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.action_intents import ActionIntent, GateState, evaluate_wildfire_uas_intent


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a bounded wildfire UAS governance action intent.")
    parser.add_argument("intent", help="Path to an ActionIntent JSON file")
    parser.add_argument("--gates", help="Optional GateState JSON file; omitted means all execution gates remain false")
    args = parser.parse_args()

    intent = ActionIntent.model_validate_json(Path(args.intent).read_text(encoding="utf-8"))
    gates = GateState()
    if args.gates:
        gates = GateState.model_validate_json(Path(args.gates).read_text(encoding="utf-8"))
    result = evaluate_wildfire_uas_intent(intent, gates)
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
