"""Fetch every matching model run for forecast-aging analysis."""

from __future__ import annotations

import datetime as dt

from gribstream import GribStreamClient

from _utils import print_rows, require_api_key, sorted_rows, with_lead_hours


def main() -> None:
    require_api_key()

    with GribStreamClient() as client:
        rows = client.runs(
            dataset="gfs",
            forecasted_from=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            forecasted_until=dt.datetime(2026, 4, 4, 6, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
            variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
            min_lead_time="0h",
            max_lead_time="18h",
        )

    print_rows(sorted_rows(with_lead_hours(rows), ["forecasted_at", "forecasted_time"]), limit=20)


if __name__ == "__main__":
    main()
