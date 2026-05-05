"""Resolve a shared parameter, then use its request fragment in a query."""

from __future__ import annotations

import datetime as dt

from gribstream import GribStreamClient

from _utils import print_rows, require_api_key, sorted_rows


def main() -> None:
    require_api_key()

    with GribStreamClient() as client:
        wind = client.resolve_shared_parameter("wind_speed_10m", dataset="ifsoper", alias="wind_mps")
        rows = client.timeseries(
            dataset="ifsoper",
            from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            until_time=dt.datetime(2026, 4, 4, 12, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(51.5072, -0.1276, "London")],
            variables=wind["variables"],
            expressions=wind.get("expressions"),
            min_lead_time="0h",
            max_lead_time="48h",
        )

    print_rows(sorted_rows(rows, ["forecasted_time"]), limit=12)


if __name__ == "__main__":
    main()
