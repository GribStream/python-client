"""Query explicit ensemble members.

On ensemble datasets, omitting ``members`` returns only the first member. Pass
``members`` when you need a specific subset.
"""

from __future__ import annotations

import datetime as dt

from gribstream import GribStreamClient

from _utils import print_rows, require_api_key, sorted_rows


def main() -> None:
    require_api_key()

    with GribStreamClient() as client:
        rows = client.runs(
            dataset="gefsatmos",
            forecasted_from=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            forecasted_until=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(40.7128, -74.0060, "New York")],
            variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
            members=[0, 1, 2, 3],
            min_lead_time="0h",
            max_lead_time="24h",
        )

    print_rows(sorted_rows(rows, ["forecasted_time", "member"]), limit=40)


if __name__ == "__main__":
    main()
