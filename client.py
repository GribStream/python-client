import requests
import pandas as pd
import datetime
import io
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import gzip
import json

gribstream_base_url = "https://gribstream.com"
# gribstream_base_url = "http://localhost:3000"
gribstream_api_url = f"{gribstream_base_url}/api/v1"

class GribStreamClient:
    def __init__(self, apikey=None):

        if apikey is None:
            print('Warning, missing API token. Running in limited DEMO mode.')
            keyreq = requests.get(f'{gribstream_base_url}/auth/demo')
            keyreq.raise_for_status()
            apikey = keyreq.content
        self.apikey = apikey

        self.session = requests.Session()

        for h, v in {'Accept-Encoding': 'gzip', 'Content-Encoding': 'gzip', 'Content-Type': 'application/json', 'Authorization': self.apikey}.items():
            self.session.headers.setdefault(h, v)

        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def forecasts(self, forecasted_from, forecasted_until, coordinates, variables, min_horizon=1, max_horizon=1, stream=False, chunksize=1000):
        url = f"{gribstream_api_url}/forecasts"
        payload = {
            "forecastedFrom": forecasted_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "forecastedUntil": forecasted_until.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "minHorizon": min_horizon,
            "maxHorizon": max_horizon,
            "coordinates": coordinates,
            "variables": variables,
        }

        if stream:
            return self._get_stream(url, payload, chunksize)
        else:
            return self._get_dataframe(url, payload)

    def min_horizon(self, from_time, until_time, coordinates, variables, as_of=datetime.datetime.now(datetime.UTC), min_horizon=1, max_horizon=6, stream=False, chunksize=1000):
        url = f"{gribstream_api_url}/forecasts/min_horizon"
        payload = {
            "fromTime": from_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "untilTime": until_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "asOf": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "minHorizon": min_horizon,
            "maxHorizon": max_horizon,
            "coordinates": coordinates,
            "variables": variables,
        }

        if stream:
            return self._get_stream(url, payload, chunksize)
        else:
            return self._get_dataframe(url, payload)

    def _get_dataframe(self, url, payload):
        resp = self.session.post(
            url, 
            data=gzip.compress(json.dumps(payload).encode('utf-8')),
            )
        resp.raise_for_status()
        df = pd.read_csv(io.BytesIO(resp.content), parse_dates=[0, 1])
        return df

    def _get_stream(self, url, payload, chunksize):
        resp = self.session.post(
            url, 
            data=gzip.compress(json.dumps(payload).encode('utf-8')), 
            stream=True,
            )
        resp.raise_for_status()

        if resp.headers.get('Content-Encoding') == 'gzip':
            decompressed = gzip.GzipFile(fileobj=resp.raw)
        else:
            decompressed = resp.raw

        for chunk in pd.read_csv(decompressed, parse_dates=[0, 1], chunksize=chunksize):
            yield chunk

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
