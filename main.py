"""
Unified entry point for the Ultimate Dispute Letter Generator.

This script invokes the existing workflow in extract_account_details.py.
It also provides a single place to extend CLI options in the future.
"""

from __future__ import annotations

import sys


def main() -> int:
	from extract_account_details import main as run
	run()
	return 0


if __name__ == "__main__":
	sys.exit(main())


