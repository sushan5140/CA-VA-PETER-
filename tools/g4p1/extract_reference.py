"""Deterministic crops from the locked G3 character sheet.

Usage: python tools/g4p1/extract_reference.py SHEET.png OUTPUT_DIR
Requires Pillow 10.1.0. The coordinates are tied to the 1491x1055 G3 sheet.
"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


EXPECTED_SIZE = (1491, 1055)
CROPS = {
    "front_clean": (188, 12, 446, 571),
    "three_quarter": (439, 13, 642, 571),
    "side": (647, 14, 793, 571),
    "back": (798, 14, 1004, 571),
    "face_neutral": (1007, 49, 1158, 274),
    "face_determined": (1167, 49, 1319, 274),
    "hair_front": (1043, 359, 1153, 525),
    "hair_side": (1156, 359, 1250, 525),
    "hair_back": (1254, 359, 1363, 525),
    "jacket_shirt": (18, 626, 250, 797),
    "scarf": (258, 626, 401, 797),
    "satchel": (409, 626, 632, 797),
    "trousers": (640, 626, 826, 797),
    "glove": (834, 626, 997, 797),
    "sneaker": (1008, 626, 1219, 797),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sheet", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(args.sheet) as source:
        if source.size != EXPECTED_SIZE:
            raise ValueError(f"Expected G3 sheet {EXPECTED_SIZE}, got {source.size}")
        source = source.convert("RGB")
        for name, box in CROPS.items():
            crop = source.crop(box)
            if name == "front_clean":
                # The title's red underline grazes the left edge of the front panel.
                # This patch touches background only; the figure starts farther right.
                background = source.getpixel((187, 208))
                ImageDraw.Draw(crop).rectangle((0, 0, 65, 197), fill=background)
                # The word "SHEET" ends just left of the rolled sleeve.
                ImageDraw.Draw(crop).rectangle((0, 193, 28, 220), fill=background)
            crop.save(args.output_dir / f"{name}.png", optimize=True)

    metadata = {
        "source_sha256": hashlib.sha256(args.sheet.read_bytes()).hexdigest(),
        "source_dimensions": EXPECTED_SIZE,
        "crop_boxes_xyxy": CROPS,
        "front_note": "Original pixels except a background-only title removal patch; inference scripts apply rembg.",
    }
    (args.output_dir / "crops.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
