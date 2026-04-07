/**
 * @file gcs_intercept.js
 * @description GCS PrePrompt Hook: Explicit Guardian & Edit Intent Interceptor (v1.20)
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

module.exports = async function(context) {
    const PROJECT_ROOT = process.cwd();
    const CHECKPOINT_PATH = path.join(PROJECT_ROOT, '.gemini', 'checkpoint.json');

    // 1. Check if we're in a re-hydrated state (L4 presence)
    if (fs.existsSync(CHECKPOINT_PATH)) {
        // Log to GCS log
        const LOG_PATH = path.join(PROJECT_ROOT, '.gemini', 'gcs.log');
        fs.appendFileSync(LOG_PATH, `[${new Date().toISOString()}] PrePrompt: Active Checkpoint Detected.\n`);
    }

    // 2. Intercept Editing Intent
    // If user's prompt contains modification requests for skeletonized files
    const prompt = context.user_prompt || "";
    const is_modifying = /\b(modify|edit|update|change|rewrite)\b/i.test(prompt);

    if (is_modifying) {
        // Call Python Interceptor to check target files
        const INTERCEPT_PY = path.join(PROJECT_ROOT, 'src', 'gcs', 'gcs_intercept.py');
        const VENV_PYTHON = path.join(PROJECT_ROOT, '.gemini', 'gcs-venv', 'bin', 'python3');

        try {
            // Check if any skeletonized files are being accessed
            // This is a simplified check for demo; a production script would parse the prompt for file paths
            const result = execSync(`${VENV_PYTHON} ${INTERCEPT_PY} --check-intent`, { encoding: 'utf-8' });
            if (result.includes("RE-HYDRATION_REQUIRED")) {
                console.log("\n⚠️ GCS: Target file is skeletonized. Re-hydrating context for precision edit...");
            }
        } catch (e) {
            // Silently fail if interceptor script fails
        }
    }

    // 3. Proactive Notifications (Every 5%)
    const current_tokens = context.input_tokens || 0;
    const limit = context.max_tokens || 2000000; // Fallback to 2M if max_tokens is undefined
    const saturation = (current_tokens / limit) * 100;

    // Ensure we only notify ONCE per 5% bucket
    const currentBucket = Math.floor(saturation / 5) * 5;
    const STATE_FILE = path.join(PROJECT_ROOT, '.gemini', 'gcs_notify.state');
    
    let lastBucket = 0;
    try { lastBucket = parseInt(fs.readFileSync(STATE_FILE, 'utf-8'), 10); } catch(e) {}

    if (currentBucket > 0 && currentBucket % 5 === 0 && currentBucket > lastBucket) {
        console.log(`\n[GCS Guardian] Current Context: ${saturation.toFixed(0)}% (${current_tokens} tokens)`);
        try { fs.writeFileSync(STATE_FILE, currentBucket.toString()); } catch(e) {}
    }
};
