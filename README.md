# NetSage AI

AI-assisted troubleshooting helper for Cisco Packet Tracer labs.

This repository currently contains **milestones M0–M1** (project setup and data models).

## Requirements

- Python 3.x

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Set `OPENAI_API_KEY` in `.env` when you are ready to use the API. The key is optional for M0.

## Run

```bash
streamlit run app.py
```

Expected startup message:

```text
NetSage AI
System initialized.
```

## Data models (M1)

Pydantic models in `models/` define the core entities: `Case`, `AIDiagnosis`, `PythonFinding`, `ComparisonResult`, `HumanReview`, and `Verification`. They validate allowed issue types, severity, review decisions, comparison states, verification states, and confidence (0–100). Models contain no networking or diagnosis logic.

## Tests

```bash
pytest
```

Do not commit `.env` or API keys.
