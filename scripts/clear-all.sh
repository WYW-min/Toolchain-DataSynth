#!/usr/bin/env bash
# 一键清理 data/ 与 logs/ 下的所有内容（不删除目录本身）

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

clear_dir() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    # 删除目录下的所有文件和子目录，保留顶层目录
    find "$dir" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    echo "Cleared: $dir"
  else
    echo "Skip (not found): $dir"
  fi
}

clear_dir "$ROOT_DIR/data"
clear_dir "$ROOT_DIR/logs"

echo "Done."
