# python-client

Python client library to interface with [GribStream](https://www.gribstream.com)

Leverage:
    - [The National Blend of Models (NBM)](https://vlab.noaa.gov/web/mdl/nbm)
    - [The Global Forecast System (GFS)](https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast)
    - [The Rapid Refresh (RAP)](https://www.nco.ncep.noaa.gov/pmb/products/rap/)

```python
from client import GribStreamClient
import datetime

with GribStreamClient(apikey=None) as client: # DEMO API token

print("Query all NBM weather forecasts for three parameters, over a three hour range, ten hours out, for three coordinates")
start = datetime.datetime.now(datetime.UTC)
df = client.forecasts(
    dataset='nbm',
    forecasted_from=datetime.datetime(year=2024, month=8, day=10, hour=0),
    forecasted_until=datetime.datetime(year=2024, month=8, day=10, hour=3),
    coordinates=[
        {"lat": 40.75, "lon": -73.98},
        {"lat": 29.75, "lon": -95.36},
        {"lat": 47.60, "lon": -122.33},
    ],
    variables=[
        {"name": "TMP", "level": "2 m above ground", "info": ""},
        {"name": "WIND", "level": "10 m above ground", "info": ""},
        {"name": "DPT", "level": "2 m above ground", "info": ""},
    ],
    min_horizon=1,
    max_horizon=10,
)
print(df.sort_values(['forecasted_time', 'lat', 'lon']).head(20).to_string(index=False))
print('response in:', datetime.datetime.now(datetime.UTC) - start)

print()

print("Query the best GFS historical data for two parameters, for a three day range, for three coordinates, as of the end of the second day")
start = datetime.datetime.now(datetime.UTC)
df = client.history(
    dataset='gfs',
    from_time=datetime.datetime(year=2022, month=8, day=10, hour=0),
    until_time=datetime.datetime(year=2022, month=8, day=13, hour=0),
    coordinates=[
        {"lat": 40.75, "lon": -73.98},
        {"lat": 29.75, "lon": -95.36},
        {"lat": 47.60, "lon": -122.33},
    ],
    variables=[
        {"name": "TMP", "level": "2 m above ground", "info": ""},
        {"name": "TMP", "level": "surface", "info": ""},
    ],
    # Time travel. Before as_of, forecasted_time is history, after it is the forecast at as_of
    as_of=datetime.datetime(year=2024, month=8, day=12, hour=0),
    min_horizon=0,
    max_horizon=264,
)
print(df.sort_values(['forecasted_time', 'lat', 'lon']).head(20).to_string(index=False))
print('response in:', datetime.datetime.now(datetime.UTC) - start)

print("done")
```

Output:
```
Warning, missing API token. Running in limited DEMO mode.
Query all NBM weather forecasts for three parameters, over a three hour range, ten hours out, for three coordinates
            forecasted_at           forecasted_time   lat     lon  DPT|2 m above ground|  TMP|2 m above ground|  WIND|10 m above ground|
2024-08-10 00:00:00+00:00 2024-08-10 01:00:00+00:00 29.75  -95.36                 297.27                 305.87                      2.0
2024-08-10 00:00:00+00:00 2024-08-10 01:00:00+00:00 40.75  -73.98                 295.27                 296.27                     11.6
2024-08-10 00:00:00+00:00 2024-08-10 01:00:00+00:00 47.60 -122.33                 289.27                 298.67                      2.0
2024-08-10 01:00:00+00:00 2024-08-10 02:00:00+00:00 29.75  -95.36                 297.72                 304.90                      1.6
2024-08-10 00:00:00+00:00 2024-08-10 02:00:00+00:00 29.75  -95.36                 297.75                 304.90                      1.6
2024-08-10 01:00:00+00:00 2024-08-10 02:00:00+00:00 40.75  -73.98                 295.32                 296.10                     11.2
2024-08-10 00:00:00+00:00 2024-08-10 02:00:00+00:00 40.75  -73.98                 295.35                 296.10                     11.2
2024-08-10 01:00:00+00:00 2024-08-10 02:00:00+00:00 47.60 -122.33                 289.72                 296.50                      1.6
2024-08-10 00:00:00+00:00 2024-08-10 02:00:00+00:00 47.60 -122.33                 289.35                 296.50                      1.6
2024-08-10 02:00:00+00:00 2024-08-10 03:00:00+00:00 29.75  -95.36                 297.47                 304.05                      1.6
2024-08-10 00:00:00+00:00 2024-08-10 03:00:00+00:00 29.75  -95.36                 297.82                 304.23                      1.2
2024-08-10 01:00:00+00:00 2024-08-10 03:00:00+00:00 29.75  -95.36                 298.01                 304.23                      1.6
2024-08-10 02:00:00+00:00 2024-08-10 03:00:00+00:00 40.75  -73.98                 295.07                 295.65                     10.4
2024-08-10 00:00:00+00:00 2024-08-10 03:00:00+00:00 40.75  -73.98                 295.42                 295.83                     10.4
2024-08-10 01:00:00+00:00 2024-08-10 03:00:00+00:00 40.75  -73.98                 295.21                 295.83                     10.4
2024-08-10 02:00:00+00:00 2024-08-10 03:00:00+00:00 47.60 -122.33                 289.87                 294.85                      1.2
2024-08-10 00:00:00+00:00 2024-08-10 03:00:00+00:00 47.60 -122.33                 289.82                 295.03                      1.6
2024-08-10 01:00:00+00:00 2024-08-10 03:00:00+00:00 47.60 -122.33                 289.61                 294.63                      1.2
2024-08-10 02:00:00+00:00 2024-08-10 04:00:00+00:00 29.75  -95.36                 297.89                 303.52                      1.2
2024-08-10 00:00:00+00:00 2024-08-10 04:00:00+00:00 29.75  -95.36                 298.23                 303.53                      1.2
response in: 0:00:01.427238

Query the best GFS historical data for two parameters, for a three day range, for three coordinates, as of the end of the second day
            forecasted_at           forecasted_time   lat     lon  TMP|2 m above ground|  TMP|surface|
2022-08-10 00:00:00+00:00 2022-08-10 00:00:00+00:00 29.75  -95.36                 305.76        306.26
2022-08-10 00:00:00+00:00 2022-08-10 00:00:00+00:00 40.75  -73.98                 303.16        303.46
2022-08-10 00:00:00+00:00 2022-08-10 00:00:00+00:00 47.60 -122.33                 297.66        298.66
2022-08-10 00:00:00+00:00 2022-08-10 01:00:00+00:00 29.75  -95.36                 304.38        304.30
2022-08-10 00:00:00+00:00 2022-08-10 01:00:00+00:00 40.75  -73.98                 301.58        301.80
2022-08-10 00:00:00+00:00 2022-08-10 01:00:00+00:00 47.60 -122.33                 295.48        296.10
2022-08-10 00:00:00+00:00 2022-08-10 02:00:00+00:00 29.75  -95.36                 303.24        303.22
2022-08-10 00:00:00+00:00 2022-08-10 02:00:00+00:00 40.75  -73.98                 301.04        301.42
2022-08-10 00:00:00+00:00 2022-08-10 02:00:00+00:00 47.60 -122.33                 294.24        294.52
2022-08-10 00:00:00+00:00 2022-08-10 03:00:00+00:00 29.75  -95.36                 302.77        302.79
2022-08-10 00:00:00+00:00 2022-08-10 03:00:00+00:00 40.75  -73.98                 300.47        300.69
2022-08-10 00:00:00+00:00 2022-08-10 03:00:00+00:00 47.60 -122.33                 291.47        290.99
2022-08-10 00:00:00+00:00 2022-08-10 04:00:00+00:00 29.75  -95.36                 301.26        300.90
2022-08-10 00:00:00+00:00 2022-08-10 04:00:00+00:00 40.75  -73.98                 299.06        299.50
2022-08-10 00:00:00+00:00 2022-08-10 04:00:00+00:00 47.60 -122.33                 288.96        288.20
2022-08-10 00:00:00+00:00 2022-08-10 05:00:00+00:00 29.75  -95.36                 300.61        300.24
2022-08-10 00:00:00+00:00 2022-08-10 05:00:00+00:00 40.75  -73.98                 297.31        297.44
2022-08-10 00:00:00+00:00 2022-08-10 05:00:00+00:00 47.60 -122.33                 287.51        286.94
2022-08-10 06:00:00+00:00 2022-08-10 06:00:00+00:00 29.75  -95.36                 300.38        299.93
2022-08-10 06:00:00+00:00 2022-08-10 06:00:00+00:00 40.75  -73.98                 296.98        296.93
response in: 0:00:00.659955
done
```

GFS and RAP are suitable for SkewT LogP charts. Check the example.


If you liked GribStream please consider upvoting on ProductHunt [here](https://www.producthunt.com/posts/gribstream)
