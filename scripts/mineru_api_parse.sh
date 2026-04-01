#!/usr/bin/env bash

set -euo pipefail

SERVER_URL="http://127.0.0.1:8000"
INPUT=""
OUTPUT=""
BACKEND="hybrid-auto-engine"
PARSE_METHOD="auto"
FORMULA_ENABLE="true"
TABLE_ENABLE="true"
KEEP_ZIP="false"

usage() {
  cat <<'EOF'
用法:
  bash scripts/mineru_api_parse.sh \
    --input /abs/path/file.pdf \
    --output /abs/path/out_dir \
    [--server-url http://127.0.0.1:8000] \
    [--backend hybrid-auto-engine] \
    [--parse-method auto] \
    [--keep-zip]

说明:
  - 该脚本通过 MinerU FastAPI 的 /file_parse 接口解析单个 PDF
  - 最小解析结果固定包含: md + middle.json + images
  - 返回 ZIP 后解压到 --output 指定目录
  - 默认 server_url: http://127.0.0.1:8000
  - 默认 backend: hybrid-auto-engine
  - 默认 parse_method: auto
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-url)
      SERVER_URL="$2"
      shift 2
      ;;
    --input)
      INPUT="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --backend)
      BACKEND="$2"
      shift 2
      ;;
    --parse-method)
      PARSE_METHOD="$2"
      shift 2
      ;;
    --keep-zip)
      KEEP_ZIP="true"
      shift
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

if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
  echo "--input 和 --output 为必填参数" >&2
  usage >&2
  exit 1
fi

if [[ "$INPUT" != /* || "$OUTPUT" != /* ]]; then
  echo "当前脚本要求 --input 和 --output 使用绝对路径" >&2
  exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "输入文件不存在: $INPUT" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "未找到 curl" >&2
  exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "未找到 unzip" >&2
  exit 1
fi

HEALTH_URL="${SERVER_URL%/}/health"
PARSE_URL="${SERVER_URL%/}/file_parse"

mkdir -p "$OUTPUT"

if ! curl -fsS "$HEALTH_URL" >/dev/null; then
  echo "MinerU 服务不可用: $HEALTH_URL" >&2
  exit 1
fi

PDF_BASENAME="$(basename "$INPUT")"
ZIP_BASENAME="${PDF_BASENAME%.*}.zip"
ZIP_PATH="$OUTPUT/$ZIP_BASENAME"

echo "调用 MinerU API..."
echo "  SERVER_URL: $SERVER_URL"
echo "  INPUT: $INPUT"
echo "  OUTPUT: $OUTPUT"
echo "  BACKEND: $BACKEND"
echo "  PARSE_METHOD: $PARSE_METHOD"

curl -fsS -X POST "$PARSE_URL" \
  -F "files=@${INPUT}" \
  -F "backend=${BACKEND}" \
  -F "parse_method=${PARSE_METHOD}" \
  -F "formula_enable=${FORMULA_ENABLE}" \
  -F "table_enable=${TABLE_ENABLE}" \
  -F "return_md=true" \
  -F "return_middle_json=true" \
  -F "return_images=true" \
  -F "response_format_zip=true" \
  -o "$ZIP_PATH"

echo "解压返回结果..."
unzip -o "$ZIP_PATH" -d "$OUTPUT" >/dev/null

if [[ "$KEEP_ZIP" != "true" ]]; then
  rm -f "$ZIP_PATH"
fi

echo "解析完成。"
echo "  输出目录: $OUTPUT"
if [[ "$KEEP_ZIP" == "true" ]]; then
  echo "  ZIP 文件: $ZIP_PATH"
fi
