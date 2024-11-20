from client import GribStreamClient
import datetime

with GribStreamClient(apikey=None) as client: # DEMO API token
    
    print("Query all weather forecasts for three parameters, over a three hour range, ten hours out, for three coordinates")
    start = datetime.datetime.now(datetime.UTC)
    df = client.forecasts(
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
    print(df.sort_values(['forecasted_time', 'lat', 'lon']).head(10).to_string(index=False))
    print('response in:', datetime.datetime.now(datetime.UTC) - start)

    print()

    print("Query the best historical data for three parameters, for a three day range, for three coordinates, as of the end of the second day")
    start = datetime.datetime.now(datetime.UTC)
    df = client.min_horizon(
        from_time=datetime.datetime(year=2024, month=8, day=10, hour=0),
        until_time=datetime.datetime(year=2024, month=8, day=13, hour=0),
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
        # Time travel. Before as_of, forecasted_time is history, after it is the forecast at as_of
        as_of=datetime.datetime(year=2024, month=8, day=12, hour=0),
        min_horizon=1,
        max_horizon=264,
    )
    print(df.sort_values(['forecasted_time', 'lat', 'lon']).head(10).to_string(index=False))
    print('response in:', datetime.datetime.now(datetime.UTC) - start)

print("done")
