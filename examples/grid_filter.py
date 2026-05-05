"""Search a small grid using server-side expressions and filters."""

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
            grid=client.grid(29.0, 31.0, -97.0, -94.0, 0.5),
            variables=[
                client.variable("CAPE", "180-0 mb above ground", info="", alias="cape"),
                client.variable("CIN", "180-0 mb above ground", info="", alias="cin"),
            ],
            expressions=[client.expression("cape + cin", alias="storm_severity")],
            filter=client.filter_expression("storm_severity >= 1200"),
            min_lead_time="0h",
            max_lead_time="24h",
        )

    print(df.sort_values("storm_severity", ascending=False).head(20).to_string(index=False))


if __name__ == "__main__":
    main()
