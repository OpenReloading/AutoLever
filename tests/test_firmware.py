"""Native build and run of the press logic test and the bench image's relay test (firmware/tests/).

Needs a C++ compiler; skipped where it is missing.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

FIRMWARE = Path(__file__).resolve().parent.parent / "firmware"

CXX = shutil.which("g++") or shutil.which("c++")

pytestmark = pytest.mark.skipif(CXX is None, reason="no C++ compiler")


@pytest.mark.parametrize("sources", [
    ["tests/logic_test.cpp", "src/logic.cpp"],
    ["tests/bench_test.cpp"],
], ids=["press", "bench"])
def test_native(tmp_path, sources):
    exe = tmp_path / "test"
    build = subprocess.run(
        [CXX or "c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-o", str(exe),
         *(str(FIRMWARE / s) for s in sources)],
        capture_output=True, text=True, timeout=120, check=False,
    )
    assert build.returncode == 0, build.stderr
    run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30, check=False)
    assert run.returncode == 0, run.stdout
    assert run.stdout.strip() == "ok"
