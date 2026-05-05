"""Request application/json instead of default CSV rows."""

from __future__ import annotations

import datetime as dt
import json

from gribstream import JSON, GribStreamClient

from _utils import require_api_key


def main() -> None:
    require_api_key()

    with GribStreamClient() as client:
        rows = client.timeseries(
            dataset="gfs",
            from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
            until_time=dt.datetime(2026, 4, 4, 6, tzinfo=dt.timezone.utc),
            coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
            variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
            accept=JSON,
        )

    print(json.dumps(rows[:5], indent=2))


if __name__ == "__main__":
    main()
