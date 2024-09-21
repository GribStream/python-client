from client import GribStreamClient
import datetime

with GribStreamClient() as client:
    
    # Non-streaming usage
    start = datetime.datetime.now(datetime.UTC)

    df = client.forecasts(
        forecasted_from="2024-09-10T00:00:00Z",
        forecasted_before="2024-09-10T00:00:00Z",
        min_horizon=1,
        max_horizon=10,
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
    )
    print(df)
    print('non streaming took', datetime.datetime.now(datetime.UTC) - start)

    # Streaming usage
    start = datetime.datetime.now(datetime.UTC)
    
    for chunk_df in client.forecasts(
        "2024-09-10T00:00:00Z",
        "2024-09-10T00:00:00Z",
        1,
        10,
        [
            {"lat": 40.75, "lon": -73.98},
            {"lat": 29.75, "lon": -95.36},
            {"lat": 47.60, "lon": -122.33},
        ],
        [
            {"name": "TMP", "level": "2 m above ground", "info": ""},
            {"name": "WIND", "level": "10 m above ground", "info": ""},
            {"name": "DPT", "level": "2 m above ground", "info": ""},
        ],
        stream=True,
        chunksize=20,
    ):
        print(chunk_df)
    print('streaming took', datetime.datetime.now(datetime.UTC) - start)

print("done")
