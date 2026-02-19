from pathlib import Path

from transctl.models.translation_resource import TAG, TranslationLayouts, TranslationResource

import pytest


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    return path


def test_from_obj_rejects_non_dict():
    with pytest.raises(TypeError, match="Invalid resource configuration"):
        TranslationResource.from_obj(resource="not-a-dict")


def test_from_obj_missing_path_raises_value_error():
    with pytest.raises(ValueError, match=r"Key 'path' is missing"):
        TranslationResource.from_obj(resource={"layout": TranslationLayouts.BY_LANGUAGE.value})


def test_from_obj_invalid_layout_raises_value_error(tmp_path: Path):
    # Ensure we don’t hit the "no matches -> None" branch before layout validation
    f = _touch(tmp_path / "a.json")

    with pytest.raises(ValueError, match=r"Invalid layout"):
        TranslationResource.from_obj(
            resource={"path": str(f), "layout": "definitely-not-a-layout"}
        )


def test_from_obj_returns_none_when_glob_matches_nothing(tmp_path: Path):
    pattern = str(tmp_path / "**" / "nope-*.json")
    res = TranslationResource.from_obj(resource={"path": pattern})
    assert res is None


def test_from_obj_skips_directories_and_can_return_empty_bucket(tmp_path: Path):
    # glob will match this directory but os.path.isfile will be False, so it’s skipped
    d = tmp_path / "some_dir"
    d.mkdir()

    res = TranslationResource.from_obj(resource={"path": str(d)})
    assert res is not None
    assert res.bucket == []


def test_from_obj_collects_only_files_when_glob_matches_files_and_dirs(tmp_path: Path):
    d = tmp_path / "mixed"
    d.mkdir()
    _touch(d / "a.json")
    _touch(d / "b.json")
    (d / "subdir").mkdir()

    # This pattern will match files AND directories under `mixed`
    pattern = str(d / "*")
    res = TranslationResource.from_obj(resource={"path": pattern})

    assert res is not None
    # Only files should be in bucket; directory entries are skipped
    sources = [src for src, _ in res.bucket]
    assert set(sources) == {d / "a.json", d / "b.json"}


def test_from_obj_layout_none_no_tags_prefixes_output_filename(tmp_path: Path):
    f = _touch(tmp_path / "messages.json")

    res = TranslationResource.from_obj(resource={"path": str(f), "layout": None})
    assert res is not None
    assert len(res.bucket) == 1

    src, out = res.bucket[0]
    assert src == f
    assert out.parent == f.parent
    assert out.name == f"{TAG}_{f.name}"


def test_from_obj_layout_along_sided_prefixes_output_filename(tmp_path: Path):
    f = _touch(tmp_path / "messages.json")

    res = TranslationResource.from_obj(
        resource={"path": str(f), "layout": TranslationLayouts.ALONG_SIDED.value}
    )
    assert res is not None
    assert len(res.bucket) == 1

    src, out = res.bucket[0]
    assert src == f
    assert out.name == f"{TAG}_{f.name}"


def test_from_obj_layout_by_language_keeps_output_name_unchanged(tmp_path: Path):
    f = _touch(tmp_path / "messages.json")

    res = TranslationResource.from_obj(
        resource={"path": str(f), "layout": TranslationLayouts.BY_LANGUAGE.value}
    )
    assert res is not None
    assert len(res.bucket) == 1

    src, out = res.bucket[0]
    assert src == f
    # In the current implementation, BY_LANGUAGE does a no-op transformation
    assert out == f


def test_from_obj_tag_in_path_requires_key_or_replace_raises(tmp_path: Path):
    # Create a file that would match once tag is decoded, but call with key=None
    key = "en"
    _touch(tmp_path / key / "messages.json")

    # Pattern includes TAG and requires decoding; passing key=None causes str.replace to TypeError
    pattern = str(tmp_path / TAG / "messages.json")
    with pytest.raises(TypeError):
        TranslationResource.from_obj(resource={"path": pattern}, path_resolution_key=None)


def test_from_obj_decodes_tag_and_restores_tag_in_output_when_layout_none(tmp_path: Path):
    key = "en"
    actual = _touch(tmp_path / key / "messages.json")

    pattern = str(tmp_path / TAG / "messages.json")
    res = TranslationResource.from_obj(resource={"path": pattern}, path_resolution_key=key)

    assert res is not None
    assert len(res.bucket) == 1

    src, out = res.bucket[0]
    assert src == actual
    # layout is None but there *are* tag indices, so it must NOT prefix TAG_.
    # Output path should be restored to the original tagged pattern.
    assert out == Path(pattern)


def test_from_obj_multiple_tag_occurrences_restored_in_output(tmp_path: Path):
    key = "en"
    # Example: "<tmp>/en/messages.en.json" should match decoded path
    actual = _touch(tmp_path / key / f"messages.{key}.json")

    # Pattern contains TAG twice
    pattern = str(tmp_path / TAG / f"messages.{TAG}.json")
    res = TranslationResource.from_obj(resource={"path": pattern}, path_resolution_key=key)

    assert res is not None
    assert len(res.bucket) == 1

    src, out = res.bucket[0]
    assert src == actual
    # Output should restore both TAG occurrences
    assert out == Path(pattern)


def test_from_obj_with_tags_and_along_sided_still_prefixes_filename(tmp_path: Path):
    key = "en"
    actual = _touch(tmp_path / key / "messages.json")

    pattern = str(tmp_path / TAG / "messages.json")
    res = TranslationResource.from_obj(
        resource={"path": pattern, "layout": TranslationLayouts.ALONG_SIDED.value},
        path_resolution_key=key,
    )

    assert res is not None
    assert len(res.bucket) == 1

    src, out = res.bucket[0]
    assert src == actual
    # Since layout==ALONG_SIDED, output file name is prefixed even when tags exist.
    # Parent should be the restored tagged directory.
    assert out.parent == Path(tmp_path / TAG)
    assert out.name == f"{TAG}_messages.json"
