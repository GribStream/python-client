"""Request application/json instead of the default CSV DataFrame."""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client import GribStreamClient, JSON


def main() -> None:
    if not os.getenv("GRIBSTREAM_API_KEY"):
        raise SystemExit("Set GRIBSTREAM_API_KEY before running this example.")

    with GribStreamClient() as client:
        rows = client.timeseries(
            dataset="gfs",
            from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            until_time=dt.datetime(2026, 4, 4, 6, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
            variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
            accept=JSON,
        )

    print(json.dumps(rows[:5], indent=2))


if __name__ == "__main__":
    main()
