"""Writes docs/assets/social-card.png (1200 x 630) from the logo, the light palette tokens of extra.css and the
site description in mkdocs.yml. Run after changing any of them, in the dev container (needs Chromium):
.venv/bin/python -m tools.social_card
"""
import html
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from tools.site_config import site_config

ROOT = Path(__file__).parent.parent
OUT = ROOT / "docs/assets/social-card.png"


def card_html() -> str:
    config = site_config()
    css = (ROOT / "docs/stylesheets/extra.css").read_text(encoding="utf-8")
    light = css.split("}", 1)[0]  # the first rule is the light scheme
    token = dict(re.findall(r"--([\w-]+):\s*(#\w+);", light))
    logo = (ROOT / "docs/assets/autolever-logo.svg").read_text(encoding="utf-8").replace("#000", token["accent"])  # color and stroke of the black logo
    return f"""<body style="margin:0;width:1200px;height:630px;background:{token["page"]};font:38px/1.4 system-ui,sans-serif;color:{token["ink"]}">
<div style="position:absolute;left:80px;top:90px;width:560px">{logo}</div>
<p style="position:absolute;left:80px;top:330px;width:1040px;margin:0">{html.escape(config["site_description"])}</p>
<div style="position:absolute;left:0;bottom:0;width:1200px;height:24px;background:{token["accent"]}"></div></body>"""


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1200, "height": 630})
        page.set_content(card_html())
        page.screenshot(path=OUT)
        browser.close()
