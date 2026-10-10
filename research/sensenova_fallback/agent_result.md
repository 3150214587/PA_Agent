# Agent Result: SenseNova free-model fallback

## Verdict

Implemented SenseNova-only free-model fallback at the **two-stage orchestrator** layer so both transport failures and JSON/validation failures can recover. Offline unit tests pass (13). Live verification script succeeded against Kilo + OpenCode listing/chat with synthetic prompts only.

## Project notes

- Repo has no dedicated `AGENTS.md`; followed `CONTRIBUTING.md` / existing orchestrator patterns (`_try_qclaw_fallback` style) and upstream free-model protocol from [dsh-our-free-model](https://github.com/Ebony-Vinyl/dsh-our-free-model).
- Did **not** modify pre-existing dirty files: `pa_agent/ai/market_features.py`, `tests/unit/test_market_features.py`, prompt_engineering `*.txt`, `research/pa_validation/`, research PA reports.
- Did **not** change trading / order logic; no live trading started.
- Did **not** install DSH plugin, change DSH config, or upgrade dependencies.

## Design boundaries

| Rule | Implementation |
| --- | --- |
| Gate | `normalize_base_url(base_url) == https://token.sensenova.cn/v1` only |
| Trigger | Stage1/Stage2 **network/HTTP** errors **or** `ValidationError` after `validate_with_retry` |
| Success | Free upstream reply **and** `JsonValidator` `Ok` for that stage |
| Providers | Kilo (`GET /models` + `isFree:true`, no auth) + OpenCode Zen (`Bearer public` + fingerprint tools, chat wire only) |
| Excluded | EAC / login credential channels; responses/messages-only OpenCode ids |
| Key isolation | Primary SenseNova key never placed in free request headers/body; asserted in code + tests |
| Cancel | `CancelledError` / `KeyboardInterrupt` re-raised; not treated as ordinary errors |
| Bounds | Max 6 candidates/stage; listing cache 30m; 429 cooldown 5m; each candidate once |
| Fail closed | Exhausted candidates keep original failure + `sensenova_free_fallback.attempts` trace; no fake JSON |
| Settings | Ephemeral free calls only — does **not** rewrite `settings.json` to free providers |

### Call chain (where fallback sits)

1. GUI → `TwoStageOrchestrator.submit`
2. `_stream_chat_resilient` → primary `DeepSeekClient.stream_chat` (existing QClaw/Cursor/… fallbacks unchanged)
3. `validate_with_retry` → `JsonValidator.validate` (+ normalizers)
4. **New:** on ordinary failure + SenseNova gate → `run_free_stage_fallback` → httpx chat completions → same stage validator
5. Only then continue Stage1→Stage2 success path or persist failure record

## Modified / added paths

```
pa_agent/ai/sensenova_fallback.py          (new)
pa_agent/orchestrator/two_stage.py         (wire Stage1/Stage2 recover)
tests/unit/test_sensenova_fallback.py      (new)
research/sensenova_fallback/agent_task.md
research/sensenova_fallback/agent_result.md
research/sensenova_fallback/verify_free_fallback.py
research/sensenova_fallback/runs/*.json    (verification records)
```

## Unit tests

Command:

```bat
D:\cl\PA_Agent\.venv\Scripts\python.exe -m pytest D:\cl\PA_Agent\tests\unit\test_sensenova_fallback.py D:\cl\PA_Agent\tests\unit\test_qclaw_auto_fallback.py -q
```

Result: **16 passed** (13 fallback + 3 qclaw regression).

Covered:

- primary success condition does not enter free runner
- non-SenseNova base_url does not trigger
- ordinary network error types vs cancel
- first candidate fail → next candidate success
- all candidates fail closed
- cancel / KeyboardInterrupt not swallowed
- validation/parse failure rotates candidate
- primary API key isolation (Kilo + OpenCode)
- Kilo discovery requires `isFree`
- orchestrator tracks provider/model attempts

## Live verification (main-agent independent)

```bat
D:\cl\PA_Agent\.venv\Scripts\python.exe D:\cl\PA_Agent\research\sensenova_fallback\verify_free_fallback.py
```

Latest success record: `research/sensenova_fallback/runs/20261010T012902Z_verify.json`

- gate + key isolation: OK
- Kilo live chat: OK (`poolside/laguna-xs-2.1:free` → `{"status":"ok","sum":7}`)
- OpenCode free list + chat: OK (`space-bunny-free`)
- No secrets written into run JSON

Optional offline-only: `set PA_FALLBACK_LIVE=0` then re-run script.

### End-to-end product acceptance (manual)

1. Keep `config/settings.json` `provider.base_url` = `https://token.sensenova.cn/v1` (or with trailing `/`).
2. Temporarily break SenseNova (invalid key / firewall) **or** wait for a real 429/timeout.
3. Run one analysis in PA Agent GUI; on failure, logs should show `SenseNova free fallback triggered`.
4. Success only if stage validation passes; inspect record `stage*_response.raw.fallback_provider/model` or exception `sensenova_free_fallback.attempts`.
5. Switch `base_url` to `https://api.deepseek.com` and confirm free fallback never runs.

## Residual risks

- Free upstreams are rate-limited (429); cooldowns + rotation mitigate but cannot guarantee availability.
- Kilo may log prompts — do not send secrets/private market materials intentionally via fallback if avoidable.
- Full PA Stage1/Stage2 JSON via free small models may still fail validation; failure remains closed with attempt traces.
- OpenCode region blocks / fingerprint policy can reject some egresses; Kilo remains the primary free pool.
