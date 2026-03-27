#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量将目录下文本文件转换为 UTF-8+BOM 编码与 CRLF 换行。
用法:
  python convert_to_utf8_bom_crlf.py <目录> [扩展名...]
  python convert_to_utf8_bom_crlf.py --file <文件路径>
"""

import os
import sys
import argparse

# 默认处理的扩展名（小写）
DEFAULT_EXTENSIONS = {".cpp", ".h", ".hpp", ".c", ".cc", ".cxx", ".hxx", ".inl", ".md", ".txt", ".cmake", ".py"}
# 排除的目录名（不进入）
EXCLUDE_DIRS = {"debug", "build", "node_modules", "cmake-build", ".git", ".svn"}
# 排除的目录前缀
EXCLUDE_DIR_PREFIXES = ("debug_", "build_", "CMakeFiles")

ENCODINGS = ["utf-8-sig", "utf-8", "gbk", "gb2312", "gb18030", "latin-1", "cp1252"]


def read_file(path):
    """尝试用多种编码读取文件，返回 (content, used_encoding) 或 (None, None)。"""
    for enc in ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return None, None


def write_utf8_bom_crlf(path, text):
    """以 UTF-8 BOM + CRLF 写回文件。"""
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)


def should_skip_dir(dirname):
    if dirname.lower() in EXCLUDE_DIRS:
        return True
    for prefix in EXCLUDE_DIR_PREFIXES:
        if dirname.lower().startswith(prefix):
            return True
    return False


def convert_dir(root_dir, extensions, dry_run=False):
    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        print("错误：目录不存在:", root_dir, file=sys.stderr)
        return 1
    converted = []
    failed = []
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if extensions and ext not in extensions:
                continue
            path = os.path.join(dirpath, name)
            content, enc = read_file(path)
            if content is None:
                failed.append(path)
                continue
            if dry_run:
                converted.append(path)
                continue
            try:
                write_utf8_bom_crlf(path, content)
                converted.append(path)
            except Exception as e:
                failed.append((path, str(e)))
    for p in converted:
        print("OK:", p)
    for item in failed:
        if isinstance(item, tuple):
            print("FAIL:", item[0], item[1], file=sys.stderr)
        else:
            print("SKIP (无法解码):", item, file=sys.stderr)
    print("已转换:", len(converted), "失败/跳过:", len(failed))
    return 0 if not failed else 1


def convert_file(file_path, dry_run=False):
    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        print("错误：文件不存在:", file_path, file=sys.stderr)
        return 1
    content, enc = read_file(file_path)
    if content is None:
        print("SKIP (无法解码):", file_path, file=sys.stderr)
        return 1
    if dry_run:
        print("DRY-RUN OK:", file_path)
        return 0
    try:
        write_utf8_bom_crlf(file_path, content)
        print("OK:", file_path)
        return 0
    except Exception as e:
        print("FAIL:", file_path, e, file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description="批量转换为 UTF-8+BOM 与 CRLF")
    parser.add_argument("path", nargs="?", default=None, help="要处理的目录；使用 -f 时为本文件路径")
    parser.add_argument("extensions", nargs="*", help="仅处理这些扩展名（如 .cpp .h）")
    parser.add_argument("--file", "-f", dest="single_file", action="store_true", help="将 path 视为单个文件")
    parser.add_argument("--dry-run", action="store_true", help="只列出将要转换的文件，不写入")
    args = parser.parse_args()

    target = args.path
    if target is None or target == "":
        parser.print_help()
        return 0

    if args.single_file:
        return convert_file(target, dry_run=args.dry_run)

    ext_set = None
    if args.extensions:
        ext_set = {e.lower() if e.startswith(".") else "." + e.lower() for e in args.extensions}
    else:
        ext_set = DEFAULT_EXTENSIONS

    return convert_dir(target, ext_set, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
