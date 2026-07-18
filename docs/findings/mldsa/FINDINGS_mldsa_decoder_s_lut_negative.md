# FINDINGS: decoder S-case constant-LUT — negative result

**Verdict: REVERTED.** WNS -4.299 -> -4.582 (regressed 0.283ns). Correctness
was never the issue: both variants bit-exact, block gate + 1-vector KAT PASS.

## What was tried
Constant-LUT rewrite of the S-mode sample transform in decoder's
SIPO_IN -> SIPO_OUT cone, following the validated rejection_s pattern:
s_lut2 as a full 8-entry table (ETA=2), s_lut4 in arithmetic form (ETA=4).

## Why it regressed (interpretation)
The probe was designed to answer mode attribution inside the transform cone,
and it did: the binding mode is NOT S. Either T0/Z (13-20 bit domains) bind
the cone, or the LUT form disturbed cross-mode logic sharing. Both readings
exclude the same lever: T0/Z domains are too wide to LUT (2^13..2^20 entries),
so the constant-LUT strategy is EXCLUDED for decoder's transform cone entirely.

## Remaining decoder options
Sign-select on the T0/Z compare-correct shapes is the one taxonomy-internal
idea left: arguable because decoder operands are narrower (13-20b) than
butterfly's 24b case that serialized, but risky for the same structural
reason. Flagged, not attempted. Beyond that: placement/directive/architectural
class, out of current scope.

## Rule for orchestrator priors
constant_lut requires small proven input domain (<=8-10 bits at most);
mode-shared transform cones need mode attribution BEFORE proposing a
mode-specific rewrite — a bit-exact rewrite of a non-binding mode adds
area/disturbs sharing and regresses.
