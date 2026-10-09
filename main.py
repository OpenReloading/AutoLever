"""mkdocs-macros module: validates data/wiring.yaml and hands it, with data/guide.yaml, to the guide pages."""
import json
import pathlib

import yaml

ROOT = pathlib.Path(__file__).parent
COLOUR = {"DIODE": "diode", "WH": "white", "BU": "blue", "BN": "brown", "BK": "black", "GY": "diode leg"}
PLAIN = {"S3": "E-STOP button", "S2": "STOP button", "S0": "START button", "S1": "JOG button",
         "J1": "DC jack J1", "F1": "Fuse holder F1", "Q1": "Power switch Q1", "QPM11": "Pressure switch", "B0": "Home sensor B0",
         "B1": "Front sensor B1", "Y1": "Valve plug Y1", "Y2": "Valve plug Y2", "D5": "Diode D5", "D6": "Diode D6"}
CORE = {"BN": "brown core", "BU": "blue core", "BK": "black core"}
WAGO = {"X-EN": "switched +24 V", "X-M1": "0 V", "X-M2": "0 V", "X-D": "diode join"}


def screws(w):
    """Wire numbers under each screw terminal. Wago slots and diode legs are not screws."""
    ends = {}
    for step in w["steps"]:
        for no, a, b, col in step["wires"]:
            if col == "DIODE":       # a diode leg shares the screw, it is not a wire
                continue
            for end in (a, b):
                if w["parts"][end.split(":")[0]]["kind"] not in ("wago", "diode"):
                    ends.setdefault(end, []).append(no)
    return ends


def load():
    w = yaml.safe_load((ROOT / "data/wiring.yaml").read_text())
    for step in w["steps"]:
        for no, a, b, col in step["wires"]:
            assert col in COLOUR, f"wire {no}: unknown colour {col}"
            for end in (a, b):
                part, pin = end.split(":", 1)
                pins = [p for side in w["parts"][part]["ports"].values() for p in side]
                assert pin in pins, f"wire {no}: {part} has no terminal {pin}"
    over = {k: v for k, v in screws(w).items() if len(v) > 2}
    assert not over, f"more than two wires under one screw: {over}"
    return w


def label(end):
    """'K1:9' → 'K1 terminal 9' in words a first-timer can find on the part."""
    part, pin = end.split(":", 1)
    if part[0] == "K" or part == "T1":
        return f"{part} terminal {pin}"
    if part.startswith("X-"):
        return f"Wago {part} ({WAGO[part]}) slot {pin}"
    if part in ("B0", "B1"):
        return f"{PLAIN[part]}, {CORE[pin]}"
    if part in ("D5", "D6"):
        return f"{PLAIN[part]}, " + ("plain leg, in its own 2-way Wago with this wire" if pin == "A" else "ring leg")
    if part in ("Y1", "Y2"):
        return f"{PLAIN[part]} pin {pin}" + (" (+)" if pin == "1" else "")
    if part == "J1":
        return f"{PLAIN[part]} {pin.replace('-', '−')}"
    if part in ("S0", "S1", "S2", "S3"):   # E-STOP and STOP use their NC contact, the others their NO contact
        return f"{PLAIN[part]} {pin} ({'NC' if part in ('S2', 'S3') else 'NO'})"
    return f"{PLAIN.get(part, part)} {pin}"


def cable_of(w, a, b, col):
    """Which kind of cable a wire is: see `cables:` in data/wiring.yaml."""
    parts = {a.split(":")[0], b.split(":")[0]}
    if col == "DIODE":
        return "diode"
    if parts & {"B0", "B1"}:
        return "sensor"
    if parts & {"Y1", "Y2"}:
        return "valve"
    if col == "GY":
        return "leg"
    return "field" if "QPM11" in parts else "core"


def cable_text(c):
    return " · ".join(x for x in (c["size"], c["awg"]) if x)


def define_env(env):
    w = load()
    CAB = w["cables"]
    shared = screws(w)

    def twin(end, no):
        """Two wires on one screw go into one twin ferrule: name the partner."""
        return "".join(f" · twin ferrule with {n}" for n in shared.get(end, []) if n != no)

    @env.macro
    def guide_data():
        """Companion UI uses the validated netlist, never a second set of endpoints."""
        guide = yaml.safe_load((ROOT / "data/guide.yaml").read_text())
        guide["parts"] = w["parts"]
        guide["steps"] = [{
            "id": str(s["id"]), "title": s["title"],
            "note": guide["wiring_notes"][str(s["id"])],
            "wires": [{"no": no, "a": a, "b": b, "col": col,
                       # a diode leg is not a wire: no twin ferrule hint on the diode rows
                       "la": label(a) + ("" if col == "DIODE" else twin(a, no)),
                       "lb": label(b) + ("" if col == "DIODE" else twin(b, no)),
                       "cable": CAB[cable_of(w, a, b, col)]["name"],
                       "size": cable_text(CAB[cable_of(w, a, b, col)])}
                      for no, a, b, col in s["wires"]]
        } for s in w["steps"]]
        guide["areas"] = w["areas"]
        guide["props"] = w["props"]
        payload = json.dumps(guide).replace("<", "\\u003c")
        return f'<script id="guide-data" type="application/json">{payload}</script>'
