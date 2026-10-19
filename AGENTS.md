# AutoLever

## Commands

- Agents run on the host; file edits and Git stay there. Start the container with `devcontainer up --docker-path podman --workspace-folder .` (creates `.venv` with `requirements.txt`); run project commands with the prefix `devcontainer exec --docker-path podman --workspace-folder .`.
- Install: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Build (as CI): `.venv/bin/mkdocs build --strict`
- Serve: `.venv/bin/mkdocs serve -a 0.0.0.0:8000`
- Browser check, with the site served: `.venv/bin/python tests/check_guide.py http://127.0.0.1:8000/AutoLever` (`site_url` serves under `/AutoLever/`)
- Playwright MCP (`.mcp.json`, `.codex/config.toml`) runs inside the container and reaches the served site at `http://127.0.0.1:8000/AutoLever/`.

## Conventions

- Content in `data/*.yaml`; `main.py` asserts wiring rules, `on_error_fail: true` fails the build.
- No third-party requests: `font: false`, `docs/assets/vendor/` unmodified; the browser check fails on external requests.
- Safety warning without exact force or pressure figures.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`gh` CLI). See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
