# Governance pulse reference doctrine

The dual-signal pulse is intentionally closer to an operational Action Review than to a sentiment dashboard.

## External reference pattern

WHO Action Reviews ask responders to identify what worked, what worked less well, why, and how to improve. UNDRR monitoring and recovery guidance likewise treats promising trends, persistent gaps, lessons and corrective action as parallel inputs to governance.

The control plane adapts that logic into a continuously updateable evidence object:

```text
source developments
      ↓
state-direction classification
      ↓
┌─────────────────┬─────────────────┐
│ stress frontier │ progress frontier│
└─────────────────┴─────────────────┘
      ↓                    ↓
problem selection      learning candidates
      └────────────┬───────────────┘
                   ↓
             replay / shadow test
                   ↓
          bounded policy/action review
```

## Why not sentiment

A positive headline can describe activity without improved outcomes. A negative headline can describe a severe event even where the response machinery performed well. Governance therefore classifies the condition, not the tone.

Examples:

- "500 personnel deployed" -> activity;
- "fire extinguished" -> outcome improvement;
- "burned area doubled" -> adverse system signal;
- "funding announced" -> activity/output depending on evidence;
- "households regained reliable water access" -> outcome improvement.

## Why not netting

The pulse deliberately has no `net_score` field.

If one province contains a fire while another experiences catastrophic growth in burned area, both facts remain true. A net score would destroy the information needed for governance.

The same rule applies outside disasters:

- MBG: one SPPG improving delivery does not cancel a severe safety incident elsewhere;
- animal welfare: higher reunification in one district does not cancel worsening shelter overload elsewhere;
- poverty: improved benefit delivery does not erase households still excluded from an entitlement.

## What progress is for

Progress evidence has three uses:

1. preserve practices that appear to work;
2. generate hypotheses about why one place/time performed better than another;
3. identify candidate interventions for replay/shadow testing elsewhere.

It is not automatic proof of causal effectiveness or transferability.

## Relationship with Nocturnal

Nocturnal should continue to preserve sourced developments without being forced to decide whether a story is "good" or "bad".

The governance layer interprets a development relative to a domain-specific desired state.

This lets the same source event remain journalism/public memory in Nocturnal while becoming an adverse, improvement or ambiguous governance signal here.
