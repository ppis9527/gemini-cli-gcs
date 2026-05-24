#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

try {
  const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
  
  // Debug log to capture exactly what the CLI sends
  fs.writeFileSync('/tmp/gcs_debug_input.json', JSON.stringify(input, null, 2));

  // AfterModel: llm_response 包含 usageMetadata
  const resp = input.llm_response;
  if (!resp) { console.log(JSON.stringify({})); process.exit(0); }

  // 支援 Gemini (usageMetadata) 與 Claude/OpenAI (usage)
  const usage = resp.usageMetadata || resp.usage;
  if (!usage) { console.log(JSON.stringify({})); process.exit(0); }

  // 精確 token 拆解 (相容多模型欄位)
  const promptTokens   = usage.promptTokenCount       || usage.input_tokens   || 0;
  const outputTokens   = usage.candidatesTokenCount    || usage.output_tokens  || 0;
  const thinkingTokens = usage.thoughtsTokenCount      || 0;
  const cachedTokens   = usage.cachedContentTokenCount || usage.cache_creation_input_tokens || usage.cache_read_input_tokens || 0;
  const totalTokens    = usage.totalTokenCount         || (promptTokens + outputTokens) || 0;

  if (promptTokens === 0) { console.log(JSON.stringify({})); process.exit(0); }

  // 偵測模型 → context window 上限
  const modelName = (resp.model || input.llm_request?.model || 'flash').toLowerCase();
  let MAX_CONTEXT = 1048576; // Flash 1M
  if (modelName.includes('pro')) MAX_CONTEXT = 2097152; // Pro 2M

  // ✅ 用 promptTokenCount：這才是真正佔用 context window 的量
  const contextUsed = promptTokens;
  const ratio = contextUsed / MAX_CONTEXT;
  const THRESHOLD = 0.6; // 調整為 60% YOLO 觸發閾值
  const percentUsed = Math.round(ratio * 100);
  const percentUsedFmt = (ratio * 100).toFixed(1);

  // State 管理與專案路徑判斷
  const projectRoot = findProjectRoot(process.cwd());
  const hasPending = projectRoot && fs.existsSync(path.join(projectRoot, '.gemini/gcs.pending'));
  const suffix = hasPending ? ' ⚡' : '';

  // Tmux status 寫入全域狀態檔案
  const globalStatusPath = path.join(process.env.HOME, '.gemini/gcs-guardian/tmux_status');
  try {
    fs.mkdirSync(path.dirname(globalStatusPath), { recursive: true });
    fs.writeFileSync(globalStatusPath, `[GCS: ${percentUsedFmt}%${suffix}]`);
  } catch(e) {}

  const STATE_DIR = projectRoot
    ? path.join(projectRoot, '.gemini')
    : path.join(process.env.HOME, '.gemini/gcs-guardian/tmp_state');
  if (!fs.existsSync(STATE_DIR)) fs.mkdirSync(STATE_DIR, { recursive: true });

  const STATE_FILE = path.join(STATE_DIR, 'monitor_state.json');
  let lastCompressed20Step = 0;
  let lastCompressed60Step = 0;
  if (fs.existsSync(STATE_FILE)) {
    try {
      const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
      lastCompressed20Step = state.last_compressed_20_step || 0;
      lastCompressed60Step = state.last_compressed_60_step || 0;
    } catch(e) {}
  }

  const current20Step = Math.floor(ratio / 0.20);
  const current60Step = Math.floor(ratio / 0.60);

  const homeDir = process.env.HOME;
  const pythonPath = path.join(homeDir, '.gemini/extensions/gcs-guardian/venv/bin/python3');
  const orchestratorPath = path.join(homeDir, '.gemini/extensions/gcs-guardian/scripts/gcs_orchestrator.py');

  function writeState() {
    try {
      fs.writeFileSync(STATE_FILE, JSON.stringify({
        last_ratio: ratio,
        last_compressed_20_step: lastCompressed20Step,
        last_compressed_60_step: lastCompressed60Step,
        prompt_tokens: promptTokens,
        output_tokens: outputTokens,
        thinking_tokens: thinkingTokens,
        cached_tokens: cachedTokens,
        total_tokens: totalTokens,
        max_context: MAX_CONTEXT,
        model: modelName,
        timestamp: new Date().toISOString()
      }, null, 2));
    } catch(e) {}
  }

  // 1. 🚨 20% YOLO 觸發：僅 summarize 寫入 pending，不銷毀 Session
  if (ratio >= 0.2 && ratio < 0.6 && current20Step > lastCompressed20Step) {
    lastCompressed20Step = current20Step;
    writeState();

    try {
      exec(`tmux display-message '🚨 [GCS] 20% YOLO summarize triggered.'`);
      fs.writeFileSync(globalStatusPath, `[GCS: ${percentUsedFmt}% ⚡]`);
    } catch(e) {}

    exec(`"${pythonPath}" "${orchestratorPath}" --compress`, (error, stdout, stderr) => {
      if (error) {
        process.stderr.write(`[GCS 20% YOLO ERROR] ${error.message}\n`);
      }
      if (stdout) process.stderr.write(stdout);
    });
  }

  // 2. 🚨 60% YOLO 觸發：在系統 Compaction 前執行 summarize 並準備銷毀 Session
  if (ratio >= 0.6 && current60Step > lastCompressed60Step) {
    lastCompressed60Step = current60Step;
    writeState();

    try {
      exec(`tmux display-message '🚨 [GCS] 60% YOLO Pre-Compaction summarize triggered!'`);
      fs.writeFileSync(globalStatusPath, `[GCS: ${percentUsedFmt}% ⚡ YOLO]`);
    } catch(e) {}

    exec(`"${pythonPath}" "${orchestratorPath}" --compress`, (error, stdout, stderr) => {
      if (error) {
        process.stderr.write(`[GCS 60% YOLO ERROR] ${error.message}\n`);
        try { exec(`tmux display-message '❌ [GCS] 60% YOLO Distillation failed!'`); } catch(e) {}
      }
      if (stdout) process.stderr.write(stdout);
    });
  }

  // 預設無條件寫入，以維持 Single Source of Truth
  writeState();
} catch(e) {
  // AfterModel fires per chunk — some chunks won't have usageMetadata, silently skip
}

function findProjectRoot(current) {
  let depth = 0;
  while (current !== '/' && depth < 10) {
    if (fs.existsSync(path.join(current, '.git')) || fs.existsSync(path.join(current, 'GEMINI.md'))) return current;
    current = path.dirname(current);
    depth++;
  }
  return null;
}
console.log(JSON.stringify({}));
