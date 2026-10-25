# AutoLever

## Commands

- Agents run on the host; file edits and Git stay there. Start the container with `devcontainer up --docker-path podman --workspace-folder .` (creates `.venv` with `requirements.txt`); run project commands with the prefix `devcontainer exec --docker-path podman --workspace-folder .`.
- Install: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Lint (as CI): `.venv/bin/pip install --only-binary :all: --require-hashes -r requirements-dev.txt`, then `.venv/bin/ruff check .` and `.venv/bin/basedpyright --pythonpath .venv/bin/python` (rules in `pyproject.toml`). `requirements-dev.txt` is compiled from `requirements-dev.in` on Python 3.13: `pip-compile --generate-hashes --output-file=requirements-dev.txt requirements-dev.in`
- Build (as CI): `.venv/bin/mkdocs build --strict`
- Serve: `.venv/bin/mkdocs serve -a 0.0.0.0:8000`
- Unit tests with coverage (CI; pytest is in `requirements-dev.txt`, install it as in the lint line): `.venv/bin/pytest --cov`; prints the summary and fails below `fail_under` in `[tool.coverage.report]` of `pyproject.toml`. Raise the floor when coverage rises, keep it a little below the measured value. Not measured: `tests/` and the browser check `tests/check_guide.py` (needs the built site, below).
- Generate the guide data after editing `data/*.yaml`: `.venv/bin/python main.py` (writes `data/buildguide.json`, committed; CI fails when it is stale)
- Browser check, against the built site (`mkdocs serve` livereload counts as an external request): `.venv/bin/mkdocs build --strict -d /tmp/www/AutoLever && python -m http.server -d /tmp/www 8000`, then `.venv/bin/python tests/check_guide.py http://127.0.0.1:8000/AutoLever`
- Preview build (as CI): `.venv/bin/mkdocs build --strict -d /tmp/www/AutoLever && .venv/bin/mkdocs build --strict -f mkdocs.develop.yml -d /tmp/www/AutoLever/develop`, then the browser check with `http://127.0.0.1:8000/AutoLever/develop`; it also checks that `noindex` and the banner are on every page of the preview and the sitemap is not, and the reverse on the root.
- Playwright MCP (`.mcp.json`, `.codex/config.toml`) runs inside the container and reaches the served site at `http://127.0.0.1:8000/AutoLever/`.

## Conventions

- Component content (parts list, tubing steps, wiring) in `data/*.yaml`. `main.py` keeps the project rules (wire labels, cable kinds, two wires per screw) and converts to the BuildGuide data format; the `buildguide` MkDocs plugin checks the result and fails the build on a problem.
- Page text is Markdown in `docs/`; the BOM, wiring and tubing components are placed with `<div data-buildguide="bom"></div>` and `<div data-buildguide="board" data-board="wiring"></div>`. The safety text lives once in `snippets/` (full on the introduction and BOM pages, short on wiring and tubing), see `docs/AGENTS.md`.
- No third-party requests: `font: false`, `repo_url` is set, but without Material's `data-md-component="source"`: `hooks/repo_facts.py` fetches the header facts (tag, stars, forks) from the GitHub API at build time and `overrides/partials/source.html` renders them, so the browser calls nothing; the browser check fails on external requests.
- Safety warning without exact force or pressure figures.
- Header title `site_name` stays short (the long name is cut off at 390 px). Footer links (repository, Discord, licence file) are the HTML in `copyright:` of `mkdocs.yml`, previous and next links come from `navigation.footer`, the 404 is `overrides/404.html`. A MakerWorld link follows when an address exists (issue #23).
- Branches: pull requests target `develop` (squash merge). `main` holds releases and changes only by a promotion pull request `develop` to `main`, merged with a merge commit. The site deploys from `main`; `develop` is published next to it as a preview under `/develop/`: the `Pages` workflow (`.github/workflows/pages.yml`) builds `main` at the root and `develop` with `mkdocs.develop.yml` (inherits `mkdocs.yml`; `site_url` with `/develop/`, `extra.preview` makes `overrides/main.html` add `noindex` and a banner, `hooks/preview.py` drops the sitemap) into one artifact. A preview build that fails only warns; the root still deploys. The `Promote` workflow (`.github/workflows/promote.yml`) opens and updates that pull request on every push to `develop`.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
