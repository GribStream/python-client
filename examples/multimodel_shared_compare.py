"""Compare one shared parameter across multiple datasets."""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client import GribStreamClient


def main() -> None:
    if not os.getenv("GRIBSTREAM_API_KEY"):
        raise SystemExit("Set GRIBSTREAM_API_KEY before running this example.")

    frames = []
    with GribStreamClient() as client:
        for dataset in ["gfs", "ifsoper"]:
            temp = client.resolve_shared_parameter("temperature_2m", dataset=dataset, alias="temp_k")
            df = client.timeseries(
                dataset=dataset,
                from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
                until_time=dt.datetime(2026, 4, 4, 12, tzinfo=dt.timezone.utc),
                coordinates=[client.coordinate(51.5072, -0.1276, "London")],
                variables=temp["variables"],
                expressions=temp.get("expressions"),
                min_lead_time="0h",
                max_lead_time="48h",
            )
            df["dataset"] = dataset
            df["temp_c"] = df["temp_k"] - 273.15
            frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    print(combined[["dataset", "forecasted_at", "forecasted_time", "name", "temp_c"]].to_string(index=False))


if __name__ == "__main__":
    main()
