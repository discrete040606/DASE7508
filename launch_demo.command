#!/bin/zsh
set -e
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/streamlit ]]; then
  echo '请先按照 README.md 安装项目依赖。'
  exit 1
fi
export MPLCONFIGDIR="$PWD/.cache/matplotlib"
exec .venv/bin/streamlit run app/demo.py --server.address 127.0.0.1 --browser.gatherUsageStats false
