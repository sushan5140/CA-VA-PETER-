# G4.P1 — Street Barricade Strategist reconstruction

## Status

**Pipeline prepared; character model generation remains incomplete.** No model is
accepted until both its GLB structure and resemblance to the locked G3 sheet
have been checked. The development branch intentionally contains no invented
GLB, model renders, or scores.

The authoritative sheet is
[`assets/characters/street_barricade_strategist/reference/g3_character_sheet.png`](../assets/characters/street_barricade_strategist/reference/g3_character_sheet.png).
Its SHA-256 is `4016419d22f2174031175f01a5a8e72196105f00e1da32d66ec8bcc5983bb32e`.
`tools/g4p1/extract_reference.py` produced the view and detail crops with
recorded coordinates in `crops.json`. The front input has the same character
pixels, apart from a small background-only patch that removes stray sheet text.
Both inference runs use that same `front_clean.png` input and their own
documented background-removal step.

## Upstream audit

| Pipeline | Source commit | Official checkpoint | Python and requirements | Documented default memory | License |
| --- | --- | --- | --- | --- | --- |
| [Stable Fast 3D](https://github.com/Stability-AI/stable-fast-3d) | `ff21fc491b4dc5314bf6734c7c0dabd86b5f5bb2` | [stabilityai/stable-fast-3d](https://huggingface.co/stabilityai/stable-fast-3d), gated `model.safetensors` | Python >= 3.8; PyTorch matching CUDA; pinned `requirements.txt`; custom texture baker and UV unwrapper | About 6 GB VRAM | [Stability AI Community License](https://github.com/Stability-AI/stable-fast-3d/blob/main/LICENSE.md) |
| [TripoSR](https://github.com/VAST-AI-Research/TripoSR) | `107cefdc244c39106fa830359024f6a2f1c78871` | [stabilityai/TripoSR](https://huggingface.co/stabilityai/TripoSR), `model.ckpt` | Python >= 3.8; PyTorch matching CUDA; pinned `requirements.txt`, including CUDA-built `torchmcubes` and `xatlas` | About 6 GB VRAM | [MIT](https://github.com/VAST-AI-Research/TripoSR/blob/main/LICENSE) |

The exact dependency versions installed by the Kaggle run are captured in
`g4p1_results/logs/versions_sf3d.log` and `versions_triposr.log`; model
revisions and GPU details are recorded in `manifest.json`. The two Python
environments are independent because the source projects pin different
`transformers` and `trimesh` versions. They never enter the game's frontend.
Kaggle's observed base image uses Python 3.13.15 and CUDA PyTorch 2.11.0,
while the upstream dependencies need an older Python environment. The runner
creates Python 3.12 virtual environments with `uv` and installs official CUDA
PyTorch 2.5.1 there. TripoSR's `torchmcubes` dependency is pinned to
`a9ac95aa329957ba646e7bb057f825f5dfa77f38` and built without isolation
against that PyTorch, as its current [README](https://github.com/tatsy/torchmcubes)
requires. Its other requirements remain those of the pinned TripoSR checkout.

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
3. Run the notebook cells. It clones both official repositories at the commits
   above, installs each in its own environment, downloads exact official model
   revisions, calls each project's `run.py`, validates the resulting GLBs, and
   renders available candidates from four angles with Blender.
4. Download `g4p1_deliverables.zip` from the Kaggle Output tab. The archive
   excludes virtual environments, upstream clones, and checkpoints.

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
| Face and layered brown hair | 35 | Pending | Pending |
| Navy jacket, red scarf, leather satchel, cargo trousers, tricolor sneakers | 25 | Pending | Pending |
| Body proportions and silhouette | 20 | Pending | Pending |
| Geometry and textures | 10 | Pending | Pending |
| Game readiness | 10 | Pending | Pending |

After choosing a candidate, run `blender_review.py` with `--output` to
normalize it to about 1.70 m, place the feet on the ground plane, preserve
the imported UVs and material slots, and cap oversized texture images at
1024 px. The script also makes four view renders. Inspect those renders before
accepting the model: the camera assumes front is Blender -Y and a single-view
model may use a different heading. Face, hair, clothing, accessory geometry,
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
