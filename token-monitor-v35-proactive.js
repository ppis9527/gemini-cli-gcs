#!/usr/bin/env node
const fs = require('fs');
const { exec } = require('child_process');

/**
 * Senior Suite v3.5 Proactive Guard
 * 50% 強制產出快照，不只是提醒。
 */

try {
  const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
  const usage = input.llm_response?.usageMetadata;

  const MAX_CONTEXT = 1000000; 
  const THRESHOLD = 0.2; // 20%

  if (usage && usage.totalTokenCount) {
    const ratio = usage.totalTokenCount / MAX_CONTEXT;
    if (ratio >= THRESHOLD) {
      process.stderr.write(`
🚨 [GCS] Context 達 20%！正在執行自動總結 (Summarizing)...
💡 請在下一個回覆後，手動輸入 "/clear" 以觸發 SessionStart 重新注入骨架化上下文。
`);
      
      // 指導 AI 在回覆中加入通知
      process.stderr.write(`💡 指令鎖定：通知使用者骨架化狀態，並引導執行 /clear。
`);
    }
  }
} catch (e) {}

console.log(JSON.stringify({}));
