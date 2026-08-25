"""Reassemble repository-owned PDFs into the rendered website."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "_file_parts"
OUTPUT = ROOT / "_site"


def main() -> None:
    manifest = json.loads((PARTS / "manifest.json").read_text(encoding="utf-8"))
    for record in manifest:
        encoded = "".join(
            (PARTS / chunk).read_text(encoding="ascii")
            for chunk in record["chunks"]
        )
        payload = base64.b64decode(encoded, validate=True)

        if len(payload) != record["size"]:
            raise ValueError(f'{record["output"]}: reconstructed size mismatch')
        digest = hashlib.sha256(payload).hexdigest()
        if digest != record["sha256"]:
            raise ValueError(f'{record["output"]}: reconstructed checksum mismatch')

        destination = OUTPUT / record["output"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)


if __name__ == "__main__":
    main()
