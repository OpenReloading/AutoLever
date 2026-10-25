"""Unit test of hooks/preview.py: the preview build drops its sitemap and leaves other files alone."""
import preview


def test_sitemap_is_removed_and_other_files_stay(tmp_path):
    for name in ("sitemap.xml", "sitemap.xml.gz", "index.html"):
        (tmp_path / name).write_text("x")
    preview.on_post_build({"site_dir": str(tmp_path)})
    assert [p.name for p in tmp_path.iterdir()] == ["index.html"]


def test_missing_sitemap_is_not_an_error(tmp_path):
    preview.on_post_build({"site_dir": str(tmp_path)})
