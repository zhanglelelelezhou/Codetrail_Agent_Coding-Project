"""Local setup and diagnostics. No model, MCP process, or hook is executed here."""

from __future__ import annotations

import platform
import shutil
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from codetrail import __version__
from codetrail.config import ConfigError, load_config


def initialize_config(path: Path | None = None) -> Path:
    """Write a packaged template, refusing to overwrite an existing file."""
    target = path if path is not None else Path.cwd() / ".codetrail" / "config.yaml"
    template = files("codetrail").joinpath("resources/config.yaml.example").read_text(encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(template)
    return target


def doctor_report(path: Path | None = None) -> dict:
    """Return an allowlist of diagnostic fields, never raw config or exceptions."""
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    def result() -> dict:
        return {
            "schema_version": 1,
            "project": "CodeTrail",
            "version": __version__,
            "ok": not any(item["status"] == "fail" for item in checks),
            "checks": checks,
        }

    add("python", "pass", platform.python_version())
    add("git", "pass" if shutil.which("git") else "warn", "Git is optional for chat and required for worktree features.")
    try:
        config = load_config(path)
    except (ConfigError, OSError, TypeError, ValueError):
        # Parser exceptions may include the offending YAML line, including secrets.
        add("config", "fail", "Cannot load configuration. Run --init if missing; otherwise check YAML syntax and required fields.")
        return result()
    add("config", "pass", "Configuration loaded and structure validated.")

    placeholders = {"your-api-key-here", "your-api-key", "your_api_key", "changeme", "replace-me"}
    for index, provider in enumerate(config.providers, start=1):
        prefix = f"provider[{index}]"
        try:
            key = provider.resolve_api_key()
            key_ok = bool(key.strip()) and key.strip().lower() not in placeholders
        except ConfigError:
            key_ok = False
        add(f"{prefix}.credentials", "pass" if key_ok else "fail",
            "Credential is present locally; remote validity is untested." if key_ok else
            "API key is missing, a placeholder, or references an unset environment variable.")
        try:
            url = urlsplit(provider.base_url)
            url_ok = url.scheme in {"http", "https"} and bool(url.hostname)
            _ = url.port
        except ValueError:
            url_ok = False
        add(f"{prefix}.endpoint", "pass" if url_ok else "fail",
            "HTTP(S) endpoint syntax is valid; no request was sent." if url_ok else
            "base_url must be an HTTP(S) URL with a hostname and a valid port.")

    for index, server in enumerate(config.mcp_servers, start=1):
        if server.is_stdio:
            available = isinstance(server.command, str) and bool(shutil.which(server.command))
            add(f"mcp[{index}].command", "pass" if available else "fail",
                "MCP executable found; server was not started." if available else
                "Configured MCP executable was not found on PATH.")
        else:
            add(f"mcp[{index}].connection", "warn", "Remote MCP connection was not tested.")
    return result()


def format_report(report: dict) -> str:
    lines = [f"CodeTrail {report['version']} - local diagnostics"]
    lines.extend(f"[{item['status'].upper()}] {item['name']}: {item['detail']}" for item in report["checks"])
    lines.append("Ready for a live connection check." if report["ok"] else "Resolve the failed checks before starting.")
    return "\n".join(lines)
