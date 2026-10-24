"""Attach TripoSR's baked PNG to its UV OBJ and export a textured GLB."""

import argparse
from pathlib import Path

import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("obj", type=Path)
    parser.add_argument("texture", type=Path)
    parser.add_argument("glb", type=Path)
    args = parser.parse_args()

    mesh = trimesh.load(args.obj, force="mesh", process=False)
    uv = getattr(mesh.visual, "uv", None)
    if uv is None or len(uv) != len(mesh.vertices):
        raise ValueError("TripoSR baked OBJ has no usable UV coordinates")
    with Image.open(args.texture) as image:
        atlas = image.convert("RGB").copy()
    mesh.visual = TextureVisuals(
        uv=uv,
        material=PBRMaterial(name="tripo_baked", baseColorTexture=atlas),
    )
    args.glb.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(args.glb)
    if args.glb.stat().st_size < 1024:
        raise ValueError("Converted GLB is unexpectedly small")


if __name__ == "__main__":
    main()
