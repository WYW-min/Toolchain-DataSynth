#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs/services"
PID_FILE="$LOG_DIR/mineru-api.pid"

usage() {
  cat <<'EOF'
用法:
  bash mineru_api_stop.sh

说明:
  - 该脚本应复制到 MinerU 仓库根目录下执行
  - 默认读取 ./logs/services/mineru-api.pid
EOF
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  "")
    ;;
  *)
    echo "未知参数: $1" >&2
    usage >&2
    exit 1
    ;;
esac

if [[ ! -f "$PID_FILE" ]]; then
  echo "未找到 PID 文件: $PID_FILE" >&2
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "$PID" ]]; then
  echo "PID 文件为空，直接清理。" >&2
  rm -f "$PID_FILE"
  exit 0
fi

if kill -0 "$PID" 2>/dev/null; then
  echo "停止 mineru-api, PID=$PID"
  kill "$PID"
  for _ in $(seq 1 10); do
    if ! kill -0 "$PID" 2>/dev/null; then
      break
    fi
    sleep 1
  done
  if kill -0 "$PID" 2>/dev/null; then
    echo "进程未在预期时间内退出，发送 SIGKILL。" >&2
    kill -9 "$PID"
  fi
else
  echo "mineru-api 进程不存在，清理过期 PID 文件。"
fi

rm -f "$PID_FILE"
echo "mineru-api 已停止。"

