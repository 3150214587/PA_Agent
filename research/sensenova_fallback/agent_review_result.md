# Agent Review Result: SenseNova free-model fallback fixes

## Verdict

Review blockers addressed with a **minimal Kilo-only** SenseNova free fallback. Offline unit tests for the new wiring pass (**19**). Related two-stage / validation / qclaw checks also pass. Pre-existing dirty files and baseline KKAI failures were left untouched. Full live PromptAssembler+JsonValidator+TwoStage pipeline acceptance remains for the main agent via `D:\tools\data\pa-fallback-review\full_pipeline_probe.py` (not modified).

## What changed (this review round)

| Path | Change |
| --- | --- |
| `pa_agent/ai/sensenova_fallback.py` | Rewrote: Kilo-only; real `PA-Agent/sensenova-fallback` UA; prefer Ling3.1 + Nemotron3.5-lightning; cooldown-before-cap; exclude content-safety; no forced `reasoning.enabled=false`; reject empty / reasoning-only / truncated; `Exception` not `BaseException`; cancel before listing; full attempt traces |
| `pa_agent/orchestrator/two_stage.py` | SenseNova-only catch of ordinary `Exception` on first call **and** `validate_with_retry` raise; non-SenseNova keeps network-only; clear stale fallback failure at submit start; `_try` uses `Exception` |
| `pa_agent/ai/deepseek_client.py` | SenseNova only: OpenAI `max_retries=0` + `call_with_rate_limit_backoff(max_retries=0)` on chat/stream; other providers unchanged |
| `tests/unit/test_sensenova_fallback.py` | Full `TwoStageOrchestrator.submit` coverage (S1/S2 network/ValueError/illegal JSON/validate-retry, primary OK, other URL, cancel, all-fail trace, real JsonValidator, cooldown-before-cap) |
| `research/sensenova_fallback/verify_free_fallback.py` | Rewrote: no OpenCode; strict JSON; no `'ok' in text`; safe `_save` redaction; smoke vs analysis flags |
| `research/sensenova_fallback/agent_review_task.md` | Full fix task saved |
| `research/sensenova_fallback/agent_review_result.md` | This file |

### Intentionally not modified

- `pa_agent/ai/market_features.py`, `tests/unit/test_market_features.py`
- prompt_engineering `*.txt`
- `research/pa_validation/`, PA research reports
- `D:\tools\data\pa-fallback-review\full_pipeline_probe.py`
- Trading / order paths; no new dependencies

## Checklist mapping

1. **Ordinary Exception + validate_with_retry** — SenseNova catches `Exception` (not cancel/SystemExit/KeyboardInterrupt) on stream and on `validate_with_retry`; non-SenseNova still only records `_is_network_error` / ValidationError paths.
2. **No OpenCode** — deleted OC UA / bash fingerprint / session ids; Kilo `isFree` only; UA=`PA-Agent/sensenova-fallback`; preferred order starts with `inclusionai/ling-3.1-flash`, `nvidia/nemotron-3.5-lightning:free`.
3. **Candidates** — filter cooldown then take ≤6; drop `*content-safety*` / guard models; do not inject `reasoning.enabled=false`.
4. **Failure hygiene** — `Exception` catches; cancel before listing; submit clears prior failure; empty/reasoning-only/`finish_reason=length` rejected; validator `Ok(wait/reject)` treated as success.
5. **SenseNova fast-fail** — SDK + rate-limit backoff `max_retries=0` only when `_is_sensenova(base_url)`; DeepSeek/other unchanged (no `max_retries` override).
6. **Tests** — orchestrator `submit` integration, not helper-only.
7. **verify script** — smoke-labeled live connectivity; `analysis_success` always false here.
8. **Artifacts** — `agent_review_task.md` + this result.

## Diff summary (functional)

### `two_stage.py`

- `s1_primary_network_error` / `s2_primary_network_error` → `s1_primary_error` / `s2_primary_error` (+ type `network_error`|`provider_error`).
- SenseNova: any ordinary primary/`validate_with_retry` Exception enters free fallback.
- Non-SenseNova: ValueError still propagates; network errors still save `network_error`.
- `self._last_sensenova_fallback_failure = None` at each `submit` start.

### `sensenova_fallback.py`

- Removed OpenCode listing/call/fingerprint/`Bearer public` path entirely.
- `build_candidates`: preferred verified models first; skip cooldown **then** cap; exclude safety-only ids.
- `call_free_candidate`: Kilo POST only; real PA-Agent UA; reject empty / reasoning-only / truncated.

### `deepseek_client.py`

- SenseNova chat + stream: `OpenAI(max_retries=0)` and backoff `max_retries=0`.
- Spot-check: SenseNova kwargs include `max_retries: 0`; DeepSeek kwargs omit override.

## Tests run (offline / lightweight)

```bat
D:\cl\PA_Agent\.venv\Scripts\python.exe -m pytest ^
  D:\cl\PA_Agent\tests\unit\test_sensenova_fallback.py ^
  D:\cl\PA_Agent\tests\unit\test_qclaw_auto_fallback.py ^
  D:\cl\PA_Agent\tests\unit\test_validation_retry.py ^
  D:\cl\PA_Agent\tests\integration\test_two_stage_network_timeout.py ^
  D:\cl\PA_Agent\tests\integration\test_two_stage_user_cancel.py ^
  D:\cl\PA_Agent\tests\integration\test_two_stage_happy_path.py -q
```

Result: **all passed** (19 fallback + 3 qclaw + validation_retry + listed two-stage integrations).

```bat
set PA_FALLBACK_LIVE=0
D:\cl\PA_Agent\.venv\Scripts\python.exe D:\cl\PA_Agent\research\sensenova_fallback\verify_free_fallback.py
```

Result: `ok=true`, `analysis_success=false`, checks gate/key_isolation/candidates_offline all true.  
Saved: `research/sensenova_fallback/runs/20261010T014439Z_verify.json`

### Not run / not claimed

- Live Kilo smoke (`PA_FALLBACK_LIVE=1`) — optional; main agent owns full pipeline probe.
- `tests/unit/test_deepseek_client.py` baseline 3 KKAI failures — pre-existing, not fixed.
- Broader integration suite failures in `baseline-integration.log` — out of scope.

## Residual risks

- Free pool rate limits / model churn can still exhaust 6 candidates; failure stays closed with attempt traces.
- Kilo may log prompts — fallback should only carry the same analysis prompts the product already sends.
- Small free models may fail Stage1/Stage2 schema more often than SenseNova primary; that is expected fail-closed behavior.

## Main-agent next step

```bat
D:\cl\PA_Agent\.venv\Scripts\python.exe D:\tools\data\pa-fallback-review\full_pipeline_probe.py
```

Note: probe injects builtin `ConnectionError` on primary; SenseNova now treats that as ordinary Exception and enters free fallback (previously `_is_network_error` did **not** classify bare `ConnectionError`, so the probe would miss fallback).
