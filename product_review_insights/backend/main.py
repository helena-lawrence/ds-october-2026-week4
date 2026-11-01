from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from .schemas import ReviewRequest, ReviewResponse
from .llm import analyze, judge, LLMUnavailable

app = FastAPI(title="Product Review Insights", version="1.0.0")

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#2563eb"/>
<path d="M16 43h8V30h-8zm12 0h8V18h-8zm12 0h8V25h-8z" fill="#fff"/>
</svg>"""
    return Response(content=icon, media_type="image/svg+xml")

@app.post("/analyze", response_model=ReviewResponse)
def analyze_review(payload: ReviewRequest):
    if not payload.review.strip():
        raise HTTPException(status_code=400, detail="Review cannot be blank")
    try:
        insights = analyze(payload.review, payload.technique)
        score = judge(payload.review, insights.summary)
        return ReviewResponse(insights=insights, judge=score, technique=payload.technique)
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
