#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件编码守卫：检测、验证、还原文件的编码与换行符。

用法:
  python encoding_guard.py snapshot <文件或目录>   # 记录当前编码信息
  python encoding_guard.py verify  <文件或目录>    # 对比快照，报告变化
  python encoding_guard.py restore <文件或目录>    # 还原为快照中的编码
"""

import os
import sys
import json
import argparse

ENCODINGS = ["utf-8-sig", "utf-8", "gbk", "gb2312", "gb18030", "latin-1", "cp1252"]
SNAPSHOT_FILE = ".encoding-snapshot.json"
TEXT_EXTENSIONS = {
    ".cpp", ".h", ".hpp", ".c", ".cc", ".cxx", ".hxx", ".inl",
    ".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml",
    ".md", ".txt", ".cmake", ".cfg", ".ini", ".conf", ".sh", ".bat", ".cmd",
}
EXCLUDE_DIRS = {"debug", "build", "node_modules", ".git", ".svn", "cmake-build"}
EXCLUDE_DIR_PREFIXES = ("debug_", "build_", "CMakeFiles")


def should_skip_dir(dirname):
    low = dirname.lower()
    if low in EXCLUDE_DIRS:
        return True
    return any(low.startswith(p) for p in EXCLUDE_DIR_PREFIXES)


def detect_bom(raw_bytes):
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", 3
    if raw_bytes.startswith(b"\xff\xfe"):
        return "utf-16-le", 2
    if raw_bytes.startswith(b"\xfe\xff"):
        return "utf-16-be", 2
    return None, 0


def detect_encoding(filepath):
    """检测文件编码，返回 (encoding, has_bom)。"""
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
    except OSError:
        return None, False

    bom_enc, bom_len = detect_bom(raw)
    if bom_enc:
        return bom_enc, True

    for enc in ENCODINGS:
        if enc == "utf-8-sig":
            continue
        try:
            raw.decode(enc)
            return enc, False
        except (UnicodeDecodeError, LookupError):
            continue
    return None, False


def detect_eol(filepath):
    """检测换行符风格，返回 'crlf' / 'lf' / 'cr' / 'mixed'。"""
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
    except OSError:
        return None

    has_crlf = b"\r\n" in raw
    cleaned = raw.replace(b"\r\n", b"")
    has_cr = b"\r" in cleaned
    has_lf = b"\n" in cleaned

    if has_crlf and not has_cr and not has_lf:
        return "crlf"
    if has_lf and not has_crlf and not has_cr:
        return "lf"
    if has_cr and not has_crlf and not has_lf:
        return "cr"
    if has_crlf or has_cr or has_lf:
        return "mixed"
    return "none"


def collect_files(target):
    """收集目标路径下的文本文件列表。"""
    target = os.path.abspath(target)
    if os.path.isfile(target):
        return [target]

    files = []
    for dirpath, dirnames, filenames in os.walk(target, topdown=True):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext in TEXT_EXTENSIONS:
                files.append(os.path.join(dirpath, name))
    return files


def get_snapshot_path(target):
    target = os.path.abspath(target)
    if os.path.isfile(target):
        return os.path.join(os.path.dirname(target), SNAPSHOT_FILE)
    return os.path.join(target, SNAPSHOT_FILE)


def cmd_snapshot(target):
    files = collect_files(target)
    if not files:
        print("未找到文本文件。")
        return 0

    snapshot = {}
    for fp in files:
        enc, has_bom = detect_encoding(fp)
        eol = detect_eol(fp)
        if enc:
            key = os.path.relpath(fp, os.path.dirname(get_snapshot_path(target)))
            snapshot[key] = {
                "encoding": enc,
                "has_bom": has_bom,
                "eol": eol,
            }

    snap_path = get_snapshot_path(target)
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"已记录 {len(snapshot)} 个文件的编码信息 -> {snap_path}")
    return 0


def cmd_verify(target):
    snap_path = get_snapshot_path(target)
    if not os.path.isfile(snap_path):
        print(f"快照文件不存在: {snap_path}")
        print("请先运行 snapshot 命令。")
        return 1

    with open(snap_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    base_dir = os.path.dirname(snap_path)
    changed = []
    ok_count = 0

    for rel_path, info in snapshot.items():
        fp = os.path.join(base_dir, rel_path)
        if not os.path.isfile(fp):
            changed.append((rel_path, "文件已删除", ""))
            continue

        enc, has_bom = detect_encoding(fp)
        eol = detect_eol(fp)
        diffs = []
        if enc != info["encoding"]:
            diffs.append(f"编码: {info['encoding']} -> {enc}")
        if has_bom != info["has_bom"]:
            diffs.append(f"BOM: {info['has_bom']} -> {has_bom}")
        if eol != info["eol"]:
            diffs.append(f"换行: {info['eol']} -> {eol}")

        if diffs:
            changed.append((rel_path, "; ".join(diffs), ""))
        else:
            ok_count += 1

    if not changed:
        print(f"全部 {ok_count} 个文件编码未变。")
        return 0

    print(f"发现 {len(changed)} 个文件编码发生变化：")
    for rel_path, detail, _ in changed:
        print(f"  CHANGED: {rel_path}  ({detail})")
    print(f"未变: {ok_count}")
    return 1


def cmd_restore(target):
    snap_path = get_snapshot_path(target)
    if not os.path.isfile(snap_path):
        print(f"快照文件不存在: {snap_path}")
        print("请先运行 snapshot 命令。")
        return 1

    with open(snap_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    base_dir = os.path.dirname(snap_path)
    restored = 0
    skipped = 0

    for rel_path, info in snapshot.items():
        fp = os.path.join(base_dir, rel_path)
        if not os.path.isfile(fp):
            continue

        enc_now, bom_now = detect_encoding(fp)
        eol_now = detect_eol(fp)

        if enc_now == info["encoding"] and bom_now == info["has_bom"] and eol_now == info["eol"]:
            skipped += 1
            continue

        try:
            with open(fp, "rb") as f:
                raw = f.read()

            dec_enc = enc_now if enc_now else "utf-8"
            text = raw.decode(dec_enc if dec_enc != "utf-8-sig" else "utf-8-sig")
            if text.startswith("\ufeff"):
                text = text[1:]

            text = text.replace("\r\n", "\n").replace("\r", "\n")
            target_eol = info["eol"]
            if target_eol == "crlf":
                text = text.replace("\n", "\r\n")
            elif target_eol == "cr":
                text = text.replace("\n", "\r")

            target_enc = info["encoding"]
            if info["has_bom"] and target_enc == "utf-8-sig":
                encoded = text.encode("utf-8-sig")
            elif info["has_bom"] and target_enc.startswith("utf-16"):
                encoded = text.encode(target_enc)
            else:
                encoded = text.encode(target_enc if target_enc != "utf-8-sig" else "utf-8")

            with open(fp, "wb") as f:
                f.write(encoded)

            print(f"  RESTORED: {rel_path}")
            restored += 1

        except Exception as e:
            print(f"  FAIL: {rel_path} ({e})", file=sys.stderr)

    print(f"已还原: {restored}, 无需还原: {skipped}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="文件编码守卫")
    sub = parser.add_subparsers(dest="command")

    p_snap = sub.add_parser("snapshot", help="记录文件编码信息")
    p_snap.add_argument("target", help="文件或目录路径")

    p_verify = sub.add_parser("verify", help="对比快照，报告编码变化")
    p_verify.add_argument("target", help="文件或目录路径")

    p_restore = sub.add_parser("restore", help="还原为快照中的编码")
    p_restore.add_argument("target", help="文件或目录路径")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    handlers = {
        "snapshot": cmd_snapshot,
        "verify": cmd_verify,
        "restore": cmd_restore,
    }
    return handlers[args.command](args.target)


if __name__ == "__main__":
    sys.exit(main())
