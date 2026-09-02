#!/usr/bin/env python3
"""One-click Google Colab launcher for the Rich Future Voice web build."""

from __future__ import annotations

from html import escape
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
LOG_PATH = Path("/content/rich_future_voice_backend.log")
DATA_DIR = Path(os.environ.get("RICH_FUTURE_DATA_DIR", "/content/rich_future_voice_data"))
BUN = Path("/root/.bun/bin/bun")
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


def install_bun() -> None:
    if not BUN.exists():
        run(["bash", "-lc", "curl -fsSL https://bun.sh/install | bash"])
    run([str(BUN), "--version"])


def build_branded_frontend() -> None:
    source_url = os.environ.get("RICH_FUTURE_SOURCE_URL", "").strip()
    expected_stamp = f"revision={revision()}\nbrand=1\nsource={source_url}\n"
    if BUILD_STAMP.exists() and BUILD_STAMP.read_text(encoding="utf-8") == expected_stamp:
        print("  Giao diện Rich Future đã được dựng — bỏ qua.")
        return

    build_env = os.environ.copy()
    build_env["PATH"] = f"{BUN.parent}{os.pathsep}{build_env.get('PATH', '')}"
    build_env["VITE_RICH_FUTURE_BRAND"] = "1"
    if source_url:
        build_env["VITE_RICH_FUTURE_SOURCE_URL"] = source_url

    run([str(BUN), "install", "--frozen-lockfile"], env=build_env)
    run([str(BUN), "run", "--cwd", "frontend", "build"], env=build_env)
    BUILD_STAMP.write_text(expected_stamp, encoding="utf-8")


def install_backend() -> None:
    expected_stamp = f"revision={revision()}\npython={sys.version}\n"
    if INSTALL_STAMP.exists() and INSTALL_STAMP.read_text(encoding="utf-8") == expected_stamp:
        print("  Backend đã được cài — bỏ qua.")
        return

    if not shutil.which("uv"):
        run([sys.executable, "-m", "pip", "install", "-q", "uv"])

    run(
        [
            "uv",
            "pip",
            "install",
            "--system",
            "--no-cache",
            "--constraint",
            "deploy/torch-constraints.txt",
            ".",
        ]
    )

    (ROOT / ".venv").mkdir(exist_ok=True)
    run([sys.executable, str(ROOT / "scripts" / "setup.py")])
    run(
        [
            sys.executable,
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
    from huggingface_hub import snapshot_download

    path = snapshot_download("k2-fsa/OmniVoice")
    print(f"  Model sẵn sàng tại {path}")


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
            "PYTHONUNBUFFERED": "1",
        }
    )

    log = LOG_PATH.open("ab")
    process = subprocess.Popen(
        [
            sys.executable,
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


def open_colab_window() -> None:
    from google.colab import output
    from IPython.display import HTML, display

    proxy_url = None
    try:
        proxy_url = output.eval_js(f"google.colab.kernel.proxyPort({PORT})")
    except Exception as exc:
        print(f"  Colab chưa tạo được URL riêng: {exc}")

    if proxy_url:
        safe_url = escape(str(proxy_url), quote=True)
        display(
            HTML(
                '<div style="margin:16px 0;padding:18px;border:1px solid #14b8a6;'
                'border-radius:12px;background:#071827">'
                f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer" '
                'style="display:inline-block;padding:12px 20px;border-radius:8px;'
                'background:#14b8a6;color:#03111d;font-weight:700;text-decoration:none">'
                'MỞ RICH FUTURE VOICE ↗</a>'
                f'<div style="margin-top:10px;color:#b8d8df">{safe_url}</div></div>'
            )
        )

    print("\n✓ Rich Future Voice đã sẵn sàng. Bấm nút phía trên hoặc dùng ứng dụng bên dưới.")
    output.serve_kernel_port_as_iframe(PORT, width="100%", height="900")


def main() -> None:
    stage("Kiểm tra GPU")
    if shutil.which("nvidia-smi"):
        run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    else:
        print("  Không thấy GPU. Hãy chọn Runtime → Change runtime type → T4 GPU.")

    stage("Chuẩn bị môi trường Colab")
    install_system_tools()
    install_bun()

    stage("Dựng giao diện Rich Future")
    build_branded_frontend()

    stage("Cài bộ máy giọng nói")
    install_backend()
    load_hugging_face_token()

    stage("Tải model mặc định")
    cache_default_model()

    stage("Khởi động Rich Future Voice")
    info = launch_backend()
    print(f"  Backend: {info}")
    open_colab_window()


if __name__ == "__main__":
    main()
