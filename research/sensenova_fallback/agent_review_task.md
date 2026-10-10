# Agent Review Task: SenseNova free-model fallback fixes

## Context

Previous SenseNova free-model fallback implementation in `D:\cl\PA_Agent` did **not** pass main-agent review and must not be treated as done. Existing dirty/unrelated edits must not be overwritten:

- `pa_agent/ai/market_features.py`
- `tests/unit/test_market_features.py`
- prompt_engineering texts
- `research/pa_validation/` and related PA research reports

Independent baseline / checklist (do not modify `full_pipeline_probe.py`):

- `D:\tools\data\pa-fallback-review\baseline.md`
- `D:\tools\data\pa-fallback-review\review-checklist.md`
- Main agent acceptance probe: `D:\tools\data\pa-fallback-review\full_pipeline_probe.py`

Goal: **minimal reliable SenseNova-only free fallback** via public no-auth Kilo `isFree` pool. No complex persistent service, no new dependencies, no OpenCode Zen disguise channel.

## Required fixes

### 1. `two_stage.py` exception coverage (SenseNova only)

- First-call failures currently enter fallback only for `_is_network_error`; ordinary `ValueError` / `RuntimeError` are re-raised and miss fallback.
- Exceptions raised by `validate_with_retry` itself (including retry-time network failures) also miss fallback.
- **Only SenseNova** (`base_url` → `https://token.sensenova.cn/v1`) must catch ordinary `Exception` and enter free fallback.
- Non-SenseNova must keep prior behavior.
- Cancel / `SystemExit` / `KeyboardInterrupt` must never be swallowed (`Exception` catch, not `BaseException`).

### 2. Remove OpenCode Zen; Kilo-only + real UA

- Delete entire OpenCode channel (UA spoof, fake bash/glob/grep/read tool fingerprint, session/request id headers).
- Keep only public no-auth Kilo `isFree` pool (sufficient).
- Real main-agent probes: `inclusionai/ling-3.1-flash` and `nvidia/nemotron-3.5-lightning:free` → HTTP 200 JSON / cost 0.
- Prefer those two over `kilo-auto/free`.
- User-Agent must be a real PA-Agent identifier (not `dsh-our-free-model` / OpenCode spoof).

### 3. Candidate building

- Filter cooldown **first**, then take at most 6 (current take-6-then-filter drops usable models).
- Exclude safety-classification-only models (e.g. content-safety / guard).
- Do **not** force thinking models with `reasoning.enabled=false` unconditionally.

### 4. Failure hygiene in free runner

- Broad `BaseException` catches → ordinary `Exception`.
- Check cancel before model listing.
- Full attempt traces on total failure; clear stale failure state across submits.
- Reject empty body / reasoning-only / truncated (`finish_reason=length`).
- Do not treat legal `wait` / `reject` validator outcomes as errors.

### 5. SenseNova primary retry must not delay fallback

- In `DeepSeekClient`, for SenseNova only: OpenAI SDK `max_retries=0`.
- `call_with_rate_limit_backoff(..., max_retries=0)`.
- No stream-create 429 restart loop for SenseNova.
- Other providers unchanged.

### 6. Unit tests: full `TwoStageOrchestrator` wiring

Must exercise orchestrator `submit` integration (not only `run_free_stage_fallback` helper):

- Stage1 & Stage2: network error / ordinary exception / illegal JSON / `validate_with_retry` raise
- Primary success → no fallback call
- Other `base_url` → no fallback
- Cancel + all-candidates-fail closed
- Fallback must go through real `JsonValidator`
- Cooldown candidate filtering

### 7. Rewrite `verify_free_fallback.py`

- Delete OpenCode path.
- Strict JSON parse; never treat substring `"ok"` as success.
- `_save` must not `replace('', '***')`.
- Persist full request/response/error (no secrets).
- Connectivity-only runs must be labeled **smoke**, not full analysis success.

### 8. Artifacts

- Save this full fix task as `agent_review_task.md` (this file).
- Final complete result as `agent_review_result.md`.
- Run offline / lightweight tests only; do not “fix” pre-existing baseline failures (KKAI deepseek_client 3 fails; unrelated integration fails).

## Non-goals

- No trading / live-order changes
- No DSH plugin / config / dependency upgrades
- No fabricated success JSON
- No persistence service beyond in-memory listing cache + cooldowns
