"""Generate the shared XLSX test-import sample file.

Writes ``samples/test_import_sample.xlsx`` next to the backend, using the same
generator the API serves from ``GET /api/v1/tests/import/template`` so the
committed sample and the downloaded template never drift apart.

Usage (from the ``backend/`` directory):

    .venv/bin/python scripts/generate_test_import_sample.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the project root importable regardless of the invocation directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.test_import_service import build_test_import_template  # noqa: E402

OUTPUT = PROJECT_ROOT / "samples" / "test_import_sample.xlsx"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(build_test_import_template())
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
