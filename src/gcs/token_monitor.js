#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

try {
  const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
  const resp = input.llm_response;
  if (!resp) { console.log(JSON.stringify({})); process.exit(0); }

  const usage = resp.usageMetadata || resp.usage;
  if (!usage) { console.log(JSON.stringify({})); process.exit(0); }

  const promptTokens   = usage.promptTokenCount       || usage.input_tokens   || 0;
  const outputTokens   = usage.candidatesTokenCount    || usage.output_tokens  || 0;
  const cachedTokens   = usage.cachedContentTokenCount || usage.cache_creation_input_tokens || usage.cache_read_input_tokens || 0;
  
  if (promptTokens === 0) { console.log(JSON.stringify({})); process.exit(0); }

  const modelName = (resp.model || input.llm_request?.model || 'flash').toLowerCase();
  let MAX_CONTEXT = 1048576;
  if (modelName.includes('pro')) MAX_CONTEXT = 2097152;

  const ratio = promptTokens / MAX_CONTEXT;
  const percentUsed = (ratio * 100).toFixed(1);

  const projectRoot = findProjectRoot(process.cwd());
  const globalStatusPath = path.join(process.env.HOME, '.gemini/gcs-guardian/tmux_status');
  const flashIcon = (projectRoot && fs.existsSync(path.join(projectRoot, '.gemini', 'gcs.pending'))) ? " ⚡" : "";

  try {
    fs.mkdirSync(path.dirname(globalStatusPath), { recursive: true });
    fs.writeFileSync(globalStatusPath, `GCS: ${percentUsed}%${flashIcon}`);
  } catch(e) {}

  const STATE_DIR = projectRoot ? path.join(projectRoot, '.gemini') : path.join(process.env.HOME, '.gemini/gcs-guardian/tmp_state');
  if (!fs.existsSync(STATE_DIR)) fs.mkdirSync(STATE_DIR, { recursive: true });

  const STATE_FILE = path.join(STATE_DIR, 'monitor_state.json');
  let lastStep = 0;
  if (fs.existsSync(STATE_FILE)) {
    try { lastStep = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8')).last_notified_step || 0; } catch(e) {}
  }
  const currentStep = Math.floor(ratio / 0.05);

  if (currentStep > lastStep) {
    process.stderr.write(`\n📊 [GCS] Context: ${currentStep * 5}% | prompt=${promptTokens.toLocaleString()} | model=${modelName}\n`);
    fs.writeFileSync(STATE_FILE, JSON.stringify({ last_notified_step: currentStep, prompt_tokens: promptTokens, max_context: MAX_CONTEXT, timestamp: new Date().toISOString() }));
  }

  if (ratio >= 0.2) {
    process.stderr.write(`\n🚨 [GCS] Threshold! (YOLO ACTIVE)\n`);
    try {
      exec(`tmux display-message '🚨 [GCS] Background YOLO distillation triggered!'`);
      fs.writeFileSync(globalStatusPath, `[GCS: ${percentUsed}% ⚡ YOLO]`);
    } catch(e) {}
    const pythonPath = path.join(process.env.HOME, '.gemini/extensions/gcs-guardian/venv/bin/python3');
    const orchestratorPath = path.join(process.env.HOME, '.gemini/extensions/gcs-guardian/scripts/gcs_orchestrator.py');
    exec(`"${pythonPath}" "${orchestratorPath}" --compress`, (error, stdout) => { if (stdout) process.stderr.write(stdout); });
  }
} catch(e) {}

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
