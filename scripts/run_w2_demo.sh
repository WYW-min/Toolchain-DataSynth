#!/usr/bin/env bash
set -euo pipefail

CONFIG="configs/w2_demo.toml"
DO_PREFLIGHT=1
PREFLIGHT_ONLY=0

usage() {
  cat <<'EOF'
用法:
  bash scripts/run_w2_demo.sh [--config <path>] [--skip-preflight] [--preflight-only]

说明:
  - 默认配置: configs/w2_demo.toml
  - 默认先执行 preflight，再执行 local
  - --preflight-only 只做预检，不启动主流程
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="${2:?missing config path}"
      shift 2
      ;;
    --skip-preflight)
      DO_PREFLIGHT=0
      shift
      ;;
    --preflight-only)
      PREFLIGHT_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "$CONFIG" ]]; then
  echo "Config not found: $CONFIG" >&2
  exit 1
fi

echo "[W2] config: $CONFIG"

if [[ "$DO_PREFLIGHT" -eq 1 ]]; then
  echo "[W2] running preflight..."
  pixi run preflight --config "$CONFIG"
fi

if [[ "$PREFLIGHT_ONLY" -eq 1 ]]; then
  echo "[W2] preflight completed."
  exit 0
fi

before_latest=""
if [[ -L latest.log ]]; then
  before_latest="$(readlink latest.log || true)"
fi

echo "[W2] running pipeline..."
pixi run local --config "$CONFIG"

after_latest=""
if [[ -L latest.log ]]; then
  after_latest="$(readlink latest.log || true)"
fi

echo "[W2] completed."
if [[ -n "$after_latest" && "$after_latest" != "$before_latest" ]]; then
  run_id="$(basename "$after_latest" .log)"
  echo "[W2] run_id: $run_id"
  echo "[W2] report: data/out/$run_id/report.json"
  echo "[W2] dataset: data/out/$run_id/FinalQA.jsonl"
  echo "[W2] failed: data/out/$run_id/FailedCases.jsonl"
  echo "[W2] intermediate: data/temp/$run_id"
else
  echo "[W2] latest.log not updated. Check logs/ and data/out manually."
fi
