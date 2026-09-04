#!/usr/bin/env python3
"""Validate SKILL.md files, agent definitions, and plugin manifests.

Manifests checked: .claude-plugin/{plugin,marketplace}.json, hooks/hooks.json,
.mcp.json and monitors/monitors.json.

Usage:
    python3 scripts/validate_skills.py              # validate skills/, agents/ and manifests
    python3 scripts/validate_skills.py skills/foo   # validate one skill dir
    python3 scripts/validate_skills.py --strict     # treat warnings as errors

No third-party dependencies: the frontmatter parser handles the flat
scalar/list/nested-map subset of YAML that skill frontmatter uses.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_DIR = REPO_ROOT / "agents"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESC_MAX = 1024
BODY_SOFT_MAX_LINES = 500

# Fields the Agent Skills spec allows. These are the only ones that survive a
# claude.ai upload, the Skills API, or packaging with package_skill.py.
SPEC_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

# Fields Claude Code understands in addition to the spec. Using any of these
# makes the skill Claude Code / plugin only — see --spec-frontmatter.
CLAUDE_CODE_KEYS = {
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "background",
    "hooks",
    "paths",
    "shell",
}

KNOWN_KEYS = SPEC_KEYS | CLAUDE_CODE_KEYS
# Agent frontmatter. Only name and description are required; the rest are the
# documented optional fields, kept here so a legitimate one does not warn.
AGENT_KNOWN_KEYS = {
    "name", "description", "tools", "disallowedTools", "model", "color",
    "metadata", "permissionMode", "skills", "memory", "hooks", "isolation",
    "effort", "background", "maxTurns", "mcpServers", "initialPrompt",
    "experimental",
}

TOOL_LIST_KEYS = ("allowed-tools", "disallowed-tools")
ARGUMENT_KEYS = ("argument-hint", "arguments")
ARG_PLACEHOLDER_RE = re.compile(r"(?<!\\)\$(ARGUMENTS|\d)")

HOOKS_MANIFEST = REPO_ROOT / "hooks" / "hooks.json"
MCP_MANIFEST = REPO_ROOT / ".mcp.json"
MONITORS_MANIFEST = REPO_ROOT / "monitors" / "monitors.json"
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"

MONITOR_REQUIRED = ("name", "command", "description")
MONITOR_KNOWN_KEYS = {"name", "command", "description", "when"}

# An MCP server is either spawned (stdio) or dialled (http/sse/ws). One of the
# two shapes has to be recognizable or there is nothing to connect to.
MCP_STDIO_KEYS = {"type", "command", "args", "env", "cwd"}
MCP_REMOTE_KEYS = {"type", "url", "headers", "headersHelper"}
MCP_KNOWN_KEYS = MCP_STDIO_KEYS | MCP_REMOTE_KEYS

# plugin.json fields that can name a component path. A string or list of strings
# is a file reference; an object or list of objects is inline config.
PLUGIN_PATH_KEYS = (
    "skills", "commands", "agents", "workflows",
    "hooks", "mcpServers", "outputStyles", "lspServers",
)

# Within an agent's "## Routing" section, a backticked kebab-case token is read
# as a skill name.
ROUTING_SECTION_RE = re.compile(r"^##+[ \t]+Routing[ \t]*$(.*?)(?=^##[ \t]|\Z)", re.M | re.S)
BACKTICKED_RE = re.compile(r"`([a-z0-9][a-z0-9-]*)`")

SECRETISH_KEY_RE = re.compile(r"(?i)(key|token|secret|password|passwd|credential|auth)")

# Events Claude Code fires. Unknown names are warned about, not rejected:
# the list grows faster than this file does.
HOOK_EVENTS = {
    "SessionStart", "Setup", "UserPromptSubmit", "UserPromptExpansion",
    "PreToolUse", "PermissionRequest", "PermissionDenied", "PostToolUse",
    "PostToolUseFailure", "PostToolBatch", "Stop", "StopFailure",
    "Notification", "MessageDisplay", "SubagentStart", "SubagentStop",
    "TaskCreated", "TaskCompleted", "TeammateIdle", "InstructionsLoaded",
    "ConfigChange", "CwdChanged", "DirectoryAdded", "FileChanged",
    "PreCompact", "PostCompact", "WorktreeCreate", "WorktreeRemove",
    "Elicitation", "ElicitationResult", "SessionEnd",
}

# type -> fields that handler type cannot work without.
HOOK_TYPE_REQUIRED = {
    "command": ("command",),
    "http": ("url",),
    "mcp_tool": ("server", "tool"),
    "prompt": ("prompt",),
    "agent": ("prompt",),
}

HOOK_HANDLER_KEYS = {
    "type", "if", "timeout", "statusMessage", "once",
    "command", "args", "async", "asyncRewake", "shell",
    "url", "headers", "allowedEnvVars",
    "server", "tool", "input",
    "prompt", "model",
}

PLUGIN_ROOT_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}([^\s\"']*)")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def split_frontmatter(text: str) -> tuple[str, str] | None:
    """Return (frontmatter, body) or None if no well-formed block is present."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    return None


def _scalar(raw: str):
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p) for p in inner.split(",")]
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    return raw


def parse_frontmatter(fm: str) -> tuple[dict, list[str]]:
    """Parse the subset of YAML used in skill frontmatter."""
    data: dict = {}
    problems: list[str] = []
    current_key: str | None = None

    for lineno, line in enumerate(fm.splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Nested map entry or list item under the previous key.
        if indent > 0:
            if current_key is None:
                problems.append(f"line {lineno}: unexpected indentation")
                continue
            stripped = line.strip()
            if stripped.startswith("- "):
                data.setdefault(current_key, [])
                if isinstance(data[current_key], list):
                    data[current_key].append(_scalar(stripped[2:]))
                continue
            if ":" in stripped:
                k, _, v = stripped.partition(":")
                if not isinstance(data.get(current_key), dict):
                    data[current_key] = {}
                data[current_key][k.strip()] = _scalar(v)
                continue
            problems.append(f"line {lineno}: cannot parse {stripped!r}")
            continue

        # A block sequence may sit at the same indentation as its key --
        # "tools:\n- Read" is as valid as the indented form, and is what
        # yaml.safe_dump emits, so generated agent files arrive this way.
        if line.startswith("- "):
            if current_key is None:
                problems.append(f"line {lineno}: list item before any key")
                continue
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(_scalar(line[2:]))
            continue

        if ":" not in line:
            problems.append(f"line {lineno}: cannot parse {line.strip()!r}")
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        current_key = key
        data[key] = _scalar(value) if value else None

    return data, problems


def rel_path(path: Path) -> str:
    """Path relative to the repo root when possible, else absolute."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def validate_skill(skill_dir: Path, report: Report, spec_only: bool = False) -> None:
    rel = rel_path(skill_dir)
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        report.error(rel, "missing SKILL.md")
        return

    text = skill_md.read_text(encoding="utf-8")
    split = split_frontmatter(text)
    if split is None:
        report.error(rel, "SKILL.md has no YAML frontmatter delimited by '---'")
        return

    fm_text, body = split
    fm, problems = parse_frontmatter(fm_text)
    for p in problems:
        report.error(rel, f"frontmatter {p}")

    # name
    name = fm.get("name")
    if not name or not isinstance(name, str):
        report.error(rel, "frontmatter is missing required field 'name'")
    else:
        if not NAME_RE.match(name):
            report.error(rel, f"name {name!r} must be lowercase kebab-case")
        if len(name) > NAME_MAX:
            report.error(rel, f"name is {len(name)} chars (max {NAME_MAX})")
        if name != skill_dir.name:
            report.error(
                rel, f"name {name!r} does not match folder name {skill_dir.name!r}"
            )

    # description
    desc = fm.get("description")
    if not desc or not isinstance(desc, str):
        report.error(rel, "frontmatter is missing required field 'description'")
    else:
        if len(desc) > DESC_MAX:
            report.error(rel, f"description is {len(desc)} chars (max {DESC_MAX})")
        if len(desc) < 40:
            report.warn(rel, "description is very short; state what it does AND when to use it")
        if not desc.rstrip().endswith((".", "!", "?")):
            report.warn(rel, "description should be a complete sentence")

    # unknown keys
    for key in fm:
        if key not in KNOWN_KEYS:
            report.warn(rel, f"unrecognized frontmatter key {key!r}")

    # tool allow/deny lists: a space- or comma-separated string is also valid
    for key in TOOL_LIST_KEYS:
        value = fm.get(key)
        if value is not None and not isinstance(value, (str, list)):
            report.warn(rel, f"{key!r} should be a string or a list")

    # portability: flag Claude Code-only fields when the spec subset is required
    if spec_only:
        for key in sorted(set(fm) & CLAUDE_CODE_KEYS):
            report.warn(
                rel,
                f"{key!r} is not in the Agent Skills spec; a claude.ai upload or "
                "package_skill.py run will reject it",
            )

    # body
    if not body.strip():
        report.error(rel, "SKILL.md has no body content")
    body_lines = len(body.splitlines())
    if body_lines > BODY_SOFT_MAX_LINES:
        report.warn(
            rel,
            f"body is {body_lines} lines (>{BODY_SOFT_MAX_LINES}); "
            "move detail into sibling files",
        )

    # arguments declared but never used, or used but never declared
    declared = fm.get("arguments")
    if isinstance(declared, str):
        declared = declared.replace(",", " ").split()
    elif not isinstance(declared, list):
        declared = []
    declared = [str(d) for d in declared if d]

    uses_positional = bool(ARG_PLACEHOLDER_RE.search(body))
    uses_named = [d for d in declared if re.search(rf"(?<!\\)\${re.escape(d)}\b", body)]

    if any(k in fm for k in ARGUMENT_KEYS) and not (uses_positional or uses_named):
        report.warn(
            rel,
            "declares arguments in frontmatter but the body has no $ARGUMENTS, "
            "$N, or named placeholder to receive them",
        )
    for d in declared:
        if d not in uses_named:
            report.warn(rel, f"argument {d!r} is declared but never used as ${d} in the body")

    # relative links resolve
    for target in re.findall(r"\]\(([^)#][^)]*)\)", body):
        if re.match(r"^[a-z]+://|^mailto:|^#", target):
            continue
        if not (skill_dir / target.split("#")[0]).exists():
            report.warn(rel, f"linked file not found: {target}")


def validate_agent(agent_md: Path, report: Report) -> None:
    """Validate one agents/<name>.md definition."""
    rel = rel_path(agent_md)

    text = agent_md.read_text(encoding="utf-8")
    split = split_frontmatter(text)
    if split is None:
        report.error(rel, "agent file has no YAML frontmatter delimited by '---'")
        return

    fm_text, body = split
    fm, problems = parse_frontmatter(fm_text)
    for p in problems:
        report.error(rel, f"frontmatter {p}")

    name = fm.get("name")
    if not name or not isinstance(name, str):
        report.error(rel, "frontmatter is missing required field 'name'")
    else:
        if not NAME_RE.match(name):
            report.error(rel, f"name {name!r} must be lowercase kebab-case")
        if len(name) > NAME_MAX:
            report.error(rel, f"name is {len(name)} chars (max {NAME_MAX})")
        if name != agent_md.stem:
            report.error(
                rel, f"name {name!r} does not match file name {agent_md.stem!r}"
            )

    desc = fm.get("description")
    if not desc or not isinstance(desc, str):
        report.error(rel, "frontmatter is missing required field 'description'")
    elif len(desc) > DESC_MAX:
        report.error(rel, f"description is {len(desc)} chars (max {DESC_MAX})")
    elif len(desc) < 40:
        report.warn(rel, "description is very short; state what it does AND when to use it")

    for key in fm:
        if key not in AGENT_KNOWN_KEYS:
            report.warn(rel, f"unrecognized frontmatter key {key!r}")

    tools = fm.get("tools")
    if tools is not None and not isinstance(tools, (str, list)):
        report.warn(rel, "'tools' should be a comma-separated string or a list")

    if not body.strip():
        report.error(rel, "agent file has no body content")
    if len(body.splitlines()) > BODY_SOFT_MAX_LINES:
        report.warn(rel, f"body is long (>{BODY_SOFT_MAX_LINES} lines); push detail into skills")

    validate_agent_routing(rel, body, report)


def skill_names() -> set[str]:
    if not SKILLS_DIR.is_dir():
        return set()
    return {p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")}


def validate_agent_routing(rel: str, body: str, report: Report) -> None:
    """Every skill an agent routes to must exist -- a typo here dead-ends silently."""
    match = ROUTING_SECTION_RE.search(body)
    if match is None:
        return
    known = skill_names()
    if not known:
        return
    for name in dict.fromkeys(BACKTICKED_RE.findall(match.group(1))):
        if NAME_RE.match(name) and name not in known:
            report.error(rel, f"routing table names skill {name!r}, which is not in skills/")


def check_plugin_root_paths(value: object, where: str, rel: str, report: Report) -> None:
    """A ${CLAUDE_PLUGIN_ROOT}/... reference must point at a file this repo ships."""
    for match in PLUGIN_ROOT_RE.finditer(str(value).replace('"', "")):
        if not (REPO_ROOT / match.group(1).lstrip("/\\")).exists():
            report.error(rel, f"{where}: path not found: {match.group(0)}")


def looks_like_a_literal_secret(key: str, value: str) -> bool:
    """A credential-shaped key whose value is not an ${ENV_VAR} reference."""
    return bool(SECRETISH_KEY_RE.search(key)) and "${" not in value and len(value) > 8


def discover_agents() -> list[Path]:
    if not AGENTS_DIR.is_dir():
        return []
    return sorted(p for p in AGENTS_DIR.glob("*.md") if p.is_file())


def validate_json_manifests(report: Report) -> None:
    for path in (
        REPO_ROOT / ".claude-plugin" / "marketplace.json",
        REPO_ROOT / ".claude-plugin" / "plugin.json",
    ):
        if not path.is_file():
            continue
        rel = rel_path(path)
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.error(rel, f"invalid JSON: {exc}")


def validate_hooks_manifest(report: Report) -> None:
    """Check hooks/hooks.json: valid JSON, known events, usable handlers, real scripts."""
    if not HOOKS_MANIFEST.is_file():
        return
    rel = rel_path(HOOKS_MANIFEST)

    try:
        data = json.loads(HOOKS_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(rel, f"invalid JSON: {exc}")
        return

    events = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(events, dict):
        report.error(rel, "expected a top-level 'hooks' object mapping event names to lists")
        return

    for event, groups in events.items():
        if event not in HOOK_EVENTS:
            report.warn(rel, f"unrecognized hook event {event!r}")
        if not isinstance(groups, list):
            report.error(rel, f"{event}: expected a list of matcher groups")
            continue

        for i, group in enumerate(groups):
            where = f"{event}[{i}]"
            if not isinstance(group, dict):
                report.error(rel, f"{where}: expected an object")
                continue
            matcher = group.get("matcher")
            if matcher is not None and not isinstance(matcher, str):
                report.error(rel, f"{where}: 'matcher' must be a string")
            handlers = group.get("hooks")
            if not isinstance(handlers, list) or not handlers:
                report.error(rel, f"{where}: needs a non-empty 'hooks' list")
                continue

            for j, handler in enumerate(handlers):
                validate_hook_handler(handler, f"{where}.hooks[{j}]", rel, report)


def validate_hook_handler(handler: object, where: str, rel: str, report: Report) -> None:
    if not isinstance(handler, dict):
        report.error(rel, f"{where}: expected an object")
        return

    htype = handler.get("type")
    if htype not in HOOK_TYPE_REQUIRED:
        report.error(
            rel,
            f"{where}: 'type' must be one of {', '.join(sorted(HOOK_TYPE_REQUIRED))}",
        )
        return
    for field in HOOK_TYPE_REQUIRED[htype]:
        if not handler.get(field):
            report.error(rel, f"{where}: type {htype!r} requires {field!r}")

    for key in handler:
        if key not in HOOK_HANDLER_KEYS:
            report.warn(rel, f"{where}: unrecognized handler key {key!r}")

    timeout = handler.get("timeout")
    if timeout is not None and (not isinstance(timeout, (int, float)) or timeout <= 0):
        report.error(rel, f"{where}: 'timeout' must be a positive number of seconds")

    args = handler.get("args")
    if args is not None and not (isinstance(args, list) and all(isinstance(a, str) for a in args)):
        report.error(rel, f"{where}: 'args' must be a list of strings")

    if htype != "command":
        return

    # A bundled script is addressed through ${CLAUDE_PLUGIN_ROOT}; make sure it is there.
    command = handler.get("command", "")
    for part in [command] + list(args or []):
        for match in PLUGIN_ROOT_RE.finditer(str(part).replace('"', "")):
            target = REPO_ROOT / match.group(1).lstrip("/\\")
            if not target.exists():
                report.error(rel, f"{where}: script not found: {match.group(0)}")

    # Shell form word-splits on spaces, and plugin paths contain them.
    if isinstance(command, str) and args is None and "${CLAUDE_" in command:
        if '"${CLAUDE_' not in command and "'${CLAUDE_" not in command:
            report.warn(
                rel,
                f"{where}: unquoted path placeholder in shell form; use exec form "
                "('args': [...]) or quote it so a space in the path cannot split the command",
            )


def validate_mcp_manifest(report: Report) -> None:
    """Check .mcp.json: valid JSON, a usable shape per server, no committed secrets."""
    if not MCP_MANIFEST.is_file():
        return
    rel = rel_path(MCP_MANIFEST)

    try:
        data = json.loads(MCP_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(rel, f"invalid JSON: {exc}")
        return

    if not isinstance(data, dict):
        report.error(rel, "expected a top-level object")
        return
    servers = data.get("mcpServers")
    if servers is None:
        report.error(rel, "expected a top-level 'mcpServers' object")
        return
    if not isinstance(servers, dict):
        report.error(rel, "'mcpServers' must be an object mapping server names to configs")
        return

    for name, config in servers.items():
        where = f"mcpServers.{name}"
        if not isinstance(config, dict):
            report.error(rel, f"{where}: expected an object")
            continue

        has_command = bool(config.get("command"))
        has_url = bool(config.get("url"))
        if has_command and has_url:
            report.error(rel, f"{where}: has both 'command' and 'url'; a server is stdio or remote, not both")
        elif not has_command and not has_url:
            report.error(rel, f"{where}: needs 'command' (stdio) or 'url' (http/sse/ws)")

        args = config.get("args")
        if args is not None and not (isinstance(args, list) and all(isinstance(a, str) for a in args)):
            report.error(rel, f"{where}: 'args' must be a list of strings")

        for field in ("env", "headers"):
            value = config.get(field)
            if value is None:
                continue
            if not (isinstance(value, dict) and all(isinstance(v, str) for v in value.values())):
                report.error(rel, f"{where}: {field!r} must be an object of string values")
                continue
            for k, v in value.items():
                if looks_like_a_literal_secret(k, v):
                    report.warn(
                        rel,
                        f"{where}: {field}.{k} looks like a literal secret; this file is "
                        "committed -- use ${ENV_VAR} and keep the value out of the repo",
                    )

        for key in config:
            if key not in MCP_KNOWN_KEYS:
                report.warn(rel, f"{where}: unrecognized key {key!r}")

        for part in [config.get("command", "")] + list(args if isinstance(args, list) else []):
            check_plugin_root_paths(part, where, rel, report)


def validate_monitors_manifest(report: Report) -> None:
    """Check monitors/monitors.json: an array of usable monitor definitions."""
    if not MONITORS_MANIFEST.is_file():
        return
    rel = rel_path(MONITORS_MANIFEST)

    try:
        data = json.loads(MONITORS_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(rel, f"invalid JSON: {exc}")
        return

    if not isinstance(data, list):
        report.error(
            rel,
            "expected a top-level array of monitor objects "
            "(unlike hooks.json, which is an object keyed by event)",
        )
        return

    known_skills = skill_names()
    seen: set[str] = set()

    for i, entry in enumerate(data):
        where = f"[{i}]"
        if not isinstance(entry, dict):
            report.error(rel, f"{where}: expected an object")
            continue

        name = entry.get("name")
        if isinstance(name, str) and name.strip():
            where = f"[{i}] {name!r}"
            if name in seen:
                report.error(rel, f"{where}: duplicate monitor name")
            seen.add(name)

        for field in MONITOR_REQUIRED:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                report.error(rel, f"{where}: requires a non-empty string {field!r}")

        when = entry.get("when")
        if when is not None:
            if not isinstance(when, str):
                report.error(rel, f"{where}: 'when' must be a string")
            elif when != "always":
                if not when.startswith("on-skill-invoke:"):
                    report.error(
                        rel,
                        f'{where}: \'when\' must be "always" or "on-skill-invoke:<skill-name>", got {when!r}',
                    )
                else:
                    skill = when.split(":", 1)[1]
                    if not skill:
                        report.error(rel, f"{where}: 'when' has no skill name after 'on-skill-invoke:'")
                    elif known_skills and skill not in known_skills:
                        report.error(
                            rel, f"{where}: 'when' names skill {skill!r}, which is not in skills/"
                        )

        for key in entry:
            if key not in MONITOR_KNOWN_KEYS:
                report.warn(rel, f"{where}: unrecognized key {key!r}")

        check_plugin_root_paths(entry.get("command", ""), where, rel, report)


def validate_plugin_components(report: Report) -> None:
    """A plugin.json path override pointing nowhere drops a whole component silently."""
    if not PLUGIN_MANIFEST.is_file():
        return
    rel = rel_path(PLUGIN_MANIFEST)

    try:
        data = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return  # already reported by validate_json_manifests
    if not isinstance(data, dict):
        return

    overrides = [(key, data.get(key)) for key in PLUGIN_PATH_KEYS]
    experimental = data.get("experimental")
    if isinstance(experimental, dict):
        overrides.append(("experimental.monitors", experimental.get("monitors")))

    for key, value in overrides:
        if value is None:
            continue
        candidates = [value] if isinstance(value, str) else value if isinstance(value, list) else []
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue  # inline config, not a path
            if not (REPO_ROOT / candidate).exists():
                report.error(rel, f"{key}: path not found: {candidate}")


def validate_manifests(report: Report) -> None:
    """Everything in the repo that is a manifest rather than a skill or an agent."""
    validate_json_manifests(report)
    validate_plugin_components(report)
    validate_hooks_manifest(report)
    validate_mcp_manifest(report)
    validate_monitors_manifest(report)


def discover(targets: list[str]) -> list[Path]:
    if targets:
        return [Path(t).resolve() for t in targets]
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help="skill directories (default: all in skills/)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument(
        "--spec-frontmatter",
        action="store_true",
        help="warn on frontmatter fields outside the Agent Skills spec "
             "(use when the skill must also upload to claude.ai)",
    )
    args = parser.parse_args()

    report = Report()
    skill_dirs = discover(args.targets)
    agent_files = [] if args.targets else discover_agents()

    if not skill_dirs:
        print("No skills found in skills/ — nothing to validate.")
        validate_manifests(report)
    else:
        seen: dict[str, Path] = {}
        for skill_dir in skill_dirs:
            if not skill_dir.is_dir():
                report.error(str(skill_dir), "not a directory")
                continue
            if skill_dir.name in seen:
                report.error(skill_dir.name, "duplicate skill name")
            seen[skill_dir.name] = skill_dir
            validate_skill(skill_dir, report, spec_only=args.spec_frontmatter)
        validate_manifests(report)

    for agent_md in agent_files:
        validate_agent(agent_md, report)

    for w in report.warnings:
        print(f"WARN  {w}")
    for e in report.errors:
        print(f"ERROR {e}")

    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    print(
        f"\n{len(skill_dirs)} skill(s) and {len(agent_files)} agent(s) checked — "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
