"""Structural GLB report; visual resemblance requires human review of renders."""

import argparse
import hashlib
import json
from pathlib import Path

import trimesh


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("glb", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    scene = trimesh.load(args.glb, force="scene", process=False)
    meshes = [geometry for geometry in scene.geometry.values() if isinstance(geometry, trimesh.Trimesh)]
    if not meshes:
        raise ValueError("GLB contains no triangle mesh")
    bounds = scene.bounds
    report = {
        "file": args.glb.name,
        "sha256": hashlib.sha256(args.glb.read_bytes()).hexdigest(),
        "bytes": args.glb.stat().st_size,
        "mesh_count": len(meshes),
        "triangles": sum(len(m.faces) for m in meshes),
        "vertices": sum(len(m.vertices) for m in meshes),
        "bounds": bounds.tolist() if bounds is not None else None,
        "extents": scene.extents.tolist() if scene.extents is not None else None,
        "watertight_meshes": sum(bool(m.is_watertight) for m in meshes),
        "uv_meshes": sum(getattr(m.visual, "uv", None) is not None for m in meshes),
        "textured_meshes": sum(getattr(getattr(m.visual, "material", None), "baseColorTexture", None) is not None for m in meshes),
        "note": "Structural report only; glTF conformance, silhouette and face fidelity need separate checks.",
    }
    if report["triangles"] <= 0 or not all(float(x) > 0 for x in report["extents"]):
        raise ValueError(f"Invalid or flat mesh: {report}")
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
