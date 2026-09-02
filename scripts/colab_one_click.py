#!/usr/bin/env python3
"""One-click Google Colab launcher for the Rich Future Voice web build."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PORT = 3900
HEALTH_URL = f"http://127.0.0.1:{PORT}/health"
WARMUP_URL = f"http://127.0.0.1:{PORT}/setup/warmup"
LOG_PATH = Path("/content/rich_future_voice_backend.log")
DATA_DIR = Path(os.environ.get("RICH_FUTURE_DATA_DIR", "/content/rich_future_voice_data"))
BUN_VERSION = "1.3.14"
UV_VERSION = "0.11.7"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
BUILD_STAMP = ROOT / "frontend" / "dist" / ".rich-future-colab-build"
INSTALL_STAMP = Path("/content/.rich_future_voice_backend_ready")


def stage(message: str) -> None:
    print(f"\n▶ {message}", flush=True)


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    shown = " ".join(command)
    print(f"  $ {shown}", flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def revision() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def health() -> dict | None:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=5) as response:
            return json.load(response)
    except Exception:
        return None


def install_system_tools() -> None:
    if shutil.which("ffmpeg") and shutil.which("lsof"):
        return
    run(["apt-get", "-qq", "update"])
    run(["apt-get", "-qq", "install", "-y", "ffmpeg", "libsndfile1", "lsof"])


def install_bun() -> Path:
    bun_path = shutil.which("bun")
    installed_version = ""
    if bun_path:
        installed_version = subprocess.check_output(
            [bun_path, "--version"], text=True
        ).strip()
    if installed_version != BUN_VERSION:
        npm = shutil.which("npm")
        if not npm:
            raise RuntimeError("Colab không có npm để cài Bun đã khóa phiên bản.")
        run([npm, "install", "--global", f"bun@{BUN_VERSION}"])
        bun_path = shutil.which("bun")
    if not bun_path:
        raise RuntimeError("Không tìm thấy Bun sau khi cài đặt.")
    run([bun_path, "--version"])
    return Path(bun_path)


def build_branded_frontend(bun: Path) -> None:
    source_url = os.environ.get("RICH_FUTURE_SOURCE_URL", "").strip()
    expected_stamp = f"revision={revision()}\nbrand=1\nui=clone-only\nsource={source_url}\n"
    if BUILD_STAMP.exists() and BUILD_STAMP.read_text(encoding="utf-8") == expected_stamp:
        print("  Giao diện Rich Future đã được dựng — bỏ qua.")
        return

    build_env = os.environ.copy()
    build_env["PATH"] = f"{bun.parent}{os.pathsep}{build_env.get('PATH', '')}"
    build_env["VITE_RICH_FUTURE_BRAND"] = "1"
    if source_url:
        build_env["VITE_RICH_FUTURE_SOURCE_URL"] = source_url

    run([str(bun), "install", "--frozen-lockfile"], env=build_env)
    run([str(bun), "run", "--cwd", "frontend", "build"], env=build_env)
    BUILD_STAMP.write_text(expected_stamp, encoding="utf-8")


def install_backend() -> None:
    expected_stamp = (
        f"revision={revision()}\npython={sys.version}\nuv={UV_VERSION}\nlock=uv.lock\n"
    )
    if (
        VENV_PYTHON.exists()
        and INSTALL_STAMP.exists()
        and INSTALL_STAMP.read_text(encoding="utf-8") == expected_stamp
    ):
        print("  Backend đã được cài — bỏ qua.")
        return

    uv_path = shutil.which("uv")
    installed_uv = ""
    if uv_path:
        installed_uv = subprocess.check_output([uv_path, "--version"], text=True).split()[1]
    if installed_uv != UV_VERSION:
        run([sys.executable, "-m", "pip", "install", "-q", f"uv=={UV_VERSION}"])

    # uv.lock is the single Python dependency contract. --frozen refuses to
    # resolve or silently rewrite it; --no-dev keeps the public Colab runtime
    # lean while still installing every production dependency at its exact
    # locked version and verified artifact hash.
    run(
        [
            "uv",
            "sync",
            "--frozen",
            "--no-dev",
        ]
    )

    if not VENV_PYTHON.exists():
        raise RuntimeError("uv sync không tạo được môi trường Python đã khóa.")
    run([str(VENV_PYTHON), str(ROOT / "scripts" / "setup.py")])
    run(
        [
            str(VENV_PYTHON),
            "-c",
            "import torch, torchaudio, fastapi, uvicorn, transformers; "
            "from omnivoice.models.omnivoice import OmniVoice; "
            "print('CUDA:', torch.cuda.is_available(), '| torch:', torch.__version__)",
        ]
    )
    INSTALL_STAMP.write_text(expected_stamp, encoding="utf-8")


def load_hugging_face_token() -> None:
    try:
        from google.colab import userdata

        token = userdata.get("HF_TOKEN")
        if token:
            os.environ["HF_TOKEN"] = token
            print("  Đã nạp HF_TOKEN từ Colab Secrets.")
    except Exception:
        print("  Không có HF_TOKEN — voice cloning/TTS vẫn hoạt động bình thường.")


def cache_default_model() -> None:
    if os.environ.get("RICH_FUTURE_SKIP_MODEL_DOWNLOAD") == "1":
        return
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(ROOT / 'backend')!r}); "
        "from huggingface_hub import snapshot_download; "
        "from huggingface_hub.constants import HF_HUB_CACHE; "
        "from services.hf_revisions import remember_revision, revision_for; "
        "repo_id='k2-fsa/OmniVoice'; "
        "model_revision=revision_for(repo_id); "
        "path=snapshot_download(repo_id, revision=model_revision); "
        "remember_revision(repo_id, model_revision, str(HF_HUB_CACHE)); "
        "print(f'  Model sẵn sàng tại {path}')"
    )
    run([str(VENV_PYTHON), "-c", code])


def start_model_warmup() -> None:
    """Load the model in the background while the user prepares their script."""
    try:
        request = urllib.request.Request(WARMUP_URL, data=b"", method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
        print(f"  Làm nóng model: {result.get('status', 'started')}")
    except Exception as exc:
        # Warmup is an optimization only; generation can still cold-load.
        print(f"  Không thể làm nóng model nền ({exc}); ứng dụng vẫn dùng được.")


def launch_backend() -> dict:
    current = health()
    if current:
        return current

    subprocess.run(
        ["bash", "-lc", f"kill -9 $(lsof -t -i:{PORT}) 2>/dev/null || true"],
        check=False,
    )
    time.sleep(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    backend_env = os.environ.copy()
    backend_env.update(
        {
            "OMNIVOICE_SERVER_MODE": "1",
            "OMNIVOICE_DATA_DIR": str(DATA_DIR),
            "OMNIVOICE_ANALYTICS_DISABLED": "1",
            "RICH_FUTURE_LOCKDOWN": "1",
            "PYTHONUNBUFFERED": "1",
        }
    )

    log = LOG_PATH.open("ab")
    process = subprocess.Popen(
        [
            str(VENV_PYTHON),
            "-m",
            "uvicorn",
            "main:app",
            "--app-dir",
            "backend",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
        cwd=ROOT,
        env=backend_env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )

    deadline = time.time() + 300
    while time.time() < deadline:
        if process.poll() is not None:
            break
        current = health()
        if current:
            return current
        print(".", end="", flush=True)
        time.sleep(3)

    try:
        tail = "".join(LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines(True)[-50:])
    except OSError:
        tail = "Không đọc được log."
    raise RuntimeError(f"Backend không khởi động được.\n\n{tail}\nLog: {LOG_PATH}")


def main() -> None:
    stage("Kiểm tra GPU")
    if shutil.which("nvidia-smi"):
        run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    else:
        print("  Không thấy GPU. Hãy chọn Runtime → Change runtime type → T4 GPU.")

    stage("Chuẩn bị môi trường Colab")
    install_system_tools()
    bun = install_bun()

    stage("Dựng giao diện Rich Future")
    build_branded_frontend(bun)

    stage("Cài bộ máy giọng nói")
    install_backend()
    load_hugging_face_token()

    stage("Tải model mặc định")
    cache_default_model()

    stage("Khởi động Rich Future Voice")
    info = launch_backend()
    start_model_warmup()
    print(f"  Backend: {info}")
    print("\n✓ Backend Rich Future Voice đã sẵn sàng trên cổng 3900.")


if __name__ == "__main__":
    main()
