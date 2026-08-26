#!/usr/bin/env python3
"""Validate SKILL.md files and agent definitions against the Agent Skills format.

Usage:
    python3 scripts/validate_skills.py              # validate skills/ and agents/
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
AGENT_KNOWN_KEYS = {"name", "description", "tools", "model", "color", "metadata"}

TOOL_LIST_KEYS = ("allowed-tools", "disallowed-tools")
ARGUMENT_KEYS = ("argument-hint", "arguments")
ARG_PLACEHOLDER_RE = re.compile(r"(?<!\\)\$(ARGUMENTS|\d)")


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
        validate_json_manifests(report)
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
        validate_json_manifests(report)

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
