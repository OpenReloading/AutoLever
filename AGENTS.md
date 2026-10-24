# AutoLever

## Commands

- Agents run on the host; file edits and Git stay there. Start the container with `devcontainer up --docker-path podman --workspace-folder .` (creates `.venv` with `requirements.txt`); run project commands with the prefix `devcontainer exec --docker-path podman --workspace-folder .`.
- Install: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Build (as CI): `.venv/bin/mkdocs build --strict`
- Serve: `.venv/bin/mkdocs serve -a 0.0.0.0:8000`
- Generate the guide data after editing `data/*.yaml`: `.venv/bin/python main.py` (writes `data/buildguide.json`, committed; CI fails when it is stale)
- Browser check, against the built site (`mkdocs serve` livereload counts as an external request): `.venv/bin/mkdocs build --strict -d /tmp/www/AutoLever && python -m http.server -d /tmp/www 8000`, then `.venv/bin/python tests/check_guide.py http://127.0.0.1:8000/AutoLever`
- Playwright MCP (`.mcp.json`, `.codex/config.toml`) runs inside the container and reaches the served site at `http://127.0.0.1:8000/AutoLever/`.

## Conventions

- Component content (parts list, tubing steps, wiring) in `data/*.yaml`. `main.py` keeps the project rules (wire labels, cable kinds, two wires per screw) and converts to the BuildGuide data format; the `buildguide` MkDocs plugin checks the result and fails the build on a problem.
- Page text is Markdown in `docs/`; the BOM, wiring and tubing components are placed with `<div data-buildguide="bom"></div>` and `<div data-buildguide="board" data-board="wiring"></div>`. The safety text lives once in `snippets/` (full on the introduction and BOM pages, short on wiring and tubing), see `docs/AGENTS.md`.
- No third-party requests: `font: false`, `repo_url` is set, but without Material's `data-md-component="source"`: `hooks/repo_facts.py` fetches the header facts (tag, stars, forks) from the GitHub API at build time and `overrides/partials/source.html` renders them, so the browser calls nothing; the browser check fails on external requests.
- Safety warning without exact force or pressure figures.
- Branches: pull requests target `develop` (squash merge). `main` holds releases and changes only by a promotion pull request `develop` to `main`, merged with a merge commit. The site deploys from `main`. The `Promote` workflow (`.github/workflows/promote.yml`) opens and updates that pull request on every push to `develop`.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
