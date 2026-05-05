"""Build and print a request payload without sending it."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client import GribStreamClient


def main() -> None:
    with GribStreamClient() as client:
        payload = client.build_timeseries_payload(
            from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            until_time=dt.datetime(2026, 4, 4, 6, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
            variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
            min_lead_time="0h",
            max_lead_time="24h",
        )

    print(json.dumps(payload, indent=2))
    print()
    print("curl -sS https://gribstream.com/api/v2/gfs/timeseries \\")
    print("  -H 'Authorization: Bearer $GRIBSTREAM_API_KEY' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -H 'Accept: text/csv' \\")
    print(f"  -d '{json.dumps(payload, separators=(',', ':'))}'")


if __name__ == "__main__":
    main()
