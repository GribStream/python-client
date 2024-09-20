import requests
import pandas as pd
import io
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import gzip
import json
import brotli
import zlib

class GribStreamClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def forecasts(self, forecasted_from, forecasted_before, min_horizon, max_horizon, coordinates, variables, stream=False, chunksize=1000):
        url = f"{self.base_url}/forecasts"
        payload = {
            "forecastedFrom": forecasted_from,
            "forecastedBefore": forecasted_before,
            "minHorizon": min_horizon,
            "maxHorizon": max_horizon,
            "coordinates": coordinates,
            "variables": variables,
        }

        if stream:
            return self._get_forecasts_stream(url, payload, chunksize)
        else:
            return self._get_forecasts_dataframe(url, payload)

    def _get_forecasts_dataframe(self, url, payload):
        resp = self.session.post(
            url, 
            data=zlib.compress(json.dumps(payload).encode('utf-8')),
            headers={'Accept-Encoding': 'deflate, gzip, br', 'Content-Encoding': 'deflate', 'Content-Type': 'application/json'},
            )
        resp.raise_for_status()
        df = pd.read_csv(io.BytesIO(resp.content), parse_dates=[0, 1])
        return df

    def _get_forecasts_stream(self, url, payload, chunksize):
        resp = self.session.post(
            url, 
            data=zlib.compress(json.dumps(payload).encode('utf-8')), 
            headers={'Accept-Encoding': 'gzip', 'Content-Encoding': 'deflate', 'Content-Type': 'application/json'},
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
