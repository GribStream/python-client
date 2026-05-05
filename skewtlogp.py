"""Skew-T Log-P example using GribStream pressure-level data.

This example writes a PNG by default so it works in terminals and headless
sessions. Use ``--show`` if you want an interactive Matplotlib window.

Install optional plotting dependencies with:
    pip install -r requirements-examples.txt
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

from gribstream import GribStreamClient

PRESSURE_LEVELS = [
    100,
    125,
    150,
    175,
    200,
    225,
    250,
    275,
    300,
    325,
    350,
    375,
    400,
    425,
    450,
    475,
    500,
    525,
    550,
    575,
    600,
    625,
    650,
    675,
    700,
    725,
    750,
    775,
    800,
    825,
    850,
    875,
    900,
    925,
    950,
    975,
    1000,
]


def parse_utc_time(value: str) -> dt.datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a Skew-T Log-P chart from GribStream data.")
    parser.add_argument("--dataset", default="hrrr", help="Dataset code with pressure-level TMP/DPT/UGRD/VGRD fields.")
    parser.add_argument("--time", default="2026-03-28T00:00:00Z", help="UTC valid time, e.g. 2026-03-28T00:00:00Z.")
    parser.add_argument("--lat", type=float, default=31.106, help="Latitude for the sounding point.")
    parser.add_argument("--lon", type=float, default=-96.2115, help="Longitude for the sounding point.")
    parser.add_argument("--name", default="Houston", help="Point label copied into result rows and chart title.")
    parser.add_argument("--min-lead-time", default="0h", help="Minimum lead time duration accepted by the API.")
    parser.add_argument("--max-lead-time", default="48h", help="Maximum lead time duration accepted by the API.")
    parser.add_argument("--output", type=Path, default=Path("skewtlogp.png"), help="PNG output path.")
    parser.add_argument("--show", action="store_true", help="Open an interactive Matplotlib window after saving.")
    return parser


def require_api_key() -> None:
    if not os.getenv("GRIBSTREAM_API_KEY"):
        raise SystemExit("Set GRIBSTREAM_API_KEY before running this example.")


def require_plotting_dependencies(show: bool):
    try:
        import matplotlib

        if not show:
            matplotlib.use("Agg")

        import matplotlib.pyplot as plt
        import numpy as np
        from metpy.plots import SkewT
        from metpy.units import units
    except ImportError as exc:
        raise SystemExit("Install optional plotting dependencies with: pip install -r requirements-examples.txt") from exc

    return plt, np, SkewT, units


def build_variables() -> list[dict[str, object]]:
    variables: list[dict[str, object]] = []
    for level in PRESSURE_LEVELS:
        level_name = f"{level} mb"
        variables.extend(
            [
                GribStreamClient.variable("TMP", level_name, info="", alias=f"tmp_{level}"),
                GribStreamClient.variable("DPT", level_name, info="", alias=f"dpt_{level}"),
                GribStreamClient.variable("UGRD", level_name, info="", alias=f"u_{level}"),
                GribStreamClient.variable("VGRD", level_name, info="", alias=f"v_{level}"),
            ]
        )
    return variables


def complete_levels(row, np) -> list[int]:
    levels: list[int] = []
    for level in PRESSURE_LEVELS:
        try:
            values = [float(row[f"tmp_{level}"]), float(row[f"dpt_{level}"]), float(row[f"u_{level}"]), float(row[f"v_{level}"])]
        except (KeyError, TypeError, ValueError):
            continue
        if all(np.isfinite(value) for value in values):
            levels.append(level)
    return levels


def main() -> None:
    args = build_parser().parse_args()
    require_api_key()
    plt, np, SkewT, units = require_plotting_dependencies(args.show)

    valid_time = parse_utc_time(args.time)
    coordinate = GribStreamClient.coordinate(args.lat, args.lon, args.name)

    with GribStreamClient() as client:
        rows = client.timeseries(
            dataset=args.dataset,
            times_list=[valid_time],
            min_lead_time=args.min_lead_time,
            max_lead_time=args.max_lead_time,
            coordinates=[coordinate],
            variables=build_variables(),
        )

    if not rows:
        raise RuntimeError("GribStream returned no rows for the selected sounding.")

    row = rows[0]
    levels = complete_levels(row, np)
    if len(levels) < 3:
        raise RuntimeError("Fewer than three complete pressure levels were returned; cannot draw a useful Skew-T.")

    pressure = np.array(levels) * units.hPa
    temperature = (np.array([float(row[f"tmp_{level}"]) for level in levels]) * units.kelvin).to("degC")
    dewpoint = (np.array([float(row[f"dpt_{level}"]) for level in levels]) * units.kelvin).to("degC")
    u_wind = (np.array([float(row[f"u_{level}"]) for level in levels]) * units("m/s")).to("knots")
    v_wind = (np.array([float(row[f"v_{level}"]) for level in levels]) * units("m/s")).to("knots")

    fig = plt.figure(figsize=(9, 9))
    skew = SkewT(fig, rotation=45)
    skew.plot(pressure, temperature, "r", label="Temperature")
    skew.plot(pressure, dewpoint, "g", label="Dewpoint")
    skew.plot_barbs(pressure, u_wind, v_wind)
    skew.plot_dry_adiabats()
    skew.plot_moist_adiabats()
    skew.plot_mixing_lines()

    plt.legend()
    plt.title(
        f"Skew-T Log-P: {args.name} ({args.lat:.4f}, {args.lon:.4f})\n"
        f"{args.dataset} run {row['forecasted_at']} for valid time {row['forecasted_time']}"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Wrote {args.output}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
