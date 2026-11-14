"""Render checks of cad/stamplc_box.scad: every part is one solid body, the outer size, the print orientation of the
USB plug, and the clearance asserts.

Needs OpenSCAD (installed in the dev container); skipped where it is missing.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from test_cad import bodies, solid_defects

SCAD = Path(__file__).resolve().parent.parent / "cad" / "stamplc_box.scad"

pytestmark = pytest.mark.skipif(shutil.which("openscad") is None, reason="openscad not installed")


def render(out: Path, part: str, **params) -> subprocess.CompletedProcess:
    define = [f"-D{k}={v}" for k, v in {"part": f'"{part}"', **params}.items()]
    return subprocess.run(
        ["openscad", "-o", str(out), *define, str(SCAD)],
        capture_output=True, text=True, timeout=600, check=False,
    )


def size(stl: Path) -> tuple[float, float, float]:
    v = [tuple(map(float, m.groups())) for line in stl.read_text().splitlines()
         if (m := re.match(r"\s*vertex\s+(\S+)\s+(\S+)\s+(\S+)", line))]
    return tuple(max(p[i] for p in v) - min(p[i] for p in v) for i in range(3))  # type: ignore[return-value]


@pytest.mark.parametrize("part", ["base", "lid", "estop_ring", "usb_plug"])
def test_part_is_one_solid_body(tmp_path, part):
    result = render(tmp_path / "out.stl", part)
    assert result.returncode == 0, result.stderr
    assert bodies(tmp_path / "out.stl") == 1
    assert solid_defects(tmp_path / "out.stl") == (0, 0)


def test_usb_plug_exports_flange_down(tmp_path):
    # on the bed: the flange, 16 - 2 * 0.2 + 2 * 2 = 19.6 mm wide; the body above it is 15.6 mm
    result = render(tmp_path / "plug.stl", "usb_plug")
    assert result.returncode == 0, result.stderr
    v = [tuple(map(float, m.groups())) for line in (tmp_path / "plug.stl").read_text().splitlines()
         if (m := re.match(r"\s*vertex\s+(\S+)\s+(\S+)\s+(\S+)", line))]
    z0 = min(p[2] for p in v)
    ys = [p[1] for p in v if p[2] == z0]
    assert max(ys) - min(ys) == pytest.approx(19.6, abs=0.01)


def test_default_box_size(tmp_path):
    # window 72.6 x 77.6 at x 70, 34 mm beside it; cavity 176.6 x 127.6; walls 2.6; rim 3 + 60, lid 3
    result = render(tmp_path / "base.stl", "base")
    assert result.returncode == 0, result.stderr
    assert size(tmp_path / "base.stl") == pytest.approx((181.8, 132.8, 63), abs=0.01)
    result = render(tmp_path / "lid.stl", "lid")
    assert result.returncode == 0, result.stderr
    # the lip stands 3 mm under the 3 mm plate
    assert size(tmp_path / "lid.stl") == pytest.approx((181.8, 132.8, 6), abs=0.01)


@pytest.mark.parametrize(("params", "message"), [
    ({"usb_notch": "[40,16]"}, "USB notch reaches the right wall"),
    ({"x_left": 60}, "E-STOP body overlaps the rail"),
    ({"estop_depth": 20}, "unit sits too low"),
    ({"rack_x0": 60}, "Wago rack reaches the right wall"),
])
def test_clearance_asserts(tmp_path, params, message):
    result = render(tmp_path / "out.stl", "base", **params)
    assert result.returncode != 0
    assert message in result.stderr
