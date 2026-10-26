"""Unit test of overrides/main.html: values inserted into the link preview meta are escaped (MkDocs templates have no autoescape)."""
from pathlib import Path
from types import SimpleNamespace

from jinja2 import DictLoader, Environment


def render(title, description):
    stub = "{% block extrahead %}{% endblock %}"
    source = Path(__file__).parent.parent.joinpath("overrides/main.html").read_text(encoding="utf-8")
    config = SimpleNamespace(
        site_name='Auto"Lever', site_description=description, site_url="https://example.org/x/"
    )
    page = SimpleNamespace(title=title, is_homepage=False, canonical_url='https://example.org/x/a"b/')
    return Environment(loader=DictLoader({"base.html": stub, "main.html": source})).get_template("main.html").render(config=config, page=page)


def test_quotes_and_angle_brackets_stay_inside_the_attribute():
    out = render('Say "hi"', 'a "b" <c>')
    assert 'content="Say &#34;hi&#34; - Auto&#34;Lever"' in out
    assert 'content="a &#34;b&#34; &lt;c&gt;"' in out
    assert 'content="https://example.org/x/a&#34;b/"' in out
    assert 'content="Say "' not in out
