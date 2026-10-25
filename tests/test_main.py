"""Unit tests of the project rules in main.py (wire labels, cable kinds, two wires per screw, build checks)."""
import json
import shutil

import pytest
import yaml

import main

PARTS = {
    "K1": {"kind": "socket", "ports": {"left": ["9"], "right": ["14"]}},
    "S2": {"kind": "button", "ports": {"top": ["1", "2"]}},
    "X-EN": {"kind": "wago", "ports": {"top": ["1", "2"]}},
    "D5": {"kind": "diode", "ports": {"top": ["A", "K"]}},
}


def wiring(*wires):
    return {"parts": PARTS, "steps": [{"id": "A", "wires": list(wires)}]}


def test_wires_on_one_screw_are_listed_together():
    assert main.screws(wiring(["1", "K1:9", "S2:1", "WH"], ["2", "K1:9", "S2:2", "BU"])) == {"K1:9": ["1", "2"], "S2:1": ["1"], "S2:2": ["2"]}


def test_wago_slots_and_diode_legs_are_not_screws():
    assert main.screws(wiring(["1", "K1:9", "X-EN:1", "WH"], ["2", "D5:K", "K1:14", "GY"], ["3", "D5:K", "D5:A", "DIODE"])) == {"K1:9": ["1"], "K1:14": ["2"]}


@pytest.mark.parametrize(("wire", "message"), [
    (["6", "K9:1", "S2:1", "WH"], "wire 6, from end K9:1: unknown part K9"),
    (["6", "S2:1", "K1:99", "WH"], "wire 6, to end K1:99: part K1 has no terminal 99"),
])
def test_a_wire_with_an_unknown_end_names_its_number_and_end(wire, message):
    with pytest.raises(ValueError, match=message):
        main.screws(wiring(wire))


@pytest.mark.parametrize(("end", "text"), [
    ("K1:9", "K1 terminal 9"),
    ("T1:3", "T1 terminal 3"),
    ("X-EN:2", "Wago X-EN (switched +24 V) slot 2"),
    ("B0:BN", "Home sensor B0, brown core"),
    ("D5:A", "Diode D5, plain leg, in its own 2-way Wago with this wire"),
    ("D6:K", "Diode D6, ring leg"),
    ("Y1:1", "Valve plug Y1 pin 1 (+)"),
    ("Y2:2", "Valve plug Y2 pin 2"),
    ("F1:1", "Fuse holder F1 tab 1"),
    ("J1:-", "DC jack J1 \u2212"),
    ("S3:1", "E-STOP button 1 (NC)"),
    ("S2:2", "STOP button 2 (NC)"),
    ("S0:3", "START button 3 (NO)"),
    ("QPM11:1", "Pressure switch 1"),
    ("UNKNOWN:1", "UNKNOWN 1"),
])
def test_label_names_the_terminal_in_words(end, text):
    assert main.label(end) == text


@pytest.mark.parametrize(("a", "b", "col", "kind"), [
    ("D5:K", "K1:9", "DIODE", "diode"),
    ("B0:BN", "K1:9", "WH", "sensor"),
    ("K1:9", "Y2:1", "BU", "valve"),
    ("K1:9", "X-M1:1", "GY", "leg"),
    ("K1:9", "QPM11:1", "BK", "field"),
    ("K1:9", "X-M1:1", "WH", "core"),
])
def test_cable_of_picks_the_cable_kind(a, b, col, kind):
    assert main.cable_of({}, a, b, col) == kind


def test_cable_text_skips_an_empty_awg():
    assert main.cable_text({"size": "0.5 mm²", "awg": "AWG 20"}) == "0.5 mm² · AWG 20"
    assert main.cable_text({"size": "as supplied", "awg": ""}) == "as supplied"


def test_connection_names_the_twin_ferrule_partner_but_not_for_a_diode_leg():
    w = {"cables": {"core": {"name": "Stranded wire", "size": "0.5 mm²", "awg": "AWG 20"}, "diode": {"name": "Diode", "size": "", "awg": ""}}}
    shared = {"K1:9": ["1", "2"], "X-EN:1": ["1"]}
    wire = main.connection(w, shared, "1", "K1:9", "X-EN:1", "WH")
    assert wire["la"] == "K1 terminal 9 · twin ferrule with 2"
    assert wire["lb"] == "Wago X-EN (switched +24 V) slot 1"
    assert (wire["cable"], wire["size"]) == ("Stranded wire", "0.5 mm² · AWG 20")
    leg = main.connection(w, shared, "3", "K1:9", "X-EN:1", "DIODE")
    assert leg["la"] == "K1 terminal 9"
    assert "cable" not in leg


@pytest.fixture
def data(tmp_path, monkeypatch):
    shutil.copytree(main.ROOT / "data", tmp_path / "data")
    monkeypatch.setattr(main, "ROOT", tmp_path)
    return tmp_path / "data"


def edit(path, change):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(doc)
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")


def test_the_committed_guide_data_builds_and_matches_the_file():
    built = main.build()
    assert sorted(built["boards"]) == ["tubing", "wiring"]
    assert all(step["connections"] for board in built["boards"].values() for step in board["steps"])
    assert json.loads(main.OUT.read_text(encoding="utf-8")) == built


def test_a_third_wire_under_one_screw_fails_the_build(data):
    def add(doc):
        wires = doc["steps"][0]["wires"]
        first = next(w for step in doc["steps"] for w in step["wires"] if w[3] != "DIODE")
        wires += [[f"9{i}", first[1], first[2], first[3]] for i in (1, 2)]
    edit(data / "wiring.yaml", add)
    with pytest.raises(AssertionError, match="more than two wires under one screw"):
        main.build()


def test_wiring_notes_must_match_the_wiring_steps(data):
    edit(data / "guide.yaml", lambda doc: doc["wiring_notes"].popitem())
    with pytest.raises(AssertionError, match="wiring_notes and wiring steps differ"):
        main.build()



@pytest.mark.parametrize("board", ["wiring", "tubing"])
def test_board_canvas_ratio_in_the_stylesheet_is_the_board_size(board):
    width, height = json.loads((main.ROOT / "data/buildguide.json").read_text(encoding="utf-8"))["boards"][board]["size"]
    css = (main.ROOT / "docs/stylesheets/extra.css").read_text(encoding="utf-8")
    assert f'[data-board="{board}"] {{\n  --board-ratio: {width} / {height};' in css


def test_a_set_makerworld_address_is_the_link_and_an_unset_one_shows_none():
    g = {"bom": [{"id": "a", "part": "A", "makerworld": "https://makerworld.com/models/1"}, {"id": "b", "part": "B", "makerworld": None}, {"id": "c", "part": "C"}]}
    assert main.bom_items(g) == [{"id": "a", "part": "A", "link": "https://makerworld.com/models/1"}, {"id": "b", "part": "B"}, {"id": "c", "part": "C"}]
    assert main.unset_makerworld(g) == ["b"]
