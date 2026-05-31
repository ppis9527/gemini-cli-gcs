#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { exec, execSync } = require('child_process');

function resolveMaxContext(modelName) {
  const model = (modelName || '').toLowerCase();
  const MODEL_CONTEXT_MAP = {
    'gemini-2.5-pro': 2097152,
    'gemini-2.5-flash': 1048576,
  };
  return MODEL_CONTEXT_MAP[model] || 1048576;
}

function getCompactBucketsToTrigger(lastCompactBucket, percent, buckets = [20, 30, 40, 50]) {
  return buckets.filter((b) => b > lastCompactBucket && b <= percent);
}

function main() {
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

  const modelName = (resp.model || input.llm_request?.model || 'gemini-2.5-flash').toLowerCase();
  const MAX_CONTEXT = resolveMaxContext(modelName);

  const ratio = promptTokens / MAX_CONTEXT;
  const percentUsed = (ratio * 100).toFixed(1);

  const projectRoot = findProjectRoot(process.cwd()) || (fs.existsSync(path.join(process.cwd(), 'src', 'gcs', 'gcs_orchestrator.py')) ? process.cwd() : null);
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
  let lastCompactBucket = 0;
  if (fs.existsSync(STATE_FILE)) {
    try {
      const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
      lastStep = state.last_notified_step || 0;
      lastCompactBucket = state.last_compact_bucket || 0;
    } catch(e) {}
  }
  const currentStep = Math.floor(ratio / 0.05);
  const currentPercent = ratio * 100;

  if (currentStep > lastStep) {
    process.stderr.write(`\n📊 [GCS] Context: ${currentStep * 5}% | prompt=${promptTokens.toLocaleString()} | model=${modelName}\n`);
  }

  const pendingCompactBuckets = getCompactBucketsToTrigger(lastCompactBucket, currentPercent);
  for (const bucket of pendingCompactBuckets) {
    process.stderr.write(`\n🚨 [GCS] ${bucket}% threshold reached. Background compact triggered.\n`);
    try {
      exec(`tmux display-message '🚨 [GCS] Background YOLO distillation triggered!'`);
      fs.writeFileSync(globalStatusPath, `[GCS: ${percentUsed}% ⚡ YOLO]`);
    } catch(e) {}
    const localPython = path.join(projectRoot || "", '.gemini', 'gcs-venv', 'bin', 'python3');
    const extensionPython = path.join(process.env.HOME, '.gemini/extensions/gcs-guardian/venv/bin/python3');
    const pythonPath = fs.existsSync(localPython) ? localPython : (fs.existsSync(extensionPython) ? extensionPython : 'python3');

    const localOrchestrator = projectRoot ? path.join(projectRoot, 'src', 'gcs', 'gcs_orchestrator.py') : '';
    const extensionOrchestrator = path.join(process.env.HOME, '.gemini/extensions/gcs-guardian/scripts/gcs_orchestrator.py');
    const orchestratorPath = fs.existsSync(localOrchestrator) ? localOrchestrator : extensionOrchestrator;
    const preflightPath = projectRoot ? path.join(projectRoot, 'src', 'gcs', 'gcs_preflight.py') : '';

    if (fs.existsSync(orchestratorPath)) {
      let preflightOk = true;
      if (fs.existsSync(preflightPath)) {
        try {
          execSync(`"${pythonPath}" "${preflightPath}"`, { stdio: 'ignore' });
        } catch (e) {
          try {
            execSync(`python3 "${preflightPath}"`, { stdio: 'ignore' });
          } catch (fallbackErr) {
            preflightOk = false;
            process.stderr.write(`\n[WARN] GCS preflight failed. Install deps: pip install -r requirements.txt\n`);
          }
        }
      }

      if (preflightOk) {
        exec(`"${pythonPath}" "${orchestratorPath}" --background`, (error, stdout, stderr) => {
          if (stdout) process.stderr.write(stdout);
          if (stderr) process.stderr.write(stderr);
        });
      }
    } else {
      process.stderr.write(`\n[WARN] GCS orchestrator not found: ${orchestratorPath}\n`);
    }
    lastCompactBucket = bucket;
  }

  fs.writeFileSync(STATE_FILE, JSON.stringify({
    last_notified_step: Math.max(lastStep, currentStep),
    last_compact_bucket: lastCompactBucket,
    prompt_tokens: promptTokens,
    max_context: MAX_CONTEXT,
    model_name: modelName,
    timestamp: new Date().toISOString()
  }));
  } catch(e) {
    process.stderr.write(`\n[ERROR] token_monitor failed: ${e && e.stack ? e.stack : e}\n`);
  }
}

function findProjectRoot(current) {
  let depth = 0;
  while (current !== '/' && depth < 10) {
    if (
      fs.existsSync(path.join(current, '.git')) ||
      fs.existsSync(path.join(current, 'GEMINI.md')) ||
      fs.existsSync(path.join(current, 'src', 'gcs', 'gcs_orchestrator.py'))
    ) return current;
    current = path.dirname(current);
    depth++;
  }
  return null;
}

if (require.main === module) {
  main();
  console.log(JSON.stringify({}));
}

module.exports = {
  resolveMaxContext,
  getCompactBucketsToTrigger,
  findProjectRoot,
  main,
};
