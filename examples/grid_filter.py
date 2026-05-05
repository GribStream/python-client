"""Search a small grid using server-side expressions and filters."""

from __future__ import annotations

import datetime as dt

from gribstream import GribStreamClient

from _utils import print_rows, require_api_key


def main() -> None:
    require_api_key()

    with GribStreamClient() as client:
        rows = client.timeseries(
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

    rows = sorted(rows, key=lambda row: float(row.get("storm_severity") or 0), reverse=True)
    print_rows(rows, limit=20)


if __name__ == "__main__":
    main()
