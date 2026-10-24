# G4.P1 — Street Barricade Strategist reconstruction

## Status

**TripoSR reconstruction ran on a Kaggle T4; G4.P1 remains incomplete.** A real
textured GLB was generated, baked, exported, structurally checked, and rendered
from four angles. Its face, hair, satchel, and back do not match the locked G3
design closely enough for the game, so it is an experimental candidate rather
than the final `street_barricade_strategist.glb`. The 65,593-triangle mesh is
also unrigged and above the game budget. The Kaggle output archive is named
`g4p1_deliverables.zip` and labels the mesh `triposr_candidate.glb`.

The authoritative sheet is
[`assets/characters/street_barricade_strategist/reference/g3_character_sheet.png`](../assets/characters/street_barricade_strategist/reference/g3_character_sheet.png).
Its SHA-256 is `4016419d22f2174031175f01a5a8e72196105f00e1da32d66ec8bcc5983bb32e`.
`tools/g4p1/extract_reference.py` produced the view and detail crops with
recorded coordinates in `crops.json`. The front input has the same character
pixels, apart from a small background-only patch that removes stray sheet text.
Both pipelines are configured to use that same `front_clean.png` input and
their own documented background-removal step.

## Upstream audit

| Pipeline | Source commit | Official checkpoint | Python and requirements | Documented default memory | License |
| --- | --- | --- | --- | --- | --- |
| [Stable Fast 3D](https://github.com/Stability-AI/stable-fast-3d) | `ff21fc491b4dc5314bf6734c7c0dabd86b5f5bb2` | [stabilityai/stable-fast-3d](https://huggingface.co/stabilityai/stable-fast-3d), gated `model.safetensors` | Python >= 3.8; PyTorch matching CUDA; pinned `requirements.txt`; custom texture baker and UV unwrapper | About 6 GB VRAM | [Stability AI Community License](https://github.com/Stability-AI/stable-fast-3d/blob/main/LICENSE.md) |
| [TripoSR](https://github.com/VAST-AI-Research/TripoSR) | `107cefdc244c39106fa830359024f6a2f1c78871` | [stabilityai/TripoSR](https://huggingface.co/stabilityai/TripoSR), `model.ckpt` | Python >= 3.8; PyTorch matching CUDA; pinned `requirements.txt`, including CUDA-built `torchmcubes` and `xatlas` | About 6 GB VRAM | [MIT](https://github.com/VAST-AI-Research/TripoSR/blob/main/LICENSE) |

The exact TripoSR dependency versions installed by the Kaggle run are captured
in `g4p1_results/logs/versions_triposr.log`; model revisions and GPU details
are recorded in `manifest.json`. The two Python
environments are independent because the source projects pin different
`transformers` and `trimesh` versions. They never enter the game's frontend.
Kaggle's observed base image uses Python 3.13.15 and CUDA PyTorch 2.11.0,
while the upstream dependencies need an older Python environment. The runner
creates Python 3.12 virtual environments with `uv` and installs official CUDA
PyTorch 2.5.1 there. TripoSR's `torchmcubes` dependency is pinned to
`a9ac95aa329957ba646e7bb057f825f5dfa77f38` and built without isolation
against that PyTorch, as its current [README](https://github.com/tatsy/torchmcubes)
requires. Its other requirements remain those of the pinned TripoSR checkout.
The runner also installs CPU `onnxruntime` for TripoSR's `rembg` step, because
the current unpinned `rembg` dependency does not pull that optional runtime.
Kaggle's headless display requires `xvfb-run` for TripoSR's OpenGL bake.
The pinned TripoSR source has a CUDA device mismatch in `tsr/bake_texture.py`;
`patch_triposr_bake.py` applies a minimal, checked, idempotent fix before
inference. It moves atlas position samples to the scene-code device and copies
the color result to CPU before NumPy conversion.

SF3D's official checkpoint requires the account holder to accept its Hugging
Face conditions and supply a read token. The community license also has
commercial registration and revenue conditions; confirm the game's use against
the complete license before release. TripoSR's project and checkpoint are MIT
licensed; retain the copyright and license notice when redistributing its
software. The source sheet is supplied by the game team; its art rights remain
the team's responsibility. Do not commit the multi-GB pretrained checkpoints.

## Run on Kaggle

1. Open `tools/g4p1/g4p1_kaggle.ipynb` in a private Kaggle notebook. Enable
   Internet and a T4 or P100 GPU. Kaggle's [notebook documentation](https://www.kaggle.com/docs/notebooks)
   describes the accelerator and Internet settings.
2. If SF3D access has been granted, add an `HF_TOKEN` Kaggle secret with read
   access. Do not paste the token into notebook cells, logs, commits, or a PR.
3. Run the notebook cells. It clones each accessible official repository at
   the commit above, installs each in its own environment, downloads its exact
   official model revision, calls its `run.py`, validates the resulting GLB,
   and renders available candidates from four angles with Blender.
4. Download `g4p1_deliverables.zip` from the Kaggle Output tab. The archive
   excludes virtual environments, upstream clones, and checkpoints.

The actual T4 run on 2026-10-24 used a Tesla T4 (14.56 GiB), Python 3.13.15
in Kaggle and a Python 3.12 venv with CUDA PyTorch 2.5.1 for TripoSR. Its
official checkpoint revision was
`5b521936b01fbe1890f6f9baed0254ab6351c04a`. The [private Kaggle notebook](https://www.kaggle.com/code/syedasubhana/g4-p1-street-barricade-strategist-reconstruction)
contains the actual run manifest, logs, renders, validation reports, and
download archive. The final pipeline manifest reports
`triposr: structurally_valid; visual review pending` and
`sf3d: not_run: gated Hugging Face checkpoint requires accepted access and HF_TOKEN`.
An attempt through Stability AI's public SF3D Space also failed at `/run_button`
with the Space's generic Gradio `AppError`, including with an alpha-masked
reference; no SF3D mesh was produced. The official checkpoint cannot be run
until access is accepted and a read token is supplied as a Kaggle secret.

The official invocation used by the runner is equivalent to:

```sh
python run.py front_clean.png --output-dir sf3d --texture-resolution 1024 --remesh_option none
python run.py front_clean.png --output-dir triposr --bake-texture --texture-resolution 1024 --model-save-format obj
```

Both commands additionally receive the downloaded local checkpoint path through
the option documented in their respective `run.py` files. TripoSR's baked OBJ
and PNG are converted to a textured GLB by `convert_triposr.py`, because its
bake path exports through `xatlas`. Any failed stage is recorded in the manifest
and `logs/`; one pipeline does not suppress the other.

## Selection and refinement gate

Compare the candidate renders and the G3 sheet side by side. Do not select a
generic face, fused scarf or satchel, wrong hair silhouette, or distorted
proportions. Score each candidate out of 100:

| Criterion | Points | SF3D | TripoSR |
| --- | ---: | ---: | ---: |
| Face and layered brown hair | 35 | No result | 12 — generic, flattened face and clumped hair |
| Navy jacket, red scarf, leather satchel, cargo trousers, tricolor sneakers | 25 | No result | 15 — main colors read, satchel and details blur together |
| Body proportions and silhouette | 20 | No result | 11 — recognizable figure, weak G3 proportions and back |
| Geometry and textures | 10 | No result | 5 — UV bake works, soft surface and open mesh |
| Game readiness | 10 | No result | 2 — 65,593 triangles, unrigged, no animation topology |
| **Total** | **100** | **No result** | **45 — rejected** |

The Blender cleaned candidate is Y-up, 1.70 m tall with feet at Y=0,
3,208,436 bytes, one mesh and one textured UV material. Its SHA-256 is
`a0ff8c1fecaae8963ffabda421b1fd9928bdee55d893178dafaefe2888471e5c`.
The structural checker found 65,593 triangles, 53,289 vertices, and no
watertight mesh. The four-angle comparison is `visual_comparison.png` in the
Kaggle archive. This is evidence of the trial, not acceptance of the asset.

After choosing a candidate, run `blender_review.py` with `--output` to
normalize it to about 1.70 m, place the feet on the ground plane, preserve
the imported UVs and material slots, and cap oversized texture images at
1024 px. The script also makes four view renders. Inspect those renders before
accepting the model: the review camera assumes TripoSR's converted front is
Blender +X; another model may use a different heading. Face, hair, clothing, accessory geometry,
animation topology, and any decimation require visual review and manual repair.
The current game's `src/character/player.js` is an unrigged procedural
prototype; a shared humanoid rig and live asset swap are separate integration
work, and rig compatibility cannot be claimed from an unrigged reconstruction.

Run `validate_glb.py` on the final exported asset. The report covers triangles,
vertices, extents, UV presence, textured meshes, and file hash. Then run
`npm install` and `npm run dev` at the game root and open
`/tools/g4p1/viewer/` to load the GLB in the isolated Three.js reviewer.
Check its texture appearance, orientation, ground contact, and performance.
Aim for roughly 10K–20K triangles, few materials, and 1024 px textures where
the G3 resemblance survives; keep a more detailed asset if reducing it would
damage the face, hair, scarf, satchel, or shoe shapes.

Only after a visually accepted, refined model passes these checks should it
be named `street_barricade_strategist.glb` and placed in the game repository.
