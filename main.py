"""Writes data/buildguide.json (BuildGuide data format) from data/wiring.yaml and data/guide.yaml.
Run after editing data/: python main.py. The MkDocs plugin checks the result at build time; CI fails when the committed file is stale.
"""
import itertools
import json
import pathlib

import yaml

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "data/buildguide.json"
PLAIN = {"S3": "E-STOP button", "S2": "STOP button", "S0": "START button", "S1": "JOG button",
         "J1": "DC jack J1", "F1": "Fuse holder F1", "Q1": "Power switch Q1", "QPM11": "Pressure switch", "B0": "Home sensor B0",
         "B1": "Front sensor B1", "Y1": "Valve plug Y1", "Y2": "Valve plug Y2", "D5": "Diode D5", "D6": "Diode D6"}
CORE = {"BN": "brown core", "BU": "blue core", "BK": "black core"}
WAGO = {"X-EN": "switched +24 V", "X-M1": "0 V", "X-M2": "0 V", "X-D": "diode join"}
# board look: [line, outline] per wire colour, list swatch where it differs, and the part kinds
WIRE = {"WH": ["#ffffff", "#334155", "#fff"], "BU": ["#2563eb", "#1e3a8a", "#347bdc"], "BN": ["#92400e", "#451a03", "#956238"],
        "BK": ["#1f2937", "#000000", "#273039"], "GY": ["#9ca3af", "#4b5563", "#929ea9"], "DIODE": ["#d1d5db", "#111827", "#29363a"]}
KINDS = {
    "socket": {"fill": "#1f2937", "stroke": "#1f2937", "inset": 17, "diodeLoop": "around"},
    "box": {"fill": "#f1f5f9", "stroke": "#17202a", "offset": {"bottom": -16}},
    "diode": {"fill": "#111827", "stroke": "#111827", "band": True},
    "wago": {"fill": "#f1f5f9", "stroke": "#64748b"},
    "plug": {"fill": "#1f2937", "stroke": "#1f2937"},
    "sensor": {"fill": "#e8f5ec", "stroke": "#15803d", "pins": {"BN": "#92400e", "BU": "#2563eb", "BK": "#111827"}},
    "button": {"round": True, "stroke": "#9ca3af"},
}
# tubing: the old schematic as a routed board, one connection per tube of guide.yaml (ends by tube id)
TUBE_ENDS = {"air1": ("AIR:out", "FRL:in"), "shutoff": ("FRL:out", "SHUT:in"), "air2": ("SHUT:out", "TEE:in"),
             "air3": ("TEE:out", "VALVE:P"), "air4": ("VALVE:A", "CYL:cap"), "air5": ("VALVE:B", "CYL:rod"),
             "air6": ("VALVE:R+S", "SIL:in")}
TUBING_PARTS = {
    "AIR": {"name": "AIR", "sub": "7–10 bar", "at": [20, 250], "size": [90, 56], "ports": {"right": ["out"]}},  # noqa: RUF001
    "FRL": {"name": "FRL", "sub": "Filter-regulator", "at": [200, 236], "size": [110, 84], "ports": {"left": ["in"], "right": ["out"]}},
    "SHUT": {"name": "3/2", "sub": "shut-off, vents", "at": [400, 250], "size": [80, 56], "ports": {"left": ["in"], "right": ["out"]}},
    "TEE": {"name": "Tee", "sub": "6 mm", "at": [570, 254], "size": [60, 48], "ports": {"left": ["in"], "right": ["out"]}},
    "VALVE": {"name": "5/3 VALVE · exhaust centre", "at": [720, 230], "size": [200, 96],
              "ports": {"left": ["P"], "right": ["A", "B"], "bottom": ["R+S"]}},
    "CYL": {"name": "DSNU CYLINDER", "at": [880, 60], "size": [200, 56], "ports": {"bottom": ["cap", "rod"]}},
    "SIL": {"sub": "2 × silencers · R + S → atmosphere", "at": [745, 460], "size": [150, 40], "ports": {"top": ["in"]}},  # noqa: RUF001
}
TUBING_PROPS = [{"name": "QPM11 on the branch", "at": [520, 150], "size": [160, 40]}]


def screws(w):
    """Wire numbers under each screw terminal. Wago slots and diode legs are not screws."""
    ends = {}
    for step in w["steps"]:
        for no, a, b, col in step["wires"]:
            for side, end in (("from", a), ("to", b)):   # also keeps label() from a bare KeyError
                part, _, pin = end.partition(":")
                if part not in w["parts"]:
                    raise ValueError(f"wire {no}, {side} end {end}: unknown part {part}")
                if pin not in itertools.chain.from_iterable(w["parts"][part]["ports"].values()):
                    raise ValueError(f"wire {no}, {side} end {end}: part {part} has no terminal {pin}")
            if col == "DIODE":       # a diode leg shares the screw, it is not a wire
                continue
            for end in (a, b):
                if w["parts"][end.split(":")[0]]["kind"] not in ("wago", "diode"):
                    ends.setdefault(end, []).append(no)
    return ends


def label(end):  # noqa: PLR0911
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
    if part == "F1":
        return f"{PLAIN[part]} tab {pin}"
    if part == "J1":
        return f"{PLAIN[part]} {pin.replace('-', '−')}"  # noqa: RUF001
    if part in ("S0", "S1", "S2", "S3"):   # E-STOP and STOP use their NC contact, the others their NO contact
        return f"{PLAIN[part]} {pin} ({'NC' if part in ('S2', 'S3') else 'NO'})"
    return f"{PLAIN.get(part, part)} {pin}"


def cable_of(w, a, b, col):  # noqa: ARG001
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


def connection(w, shared, no, a, b, col):  # noqa: PLR0913
    def twin(end):
        """Two wires on one screw go into one twin ferrule: name the partner."""
        return "".join(f" · twin ferrule with {n}" for n in shared.get(end, []) if n != no)

    cable = w["cables"][cable_of(w, a, b, col)]
    c = {"no": no, "a": a, "b": b, "color": col,
         # a diode leg is not a wire: no twin ferrule hint on the diode rows
         "la": label(a) + ("" if col == "DIODE" else twin(a)), "lb": label(b) + ("" if col == "DIODE" else twin(b))}
    if col != "DIODE":
        c.update(cable=cable["name"], size=cable_text(cable))
    return c


def bom_items(g):
    """BOM rows for the guide: the makerworld address becomes the link, an unset one shows no link (a dead link is worse than none)."""
    return [{("link" if k == "makerworld" else k): v for k, v in item.items() if k != "makerworld" or v} for item in g["bom"]]


def unset_makerworld(g):
    """Ids of the printed parts whose `makerworld:` field is still empty."""
    return [item["id"] for item in g["bom"] if "makerworld" in item and not item["makerworld"]]


def build():
    w = yaml.safe_load((ROOT / "data/wiring.yaml").read_text(encoding="utf-8"))
    g = yaml.safe_load((ROOT / "data/guide.yaml").read_text(encoding="utf-8"))
    shared = screws(w)
    over = {k: v for k, v in shared.items() if len(v) > 2}
    assert not over, f"more than two wires under one screw: {over}"
    notes = g["wiring_notes"]
    ids = {str(s["id"]) for s in w["steps"]}
    assert set(notes) == ids, f"wiring_notes and wiring steps differ: notes only {sorted(set(notes) - ids)}, steps only {sorted(ids - set(notes))}"
    return {
        "storage": "autolever-guide",
        "bom": {"note": "Feel free to substitute as required for local availability and cost. Cable and tube lengths are estimates.",
                "export": "autolever-bom.csv", "linkLabel": "MakerWorld",
                "items": bom_items(g)},
        "boards": {
            "wiring": {
                "title": "Wiring", "label": "Wiring board", "size": [1360, 860], "prefix": "wire", "single": True,
                "legend": [{"key": "diode", "text": "Silver ring = cathode"}, "Green = selected connection"],
                "colors": {k: {"line": line, "outline": outline, "swatch": swatch, **({"diode": True} if k == "DIODE" else {})}
                           for k, (line, outline, swatch) in WIRE.items()},
                "kinds": KINDS, "areas": w["areas"], "props": w["props"], "parts": w["parts"],
                "steps": [{"id": str(s["id"]), "title": s["title"], "note": notes[str(s["id"])], "connections": [connection(w, shared, *wire) for wire in s["wires"]]}
                          for s in w["steps"]],
            },
            "tubing": {
                "title": "Tubing", "label": "Pneumatic tubing diagram", "size": [1100, 530], "prefix": "tube", "scope": "all", "listAll": True, "listColor": False,
                "legend": ["6 × 4 mm tube · schematic", "Green = selected connection"],  # noqa: RUF001
                "colors": {"AIR": {"line": "#7694b2", "outline": "#3f5f7f"}},
                "props": TUBING_PROPS, "parts": TUBING_PARTS,
                "steps": [{"id": str(i), "title": t["title"], "note": f'{t["text"]} Check: {t["check"]}', "connections": [{"no": str(i), "a": a, "b": b, "color": "AIR", "la": t["from"], "lb": t["to"]}]}
                          for i, t in enumerate(g["tubes"], 1) for a, b in [TUBE_ENDS[t["id"]]]],
            },
        },
    }


if __name__ == "__main__":
    unset = unset_makerworld(yaml.safe_load((ROOT / "data/guide.yaml").read_text(encoding="utf-8")))
    if unset:
        print(f"makerworld not set (no link in the BOM): {', '.join(unset)}")
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
