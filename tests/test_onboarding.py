import json
import socket
import sys

import pytest
import yaml

from codetrail.config import load_config
from codetrail.onboarding import doctor_report, initialize_config


@pytest.fixture
def configuration(tmp_path):
    def create(**overrides):
        provider = {"name": "test", "protocol": "openai", "base_url": "https://example.invalid/v1",
                    "model": "test-model", "api_key": "dummy-unit-test-credential"}
        provider.update(overrides.pop("provider", {}))
        config = {"providers": [provider], **overrides}
        path = tmp_path / "diagnostic.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        return path
    return create


def test_initialize_default_template_and_preserve_existing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = initialize_config()
    assert path == tmp_path / ".codetrail" / "config.yaml"
    assert load_config(path).providers[0].api_key == "${OPENAI_API_KEY}"
    path.write_text("existing-personal-configuration", encoding="utf-8")
    with pytest.raises(FileExistsError):
        initialize_config()
    assert path.read_text(encoding="utf-8") == "existing-personal-configuration"


def test_initialize_explicit_nested_path(tmp_path):
    target = tmp_path / "nested" / "custom.yaml"
    assert initialize_config(target) == target
    assert load_config(target).permission_mode == "default"


def test_doctor_is_offline_and_excludes_secrets(configuration, monkeypatch):
    def forbid_network(*args, **kwargs):
        raise AssertionError("Doctor must be offline")
    monkeypatch.setattr(socket, "create_connection", forbid_network)
    path = configuration(mcp_servers=[
        {"name": "private-server-name", "command": sys.executable, "args": ["must-not-run.py"],
         "env": {"PRIVATE_TOKEN": "dummy-mcp-secret"}},
        {"name": "remote", "url": "https://example.invalid/mcp",
         "headers": {"Authorization": "Bearer dummy-header-secret"}},
    ])
    report = doctor_report(path)
    assert report["ok"]
    output = json.dumps(report)
    for value in ["dummy-unit-test-credential", "dummy-mcp-secret", "dummy-header-secret", "private-server-name"]:
        assert value not in output
    assert any(c["name"] == "mcp[2].connection" and c["status"] == "warn" for c in report["checks"])


def test_malformed_yaml_does_not_echo_parser_context(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text('providers: [\napi_key: "dummy-sensitive-line"\n', encoding="utf-8")
    report = doctor_report(path)
    assert not report["ok"]
    assert "dummy-sensitive-line" not in json.dumps(report)


def test_missing_file_reports_failure(tmp_path):
    assert not doctor_report(tmp_path / "missing.yaml")["ok"]


@pytest.mark.parametrize("key", ["", "your-api-key-here", "${CODETRAIL_MISSING_TEST_KEY}"])
def test_missing_or_placeholder_credentials_fail(configuration, monkeypatch, key):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODETRAIL_MISSING_TEST_KEY", raising=False)
    report = doctor_report(configuration(provider={"api_key": key}))
    assert not report["ok"]
    assert any(c["name"].endswith(".credentials") and c["status"] == "fail" for c in report["checks"])


@pytest.mark.parametrize("endpoint", ["no-scheme", "file:///tmp/test", "https://example.invalid:bad", "https://[bad"])
def test_invalid_endpoint_fails_without_crashing(configuration, endpoint):
    report = doctor_report(configuration(provider={"base_url": endpoint}))
    assert not report["ok"]


@pytest.mark.parametrize("field,value", [("name", []), ("protocol", {}), ("base_url", 123), ("model", ""), ("api_key", None)])
def test_invalid_provider_types_fail_without_crashing(configuration, field, value):
    assert not doctor_report(configuration(provider={field: value}))["ok"]


def test_missing_mcp_executable_fails(configuration):
    path = configuration(mcp_servers=[{"name": "test", "command": "codetrail-nonexistent-test-executable"}])
    assert not doctor_report(path)["ok"]
