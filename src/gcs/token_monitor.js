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
  const THRESHOLD = 0.2;
  const percentUsed = Math.round(ratio * 100);

  // Tmux status 寫入全域狀態檔案
  const globalStatusPath = path.join(process.env.HOME, '.gemini/gcs-guardian/tmux_status');
  try {
    fs.mkdirSync(path.dirname(globalStatusPath), { recursive: true });
    fs.writeFileSync(globalStatusPath, `[GCS: ${percentUsed}%]`);
  } catch(e) {}

  // State 管理
  const projectRoot = findProjectRoot(process.cwd());
  const STATE_DIR = projectRoot
    ? path.join(projectRoot, '.gemini')
    : path.join(process.env.HOME, '.gemini/gcs-guardian/tmp_state');
  if (!fs.existsSync(STATE_DIR)) fs.mkdirSync(STATE_DIR, { recursive: true });

  const STATE_FILE = path.join(STATE_DIR, 'monitor_state.json');
  let lastStep = 0;
  if (fs.existsSync(STATE_FILE)) {
    try { lastStep = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8')).last_notified_step || 0; } catch(e) {}
  }

  const currentStep = Math.floor(ratio / 0.05);

  // 📊 每 5% 階梯通知 — 顯示完整拆解方便對照 CLI 右下角數值
  if (currentStep > lastStep) {
    const percent = currentStep * 5;
    process.stderr.write(
      `\n📊 [GCS] Context: ${percent}% ` +
      `| prompt=${promptTokens.toLocaleString()} ` +
      `out=${outputTokens.toLocaleString()} ` +
      `think=${thinkingTokens.toLocaleString()} ` +
      `cached=${cachedTokens.toLocaleString()} ` +
      `| ${contextUsed.toLocaleString()}/${MAX_CONTEXT.toLocaleString()} ` +
      `| model=${modelName}\n`
    );
    fs.writeFileSync(STATE_FILE, JSON.stringify({
      last_ratio: ratio,
      last_notified_step: currentStep,
      prompt_tokens: promptTokens,
      output_tokens: outputTokens,
      thinking_tokens: thinkingTokens,
      cached_tokens: cachedTokens,
      total_tokens: totalTokens,
      max_context: MAX_CONTEXT,
      model: modelName,
      timestamp: new Date().toISOString()
    }));
  }

  // 🚨 20% YOLO 治理觸發
  if (ratio >= THRESHOLD) {
    process.stderr.write(`\n🚨 [GCS] ${Math.round(THRESHOLD*100)}% Threshold! prompt=${promptTokens.toLocaleString()} (YOLO ACTIVE)\n`);
    
    // Tmux 實時視效與狀態更新
    try {
      exec(`tmux display-message '🚨 [GCS] Background YOLO distillation triggered! (prompt: ${promptTokens.toLocaleString()})'`);
      fs.writeFileSync(globalStatusPath, `[GCS: ${percentUsed}% ⚡ YOLO]`);
    } catch(e) {}

    const homeDir = process.env.HOME;
    const pythonPath = path.join(homeDir, '.gemini/extensions/gcs-guardian/venv/bin/python3');
    const orchestratorPath = path.join(homeDir, '.gemini/extensions/gcs-guardian/scripts/gcs_orchestrator.py');
    exec(`"${pythonPath}" "${orchestratorPath}" --compress`, (error, stdout, stderr) => {
      if (error) {
        process.stderr.write(`[GCS YOLO ERROR] ${error.message}\n`);
        try { exec(`tmux display-message '❌ [GCS] YOLO Distillation failed!'`); } catch(e) {}
      }
      if (stdout) process.stderr.write(stdout);
    });
  }
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
