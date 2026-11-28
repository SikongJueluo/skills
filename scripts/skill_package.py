#!/usr/bin/env python3
"""Check Skill translation provenance and sync static assets without a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
SKILLS_ROOT = ROOT / "skills"
LOCK_PATH = ROOT / "compiler" / "lock.json"
SPEC_NAME = "SPEC.zh.md"
ALIASES = {"jj-desc"}


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def package_files(directory: Path) -> set[Path]:
    if directory.is_symlink():
        raise ValueError(f"Package directory is a symlink: {directory.relative_to(ROOT)}")
    files = set()
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        if relative.parts[0] == "evals":
            continue
        if path.is_symlink():
            raise ValueError(f"Package contains a symlink: {path.relative_to(ROOT)}")
        if path.is_file():
            files.add(relative)
    return files


def package_mapping(source: Path) -> tuple[dict[Path, Path], set[Path]]:
    files = package_files(source)
    if Path(SPEC_NAME) not in files:
        raise ValueError(f"{source.relative_to(ROOT)} is missing {SPEC_NAME}")

    translations: dict[Path, Path] = {}
    assets = set()
    for relative in sorted(files):
        if relative == Path(SPEC_NAME):
            output = Path("SKILL.md")
        elif relative.name.endswith(".zh.md"):
            output = relative.with_name(relative.name.removesuffix(".zh.md") + ".md")
        elif relative.name.endswith(".en.md"):
            raise ValueError(f"Keep English outputs under skills/, not src/: {source / relative}")
        else:
            assets.add(relative)
            continue
        if output in translations:
            raise ValueError(f"Multiple sources map to {source.name}/{output}")
        translations[output] = relative

    outputs = set(translations) | assets
    for output in sorted(outputs):
        if (output in translations and output in assets) or any(parent in outputs for parent in output.parents):
            raise ValueError(f"Source mapping collides at runtime path {source.name}/{output}")
    return translations, assets


def read_lock() -> dict:
    if not LOCK_PATH.exists():
        return {}
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if not isinstance(lock, dict) or lock.get("version") != 1 or not isinstance(lock.get("skills"), dict):
        raise ValueError("Unsupported compiler/lock.json format")
    return lock["skills"]


def sync(sources: list[Path]) -> None:
    for source in sources:
        _, assets = package_mapping(source)
        runtime = SKILLS_ROOT / source.name
        package_files(runtime)
        for relative in sorted(assets):
            target = runtime / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)
            shutil.copymode(source / relative, target)


def check_package(source: Path) -> tuple[dict, list[str]]:
    translations, assets = package_mapping(source)
    runtime = SKILLS_ROOT / source.name
    files = package_files(runtime)
    problems = []
    pairs = {}
    for output, original in translations.items():
        if output not in files:
            problems.append(f"Missing English output: {runtime.relative_to(ROOT) / output}")
            continue
        pairs[output.as_posix()] = {
            "source_sha256": sha256(source / original),
            "output_sha256": sha256(runtime / output),
        }
    for relative in sorted(assets):
        if relative not in files or sha256(source / relative) != sha256(runtime / relative):
            problems.append(f"Missing or stale runtime asset: {runtime.relative_to(ROOT) / relative}; run skill-sync")
    for relative in sorted(files - translations.keys() - assets):
        problems.append(f"Unpaired runtime file: {runtime.relative_to(ROOT) / relative}")
    return pairs, problems


def record(source: Path, generator: str) -> list[str]:
    if not generator.strip():
        return ["Generator provenance must not be empty"]
    pairs, problems = check_package(source)
    if problems:
        return problems
    lock = read_lock()
    lock[source.name] = {"generator": generator, "translations": pairs}
    content = json.dumps({"version": 1, "skills": lock}, indent=2, sort_keys=True, ensure_ascii=False)
    LOCK_PATH.write_text(content + "\n", encoding="utf-8")
    return []


def check(sources: list[Path]) -> list[str]:
    lock = read_lock()
    problems = []
    names = {source.name for source in sources}
    for runtime in sorted(SKILLS_ROOT.iterdir()):
        if runtime.is_dir() and runtime.name not in names:
            if runtime.name not in ALIASES:
                problems.append(f"Runtime package has no source: {runtime.relative_to(ROOT)}")
            elif package_files(runtime) != {Path("SKILL.md")}:
                problems.append(f"Expected only SKILL.md in alias package: {runtime.relative_to(ROOT)}")
    for name in sorted(lock.keys() - names):
        problems.append(f"Compiler lock contains {name!r} without a source package")
    for source in sources:
        pairs, package_problems = check_package(source)
        problems.extend(package_problems)
        entry = lock.get(source.name)
        if not isinstance(entry, dict) or not entry.get("generator") or not isinstance(entry.get("translations"), dict):
            problems.append(f"Missing or invalid provenance for {source.name}; run skill-record to record file provenance (not quality or performance validation)")
            continue
        recorded = entry["translations"]
        for output in sorted(pairs.keys() | recorded.keys()):
            if pairs.get(output) != recorded.get(output):
                problems.append(f"Missing or stale translation record: {source.name}/{output}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sync_parser = commands.add_parser("sync", help="copy only static assets from src/ into skills/")
    sync_parser.add_argument("--skill", help="sync one source package")
    record_parser = commands.add_parser("record", help="record existing source/output hashes and generator metadata")
    record_parser.add_argument("skill")
    record_parser.add_argument("--generator", required=True, help="model ID or preserved baseline provenance")
    commands.add_parser("check", help="check translation freshness and asset sync")
    args = parser.parse_args()

    try:
        for directory in (SOURCE_ROOT, SKILLS_ROOT):
            if directory.is_symlink():
                raise ValueError(f"Package root is a symlink: {directory.relative_to(ROOT)}")
        sources = {path.name: path for path in sorted(SOURCE_ROOT.iterdir()) if path.is_dir() or path.is_symlink()}
        skill = getattr(args, "skill", None)
        if skill is not None and skill not in sources:
            raise ValueError(f"No source package found for {skill!r}")
        if args.command == "sync":
            sync([sources[skill]] if skill else list(sources.values()))
            problems = []
        elif args.command == "record":
            problems = record(sources[skill], args.generator)
        else:
            problems = check(list(sources.values()))
    except (OSError, ValueError) as error:
        problems = [str(error)]
    if problems:
        print("\n".join(f"error: {problem}" for problem in problems), file=sys.stderr)
        return 1
    print(f"{args.command}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
