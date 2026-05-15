#!/usr/bin/env python3
"""重新加载模型配置。

用法:
    python3 scripts/reload_models.py

当直接编辑 nexus/config/models.json 后，运行此脚本清空 LLM 运行时缓存，
下一次请求将自动读取最新的模型配置。无需重启 Nexus 服务。
"""

import os
import sys

_nexus_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _nexus_root not in sys.path:
    sys.path.insert(0, _nexus_root)

from nexus.core.cache import CacheManager


def main():
    CacheManager.clear_all_llm_runtimes()
    print("LLM 运行时缓存已清空。下次请求将加载最新模型配置。")


if __name__ == "__main__":
    main()
