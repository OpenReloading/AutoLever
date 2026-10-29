Page text is Markdown here, not in `data/guide.yaml`. The BOM and the boards come from `data/buildguide.json` through `<div data-buildguide="bom"></div>` and `<div data-buildguide="board" data-board="KEY"></div>` (`KEY`: `wiring`, `relay` (deprecated relay edition) or `tubing`); a page may hold several.

The safety warning is the `!!! danger "Safety"` admonition at the top of each page and includes its text from `snippets/` (`--8<-- "safety.md"`, full on the introduction and BOM; `safety-short.md`, on wiring and tubing, with a link to the introduction, and once more above "Build it" on the introduction). Change the wording there only. Keep it free of exact force or pressure figures.

The pre-release notice is the `!!! warning "Status"` block on the introduction and the `hero-label` line above its title, with the matching bold line in `README.md`. When the first build is done, delete all three, and with the label its `.hero-label` rules in `docs/stylesheets/extra.css`.
