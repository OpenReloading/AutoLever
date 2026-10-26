<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/assets/autolever-logo-dark.svg"><img src="docs/assets/autolever-logo.svg" width="320" alt="AutoLever"></picture></p>

# AutoLever

An air cylinder works the lever of your Lee APP reloading press for sizing and decapping. START cycles it until STOP, and JOG cycles it only while you hold the button.

**Pre-release, October 2026.** Nothing has been built yet, the printed parts are not on MakerWorld yet, details will change.

For Lee APP owners (Classic or Deluxe) with compressed air at 7 to 10 bar and a 3D printer. Four relays, a timer and two sensors run the sequence, so nothing needs programming or flashing.

**Safety.** Use at your own risk. Moving parts can cause serious injury: before reaching in, unplug the power supply and release the air pressure. The box runs on 24 V DC from an enclosed external adapter, with no mains inside. E-STOP is not a safety-rated emergency stop. This is a DIY design whose safety has not been independently verified. Leave wiring to a qualified electrician, have the build checked before use and do not use it for priming.

## Build it

The [build guide](https://openreloading.github.io/AutoLever/) has the parts list and interactive [wiring](https://openreloading.github.io/AutoLever/wiring/) and [tubing](https://openreloading.github.io/AutoLever/tubing/) boards. To run it locally:

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve
```

## Change it

Edit `data/*.yaml`, run `.venv/bin/python main.py` and commit `data/buildguide.json`. Printable parts are in `cad/`.

## Community and licence

Questions: [Discord](https://discord.gg/KkYJ5fdukR). Built by reloaders for reloaders, with AI as a tool.

MIT licence. The [BuildGuide](https://github.com/OpenReloading/BuildGuide) plugin bundles JointJS (MPL 2.0) and libavoid-js (LGPL 2.1+).
