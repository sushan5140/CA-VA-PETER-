"""Blender background render and conservative GLB cleanup for a reviewed candidate.

blender -b -t 2 --python tools/g4p1/blender_review.py -- \
  --input candidate.glb --render-dir renders [--output cleaned.glb]

The four cameras assume the imported model faces Blender -Y. Review the preview
before naming the views; single-view reconstruction can choose another heading.
"""

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    return Vector([min(p[i] for p in points) for i in range(3)]), Vector(
        [max(p[i] for p in points) for i in range(3)]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    args.render_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(args.input))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise ValueError("Imported GLB has no mesh")
    initial_min, initial_max = bounds(meshes)
    height = initial_max.z - initial_min.z
    if height <= 0:
        raise ValueError("Imported mesh has zero height")
    scale = 1.70 / height
    center_xy = (initial_min + initial_max) / 2

    # Normalize only outermost imported nodes, preserving their child hierarchy.
    imported = list(bpy.context.scene.objects)
    roots = [obj for obj in imported if obj.parent is None]
    for obj in roots:
        obj.location.x = (obj.location.x - center_xy.x) * scale
        obj.location.y = (obj.location.y - center_xy.y) * scale
        obj.location.z = (obj.location.z - initial_min.z) * scale
        obj.scale *= scale
    bpy.context.view_layer.update()

    for mesh in meshes:
        for polygon in mesh.data.polygons:
            polygon.use_smooth = True
    for image in bpy.data.images:
        if image.source == "FILE" and max(image.size[:]) > 1024:
            image.scale(1024, 1024)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=str(args.output), export_format="GLB",
                                  export_apply=True, export_texcoords=True,
                                  export_normals=True, export_materials="EXPORT")

    world = bpy.context.scene.world or bpy.data.worlds.new("Review world")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs[0].default_value = (0.7, 0.72, 0.76, 1)
    world.node_tree.nodes.get("Background").inputs[1].default_value = 0.8

    for name, pos, power, size in [
        ("key", (-2.3, -3.0, 4.0), 700, 4),
        ("fill", (2.8, -1.0, 2.7), 450, 3),
        ("rim", (1.0, 2.5, 3.5), 550, 3),
    ]:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = power
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (Vector((0, 0, 0.85)) - obj.location).to_track_quat("-Z", "Y").to_euler()

    camera_data = bpy.data.cameras.new("turntable")
    camera = bpy.data.objects.new("turntable", camera_data)
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.2
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    # Kaggle's apt Blender build omits OpenImageDenoiser.
    for layer in scene.view_layers:
        layer.cycles.use_denoising = False
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    for name, degrees in [("front", 0), ("three_quarter", 45), ("side", 90), ("back", 180)]:
        theta = math.radians(degrees)
        camera.location = (3.5 * math.sin(theta), -3.5 * math.cos(theta), 1.0)
        camera.rotation_euler = (Vector((0, 0, 0.85)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(args.render_dir / f"{name}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
