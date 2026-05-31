#!/usr/bin/env python3
"""
Neon Citadel — headless test harness entry point.

Runs the full reference-model suite against the live Swift source. No third-party
dependencies; Python 3.10+ stdlib only.

    python3 run_tests.py            # run everything, normal verbosity
    python3 run_tests.py -v         # verbose (per-test names)

Exit code is non-zero if any test fails, so it's CI-friendly.
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # make `neon_sim` importable


def main() -> int:
    verbosity = 2 if "-v" in sys.argv else 1
    loader = unittest.TestLoader()
    suite = loader.discover(str(HERE / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
