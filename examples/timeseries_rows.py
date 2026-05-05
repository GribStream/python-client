"""Fetch best-available values as CSV rows using only stdlib parsing."""

from __future__ import annotations

import datetime as dt

from gribstream import GribStreamClient

from _utils import print_rows, require_api_key, sorted_rows


def main() -> None:
    require_api_key()

    with GribStreamClient() as client:
        rows = client.timeseries(
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

    print_rows(sorted_rows(rows, ["forecasted_time", "name"]), limit=12)


if __name__ == "__main__":
    main()
