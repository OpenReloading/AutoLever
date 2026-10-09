# AutoLever

Pneumatic drive for the Lee APP reloading press. A Festo cylinder works the lever, four 24 V relays and a timer run the cycle. No microcontroller, nothing to flash.

Build guide with parts list, wiring and tubing: https://openreloading.github.io/AutoLever/

**Pre-release, October 2026.** Nothing has been built yet, the printed parts are not on MakerWorld yet, details will change.

Use at your own risk. The box runs on 24 V DC from an external desktop power supply, no mains inside.

## Repo

- `data/wiring.yaml`: every wire and terminal
- `data/guide.yaml`: text, tubing steps, parts list
- `docs/`: the MkDocs site. `pip install -r requirements.txt`, then `mkdocs serve`.
- `tests/check_guide.py`: Playwright check against a running `mkdocs serve`

A push to `main` builds and deploys the site with GitHub Actions.

MIT licence. `docs/assets/vendor/` holds unmodified JointJS (MPL 2.0) and libavoid-js (LGPL 2.1+).
