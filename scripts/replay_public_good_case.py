from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.replay import ReplayPacket, run_replay, score_replay


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a hindsight-safe public-good historical replay.")
    parser.add_argument("packet", help="Path to ReplayPacket JSON")
    parser.add_argument("--score", action="store_true", help="Reveal the packet reference and score the primary stage")
    args = parser.parse_args()

    packet = ReplayPacket.model_validate_json(Path(args.packet).read_text(encoding="utf-8"))
    result = score_replay(packet) if args.score else run_replay(packet)
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
