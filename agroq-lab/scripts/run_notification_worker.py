from __future__ import annotations

import argparse
import time

from app import get_db, init_db
from notification_center import (
    dispatch_pending_notifications,
    initialize_notification_schema,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dispatch AgroQ administrator notifications."
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=max, default=10)
    args = parser.parse_args()

    init_db()
    initialize_notification_schema(get_db)

    while True:
        result = dispatch_pending_notifications(get_db)
        print(
            f"notification worker: sent={result['sent']} "
            f"failed={result['failed']} skipped={result['skipped']}",
            flush=True,
        )
        if args.once:
            return 0
        time.sleep(max(5, int(args.interval)))


if __name__ == "__main__":
    raise SystemExit(main())
