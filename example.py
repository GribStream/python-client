"""Minimal GribStream client example.

Run from the repository root after setting GRIBSTREAM_API_KEY.
"""

from __future__ import annotations

import datetime as dt

from gribstream import GribStreamClient

from examples._utils import print_rows, require_api_key, sorted_rows


def main() -> None:
    require_api_key()

    start = dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc)
    end = dt.datetime(2026, 4, 4, 6, tzinfo=dt.timezone.utc)

    with GribStreamClient() as client:
        rows = client.timeseries(
            dataset="gfs",
            from_time=start,
            until_time=end,
            coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
            variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
            min_lead_time="0h",
            max_lead_time="24h",
        )

    print_rows(sorted_rows(rows, ["forecasted_time", "name"]), limit=5)


if __name__ == "__main__":
    main()
