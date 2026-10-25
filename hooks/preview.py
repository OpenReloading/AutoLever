"""Preview build only (mkdocs.develop.yml): the preview lists itself nowhere, so its sitemap is not published."""

from pathlib import Path


def on_post_build(config):
    for name in ("sitemap.xml", "sitemap.xml.gz"):
        Path(config["site_dir"], name).unlink(missing_ok=True)
