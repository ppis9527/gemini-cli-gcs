#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

/**
 * @file token_monitor.js
 * @description GCS Guardian: Precise API-level Token Monitoring (v2.0)
 * @triggered-by AfterModel Hook
 */

try {
  const input = JSON.parse(fs.readFileSync(0, 'utf-8'));

  // AfterModel: llm_response 包含 usageMetadata
  const resp = input.llm_response;
  if (!resp) { console.log(JSON.stringify({})); process.exit(0); }

  const usage = resp.usageMetadata;
  if (!usage) { console.log(JSON.stringify({})); process.exit(0); }

  // 精確 token 拆解
  const promptTokens   = usage.promptTokenCount       || 0;
  const outputTokens   = usage.candidatesTokenCount    || 0;
  const thinkingTokens = usage.thoughtsTokenCount      || 0;
  const cachedTokens   = usage.cachedContentTokenCount || 0;
  const totalTokens    = usage.totalTokenCount         || 0;

  if (promptTokens === 0) { console.log(JSON.stringify({})); process.exit(0); }

  // 偵測模型 → context window 上限
  const modelName = (resp.model || input.llm_request?.model || 'flash').toLowerCase();
  let MAX_CONTEXT = 1048576; // Flash 1M
  if (modelName.includes('pro')) MAX_CONTEXT = 2097152; // Pro 2M

  // ✅ 用 promptTokenCount：這才是真正佔用 context window 的量
  const contextUsed = promptTokens;
  const ratio = contextUsed / MAX_CONTEXT;
  const THRESHOLD = 0.2;

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
    
    // 定位 Orchestrator 路徑
    const ORCHESTRATOR_PATH = projectRoot 
      ? path.join(projectRoot, 'src/gcs/gcs_orchestrator.py')
      : "/Users/yj/.gemini/extensions/gcs-guardian/scripts/gcs_orchestrator.py";
    
    const VENV_PYTHON = projectRoot
      ? path.join(projectRoot, '.gemini/gcs-venv/bin/python3')
      : "/Users/yj/.gemini/extensions/gcs-guardian/venv/bin/python3";

    exec(`${VENV_PYTHON} ${ORCHESTRATOR_PATH} --background`, (error, stdout, stderr) => {
      if (error) process.stderr.write(`[GCS YOLO ERROR] ${error.message}\n`);
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
