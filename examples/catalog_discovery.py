"""Use public catalog endpoints to discover datasets and exact selectors."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client import GribStreamClient


def main() -> None:
    with GribStreamClient() as client:
        datasets = client.list_datasets(code=["gfs", "ifsoper", "gefsatmos"])
        print("Datasets:")
        for dataset in datasets:
            print(f"- {dataset['code']}: {dataset.get('display_label') or dataset.get('full_name')}")

        parameter = client.get_dataset_parameter("ifsoper", "2t")
        print("\nIFS 2t selector variations:")
        for variation in parameter.get("variations", [])[:5]:
            print(f"- {variation['selector']}")


if __name__ == "__main__":
    main()
