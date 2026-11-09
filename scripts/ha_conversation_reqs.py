"""Print the pip requirements HA's conversation stack needs (CI helper).

The integration declares a manifest dependency on ``conversation``; its
runtime deps (hassil, intents, audio libs) are not part of the
pytest-homeassistant-custom-component install. Reading the pins from the
installed HA core manifests keeps them in lock-step with that HA version.
"""
from __future__ import annotations

import json
import pathlib

import homeassistant

COMPONENTS = ("conversation", "assist_pipeline", "ffmpeg", "stt", "tts", "intent")


def main() -> None:
    base = pathlib.Path(homeassistant.__file__).parent / "components"
    reqs: set[str] = set()
    for comp in COMPONENTS:
        manifest = base / comp / "manifest.json"
        if manifest.exists():
            reqs.update(json.loads(manifest.read_text()).get("requirements", []))
    print(" ".join(sorted(reqs)))


if __name__ == "__main__":
    main()
