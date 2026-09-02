"""Security contract for the public Rich Future Colab notebook."""

import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT / "backend"))


def test_colab_launcher_pins_network_executables_and_model_revision():
    source = (ROOT / "scripts" / "colab_one_click.py").read_text(encoding="utf-8")

    assert "curl -fsSL https://bun.sh/install | bash" not in source
    assert 'BUN_VERSION = "1.3.14"' in source
    assert 'UV_VERSION = "0.11.7"' in source
    assert '"sync",' in source
    assert '"--frozen",' in source
    assert '"--no-dev",' in source
    assert '"--system",' not in source
    assert "snapshot_download(repo_id, revision=model_revision)" in source
    assert '"RICH_FUTURE_LOCKDOWN": "1"' in source
    assert 'WARMUP_URL = f"http://127.0.0.1:{PORT}/setup/warmup"' in source


def test_public_notebook_pins_the_reviewed_application_commit():
    notebook = json.loads(
        (ROOT / "notebooks" / "Rich_Future_Voice_Colab.ipynb").read_text(
            encoding="utf-8"
        )
    )
    source = "".join(notebook["cells"][0]["source"])

    assert "ee8d17abc6bf27b2985429817fd47289872d1ac9" in source
    assert '"pull"' not in source
    assert "source_revision != SOURCE_REVISION" in source


def test_frontend_advisory_overrides_are_pinned_to_patched_releases():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package["overrides"] == {
        "@babel/core": "7.29.7",
        "brace-expansion": "5.0.9",
        "browserslist": "4.28.8",
        "undici": "7.29.0",
    }


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
