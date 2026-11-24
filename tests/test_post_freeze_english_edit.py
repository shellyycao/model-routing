"""The post-freeze English-only edit must not weaken the frozen-hash checks (see PROVENANCE.md)."""

import shutil

import pytest

from src.bedrock import provenance


@pytest.mark.parametrize("rel", sorted(provenance._POST_FREEZE_ENGLISH_EDITS))
def test_edited_files_have_exactly_the_documented_edit(rel):
    text = (provenance._REPO_ROOT / rel).read_text(encoding="utf-8")
    for current, _frozen in provenance._POST_FREEZE_ENGLISH_EDITS[rel]:
        assert text.count(current) == 1
    assert provenance._frozen_bytes(provenance._REPO_ROOT / rel) is not None


@pytest.mark.parametrize("rel", sorted(provenance._POST_FREEZE_ENGLISH_EDITS))
def test_any_other_change_still_changes_the_hash(rel, tmp_path, monkeypatch):
    original = provenance._REPO_ROOT / rel
    before = provenance.hash_file(original)
    fake_root = tmp_path / "repo"
    copy = fake_root / rel
    copy.parent.mkdir(parents=True)
    shutil.copyfile(original, copy)
    monkeypatch.setattr(provenance, "_REPO_ROOT", fake_root)
    assert provenance.hash_file(copy) == before
    copy.write_text(copy.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    assert provenance.hash_file(copy) != before
