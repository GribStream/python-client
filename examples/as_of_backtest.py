"""Leakage-safe backtest query using timeseries.as_of."""

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
            from_time=dt.datetime(2026, 4, 4, 12, tzinfo=dt.timezone.utc),
            until_time=dt.datetime(2026, 4, 5, 0, tzinfo=dt.timezone.utc),
            as_of=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
            variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
            min_lead_time="0h",
            max_lead_time="48h",
        )

    df["lead_hours"] = (df["forecasted_time"] - df["forecasted_at"]).dt.total_seconds() / 3600
    print(df.sort_values("forecasted_time").to_string(index=False))


if __name__ == "__main__":
    main()
