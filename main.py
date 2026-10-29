"""Writes data/buildguide.json (BuildGuide data format) from data/wiring.yaml (StamPLC edition), data/relay.yaml (relay edition, deprecated) and data/guide.yaml.
Run after editing data/: python main.py. The MkDocs plugin checks the result at build time; CI fails when the committed file is stale.
"""
import itertools
import json
import pathlib

import yaml

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "data/buildguide.json"
PLAIN = {"S3": "E-STOP button", "S2": "STOP button", "S0": "START button", "S1": "JOG button",
         "J1": "DC jack J1", "F1": "fuse holder F1", "FU1": "inline fuse holder FU1", "PLC": "StamPLC", "Q1": "power button Q1", "QPM11": "pressure switch QPM11", "B0": "home sensor B0",
         "B1": "front sensor B1", "Y1": "valve plug Y1", "Y2": "valve plug Y2", "D5": "diode D5", "D6": "diode D6", "T1": "jam timer T1 (8-pin timer)"}
CORE = {"BN": "brown wire (+24 V)", "BU": "blue wire (Ground)", "BK": "black wire (signal)"}
WAGO = {"X-EN": "+24 V while on", "X-M1": "Ground", "X-M2": "Ground", "X-D": "diode join",
        "X-24": "+24 V after POWER", "X-0V1": "Ground", "X-0V2": "Ground", "X-S": "rail after the E-STOP", "X-V": "valve rail"}
# StamPLC terminals: the power and COM terminals, inputs 1 to 8 on one edge, relays 1 to 4 (NC, COM, NO) on the other
PLC_POWER = {"+": ("+", " (+24 V in)"), "-": ("\u2212", " (Ground)"), "C": ("C", " (input common, Ground)")}
PLC_INPUT = {"1": "home sensor B0", "2": "front sensor B1", "3": "rail after the E-STOP (X-S)", "4": "valve rail after the pressure switch (X-V)"}
PLC_POLE = {"NC": ("NC", " (closed at rest)"), "C": ("COM", " (common)"), "NO": ("NO", " (closed when the relay is on)")}
# marks on a button's contact block: terminals 1, 2 are the closed contact, 3, 4 the open contact
MARK = {"1": "11", "2": "12", "3": "23", "4": "24"}
CONNECTORS = ("J1", "F1", "FU1", "Q1", "S3", "S2", "S0", "S1", "QPM11", "Y1", "Y2", "PLC")  # parts that get a one-line connector list
# board look: [line, outline] per wire colour, list swatch where it differs, and the part kinds
WIRE = {"red": ["#dc2626", "#7f1d1d", "#dc2626"], "blue": ["#2563eb", "#1e3a8a", "#347bdc"], "brown": ["#92400e", "#451a03", "#956238"],
        "black": ["#1f2937", "#000000", "#273039"], "grey": ["#9ca3af", "#4b5563", "#929ea9"], "DIODE": ["#d1d5db", "#111827", "#29363a"]}
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


def cap(text):
    """Capital first letter, the rest untouched (str.capitalize lowercases 'E-STOP')."""
    return text[:1].upper() + text[1:]


def terminal(part, pin):
    """The short terminal name: 'terminal 3', 'pin 1', 'IN'."""
    if part == "PLC":
        return PLC_POWER[pin][0] if pin in PLC_POWER else f"input {pin}" if pin.isdigit() else f"relay {pin[0]} {PLC_POLE[pin[1:]][0]}"
    return {"F1": f"tab {pin}", "FU1": f"lead {pin}", "T1": f"pin {pin}", "Y1": f"pin {pin}", "Y2": f"pin {pin}", "Q1": pin, "J1": "+" if pin == "+" else "\u2212"}.get(part, f"terminal {pin}")


def detail(part, pin):
    """What the terminal is, in words, where the short name does not say: the contact of a button, the pole of a plug."""
    if part in ("S0", "S1", "S2", "S3"):   # E-STOP and STOP use their closed contact, the others their open contact
        return f" ({'closed' if part in ('S2', 'S3') else 'open'} contact, marked {MARK[pin]})"
    if part in ("Y1", "Y2"):
        return " (+24 V)" if pin == "1" else " (Ground)"
    if part == "PLC":
        return PLC_POWER[pin][1] if pin in PLC_POWER else f" ({PLC_INPUT[pin]})" if pin in PLC_INPUT else PLC_POLE[pin[1:]][1] if pin[1:] in PLC_POLE else ""
    return {"+": " (+24 V, centre pin)", "-": " (Ground)"}.get(pin, "") if part == "J1" else ""


def label(end):
    """'K1:9' → 'Relay K1 terminal 9' in words a first-timer can find on the part."""
    part, pin = end.split(":", 1)
    if part[0] == "K":
        return f"Relay {part} terminal {pin}"
    if part.startswith("X-"):
        return f"Wago {part} ({WAGO[part]}) slot {pin}"
    if part in ("B0", "B1"):
        return f"{cap(CORE[pin])} of the {PLAIN[part]}"
    if part in ("D5", "D6"):
        return f"{cap(PLAIN[part])}, " + ("plain leg, in its own 2-way Wago with this wire" if pin == "A" else "ring leg")
    return f"{cap(PLAIN.get(part, part))} {terminal(part, pin)}{detail(part, pin)}"


def cable_of(a, b, col):
    """Which kind of cable a wire is: see `cables:` in data/wiring.yaml and data/relay.yaml."""
    parts = {a.split(":")[0], b.split(":")[0]}
    if col == "DIODE":
        return "diode"
    if parts & {"B0", "B1"}:
        return "sensor"
    if parts & {"Y1", "Y2"}:
        return "valve"
    if col == "grey":
        return "leg"
    return "field" if "QPM11" in parts else "core"


def cable_text(c):
    return " · ".join(x for x in (c["size"], c["awg"]) if x)


def connection(w, shared, no, a, b, col):  # noqa: PLR0913
    def twin(end):
        """Two wires on one screw go into one twin ferrule: name the partner."""
        return "".join(f" · one twin ferrule with wire {n}" for n in shared.get(end, []) if n != no)

    cable = w["cables"][cable_of(a, b, col)]
    c = {"no": no, "a": a, "b": b, "color": col,
         # a diode leg is not a wire: no twin ferrule hint on the diode rows
         "la": label(a) + ("" if col == "DIODE" else twin(a)), "lb": label(b) + ("" if col == "DIODE" else twin(b))}
    if col != "DIODE":
        c.update(cable=cable["name"], size=cable_text(cable))
    return c


def twin_ferrules(step, shared):
    """One sentence for each screw of the step that takes two wires: they are crimped once, into one twin ferrule."""
    nos = [wire[0] for wire in step["wires"]]
    ends = dict.fromkeys(end for wire in step["wires"] if wire[3] != "DIODE" for end in wire[1:3])
    return " ".join(f"Crimp wires {' and '.join(shared[end])} into one twin ferrule, then one screw at {label(end)}."
                    for end in ends if len(shared.get(end, [])) == 2 and set(shared[end]) <= set(nos))


def connector_line(w, step):
    """'Connectors: power button Q1: IN red, OUT red, GND black' for each part of CONNECTORS that the step wires, with the wire colour at each terminal."""
    colours = {}
    for _no, a, b, col in step["wires"]:
        if col != "DIODE":
            for end in (a, b):
                colours.setdefault(end, []).append(col)
    parts = []
    for part in CONNECTORS:
        ends = [end for end in colours if end.split(":")[0] == part]
        if ends:
            ends.sort(key=lambda end: [p for side in w["parts"][part]["ports"].values() for p in side].index(end.split(":", 1)[1]))
            parts.append(f"{PLAIN[part]}: " + ", ".join(f"{terminal(*end.split(':', 1))} {' and '.join(colours[end])}" for end in ends))
    return f"Connectors: {'; '.join(parts)}." if parts else ""


def step_note(w, notes, step, shared):
    """The instruction, the connector line, the twin ferrule sentences, then the details of guide.yaml."""
    note = notes[str(step["id"])]
    return " ".join(x for x in (note["do"], connector_line(w, step), twin_ferrules(step, shared), note["text"]) if x)


def bom_items(g):
    """BOM rows for the guide: the makerworld address becomes the link, an unset one shows no link (a dead link is worse than none)."""
    return [{("link" if k == "makerworld" else k): v for k, v in item.items() if k != "makerworld" or v} for item in g["bom"]]


def unset_makerworld(g):
    """Ids of the printed parts whose `makerworld:` field is still empty."""
    return [item["id"] for item in g["bom"] if "makerworld" in item and not item["makerworld"]]


def wiring_board(w, notes, title, prefix, size):
    """One wiring board from a wiring file (wiring.yaml, relay.yaml) and the notes of its steps in guide.yaml."""
    shared = screws(w)
    over = {k: v for k, v in shared.items() if len(v) > 2}
    assert not over, f"more than two wires under one screw: {over}"
    step_of = {wire[0]: str(s["id"]) for s in w["steps"] for wire in s["wires"]}
    split = {end: nos for end, nos in shared.items() if len({step_of[no] for no in nos}) > 1}
    assert not split, f"wires under one screw (one twin ferrule) belong in one step: {split}"
    ids = {str(s["id"]) for s in w["steps"]}
    assert set(notes) == ids, f"{title} notes and steps differ: notes only {sorted(set(notes) - ids)}, steps only {sorted(ids - set(notes))}"
    return {
        "title": title, "label": "Wiring board", "size": size, "prefix": prefix, "single": True,
        "legend": ["Red = +24 V, black = Ground, sensor wires keep their own colours", {"key": "diode", "text": "Silver ring = cathode"}, "Green = selected connection"],
        "colors": {k: {"line": line, "outline": outline, "swatch": swatch, **({"diode": True} if k == "DIODE" else {})}
                   for k, (line, outline, swatch) in WIRE.items()},
        "kinds": KINDS, "areas": w["areas"], "props": w["props"], "parts": w["parts"],
        "steps": [{"id": str(s["id"]), "title": s["title"], "note": step_note(w, notes, s, shared), "connections": [connection(w, shared, *wire) for wire in s["wires"]]}
                  for s in w["steps"]],
    }


def build():
    def load(name):
        return yaml.safe_load((ROOT / "data" / name).read_text(encoding="utf-8"))

    g = load("guide.yaml")
    return {
        "storage": "autolever-guide",
        "bom": {"note": "Feel free to substitute as required for local availability and cost. Cable and tube lengths are estimates.",
                "export": "autolever-bom.csv", "linkLabel": "MakerWorld",
                "items": bom_items(g)},
        "boards": {
            "wiring": wiring_board(load("wiring.yaml"), g["wiring_notes"], "Wiring", "plc", [1360, 860]),
            "relay": wiring_board(load("relay.yaml"), g["relay_notes"], "Wiring (relay edition)", "wire", [1360, 860]),
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
