"""Leakage-safe backtest query using timeseries.as_of."""

from __future__ import annotations

import datetime as dt

from gribstream import GribStreamClient

from _utils import print_rows, require_api_key, sorted_rows, with_lead_hours


def main() -> None:
    require_api_key()

    with GribStreamClient() as client:
        rows = client.timeseries(
            dataset="gfs",
            from_time=dt.datetime(2026, 4, 4, 12, tzinfo=dt.timezone.utc),
            until_time=dt.datetime(2026, 4, 5, 0, tzinfo=dt.timezone.utc),
            as_of=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
            variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
            min_lead_time="0h",
            max_lead_time="48h",
        )

    print_rows(sorted_rows(with_lead_hours(rows), ["forecasted_time"]), limit=30)


if __name__ == "__main__":
    main()
