
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.backup_common import (
    BackupError,
    verify_backup_directory,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify an ExceptionOps backup using its SHA-256 manifest."
    )

    parser.add_argument(
        "--backup-dir",
        type=Path,
        required=True,
        help="Path to a completed ExceptionOps backup directory.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    try:
        manifest = verify_backup_directory(
            args.backup_dir
        )

        print("BACKUP VERIFICATION PASSED")
        print(
            "Created at UTC: "
            f"{manifest['created_at_utc']}"
        )
        print(
            "Database archive size: "
            f"{manifest['database']['size_bytes']} bytes"
        )
        print(
            "Database SHA-256: "
            f"{manifest['database']['sha256']}"
        )
        print(
            "Document files verified: "
            f"{manifest['documents']['file_count']}"
        )
        print(
            "Document bytes verified: "
            f"{manifest['documents']['total_size_bytes']}"
        )

        return 0

    except (BackupError, OSError) as exc:
        print(
            f"BACKUP VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
