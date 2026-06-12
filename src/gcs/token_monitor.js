#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');
const { exec, execSync, execFileSync } = require('child_process');
const IS_WIN = process.platform === "win32";

const LOCK_TIMEOUT_MS = 2000; // 2s global protection, ensuring it absolutely never blocks main user conversation
const timer = setTimeout(() => process.exit(0), LOCK_TIMEOUT_MS);
timer.unref();

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
  return String(modelName || '')
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
    const args = ['display-message'];
    if (process.env.TMUX_PANE) {
      args.push('-t', process.env.TMUX_PANE);
    }
    args.push('-p', '-F', '#{session_id}');
    const sessionId = execFileSync('tmux', args, {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 1500,
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

function shouldResetSession(previousPromptTokens, currentPromptTokens, maxContext, lastTimestamp) {
  const previous = Number(previousPromptTokens || 0);
  const current = Number(currentPromptTokens || 0);
  const limit = Number(maxContext) > 0 ? Number(maxContext) : 1048576;

  // Reset if the last update was more than 5 minutes ago (idle timeout)
  if (lastTimestamp && (Date.now() - new Date(lastTimestamp).getTime() > 5 * 60 * 1000)) {
    return true;
  }

  if (previous > 0 && current > 0) {
    // Reset if it drops below 10% of maximum context (meaning it transitioned from above 10% to below 10%)
    if (previous / limit >= 0.10 && current / limit < 0.10) {
      return true;
    }
    // Or if it drops by more than 50% of the previous value (e.g. manual clear)
    if (current < previous * 0.5) {
      return true;
    }
  }
  return false;
}

function printToPane(text) {
  try {
    if (!process.env.TMUX && !process.env.TMUX_PANE) {
      process.stderr.write(text + '\n');
      return;
    }
    const args = ['display-message'];
    if (process.env.TMUX_PANE) {
      args.push('-t', process.env.TMUX_PANE);
    }
    args.push('-p', '#{pane_tty}');
    const tty = execFileSync('tmux', args, {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 1500,
    }).trim();
    if (tty && fs.existsSync(tty)) {
      // Print on the line above the current cursor position to avoid splitting prompt input
      fs.writeFileSync(tty, `\x1b[s\x1b[A\r\x1b[K${text}\x1b[u`);
    } else {
      process.stderr.write(text + '\n');
    }
  } catch (e) {
    process.stderr.write(text + '\n');
  }
}



function main() {
  if (process.stdin.isTTY) {
    console.log(JSON.stringify({}));
    process.exit(0);
  }
  try {
    const rawInput = fs.readFileSync(0, 'utf-8');
    if (!rawInput.trim()) { console.log(JSON.stringify({})); process.exit(0); }
    const input = JSON.parse(rawInput);
    if (!input || typeof input !== 'object') { console.log(JSON.stringify({})); process.exit(0); }

    let promptTokens = 0;
    let outputTokens = 0;
    let cachedTokens = 0;
    let modelName = 'gemini-2.5-flash';
    let maxContextOverride = null;

    if (input.context_window) {
      // Format B: Jetski statusline payload
      promptTokens = Number(input.context_window.total_input_tokens) || 0;
      outputTokens = Number(input.context_window.total_output_tokens) || 0;
      const currUsage = input.context_window.current_usage || {};
      cachedTokens = Number(currUsage.cache_read_input_tokens) || 0;
      modelName = String(input.model?.id || input.model || 'gemini-2.5-flash').toLowerCase();
      maxContextOverride = input.context_window.context_window_size || null;
    } else if (input.llm_response) {
      // Format A: Standard model hook payload
      const resp = input.llm_response;
      const usage = resp.usageMetadata || resp.usage || {};
      promptTokens = Number(usage.promptTokenCount || usage.input_tokens) || 0;
      outputTokens = Number(usage.candidatesTokenCount || usage.output_tokens) || 0;
      cachedTokens = Number(usage.cachedContentTokenCount || usage.cache_creation_input_tokens || usage.cache_read_input_tokens) || 0;
      modelName = String(resp.model || input.llm_request?.model || 'gemini-2.5-flash').toLowerCase();
    } else {
      // Unsupported structure
      console.log(JSON.stringify({}));
      process.exit(0);
    }

    if (promptTokens === 0) { console.log(JSON.stringify({})); process.exit(0); }

    const parsedOverride = Number(maxContextOverride);
    const MAX_CONTEXT = (parsedOverride > 0) ? parsedOverride : resolveMaxContext(modelName);

    const ratio = promptTokens / MAX_CONTEXT;
    const percentUsed = (ratio * 100).toFixed(1);

  const projectRoot = findProjectRoot(process.cwd()) || (fs.existsSync(path.join(process.cwd(), 'src', 'gcs', 'gcs_orchestrator.py')) ? process.cwd() : null);
  const flashIcon = (projectRoot && fs.existsSync(path.join(projectRoot, '.gemini', 'gcs.pending'))) ? " ⚡" : "";
  const sessionId = resolveTmuxSessionId();
  const sessionPaths = getSessionRuntimePaths(sessionId);
  const globalStatusPath = sessionPaths.statusFile;

  const HOME = os.homedir();
  let gdriveStatusPath = null;
  if (IS_WIN) {
    gdriveStatusPath = "G:\\My Drive\\MyMDs\\System status\\gcert\\.remote_gcs_status";
  } else if (process.platform === "darwin") {
    const cloudStorageDir = path.join(HOME, "Library/CloudStorage");
    let username = null;
    try {
      username = os.userInfo().username || process.env.USER || process.env.USERNAME;
    } catch (e) {
      username = process.env.USER || process.env.USERNAME;
    }
    if (username) {
      let gdriveDir = `GoogleDrive-${username}@google.com`; // Dynamic fallback default
      try {
        if (fs.existsSync(cloudStorageDir)) {
          const folders = fs.readdirSync(cloudStorageDir);
          const found = folders.find(f => f.startsWith("GoogleDrive-"));
          if (found) gdriveDir = found;
        }
      } catch(e) {}
      gdriveStatusPath = path.join(cloudStorageDir, gdriveDir, "My Drive/MyMDs/System status/gcert/.remote_gcs_status");
    }
  } else {
    gdriveStatusPath = path.join(HOME, "DriveFileStream/My Drive/MyMDs/System status/gcert/.remote_gcs_status");
  }

  function writeStatus(text) {
    try {
      fs.mkdirSync(sessionPaths.sessionRoot, { recursive: true });
      fs.writeFileSync(globalStatusPath, text);
      // Also write to the global / legacy path so unified status readers (like tmux_remote_dashboard.sh) can work out-of-the-box
      const legacyStatusPath = path.join(sessionPaths.runtimeRoot, 'tmux_status');
      fs.writeFileSync(legacyStatusPath, text);
    } catch(e) {}
    if (gdriveStatusPath) {
      // Use asynchronous writeFile to prevent Cloud Drive disk I/O locking up the process
      fs.writeFile(gdriveStatusPath, text, (err) => {});
    }
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
      if (shouldResetSession(state.prompt_tokens, promptTokens, MAX_CONTEXT, state.timestamp)) {
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
  if (pendingCompactBuckets.length > 0) {
    const bucket = pendingCompactBuckets[pendingCompactBuckets.length - 1];
    const color = bucket >= 50 ? '\x1b[1;31m' : '\x1b[1;33m';
    const msg = `${color}🚨 [GCS] ${bucket}% threshold reached. Background compaction triggered!\x1b[0m`;
    printToPane(msg);
    try {
      writeStatus(`[GCS: ${percentUsed}% ⚡ YOLO]`);
    } catch(e) {}
    const localPython = IS_WIN
      ? (projectRoot ? path.join(projectRoot, '.gemini', 'gcs-venv', 'Scripts', 'python.exe') : null)
      : (projectRoot ? path.join(projectRoot, '.gemini', 'gcs-venv', 'bin', 'python3') : null);
    const extensionPaths = [
      path.join(os.homedir(), '.gemini', 'extensions', 'custom-session-manager'),
      path.join(os.homedir(), '.gemini', 'skills', 'custom-session-manager'),
      path.join(os.homedir(), '.gemini', 'local-extensions', 'custom-session-manager')
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

    const isAbsExtPy = path.isAbsolute(extensionPython);
    let pythonPath = (localPython && fs.existsSync(localPython))
      ? localPython
      : ((isAbsExtPy && fs.existsSync(extensionPython)) ? extensionPython : (IS_WIN ? 'python' : 'python3'));

    const localOrchestrator = projectRoot ? path.join(projectRoot, 'src', 'gcs', 'gcs_orchestrator.py') : '';
    const orchestratorPath = fs.existsSync(localOrchestrator) ? localOrchestrator : extensionOrchestrator;
    const preflightPath = orchestratorPath ? path.join(path.dirname(orchestratorPath), 'gcs_preflight.py') : '';


    if (fs.existsSync(orchestratorPath)) {
      let preflightOk = true;
      if (fs.existsSync(preflightPath)) {
        try {
          execFileSync(pythonPath, [preflightPath], { stdio: 'ignore', timeout: 1500 });
        } catch (e) {
          try {
            const fallbackPy = IS_WIN ? 'python' : 'python3';
            execFileSync(fallbackPy, [preflightPath], { stdio: 'ignore', timeout: 1500 });
            pythonPath = fallbackPy;
          } catch (fallbackErr) {
            preflightOk = false;
            process.stderr.write(`\n[WARN] GCS preflight failed. Install deps: pip install -r requirements.txt\n`);
          }
        }
      }

      if (preflightOk) {
        const { spawn: spawnProcess } = require("child_process");
        
        // Redirect child process stderr to gcs.log to capture background issues
        const logFile = projectRoot ? path.join(projectRoot, '.gemini', 'gcs.log') : path.join(os.tmpdir(), 'gcs.log');
        let logFd = null;
        try {
          fs.mkdirSync(path.dirname(logFile), { recursive: true });
          logFd = fs.openSync(logFile, 'a');
        } catch (e) {}

        const child = spawnProcess(pythonPath, [orchestratorPath, "--tokens", promptTokens.toString(), "--background"], {
          detached: true,
          cwd: projectRoot || process.cwd(),
          stdio: ["ignore", "ignore", logFd || "ignore"],
          windowsHide: true
        });
        
        // Immediately close the parent's copy of logFd to prevent descriptor leaks.
        // The child process retains its copy because of the stdio mapping.
        if (logFd) {
          try { fs.closeSync(logFd); } catch(e) {}
        }
        child.unref();
      }
    } else {
      process.stderr.write(`\n[WARN] GCS orchestrator not found: ${orchestratorPath}\n`);
    }
    lastCompactBucket = bucket;
  }

  fs.writeFileSync(STATE_FILE, JSON.stringify({
    last_notified_step: currentStep,
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
  current = path.resolve(current);
  let depth = 0;
  const rootDir = path.parse(current).root;
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
