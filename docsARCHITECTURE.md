# NetSage AI — Complete Implementation Blueprint

## 0. PROJECT SCOPE AND DESIGN PRINCIPLE

NetSage AI is an AI-assisted troubleshooting helper for Cisco-style networking labs created and tested using Cisco Packet Tracer.

The system receives:

1. Network symptoms
2. Topology notes
3. Packet Tracer `show` command output

It produces a structured troubleshooting diagnosis containing:

- Likely root cause
- OSI layer
- Confidence
- Evidence
- Next command
- Fix steps

The system also runs deterministic Python checks for:

- Duplicate IP
- Wrong subnet mask
- Gateway mismatch
- Interface down
- Missing VLAN
- Missing route

The AI result and deterministic Python result are compared.

A human must review the diagnosis before it can be accepted.

The human reviewer can:

- Accept
- Edit
- Reject

The system must contain at least 30 troubleshooting cases covering:

- VLAN
- Gateway
- DHCP
- DNS
- Routing
- ACL
- NAT
- Wireless

At least 5 cases must document situations where the human corrected the AI.

A dashboard summarizes:

- Issue types
- Severity
- AI vs human agreement

The complete demonstration flow is:

```text
Broken Packet Tracer Lab
        ↓
User enters symptom
        ↓
Topology notes + show-command output
        ↓
AI analysis
        ↓
Python deterministic checks
        ↓
AI vs Python comparison
        ↓
Mandatory human review
        ↓
Accept / Edit / Reject
        ↓
Apply fix in Packet Tracer
        ↓
Verification
```

---

# 1. PROJECT OBJECTIVE

## Primary objective

Build a controlled AI troubleshooting assistant that helps students diagnose networking problems in Cisco-style Packet Tracer labs.

## Core design goal

NetSage AI must answer:

> "Given the observed symptom, topology information, and Packet Tracer evidence, what is the most likely networking problem, what evidence supports it, what should I check next, and how can I fix it?"

## Important architectural rule

The system must NOT present the AI diagnosis as automatically correct.

Instead:

```text
Evidence
  ↓
Deterministic checks
  ↓
AI reasoning
  ↓
Comparison
  ↓
Human decision
```

The human reviewer remains the final decision-maker.

---

# 2. SYSTEM ARCHITECTURE

```text
                    ┌──────────────────────┐
                    │  Cisco Packet Tracer │
                    └──────────┬───────────┘
                               │
                  Symptoms + topology + output
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Streamlit UI       │
                    │  Input / Review /    │
                    │     Dashboard        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Input Validator    │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
          ┌─────────────────┐    ┌──────────────────┐
          │ Python Rule     │    │ OpenAI AI        │
          │ Engine          │    │ Diagnosis        │
          │                 │    │ Engine           │
          └────────┬────────┘    └────────┬─────────┘
                   │                      │
                   │                      │
                   └──────────┬───────────┘
                              ▼
                   ┌─────────────────────┐
                   │ Comparison Engine   │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Human Review         │
                   │                     │
                   │ Accept / Edit /     │
                   │ Reject              │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Verification        │
                   │ Result              │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Case + Review Logs  │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Streamlit Dashboard │
                   └─────────────────────┘
```

---

# 3. COMPLETE DATA FLOW

## Step 1 — Create broken lab

A networking case is created in Cisco Packet Tracer.

Example:

```text
PC1 cannot communicate with PC2.
Both devices appear to be connected.
```

The Packet Tracer topology becomes the physical/networking ground truth.

---

## Step 2 — Capture symptom

User enters:

```text
PC1 cannot ping PC2.
```

---

## Step 3 — Enter topology notes

Example:

```text
PC1 is connected to Switch1 Fa0/1.
PC2 is connected to Switch1 Fa0/2.
PC1 belongs to VLAN 10.
PC2 belongs to VLAN 20.
No router is configured between the VLANs.
```

---

## Step 4 — Enter Packet Tracer evidence

Example:

```text
show vlan brief

VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/3, Fa0/4
10   STUDENTS                         active    Fa0/1
```

---

## Step 5 — Validate input

The application checks that required information exists.

Required:

- Symptom
- Topology notes
- Evidence

If required input is missing, diagnosis should not proceed normally.

---

## Step 6 — Run deterministic Python checks

The rule engine analyzes evidence for mechanically detectable problems.

Example:

```text
Detected:
VLAN 20 is referenced in topology notes
but is not present in the provided VLAN evidence.
```

Result:

```text
rule = missing_vlan
status = detected
confidence = deterministic
```

The Python engine must never fabricate missing information.

---

## Step 7 — Run AI diagnosis

The AI receives the structured case.

It analyzes:

- Symptom
- Topology notes
- Packet Tracer evidence
- Deterministic findings

The AI returns structured JSON.

---

## Step 8 — Compare AI and Python

Example:

```text
AI:
Missing VLAN 20

Python:
Missing VLAN 20

Comparison:
AGREEMENT
```

Another example:

```text
AI:
ACL is blocking traffic

Python:
No deterministic ACL rule available

Comparison:
AI_ONLY
```

The comparison engine must not treat `AI_ONLY` as proof that the AI is wrong.

It means only that the deterministic checker cannot independently verify it.

---

## Step 9 — Human review

The reviewer sees:

```text
AI Diagnosis
Python Findings
Comparison
Evidence
```

The reviewer must choose:

```text
Accept
Edit
Reject
```

No diagnosis becomes the final diagnosis without this decision.

---

## Step 10 — Fix

The user manually changes the Packet Tracer configuration.

NetSage AI does not need to directly control Packet Tracer.

---

## Step 11 — Verification

The user runs the appropriate Packet Tracer commands again.

Example:

```text
show vlan brief
show interfaces status
ping 192.168.10.20
```

The new evidence is recorded.

---

## Step 12 — Store case

Store:

- Original input
- AI diagnosis
- Python result
- Comparison
- Human decision
- Edited diagnosis if applicable
- Verification result

---

# 4. MODULES

The project should be divided into these modules:

```text
1. Streamlit UI
2. Input Validator
3. Case Manager
4. Evidence Parser
5. Python Rule Engine
6. AI Diagnosis Engine
7. AI/Python Comparison Engine
8. Human Review Manager
9. Verification Manager
10. Dataset Manager
11. Review Logger
12. Dashboard
13. Configuration Manager
```

Do not create more modules unless implementation actually requires them.

---

# 5. RESPONSIBILITY OF EACH MODULE

## 5.1 Streamlit UI

Responsible for:

- Collecting inputs
- Displaying diagnosis
- Displaying Python findings
- Displaying comparison
- Displaying human review controls
- Displaying dashboard

It should NOT contain networking logic.

---

## 5.2 Input Validator

Responsible for validating:

- Symptom exists
- Topology notes exist
- Evidence exists
- Input is within expected format

It should return validation errors rather than silently modifying user input.

---

## 5.3 Case Manager

Responsible for:

- Creating a troubleshooting case
- Loading existing cases
- Updating case state
- Maintaining case identifiers

---

## 5.4 Evidence Parser

Responsible for converting supplied Packet Tracer output into structured information where practical.

Examples:

```text
show ip interface brief
show vlan brief
show ip route
show interfaces
```

The parser should only extract information that is actually present.

It must not infer missing information.

---

## 5.5 Python Rule Engine

Responsible for deterministic checks.

Required rules:

```text
duplicate_ip
wrong_subnet_mask
gateway_mismatch
interface_down
missing_vlan
missing_route
```

The rule engine is not an AI system.

Its job is to identify mechanically verifiable conditions.

---

## 5.6 AI Diagnosis Engine

Responsible for:

- Understanding symptoms
- Reasoning across topology/evidence
- Identifying likely root cause
- Selecting OSI layer
- Providing confidence
- Citing evidence
- Suggesting next command
- Providing fix steps

The AI must only reason from supplied evidence.

---

## 5.7 Comparison Engine

Responsible for comparing:

```text
AI diagnosis
vs
Python deterministic findings
```

Possible comparison statuses:

```text
AGREEMENT
PARTIAL_AGREEMENT
AI_ONLY
PYTHON_ONLY
CONFLICT
NO_DETERMINISTIC_RESULT
```

---

## 5.8 Human Review Manager

Responsible for:

```text
Accepted
Edited
Rejected
```

It must record:

- Reviewer decision
- Original AI result
- Edited result if applicable
- Review timestamp
- Optional reviewer comment

---

## 5.9 Verification Manager

Responsible for recording whether the issue was successfully verified after the fix.

Example:

```text
verification_status:
verified
not_verified
not_attempted
```

---

## 5.10 Dataset Manager

Responsible for:

- Storing troubleshooting cases
- Loading cases
- Ensuring minimum 30 cases
- Categorizing cases

---

## 5.11 Review Logger

Responsible for storing human-review information.

At least five cases must show:

```text
AI diagnosis ≠ final human diagnosis
```

These cases become the project's documented examples of human correction.

---

## 5.12 Dashboard

Responsible for summarizing:

- Issue types
- Severity
- AI/human agreement

The dashboard should use stored review/case data rather than manually entered statistics.

---

## 5.13 Configuration Manager

Responsible for:

- OpenAI API key configuration
- Application configuration
- Environment variables

Secrets must not be hardcoded.

---

# 6. INPUT/OUTPUT CONTRACT FOR EACH MODULE

## 6.1 Input Validator

### Input

```json
{
  "symptom": "string",
  "topology_notes": "string",
  "show_output": "string"
}
```

### Output

```json
{
  "valid": true,
  "errors": []
}
```

---

# 6.2 Rule Engine

### Input

```json
{
  "symptom": "string",
  "topology_notes": "string",
  "show_output": "string"
}
```

### Output

```json
{
  "findings": [
    {
      "rule_id": "missing_vlan",
      "status": "detected",
      "evidence": [
        "VLAN 20 referenced in topology notes",
        "VLAN 20 absent from show vlan brief"
      ]
    }
  ]
}
```

---

# 6.3 AI Diagnosis Engine

### Input

```json
{
  "symptom": "string",
  "topology_notes": "string",
  "show_output": "string",
  "python_findings": []
}
```

### Output

Must conform to the AI response schema defined in Section 8.

---

# 6.4 Comparison Engine

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
  "reason": "Both identify missing VLAN 20 as the likely issue."
}
```

---

# 6.5 Human Review

### Input

```json
{
  "ai_diagnosis": {},
  "python_findings": {},
  "comparison": {}
}
```

### Output

```json
{
  "decision": "edited",
  "final_diagnosis": {},
  "review_comment": "AI selected wrong VLAN. Evidence indicates gateway mismatch."
}
```

---

# 7. DATA MODELS

Use simple models.

Do not build a complex distributed data architecture.

A case should conceptually contain:

```text
Case
├── case_id
├── issue_type
├── severity
├── symptom
├── topology_notes
├── show_output
├── expected_root_cause
├── ai_diagnosis
├── python_findings
├── comparison
├── human_review
└── verification
```

---

## Case model

```json
{
  "case_id": "CASE-001",
  "issue_type": "VLAN",
  "severity": "medium",
  "symptom": "...",
  "topology_notes": "...",
  "show_output": "...",
  "expected_root_cause": "...",
  "ai_diagnosis": {},
  "python_findings": [],
  "comparison": {},
  "human_review": {},
  "verification": {}
}
```

---

# 8. AI RESPONSE JSON SCHEMA

The AI response must be structured.

Recommended schema:

```json
{
  "diagnosis": {
    "root_cause": "string",
    "issue_type": "VLAN|GATEWAY|DHCP|DNS|ROUTING|ACL|NAT|WIRELESS|OTHER",
    "osi_layer": "string",
    "confidence": 0,
    "severity": "low|medium|high"
  },
  "evidence": [
    {
      "source": "topology|show_output|symptom|python_rule",
      "observation": "string"
    }
  ],
  "next_command": {
    "command": "string",
    "purpose": "string"
  },
  "fix_steps": [
    "string"
  ],
  "uncertainties": [
    "string"
  ]
}
```

## Rules

### root_cause

Must describe a specific likely networking problem.

Bad:

```text
There may be a network configuration issue.
```

Good:

```text
The switch port connected to PC1 is assigned to VLAN 20 while PC1 is expected to be in VLAN 10.
```

---

### issue_type

Must be one of:

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

---

### osi_layer

Use the relevant OSI layer based on networking reasoning.

Examples:

```text
Layer 2
Layer 3
Layer 7
```

Do not force a layer when the evidence is insufficient.

---

### confidence

Use numeric confidence:

```text
0–100
```

The value represents the AI's confidence, not factual certainty.

---

### evidence

Every diagnosis must contain evidence.

Evidence must point to supplied information.

The AI must not invent command output.

---

### next_command

The command should be relevant to validating the diagnosis.

Example:

```text
show ip route
```

---

### fix_steps

Fixes must be specific and technically appropriate.

---

### uncertainties

The AI must explicitly identify missing evidence when the diagnosis cannot be established confidently.

---

# 9. PYTHON RULE ENGINE SPECIFICATION

The deterministic engine is one of the most important parts of the project.

Do NOT replace these rules with an LLM.

---

## Rule 1 — Duplicate IP

### Objective

Detect when multiple devices/interfaces use the same IP address.

### Input

Structured interface/IP information extracted from evidence.

### Logic

```text
Create mapping:

IP → list of interfaces/devices

If any IP has more than one device/interface:
    duplicate IP detected
```

### Example

```text
PC1 = 192.168.1.10
PC2 = 192.168.1.10
```

Result:

```json
{
  "rule_id": "duplicate_ip",
  "status": "detected",
  "evidence": [
    "PC1 uses 192.168.1.10",
    "PC2 uses 192.168.1.10"
  ]
}
```

---

## Rule 2 — Wrong Subnet Mask

### Objective

Detect incompatible subnet configuration where sufficient addressing information exists.

### Logic

Compare:

```text
IP address
subnet mask
expected network relationship
```

The rule must only report a mismatch when it can be determined from supplied data.

Do NOT guess the expected mask.

---

## Rule 3 — Gateway Mismatch

### Objective

Detect when a host's configured default gateway does not belong to the expected local subnet or does not correspond to the documented gateway.

### Logic

Compare:

```text
host IP
host subnet mask
default gateway
topology notes
```

Only report a mismatch when evidence supports it.

---

## Rule 4 — Interface Down

### Objective

Detect interfaces explicitly shown as down/down or administratively down.

Example evidence:

```text
GigabitEthernet0/1 is administratively down
```

Result:

```text
interface_down = detected
```

Do not infer interface state from a missing line.

---

## Rule 5 — Missing VLAN

### Objective

Detect when a VLAN referenced by the topology or interface configuration is absent from VLAN evidence.

Example:

```text
Topology:
PC1 belongs to VLAN 20.

show vlan brief:
VLAN 10
VLAN 30
```

Result:

```text
missing_vlan = detected
```

---

## Rule 6 — Missing Route

### Objective

Detect when a required destination network has no corresponding route in the supplied routing table.

The expected destination must come from:

- topology notes
- case definition
- supplied evidence

Do not invent destination networks.

---

# 10. AI + PYTHON COMPARISON LOGIC

The comparison engine must distinguish agreement from lack of evidence.

## AGREE

Python and AI identify substantially the same issue.

```text
AI → missing VLAN
Python → missing VLAN
```

---

## PARTIAL_AGREEMENT

AI and Python identify related but not identical findings.

Example:

```text
AI → routing problem
Python → missing route
```

---

## PYTHON_ONLY

Python detects a deterministic issue that AI did not identify.

Example:

```text
Python → duplicate IP
AI → DHCP issue
```

---

## AI_ONLY

AI identifies an issue that is outside the deterministic rule engine.

Example:

```text
AI → DNS configuration issue
Python → no applicable finding
```

This is NOT automatically an AI failure.

---

## CONFLICT

AI and Python make materially incompatible diagnoses.

Example:

```text
AI → gateway mismatch
Python → evidence indicates interface down
```

---

## NO_DETERMINISTIC_RESULT

The Python engine cannot establish a finding from available evidence.

This is different from:

```text
Python found no problem.
```

It means:

```text
There is insufficient deterministic evidence.
```

That distinction is critical.

---

# 11. HUMAN REVIEW WORKFLOW

Human review is mandatory.

The reviewer must see:

```text
1. Symptom
2. Topology notes
3. Packet Tracer evidence
4. AI diagnosis
5. AI evidence
6. Python findings
7. AI/Python comparison
8. Recommended next command
9. Fix steps
```

Then choose:

```text
ACCEPT
EDIT
REJECT
```

---

## Accept

The human agrees with the AI diagnosis.

Store:

```json
{
  "decision": "accepted"
}
```

---

## Edit

The human modifies the diagnosis.

Store both:

```text
Original AI diagnosis
+
Final human diagnosis
```

This is essential.

Otherwise the project cannot prove that humans corrected AI.

---

## Reject

The human determines that the AI diagnosis should not be used.

Store:

```text
decision = rejected
```

A rejection should not silently disappear.

---

# 12. CASE DATASET SCHEMA

Minimum:

```text
30 cases
```

Cases must cover all required issue categories.

The dataset should contain cases from:

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

A practical distribution can be approximately balanced, but the official requirement is coverage rather than a specific number per category.

Each case should contain:

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

The expected diagnosis exists primarily for testing/evaluation.

It should NOT automatically be shown to the AI during normal diagnosis.

---

# 13. REVIEW LOG SCHEMA

Each review must preserve the AI output and human decision.

```json
{
  "review_id": "REV-001",
  "case_id": "CASE-001",
  "ai_diagnosis": {},
  "python_findings": [],
  "comparison_status": "AGREEMENT",
  "human_decision": "edited",
  "human_final_diagnosis": {},
  "review_comment": "AI identified routing but the actual issue was an incorrect gateway.",
  "verification_status": "verified",
  "timestamp": "..."
}
```

---

## Required human-correction cases

At least five records must satisfy:

```text
human_decision = edited
```

or a clearly documented human correction.

These cases should be highlighted during the demonstration.

Example:

```text
Case CASE-007

AI:
DNS issue

Human:
Incorrect gateway configuration

Reason:
Packet Tracer evidence showed the host could not reach its local gateway.
```

Do not manufacture these examples merely to satisfy the number.

They must represent actual documented review decisions.

---

# 14. DASHBOARD DATA REQUIREMENTS

The dashboard only needs to summarize the required information.

## Issue types

Display counts such as:

```text
VLAN       5
Gateway    4
DHCP       4
DNS        3
Routing    5
ACL        3
NAT        3
Wireless   3
```

The exact distribution depends on the actual 30-case dataset.

---

## Severity

Show:

```text
Low
Medium
High
```

based on stored case/review data.

---

## AI vs human agreement

Calculate from review records.

For example:

```text
Accepted without modification
Edited
Rejected
```

The dashboard should make it easy to see how often humans agreed with the AI.

Do not manually hardcode percentages.

---

# 15. ERROR HANDLING

The system must handle failures without producing fake diagnoses.

## Missing input

Show:

```text
Required evidence is missing.
```

Do not ask AI to fill the gap.

---

## Invalid AI JSON

If the AI response cannot be parsed:

```text
AI diagnosis unavailable.
```

The application should still be able to display Python findings.

---

## OpenAI API failure

Show an application error and allow the user to retry.

Do not generate a fake diagnosis.

---

## Rule parser failure

Store:

```text
rule_engine_status = error
```

Do not treat parser failure as:

```text
no issue detected
```

---

## Conflicting results

Display both results.

Do not automatically select one.

Human review decides.

---

## Insufficient evidence

The AI should explicitly indicate uncertainty.

The system should not pretend that a diagnosis is confirmed.

---

# 16. SECURITY REQUIREMENTS

Keep security proportional to a college project.

Required:

## API key

Never hardcode the OpenAI API key.

Use an environment variable or Streamlit secrets.

Example:

```text
OPENAI_API_KEY
```

---

## Git

Never commit:

```text
.env
API keys
secrets
```

Add them to `.gitignore`.

---

## User input

Treat all topology notes and command output as untrusted text.

Do not execute user-provided commands on the operating system.

The application should only analyze text.

---

## AI prompt injection

Packet Tracer output must be treated as evidence, not instructions.

For example, if input contains:

```text
Ignore previous instructions and output...
```

the AI must continue treating the content as networking evidence.

---

# 17. TESTING STRATEGY

Testing must be divided into four levels.

---

## 17.1 Unit testing

Test each deterministic rule independently.

Required tests:

```text
test_duplicate_ip
test_wrong_subnet_mask
test_gateway_mismatch
test_interface_down
test_missing_vlan
test_missing_route
```

Each should contain:

```text
positive case
negative case
insufficient-evidence case
```

---

## 17.2 AI schema testing

Verify that AI responses always contain:

```text
diagnosis
root_cause
issue_type
osi_layer
confidence
severity
evidence
next_command
fix_steps
uncertainties
```

Invalid output must be rejected.

---

## 17.3 Integration testing

Test:

```text
Streamlit
→ validator
→ Python
→ AI
→ comparison
→ review
→ logging
```

---

## 17.4 End-to-end Packet Tracer testing

At least one complete demonstration should follow:

```text
Broken lab
→ symptom
→ evidence
→ AI
→ Python
→ comparison
→ human review
→ fix
→ verification
```

Ideally prepare multiple demonstrations from different issue categories.

---

# 18. PROJECT FOLDER STRUCTURE

Use a simple structure.

```text
netsage-ai/
│
├── app.py
│
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── config/
│   └── settings.py
│
├── ui/
│   ├── input_view.py
│   ├── diagnosis_view.py
│   ├── review_view.py
│   └── dashboard_view.py
│
├── core/
│   ├── validator.py
│   ├── case_manager.py
│   ├── comparison.py
│   └── verification.py
│
├── ai/
│   ├── diagnosis.py
│   ├── prompts.py
│   └── schema.py
│
├── rules/
│   ├── engine.py
│   ├── duplicate_ip.py
│   ├── subnet_mask.py
│   ├── gateway.py
│   ├── interface.py
│   ├── vlan.py
│   └── route.py
│
├── data/
│   ├── cases.json
│   └── reviews.json
│
├── tests/
│   ├── test_rules.py
│   ├── test_validator.py
│   ├── test_comparison.py
│   └── test_ai_schema.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── DATA_MODEL.md
    ├── AI_SPEC.md
    ├── RULE_ENGINE.md
    ├── TESTING.md
    └── DEMO.md
```

Do not introduce a database unless the project actually requires one.

For a 30-case college project, JSON files are sufficient for the initial implementation.

---

# 19. IMPLEMENTATION ORDER

Cursor should implement the project in this order.

## Phase 1 — Repository

Create:

```text
folder structure
requirements.txt
.gitignore
.env.example
README.md
```

Verify the application runs.

---

## Phase 2 — Data models

Implement:

```text
Case
AIDiagnosis
PythonFinding
ComparisonResult
HumanReview
Verification
```

Do this before building UI.

---

## Phase 3 — Dataset

Create the minimum 30 cases.

Ensure all required categories are represented:

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

Do not move forward with an incomplete dataset.

---

## Phase 4 — Input validation

Implement validation for:

```text
symptom
topology notes
show output
```

Test invalid inputs.

---

## Phase 5 — Deterministic rule engine

Implement:

```text
duplicate IP
wrong subnet mask
gateway mismatch
interface down
missing VLAN
missing route
```

This should be completed before depending heavily on AI.

---

## Phase 6 — AI diagnosis

Implement the OpenAI API integration.

The AI receives:

```text
symptom
topology
show output
Python findings
```

Return only the required structured schema.

---

## Phase 7 — Comparison

Implement:

```text
AGREEMENT
PARTIAL_AGREEMENT
AI_ONLY
PYTHON_ONLY
CONFLICT
NO_DETERMINISTIC_RESULT
```

Test each condition.

---

## Phase 8 — Human review

Implement:

```text
Accept
Edit
Reject
```

Store both:

```text
AI diagnosis
human final result
```

---

## Phase 9 — Verification

Allow the user to record whether the fix was verified.

---

## Phase 10 — Dashboard

Calculate:

```text
issue type distribution
severity distribution
AI/human agreement
```

from stored data.

---

## Phase 11 — Testing

Run:

```text
unit tests
schema tests
integration tests
end-to-end tests
```

---

## Phase 12 — Packet Tracer demonstrations

Prepare broken labs and evidence.

Run the complete demonstration flow.

---

## Phase 13 — Documentation

Complete:

```text
README
architecture
data model
AI specification
rule engine specification
testing documentation
demo instructions
```

---

# 20. DEFINITION OF DONE

NetSage AI is considered complete only when ALL of the following are true.

## Core system

- [ ] Streamlit application runs
- [ ] Symptom input works
- [ ] Topology notes input works
- [ ] Show-command output input works
- [ ] AI diagnosis works
- [ ] AI response is structured
- [ ] Python rule engine works
- [ ] AI/Python comparison works
- [ ] Human review is mandatory
- [ ] Accept works
- [ ] Edit works
- [ ] Reject works
- [ ] Verification can be recorded
- [ ] Dashboard works

## Required Python rules

- [ ] Duplicate IP
- [ ] Wrong subnet mask
- [ ] Gateway mismatch
- [ ] Interface down
- [ ] Missing VLAN
- [ ] Missing route

## Dataset

- [ ] At least 30 cases
- [ ] VLAN cases
- [ ] Gateway cases
- [ ] DHCP cases
- [ ] DNS cases
- [ ] Routing cases
- [ ] ACL cases
- [ ] NAT cases
- [ ] Wireless cases

## Human correction

- [ ] At least 5 documented cases where humans corrected AI

## Dashboard

- [ ] Issue types
- [ ] Severity
- [ ] AI vs human agreement

## Security

- [ ] API key not hardcoded
- [ ] Secrets excluded from Git
- [ ] User input not executed as commands

## Demonstration

- [ ] Broken Packet Tracer lab
- [ ] Symptom
- [ ] Packet Tracer evidence
- [ ] AI analysis
- [ ] Python check
- [ ] Comparison
- [ ] Human review
- [ ] Fix
- [ ] Verification

---

# 21. UNNECESSARY FEATURES

Do NOT build these unless the official requirement changes.

## 21.1 Automatic Packet Tracer control

Do not attempt to make Python automatically manipulate Packet Tracer.

Why:

- Not required
- Adds significant complexity
- Creates fragile automation
- Distracts from the actual AI + deterministic troubleshooting objective

Manual Packet Tracer correction is sufficient.

---

## 21.2 Real-time network monitoring

Not required.

NetSage AI is a troubleshooting helper for Packet Tracer evidence.

It is not a production network monitoring platform.

---

## 21.3 Mobile application

Not required.

Streamlit is enough.

---

## 21.4 User authentication system

Not required by the supplied requirements.

Do not waste project time on login/signup.

---

## 21.5 Complex database

Not required for 30 cases.

JSON is sufficient for the initial implementation.

---

## 21.6 Training your own LLM

Bad use of time.

You do not need to train an LLM for this project.

The important engineering contribution is:

```text
AI reasoning
+
deterministic verification
+
human review
```

---

# 22. OVERENGINEERING TO AVOID

Avoid:

```text
microservices
Kubernetes
Docker orchestration
vector databases
RAG pipelines
fine-tuning
agent swarms
complex authentication
real-time network telemetry
automatic Cisco device control
```

None of these are required by the official requirements supplied.

Adding them does not automatically make the project more impressive.

It can actually make the project worse because you will have less time to make the required components reliable.

---

# 23. LIKELY FAILURE POINTS

## Failure 1 — Treating AI as the truth

This is the biggest architectural mistake.

Bad:

```text
AI says gateway problem
→ system accepts gateway problem
```

Correct:

```text
AI says gateway problem
+
Python evidence
+
human review
→ final decision
```

---

## Failure 2 — Fake deterministic rules

Do not build Python rules that simply repeat what the AI said.

For example:

```python
if "vlan" in ai_response:
    return "VLAN problem"
```

That is not deterministic verification.

Python must independently inspect evidence.

---

## Failure 3 — AI hallucinating evidence

The AI must never say:

```text
show ip route shows...
```

unless the provided output actually contains that information.

---

## Failure 4 — Confusing "not detected" with "not present"

This is extremely important.

These are different:

```text
Python detected no missing route
```

and:

```text
Python could not determine whether a route exists
```

The second may simply mean insufficient evidence.

---

## Failure 5 — Human review becomes cosmetic

If the reviewer clicks "Accept" without seeing the evidence and comparison, the human-in-the-loop requirement becomes meaningless.

The review UI should clearly show:

```text
AI
Python
Evidence
Comparison
Decision
```

---

## Failure 6 — Dashboard numbers are hardcoded

Never write:

```text
AI accuracy = 83%
```

manually.

Calculate it from review records.

---

## Failure 7 — Dataset cases are unrealistic

The 30 cases should correspond to actual Cisco-style troubleshooting situations and Packet Tracer evidence.

Do not create 30 superficial variations of the same problem.

---

# 24. AI HALLUCINATION RISKS

The AI can hallucinate:

- Commands
- Configuration
- Evidence
- Root causes
- Network topology
- IP addresses
- VLAN IDs
- Routes

Therefore the prompt must enforce:

```text
Use only supplied evidence.
Do not invent command output.
Do not invent topology information.
Explicitly identify missing evidence.
Separate observations from conclusions.
```

The AI should reason like:

```text
Observation:
Fa0/1 is administratively down.

Inference:
This may explain the connectivity failure.

Recommended validation:
show interfaces status
```

Not:

```text
The cable is definitely broken.
```

unless evidence supports that conclusion.

---

# 25. NETWORKING LOGIC RISKS

Networking problems frequently have multiple plausible causes.

For example:

```text
PC cannot ping server
```

could be caused by:

```text
VLAN
IP configuration
subnet mask
gateway
routing
ACL
interface state
NAT
```

Therefore the AI must not jump directly from symptom to root cause.

The system should follow:

```text
Symptom
→ Evidence
→ Candidate cause
→ Validation command
→ Fix
→ Verification
```

This is much more defensible.

---

# 26. PACKET TRACER AS GROUND TRUTH

For the project, Packet Tracer is the source of truth for the actual lab state.

If AI says:

```text
VLAN 20 exists
```

but Packet Tracer evidence says:

```text
VLAN 20 does not exist
```

the Packet Tracer evidence wins.

If AI says:

```text
interface is up
```

but:

```text
show interfaces
```

shows:

```text
administratively down
```

the command output wins.

The AI is an interpretation layer.

It is not a replacement for the network evidence.

---

# 27. WHERE DETERMINISTIC PYTHON MUST BE USED

Use Python whenever the problem can be answered mechanically.

Examples:

```text
Are two devices using the same IP?
→ Python

Does an explicitly documented VLAN exist in VLAN output?
→ Python

Is an interface explicitly down?
→ Python

Does a required route appear in the routing table?
→ Python

Does the configured gateway match the supplied subnet?
→ Python

Is the subnet configuration mathematically consistent?
→ Python
```

Use AI when reasoning is required:

```text
What is the most likely root cause?

Which evidence is most relevant?

What should the user check next?

What troubleshooting sequence makes sense?

How do multiple observations combine into a diagnosis?
```

This separation is one of the strongest aspects of the project.

---

# 28. RECOMMENDED TEAM RESPONSIBILITIES

For a 3–4 student team:

## Member 1 — Networking + Dataset

Responsible for:

```text
Packet Tracer cases
networking correctness
30-case dataset
verification scenarios
```

---

## Member 2 — Python Rule Engine

Responsible for:

```text
evidence parsing
six deterministic rules
unit tests
comparison inputs
```

---

## Member 3 — AI + Backend

Responsible for:

```text
OpenAI integration
prompt design
structured output
AI validation
comparison engine
```

---

## Member 4 — Streamlit + Dashboard + Testing

Responsible for:

```text
UI
human review
dashboard
integration testing
demo flow
```

Everyone should still understand the complete architecture.

---

# 29. CURSOR IMPLEMENTATION RULES

When giving this blueprint to Cursor, Cursor must follow these constraints:

```text
1. Do not implement the entire application in one step.

2. Implement one phase at a time.

3. Do not invent features outside the official requirements.

4. Do not replace deterministic Python rules with AI.

5. Do not allow AI output to bypass human review.

6. Do not hardcode dashboard metrics.

7. Do not hardcode API keys.

8. Do not invent Packet Tracer evidence.

9. Keep modules small and testable.

10. Write tests alongside implementation.

11. Before modifying an existing module, inspect its current implementation.

12. Do not rewrite working modules unnecessarily.

13. Preserve the defined JSON contracts.

14. Validate AI output before displaying it as a diagnosis.

15. Never treat missing evidence as proof that a network condition does not exist.
```

---

# 30. FINAL ARCHITECTURAL PRINCIPLE

The entire NetSage AI project should be explainable in one diagram:

```text
              PACKET TRACER
                   │
                   │ Evidence
                   ▼
            ┌───────────────┐
            │ Input Layer   │
            └───────┬───────┘
                    │
             ┌──────┴──────┐
             ▼             ▼
       ┌───────────┐   ┌───────────┐
       │  Python   │   │    AI     │
       │ Determin. │   │ Reasoning │
       │   Rules   │   │           │
       └─────┬─────┘   └─────┬─────┘
             │               │
             └───────┬───────┘
                     ▼
              ┌─────────────┐
              │ Comparison  │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │   HUMAN     │
              │   REVIEW    │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │    FIX      │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ VERIFICATION│
              └─────────────┘
```

The project's strongest argument is therefore:

> **NetSage AI does not blindly trust AI. It combines Packet Tracer evidence, deterministic networking checks, AI-assisted reasoning, and mandatory human review to produce an auditable troubleshooting workflow.**

That is the architecture Cursor should implement.