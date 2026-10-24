"""Compose the locked reference beside model turntable renders, if present."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    names = ("front", "three_quarter", "side", "back")
    reference = args.results / "reference"
    rows = [("Locked G3", [reference / f"{x}.png" for x in ("front_clean", *names[1:])])]
    for model in ("sf3d", "triposr"):
        images = [args.results / model / "renders" / f"{angle}.png" for angle in names]
        if all(path.exists() for path in images):
            rows.append((model.upper(), images))
    if len(rows) == 1:
        raise ValueError("No model renders found for a visual comparison")
    width, height, label = 320, 420, 34
    sheet = Image.new("RGB", (width * 4, (height + label) * len(rows)), (244, 241, 236))
    draw = ImageDraw.Draw(sheet)
    for row_index, (title, images) in enumerate(rows):
        for col_index, path in enumerate(images):
            with Image.open(path) as source:
                frame = source.convert("RGBA")
                frame.thumbnail((width - 12, height - 12), Image.Resampling.LANCZOS)
                x = col_index * width + (width - frame.width) // 2
                y = row_index * (height + label) + label + (height - frame.height) // 2
                sheet.paste(frame, (x, y), frame)
            draw.text((col_index * width + 8, row_index * (height + label) + 8),
                      f"{title} / {names[col_index]}", fill=(29, 31, 36))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)


if __name__ == "__main__":
    main()
