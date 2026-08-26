# NetSage AI — Cursor Implementation Plan

## Purpose

This document converts the NetSage AI architecture into incremental implementation milestones.

Cursor must follow the milestones **in the exact order defined below**.

Do not skip milestones.

Do not combine milestones.

Do not implement future functionality early unless explicitly required as a dependency.

The project must remain aligned with the official requirements:

- Cisco Packet Tracer troubleshooting helper
- Symptoms + topology notes + show-command output
- AI diagnosis
- OSI layer
- Confidence
- Evidence
- Next command
- Fix steps
- Mandatory human review
- Accept / Edit / Reject
- At least 30 troubleshooting cases
- VLAN, gateway, DHCP, DNS, routing, ACL, NAT, wireless
- Deterministic Python rules:
  - duplicate IP
  - wrong subnet mask
  - gateway mismatch
  - interface down
  - missing VLAN
  - missing route
- Structured AI output
- At least 5 human-corrected AI cases
- Dashboard:
  - issue types
  - severity
  - AI vs human agreement
- Demo:
  - broken lab
  - symptom
  - Packet Tracer evidence
  - AI analysis
  - Python check
  - comparison
  - human review
  - fix
  - verification

---

# GLOBAL CURSOR RULES

Before implementing any milestone, Cursor must:

1. Inspect the existing repository.
2. Read the relevant documentation.
3. Preserve existing working code.
4. Avoid unnecessary refactoring.
5. Follow the contracts in this document.
6. Write tests for new logic.
7. Run the relevant tests before declaring the milestone complete.
8. Do not implement features belonging to future milestones.
9. Do not invent requirements.
10. Do not replace deterministic logic with AI.
11. Do not hardcode API keys or secrets.
12. Do not invent Packet Tracer evidence.
13. Do not bypass mandatory human review.

When a milestone is complete, Cursor should report:

```text
Milestone:
Files created:
Files modified:
Tests executed:
Tests passed:
Acceptance criteria:
Known limitations:
```

---

# M0 — PROJECT SETUP

## Objective

Create the initial Python/Streamlit project structure, dependency configuration, Git configuration, environment configuration, and basic application entry point.

No actual networking logic or AI diagnosis should be implemented yet.

---

## Files to create

```text
app.py
requirements.txt
README.md
.gitignore
.env.example

config/
    __init__.py
    settings.py

core/
    __init__.py

ai/
    __init__.py

rules/
    __init__.py

data/
    .gitkeep

tests/
    __init__.py

docs/
    .gitkeep
```

---

## Files to modify

None.

---

## Dependencies

Python 3.x

Required initial packages should be limited to what is actually needed.

At minimum:

```text
streamlit
openai
python-dotenv
pydantic
pytest
```

If an additional dependency is introduced, document why it is necessary.

---

## Input/Output contracts

### Input

Environment configuration:

```text
OPENAI_API_KEY
```

The API key may be absent during M0.

### Output

The application must start successfully.

Example:

```text
NetSage AI
System initialized.
```

---

## Implementation requirements

### 1. Create repository structure

Use the project structure defined in the architecture.

### 2. Configure environment variables

Use:

```text
.env
```

for local development.

`.env` must not be committed.

`.env.example` may contain:

```text
OPENAI_API_KEY=
```

### 3. Create settings module

The settings module must provide access to configuration without exposing secrets.

### 4. Create minimal Streamlit entry point

`app.py` should only prove that the environment works.

### 5. Create Git configuration

`.gitignore` must exclude:

```text
.env
__pycache__/
.pytest_cache/
*.pyc
```

and other generated files as appropriate.

---

## Tests required

Verify:

- Python environment works
- Imports work
- Settings module imports
- Streamlit application starts
- Tests can run using pytest

---

## Acceptance criteria

- [ ] Repository structure exists.
- [ ] `app.py` starts.
- [ ] `requirements.txt` exists.
- [ ] `.gitignore` protects secrets.
- [ ] `.env.example` exists.
- [ ] No API key is hardcoded.
- [ ] pytest executes successfully.
- [ ] No networking logic exists yet.
- [ ] No AI diagnosis exists yet.

---

## What must NOT be implemented yet

Do NOT implement:

- Data models
- Dataset loader
- Rule engine
- AI diagnosis
- AI JSON schema
- Comparison engine
- Human review
- Review logging
- Dashboard
- Packet Tracer integration

---

# M1 — DATA MODELS

## Objective

Create strongly defined data models representing the core entities of NetSage AI.

The models become the foundation for all later milestones.

Use Pydantic models.

---

## Files to create

```text
models/
    __init__.py
    case.py
    diagnosis.py
    rules.py
    comparison.py
    review.py
    verification.py
```

---

## Files to modify

```text
README.md
```

Only if necessary to document the model architecture.

---

## Dependencies

M0 complete.

Pydantic installed.

---

## Input/Output contracts

### Case

```json
{
  "case_id": "CASE-001",
  "issue_type": "VLAN",
  "severity": "medium",
  "symptom": "...",
  "topology_notes": "...",
  "show_output": "...",
  "expected_root_cause": "...",
  "expected_osi_layer": "Layer 2",
  "expected_next_command": "...",
  "expected_fix": "...",
  "verification": "..."
}
```

### AI diagnosis

```json
{
  "diagnosis": {
    "root_cause": "string",
    "issue_type": "VLAN",
    "osi_layer": "Layer 2",
    "confidence": 85,
    "severity": "medium"
  },
  "evidence": [],
  "next_command": {},
  "fix_steps": [],
  "uncertainties": []
}
```

### Python finding

```json
{
  "rule_id": "missing_vlan",
  "status": "detected",
  "evidence": []
}
```

### Comparison

```json
{
  "status": "AGREEMENT",
  "reason": "..."
}
```

### Human review

```json
{
  "review_id": "REV-001",
  "case_id": "CASE-001",
  "human_decision": "accepted",
  "human_final_diagnosis": {},
  "review_comment": "..."
}
```

### Verification

```json
{
  "status": "verified",
  "evidence": "..."
}
```

---

## Implementation requirements

Create validation for:

### Issue types

```text
VLAN
GATEWAY
DHCP
DNS
ROUTING
ACL
NAT
WIRELESS
OTHER
```

### Severity

```text
low
medium
high
```

### Review decisions

```text
accepted
edited
rejected
```

### Comparison states

```text
AGREEMENT
PARTIAL_AGREEMENT
AI_ONLY
PYTHON_ONLY
CONFLICT
NO_DETERMINISTIC_RESULT
```

### Verification states

```text
verified
not_verified
not_attempted
```

Confidence must be between:

```text
0–100
```

Models must reject invalid values.

---

## Tests required

Test:

- Valid case creation
- Invalid issue type
- Invalid severity
- Invalid review decision
- Confidence below 0
- Confidence above 100
- Valid AI diagnosis
- Invalid AI diagnosis
- Valid comparison
- Valid review
- Valid verification

---

## Acceptance criteria

- [ ] All core entities have models.
- [ ] Models validate invalid input.
- [ ] Models serialize to JSON.
- [ ] Models deserialize from JSON.
- [ ] Tests pass.
- [ ] No business logic exists in the models.

---

## What must NOT be implemented yet

Do NOT implement:

- Dataset loading
- Networking rules
- OpenAI API calls
- Streamlit review UI
- Dashboard
- Comparison logic

---

# M2 — DATASET LOADER

## Objective

Create the case dataset structure and loader.

The loader must support at least 30 troubleshooting cases.

---

## Files to create

```text
data/
    cases.json

core/
    dataset_loader.py

tests/
    test_dataset_loader.py
```

---

## Files to modify

```text
models/case.py
```

Only if required to support dataset serialization.

---

## Dependencies

- M1 data models
- JSON
- Pydantic

---

## Input/Output contracts

### Input

```text
data/cases.json
```

### Output

```text
list[Case]
```

---

## Dataset requirements

The dataset must contain at least:

```text
30 cases
```

The dataset must cover:

```text
VLAN
Gateway
DHCP
DNS
Routing
ACL
NAT
Wireless
```

Each case must contain sufficient information to reproduce the troubleshooting scenario.

---

## Implementation requirements

The loader must:

- Load JSON.
- Validate every case.
- Return typed Case objects.
- Reject malformed cases.
- Report which case failed validation.
- Never silently discard invalid cases.

The dataset must not expose expected answers to the AI during normal runtime.

---

## Tests required

Test:

- Dataset loads.
- All cases validate.
- Minimum case count is satisfied.
- Required issue categories exist.
- Duplicate case IDs are rejected.
- Malformed case is rejected.
- Missing required field is rejected.

---

## Acceptance criteria

- [ ] `cases.json` contains at least 30 valid cases.
- [ ] All eight required categories are represented.
- [ ] Dataset loader returns validated models.
- [ ] Invalid datasets fail clearly.
- [ ] Dataset tests pass.

---

## What must NOT be implemented yet

Do NOT implement:

- AI analysis
- Rule engine
- Dashboard
- Human review
- Automatic evaluation
- Packet Tracer automation

---

# M3 — PYTHON RULE ENGINE

## Objective

Implement the six required deterministic networking checks.

This milestone is critical.

The rules must operate independently of the AI.

---

## Files to create

```text
rules/
    engine.py
    duplicate_ip.py
    subnet_mask.py
    gateway.py
    interface.py
    vlan.py
    route.py

tests/
    test_rule_engine.py
```

---

## Files to modify

```text
models/rules.py
```

Only if additional structured rule information is required.

---

## Dependencies

- M1
- M2

---

## Input/Output contracts

### Input

```json
{
  "symptom": "...",
  "topology_notes": "...",
  "show_output": "..."
}
```

### Output

```json
{
  "findings": [
    {
      "rule_id": "duplicate_ip",
      "status": "detected",
      "evidence": [
        "..."
      ]
    }
  ]
}
```

---

# Required rules

## R001 — Duplicate IP

Detect multiple devices/interfaces using the same IP address.

Only report a duplicate when the supplied evidence explicitly supports it.

---

## R002 — Wrong subnet mask

Detect a subnet mask inconsistency only when enough information exists to determine that it is wrong.

Do not guess the expected subnet mask.

---

## R003 — Gateway mismatch

Detect when:

- Gateway is outside the host's subnet, or
- Gateway conflicts with explicitly supplied topology information.

---

## R004 — Interface down

Detect explicit interface states such as:

```text
administratively down
down/down
```

Do not infer interface state from missing output.

---

## R005 — Missing VLAN

Detect when a VLAN required by supplied topology/configuration is absent from the supplied VLAN evidence.

---

## R006 — Missing route

Detect when a required destination network has no corresponding route in supplied routing evidence.

The required destination must come from supplied information.

---

## Implementation requirements

The engine must:

- Run rules independently.
- Return structured findings.
- Preserve evidence.
- Clearly distinguish:
  - detected
  - not_detected
  - insufficient_evidence
- Never invent missing information.
- Never call OpenAI.
- Never depend on an AI result.

---

## Tests required

At minimum test:

```text
duplicate IP:
    detected
    not detected
    insufficient evidence

subnet:
    detected
    valid
    insufficient evidence

gateway:
    detected
    valid
    insufficient evidence

interface:
    down
    up
    insufficient evidence

VLAN:
    missing
    present
    insufficient evidence

route:
    missing
    present
    insufficient evidence
```

---

## Acceptance criteria

- [ ] Six deterministic rules exist.
- [ ] Rules operate without OpenAI.
- [ ] Rules return structured findings.
- [ ] Rules preserve evidence.
- [ ] Insufficient evidence is distinguishable from no problem.
- [ ] No AI code exists inside the rule engine.
- [ ] Tests pass.

---

## What must NOT be implemented yet

Do NOT implement:

- OpenAI calls
- AI prompts
- AI diagnosis
- Comparison
- Human review
- Streamlit UI
- Dashboard

---

# M4 — RULE ENGINE TESTS

## Objective

Harden the deterministic rule engine using comprehensive unit tests.

This milestone is intentionally separate from M3.

The goal is to prove that the Python component is trustworthy before AI is introduced.

---

## Files to create

```text
tests/
    fixtures/
        rule_cases.json

    test_duplicate_ip.py
    test_subnet_mask.py
    test_gateway.py
    test_interface.py
    test_vlan.py
    test_route.py
```

---

## Files to modify

Rule files only when tests expose actual defects.

---

## Dependencies

M3.

---

## Input/Output contracts

Input:

```text
controlled evidence fixture
```

Output:

```text
expected deterministic finding
```

---

## Implementation requirements

Create tests for:

1. Positive detection
2. Negative detection
3. Insufficient evidence
4. Multiple simultaneous findings
5. Malformed evidence
6. Empty evidence

Tests should verify both:

```text
rule result
+
evidence
```

---

## Tests required

All tests in this milestone are themselves the tests.

Run:

```text
pytest
```

---

## Acceptance criteria

- [ ] Every required rule has dedicated tests.
- [ ] Positive cases pass.
- [ ] Negative cases pass.
- [ ] Insufficient evidence cases pass.
- [ ] Malformed input is handled safely.
- [ ] Entire test suite passes.
- [ ] Rule engine behavior is stable.

---

## What must NOT be implemented yet

Do NOT implement:

- AI
- OpenAI API
- Comparison
- Human review
- UI
- Dashboard

---

# M5 — AI DIAGNOSIS SERVICE

## Objective

Create the service responsible for sending troubleshooting evidence to OpenAI and receiving a structured diagnosis.

---

## Files to create

```text
ai/
    diagnosis.py
    prompts.py
```

---

## Files to modify

```text
config/settings.py
```

Only if required for API configuration.

---

## Dependencies

- M1
- M3
- OpenAI API

---

## Input/output contract

### Input

```json
{
  "symptom": "...",
  "topology_notes": "...",
  "show_output": "...",
  "python_findings": []
}
```

### Output

Raw AI response.

The raw response must NOT be trusted yet.

M6 will validate it.

---

## Implementation requirements

The AI prompt must instruct the model to:

- Analyze only supplied information.
- Treat Packet Tracer evidence as authoritative.
- Use Python findings as deterministic evidence.
- Distinguish observations from conclusions.
- Avoid inventing evidence.
- Explicitly identify uncertainty.
- Recommend a next command.
- Return the required troubleshooting information.

The service must:

- Use the OpenAI API.
- Handle API errors.
- Handle timeouts/errors.
- Return raw response data to the validation layer.
- Never silently fabricate a fallback diagnosis.

---

## Tests required

Without requiring a live API call:

- Service initialization
- Missing API key
- Request construction
- Error handling
- Timeout handling

Use mocks for OpenAI calls.

---

## Acceptance criteria

- [ ] OpenAI service exists.
- [ ] API key comes from configuration.
- [ ] No key is hardcoded.
- [ ] Prompt includes required evidence.
- [ ] Prompt explicitly prevents evidence hallucination.
- [ ] API errors are handled.
- [ ] Tests use mocks.
- [ ] No unvalidated AI response is displayed as final diagnosis.

---

## What must NOT be implemented yet

Do NOT implement:

- Final AI schema validation
- Comparison
- Human review
- Dashboard
- End-to-end UI

---

# M6 — AI STRUCTURED OUTPUT VALIDATION

## Objective

Validate and normalize AI output against the project's structured diagnosis model.

No AI response should reach the user as a diagnosis unless it passes validation.

---

## Files to create

```text
ai/
    schema.py
    validator.py

tests/
    test_ai_validation.py
```

---

## Files to modify

```text
models/diagnosis.py
ai/diagnosis.py
```

Only when necessary.

---

## Dependencies

M1 and M5.

---

## Input/output contract

### Input

Raw AI response.

### Output

Validated:

```text
AIDiagnosis
```

or:

```text
ValidationError
```

---

## Required fields

```text
diagnosis.root_cause
diagnosis.issue_type
diagnosis.osi_layer
diagnosis.confidence
diagnosis.severity

evidence
next_command
fix_steps
uncertainties
```

---

## Implementation requirements

Validation must reject:

- Invalid JSON
- Missing fields
- Invalid issue type
- Invalid severity
- Confidence outside 0–100
- Invalid evidence structure
- Missing next command
- Invalid fix steps

The system should provide useful error information.

---

## Tests required

Test:

- Valid response
- Missing field
- Invalid JSON
- Invalid issue type
- Invalid severity
- Confidence >100
- Confidence <0
- Empty evidence
- Invalid next command
- Invalid fix steps

---

## Acceptance criteria

- [ ] Invalid AI responses cannot become diagnoses.
- [ ] Valid responses become typed models.
- [ ] Validation tests pass.
- [ ] AI output cannot bypass validation.

---

## What must NOT be implemented yet

Do NOT implement:

- Comparison
- Human review
- Dashboard
- Full Streamlit workflow

---

# M7 — AI + PYTHON COMPARISON ENGINE

## Objective

Compare AI reasoning with deterministic Python findings.

The engine must distinguish agreement from absence of deterministic evidence.

---

## Files to create

```text
core/
    comparison.py

tests/
    test_comparison.py
```

---

## Files to modify

```text
models/comparison.py
```

Only if required.

---

## Dependencies

M3, M4, M6.

---

## Input/output contract

### Input

```json
{
  "ai_diagnosis": {},
  "python_findings": []
}
```

### Output

```json
{
  "status": "AGREEMENT",
  "reason": "..."
}
```

---

## Required statuses

```text
AGREEMENT
PARTIAL_AGREEMENT
AI_ONLY
PYTHON_ONLY
CONFLICT
NO_DETERMINISTIC_RESULT
```

---

## Implementation requirements

### AGREEMENT

AI and Python identify substantially the same issue.

### PARTIAL_AGREEMENT

They identify related problems but not exactly the same diagnosis.

### AI_ONLY

AI identifies a problem outside the deterministic rules.

### PYTHON_ONLY

Python identifies a deterministic problem AI did not identify.

### CONFLICT

The conclusions materially disagree.

### NO_DETERMINISTIC_RESULT

Python cannot establish a deterministic finding from available evidence.

The engine must NOT assume:

```text
no Python finding = AI is wrong
```

---

## Tests required

Create test cases for every comparison status.

Also test:

- Empty Python findings
- Multiple Python findings
- Multiple evidence items
- AI diagnosis with unrelated issue type

---

## Acceptance criteria

- [ ] All six comparison states work.
- [ ] Comparison is deterministic.
- [ ] Comparison does not call OpenAI.
- [ ] Comparison does not modify AI output.
- [ ] Tests pass.

---

## What must NOT be implemented yet

Do NOT implement:

- Human review
- Review persistence
- Streamlit workflow
- Dashboard

---

# M8 — HUMAN REVIEW

## Objective

Implement the mandatory human review decision process.

The reviewer must be able to:

```text
Accept
Edit
Reject
```

---

## Files to create

```text
core/
    review.py

tests/
    test_review.py
```

---

## Files to modify

```text
models/review.py
```

---

## Dependencies

M6 and M7.

---

## Input/output contract

### Input

```json
{
  "ai_diagnosis": {},
  "python_findings": [],
  "comparison": {}
}
```

### Output

```json
{
  "decision": "accepted|edited|rejected",
  "final_diagnosis": {},
  "review_comment": "..."
}
```

---

## Implementation requirements

### Accept

Final diagnosis equals AI diagnosis.

### Edit

Final diagnosis differs from AI diagnosis.

Both versions must remain available.

### Reject

AI diagnosis is rejected.

A rejection must be recorded.

Human review must be mandatory before final diagnosis status becomes accepted.

---

## Tests required

Test:

- Accept
- Edit
- Reject
- Edit preserves original AI diagnosis
- Reject preserves original AI diagnosis
- Invalid review decision
- Missing final diagnosis for edit

---

## Acceptance criteria

- [ ] Accept works.
- [ ] Edit works.
- [ ] Reject works.
- [ ] Original AI diagnosis is preserved.
- [ ] Human final diagnosis is preserved.
- [ ] Review cannot be skipped in the final workflow.

---

## What must NOT be implemented yet

Do NOT implement:

- Review database/file persistence
- Dashboard
- Final Streamlit UI

---

# M9 — REVIEW LOGGING

## Objective

Persist case analysis and human-review history.

---

## Files to create

```text
core/
    review_logger.py

data/
    reviews.json

tests/
    test_review_logger.py
```

---

## Files to modify

```text
models/review.py
```

Only if required.

---

## Dependencies

M8.

---

## Input/output contract

### Input

```text
Case
+
AI diagnosis
+
Python findings
+
Comparison
+
Human review
+
Verification
```

### Output

Persisted review record.

---

## Review record must include

```text
review_id
case_id
AI diagnosis
Python findings
comparison status
human decision
human final diagnosis
review comment
verification status
timestamp
```

---

## Implementation requirements

The logger must:

- Generate unique review IDs.
- Preserve original AI output.
- Preserve human correction.
- Preserve comparison result.
- Persist review data.
- Load existing reviews.
- Avoid silently overwriting existing records.

---

## Tests required

Test:

- Create review
- Save review
- Load review
- Multiple reviews
- Edited review
- Rejected review
- Corrupted JSON handling

---

## Acceptance criteria

- [ ] Review records persist.
- [ ] Original AI diagnosis remains available.
- [ ] Human correction remains available.
- [ ] Review data can be loaded.
- [ ] At least five review records can represent human corrections.
- [ ] Tests pass.

---

## What must NOT be implemented yet

Do NOT implement:

- Dashboard
- Full Streamlit UI
- Automatic evaluation
- Packet Tracer automation

---

# M10 — STREAMLIT INTERFACE

## Objective

Build the user interface for the complete troubleshooting workflow.

The UI must connect already-tested backend components.

Do not place networking/business logic inside Streamlit components.

---

## Files to create

```text
ui/
    input_view.py
    diagnosis_view.py
    review_view.py
    verification_view.py
```

---

## Files to modify

```text
app.py
```

---

## Dependencies

M2 through M9.

---

## Input/output contract

### User input

```text
Symptom
Topology notes
Show-command output
```

### UI output

Display:

```text
AI diagnosis
Python findings
Comparison
Human review
Verification
```

---

## Implementation requirements

The workflow must be:

```text
Input
↓
Validation
↓
Python rules
↓
AI
↓
AI validation
↓
Comparison
↓
Human review
↓
Verification
↓
Logging
```

The user must clearly see the evidence used by the system.

---

## Required UI sections

### 1. Case input

Fields:

- Symptom
- Topology notes
- Show-command output

### 2. Analysis

Display:

- Root cause
- Issue type
- OSI layer
- Confidence
- Severity
- Evidence
- Next command
- Fix steps
- Uncertainties

### 3. Python findings

Display deterministic findings separately.

### 4. Comparison

Display comparison status.

### 5. Human review

Controls:

```text
Accept
Edit
Reject
```

### 6. Verification

Allow verification status to be recorded.

---

## Tests required

Test backend/UI integration where practical.

At minimum verify:

- Inputs reach backend.
- AI result displays.
- Python findings display.
- Comparison displays.
- Review decision is recorded.
- Verification is recorded.

---

## Acceptance criteria

- [ ] User can submit a troubleshooting case.
- [ ] AI analysis appears.
- [ ] Python findings appear.
- [ ] Comparison appears.
- [ ] Human review is visible.
- [ ] Accept/Edit/Reject works.
- [ ] Verification can be recorded.
- [ ] Review is persisted.

---

## What must NOT be implemented yet

Do NOT implement:

- Dashboard
- Advanced analytics
- User authentication
- Packet Tracer automation
- Mobile interface

---

# M11 — DASHBOARD

## Objective

Create the required dashboard using stored case/review data.

---

## Files to create

```text
ui/
    dashboard_view.py

tests/
    test_dashboard_data.py
```

---

## Files to modify

```text
app.py
core/review_logger.py
```

Only if required.

---

## Dependencies

M9 and M10.

---

## Input/output contract

### Input

Stored cases and review records.

### Output

Dashboard metrics.

Required:

```text
Issue types
Severity
AI vs human agreement
```

---

## Implementation requirements

### Issue type summary

Calculate counts from actual data.

### Severity summary

Calculate counts from actual data.

### AI vs human agreement

At minimum distinguish:

```text
Accepted
Edited
Rejected
```

The dashboard must derive statistics dynamically.

---

## Tests required

Test metric calculations using controlled review data.

Example:

```text
5 accepted
3 edited
2 rejected
```

Expected:

```text
accepted = 5
edited = 3
rejected = 2
```

---

## Acceptance criteria

- [ ] Dashboard shows issue types.
- [ ] Dashboard shows severity.
- [ ] Dashboard shows AI/human agreement.
- [ ] Values come from stored data.
- [ ] No hardcoded percentages.
- [ ] Dashboard handles empty data safely.

---

## What must NOT be implemented yet

Do NOT implement:

- Predictive analytics
- Network monitoring
- Advanced ML metrics
- User accounts
- Real-time Packet Tracer integration

---

# M12 — END-TO-END INTEGRATION

## Objective

Connect the complete system into the required demonstration flow.

---

## Files to create

```text
tests/
    test_end_to_end.py

docs/
    DEMO.md
```

---

## Files to modify

Potentially:

```text
app.py
core/*
ai/*
ui/*
```

Only for integration defects.

---

## Dependencies

M0–M11.

---

## Required flow

```text
Broken Packet Tracer lab
        ↓
Symptom
        ↓
Packet Tracer evidence
        ↓
AI analysis
        ↓
Python check
        ↓
AI/Python comparison
        ↓
Human review
        ↓
Fix
        ↓
Verification
        ↓
Review logging
```

---

## Implementation requirements

Create at least one complete demonstration case.

The demonstration must show:

1. Original broken state.
2. Symptom.
3. Topology.
4. Show-command evidence.
5. Python finding.
6. AI diagnosis.
7. Comparison.
8. Human decision.
9. Fix in Packet Tracer.
10. Verification evidence.
11. Final result.

---

## Tests required

End-to-end test should verify the backend pipeline:

```text
Case
→ Python
→ AI mock
→ validation
→ comparison
→ review
→ logging
```

Do not require a live OpenAI API for automated tests.

---

## Acceptance criteria

- [ ] Full workflow executes.
- [ ] Human review cannot be bypassed.
- [ ] Final result is logged.
- [ ] Verification is recorded.
- [ ] At least one Packet Tracer demonstration is documented.
- [ ] Automated integration test passes.

---

## What must NOT be implemented yet

Do NOT implement:

- New features
- Major architecture changes
- Real-time monitoring
- Automatic Packet Tracer control
- Complex deployment infrastructure

---

# M13 — EVALUATION ON 30+ CASES

## Objective

Evaluate the system against the complete troubleshooting dataset.

This milestone measures actual behavior rather than merely proving that the software runs.

---

## Files to create

```text
evaluation/
    evaluate_cases.py
    results.json
    README.md

tests/
    test_evaluation.py
```

---

## Files to modify

None unless evaluation exposes defects.

---

## Dependencies

M12.

---

## Input/output contract

### Input

At least 30 cases.

### Output

Evaluation results containing:

```text
case_id
expected issue
AI issue
Python findings
comparison
human decision
verification
```

---

## Implementation requirements

Evaluate all cases.

Do not modify expected answers simply to make the system look better.

Record mismatches honestly.

The evaluation must identify:

```text
AI correct
AI incorrect
Python correct
Python incorrect
AI/Python agreement
AI/Python disagreement
human correction
```

---

## Required human-correction evidence

At least five cases must document genuine human correction.

These cases must retain:

```text
original AI diagnosis
human correction
reason
```

---

## Tests required

Verify:

- At least 30 cases are evaluated.
- All required categories exist.
- Results are generated for every case.
- No case silently disappears.

---

## Acceptance criteria

- [ ] 30+ cases evaluated.
- [ ] All eight required categories represented.
- [ ] Evaluation results saved.
- [ ] Human corrections documented.
- [ ] Mismatches are visible.
- [ ] No evaluation result is manually fabricated.

---

## What must NOT be implemented yet

Do NOT implement:

- Model fine-tuning
- Automatic model retraining
- Additional AI agents
- Advanced statistical analytics

---

# M14 — RESPONSIBLE AI ANALYSIS

## Objective

Document the limitations, risks, human oversight, and reliability boundaries of NetSage AI.

This is an analysis/documentation milestone, not a feature-development milestone.

---

## Files to create

```text
docs/
    RESPONSIBLE_AI.md
```

---

## Files to modify

```text
README.md
```

Only if links to responsible AI documentation are required.

---

## Dependencies

M13.

---

## Required topics

Document:

### 1. AI hallucination

Examples:

- Invented evidence
- Incorrect diagnosis
- Incorrect command
- Incorrect topology interpretation

### 2. Human oversight

Explain why human review is mandatory.

### 3. Deterministic validation

Explain why Python is used for mechanically verifiable networking conditions.

### 4. Packet Tracer as evidence

Explain that actual Packet Tracer output has priority over AI assumptions.

### 5. Uncertainty

Explain why the AI must identify insufficient evidence.

### 6. Limitations

Document that NetSage AI is a troubleshooting helper, not an autonomous network administrator.

---

## Tests required

No major automated tests required.

Review documentation against actual architecture.

---

## Acceptance criteria

- [ ] AI limitations documented.
- [ ] Human review documented.
- [ ] Deterministic rules documented.
- [ ] Evidence hierarchy documented.
- [ ] Hallucination risks documented.
- [ ] System boundaries documented.
- [ ] No unsupported claims about AI accuracy.

---

## What must NOT be implemented yet

Do NOT add:

- New AI safety systems not required by the project.
- Automatic remediation.
- Autonomous network configuration.
- Additional AI agents.

---

# M15 — FINAL TESTING

## Objective

Perform final technical validation of the complete NetSage AI project.

No major new features should be introduced during this milestone.

---

## Files to create

```text
docs/
    FINAL_TEST_REPORT.md
```

---

## Files to modify

Only if final testing identifies genuine defects.

---

## Dependencies

M0–M14.

---

# Final test categories

## 1. Unit tests

Run:

```text
pytest
```

All tests must pass.

---

## 2. Rule engine tests

Verify all six rules:

```text
duplicate IP
wrong subnet mask
gateway mismatch
interface down
missing VLAN
missing route
```

---

## 3. AI schema tests

Verify malformed AI output cannot reach the diagnosis display.

---

## 4. Comparison tests

Verify:

```text
AGREEMENT
PARTIAL_AGREEMENT
AI_ONLY
PYTHON_ONLY
CONFLICT
NO_DETERMINISTIC_RESULT
```

---

## 5. Human review tests

Verify:

```text
Accept
Edit
Reject
```

---

## 6. Logging tests

Verify review records persist correctly.

---

## 7. Dataset tests

Verify:

```text
30+ cases
8 issue categories
```

---

## 8. Dashboard tests

Verify:

```text
issue types
severity
AI/human agreement
```

---

## 9. Security tests

Verify:

- No API keys in repository.
- `.env` is ignored.
- No user input is executed.
- No secrets appear in logs.

---

## 10. End-to-end demonstration

Perform the complete flow:

```text
Broken lab
↓
Symptom
↓
Evidence
↓
AI
↓
Python
↓
Comparison
↓
Human review
↓
Fix
↓
Verification
```

---

# FINAL ACCEPTANCE CRITERIA

The project is complete only if:

- [ ] All M0–M15 milestones are completed.
- [ ] Full automated test suite passes.
- [ ] At least 30 cases exist.
- [ ] All required issue categories are covered.
- [ ] All six deterministic rules work.
- [ ] AI output is structured and validated.
- [ ] AI and Python results are compared.
- [ ] Human review is mandatory.
- [ ] Accept/Edit/Reject works.
- [ ] At least five human corrections are documented.
- [ ] Review logs persist.
- [ ] Dashboard works.
- [ ] Packet Tracer demonstration works.
- [ ] Verification is documented.
- [ ] Responsible AI limitations are documented.
- [ ] No secrets are committed.
- [ ] README explains how to run the project.

---

# FINAL DEFINITION OF DONE

NetSage AI is ready for submission only when a reviewer can start from a broken Packet Tracer lab and follow this complete chain without manual intervention inside the software:

```text
BROKEN LAB
   ↓
SYMPTOM
   ↓
TOPOLOGY + SHOW OUTPUT
   ↓
PYTHON DETERMINISTIC CHECK
   ↓
AI DIAGNOSIS
   ↓
STRUCTURED VALIDATION
   ↓
AI/PYTHON COMPARISON
   ↓
MANDATORY HUMAN REVIEW
   ↓
ACCEPT / EDIT / REJECT
   ↓
FIX IN PACKET TRACER
   ↓
VERIFICATION
   ↓
LOGGED RESULT
   ↓
DASHBOARD
```

The system must demonstrate that:

> **AI assists diagnosis, deterministic Python validates what can be mechanically verified, Packet Tracer provides the networking evidence, and a human remains responsible for the final diagnosis.**

Do not claim that the AI is always correct.

Do not claim that Python can detect every networking problem.

Do not claim that absence of a Python finding proves that the network is healthy.

The project's strength is the combination of the three evidence sources:

```text
Packet Tracer evidence
        +
Deterministic Python
        +
AI reasoning
        +
Human review
```

not AI alone.