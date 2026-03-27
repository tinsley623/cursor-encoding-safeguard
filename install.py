#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 cursor-encoding-safeguard 安装到 Cursor 项目或全局配置目录。

用法:
  python install.py <项目路径>     # 安装到指定项目的 .cursor/ 下
  python install.py --global       # 安装 Rule 到全局 ~/.cursor/rules/，Skills 到 ~/.cursor/skills/
  python install.py --uninstall <项目路径>   # 从项目中移除
  python install.py --uninstall --global     # 从全局移除
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent

RULE_FILES = [
    ("rules/preserve-encoding.mdc", "rules/preserve-encoding.mdc"),
]

SKILL_DIRS = [
    "skills/batch-utf8-bom-crlf",
    "skills/preserve-file-encoding",
]


def get_global_cursor_dir():
    home = Path.home()
    return home / ".cursor"


def copy_file(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  {dst}")


def copy_dir(src_dir, dst_dir):
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)
    file_count = sum(1 for _ in dst_dir.rglob("*") if _.is_file())
    print(f"  {dst_dir}  ({file_count} files)")


def install_to_target(cursor_dir: Path):
    cursor_dir = Path(cursor_dir)
    print(f"Installing to: {cursor_dir}")
    print()

    print("Rules:")
    for src_rel, dst_rel in RULE_FILES:
        src = REPO_DIR / src_rel
        dst = cursor_dir / dst_rel
        copy_file(src, dst)

    print()
    print("Skills:")
    for skill_rel in SKILL_DIRS:
        src = REPO_DIR / skill_rel
        dst = cursor_dir / skill_rel
        copy_dir(src, dst)

    print()
    print("Done!")


def uninstall_from_target(cursor_dir: Path):
    cursor_dir = Path(cursor_dir)
    print(f"Uninstalling from: {cursor_dir}")
    print()

    removed = 0
    for _, dst_rel in RULE_FILES:
        dst = cursor_dir / dst_rel
        if dst.exists():
            dst.unlink()
            print(f"  Removed: {dst}")
            removed += 1

    for skill_rel in SKILL_DIRS:
        dst = cursor_dir / skill_rel
        if dst.exists():
            shutil.rmtree(dst)
            print(f"  Removed: {dst}")
            removed += 1

    if removed == 0:
        print("  Nothing to remove.")
    else:
        print(f"\nRemoved {removed} items.")


def main():
    parser = argparse.ArgumentParser(
        description="Install cursor-encoding-safeguard to a Cursor project or globally"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Path to the project root (installs to <project>/.cursor/)",
    )
    parser.add_argument(
        "--global", "-g",
        dest="global_install",
        action="store_true",
        help="Install globally to ~/.cursor/",
    )
    parser.add_argument(
        "--uninstall", "-u",
        action="store_true",
        help="Uninstall instead of install",
    )
    args = parser.parse_args()

    if not args.global_install and not args.project_path:
        parser.print_help()
        print("\nError: specify a project path or use --global")
        return 1

    if args.global_install:
        cursor_dir = get_global_cursor_dir()
    else:
        project = Path(args.project_path).resolve()
        if not project.is_dir():
            print(f"Error: directory not found: {project}", file=sys.stderr)
            return 1
        cursor_dir = project / ".cursor"

    if args.uninstall:
        uninstall_from_target(cursor_dir)
    else:
        install_to_target(cursor_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
