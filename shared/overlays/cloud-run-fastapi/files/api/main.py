"""FastAPI starter for Google Cloud Run. Scales to zero when idle.

Run locally:  uvicorn main:app --reload --port 8080
Env vars come from Cloud Run settings, never from the repo.
"""
from fastapi import FastAPI

app = FastAPI(title="API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Add your routes below. Keep heavy work (reports, imports, AI calls) here,
# and keep the web app thin.
