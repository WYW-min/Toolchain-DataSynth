#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="127.0.0.1"
PORT="8000"
CUDA_DEVICES="0"
HEALTH_TIMEOUT_SECONDS="60"
LOG_DIR="$ROOT_DIR/logs/services"
PID_FILE="$LOG_DIR/mineru-api.pid"
LOG_FILE="$LOG_DIR/mineru-api.log"

usage() {
  cat <<'EOF'
用法:
  bash mineru_api_start.sh [--host 127.0.0.1] [--port 8000] [--cuda-devices 7] [--health-timeout 60]

说明:
  - 该脚本应复制到 MinerU 仓库根目录下执行
  - 默认日志路径: ./logs/services/mineru-api.log
  - 默认 PID 路径: ./logs/services/mineru-api.pid
  - 默认启动命令: uv run mineru-api --host <host> --port <port>
  - 默认 CUDA_VISIBLE_DEVICES=0
  - --cuda-devices 支持逗号分隔多个编号，例如 0,1
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --cuda-devices)
      CUDA_DEVICES="$2"
      shift 2
      ;;
    --health-timeout)
      HEALTH_TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$ROOT_DIR/pyproject.toml" ]]; then
  echo "当前目录不是 MinerU 仓库根目录: $ROOT_DIR" >&2
  exit 1
fi

mkdir -p "$LOG_DIR"

if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$EXISTING_PID" ]] && kill -0 "$EXISTING_PID" 2>/dev/null; then
    echo "mineru-api 已在运行，PID=$EXISTING_PID" >&2
    echo "日志文件: $LOG_FILE" >&2
    exit 0
  fi
  rm -f "$PID_FILE"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "未找到 uv，请先确保 MinerU 环境可用。" >&2
  exit 1
fi

echo "启动 mineru-api..."
echo "  ROOT_DIR: $ROOT_DIR"
echo "  HOST: $HOST"
echo "  PORT: $PORT"
echo "  CUDA_VISIBLE_DEVICES: $CUDA_DEVICES"
echo "  LOG_FILE: $LOG_FILE"

START_CMD=(uv run mineru-api --host "$HOST" --port "$PORT")

nohup env CUDA_VISIBLE_DEVICES="$CUDA_DEVICES" "${START_CMD[@]}" >>"$LOG_FILE" 2>&1 &

PID="$!"
echo "$PID" >"$PID_FILE"

HEALTH_URL="http://${HOST}:${PORT}/health"
DEADLINE=$((SECONDS + HEALTH_TIMEOUT_SECONDS))

until curl -fsS "$HEALTH_URL" >/dev/null 2>&1; do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "mineru-api 启动失败，进程已退出。" >&2
    echo "最近日志:" >&2
    tail -n 50 "$LOG_FILE" >&2 || true
    rm -f "$PID_FILE"
    exit 1
  fi
  if (( SECONDS >= DEADLINE )); then
    echo "等待健康检查超时: $HEALTH_URL" >&2
    echo "最近日志:" >&2
    tail -n 50 "$LOG_FILE" >&2 || true
    exit 1
  fi
  sleep 1
done

echo "mineru-api 已启动成功。"
echo "  PID: $PID"
echo "  HEALTH_URL: $HEALTH_URL"
echo "  LOG_FILE: $LOG_FILE"
