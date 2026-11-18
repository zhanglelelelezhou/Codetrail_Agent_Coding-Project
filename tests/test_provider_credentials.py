"""Regression tests for real configuration-to-provider credential resolution."""

import pytest
import yaml

from codetrail.config import ConfigError, ProviderConfig, load_config


def test_loaded_provider_resolves_environment_reference(tmp_path, monkeypatch):
    monkeypatch.setenv("CODETRAIL_UNIT_TEST_KEY", "dummy-provider-credential")
    path = tmp_path / "provider.yaml"
    path.write_text(yaml.safe_dump({"providers": [{
        "name": "test", "protocol": "openai", "base_url": "https://example.invalid/v1",
        "model": "test-model", "api_key": "${CODETRAIL_UNIT_TEST_KEY}",
    }]}), encoding="utf-8")
    provider = load_config(path).providers[0]
    assert provider.resolve_api_key() == "dummy-provider-credential"
    assert provider.api_key == "${CODETRAIL_UNIT_TEST_KEY}"


def test_missing_environment_reference_fails_without_disclosing_values(monkeypatch):
    monkeypatch.delenv("CODETRAIL_UNIT_TEST_MISSING", raising=False)
    provider = ProviderConfig("test", "openai", "https://example.invalid", "test",
                              api_key="private-prefix-${CODETRAIL_UNIT_TEST_MISSING}")
    with pytest.raises(ConfigError) as error:
        provider.resolve_api_key()
    assert "private-prefix" not in str(error.value)
    assert "unset environment variable" in str(error.value)


@pytest.mark.parametrize("protocol,variable", [
    ("openai", "OPENAI_API_KEY"), ("openai-compat", "OPENAI_API_KEY"),
    ("anthropic", "ANTHROPIC_API_KEY"),
])
def test_default_environment_fallback(protocol, variable, monkeypatch):
    monkeypatch.setenv(variable, "dummy-fallback-credential")
    provider = ProviderConfig("test", protocol, "https://example.invalid", "test")
    assert provider.resolve_api_key() == "dummy-fallback-credential"


def test_literal_credential_takes_precedence_over_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-environment-credential")
    provider = ProviderConfig("test", "openai", "https://example.invalid", "test", api_key="dummy-explicit")
    assert provider.resolve_api_key() == "dummy-explicit"
