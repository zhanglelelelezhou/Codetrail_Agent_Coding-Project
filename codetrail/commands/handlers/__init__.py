# 来源：公众号@小林coding

from __future__ import annotations

from codetrail.commands.handlers.clear import CLEAR_COMMAND
from codetrail.commands.handlers.compact import COMPACT_COMMAND
from codetrail.commands.handlers.help import HELP_COMMAND
from codetrail.commands.handlers.mcp import MCP_COMMAND
from codetrail.commands.handlers.memory import MEMORY_COMMAND
from codetrail.commands.handlers.permission import PERMISSION_COMMAND
from codetrail.commands.handlers.plan import PLAN_COMMAND
from codetrail.commands.handlers.sandbox import SANDBOX_COMMAND
from codetrail.commands.handlers.session import SESSION_COMMAND
from codetrail.commands.handlers.skill import SKILL_COMMAND
from codetrail.commands.handlers.rewind import REWIND_COMMAND
from codetrail.commands.handlers.status import STATUS_COMMAND
from codetrail.commands.registry import CommandRegistry


ALL_COMMANDS = [
    HELP_COMMAND,
    COMPACT_COMMAND,
    CLEAR_COMMAND,
    PLAN_COMMAND,
    SESSION_COMMAND,
    MCP_COMMAND,
    MEMORY_COMMAND,
    PERMISSION_COMMAND,
    SANDBOX_COMMAND,
    REWIND_COMMAND,
    STATUS_COMMAND,
    SKILL_COMMAND,
]


def register_all_commands(registry: CommandRegistry) -> None:
    for cmd in ALL_COMMANDS:
        registry.register_sync(cmd)

