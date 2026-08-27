# NetSage AI

AI-assisted troubleshooting helper for Cisco Packet Tracer labs.

NetSage AI combines deterministic Python rule-checking, AI-assisted diagnosis, and mandatory human review to help students and engineers troubleshoot Cisco Packet Tracer lab issues. The system does not diagnose or fix anything autonomously -- every AI diagnosis must be reviewed and accepted, edited, or rejected by a human before it is treated as final.

## Requirements

- Python 3.x
- An OpenAI API key (optional for most of the app; required for live AI diagnosis)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set `OPENAI_API_KEY` to your real key when you want live AI diagnosis. The app and its Python rule engine work without it; only the AI analysis step requires a configured key.

## Run

```bash
streamlit run app.py
```

The app has two tabs:

- **Analyze Case** -- enter a symptom, topology notes, and show-command output. The system runs the deterministic Python rules, requests an AI diagnosis (if a key is configured), compares the two, and walks you through mandatory human review (Accept/Edit/Reject) and post-fix verification.
- **Dashboard** -- shows aggregate statistics (issue types, severity, AI vs. human agreement) computed from every case that has been reviewed and logged so far.

## How the pipeline works

Symptom + Topology Notes + Show Output
        -> Python deterministic rules   (rules/)
        -> AI diagnosis                 (ai/)
        -> Structured validation        (ai/validator.py)
        -> AI vs. Python comparison     (core/comparison.py)
        -> Mandatory human review       (core/review.py)
        -> Verification                 (models/verification.py)
        -> Persisted review log         (core/review_logger.py)

## Project structure

| Area | Purpose |
|---|---|
| `models/` | Pydantic models for every core entity (`Case`, `AIDiagnosis`, `PythonFinding`, `ComparisonResult`, `HumanReview`, `Verification`). Validation only -- no business logic. |
| `data/cases.json` | 30 troubleshooting cases covering VLAN, gateway, DHCP, DNS, routing, ACL, NAT, and wireless. |
| `core/dataset_loader.py` | Loads and validates the case dataset. `runtime_input()` strips expected-answer fields so they are never sent to the AI. |
| `rules/` | Six independent, deterministic checks: duplicate IP, wrong subnet mask, gateway mismatch, interface down, missing VLAN, missing route. Never calls OpenAI. Reports `insufficient_evidence` rather than guessing when evidence is incomplete. |
| `ai/` | `DiagnosisService` calls OpenAI and returns raw, unvalidated text. `schema.py`/`validator.py` parse and validate that text into a typed `AIDiagnosis`, rejecting anything malformed before it can reach a human. |
| `core/comparison.py` | Compares the AI diagnosis against Python findings: `AGREEMENT`, `PARTIAL_AGREEMENT`, `AI_ONLY`, `PYTHON_ONLY`, `CONFLICT`, or `NO_DETERMINISTIC_RESULT`. |
| `core/review.py` | Enforces the Accept/Edit/Reject workflow. No diagnosis becomes "final" without going through this. |
| `core/review_logger.py` | Persists every completed review (original AI diagnosis, Python findings, comparison, human decision, verification) to `data/reviews.json`, with atomic writes. |
| `ui/` | Streamlit display components. Pure display -- all decisions are delegated to `core/`, `ai/`, and `rules/`. |
| `evaluation/` | Scripts and results for evaluating the system against the full 30-case dataset (see `evaluation/README.md`). |
| `docs/` | Architecture, demo walkthrough, and Responsible AI documentation. |

## Documentation

- [`docsARCHITECTURE.md`](docsARCHITECTURE.md) -- system architecture
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) -- the milestone-by-milestone build plan this project followed
- [`docs/DEMO.md`](docs/DEMO.md) -- a full end-to-end demonstration case
- [`docs/RESPONSIBLE_AI.md`](docs/RESPONSIBLE_AI.md) -- limitations, hallucination risks, why human review is mandatory, and system boundaries
- [`evaluation/README.md`](evaluation/README.md) -- how to run and interpret the 30-case evaluation

## Tests

```bash
pytest
```

All tests run without requiring a live OpenAI API key -- the AI service is mocked throughout the test suite.

## Security

- Never commit `.env` or any real API key. `.gitignore` excludes `.env` by default.
- `.env.example` documents required environment variables without real values.
