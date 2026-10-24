"""Attach TripoSR's baked PNG to its UV OBJ and export a textured GLB."""

import argparse
from pathlib import Path

import numpy as np
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
    # TripoSR OBJ is Z-up; glTF and Three.js expect Y-up. Put the feet on
    # Y=0 and preserve a useful 1.70 m character scale for the game.
    mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
    height = float(mesh.bounds[1, 1] - mesh.bounds[0, 1])
    if height <= 0:
        raise ValueError("TripoSR mesh has no height")
    mesh.apply_scale(1.70 / height)
    center = (mesh.bounds[0] + mesh.bounds[1]) / 2
    mesh.apply_translation((-center[0], -mesh.bounds[0, 1], -center[2]))
    args.glb.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(args.glb)
    if args.glb.stat().st_size < 1024:
        raise ValueError("Converted GLB is unexpectedly small")


if __name__ == "__main__":
    main()
