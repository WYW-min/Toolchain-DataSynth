#!/usr/bin/env bash
# 一键清理 logs/ 与 data/ 下除 data/in 之外的内容（不删除目录本身）

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

clear_data_dir() {
  local dir="$1"
  local keep_dir="$dir/in"
  if [[ -d "$dir" ]]; then
    find "$dir" -mindepth 1 -maxdepth 1 ! -path "$keep_dir" -exec rm -rf {} +
    echo "Cleared (kept data/in): $dir"
  else
    echo "Skip (not found): $dir"
  fi
}

clear_data_dir "$ROOT_DIR/data"
clear_dir "$ROOT_DIR/logs"

echo "Done."
