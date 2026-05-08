# GribStream Python Client

<p align="center">
  <img src="https://gribstream.com/home-hero-videoframe-166.webp" alt="GribStream weather forecast visualization" width="760">
</p>

A lightweight Python client for the [GribStream API](https://gribstream.com/docs). Use it to pull forecast data from models like GFS, HRRR, IFS, GEFS, NBM, and other datasets exposed by GribStream.

The client is intentionally small: core install depends only on `requests` and returns plain Python objects.

## What You Can Do

- Query best-available forecast values by valid time with `timeseries`.
- Query every matching model run with `runs` for forecast-aging or run-to-run analysis.
- Discover datasets and exact parameter selectors from the public catalog.
- Query points or grids.
- Use server-side expressions and filters.
- Request CSV rows, JSON, or streaming NDJSON.
- Select ensemble members on ensemble datasets.

## Install

When published to PyPI:

```bash
pip install gribstream
```

From a source checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional plotting dependencies for the Skew-T example:

```bash
pip install -e '.[examples]'
```

## Authentication

Create an API token in the GribStream dashboard, then export it:

```bash
export GRIBSTREAM_API_KEY='YOUR_TOKEN_HERE'
```

The client sends that token as `Authorization: Bearer $GRIBSTREAM_API_KEY`. Public catalog endpoints do not require a token, but forecast query endpoints do.

Optional: set `GRIBSTREAM_BASE_URL` to target a non-default deployment.

## Quickstart

```python
from gribstream import GribStreamClient

with GribStreamClient() as client:
    rows = client.timeseries(
        dataset="gfs",
        from_time="2026-04-04T00:00:00Z",
        until_time="2026-04-04T06:00:00Z",
        coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
        variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
        min_lead_time="0h",
        max_lead_time="24h",
    )

for row in rows[:3]:
    print(row)
```

By default, CSV responses are parsed into `list[dict[str, str]]`. Column names come from your aliases when you provide them, such as `temp_k` above.

## Exact Selectors

GribStream selectors are exact dataset-defined tuples. Do not guess parameter levels or casing. Use the catalog helpers when you need to discover them:

```python
from gribstream import GribStreamClient

with GribStreamClient() as client:
    parameter = client.get_dataset_parameter("ifsoper", "2t")
    for variation in parameter["variations"]:
        print(variation["selector"])
```

You can copy a returned selector directly into a query:

```python
selector = parameter["variations"][0]["selector"]
selector["alias"] = "temp_k"

rows = client.timeseries(
    dataset="ifsoper",
    from_time="2026-04-04T00:00:00Z",
    until_time="2026-04-04T12:00:00Z",
    coordinates=[client.coordinate(51.5072, -0.1276, "London")],
    variables=[selector],
)
```

## Runs vs Timeseries

Use `timeseries` when you want the freshest available run for each valid time:

```python
rows = client.timeseries(
    dataset="gfs",
    from_time="2026-04-04T00:00:00Z",
    until_time="2026-04-04T06:00:00Z",
    coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
    variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
)
```

Use `runs` when you want every model run in a run-time window:

```python
rows = client.runs(
    dataset="gfs",
    forecasted_from="2026-04-04T00:00:00Z",
    forecasted_until="2026-04-04T06:00:00Z",
    coordinates=[client.coordinate(29.7604, -95.3698, "Houston")],
    variables=[client.variable("TMP", "2 m above ground", alias="temp_k")],
    min_lead_time="0h",
    max_lead_time="18h",
)
```

## Shared Parameters

Most single-model queries should use exact selectors. Shared parameters are useful when you are writing multi-model code and want one logical signal, such as `wind_speed_10m`, mapped to each dataset's native selectors.

```python
with GribStreamClient() as client:
    wind_request = client.resolve_shared_parameter(
        "wind_speed_10m",
        dataset="ifsoper",
        alias="wind_mps",
    )

    rows = client.timeseries(
        dataset="ifsoper",
        from_time="2026-04-04T00:00:00Z",
        until_time="2026-04-04T12:00:00Z",
        coordinates=[client.coordinate(51.5072, -0.1276, "London")],
        variables=wind_request["variables"],
        expressions=wind_request.get("expressions"),
    )
```

`resolve_shared_parameter` returns a request fragment containing `variables` and, when needed, `expressions`.

## Response Formats

Default CSV parsing:

```python
rows = client.timeseries(...)
```

JSON response:

```python
from gribstream import JSON

rows = client.timeseries(..., accept=JSON)
```

Streaming NDJSON response:

```python
from gribstream import NDJSON

for row in client.timeseries(..., accept=NDJSON, stream=True):
    print(row)
```

## Examples

The repository includes runnable examples. After installing from a source checkout with `pip install -e .`, run them directly:

```bash
python examples/timeseries_rows.py
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

The Skew-T example writes `skewtlogp.png` by default, so it works in terminal and headless environments:

```bash
python skewtlogp.py --output out/skewt-houston.png
```

## Links

- GribStream: https://gribstream.com
- API docs: https://gribstream.com/docs
- Quickstart: https://gribstream.com/quickstart
- OpenAPI spec: https://gribstream.com/docs/openapi.yaml
