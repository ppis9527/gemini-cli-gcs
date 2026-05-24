#!/bin/bash
PAYLOAD=$(cat)

# 把 payload 寫到 debug log 方便排查
echo "[$(date)] Received payload: $PAYLOAD" >> /tmp/statusline_debug.log

SETTINGS_FILE="$HOME/.gemini/jetski/cli/statusline_settings.json"
# 如果沒有設定檔，建立預設
if [ ! -f "$SETTINGS_FILE" ]; then
  mkdir -p "$(dirname "$SETTINGS_FILE")"
  cat << 'innerEOF' > "$SETTINGS_FILE"
{
  "statusline_order": [
    "state",
    "model",
    "cwd",
    "vcs",
    "context",
    "tasks",
    "artifacts",
    "cache",
    "version",
    "subagents",
    "sandbox",
    "plan_tier"
  ],
  "context": { "enabled": true, "color": "WHITE" },
  "cwd": { "enabled": true, "color": "WHITE" },
  "state": { "enabled": true, "color": "WHITE" },
  "model": { "enabled": true, "color": "WHITE" },
  "vcs": { "enabled": true, "color": "WHITE" },
  "tasks": { "enabled": true, "color": "WHITE" },
  "artifacts": { "enabled": true, "color": "WHITE" },
  "cache": { "enabled": true, "color": "WHITE" },
  "version": { "enabled": true, "color": "WHITE" },
  "subagents": { "enabled": true, "color": "WHITE" },
  "sandbox": { "enabled": true, "color": "WHITE" },
  "plan_tier": { "enabled": true, "color": "WHITE" }
}
innerEOF
fi

CWD=$(echo "$PAYLOAD" | jq -r '.cwd // ""')

# 判斷是否已優化 (gcs.pending)
IS_OPTIMIZED=false
if [ -f "$CWD/.gemini/gcs.pending" ]; then
  IS_OPTIMIZED=true
fi

# ANSI 色彩定義
COLOR_RESET="\033[0m"
COLOR_WHITE="\033[1;37m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_GRAY="\033[90m"
COLOR_RED="\033[31m"

# 1. 獲取 Git 分支
BRANCH=""
if [ -d "$CWD/.git" ] || (cd "$CWD" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
  BRANCH=$(cd "$CWD" && (git branch --show-current 2>/dev/null || git rev-parse --abbrev-ref HEAD 2>/dev/null))
fi

# 2. 準備各板塊的實時資料與著色

# State: ● READY
AGENT_STATE=$(echo "$PAYLOAD" | jq -r '.agent_state // ""')
if [ "$AGENT_STATE" = "working" ]; then
  STATE_VAL="${COLOR_WHITE}● WORKING${COLOR_RESET}"
else
  STATE_VAL="${COLOR_WHITE}● READY${COLOR_RESET}"
fi

# Model
MODEL_VAL=$(echo "$PAYLOAD" | jq -r '.model.display_name // .model.id // ""')

# CWD
CWD_VAL="$CWD"

# VCS
VCS_VAL="$BRANCH"

# Context 進度條與著色
PERCENT_RAW=$(echo "$PAYLOAD" | jq -r '.context_window.used_percentage // 0')
PERCENT_INT=$(printf "%.0f" "$PERCENT_RAW" 2>/dev/null || echo 0)
PERCENT_FMT=$(printf "%.1f" "$PERCENT_RAW" 2>/dev/null || echo "0.0")

# 產生 10 格進度條
FILLED=$(( (PERCENT_INT + 5) / 10 ))
if [ "$FILLED" -gt 10 ]; then FILLED=10; fi
EMPTY=$(( 10 - FILLED ))

BAR=""
for i in $(seq 1 $FILLED 2>/dev/null); do BAR="${BAR}▰"; done
for i in $(seq 1 $EMPTY 2>/dev/null); do BAR="${BAR}▱"; done

BAR_STR="${COLOR_GREEN}${BAR}${COLOR_RESET}"

FLASH_ICON=""
if [ "$IS_OPTIMIZED" = "true" ]; then
  FLASH_ICON=" ⚡"
fi

if [ "$PERCENT_INT" -ge 85 ]; then
  PCT_STR="${COLOR_RED}${PERCENT_FMT}%${FLASH_ICON}${COLOR_RESET}"
else
  PCT_STR="${COLOR_YELLOW}${PERCENT_FMT}%${FLASH_ICON}${COLOR_RESET}"
fi
CONTEXT_VAL="Context: ${BAR_STR} ${PCT_STR}"

# 實時同步更新 Tmux statusbar 狀態檔案
GLOBAL_STATUS_PATH="$HOME/.gemini/gcs-guardian/tmux_status"
if [ "$IS_OPTIMIZED" = "true" ]; then
  echo "[GCS: ${PERCENT_FMT}% ⚡]" > "$GLOBAL_STATUS_PATH"
else
  echo "[GCS: ${PERCENT_FMT}%]" > "$GLOBAL_STATUS_PATH"
fi

# Tasks
TASKS_COUNT=$(echo "$PAYLOAD" | jq -r '.task_count // 0')
TASKS_VAL="Tasks: ${TASKS_COUNT}"

# Artifacts
ARTS_COUNT=$(echo "$PAYLOAD" | jq -r '.artifact_count // 0')
ARTS_VAL="Artifacts: ${ARTS_COUNT}"

# Version (寫死為狀態列腳本的發布/更新日期)
VERSION_VAL="2026.05.24"
VER_VAL="Ver: ${VERSION_VAL}"

# Subagents
SUBAGENTS_VAL="Subagents: 0"

# Sandbox ON/OFF 灰色/綠色著色
SANDBOX_ENABLED=$(echo "$PAYLOAD" | jq -r '.sandbox.enabled // false')
if [ "$SANDBOX_ENABLED" = "true" ]; then
  SANDBOX_VAL="Sandbox: ${COLOR_GREEN}ON${COLOR_RESET}"
else
  SANDBOX_VAL="Sandbox: ${COLOR_GRAY}OFF${COLOR_RESET}"
fi

# Quota (plan_tier)
PLAN_TIER=$(echo "$PAYLOAD" | jq -r '.plan_tier // "free"')
PLAN_VAL="Quota: ${PLAN_TIER}"

# Cache 讀取量與命中率計算與著色
CACHE_READ=$(echo "$PAYLOAD" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
TOTAL_INPUT=$(echo "$PAYLOAD" | jq -r '.context_window.total_input_tokens // 0')

if [ "$TOTAL_INPUT" -gt 0 ] && [ "$CACHE_READ" -gt 0 ]; then
  CACHE_HIT_PCT=$(awk -v cr="$CACHE_READ" -v ti="$TOTAL_INPUT" 'BEGIN {printf "%.1f", (cr / ti) * 100}')
  CACHE_READ_FMT=$(printf "%'d" "$CACHE_READ")
  CACHE_VAL="⚡ Cache: ${CACHE_READ_FMT} (${CACHE_HIT_PCT}%)"
else
  CACHE_VAL="⚡ Cache: 0 (0.0%)"
fi

# 3. 用 jq 安全組合成 values JSON
VALUES_JSON=$(jq -n   --arg state "$STATE_VAL"   --arg model "$MODEL_VAL"   --arg cwd "$CWD_VAL"   --arg vcs "$VCS_VAL"   --arg context "$CONTEXT_VAL"   --arg tasks "$TASKS_VAL"   --arg artifacts "$ARTS_VAL"   --arg cache "$CACHE_VAL"   --arg version "$VER_VAL"   --arg subagents "$SUBAGENTS_VAL"   --arg sandbox "$SANDBOX_VAL"   --arg plan_tier "$PLAN_VAL"   '{state: $state, model: $model, cwd: $cwd, vcs: $vcs, context: $context, tasks: $tasks, artifacts: $artifacts, cache: $cache, version: $version, subagents: $subagents, sandbox: $sandbox, plan_tier: $plan_tier}')

# 4. 根據 settings 動態排序，並拆分到第一行與第二行
ROW1=$(jq -rn   --argjson settings "$(cat "$SETTINGS_FILE")"   --argjson values "$VALUES_JSON"   '
  $settings.statusline_order as $order |
  [
    $order[] as $k |
    select($k == "state" or $k == "model" or $k == "cwd" or $k == "vcs" or $k == "context") |
    select($settings[$k] == null or $settings[$k].enabled == true) |
    $values[$k] |
    select(. != null and . != "")
  ] | join(" | ")
  ')
ROW2=$(jq -rn   --argjson settings "$(cat "$SETTINGS_FILE")"   --argjson values "$VALUES_JSON"   '
  $settings.statusline_order as $order |
  [
    $order[] as $k |
    select($k == "tasks" or $k == "artifacts" or $k == "cache" or $k == "version" or $k == "subagents" or $k == "sandbox" or $k == "plan_tier") |
    select($settings[$k] == null or $settings[$k].enabled == true) |
    $values[$k] |
    select(. != null and . != "")
  ] | join(" | ")
  ')

# 5. 輸出雙行格式，加上邊框線條
echo -e "╭ $ROW1"
echo -e "╰ $ROW2"
