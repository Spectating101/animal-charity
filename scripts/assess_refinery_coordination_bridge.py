from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.refinery_coordination_adapter import (
    RefineryCoordinationBridgePacket,
    assess_refinery_coordination_bridge,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess a bounded Refinery coordination projection plus explicit initiative needs.")
    parser.add_argument("packet")
    args = parser.parse_args()
    payload = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    packet = RefineryCoordinationBridgePacket.model_validate(payload)
    result = assess_refinery_coordination_bridge(packet)
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
