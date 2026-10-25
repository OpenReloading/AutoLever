"""Unit tests of hooks/repo_facts.py: header facts come from the API, any failure leaves them out."""
import types
import urllib.error

import pytest
import repo_facts


@pytest.fixture(autouse=True)
def clean_cache(monkeypatch):
    monkeypatch.setattr(repo_facts, "_cache", {})


def fake_api(monkeypatch, answers):
    """Answers by API path; an exception instance is raised."""
    def get(path):
        answer = answers[path]
        if isinstance(answer, Exception):
            raise answer
        return answer
    monkeypatch.setattr(repo_facts, "_get", get)


class Config(types.SimpleNamespace):
    """The part of MkDocs' config the hook uses: .get() and .extra."""

    def __init__(self, repo_url):
        super().__init__(repo_url=repo_url, extra={})

    def get(self, key, default=None):
        return getattr(self, key, default)


REPO = {"stargazers_count": 1234, "forks_count": 7}


@pytest.mark.parametrize(("n", "text"), [(0, "0"), (999, "999"), (1000, "1k"), (1234, "1.2k"), (9999, "10k"), (15200, "15.2k")])
def test_counts_are_rounded_like_materials_script(n, text):
    assert repo_facts._count(n) == text


def test_the_header_gets_tag_stars_and_forks(monkeypatch):
    fake_api(monkeypatch, {"o/r": REPO, "o/r/releases/latest": {"tag_name": "v1.2"}})
    config = repo_facts.on_config(Config("https://github.com/o/r/"))
    assert config.extra["repo_facts"] == {"version": "v1.2", "stars": "1.2k", "forks": "7"}


def test_without_a_release_the_newest_tag_is_used(monkeypatch):
    fake_api(monkeypatch, {"o/r": REPO, "o/r/releases/latest": OSError("404"), "o/r/tags": [{"name": "v0.9"}]})
    assert repo_facts._facts("o/r")["version"] == "v0.9"


def test_without_release_and_tag_the_version_is_left_out(monkeypatch):
    fake_api(monkeypatch, {"o/r": REPO, "o/r/releases/latest": OSError("404"), "o/r/tags": []})
    assert repo_facts._facts("o/r") == {"stars": "1.2k", "forks": "7"}


def test_an_api_failure_leaves_the_facts_out_and_is_not_asked_twice(monkeypatch):
    calls = []

    def get(path):
        calls.append(path)
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(repo_facts, "_get", get)
    for _ in range(2):
        config = repo_facts.on_config(Config("https://github.com/o/r"))
        assert config.extra["repo_facts"] == {}
    assert calls == ["o/r"]


@pytest.mark.parametrize("repo_url", [None, "", "https://example.org/o/r", "https://github.com/o"])
def test_a_repo_url_that_is_not_a_github_repo_changes_nothing(monkeypatch, repo_url):
    fake_api(monkeypatch, {})
    config = repo_facts.on_config(Config(repo_url))
    assert config.extra == {}


@pytest.mark.parametrize(("token", "auth"), [("t0ken", "Bearer t0ken"), (None, None)])
def test_the_token_is_sent_only_when_set(monkeypatch, token, auth):
    seen = {}

    class Reply:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"{}"

    def urlopen(request, timeout):
        seen["auth"] = request.get_header("Authorization")
        return Reply()
    if token:
        monkeypatch.setenv("GITHUB_TOKEN", token)
    else:
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(repo_facts.urllib.request, "urlopen", urlopen)
    assert repo_facts._get("o/r") == {}
    assert seen["auth"] == auth
