"""Run the two official image-to-3D entry points in isolated Kaggle environments.

Run from the game repository root on a Kaggle GPU notebook with internet enabled.
The official model loaders download checkpoints from Hugging Face. SF3D additionally
requires a Hugging Face account that has accepted its model terms and an HF_TOKEN
Kaggle secret. No checkpoint or secret is written to this repository.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "assets/characters/street_barricade_strategist/reference/front_clean.png"
OUT = Path(os.environ.get("G4P1_OUTPUT", "/kaggle/working/g4p1_results"))
UPSTREAM = OUT / "upstream"
REPOS = {
    "triposr": ("https://github.com/VAST-AI-Research/TripoSR", "107cefdc244c39106fa830359024f6a2f1c78871"),
    "sf3d": ("https://github.com/Stability-AI/stable-fast-3d", "ff21fc491b4dc5314bf6734c7c0dabd86b5f5bb2"),
}
TORCHMCUBES_COMMIT = "a9ac95aa329957ba646e7bb057f825f5dfa77f38"


def execute(name: str, cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> bool:
    print(f"[{name}] {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    (OUT / "logs" / f"{name}.log").write_text(result.stdout, encoding="utf-8")
    print(result.stdout[-5000:], flush=True)
    print(f"[{name}] exit={result.returncode}", flush=True)
    return result.returncode == 0


def has_torch(python: Path) -> bool:
    check = subprocess.run([str(python), "-c", "import torch; assert torch.cuda.is_available()"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return check.returncode == 0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not INPUT.is_file():
        raise FileNotFoundError(f"Run tools/g4p1/extract_reference.py first: {INPUT}")
    reference_out = OUT / "reference"
    reference_out.mkdir(exist_ok=True)
    for image_name in ("front_clean", "three_quarter", "side", "back"):
        shutil.copy2(INPUT.parent / f"{image_name}.png", reference_out / f"{image_name}.png")
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("Kaggle base image must provide CUDA PyTorch") from exc
    if not torch.cuda.is_available():
        raise RuntimeError("No CUDA GPU is available; select a Kaggle GPU accelerator")

    manifest = {
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "gpu_total_vram_bytes": torch.cuda.get_device_properties(0).total_memory,
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "upstream_commits": {key: item[1] for key, item in REPOS.items()},
        "runs": {},
    }
    if manifest["gpu_total_vram_bytes"] < 6 * 1024**3:
        raise RuntimeError("GPU has under 6 GiB VRAM; both upstream READMEs cite ~6 GB")

    UPSTREAM.mkdir(exist_ok=True)
    for name, (url, commit) in REPOS.items():
        if name == "sf3d" and not os.environ.get("HF_TOKEN"):
            manifest["runs"][name] = "not_run: gated Hugging Face checkpoint requires accepted access and HF_TOKEN"
            continue
        checkout = UPSTREAM / name
        if not checkout.exists():
            if not execute(f"clone_{name}", ["git", "clone", "--depth", "1", url, str(checkout)]):
                manifest["runs"][name] = "clone_failed"
                continue
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
        if actual != commit:
            if not execute(f"fetch_{name}", ["git", "fetch", "--depth", "1", "origin", commit], cwd=checkout):
                manifest["runs"][name] = f"pinned_commit_unavailable: {actual}"
                continue
            if not execute(f"checkout_{name}", ["git", "checkout", "--detach", commit], cwd=checkout):
                manifest["runs"][name] = "checkout_failed"
                continue

        venv = OUT / "venvs" / name
        py = venv / "bin" / "python"
        if not py.exists():
            if sys.version_info >= (3, 13) and Path("/usr/bin/python3.12").is_file() and shutil.which("uv"):
                venv_cmd = ["uv", "venv", "--python", "/usr/bin/python3.12", "--seed", "--clear", str(venv)]
            else:
                venv_cmd = [sys.executable, "-m", "venv", "--system-site-packages", str(venv)]
            if not execute(f"venv_{name}", venv_cmd):
                manifest["runs"][name] = "venv_failed"
                continue
        if not has_torch(py):
            if not shutil.which("uv") or not execute(
                f"torch_{name}",
                ["uv", "pip", "install", "--python", str(py), "torch==2.5.1", "torchvision==0.20.1",
                 "--index-url", "https://download.pytorch.org/whl/cu121"],
            ):
                manifest["runs"][name] = "CUDA_PyTorch_install_failed"
                continue
        setup_version = "setuptools==69.5.1"
        if not execute(f"build_tools_{name}", [str(py), "-m", "pip", "install", "-U", setup_version, "wheel"]):
            manifest["runs"][name] = "build_tools_failed"
            continue
        requirements = checkout / "requirements.txt"
        if name == "triposr":
            # Upstream's torchmcubes now requires an installed torch in its build
            # environment; its README explicitly requires --no-build-isolation.
            filtered = OUT / "triposr_requirements_without_torchmcubes.txt"
            filtered.write_text("numpy==1.26.4\n" + "".join(
                line for line in requirements.read_text(encoding="utf-8").splitlines(keepends=True)
                if "github.com/tatsy/torchmcubes" not in line
            ), encoding="utf-8")
            requirements = filtered
        if not execute(f"install_{name}", [str(py), "-m", "pip", "install", "-r", str(requirements)], cwd=checkout):
            manifest["runs"][name] = "dependency_install_failed"
            continue
        if name == "triposr":
            if not execute("torchmcubes_build_tools", [str(py), "-m", "pip", "install", "scikit-build-core>=1.0", "pybind11>=2.10"]):
                manifest["runs"][name] = "torchmcubes_build_tools_failed"
                continue
            source = f"git+https://github.com/tatsy/torchmcubes.git@{TORCHMCUBES_COMMIT}"
            if not execute("torchmcubes", [str(py), "-m", "pip", "install", "--no-build-isolation", source]):
                manifest["runs"][name] = "torchmcubes_build_failed"
                continue
        execute(f"versions_{name}", [str(py), "-m", "pip", "freeze"])
        run_out = OUT / name
        run_out.mkdir(exist_ok=True)
        env = os.environ.copy()
        env["HF_HUB_DISABLE_TELEMETRY"] = "1"

        if name == "sf3d":
            if not env.get("HF_TOKEN"):
                manifest["runs"][name] = "not_run: gated Hugging Face checkpoint requires accepted access and HF_TOKEN"
                continue
            model_id, weight, model_option = "stabilityai/stable-fast-3d", "model.safetensors", "--pretrained-model"
        else:
            model_id, weight, model_option = "stabilityai/TripoSR", "model.ckpt", "--pretrained-model-name-or-path"
        checkpoint = OUT / "checkpoints" / name
        if not execute(f"checkpoint_{name}", [str(py), str(ROOT / "tools/g4p1/download_checkpoint.py"),
                                               model_id, weight, str(checkpoint)], env=env):
            manifest["runs"][name] = "official_checkpoint_download_failed: inspect access/network logs"
            continue
        manifest.setdefault("model_revisions", {})[name] = json.loads(
            (checkpoint / "revision.json").read_text(encoding="utf-8")
        )["revision"]
        if name == "sf3d":
            cmd = [str(py), "run.py", str(INPUT), "--output-dir", str(run_out),
                   "--texture-resolution", "1024", "--remesh_option", "none",
                   model_option, str(checkpoint)]
        else:
            cmd = [str(py), "run.py", str(INPUT), "--output-dir", str(run_out),
                   "--bake-texture", "--texture-resolution", "1024",
                   "--model-save-format", "obj", model_option, str(checkpoint)]
        if not execute(f"inference_{name}", cmd, cwd=checkout, env=env):
            manifest["runs"][name] = "inference_failed: inspect logs"
            continue

        if name == "sf3d":
            glb = run_out / "0" / "mesh.glb"
        else:
            glb = run_out / "0" / "mesh.glb"
            if not execute("convert_triposr", [str(py), str(ROOT / "tools/g4p1/convert_triposr.py"),
                                                str(run_out / "0" / "mesh.obj"),
                                                str(run_out / "0" / "texture.png"), str(glb)]):
                manifest["runs"][name] = "mesh_conversion_failed"
                continue
        if not glb.is_file():
            manifest["runs"][name] = "missing_glb"
            continue
        if execute(f"validate_{name}", [str(py), str(ROOT / "tools/g4p1/validate_glb.py"),
                                          str(glb), "--output", str(run_out / "validation.json")]):
            manifest["runs"][name] = "structurally_valid; visual review pending"
            blender = shutil.which("blender")
            if blender:
                if not execute(f"render_{name}", [blender, "-b", "-t", "2", "--python",
                                                   str(ROOT / "tools/g4p1/blender_review.py"), "--",
                                                   "--input", str(glb), "--render-dir", str(run_out / "renders")]):
                    manifest["runs"][name] += "; Blender render failed"
            else:
                manifest["runs"][name] += "; Blender unavailable"
        else:
            manifest["runs"][name] = "structural_validation_failed"

    comparison_python = OUT / "venvs" / "triposr" / "bin" / "python"
    if comparison_python.exists() and any((OUT / model / "renders").exists() for model in REPOS):
        execute("comparison", [str(comparison_python), str(ROOT / "tools/g4p1/make_comparison.py"),
                               str(OUT), "--output", str(OUT / "visual_comparison.png")])
    manifest["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
