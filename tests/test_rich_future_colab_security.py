"""Security contract for the public Rich Future Colab notebook."""

from pathlib import Path
import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT / "backend"))


def test_colab_launcher_pins_network_executables_and_model_revision():
    source = (ROOT / "scripts" / "colab_one_click.py").read_text(encoding="utf-8")

    assert "curl -fsSL https://bun.sh/install | bash" not in source
    assert 'BUN_VERSION = "1.3.14"' in source
    assert "snapshot_download(repo_id, revision=model_revision)" in source
    assert '"RICH_FUTURE_LOCKDOWN": "1"' in source


def test_colab_security_headers_are_applied_without_replacing_stricter_values():
    from main import ColabSecurityHeadersMiddleware

    app = FastAPI()

    @app.get("/")
    def index():
        return {"ok": True}

    app.add_middleware(ColabSecurityHeadersMiddleware)
    response = TestClient(app).get("/")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert "object-src 'none'" in response.headers["content-security-policy"]
    assert "colab.research.google.com" in response.headers["content-security-policy"]
    assert response.headers["permissions-policy"] == (
        "camera=(), geolocation=(), microphone=(self)"
    )
