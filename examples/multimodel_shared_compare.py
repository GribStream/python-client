"""Compare one shared parameter across multiple datasets."""

from __future__ import annotations

import datetime as dt

from gribstream import GribStreamClient

from _utils import print_rows, require_api_key, sorted_rows


def main() -> None:
    require_api_key()

    rows = []
    with GribStreamClient() as client:
        for dataset in ["gfs", "ifsoper"]:
            temp = client.resolve_shared_parameter("temperature_2m", dataset=dataset, alias="temp_k")
            dataset_rows = client.timeseries(
                dataset=dataset,
                from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
                until_time=dt.datetime(2026, 4, 4, 12, tzinfo=dt.timezone.utc),
                coordinates=[client.coordinate(51.5072, -0.1276, "London")],
                variables=temp["variables"],
                expressions=temp.get("expressions"),
                min_lead_time="0h",
                max_lead_time="48h",
            )
            for row in dataset_rows:
                copied = dict(row)
                copied["dataset"] = dataset
                copied["temp_c"] = round(float(copied["temp_k"]) - 273.15, 2)
                rows.append(copied)

    print_rows(
        sorted_rows(rows, ["forecasted_time", "dataset"]),
        ["dataset", "forecasted_at", "forecasted_time", "name", "temp_c"],
        limit=40,
    )


if __name__ == "__main__":
    main()
