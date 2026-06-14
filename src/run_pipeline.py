from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    subprocess.run([sys.executable, str(REPO_ROOT / "src" / script)], check=True)


def main() -> None:
    run("clean_data.py")
    run("visualize.py")
    run("regression.py")
    run("build_static_dashboard.py")
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
