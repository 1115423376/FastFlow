#!/usr/bin/env python3
"""邀请码生成工具。

用法:
    python3 scripts/generate_invite_codes.py [--count N] [--output PATH]

示例:
    python3 scripts/generate_invite_codes.py --count 10
    python3 scripts/generate_invite_codes.py --count 5 --output nexus/config/invite_codes.json
"""

import argparse
import json
import os
import random
import string
import sys
import time

DEFAULT_COUNT = 10
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "config", "invite_codes.json")
CODE_LENGTH = 6
CODE_CHARS = string.ascii_uppercase + string.digits


def generate_codes(count: int) -> list[dict]:
    seen: set[str] = set()
    codes: list[dict] = []
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    while len(codes) < count:
        code = "".join(random.choices(CODE_CHARS, k=CODE_LENGTH))
        if code in seen:
            continue
        seen.add(code)
        codes.append({
            "code": code,
            "used": False,
            "used_by": None,
            "created_at": now,
            "used_at": None,
        })
    return codes


def load_existing(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_codes(path: str, codes: list[dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(codes, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="生成一次性邀请码")
    parser.add_argument("--count", "-c", type=int, default=DEFAULT_COUNT,
                        help=f"生成数量（默认: {DEFAULT_COUNT}）")
    parser.add_argument("--output", "-o", type=str, default=DEFAULT_OUTPUT,
                        help=f"输出文件路径（默认: {DEFAULT_OUTPUT}）")
    args = parser.parse_args()

    if args.count < 1:
        print("错误: --count 必须 >= 1", file=sys.stderr)
        sys.exit(1)

    existing = load_existing(args.output)
    new_codes = generate_codes(args.count)
    all_codes = existing + new_codes

    save_codes(args.output, all_codes)

    unused_count = sum(1 for c in all_codes if not c.get("used"))
    print(f"已生成 {len(new_codes)} 个新邀请码，追加到 {args.output}")
    print(f"当前共有 {len(all_codes)} 个邀请码（{unused_count} 个未使用）")
    print()
    for c in new_codes:
        print(f"  {c['code']}")


if __name__ == "__main__":
    main()
