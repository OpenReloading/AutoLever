<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/assets/autolever-logo-dark.svg"><img src="docs/assets/autolever-logo.svg" width="320" alt="AutoLever"></picture></p>

# AutoLever

Pneumatic drive for the Lee APP reloading press. A Festo cylinder works the lever, four 24 V relays and a timer run the cycle. No microcontroller, nothing to flash.

Build guide with parts list, wiring and tubing: https://openreloading.github.io/AutoLever/

Built by reloaders for reloaders, with AI as a tool.

**Pre-release, October 2026.** Nothing has been built yet, the printed parts are not on MakerWorld yet, details will change.

Questions and ideas: [Discord](https://discord.gg/KkYJ5fdukR).

Use at your own risk. The box runs on 24 V DC from an external desktop power supply, no mains inside.

## Repo

- `data/wiring.yaml`: every wire and terminal
- `data/guide.yaml`: tubing steps, parts list
- `main.py`: writes `data/buildguide.json` ([BuildGuide](https://github.com/OpenReloading/BuildGuide) data format) from both. Run `python main.py` after editing `data/` and commit the result.
- `docs/`: the MkDocs site in Markdown; the BuildGuide MkDocs plugin draws the BOM, wiring and tubing components in it. The safety text is in `snippets/`. `pip install -r requirements.txt`, then `mkdocs serve`.
- `tests/check_guide.py`: Playwright check against the built site served under `/AutoLever/`

Pull requests run the build, the `data/buildguide.json` freshness check and the browser check. A push to `main` or `develop` builds and deploys the site with GitHub Actions: `main` is the released site, `develop` a preview under `/develop/` (marked `noindex`, with a banner).

MIT licence. The BuildGuide plugin bundles JointJS (MPL 2.0) and libavoid-js (LGPL 2.1+).
