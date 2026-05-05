"""Discover an exact selector, then use it in a data query."""

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
        parameter = client.get_dataset_parameter("ifsoper", "2t")
        selector = parameter["variations"][0]["selector"]
        selector["alias"] = "temp_k"

        df = client.timeseries(
            dataset="ifsoper",
            from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            until_time=dt.datetime(2026, 4, 4, 12, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(51.5072, -0.1276, "London")],
            variables=[selector],
            min_lead_time="0h",
            max_lead_time="48h",
        )

    print(df.sort_values("forecasted_time").to_string(index=False))


if __name__ == "__main__":
    main()
