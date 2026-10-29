# Finance & Poverty Nexus — Rwanda

Flask + Plotly dashboard linking financial inclusion to poverty across Rwanda's 30 districts.

## Run locally
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                                      # http://localhost:5000
```

## Add your contact details
Edit `config.py` (or set the environment variables in `.env.example`). They update the footer, Contact page and copyright line.

## Deploy
- **Render / Railway / Heroku:** connect the repo; start command is in `Procfile`. Set `SECRET_KEY`, `ORG_NAME`, contact vars, and attach a persistent disk with `DATA_DIR` pointing to it (otherwise saved reports reset on redeploy).
- **Docker:** `docker build -t nexus . && docker run -p 8000:8000 -v nexus-data:/data -e SECRET_KEY=... nexus`
- Health check: `/health`

## Pages
Dashboard · Map & correlation · District profile · Compare · Policy simulator · Risk calculator · Action plan · Report exclusion · Resources · Data & method · Contact · `/api/districts` · `/download/data.csv`

## Notes
- District boundaries download once on first map visit and are cached in `static/data/` (or run `python scripts/fetch_geojson.py`). If unavailable, the map falls back to bubbles.
- Reports and contact messages are stored in SQLite (`DATA_DIR/reports.db`). There is no admin login yet — add one before exposing message contents publicly.
