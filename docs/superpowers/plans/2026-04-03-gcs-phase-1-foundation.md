# Implementation Plan: GCS Phase 1 - Foundation & Security (v1.5)

## 1. Objective
Establish core physical layout, proactive budget monitoring, and symmetric realpath jailing.

## 2. Tasks

### T1: Global Layout Implementation
- **Action**: Define GCS Layer 1-6 using XML delimiters.
- **Requirement**: MUST test against isolated `$GEMINI_HOME` first.

### T2: Context Paging & Sanitization
- **Action**: ANSI stripping + `<context_pagination>` for tool outputs > 5k tokens.

### T3: Symmetric Realpath Lock
- **Action**: Implement `Path(target).resolve().relative_to(Path(root).resolve())`.
- **TestCase**: Include `../../` and symlink-to-external jumps.

### T4: Proactive Budget & TTFT Logging
- **Action**: Report `<gcs_metrics>` and log TTFT for performance baseline comparison.

## 3. Validation Plan (Isolated Testing)

### V1: Sandbox Environment Setup
- **Base Path**: `/tmp/gcs-test-bench`
- **Isolation**: `export GEMINI_HOME=/tmp/gcs-test-bench/.gemini`.
- **Files**:
  - `root/secret.txt` (local)
  - `root/ext_link` -> symlink to `/etc/hosts`
  - `root/large.log` (10k tokens)

### V2: Unit Verification
1. **Security**:
   - `read_file("ext_link")` -> DENY.
   - `read_file("../../../etc/passwd")` -> DENY.
2. **Layout**: Verify Layer 1-6 XML ordering in isolated GEMINI.md.
3. **Paging**: `cat large.log` -> verify pagination marker + unit="tokens".
4. **Budget**: Cross 20k -> verify `<gcs_metrics>` + `checkpoint.json` write.

### V3: Success Criteria
- `Cached_TTFT / Uncached_TTFT < 0.4`.
- 100% ANSI clean in all test bench logs.

## 4. Rollout Strategy
1. **Validation**: Execute V1-V3 in bench.
2. **Promotion**: Copy tested GEMINI.md to `~/.gemini/GEMINI.md` ONLY after 100% pass.
