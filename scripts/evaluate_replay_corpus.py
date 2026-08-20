from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.replay_corpus import dump_corpus_result, evaluate_corpus, load_corpus


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a public-good historical replay corpus and fail if any benchmark contract is violated."
    )
    parser.add_argument("corpus", help="Path to a ReplayCorpusSpec JSON file")
    args = parser.parse_args()

    spec = load_corpus(args.corpus)
    result = evaluate_corpus(spec, ROOT)
    print(dump_corpus_result(result))
    return 1 if result.failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
