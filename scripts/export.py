#!/usr/bin/env python3
"""Install this repo's components into the harness of your choice.

The repo is the single source. Each target is a thin adapter that knows where
that harness keeps skills, agents, hooks and MCP servers -- nothing here is a
second copy of the content.

    python3 scripts/export.py --target claude-code-user
    python3 scripts/export.py --target claude-code-project --dest ~/work/api
    python3 scripts/export.py --target claude-ai
    python3 scripts/export.py --target generic
    python3 scripts/export.py --target plugin            # validate only
    python3 scripts/export.py --target claude-code-user --uninstall

Three properties worth relying on:

* **Symlinks by default.** An exported skill points back at this repo, so
  editing SKILL.md here changes the installed skill with no re-run. Pass
  ``--copy`` when a real copy is needed; Windows without Developer Mode falls
  back to copying on its own and says so.
* **Idempotent, with ``--dry-run``.** A second run reports "no change". A
  dry run writes nothing and lists what it would do.
* **An allowlist, not a denylist.** Only the component types in EXPORTABLE ever
  leave the repo. ``docs/`` holds personal working data and is not exportable
  by any target, which is deliberate: a copy under ~/.claude is in scope for
  every unrelated session on the machine.

Every install writes a receipt (``.ai-agency-export.json``) naming exactly what
it created, so ``--uninstall`` removes our files and our settings entries and
leaves everything else alone.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skills import SPEC_KEYS, split_frontmatter  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
RECEIPT_NAME = ".ai-agency-export.json"
RECEIPT_VERSION = 1
PLUGIN_ROOT_TOKEN = "${CLAUDE_PLUGIN_ROOT}"

# The allowlist. A component type absent from here cannot be exported by any
# target, whatever a caller asks for.
EXPORTABLE = ("skills", "agents", "hooks", "mcp", "monitors")

TARGETS = ("claude-code-user", "claude-code-project", "claude-ai", "plugin", "generic")


class Plan:
    """Collects what happened (or would happen) so one report covers every mode."""

    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.actions: list[str] = []
        self.skipped: list[str] = []
        self.notes: list[str] = []
        self.errors: list[str] = []

    def did(self, msg: str) -> None:
        self.actions.append(msg)

    def unchanged(self, msg: str) -> None:
        self.skipped.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def report(self) -> int:
        verb = "would " if self.dry_run else ""
        for msg in self.actions:
            print(f"  {verb}{msg}")
        for msg in self.skipped:
            print(f"  unchanged: {msg}")
        for msg in self.notes:
            print(f"  note: {msg}")
        for msg in self.errors:
            print(f"  ERROR: {msg}", file=sys.stderr)
        if not self.actions and not self.errors:
            print("  no change." if not self.dry_run else "  nothing to do.")
        return 1 if self.errors else 0


# --------------------------------------------------------------------------
# helpers


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def substitute_plugin_root(value):
    """${CLAUDE_PLUGIN_ROOT} only expands inside a plugin; everywhere else it is
    a literal that would break the command. Point it at this checkout."""
    if isinstance(value, str):
        return value.replace(PLUGIN_ROOT_TOKEN, REPO_ROOT.as_posix())
    if isinstance(value, list):
        return [substitute_plugin_root(v) for v in value]
    if isinstance(value, dict):
        return {k: substitute_plugin_root(v) for k, v in value.items()}
    return value


def read_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{rel(path)}: invalid JSON: {exc}")


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def link_or_copy(src: Path, dst: Path, plan: Plan, copy: bool) -> str | None:
    """Return the action taken, or None when the destination is already correct."""
    want_link = not copy

    if dst.is_symlink():
        try:
            if Path(os.readlink(dst)) == src and want_link:
                plan.unchanged(f"{dst}")
                return None
        except OSError:
            pass
    elif dst.exists() and copy:
        if _same_tree(src, dst):
            plan.unchanged(f"{dst}")
            return None

    if dst.is_symlink() or dst.exists():
        if plan.dry_run:
            plan.did(f"replace {dst}")
            return "replace"
        _remove(dst)

    if plan.dry_run:
        plan.did(f"{'link' if want_link else 'copy'} {dst} -> {rel(src)}")
        return "link" if want_link else "copy"

    dst.parent.mkdir(parents=True, exist_ok=True)
    if want_link:
        try:
            os.symlink(src, dst, target_is_directory=src.is_dir())
            plan.did(f"link {dst} -> {rel(src)}")
            return "link"
        except OSError as exc:
            # Windows without Developer Mode, or a filesystem that has no symlinks.
            plan.note(f"symlink unavailable ({exc.strerror or exc}); copying instead")
    _copy(src, dst)
    plan.did(f"copy {dst} <- {rel(src)}")
    return "copy"


def _copy(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _same_tree(src: Path, dst: Path) -> bool:
    if src.is_file() and dst.is_file():
        return src.read_bytes() == dst.read_bytes()
    if src.is_dir() and dst.is_dir():
        s = {p.relative_to(src) for p in src.rglob("*") if p.is_file()}
        d = {p.relative_to(dst) for p in dst.rglob("*") if p.is_file()}
        return s == d and all((src / p).read_bytes() == (dst / p).read_bytes() for p in s)
    return False


def repo_skills() -> list[Path]:
    d = REPO_ROOT / "skills"
    return sorted(p for p in d.iterdir() if p.is_dir() and not p.name.startswith(".")) if d.is_dir() else []


def repo_agents() -> list[Path]:
    d = REPO_ROOT / "agents"
    return sorted(d.glob("*.md")) if d.is_dir() else []


def repo_hook_groups() -> dict:
    data = read_json(REPO_ROOT / "hooks" / "hooks.json") or {}
    return substitute_plugin_root(data.get("hooks") or {})


def repo_mcp_servers() -> dict:
    data = read_json(REPO_ROOT / ".mcp.json") or {}
    return substitute_plugin_root(data.get("mcpServers") or {})


def repo_monitors() -> list:
    return read_json(REPO_ROOT / "monitors" / "monitors.json") or []


# --------------------------------------------------------------------------
# receipts


def load_receipt(path: Path) -> dict:
    data = read_json(path)
    return data if isinstance(data, dict) else {}


def write_receipt(path: Path, payload: dict, plan: Plan) -> None:
    """Rewrite only on a real change, so an unchanged re-run reports no change."""
    text = json.dumps(payload, indent=2) + "\n"
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        plan.unchanged(f"{path}")
        return
    if plan.dry_run:
        plan.did(f"write receipt {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    plan.did(f"write receipt {path}")


# --------------------------------------------------------------------------
# settings.json merging


def merge_hooks(settings_file: Path, groups: dict, plan: Plan) -> list[dict]:
    """Add our hook groups to a settings file, leaving anything already there alone.

    Returns the groups actually installed, recorded in the receipt so uninstall
    can remove precisely those and nothing else.
    """
    settings = read_json(settings_file) or {}
    if not isinstance(settings, dict):
        plan.error(f"{settings_file} is not a JSON object; refusing to touch it")
        return []

    existing = settings.get("hooks")
    if existing is not None and not isinstance(existing, dict):
        plan.error(f"{settings_file}: 'hooks' is not an object; refusing to touch it")
        return []
    existing = dict(existing or {})

    installed: list[dict] = []
    changed = False
    for event, our_groups in groups.items():
        theirs = list(existing.get(event) or [])
        seen = {canonical(g) for g in theirs}
        for group in our_groups:
            # Recorded either way: the receipt describes what is installed, not
            # what this particular run happened to add.
            installed.append({"event": event, "group": group})
            if canonical(group) in seen:
                plan.unchanged(f"{settings_file} hooks.{event} entry")
                continue
            theirs.append(group)
            plan.did(f"add hooks.{event} entry to {settings_file}")
            changed = True
        existing[event] = theirs

    if changed and not plan.dry_run:
        settings["hooks"] = existing
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return installed


def unmerge_hooks(settings_file: Path, installed: list[dict], plan: Plan) -> None:
    settings = read_json(settings_file)
    if not isinstance(settings, dict) or not isinstance(settings.get("hooks"), dict):
        return
    hooks = settings["hooks"]
    changed = False
    for entry in installed:
        event, target = entry.get("event"), canonical(entry.get("group"))
        groups = hooks.get(event)
        if not isinstance(groups, list):
            continue
        kept = [g for g in groups if canonical(g) != target]
        if len(kept) != len(groups):
            changed = True
            plan.did(f"remove hooks.{event} entry from {settings_file}")
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if not changed:
        return
    if not hooks:
        settings.pop("hooks", None)
    if plan.dry_run:
        return
    settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# targets


def layout(target: str, dest: Path) -> dict:
    if target == "claude-code-user":
        return {
            "skills": dest / "skills",
            "agents": dest / "agents",
            "settings": dest / "settings.json",
            "mcp": None,
            "receipt": dest / RECEIPT_NAME,
        }
    return {
        "skills": dest / ".claude" / "skills",
        "agents": dest / ".claude" / "agents",
        "settings": dest / ".claude" / "settings.json",
        "mcp": dest / ".mcp.json",
        "receipt": dest / ".claude" / RECEIPT_NAME,
    }


def export_claude_code(target: str, dest: Path, plan: Plan, copy: bool) -> None:
    paths = layout(target, dest)
    written: list[str] = []

    for skill in repo_skills():
        dst = paths["skills"] / skill.name
        link_or_copy(skill, dst, plan, copy)
        written.append(str(dst))
    for agent in repo_agents():
        dst = paths["agents"] / agent.name
        link_or_copy(agent, dst, plan, copy)
        written.append(str(dst))

    hooks = merge_hooks(paths["settings"], repo_hook_groups(), plan) if repo_hook_groups() else []

    servers = repo_mcp_servers()
    if servers and paths["mcp"] is not None:
        existing = read_json(paths["mcp"]) or {}
        merged = dict(existing.get("mcpServers") or {})
        added = [n for n, c in servers.items() if merged.get(n) != c]
        merged.update(servers)
        if added:
            plan.did(f"add {len(added)} MCP server(s) to {paths['mcp']}: {', '.join(added)}")
            if not plan.dry_run:
                paths["mcp"].write_text(
                    json.dumps({**existing, "mcpServers": merged}, indent=2) + "\n",
                    encoding="utf-8",
                )
        else:
            plan.unchanged(f"{paths['mcp']}")
        written_mcp = sorted(servers)
    elif servers:
        # User scope keeps MCP in ~/.claude.json, which Claude Code writes for
        # itself. Hand over the commands rather than editing it underneath.
        plan.note("MCP servers are not installed at user scope; run these instead:")
        for name, config in servers.items():
            plan.note(f"    claude mcp add-json {name} '{canonical(config)}' -s user")
        written_mcp = []
    else:
        written_mcp = []

    if repo_monitors():
        plan.note(
            "monitors are a plugin-only component -- there is no user or project "
            "location for them. Use --target plugin (install this repo as a plugin) "
            "if you want the monitors."
        )

    write_receipt(
        paths["receipt"],
        {
            "version": RECEIPT_VERSION,
            "target": target,
            "repo": REPO_ROOT.as_posix(),
            "mode": "copy" if copy else "link",
            "written": written,
            "hooks": hooks,
            "settings_file": str(paths["settings"]),
            "mcp_file": str(paths["mcp"]) if paths["mcp"] else None,
            "mcp_servers": written_mcp,
        },
        plan,
    )


def strip_to_spec_frontmatter(text: str) -> tuple[str, list[str]]:
    """Drop frontmatter keys the Agent Skills spec does not allow.

    Works on the raw lines rather than a parse-and-reserialize, so everything
    that stays keeps its exact formatting.
    """
    split = split_frontmatter(text)
    if split is None:
        return text, []
    fm, body = split

    kept: list[str] = []
    dropped: list[str] = []
    skipping = False
    for line in fm.splitlines():
        if line[:1] in (" ", "\t") or not line.strip():
            if not skipping:
                kept.append(line)
            continue
        key = line.split(":", 1)[0].strip()
        if key and key not in SPEC_KEYS:
            skipping = True
            dropped.append(key)
            continue
        skipping = False
        kept.append(line)

    if not dropped:
        return text, []  # nothing to remove: hand back the file untouched
    return "---\n" + "\n".join(kept).strip("\n") + "\n---\n" + body, dropped


def export_claude_ai(dest: Path, plan: Plan) -> None:
    """One archive per skill, frontmatter reduced to what an upload accepts."""
    for skill in repo_skills():
        skill_md = skill / "SKILL.md"
        if not skill_md.is_file():
            continue
        rewritten, dropped = strip_to_spec_frontmatter(skill_md.read_text(encoding="utf-8"))
        archive = dest / f"{skill.name}.zip"

        if dropped:
            plan.note(f"{skill.name}: dropped {', '.join(sorted(set(dropped)))}")
        if plan.dry_run:
            plan.did(f"build {archive}")
            continue

        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{skill.name}/SKILL.md", rewritten)
            for extra in sorted(skill.rglob("*")):
                if extra.is_file() and extra != skill_md:
                    zf.write(extra, f"{skill.name}/{extra.relative_to(skill).as_posix()}")
        plan.did(f"build {archive}")

    plan.note("these are archives only; upload them yourself -- nothing is sent anywhere")


def export_generic(dest: Path, plan: Plan) -> None:
    """A flat bundle plus a manifest, for a harness with no adapter yet."""
    manifest = {
        "source": REPO_ROOT.as_posix(),
        "components": {
            "skills": [p.name for p in repo_skills()],
            "agents": [p.stem for p in repo_agents()],
            "hooks": sorted(repo_hook_groups().keys()),
            "mcpServers": sorted(repo_mcp_servers().keys()),
            "monitors": [m.get("name") for m in repo_monitors() if isinstance(m, dict)],
        },
    }

    for name in ("skills", "agents", "hooks", "monitors"):
        src = REPO_ROOT / name
        if src.is_dir():
            if plan.dry_run:
                plan.did(f"copy {dest / name}")
            else:
                dst = dest / name
                if dst.exists():
                    shutil.rmtree(dst)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst)
                plan.did(f"copy {dst}")
    mcp = REPO_ROOT / ".mcp.json"
    if mcp.is_file():
        if plan.dry_run:
            plan.did(f"copy {dest / 'mcp.json'}")
        else:
            shutil.copy2(mcp, dest / "mcp.json")
            plan.did(f"copy {dest / 'mcp.json'}")

    if plan.dry_run:
        plan.did(f"write {dest / 'manifest.json'}")
    else:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        plan.did(f"write {dest / 'manifest.json'}")


def export_plugin(plan: Plan) -> None:
    plan.note("the plugin marketplace installs from git; there is nothing to copy.")
    plan.note("    /plugin marketplace add shulginilya/ai_agency_skills")
    plan.note("    /plugin install ai-agency-skills@ai-agency-skills")


# --------------------------------------------------------------------------
# uninstall


def uninstall(target: str, dest: Path, plan: Plan) -> None:
    paths = layout(target, dest)
    receipt = load_receipt(paths["receipt"])
    if not receipt:
        plan.error(f"no receipt at {paths['receipt']}; nothing to uninstall")
        return

    for entry in receipt.get("written") or []:
        path = Path(entry)
        if path.is_symlink() or path.exists():
            plan.did(f"remove {path}")
            if not plan.dry_run:
                _remove(path)
        else:
            plan.unchanged(f"{path} (already gone)")

    settings_file = receipt.get("settings_file")
    if settings_file and receipt.get("hooks"):
        unmerge_hooks(Path(settings_file), receipt["hooks"], plan)

    mcp_file, servers = receipt.get("mcp_file"), receipt.get("mcp_servers") or []
    if mcp_file and servers:
        data = read_json(Path(mcp_file))
        if isinstance(data, dict) and isinstance(data.get("mcpServers"), dict):
            for name in servers:
                if data["mcpServers"].pop(name, None) is not None:
                    plan.did(f"remove MCP server {name} from {mcp_file}")
            if not plan.dry_run:
                Path(mcp_file).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    plan.did(f"remove receipt {paths['receipt']}")
    if not plan.dry_run:
        paths["receipt"].unlink(missing_ok=True)


# --------------------------------------------------------------------------


def default_dest(target: str) -> Path | None:
    if target == "claude-code-user":
        return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    if target == "claude-ai":
        return REPO_ROOT / "dist" / "claude-ai"
    if target == "generic":
        return REPO_ROOT / "dist" / "generic"
    return None


def run_validator() -> int:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_skills.py")],
        cwd=REPO_ROOT,
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--target", required=True, choices=TARGETS)
    parser.add_argument("--dest", type=Path, help="destination (required for claude-code-project)")
    parser.add_argument("--copy", action="store_true", help="copy instead of symlinking")
    parser.add_argument("--dry-run", action="store_true", help="write nothing; list what would happen")
    parser.add_argument("--uninstall", action="store_true", help="reverse a previous install using its receipt")
    parser.add_argument("--skip-validate", action="store_true", help="export even if the repo does not validate")
    args = parser.parse_args()

    dest = args.dest or default_dest(args.target)
    if args.target == "claude-code-project" and dest is None:
        parser.error("--target claude-code-project needs --dest <project directory>")
    if dest is not None:
        dest = dest.expanduser().resolve()

    plan = Plan(args.dry_run)

    if args.uninstall:
        if args.target not in ("claude-code-user", "claude-code-project"):
            parser.error(f"--uninstall does not apply to --target {args.target}")
        print(f"uninstall {args.target} from {dest}")
        uninstall(args.target, dest, plan)
        return plan.report()

    if not args.skip_validate and args.target != "plugin":
        if run_validator() != 0:
            print("\nrefusing to export a repo that does not validate "
                  "(--skip-validate to override)", file=sys.stderr)
            return 1

    print(f"export {args.target}" + (f" to {dest}" if dest else ""))
    if args.target in ("claude-code-user", "claude-code-project"):
        export_claude_code(args.target, dest, plan, args.copy)
    elif args.target == "claude-ai":
        export_claude_ai(dest, plan)
    elif args.target == "generic":
        export_generic(dest, plan)
    else:
        export_plugin(plan)

    return plan.report()


if __name__ == "__main__":
    sys.exit(main())
