"""Download FreshRetailNet-50K and save a random subset of stores as parquet."""

import argparse
import logging
import random
from pathlib import Path

from datasets import load_dataset

DATASET_NAME = "Dingdong-Inc/FreshRetailNet-50K"

logger = logging.getLogger(__name__)


def pick_stores(store_ids: list[int], n_stores: int, seed: int) -> set[int]:
    """Return a reproducible random sample of store ids."""
    ordered = sorted(store_ids)
    if n_stores >= len(ordered):
        return set(ordered)
    return set(random.Random(seed).sample(ordered, n_stores))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-stores", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dataset = load_dataset(DATASET_NAME)
    stores = pick_stores(dataset["train"].unique("store_id"), args.n_stores, args.seed)
    out_dir = Path("data") / "frn" / f"stores_{len(stores)}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # The eval split is the final hold-out: saved now, opened once at the end.
    for split in ("train", "eval"):
        subset = dataset[split].filter(
            lambda ids: [store_id in stores for store_id in ids],
            input_columns="store_id",
            batched=True,
        )
        path = out_dir / f"{split}.parquet"
        subset.to_parquet(path)
        logger.info("Wrote %d %s rows to %s", subset.num_rows, split, path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    main()
