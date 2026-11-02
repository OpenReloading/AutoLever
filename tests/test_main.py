"""Unit tests of the project rules in main.py (wire labels, cable kinds, two wires per screw, build checks)."""
import json
import shutil

import pytest
import yaml

import main

PARTS = {
    "PLC": {"kind": "box", "ports": {"top": ["+", "-", "C", "1"], "bottom": ["1NC", "1C"]}},
    "S3": {"kind": "button", "ports": {"top": ["1", "2"]}},
    "X-24": {"kind": "wago", "ports": {"top": ["1", "2"]}},
    "Y1": {"kind": "plug", "ports": {"left": ["1", "2"]}},
}


def wiring(*wires):
    return {"parts": PARTS, "steps": [{"id": "A", "wires": list(wires)}]}


def test_wires_on_one_screw_are_listed_together():
    assert main.screws(wiring(["1", "PLC:+", "S3:1", "red"], ["2", "PLC:+", "S3:2", "black"])) == {"PLC:+": ["1", "2"], "S3:1": ["1"], "S3:2": ["2"]}


def test_wago_slots_and_diode_legs_are_not_screws():
    assert main.screws(wiring(["1", "PLC:+", "X-24:1", "red"], ["D7", "Y1:1", "Y1:2", "DIODE"])) == {"PLC:+": ["1"]}


@pytest.mark.parametrize(("wire", "message"), [
    (["6", "K9:1", "S3:1", "red"], "wire 6, from end K9:1: unknown part K9"),
    (["6", "S3:1", "PLC:99", "red"], "wire 6, to end PLC:99: part PLC has no terminal 99"),
])
def test_a_wire_with_an_unknown_end_names_its_number_and_end(wire, message):
    with pytest.raises(ValueError, match=message):
        main.screws(wiring(wire))


@pytest.mark.parametrize(("end", "text"), [
    ("X-0V1:1", "Wago X-0V1 (Ground) slot 1"),
    ("B0:BN", "Brown wire (+24 V) of the home sensor B0"),
    ("B1:BK", "Black wire (signal) of the front sensor B1"),
    ("Y1:1", "Valve plug Y1 pin 1 (+24 V)"),
    ("Y2:2", "Valve plug Y2 pin 2 (Ground)"),
    ("J1:+", "DC jack J1 + (+24 V, centre pin)"),
    ("J1:-", "DC jack J1 \u2212 (Ground)"),
    ("Q1:GND", "Power button Q1 GND"),
    ("S3:1", "E-STOP button terminal 1 (closed contact, marked 11)"),
    ("S3:2", "E-STOP button terminal 2 (closed contact, marked 12)"),
    ("QPM11:1", "Pressure switch QPM11 terminal 1"),
    ("PLC:+", "StamPLC + (+24 V in)"),
    ("PLC:-", "StamPLC \u2212 (Ground)"),
    ("PLC:C", "StamPLC C (input common, Ground)"),
    ("PLC:3", "StamPLC input 3 (rail after the E-STOP (X-S))"),
    ("PLC:8", "StamPLC input 8"),
    ("PLC:1NC", "StamPLC relay 1 NC (closed at rest)"),
    ("PLC:2C", "StamPLC relay 2 COM (common)"),
    ("PLC:2NO", "StamPLC relay 2 NO (closed when the relay is on)"),
    ("FU1:2", "Inline fuse holder FU1 lead 2"),
    ("X-24:2", "Wago X-24 (+24 V after POWER) slot 2"),
    ("UNKNOWN:1", "UNKNOWN terminal 1"),
])
def test_label_names_the_terminal_in_words(end, text):
    assert main.label(end) == text


@pytest.mark.parametrize(("a", "b", "col", "kind"), [
    ("Y1:1", "Y1:2", "DIODE", "diode"),
    ("B0:BN", "X-24:1", "brown", "sensor"),
    ("PLC:1NO", "Y1:1", "red", "valve"),
    ("X-V:1", "QPM11:1", "red", "field"),
    ("PLC:+", "X-24:1", "red", "core"),
])
def test_cable_of_picks_the_cable_kind(a, b, col, kind):
    assert main.cable_of(a, b, col) == kind


def test_cable_text_skips_an_empty_awg():
    assert main.cable_text({"size": "0.5 mm²", "awg": "AWG 20"}) == "0.5 mm² · AWG 20"
    assert main.cable_text({"size": "as supplied", "awg": ""}) == "as supplied"


def test_connection_names_the_twin_ferrule_partner_but_not_for_a_diode_leg():
    w = {"cables": {"core": {"name": "Stranded wire", "size": "0.5 mm²", "awg": "AWG 20"}, "diode": {"name": "Diode", "size": "", "awg": ""}}}
    shared = {"PLC:+": ["1", "2"], "X-24:1": ["1"]}
    wire = main.connection(w, shared, "1", "PLC:+", "X-24:1", "red")
    assert wire["la"] == "StamPLC + (+24 V in) · one twin ferrule with wire 2"
    assert wire["lb"] == "Wago X-24 (+24 V after POWER) slot 1"
    assert (wire["cable"], wire["size"]) == ("Stranded wire", "0.5 mm² · AWG 20")
    leg = main.connection(w, shared, "3", "PLC:+", "X-24:1", "DIODE")
    assert leg["la"] == "StamPLC + (+24 V in)"
    assert "cable" not in leg


def test_a_twin_ferrule_gets_one_sentence_in_the_step_of_its_wires():
    step = {"id": "A", "wires": [["1", "PLC:+", "S3:1", "red"], ["2", "PLC:+", "S3:2", "red"], ["3", "X-24:1", "X-24:2", "red"]]}
    shared = main.screws({"parts": PARTS, "steps": [step]})
    assert main.twin_ferrules(step, shared) == "Crimp wires 1 and 2 into one twin ferrule, then one screw at StamPLC + (+24 V in)."
    assert main.twin_ferrules({"id": "B", "wires": step["wires"][:1]}, shared) == ""   # the partner wire is in another step: no sentence


def test_connector_line_names_the_colour_at_each_terminal_in_port_order():
    parts = {**PARTS, "Q1": {"kind": "button", "ports": {"top": ["IN", "OUT", "GND"]}}}
    step = {"id": "A", "wires": [["15", "Q1:GND", "X-24:1", "black"], ["2", "X-24:2", "Q1:IN", "red"], ["3", "Q1:OUT", "S3:1", "red"], ["D7", "Y1:1", "Y1:2", "DIODE"]]}
    assert main.connector_line({"parts": parts}, step) == "Connectors: power button Q1: IN red, OUT red, GND black; E-STOP button: terminal 1 red."
    assert main.connector_line({"parts": parts}, {"id": "B", "wires": [["1", "X-24:1", "X-24:2", "red"]]}) == ""


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


def test_a_twin_ferrule_split_over_two_steps_fails_the_build(data):
    def add(doc):   # a second wire on a screw of the first step, but in the last step
        first = next(w for w in doc["steps"][0]["wires"] if w[3] != "DIODE" and doc["parts"][w[1].split(":")[0]]["kind"] != "wago")
        doc["steps"][-1]["wires"].append(["99", first[1], first[2], first[3]])
    edit(data / "wiring.yaml", add)
    with pytest.raises(AssertionError, match="one twin ferrule"):
        main.build()


@pytest.mark.parametrize(("board", "red", "black", "sensor"), [
    ("wiring", ("1", "2", "6", "10", "22"), ("3", "4", "9", "26"), ("16", "17", "18")),
])
def test_the_wires_of_the_box_are_red_and_black_and_a_sensor_keeps_its_own_colours(board, red, black, sensor):
    steps = main.build()["boards"][board]["steps"]
    colour = {c["no"]: c["color"] for s in steps for c in s["connections"]}
    assert {colour[n] for n in red} == {"red"}
    assert {colour[n] for n in black} == {"black"}
    assert tuple(colour[n] for n in sensor) == ("brown", "blue", "black")


def test_notes_must_match_the_steps_of_the_board(data):
    edit(data / "guide.yaml", lambda doc: doc["wiring_notes"].popitem())
    with pytest.raises(AssertionError, match="notes and steps differ"):
        main.build()


@pytest.mark.parametrize("board", ["wiring", "tubing"])
def test_board_canvas_ratio_in_the_stylesheet_is_the_board_size(board):
    width, height = json.loads((main.ROOT / "data/buildguide.json").read_text(encoding="utf-8"))["boards"][board]["size"]
    css = (main.ROOT / "site/src/css/autolever.css").read_text(encoding="utf-8")
    assert f'[data-board="{board}"] {{\n  --board-ratio: {width} / {height};' in css


def test_a_set_makerworld_address_is_the_link_and_an_unset_one_shows_none():
    g = {"bom": [{"id": "a", "part": "A", "makerworld": "https://makerworld.com/models/1"}, {"id": "b", "part": "B", "makerworld": None}, {"id": "c", "part": "C"}]}
    assert main.bom_items(g) == [{"id": "a", "part": "A", "link": "https://makerworld.com/models/1"}, {"id": "b", "part": "B"}, {"id": "c", "part": "C"}]
    assert main.unset_makerworld(g) == ["b"]
