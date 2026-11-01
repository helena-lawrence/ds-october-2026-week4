from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

AspectName = Literal["quality", "price", "delivery", "packaging", "customer service"]
Sentiment = Literal["positive", "negative", "neutral"]

class Aspect(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aspect: AspectName
    sentiment: Sentiment

class Insights(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aspects: list[Aspect]
    rating_guess: int = Field(ge=1, le=5)
    would_recommend: bool
    summary: str = Field(min_length=10)

    @model_validator(mode="after")
    def unique_aspects(self):
        names = [x.aspect for x in self.aspects]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate aspects")
        if len(self.summary.split('.')) > 3:
            raise ValueError("Summary must be one sentence")
        return self

class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: int = Field(ge=1, le=5)
    reason: str = Field(min_length=5)

class ReviewRequest(BaseModel):
    review: str = Field(min_length=10, max_length=5000)
    technique: Literal["zero_shot", "few_shot", "role_based"] = "few_shot"

class ReviewResponse(BaseModel):
    insights: Insights
    judge: JudgeResult
    technique: str
