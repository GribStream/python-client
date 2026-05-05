"""Stream newline-delimited JSON rows."""

from __future__ import annotations

import datetime as dt
import itertools

from gribstream import NDJSON, GribStreamClient

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
            accept=NDJSON,
            stream=True,
        )
        for row in itertools.islice(rows, 5):
            print(row)


if __name__ == "__main__":
    main()
