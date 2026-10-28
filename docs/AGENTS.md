Page text is Markdown here, not in `data/guide.yaml`. The BOM and the boards come from `data/buildguide.json` through `<div data-buildguide="bom"></div>` and `<div data-buildguide="board" data-board="KEY"></div>` (`KEY`: `wiring`, `relay` (deprecated relay edition) or `tubing`); a page may hold several.

The safety warning is the `!!! danger "Safety"` admonition at the top of each page and includes its text from `snippets/` (`--8<-- "safety.md"`, full on the introduction and BOM; `safety-short.md`, on wiring and tubing, with a link to the introduction). Change the wording there only. Keep it free of exact force or pressure figures.

The pre-release notice is the `!!! warning "Pre-release, October 2026"` block on the introduction, with the matching bold line in `README.md`. When the first build is done, delete both.
