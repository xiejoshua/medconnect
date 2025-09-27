# Backend (FastAPI) for MedConnect


This is a minimal Flask app that provides a `/api/search` endpoint used by the `medical-platform` frontend.

Run locally:

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

The endpoint: `GET /api/search?q=<query>` returns a JSON array of doctor objects.
