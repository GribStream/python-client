"""Python client for the GribStream API v2.

The client intentionally stays close to the published API contract. It exposes
forecast query endpoints, public catalog discovery endpoints, response-format
selection, and small helpers for constructing request payloads.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import os
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_BASE_URL = "https://gribstream.com"
API_KEY_ENV = "GRIBSTREAM_API_KEY"
BASE_URL_ENV = "GRIBSTREAM_BASE_URL"

CSV = "text/csv"
JSON = "application/json"
NDJSON = "application/ndjson"
X_NDJSON = "application/x-ndjson"

JsonObject = dict[str, Any]
TimeLike = str | dt.datetime
DurationLike = str | dt.timedelta | int | float


class GribStreamApiError(RuntimeError):
    """Raised when GribStream returns a non-success HTTP status."""

    def __init__(self, response: requests.Response) -> None:
        self.response = response
        self.status_code = response.status_code
        retry_after = response.headers.get("Retry-After")
        message = f"GribStream API request failed: {response.status_code} {response.reason}"
        if retry_after:
            message += f" (Retry-After: {retry_after}s)"
        body = response.text.strip()
        if body:
            message += f"\n{body[:2000]}"
        super().__init__(message)


class GribStreamClient:
    """Small convenience wrapper around GribStream API v2.

    Parameters
    ----------
    api_key:
        Raw API token. If omitted, the client reads ``GRIBSTREAM_API_KEY``.
    base_url:
        Deployment base URL. Defaults to ``GRIBSTREAM_BASE_URL`` or
        ``https://gribstream.com``.
    timeout:
        Per-request timeout in seconds.
    retries:
        Retry count for transient HTTP errors.
    session:
        Optional ``requests.Session`` for callers that need custom transport.
    apikey:
        Deprecated spelling kept for compatibility with older examples.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 120,
        retries: int = 5,
        session: Optional[requests.Session] = None,
        apikey: Optional[str] = None,
    ) -> None:
        if api_key is not None and apikey is not None:
            raise ValueError("Pass either api_key or deprecated apikey, not both.")
        if api_key is None:
            api_key = apikey
        if api_key is None:
            api_key = os.getenv(API_KEY_ENV)

        self.api_key = api_key.strip() if api_key else None
        self.base_url = (base_url or os.getenv(BASE_URL_ENV) or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self._owns_session = session is None

        self.session.headers.setdefault("Accept-Encoding", "gzip")
        self.session.headers.setdefault("Content-Type", "application/json")

        retry_policy = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def timeseries(
        self,
        dataset: str,
        *,
        from_time: Optional[TimeLike] = None,
        until_time: Optional[TimeLike] = None,
        times_list: Optional[Sequence[TimeLike]] = None,
        coordinates: Optional[Sequence[Mapping[str, Any]]] = None,
        grid: Optional[Mapping[str, Any]] = None,
        variables: Optional[Sequence[Mapping[str, Any]]] = None,
        expressions: Optional[Sequence[Mapping[str, Any]]] = None,
        filter: Optional[Mapping[str, Any]] = None,
        as_of: Optional[TimeLike] = None,
        min_lead_time: Optional[DurationLike] = None,
        max_lead_time: Optional[DurationLike] = None,
        min_horizon: Optional[int] = None,
        max_horizon: Optional[int] = None,
        members: Optional[Sequence[int]] = None,
        accept: str = CSV,
        stream: bool = False,
        chunksize: int = 10_000,
        raw: bool = False,
        **extra_body: Any,
    ) -> Any:
        """Query best-available values by valid time.

        ``from_time``/``until_time`` and ``times_list`` are valid-time selectors.
        ``as_of`` is a run-time cutoff for leakage-safe backtests.
        """
        payload = self.build_timeseries_payload(
            from_time=from_time,
            until_time=until_time,
            times_list=times_list,
            coordinates=coordinates,
            grid=grid,
            variables=variables,
            expressions=expressions,
            filter=filter,
            as_of=as_of,
            min_lead_time=min_lead_time,
            max_lead_time=max_lead_time,
            min_horizon=min_horizon,
            max_horizon=max_horizon,
            members=members,
            **extra_body,
        )
        return self.query(dataset, "timeseries", payload, accept=accept, stream=stream, chunksize=chunksize, raw=raw)

    def runs(
        self,
        dataset: str,
        *,
        forecasted_from: Optional[TimeLike] = None,
        forecasted_until: Optional[TimeLike] = None,
        times_list: Optional[Sequence[TimeLike]] = None,
        coordinates: Optional[Sequence[Mapping[str, Any]]] = None,
        grid: Optional[Mapping[str, Any]] = None,
        variables: Optional[Sequence[Mapping[str, Any]]] = None,
        expressions: Optional[Sequence[Mapping[str, Any]]] = None,
        filter: Optional[Mapping[str, Any]] = None,
        min_lead_time: Optional[DurationLike] = None,
        max_lead_time: Optional[DurationLike] = None,
        min_horizon: Optional[int] = None,
        max_horizon: Optional[int] = None,
        members: Optional[Sequence[int]] = None,
        accept: str = CSV,
        stream: bool = False,
        chunksize: int = 10_000,
        raw: bool = False,
        **extra_body: Any,
    ) -> Any:
        """Query every matching forecast run.

        ``forecasted_from``/``forecasted_until`` and ``times_list`` are model
        run-time selectors, not valid-time selectors.
        """
        payload = self.build_runs_payload(
            forecasted_from=forecasted_from,
            forecasted_until=forecasted_until,
            times_list=times_list,
            coordinates=coordinates,
            grid=grid,
            variables=variables,
            expressions=expressions,
            filter=filter,
            min_lead_time=min_lead_time,
            max_lead_time=max_lead_time,
            min_horizon=min_horizon,
            max_horizon=max_horizon,
            members=members,
            **extra_body,
        )
        return self.query(dataset, "runs", payload, accept=accept, stream=stream, chunksize=chunksize, raw=raw)

    def history(self, dataset: str, **kwargs: Any) -> Any:
        """Deprecated alias for :meth:`timeseries`."""
        return self.timeseries(dataset, **kwargs)

    def forecasts(self, dataset: str, **kwargs: Any) -> Any:
        """Deprecated alias for :meth:`runs`."""
        return self.runs(dataset, **kwargs)

    def query(
        self,
        dataset: str,
        endpoint: str,
        payload: Mapping[str, Any],
        *,
        accept: str = CSV,
        stream: bool = False,
        chunksize: int = 10_000,
        raw: bool = False,
    ) -> Any:
        """POST a fully formed payload to a forecast query endpoint.

        ``endpoint`` is usually ``"timeseries"`` or ``"runs"``. Legacy aliases
        ``"history"`` and ``"forecasts"`` are also accepted by the API.
        """
        if endpoint not in {"timeseries", "runs", "history", "forecasts"}:
            raise ValueError("endpoint must be one of: timeseries, runs, history, forecasts")
        response = self._request(
            "POST",
            f"/api/v2/{dataset}/{endpoint}",
            json_body=dict(payload),
            accept=accept,
            require_auth=True,
            stream=stream,
        )
        if raw:
            return response
        return self._parse_query_response(response, accept=accept, stream=stream, chunksize=chunksize)

    def build_timeseries_payload(
        self,
        *,
        from_time: Optional[TimeLike] = None,
        until_time: Optional[TimeLike] = None,
        times_list: Optional[Sequence[TimeLike]] = None,
        coordinates: Optional[Sequence[Mapping[str, Any]]] = None,
        grid: Optional[Mapping[str, Any]] = None,
        variables: Optional[Sequence[Mapping[str, Any]]] = None,
        expressions: Optional[Sequence[Mapping[str, Any]]] = None,
        filter: Optional[Mapping[str, Any]] = None,
        as_of: Optional[TimeLike] = None,
        min_lead_time: Optional[DurationLike] = None,
        max_lead_time: Optional[DurationLike] = None,
        min_horizon: Optional[int] = None,
        max_horizon: Optional[int] = None,
        members: Optional[Sequence[int]] = None,
        **extra_body: Any,
    ) -> JsonObject:
        payload: JsonObject = {}
        self._add_time_selection(payload, "fromTime", from_time, "untilTime", until_time, times_list)
        if as_of is not None:
            payload["asOf"] = self._format_time(as_of)
        self._add_common_query_fields(
            payload,
            coordinates=coordinates,
            grid=grid,
            variables=variables,
            expressions=expressions,
            filter=filter,
            min_lead_time=min_lead_time,
            max_lead_time=max_lead_time,
            min_horizon=min_horizon,
            max_horizon=max_horizon,
            members=members,
            extra_body=extra_body,
        )
        return payload

    def build_runs_payload(
        self,
        *,
        forecasted_from: Optional[TimeLike] = None,
        forecasted_until: Optional[TimeLike] = None,
        times_list: Optional[Sequence[TimeLike]] = None,
        coordinates: Optional[Sequence[Mapping[str, Any]]] = None,
        grid: Optional[Mapping[str, Any]] = None,
        variables: Optional[Sequence[Mapping[str, Any]]] = None,
        expressions: Optional[Sequence[Mapping[str, Any]]] = None,
        filter: Optional[Mapping[str, Any]] = None,
        min_lead_time: Optional[DurationLike] = None,
        max_lead_time: Optional[DurationLike] = None,
        min_horizon: Optional[int] = None,
        max_horizon: Optional[int] = None,
        members: Optional[Sequence[int]] = None,
        **extra_body: Any,
    ) -> JsonObject:
        payload: JsonObject = {}
        self._add_time_selection(
            payload,
            "forecastedFrom",
            forecasted_from,
            "forecastedUntil",
            forecasted_until,
            times_list,
        )
        self._add_common_query_fields(
            payload,
            coordinates=coordinates,
            grid=grid,
            variables=variables,
            expressions=expressions,
            filter=filter,
            min_lead_time=min_lead_time,
            max_lead_time=max_lead_time,
            min_horizon=min_horizon,
            max_horizon=max_horizon,
            members=members,
            extra_body=extra_body,
        )
        return payload

    def list_datasets(
        self,
        *,
        code: Optional[str | Sequence[str]] = None,
        family: Optional[str] = None,
        is_ensemble: Optional[bool] = None,
        tag: Optional[str | Sequence[str]] = None,
    ) -> list[JsonObject]:
        """List public datasets, optionally filtered by code/family/tag."""
        return self._get_json(
            "/api/v2/catalog/datasets",
            params={"code": code, "family": family, "is_ensemble": is_ensemble, "tag": tag},
        )

    def get_dataset(self, dataset: str) -> JsonObject:
        """Return public metadata for one dataset code."""
        return self._get_json(f"/api/v2/catalog/datasets/{dataset}")

    def list_dataset_parameters(self, dataset: str) -> list[JsonObject]:
        """List parameter summaries for one dataset."""
        return self._get_json(f"/api/v2/catalog/datasets/{dataset}/parameters")

    def get_dataset_parameter(self, dataset: str, parameter: str) -> JsonObject:
        """Return full parameter metadata and selector variations."""
        return self._get_json(f"/api/v2/catalog/datasets/{dataset}/parameters/{parameter}")

    def list_shared_parameters(
        self,
        *,
        dataset: Optional[str | Sequence[str]] = None,
        dataset_mode: Optional[str] = None,
    ) -> list[JsonObject]:
        """List curated shared cross-dataset parameter presets."""
        return self._get_json(
            "/api/v2/catalog/shared-parameters",
            params={"dataset": dataset, "dataset_mode": dataset_mode},
        )

    def get_shared_parameter(
        self,
        parameter: str,
        *,
        dataset: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> JsonObject:
        """Return a shared parameter preset, optionally resolved for a dataset."""
        return self._get_json(
            f"/api/v2/catalog/shared-parameters/{parameter}",
            params={"dataset": dataset, "alias": alias},
        )

    def resolve_shared_parameter(self, parameter: str, *, dataset: str, alias: Optional[str] = None) -> JsonObject:
        """Return the machine-readable request fragment for one shared preset."""
        detail = self.get_shared_parameter(parameter, dataset=dataset, alias=alias)
        if detail.get("resolved_supported") is False:
            raise ValueError(f"Shared parameter {parameter!r} is not supported for dataset {dataset!r}.")
        request = detail.get("resolved_request")
        if not request:
            raise ValueError(f"Shared parameter {parameter!r} did not include a resolved_request.")
        return request

    @staticmethod
    def coordinate(lat: float, lon: float, name: Optional[str] = None) -> JsonObject:
        coordinate: JsonObject = {"lat": lat, "lon": lon}
        if name is not None:
            coordinate["name"] = name
        return coordinate

    @staticmethod
    def grid(
        min_latitude: float,
        max_latitude: float,
        min_longitude: float,
        max_longitude: float,
        step: float,
    ) -> JsonObject:
        return {
            "minLatitude": min_latitude,
            "maxLatitude": max_latitude,
            "minLongitude": min_longitude,
            "maxLongitude": max_longitude,
            "step": step,
        }

    @staticmethod
    def variable(
        name: str,
        level: str,
        *,
        info: Optional[str] = None,
        alias: Optional[str] = None,
        hidden: Optional[bool] = None,
    ) -> JsonObject:
        variable: JsonObject = {"name": name, "level": level}
        if info is not None:
            variable["info"] = info
        if alias is not None:
            variable["alias"] = alias
        if hidden is not None:
            variable["hidden"] = hidden
        return variable

    @staticmethod
    def expression(expression: str, *, alias: Optional[str] = None, hidden: Optional[bool] = None) -> JsonObject:
        field: JsonObject = {"expression": expression}
        if alias is not None:
            field["alias"] = alias
        if hidden is not None:
            field["hidden"] = hidden
        return field

    @staticmethod
    def filter_expression(expression: str) -> JsonObject:
        return {"expression": expression}

    @staticmethod
    def merge_request_fragment(payload: Mapping[str, Any], fragment: Mapping[str, Any]) -> JsonObject:
        """Merge a shared-parameter request fragment into a query payload."""
        merged = dict(payload)
        for key in ("variables", "expressions"):
            if key in fragment:
                merged[key] = [*merged.get(key, []), *fragment[key]]
        return merged

    def close(self) -> None:
        """Close the underlying HTTP session if this client owns it."""
        if self._owns_session:
            self.session.close()

    def __enter__(self) -> "GribStreamClient":
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Exception], traceback: Optional[Any]) -> None:
        self.close()

    def _get_json(self, path: str, *, params: Optional[Mapping[str, Any]] = None) -> Any:
        response = self._request("GET", path, params=params, accept=JSON, require_auth=False)
        return response.json()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json_body: Optional[Mapping[str, Any]] = None,
        accept: Optional[str] = None,
        require_auth: bool = False,
        stream: bool = False,
    ) -> requests.Response:
        if require_auth and not self.api_key:
            raise ValueError(f"Set {API_KEY_ENV} or pass api_key=... before calling forecast query endpoints.")

        headers: JsonObject = {}
        if accept:
            headers["Accept"] = accept
        if self.api_key:
            headers["Authorization"] = self._authorization_header(self.api_key)

        response = self.session.request(
            method,
            self._url(path),
            params=self._normalize_params(params),
            json=json_body,
            headers=headers,
            timeout=self.timeout,
            stream=stream,
        )
        if response.status_code >= 400:
            raise GribStreamApiError(response)
        return response

    def _parse_query_response(
        self,
        response: requests.Response,
        *,
        accept: str,
        stream: bool,
        chunksize: int,
    ) -> Any:
        accept = (accept or CSV).lower()
        if accept in {NDJSON, X_NDJSON}:
            if stream:
                return self._iter_ndjson(response)
            try:
                return [json.loads(line) for line in response.text.splitlines() if line.strip()]
            finally:
                response.close()

        if accept == JSON:
            try:
                return response.json()
            finally:
                response.close()

        if stream:
            return self._iter_csv_chunks(response, chunksize)
        try:
            return self._read_csv_response(response)
        finally:
            response.close()

    def _read_csv_response(self, response: requests.Response) -> pd.DataFrame:
        frame = pd.read_csv(io.BytesIO(response.content))
        return self._parse_time_columns(frame)

    def _iter_csv_chunks(self, response: requests.Response, chunksize: int) -> Iterator[pd.DataFrame]:
        response.raw.decode_content = True
        try:
            for chunk in pd.read_csv(response.raw, chunksize=chunksize):
                yield self._parse_time_columns(chunk)
        finally:
            response.close()

    def _iter_ndjson(self, response: requests.Response) -> Iterator[JsonObject]:
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    yield json.loads(line)
        finally:
            response.close()

    @staticmethod
    def _parse_time_columns(frame: pd.DataFrame) -> pd.DataFrame:
        for column in ("forecasted_at", "forecasted_time"):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column], utc=True)
        return frame

    @staticmethod
    def _add_time_selection(
        payload: JsonObject,
        start_key: str,
        start: Optional[TimeLike],
        end_key: str,
        end: Optional[TimeLike],
        times_list: Optional[Sequence[TimeLike]],
    ) -> None:
        has_range = start is not None or end is not None
        has_list = times_list is not None
        if has_range and has_list:
            raise ValueError("Use either a time range or times_list, not both.")
        if has_list:
            values = [GribStreamClient._format_time(value) for value in times_list or []]
            if not values:
                raise ValueError("times_list must contain at least one timestamp.")
            payload["timesList"] = values
            return
        if start is None or end is None:
            raise ValueError(f"Pass both {start_key} and {end_key}, or pass times_list.")
        payload[start_key] = GribStreamClient._format_time(start)
        payload[end_key] = GribStreamClient._format_time(end)

    @staticmethod
    def _add_common_query_fields(
        payload: JsonObject,
        *,
        coordinates: Optional[Sequence[Mapping[str, Any]]],
        grid: Optional[Mapping[str, Any]],
        variables: Optional[Sequence[Mapping[str, Any]]],
        expressions: Optional[Sequence[Mapping[str, Any]]],
        filter: Optional[Mapping[str, Any]],
        min_lead_time: Optional[DurationLike],
        max_lead_time: Optional[DurationLike],
        min_horizon: Optional[int],
        max_horizon: Optional[int],
        members: Optional[Sequence[int]],
        extra_body: Mapping[str, Any],
    ) -> None:
        if not variables:
            raise ValueError("At least one variable is required.")
        if not coordinates and grid is None:
            raise ValueError("Pass coordinates, grid, or both.")

        payload["variables"] = [dict(variable) for variable in variables]
        if coordinates:
            payload["coordinates"] = [dict(coordinate) for coordinate in coordinates]
        if grid is not None:
            payload["grid"] = dict(grid)
        if expressions:
            payload["expressions"] = [dict(expression) for expression in expressions]
        if filter is not None:
            payload["filter"] = dict(filter)
        if min_lead_time is not None:
            payload["minLeadTime"] = GribStreamClient._format_duration(min_lead_time)
        if max_lead_time is not None:
            payload["maxLeadTime"] = GribStreamClient._format_duration(max_lead_time)
        if min_horizon is not None:
            payload["minHorizon"] = min_horizon
        if max_horizon is not None:
            payload["maxHorizon"] = max_horizon
        if members is not None:
            payload["members"] = list(members)
        for key, value in extra_body.items():
            if value is not None:
                payload[key] = value

    @staticmethod
    def _format_time(value: TimeLike) -> str:
        if isinstance(value, str):
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.timezone.utc)
        else:
            value = value.astimezone(dt.timezone.utc)
        return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _format_duration(value: DurationLike) -> str:
        if isinstance(value, dt.timedelta):
            seconds = int(value.total_seconds())
            if seconds % 3600 == 0:
                return f"{seconds // 3600}h"
            if seconds % 60 == 0:
                return f"{seconds // 60}m"
            return f"{seconds}s"
        return str(value)

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    @staticmethod
    def _authorization_header(api_key: str) -> str:
        return api_key if api_key.lower().startswith("bearer ") else f"Bearer {api_key}"

    @staticmethod
    def _normalize_params(params: Optional[Mapping[str, Any]]) -> Optional[JsonObject]:
        if not params:
            return None
        normalized: JsonObject = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                normalized[key] = str(value).lower()
            elif isinstance(value, str):
                normalized[key] = value
            elif isinstance(value, Iterable):
                normalized[key] = ",".join(str(item) for item in value)
            else:
                normalized[key] = value
        return normalized


__all__ = [
    "API_KEY_ENV",
    "BASE_URL_ENV",
    "CSV",
    "JSON",
    "NDJSON",
    "X_NDJSON",
    "GribStreamApiError",
    "GribStreamClient",
]
