# Responsible AI in NetSage AI

This document explains the limitations, risks, and human-oversight design of NetSage AI, and why the system is built the way it is. It should be read alongside `docsARCHITECTURE.md` and `IMPLEMENTATION_PLAN.md`.

## 1. AI Hallucination

Large language models can produce confident, well-formatted, and completely wrong output. In a networking troubleshooting context, this can take several concrete forms:

- **Invented evidence** — the model claims a `show` command output said something it never actually said, or references an IP address, VLAN, or interface that never appeared in the supplied evidence.
- **Incorrect diagnosis** — the model identifies a plausible-sounding root cause that does not match the actual evidence supplied for the case.
- **Incorrect command** — the model recommends a Packet Tracer/IOS command that is syntactically wrong, does not exist, or would not actually help verify the stated diagnosis.
- **Incorrect topology interpretation** — the model misreads relationships between devices (e.g. assumes two interfaces are on the same subnet when the topology notes do not support that).

NetSage AI does not assume these risks away. Instead, the system is architected so that no single AI output can become a final result without independent checks:

- The AI's system prompt (`ai/prompts.py`) explicitly instructs the model to distinguish observations from conclusions, avoid inventing evidence, and flag uncertainty.
- Every AI response is parsed and schema-validated (`ai/schema.py`, `ai/validator.py`) before it can reach a human. Malformed, incomplete, or structurally invalid output is rejected outright — it never reaches the diagnosis display.
- The AI's conclusion is checked against deterministic Python rules (`core/comparison.py`), and any disagreement is surfaced explicitly rather than hidden.
- A human must review every AI diagnosis before it is treated as final (see Section 2).

## 2. Human Oversight Is Mandatory

NetSage AI cannot mark any diagnosis as final without a human explicitly choosing to Accept, Edit, or Reject it (`core/review.py`). This is not a convenience feature — it is a structural requirement enforced in code: there is no code path in the system that produces a "final" diagnosis without going through `submit_review()`.

Human review is mandatory because:

- The AI has no way to physically verify a network — it only reasons from the text evidence it was given.
- Confidence scores reported by the AI (0–100) reflect the model's own self-assessment, not a guarantee of correctness.
- A student or engineer applying a fix in a real (or simulated) network needs to be accountable for that fix, not defer responsibility to an automated system.
- The evaluation in M13 exists specifically to measure how often human correction is genuinely needed — treating that number as evidence for why review must stay mandatory, not as a problem to be optimized away.

## 3. Why Deterministic Validation (Python) Exists Alongside AI

Some networking conditions are mechanically verifiable from `show` command text — a subnet mask either matches or it doesn't; a VLAN either appears in `show vlan brief` or it doesn't. These conditions do not require language understanding, and using an LLM to check them introduces unnecessary risk of error or inconsistency.

`rules/` implements six such checks (duplicate IP, wrong subnet mask, gateway mismatch, interface down, missing VLAN, missing route) using plain string/regex parsing and arithmetic — no AI call, no ambiguity, and fully reproducible. Given the same input, a Python rule always produces the same output. The same is not true of an LLM.

Critically, the Python rules are conservative by design: when the supplied evidence is insufficient to reach a conclusion, a rule reports `insufficient_evidence` rather than guessing. This is enforced by explicit tests (e.g. `test_route_does_not_invent_required_destination`, `test_vlan_does_not_treat_missing_table_as_vlan_absent`) that check the rules never fabricate a determination from missing data.

## 4. Packet Tracer Evidence Has Priority Over AI Assumptions

The AI's system prompt explicitly instructs it to treat supplied Packet Tracer/IOS command output as ground truth for the lab state, and to analyze only the evidence it was given (`ai/prompts.py`). The AI is never given the dataset's "expected" answer fields (`core/dataset_loader.py`'s `runtime_input()` function enforces this at the code level, not just by instruction) — it must reason from the same raw evidence a human engineer would have.

This matters because an AI that is allowed to substitute its own assumptions for actual command output would no longer be diagnosing the specific lab in front of it — it would be pattern-matching to what a *typical* case of that type usually looks like, which may not be true here.

## 5. Why the AI Must Identify Uncertainty

A diagnosis presented with unwarranted confidence is more dangerous than one that honestly says "I'm not sure." NetSage AI's structured output format requires an `uncertainties` field, and the system prompt explicitly instructs the model to identify missing evidence rather than fill the gap with a guess.

This mirrors the same design principle behind the Python rules' `insufficient_evidence` status: **absence of information should be reported as absence of information**, not silently converted into a confident-sounding answer. A reviewer who sees "uncertain, and here's what's missing" is much better positioned to make a good decision than one shown a confident diagnosis that is quietly guessing.

## 6. System Boundaries and Limitations

NetSage AI is a **troubleshooting assistant**, not an autonomous network administrator. It does not:

- Connect to, control, or modify a live Packet Tracer simulation or any real network device.
- Apply any fix automatically. All fixes described in a diagnosis are recommendations for a human to manually apply and verify.
- Guarantee correctness. The AI is one input among several (Python rules, human judgment, actual command evidence) — not a source of ground truth on its own.
- Learn, retrain, or improve itself from usage. Every case is evaluated independently with no memory of prior sessions.

**We do not claim the AI is always correct.** We do not claim the Python rules can detect every possible networking problem — they cover six specific, mechanically verifiable conditions, not the full space of network faults. We do not claim that the absence of a Python finding proves a network is healthy; `NO_DETERMINISTIC_RESULT` and `PYTHON_ONLY`/`AI_ONLY` comparison states exist specifically to make that distinction visible rather than papering over it.

The system's actual value comes from combining four things — Packet Tracer evidence, deterministic Python validation, AI reasoning, and mandatory human review — not from AI alone.