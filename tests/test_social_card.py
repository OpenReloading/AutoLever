"""Unit test of tools/social_card.py: the card page takes its colours from the light tokens and its text from mkdocs.yml (the PNG itself is checked by tests/check_guide.py)."""
import html
import re
from pathlib import Path

from tools import social_card
from tools.site_config import site_config


def test_site_url_takes_the_default_of_the_environment_tag():
    assert site_config()["site_url"] == "https://openreloading.github.io/AutoLever/"


def test_card_page_uses_the_light_tokens_and_the_site_description():
    page = social_card.card_html()
    css = Path(social_card.ROOT, "docs/stylesheets/extra.css").read_text(encoding="utf-8")
    light = css.split("}", 1)[0]
    description = site_config()["site_description"]
    assert html.escape(description) in page
    assert "#000" not in page  # the black logo is recoloured
    for name in ("page", "ink", "accent"):
        token = re.search(rf"--{name}:\s*(#\w+);", light)
        assert token
        assert token[1] in page, name
    assert "width:1200px;height:630px" in page
