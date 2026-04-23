"""Tests for cronwatch.watermark."""
import os
import pytest

from cronwatch.watermark import (
    WatermarkPolicy,
    get_watermark_path,
    load_watermarks,
    save_watermarks,
    update_watermarks,
)
from cronwatch.runner import JobResult


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


def _make_result(command="backup.sh", exit_code=0, duration=5.0, stdout="ok", stderr=""):
    return JobResult(
        command=command,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration=duration,
    )


def test_watermark_policy_defaults():
    p = WatermarkPolicy()
    assert p.enabled is False
    assert p.track_duration is True
    assert p.track_output_bytes is True


def test_watermark_policy_from_config_none_returns_defaults():
    p = WatermarkPolicy.from_config(None)
    assert p.enabled is False


def test_watermark_policy_from_config_sets_fields():
    p = WatermarkPolicy.from_config({"enabled": True, "track_duration": False})
    assert p.enabled is True
    assert p.track_duration is False
    assert p.track_output_bytes is True


def test_watermark_policy_invalid_enabled_raises():
    with pytest.raises(TypeError):
        WatermarkPolicy(enabled="yes")  # type: ignore[arg-type]


def test_get_watermark_path_uses_log_dir(log_dir):
    path = get_watermark_path("myjob", log_dir)
    assert path.startswith(log_dir)
    assert "myjob" in path
    assert path.endswith(".watermark.json")


def test_load_watermarks_returns_empty_when_no_file(log_dir):
    marks = load_watermarks("nojob", log_dir)
    assert marks == {}


def test_save_and_load_roundtrip(log_dir):
    data = {"duration": 12.5, "output_bytes": 1024.0}
    save_watermarks("myjob", data, log_dir)
    loaded = load_watermarks("myjob", log_dir)
    assert loaded == data


def test_update_watermarks_disabled_returns_empty(log_dir):
    policy = WatermarkPolicy(enabled=False)
    result = _make_result(duration=10.0)
    marks = update_watermarks(result, policy, log_dir)
    assert marks == {}


def test_update_watermarks_records_duration(log_dir):
    policy = WatermarkPolicy(enabled=True)
    result = _make_result(duration=7.3)
    marks = update_watermarks(result, policy, log_dir)
    assert marks["duration"] == pytest.approx(7.3)


def test_update_watermarks_keeps_higher_duration(log_dir):
    policy = WatermarkPolicy(enabled=True)
    update_watermarks(_make_result(duration=3.0), policy, log_dir)
    update_watermarks(_make_result(duration=10.0), policy, log_dir)
    marks = load_watermarks("backup.sh", log_dir)
    assert marks["duration"] == pytest.approx(10.0)


def test_update_watermarks_does_not_lower_duration(log_dir):
    policy = WatermarkPolicy(enabled=True)
    update_watermarks(_make_result(duration=10.0), policy, log_dir)
    update_watermarks(_make_result(duration=2.0), policy, log_dir)
    marks = load_watermarks("backup.sh", log_dir)
    assert marks["duration"] == pytest.approx(10.0)


def test_update_watermarks_records_output_bytes(log_dir):
    policy = WatermarkPolicy(enabled=True)
    result = _make_result(stdout="hello", stderr="world")
    marks = update_watermarks(result, policy, log_dir)
    assert marks["output_bytes"] == float(len(b"hello") + len(b"world"))


def test_update_watermarks_skip_duration_when_disabled(log_dir):
    policy = WatermarkPolicy(enabled=True, track_duration=False)
    result = _make_result(duration=99.0)
    marks = update_watermarks(result, policy, log_dir)
    assert "duration" not in marks
