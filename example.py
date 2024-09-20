from client import GribStreamClient

baseurl = "http://gribstream.com/api/v1"

with GribStreamClient(baseurl) as client:
    
    # Non-streaming usage
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

    # Streaming usage
    # for chunk_df in client.forecasts(
    #     "2024-09-10T00:00:00Z",
    #     "2024-09-10T00:00:00Z",
    #     1,
    #     10,
    #     [
    #         {"lat": 40.75, "lon": -73.98},
    #         {"lat": 29.75, "lon": -95.36},
    #         {"lat": 47.60, "lon": -122.33},
    #     ],
    #     [
    #         {"name": "TMP", "level": "2 m above ground", "info": ""},
    #         {"name": "WIND", "level": "10 m above ground", "info": ""},
    #         {"name": "DPT", "level": "2 m above ground", "info": ""},
    #     ],
    #     stream=True,
    # ):
    #     print(chunk_df)

print("done")
