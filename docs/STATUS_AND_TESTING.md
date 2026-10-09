# Status and testing

Archive checkpoint: 2026-10-09. Development paused when the user moved to Arkham Knight.

## User reports

- v1: Infinite Health and melee Super Damage work.
- v3: first Anarky race appeared frozen, but a bounded temporary memory helper also held the countdown. This does not prove the native pause-bit method.
- v4: subsequent Anarky race continued counting down, including after checkpoint reload.
- v5: latest fix directly holds captured `RemainingTime` plus matching HUD integer. Live inspection showed the timer decreased even with its pause bit set. Auto-follow and scoped selection retained. **No standalone user confirmation yet.**

## Included features / test scope

Health; enemy controller freeze; melee damage/one-hit and experimental Batarang KO/projectile edits; grapple/Batarang reach; minimum 99 upgrade points; challenge HUD score and challenge/predator timer experiments; J/K/L positions; F1-F4 upward teleports; scoped Anarky bomb countdown hold.

The relevant layouts were inspected live. Lua API simulations redirected gameplay writes to an overlay. These are implementation/metadata checks, not evidence of in-game success. Challenge HUD fields do not establish medal/save score manipulation. Other gadgets are not claimed supported.

No armor refill, no-hit-box, fly, XP, combo, waypoint, puzzle bypass, or global Gameplay/Time section. City-only Zsasz phone race not copied into Origins.

## Research scripts

`origins_anarky_rescue.py` is a bounded live-memory WRITE helper, not a normal table dependency. Do not run it blindly. Other historical tests contain session-specific addresses/PIDs and require review before reuse. Dependencies are intentionally not bundled. Generated runtime/builder correspond to v5; v1-v4 source lives inside historical CTs.