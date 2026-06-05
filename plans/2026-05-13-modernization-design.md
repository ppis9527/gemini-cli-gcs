# Design Doc: custom-session-manager Modernization (gPowers Standard)

## 1. Problem Statement
The `custom-session-manager` (V5.4.3) possesses excellent core logic (6-Layer Context Governance, High-Fidelity Skeletonization). However, its current implementation lacks modern Agentic Ergonomics and structural safeguards:
- `SKILL.md` is plain Markdown, risking LLM hallucination and unbounded execution.
- Python scripts emit raw text/markdown instead of structured data.
- The `/compact` workflow creates friction by forcing the user to manually copy-paste massive prompts to restart the session.
- Lack of empirical testing (`EVAL.yaml`).

## 2. Goals
**Preserve** the core tactical logic (skeletonization, quotas, 6-layers) while **Modernizing** the wrapper and integration points to meet strict `gPowers` standards.

## 3. Proposed Architecture & Refactoring Plan

### 3.1 Structural Modernization (`SKILL.md`)
Wrap the existing logic in explicit XML boundaries.
- `<instructions>`: The step-by-step workflow for `/compact`, `/snapshot`, and `/scan2db`.
- `<constraints>`: Strict negative prompts (e.g., "Do NOT summarize physical code differently than the skeletonizer output").
- `<examples>`: Concrete multi-turn examples showing exactly how the Agent should call `skeletonize.py`.

### 3.2 Output Standardization (Python Scripts)
Refactor `skeletonize.py` and `quota_manager.py` to communicate cleanly with the LLM.
- **Current**: Returns raw strings with `# Error:` inline.
- **Proposed**: Return strictly formatted JSON objects:
  ```json
  {
    "status": "success|error",
    "data": { "skeletons": [...] },
    "error_msg": null
  }
  ```
  *Benefit: The agent can reliably parse the output and implement fallback logic without guessing.*

### 3.3 Zero-Friction Context Handoff (The `/compact` UX)
**Current Workflow**: Agent prints a text block -> User presses Ctrl+C -> User restarts CLI -> User pastes text block.
**Proposed Alternatives (For Discussion):**
- **Alternative A (The Payload File - Recommended)**: The Agent writes the full L1-L6 state to a specific `handoff.json` or `handoff.md` in a `.gemini/tmp/` directory. It tells the user: *"Run `gemini` and type `/load_handoff`"*. 
- **Alternative B (Native State Injection)**: If the Gemini CLI has an automated context-flushing tool, invoke it directly. (Assuming none exists, Alternative A is safest).

### 3.4 Verification Layer
Implement an `EVAL.yaml` to ensure future iterations of the CLI do not break this skill.
- Test 1: Ensure `/compact` calls `skeletonize.py` exactly 5 times.
- Test 2: Ensure quota thresholds are respected.

## 4. Migration Strategy
1. Backup current `SKILL.md`.
2. Rewrite `SKILL.md` with XML tags.
3. Refactor Python scripts for JSON output and update `sanitizers.py` tests.
4. Implement the `EVAL.yaml` test suite.

#gemini-cli #design #gpowers #session-manager #2026-05-13
