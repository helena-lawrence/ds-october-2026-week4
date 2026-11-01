# Product Review Insights — Helena Lawrence

Azure OpenAI product-review aspect sentiment extraction, summary generation, and independent LLM-as-judge scoring.

## Quick start (Docker)
1. Copy `.env.example` to `.env` and add real Azure OpenAI endpoint, key, and deployment name. Use a deployment supporting JSON mode.
2. Run `docker compose up --build` from the repository root.
3. Visit Streamlit at http://localhost:8502 and FastAPI docs at http://localhost:8001/docs.
4. Test `GET http://localhost:8001/health`.

The Compose file defaults to non-conflicting host ports (`8001` for the API and `8502` for Streamlit). If those ports are already in use on your machine, override them with `BACKEND_PORT` and `FRONTEND_PORT` before starting Docker.

## Azure connection troubleshooting
Set `AZURE_OPENAI_ENDPOINT` in `.env` to the real endpoint for your Azure OpenAI resource, not the sample `YOUR-RESOURCE` value. You can find it in the resource's Azure portal under **Keys and Endpoint**. Keep the API key private. If the endpoint is correct but requests still fail, verify that your network can resolve and reach the resource on HTTPS port 443; a corporate firewall or proxy may block access.

## Local start (Windows PowerShell)
```powershell
# Create the virtual environment first (choose the command your machine has):
py -3.12 -m venv .venv
# If `py` is not available and you have uv installed:
uv venv --no-project --python 3.12 .venv

# Then activate it:
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt -r frontend/requirements.txt
Copy-Item .env.example .env
# Edit .env with your Azure settings
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
# In a second terminal, from project root, activate venv:
$env:API_URL = "http://127.0.0.1:8001"
streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8502
```

The local commands use ports 8001 and 8502 to avoid conflicts with Docker-published services on ports 8000 and 8501. Open Streamlit at http://localhost:8502 and FastAPI docs at http://localhost:8001/docs.

## Accuracy experiment
`python evaluate.py` runs 3 techniques on the same 20 manually labelled synthetic reviews. Outputs `reports/accuracy.csv` and `reports/predictions.csv`. The first run also writes `data/human_judge_scores.csv` with ten generated summaries. BEFORE comparing with the judge, manually score each summary using the 1-5 rubric in `backend/llm.py`; rerun `python evaluate.py` to calculate exact and within-one agreement in `reports/judge_agreement.csv`. Do not report fabricated metrics. Results vary by deployment/model. Judge and extraction are separate calls, so this consumes API tokens.

### Accuracy results (fill after execution)
| Technique | Aspects exact (%) | Rating exact (%) | Recommend exact (%) | Mean (%) |
|---|---:|---:|---:|---:|
| Zero-shot | TBD | TBD | TBD | TBD |
| Few-shot | TBD | TBD | TBD | TBD |
| Role-based | TBD | TBD | TBD | TBD |

**Chosen technique:** TBD after running experiment. Prefer highest measured average accuracy, considering latency and cost.

**Judge agreement (10 manually scored examples):** TBD; record exact agreement and within-one-point agreement.

## Endpoints
- `GET /health` → 200 `{"status":"ok"}` (process health, not Azure readiness)
- `POST /analyze` → 200 with validated insights and judge
- 422 invalid request body, 400 blank/whitespace review, 503 Azure unavailable or invalid model response after retry.

## Design notes
- All LLM requests happen in FastAPI, not Streamlit.
- Secrets are only in uncommitted `.env`, not the frontend.
- 20 synthetic labels are hand-authored; they are a small demonstration set, not proof of production quality.
- Rating is inferred from review text and may differ from an actual customer star rating.
- Exact aspect mapping is strict: one wrong or extra aspect fails the aspect field for that review.
