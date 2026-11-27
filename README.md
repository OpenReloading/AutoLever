<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/assets/autolever-logo-dark.svg"><img src="docs/assets/autolever-logo.svg" width="320" alt="AutoLever"></picture></p>

# AutoLever

[![Sponsor](https://img.shields.io/badge/Sponsor-eikelandin-db61a2?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/eikelandin)
[![Discord](https://img.shields.io/badge/Discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/hUCSjDYNaa)

An air cylinder works the lever of your Lee APP reloading press for sizing and decapping. START cycles it until you press START again, and JOG cycles it only while you hold the button.

**Pre-release, October 2026.** Nothing has been built yet, the printed parts are not on MakerWorld yet, details will change.

For Lee APP owners (Classic or Deluxe) with compressed air at 7 to 10 bar and a 3D printer. A StamPLC controller and two sensors run the sequence; flash its firmware once over USB-C.

**Safety.** Use at your own risk. Moving parts can cause serious injury: before reaching in, unplug the power supply and release the air pressure. The box runs on 24 V DC from an enclosed external adapter, with no mains inside. E-STOP is not a safety-rated emergency stop. This is a DIY design whose safety has not been independently verified. Leave wiring to a qualified electrician, have the build checked before use and do not use it for priming.

## Build it

The [build guide](https://openreloading.github.io/AutoLever/) has the parts list and interactive [wiring](https://openreloading.github.io/AutoLever/wiring/) and [tubing](https://openreloading.github.io/AutoLever/tubing/) boards. To run it locally (Python 3.12 or later):

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve
```

## Change it

Edit `data/*.yaml`, run `.venv/bin/python main.py` and commit `data/buildguide.json`. Printable parts are in `cad/`.

## Community and license

Built by reloaders for reloaders, with AI as a tool.

- Code (firmware, scripts, tests, site templates): AGPL-3.0-only, see [LICENSE](LICENSE).
- The firmware (`firmware/`) adds a section 7 permission to link it with the binary-only Espressif Wi-Fi and PHY libraries and convey the result, see [LICENSES/LicenseRef-Espressif-WiFi-PHY-exception.txt](LICENSES/LicenseRef-Espressif-WiFi-PHY-exception.txt).
- CAD sources and their renders (`cad/`, `docs/assets/boxes/`) and the parts printed from them: CERN-OHL-S-2.0, see [LICENSES/CERN-OHL-S-2.0.txt](LICENSES/CERN-OHL-S-2.0.txt).
- Guide, BOM and wiring data (`data/`): CC-BY-SA-4.0, see [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt).
- Documentation and site text: MIT, see [LICENSES/MIT.txt](LICENSES/MIT.txt).
- The AutoLever name and logos: no open license, see [LICENSES/LicenseRef-Brand.txt](LICENSES/LicenseRef-Brand.txt).

The device's web page shows the firmware version and links the source of that commit; `firmware/version.py` stamps both from git at build time. A changed firmware links its own source: the repository address is in `firmware/src/web.cpp`. The [BuildGuide](https://github.com/OpenReloading/BuildGuide) plugin bundles JointJS (MPL 2.0) and libavoid-js (LGPL 2.1+).
