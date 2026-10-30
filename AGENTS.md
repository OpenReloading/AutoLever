# AutoLever

## Commands

- Agents run on the host; file edits and Git stay there. Start the container with `devcontainer up --docker-path podman --workspace-folder .` (creates `.venv` with `requirements.txt`); run project commands with the prefix `devcontainer exec --docker-path podman --workspace-folder .`.
- Install: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Lint (as CI): `.venv/bin/pip install --only-binary :all: --require-hashes -r requirements-dev.txt`, then `.venv/bin/ruff check .` and `.venv/bin/basedpyright --pythonpath .venv/bin/python`. `requirements-dev.txt` is compiled from `requirements-dev.in` on Python 3.13: `pip-compile --generate-hashes --output-file=requirements-dev.txt requirements-dev.in`
- Build (as CI): `.venv/bin/mkdocs build --strict`
- Serve: `.venv/bin/mkdocs serve -a 0.0.0.0:8000`
- Unit tests with coverage (as CI, pytest comes from `requirements-dev.txt`): `.venv/bin/pytest --cov`. Coverage floor and what is measured: `[tool.coverage]` in `pyproject.toml`. Add `--cov-report=xml:coverage.xml` for the report SonarCloud reads.
- Generate the guide data after editing `data/*.yaml`: `.venv/bin/python main.py` (writes `data/buildguide.json`, committed; CI fails when it is stale)
- Social card: `.venv/bin/python -m tools.social_card` (needs Chromium, so in the container) rewrites `docs/assets/social-card.png`; run it and commit the PNG after changing the logo, the light tokens in `docs/stylesheets/extra.css` or `site_description`. Nothing in CI catches a stale card.
- Browser check, against the built site (`mkdocs serve` livereload counts as an external request): `.venv/bin/mkdocs build --strict -d /tmp/www/AutoLever && python -m http.server -d /tmp/www 8000`, then `.venv/bin/python tests/check_guide.py http://127.0.0.1:8000/AutoLever`
- Printable parts (OpenSCAD, also in the container; `tests/test_cad.py` renders them in `pytest`): `mkdir -p cad/stl && openscad -o cad/stl/stamplc_box-base.stl -D 'part="base"' cad/stamplc_box.scad`. Each `.scad` file lists its `part` values and options at the top. `cad/stl/` is git-ignored.
- A Playwright MCP server inside the container reaches the served site at `http://127.0.0.1:8000/AutoLever/`.

## Conventions

- Component content (parts list, tubing steps, wiring) in `data/*.yaml`. `main.py` keeps the project rules (wire labels, cable kinds, two wires per screw) and converts to the BuildGuide data format; the `buildguide` MkDocs plugin checks the result and fails the build on a problem.
- Page text, component placement and the safety snippets: see `docs/AGENTS.md`.
- No third-party requests: `font: false`, and the header repository facts are fetched at build time by `hooks/repo_facts.py` and rendered by `overrides/partials/source.html` (not Material's `data-md-component="source"`), so the browser calls nothing; the browser check fails on external requests.
- Safety warning without exact force or pressure figures.
- Header title `site_name` stays short (the long name is cut off at 390 px). Footer links are the HTML in `copyright:` of `mkdocs.yml`; the 404 is `overrides/404.html`. A MakerWorld link follows when an address exists (issue #23).
- Branches: `main` is the only long-lived branch. Work on short-lived branches; pull requests target `main` and are squash-merged. Required checks of `.github/workflows/ci.yml`: `check`, `lint-python`, `workflows`, `dependency-review`. Pull request titles are Conventional Commits (`pr-title.yml`). release-please keeps one release pull request open and `release-weekly.yml` merges it on Mondays. Pages (`pages.yml`): the root is the latest release, `/next/` is `main`.

## Agent skills

- Issue tracker: GitHub Issues (`gh` CLI), see `docs/agents/issue-tracker.md`.
- Triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, see `docs/agents/triage-labels.md`.
- Domain docs: single-context, `GLOSSARY.md` and `docs/adr/` at the repo root, see `docs/agents/domain.md`.
