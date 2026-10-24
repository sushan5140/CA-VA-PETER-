"""Apply the minimal TripoSR CUDA texture-bake fix to a pinned checkout.

The upstream bake code creates position samples on CPU even when its scene code
and renderer are on CUDA, then calls NumPy on a CUDA output. Both operations
must use the renderer's device before exporting the baked atlas.
"""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    source = args.checkout / "tsr/bake_texture.py"
    text = source.read_text(encoding="utf-8")
    changes = {
        "positions = torch.tensor(positions_texture.reshape(-1, 4)[:, :-1])":
            "positions = torch.tensor(positions_texture.reshape(-1, 4)[:, :-1], device=scene_code.device)",
        'queried_grid["color"].numpy().reshape(-1, 3)':
            'queried_grid["color"].detach().cpu().numpy().reshape(-1, 3)',
    }
    for old, new in changes.items():
        if new in text:
            continue
        if text.count(old) != 1:
            raise RuntimeError(f"Expected one upstream match for {old!r}; found {text.count(old)}")
        text = text.replace(old, new)
    source.write_text(text, encoding="utf-8")
    print("TripoSR texture bake CUDA patch applied", flush=True)


if __name__ == "__main__":
    main()
