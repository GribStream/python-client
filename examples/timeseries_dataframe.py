"""Fetch best-available values into a pandas DataFrame."""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client import GribStreamClient


def main() -> None:
    if not os.getenv("GRIBSTREAM_API_KEY"):
        raise SystemExit("Set GRIBSTREAM_API_KEY before running this example.")

    with GribStreamClient() as client:
        df = client.timeseries(
            dataset="gfs",
            from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            until_time=dt.datetime(2026, 4, 4, 6, tzinfo=dt.timezone.utc),
            coordinates=[
                client.coordinate(40.7128, -74.0060, "New York"),
                client.coordinate(29.7604, -95.3698, "Houston"),
            ],
            variables=[
                client.variable("TMP", "2 m above ground", alias="temp_k"),
                client.variable("DPT", "2 m above ground", alias="dewpoint_k"),
            ],
            min_lead_time="0h",
            max_lead_time="24h",
        )

    print(df.sort_values(["forecasted_time", "name"]).head(12).to_string(index=False))


if __name__ == "__main__":
    main()
