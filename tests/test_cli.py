import json
import os
import subprocess
import sys

import pytest

from codetrail import __version__
from codetrail.onboarding import initialize_config


def run_cli(cwd, *args):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["OPENAI_API_KEY"] = "dummy-cli-test-credential"
    return subprocess.run([sys.executable, "-m", "codetrail", *args], cwd=cwd,
                          env=env, capture_output=True, text=True, encoding="utf-8", timeout=20)


@pytest.mark.parametrize("option", ["--help", "--version"])
def test_information_commands_have_no_runtime_files(tmp_path, option):
    completed = run_cli(tmp_path, option)
    assert completed.returncode == 0, completed.stderr
    assert "CodeTrail" in completed.stdout
    assert not (tmp_path / ".codetrail").exists()


def test_init_refuses_to_overwrite_from_cli(tmp_path):
    first = run_cli(tmp_path, "--init")
    assert first.returncode == 0, first.stderr
    target = tmp_path / ".codetrail" / "config.yaml"
    original = target.read_bytes()
    second = run_cli(tmp_path, "--init")
    assert second.returncode == 1
    assert target.read_bytes() == original
    assert not (target.parent / "debug.log").exists()


def test_doctor_json_and_exit_code_with_explicit_config(tmp_path):
    target = initialize_config(tmp_path / "isolated.yaml")
    completed = run_cli(tmp_path, "--config", str(target), "--doctor", "--json")
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["ok"]
    assert report["version"] == __version__
    assert "dummy-cli-test-credential" not in completed.stdout
    assert not (tmp_path / ".codetrail").exists()


def test_doctor_missing_file_returns_failure_json(tmp_path):
    completed = run_cli(tmp_path, "--doctor", "--json", "--config", str(tmp_path / "missing.yaml"))
    assert completed.returncode == 1
    assert not json.loads(completed.stdout)["ok"]


def test_prompt_missing_environment_reference_is_a_clean_error(tmp_path):
    target = initialize_config(tmp_path / "isolated.yaml")
    target.write_text(target.read_text(encoding="utf-8").replace(
        "${OPENAI_API_KEY}", "${CODETRAIL_UNIT_TEST_UNSET_VARIABLE}"
    ), encoding="utf-8")
    completed = run_cli(tmp_path, "--config", str(target), "-p", "Never sent to a model")
    assert completed.returncode == 1
    assert "unset environment variable" in completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.asyncio
async def test_tui_missing_environment_reference_is_a_visible_error(tmp_path, monkeypatch):
    from codetrail.app import CodeTrailApp
    from codetrail.config import ProviderConfig

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CODETRAIL_UNIT_TEST_UNSET_VARIABLE", raising=False)
    app = CodeTrailApp(providers=[ProviderConfig(
        "test", "openai", "https://example.invalid", "test",
        api_key="${CODETRAIL_UNIT_TEST_UNSET_VARIABLE}",
    )])
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.agent is None
        assert "unset environment variable" in str(app.screen.query_one(".error-message").content)


@pytest.mark.parametrize("arguments", [
    ["--json"], ["--init", "--doctor"], ["--doctor", "-p", "test"], ["--init", "--remote"],
])
def test_conflicting_cli_modes_are_rejected_without_side_effects(tmp_path, arguments):
    completed = run_cli(tmp_path, *arguments)
    assert completed.returncode == 2
    assert not (tmp_path / ".codetrail").exists()
