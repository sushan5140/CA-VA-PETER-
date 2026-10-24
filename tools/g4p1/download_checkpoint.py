"""Fetch an exact official Hugging Face model revision outside the game repo."""

import argparse
import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_id")
    parser.add_argument("weight")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    info = HfApi().model_info(args.repo_id)
    args.output.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=args.repo_id,
        revision=info.sha,
        allow_patterns=["config.yaml", args.weight],
        local_dir=str(args.output),
    )
    for filename in ("config.yaml", args.weight):
        if not (args.output / filename).is_file():
            raise FileNotFoundError(f"Official snapshot missing {filename}")
    (args.output / "revision.json").write_text(
        json.dumps({"repo_id": args.repo_id, "revision": info.sha}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{args.repo_id}@{info.sha}")


if __name__ == "__main__":
    main()
