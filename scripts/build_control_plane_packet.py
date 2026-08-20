from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.interoperability import InteroperabilityBundle, build_control_plane_packet


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize external evidence/capability/authority records into a public-good control-plane packet."
    )
    parser.add_argument("bundle", help="Path to an InteroperabilityBundle JSON file")
    args = parser.parse_args()

    payload = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    bundle = InteroperabilityBundle.model_validate(payload)
    packet = build_control_plane_packet(bundle)
    print(json.dumps(packet.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
