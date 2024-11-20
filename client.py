import requests
import pandas as pd
import datetime
import io
from typing import Optional, Dict, List, Any, Generator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import gzip
import json

gribstream_base_url = "https://gribstream.com"
# gribstream_base_url = "http://localhost:3000"
gribstream_api_url = f"{gribstream_base_url}/api/v1"

class GribStreamClient:
    """A client to interact with GribStream API for fetching weather forecast data."""
    def __init__(self, apikey: Optional[str] = None) -> None:
        """
        Initializes the GribStreamClient with API key and sets up a session with appropriate headers and retry configuration.

        Args:
        apikey (Optional[str]): The API key for accessing GribStream API. If None, fetches a demo token.
        """
        if apikey is None:
            print('Warning, missing API token. Running in limited DEMO mode.')
            keyreq = requests.get(f'{gribstream_base_url}/auth/demo')
            keyreq.raise_for_status()
            apikey = keyreq.content.decode()
        self.apikey = apikey

        self.session = requests.Session()
        for h, v in {'Accept-Encoding': 'gzip', 'Content-Encoding': 'gzip', 'Content-Type': 'application/json', 'Authorization': self.apikey}.items():
            self.session.headers.setdefault(h, v)

        retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def forecasts(self, forecasted_from: datetime.datetime, forecasted_until: datetime.datetime, coordinates: List[Dict[str, float]], variables: List[Dict[str, str]], min_horizon: int = 1, max_horizon: int = 1, stream: bool = False, chunksize: int = 1000) -> Any:
        """
        Fetches weather forecasts for specified parameters and time range.

        Args:
        forecasted_from (datetime.datetime): Start time for the forecast range.
        forecasted_until (datetime.datetime): End time for the forecast range.
        coordinates (List[Dict[str, float]]): List of dictionaries specifying latitude and longitude.
        variables (List[Dict[str, str]]): List of dictionaries specifying the variables to fetch.
        min_horizon (int): Minimum horizon for the forecasts.
        max_horizon (int): Maximum horizon for the forecasts.
        stream (bool): If True, returns a generator yielding chunks of data.
        chunksize (int): Number of rows per chunk if streaming.

        Returns:
        pandas.DataFrame or Generator[pandas.DataFrame, None, None]: DataFrame or stream of DataFrames containing the forecast data.
        """
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

    def min_horizon(self, from_time: datetime.datetime, until_time: datetime.datetime, coordinates: List[Dict[str, float]], variables: List[Dict[str, str]], as_of: datetime.datetime = datetime.datetime.now(datetime.timezone.utc), min_horizon: int = 1, max_horizon: int = 6, stream: bool = False, chunksize: int = 1000) -> Any:
        """
        Fetches historical forecast data for specified parameters and time range.

        Args:
        from_time (datetime.datetime): Start time for fetching historical data.
        until_time (datetime.datetime): End time for fetching historical data.
        coordinates (List[Dict[str, float]]): List of dictionaries specifying latitude and longitude.
        variables (List[Dict[str, str]]): List of dictionaries specifying the variables to fetch.
        as_of (datetime.datetime): Reference time for which the historical data is considered.
        min_horizon (int): Minimum forecast horizon in hours.
        max_horizon (int): Maximum forecast horizon in hours.
        stream (bool): If True, returns a generator yielding chunks of data.
        chunksize (int): Number of rows per chunk if streaming.

        Returns:
        pandas.DataFrame or Generator[pandas.DataFrame, None, None]: DataFrame or stream of DataFrames containing the historical forecast data.
        """
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

    def _get_dataframe(self, url: str, payload: Dict[str, Any]) -> pd.DataFrame:
        """
        Private method to fetch data and return it as a DataFrame.

        Args:
        url (str): API endpoint.
        payload (Dict[str, Any]): Parameters for the API request.

        Returns:
        pd.DataFrame: DataFrame containing the fetched data.
        """
        resp = self.session.post(url, data=gzip.compress(json.dumps(payload).encode('utf-8')))
        resp.raise_for_status()
        return pd.read_csv(io.BytesIO(resp.content), parse_dates=[0, 1])

    def _get_stream(self, url: str, payload: Dict[str, Any], chunksize: int) -> Generator[pd.DataFrame, None, None]:
        """
        Private method to stream data in chunks as DataFrames.

        Args:
        url (str): API endpoint.
        payload (Dict[str, Any]): Parameters for the API request.
        chunksize (int): Number of rows per chunk.

        Returns:
        Generator[pd.DataFrame, None, None]: Generator yielding DataFrames containing chunks of data.
        """
        resp = self.session.post(url, data=gzip.compress(json.dumps(payload).encode('utf-8')), stream=True)
        resp.raise_for_status()
        decompressed = gzip.GzipFile(fileobj=resp.raw) if resp.headers.get('Content-Encoding') == 'gzip' else resp.raw
        for chunk in pd.read_csv(decompressed, parse_dates=[0, 1], chunksize=chunksize):
            yield chunk

    def close(self) -> None:
        """Closes the session."""
        self.session.close()

    def __enter__(self) -> 'GribStreamClient':
        """Supports usage of the client as a context manager."""
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Exception], traceback: Optional[Any]) -> None:
        """Ensures the session is closed when exiting the context."""
        self.close()
