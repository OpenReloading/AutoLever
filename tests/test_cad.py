"""Render checks of cad/lee_app_handle_adapter.scad: the parameter guards and the print_plate spacing.

Needs OpenSCAD (installed in the dev container); skipped where it is missing.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

SCAD = Path(__file__).resolve().parent.parent / "cad" / "lee_app_handle_adapter.scad"

pytestmark = pytest.mark.skipif(shutil.which("openscad") is None, reason="openscad not installed")


def render(out: Path, **params) -> subprocess.CompletedProcess:
    define = [f"-D{k}={v}" for k, v in params.items()]
    return subprocess.run(
        ["openscad", "-o", str(out), *define, str(SCAD)],
        capture_output=True, text=True, timeout=600, check=False,
    )


def bodies(stl: Path) -> int:
    """Connected bodies of an ASCII STL: triangles that share a vertex belong to one body."""
    parent: dict[tuple[str, ...], tuple[str, ...]] = {}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    triangle: list[tuple[str, ...]] = []
    for line in stl.read_text().splitlines():
        if m := re.match(r"\s*vertex\s+(\S+)\s+(\S+)\s+(\S+)", line):
            v = m.groups()
            parent.setdefault(v, v)
            triangle.append(v)
            if len(triangle) == 3:
                parent[find(triangle[1])] = find(triangle[0])
                parent[find(triangle[2])] = find(triangle[0])
                triangle = []
    return len({find(v) for v in parent})


@pytest.mark.parametrize("params", [
    {"arm_r": 23, "arm_x": 0},
    {"arm_r": 23, "arm_x": 1},
    {"arm_r": 30, "arm_x": 0, "eye_extra": 10},
])
def test_pivot_eye_overlapping_a_clamp_corner_is_rejected(tmp_path, params):
    result = render(tmp_path / "out.stl", **params)
    assert result.returncode != 0
    assert "pivot eye overlaps a clamp corner: increase arm_r, move arm_x, or reduce eye_extra" in result.stderr


def test_default_print_plate_is_two_bodies(tmp_path):
    result = render(tmp_path / "out.stl")
    assert result.returncode == 0, result.stderr
    assert bodies(tmp_path / "out.stl") == 2


def test_print_plate_with_arm_beyond_a_long_clamp_is_two_bodies(tmp_path):
    # L = 50 / tan(30 deg) = 86.6 mm, more than 2 * (eye_r + 10) = 46 mm
    result = render(tmp_path / "out.stl", arm_x=1.5, gap_wide=60)
    assert result.returncode == 0, result.stderr
    assert bodies(tmp_path / "out.stl") == 2
