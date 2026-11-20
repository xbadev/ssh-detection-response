"""Helpers for loading the hyphen-named scripts as modules under test."""

import importlib.util
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DETECTOR = REPO / "04-detection-monitoring" / "detector" / "ssh-bruteforce-detector.py"
RESPONDER = REPO / "05-automated-response" / "responder" / "ssh-responder.py"


def load(path: Path, name: str, env: dict):
    """
    Import a script as a fresh module after applying `env`.

    Both scripts read their configuration from environment variables at
    import time, so every test that needs different settings loads its
    own copy with its own env.
    """
    old = {k: os.environ.get(k) for k in env}
    os.environ.update({k: str(v) for k, v in env.items()})
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
