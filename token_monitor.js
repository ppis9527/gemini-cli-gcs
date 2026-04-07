/**
 * @file token_monitor.js
 * @description GCS AfterTool Hook: Proactive Token Monitoring (v1.20)
 */

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

module.exports = async function(context) {
    const PROJECT_ROOT = process.cwd();
    const GCS_THRESHOLD = 0.20; // 20%
    const GCS_LIMIT = context.max_tokens || 200000; // Default to 200k if not specified
    const current_tokens = context.input_tokens || 0;
    const saturation = current_tokens / GCS_LIMIT;

    // 1. Log metrics to GCS log
    const LOG_PATH = path.join(PROJECT_ROOT, '.gemini', 'gcs.log');
    const log_entry = `[${new Date().toISOString()}] AfterTool: input_tokens=${current_tokens}, saturation=${(saturation * 100).toFixed(2)}%\n`;
    fs.appendFileSync(LOG_PATH, log_entry);

    // 2. Check threshold
    if (saturation >= GCS_THRESHOLD) {
        // 3. Pre-emptive Background Distillation
        const DISTILLER_PATH = path.join(PROJECT_ROOT, 'src', 'gcs', 'gcs_orchestrator.py');
        const VENV_PYTHON = path.join(PROJECT_ROOT, '.gemini', 'gcs-venv', 'bin', 'python3');

        console.log(`\n🚨 GCS: Context reached ${(saturation * 100).toFixed(0)}%. Pre-emptive distillation triggered...`);

        // Run in background (YOLO mode)
        exec(`${VENV_PYTHON} ${DISTILLER_PATH} --background`, (error, stdout, stderr) => {
            if (error) {
                fs.appendFileSync(LOG_PATH, `[${new Date().toISOString()}] Error: Distillation failed: ${stderr}\n`);
            } else {
                fs.appendFileSync(LOG_PATH, `[${new Date().toISOString()}] Success: Background distillation completed.\n`);
            }
        });

        // 4. Notify user if critically high
        if (saturation >= 0.80) {
            console.warn("\n⚠️ GCS: Context is critically full (>80%). Please use /clear after this turn.");
        }
    }
};
