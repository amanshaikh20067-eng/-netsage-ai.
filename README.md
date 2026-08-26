# NetSage AI

AI-assisted troubleshooting helper for Cisco Packet Tracer labs.

This repository currently contains **milestone M0** (project setup) only.

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

## Tests

```bash
pytest
```

Do not commit `.env` or API keys.
