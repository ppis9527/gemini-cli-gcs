#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');
const { exec, execSync } = require('child_process');
const IS_WIN = process.platform === "win32";

function resolveMaxContext(modelName) {
  const model = normalizeModelName(modelName);
  const MODEL_CONTEXT_MAP = {
    'gpt-oss-120b': 131072,
  };
  if (model.startsWith('gpt-oss-120b')) return MODEL_CONTEXT_MAP['gpt-oss-120b'];

  if (hasToken(model, 'claude') || hasToken(model, 'sonnet') || hasToken(model, 'opus')) {
    return 200000;
  }

  if (hasToken(model, 'gemini')) {
    return hasToken(model, 'pro') ? 2097152 : 1048576;
  }

  if (hasToken(model, 'flash')) return 1048576;
  if (hasToken(model, 'pro')) return 2097152;

  return 1048576;
}

function normalizeModelName(modelName) {
  return (modelName || '')
    .toLowerCase()
    .replace(/\([^)]*\)/g, ' ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function hasToken(model, token) {
  return new RegExp(`(^|-)${token}(-|$)`).test(model);
}

function getCompactBucketsToTrigger(lastCompactBucket, percent, buckets = [20, 30, 40, 50, 60, 70]) {
  return buckets.filter((b) => b > lastCompactBucket && b <= percent);
}

function resolveTmuxSessionId() {
  try {
    if (!process.env.TMUX && !process.env.TMUX_PANE) return 'no-tmux';
    const sessionId = execSync("tmux display-message -p -F '#{session_id}'", {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
    return sessionId || 'no-tmux';
  } catch (e) {
    return 'no-tmux';
  }
}

function getSessionRuntimePaths(sessionId) {
  const runtimeRoot = path.join(process.env.HOME, '.gemini', 'gcs-guardian');
  const sessionRoot = path.join(runtimeRoot, 'sessions', sessionId || 'no-tmux');
  return {
    runtimeRoot,
    sessionRoot,
    stateFile: path.join(sessionRoot, 'monitor_state.json'),
    statusFile: path.join(sessionRoot, 'tmux_status'),
  };
}

function shouldResetSession(previousPromptTokens, currentPromptTokens) {
  const previous = Number(previousPromptTokens || 0);
  const current = Number(currentPromptTokens || 0);
  return previous > 0 && current > 0 && current < previous;
}

function main() {
  try {
    const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
    let promptTokens = 0;
    let outputTokens = 0;
    let cachedTokens = 0;
    let modelName = 'gemini-2.5-flash';
    let maxContextOverride = null;

    if (input.context_window) {
      // Format B: Jetski statusline payload
      promptTokens = input.context_window.total_input_tokens || 0;
      outputTokens = input.context_window.total_output_tokens || 0;
      const currUsage = input.context_window.current_usage || {};
      cachedTokens = currUsage.cache_read_input_tokens || 0;
      modelName = (input.model?.id || 'gemini-2.5-flash').toLowerCase();
      maxContextOverride = input.context_window.context_window_size || null;
    } else if (input.llm_response) {
      // Format A: Standard model hook payload
      const resp = input.llm_response;
      const usage = resp.usageMetadata || resp.usage || {};
      promptTokens = usage.promptTokenCount || usage.input_tokens || 0;
      outputTokens = usage.candidatesTokenCount || usage.output_tokens || 0;
      cachedTokens = usage.cachedContentTokenCount || usage.cache_creation_input_tokens || usage.cache_read_input_tokens || 0;
      modelName = (resp.model || input.llm_request?.model || 'gemini-2.5-flash').toLowerCase();
    } else {
      // Unsupported structure
      console.log(JSON.stringify({}));
      process.exit(0);
    }

    if (promptTokens === 0) { console.log(JSON.stringify({})); process.exit(0); }

    const MAX_CONTEXT = maxContextOverride || resolveMaxContext(modelName);

    const ratio = promptTokens / MAX_CONTEXT;
    const percentUsed = (ratio * 100).toFixed(1);

  const projectRoot = findProjectRoot(process.cwd()) || (fs.existsSync(path.join(process.cwd(), 'src', 'gcs', 'gcs_orchestrator.py')) ? process.cwd() : null);
  const flashIcon = (projectRoot && fs.existsSync(path.join(projectRoot, '.gemini', 'gcs.pending'))) ? " ⚡" : "";
  const sessionId = resolveTmuxSessionId();
  const sessionPaths = getSessionRuntimePaths(sessionId);
  const globalStatusPath = sessionPaths.statusFile;

  const HOME = os.homedir();
  let gdriveStatusPath;
  if (IS_WIN) {
    gdriveStatusPath = "G:\\My Drive\\MyMDs\\System status\\gcert\\.remote_gcs_status";
  } else if (process.platform === "darwin") {
    const cloudStorageDir = path.join(HOME, "Library/CloudStorage");
    let gdriveDir = "GoogleDrive-yaojenliu@google.com"; // Fallback default
    try {
      if (fs.existsSync(cloudStorageDir)) {
        const folders = fs.readdirSync(cloudStorageDir);
        const found = folders.find(f => f.startsWith("GoogleDrive-"));
        if (found) gdriveDir = found;
      }
    } catch(e) {}
    gdriveStatusPath = path.join(cloudStorageDir, gdriveDir, "My Drive/MyMDs/System status/gcert/.remote_gcs_status");
  } else {
    gdriveStatusPath = path.join(HOME, "DriveFileStream/My Drive/MyMDs/System status/gcert/.remote_gcs_status");
  }

  function writeStatus(text) {
    try {
      fs.mkdirSync(sessionPaths.sessionRoot, { recursive: true });
      fs.writeFileSync(globalStatusPath, text);
    } catch(e) {}
    try {
      fs.mkdirSync(path.dirname(gdriveStatusPath), { recursive: true });
      fs.writeFileSync(gdriveStatusPath, text);
    } catch(e) {}
  }

  writeStatus(`GCS: ${percentUsed}%${flashIcon}`);

  if (!fs.existsSync(sessionPaths.sessionRoot)) fs.mkdirSync(sessionPaths.sessionRoot, { recursive: true });

  const STATE_FILE = sessionPaths.stateFile;
  let lastStep = 0;
  let lastCompactBucket = 0;
  if (fs.existsSync(STATE_FILE)) {
    try {
      const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
      lastStep = state.last_notified_step || 0;
      lastCompactBucket = state.last_compact_bucket || 0;
      if (shouldResetSession(state.prompt_tokens, promptTokens)) {
        lastStep = 0;
        lastCompactBucket = 0;
      }
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
      writeStatus(`[GCS: ${percentUsed}% ⚡ YOLO]`);
    } catch(e) {}
    const localPython = IS_WIN
      ? path.join(projectRoot || "", '.gemini', 'gcs-venv', 'Scripts', 'python.exe')
      : path.join(projectRoot || "", '.gemini', 'gcs-venv', 'bin', 'python3');
    const extensionPaths = [
      path.join(process.env.USERPROFILE || process.env.HOME, '.gemini', 'extensions', 'custom-session-manager'),
      path.join(process.env.USERPROFILE || process.env.HOME, '.gemini', 'skills', 'custom-session-manager'),
      path.join(process.env.USERPROFILE || process.env.HOME, '.gemini', 'local-extensions', 'custom-session-manager')
    ];

    let extensionPython = IS_WIN ? 'python' : 'python3';
    let extensionOrchestrator = '';

    for (const extDir of extensionPaths) {
      const py = IS_WIN
        ? path.join(extDir, 'venv', 'Scripts', 'python.exe')
        : path.join(extDir, 'venv', 'bin', 'python3');
      const orch = path.join(extDir, 'src', 'gcs', 'gcs_orchestrator.py');
      if (fs.existsSync(orch)) {
        extensionOrchestrator = orch;
        if (fs.existsSync(py)) {
          extensionPython = py;
        }
        break;
      }
    }

    const pythonPath = fs.existsSync(localPython) ? localPython : (fs.existsSync(extensionPython) ? extensionPython : (IS_WIN ? 'python' : 'python3'));

    const localOrchestrator = projectRoot ? path.join(projectRoot, 'src', 'gcs', 'gcs_orchestrator.py') : '';
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
        const { spawn: spawnProcess } = require("child_process");
        const child = spawnProcess(pythonPath, [orchestratorPath, "--tokens", promptTokens.toString(), "--background"], {
          detached: true,
          stdio: "ignore"
        });
        child.on("error", (err) => {
          process.stderr.write(`\n[ERROR] GCS distillation failed: ${err.message}\n`);
        });
        child.unref();
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
  const rootDir = IS_WIN ? current.split(path.sep)[0] + path.sep : "/";
  while (depth < 10) {
    if (
      fs.existsSync(path.join(current, '.git')) ||
      fs.existsSync(path.join(current, 'GEMINI.md')) ||
      fs.existsSync(path.join(current, 'src', 'gcs', 'gcs_orchestrator.py'))
    ) return current;
    if (current === rootDir) break;
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
  resolveTmuxSessionId,
  getSessionRuntimePaths,
  shouldResetSession,
  findProjectRoot,
  main,
};
