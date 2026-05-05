"""Small helpers used by runnable examples."""

from __future__ import annotations

import datetime as dt
import os
from collections.abc import Iterable, Sequence
from typing import Any

Row = dict[str, Any]


def require_api_key() -> None:
    if not os.getenv("GRIBSTREAM_API_KEY"):
        raise SystemExit("Set GRIBSTREAM_API_KEY before running this example.")


def parse_utc(value: Any) -> dt.datetime:
    if isinstance(value, dt.datetime):
        parsed = value
    else:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def with_lead_hours(rows: Iterable[Row]) -> list[Row]:
    result = []
    for row in rows:
        copied = dict(row)
        lead = parse_utc(copied["forecasted_time"]) - parse_utc(copied["forecasted_at"])
        copied["lead_hours"] = round(lead.total_seconds() / 3600, 2)
        result.append(copied)
    return result


def sorted_rows(rows: Iterable[Row], keys: Sequence[str], *, reverse: bool = False) -> list[Row]:
    return sorted(rows, key=lambda row: tuple(row.get(key, "") for key in keys), reverse=reverse)


def print_rows(rows: Iterable[Row], columns: Sequence[str] | None = None, *, limit: int = 20) -> None:
    selected = list(rows)[:limit]
    if not selected:
        print("(no rows)")
        return

    if columns is None:
        columns = list(selected[0].keys())

    widths = {
        column: max(len(column), *(len(str(row.get(column, ""))) for row in selected))
        for column in columns
    }
    print("  ".join(column.ljust(widths[column]) for column in columns))
    print("  ".join("-" * widths[column] for column in columns))
    for row in selected:
        print("  ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))
