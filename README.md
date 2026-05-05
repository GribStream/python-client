# GribStream Python Client

Small Python client and examples for the [GribStream API](https://gribstream.com/docs). The client targets the current v2 API contract: forecast queries, public catalog discovery, shared cross-dataset parameters, expressions, filters, grids, ensemble members, and CSV/JSON/NDJSON response formats.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For the Skew-T plotting example:

```bash
pip install -r requirements-examples.txt
```

## Authentication

Create an API token in the GribStream dashboard, then export it as `GRIBSTREAM_API_KEY`:

```bash
export GRIBSTREAM_API_KEY='YOUR_TOKEN_HERE'
```

Optional: set `GRIBSTREAM_BASE_URL` if you are targeting a non-default deployment. The client sends `Authorization: Bearer $GRIBSTREAM_API_KEY` for forecast query endpoints. Catalog endpoints are public, but using the same client initialization keeps examples consistent.

## Quickstart

```python
import datetime as dt
from client import GribStreamClient

with GribStreamClient() as client:
    df = client.timeseries(
        dataset="gfs",
        from_time=dt.datetime(2026, 4, 4, 0, tzinfo=dt.timezone.utc),
        until_time=dt.datetime(2026, 4, 4, 6, tzinfo=dt.timezone.utc),
        coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
        variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
        min_lead_time="0h",
        max_lead_time="24h",
    )

print(df.head())
```

Run the root example:

```bash
python example.py
```

The Skew-T example writes `skewtlogp.png` by default so it works in headless
shell sessions:

```bash
python skewtlogp.py --output out/skewt-houston.png
python skewtlogp.py --help
```

## API Surface

- `client.timeseries(...)`: calls `POST /api/v2/{dataset}/timeseries` for the best available value per valid time. Use this for dashboards, feature generation, and leakage-safe backtests.
- `client.runs(...)`: calls `POST /api/v2/{dataset}/runs` for every matching model run. Use this for forecast aging, run-to-run drift, and cycle comparisons.
- `client.history(...)` and `client.forecasts(...)`: compatibility aliases for `timeseries` and `runs`.
- `client.query(dataset, endpoint, payload, ...)`: sends a fully formed payload to `timeseries`, `runs`, or a legacy alias.
- Catalog helpers: `list_datasets`, `get_dataset`, `list_dataset_parameters`, `get_dataset_parameter`, `list_shared_parameters`, `get_shared_parameter`, and `resolve_shared_parameter`.

## Request Features

Forecast query helpers support the current v2 request fields:

- Time selection: `from_time`/`until_time`, `forecasted_from`/`forecasted_until`, or exact `times_list`.
- Backtesting: `as_of` on `timeseries` excludes runs newer than the cutoff.
- Lead-time filters: `min_lead_time`/`max_lead_time` are preferred; deprecated `min_horizon`/`max_horizon` remain available.
- Spatial selection: point `coordinates`, rectangular `grid`, or both.
- Data fields: exact selector `variables`, server-side `expressions`, boolean `filter`, and ensemble `members`.
- Response formats: CSV as a pandas DataFrame by default, `application/json` as Python objects, and `application/ndjson` as rows or a streaming iterator.

## Examples

All data-query examples read the token from `GRIBSTREAM_API_KEY`.

```bash
python examples/timeseries_dataframe.py
python examples/runs_forecast_aging.py
python examples/as_of_backtest.py
python examples/json_response.py
python examples/ensemble_members.py
python examples/shared_parameter_timeseries.py
python examples/multimodel_shared_compare.py
python examples/grid_filter.py
python examples/ndjson_stream.py
python examples/selector_lookup_to_query.py
python examples/payload_builder.py
python examples/catalog_discovery.py
python skewtlogp.py
```

`examples/catalog_discovery.py` and `examples/payload_builder.py` do not send authenticated data queries. The rest require `GRIBSTREAM_API_KEY`.

Example coverage:

- `timeseries_dataframe.py`: best-available valid-time query into pandas.
- `runs_forecast_aging.py`: every matching model run for forecast-aging analysis.
- `as_of_backtest.py`: leakage-safe historical query with an `as_of` cutoff.
- `json_response.py`: `application/json` instead of CSV/DataFrame.
- `ndjson_stream.py`: streaming newline-delimited JSON rows.
- `ensemble_members.py`: explicit member selection for ensemble datasets.
- `shared_parameter_timeseries.py`: resolve a normalized signal for one dataset.
- `multimodel_shared_compare.py`: compare one shared signal across datasets.
- `grid_filter.py`: grid query with server-side expressions and filters.
- `selector_lookup_to_query.py`: discover an exact selector and query with it.
- `payload_builder.py`: build a request body and curl command without sending it.
- `catalog_discovery.py`: public dataset and parameter catalog discovery.

## Shared Parameters

Use shared parameters when you want one logical signal mapped across datasets without hardcoding dataset-specific selectors.

```python
from client import GribStreamClient

with GribStreamClient() as client:
    wind = client.resolve_shared_parameter(
        "wind_speed_10m",
        dataset="ifsoper",
        alias="wind_mps",
    )
    df = client.timeseries(
        dataset="ifsoper",
        from_time="2026-04-04T00:00:00Z",
        until_time="2026-04-04T12:00:00Z",
        coordinates=[client.coordinate(51.5072, -0.1276, "London")],
        variables=wind["variables"],
        expressions=wind.get("expressions"),
    )
```

## Sources

This client was updated against GribStream's official public docs and OpenAPI contract:

- API docs: https://gribstream.com/docs
- Quickstart: https://gribstream.com/quickstart
- OpenAPI spec: https://gribstream.com/docs/openapi.yaml
- Catalog release notes: https://gribstream.com/blog/public-catalog-endpoints-now-available
