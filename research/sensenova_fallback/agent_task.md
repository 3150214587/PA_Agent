# Agent Task: SenseNova free-model fallback

## Goal

In `D:\cl\PA_Agent`, implement a SenseNova-only analysis fallback:

- Trigger **only** when `provider.base_url` normalizes to `https://token.sensenova.cn/v1`.
- On ordinary analysis failures (429 / network / timeout / server / empty response / JSON parse / validation failure, etc.), automatically try public free models from [Ebony-Vinyl/dsh-our-free-model](https://github.com/Ebony-Vinyl/dsh-our-free-model).
- Success requires **real upstream call + successful stage validation**.
- Other `base_url` values unchanged.
- User cancel / `KeyboardInterrupt` must not be swallowed.
- No infinite retries; bounded candidate rotation with cache/cooldown.
- Do not overwrite existing uncommitted work (`market_features`, prompt_engineering txt, `research/pa_validation`, etc.).
- Do not change trading / live-order logic.
- No DSH plugin install, no DSH config changes, no dependency upgrades.
- Use only public no-auth channels: **Kilo** (`isFree` discovery) + **OpenCode Zen** (`Bearer public`). No EAC / login credential channels.
- Never send the primary SenseNova API key to free upstreams.
- Provide unit tests + a `__file__`-based live verification script that saves run records without secrets.
- Save this task and the full agent result under `research/sensenova_fallback/`.

## Constraints (from upstream README)

- Kilo free pool may log prompts — synthetic prompts only for live checks.
- Respect upstream auth/rate limits; do not spoof identity to bypass limits.
- Fail closed (no fabricated success JSON).
