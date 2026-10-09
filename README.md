# AutoLever pneumatic press drive

An air cylinder works the lever of a Lee APP press, controlled by four 24 V relays and a jam timer. Press START and it presses out and back by itself until STOP, a jam or an overpressure trip; then the cylinder vents. With automatic mode off, JOG runs it only while held; E-STOP cuts the control power.

Everything in the printed box runs on 24 V DC from a closed, CE-marked desktop power supply; no mains voltage inside. This is an unchecked reference design: build and use it at your own risk. **Pre-release (October 2026):** the guide is published before the first build; nothing has been built and tested yet, the printed parts are not on MakerWorld yet, and details will change.

The build guide (introduction, BOM, step-by-step wiring and tubing) is published with GitHub Pages from this repository.

## Editing

| What | Where |
|---|---|
| Every wire, terminal and board position | `data/wiring.yaml` |
| Introduction, wiring step notes, tubing steps, BOM | `data/guide.yaml` |
| Guide pages and board | `docs/`, `docs/assets/guide.js`, `docs/assets/guide-board.js` |

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve        # preview at http://127.0.0.1:8000
```

The build fails if a wire names a terminal that does not exist or puts more than two wires under one screw. `tests/check_guide.py` (needs `playwright` and Chromium) checks every wire, tube, the BOM and the mobile layout against a running `mkdocs serve`.

## Publishing

Pushing to `main` runs `.github/workflows/pages.yml`, which builds the site and deploys it to GitHub Pages. In the repository settings, set **Pages → Source** to **GitHub Actions** once.

The printed parts will be published on MakerWorld; until then the `makerworld:` links in `data/guide.yaml` are placeholders.

## Licence

MIT, see `LICENSE`. `docs/assets/vendor/` contains unmodified copies of JointJS (MPL 2.0) and libavoid-js (LGPL 2.1 or later) with their licences.
