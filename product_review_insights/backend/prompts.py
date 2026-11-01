import json

RULES = """Return only a JSON object with keys aspects, rating_guess, would_recommend, summary.
aspects is a list of objects with aspect and sentiment.
Allowed aspects: quality, price, delivery, packaging, customer service.
Allowed sentiments: positive, negative, neutral.
Include ONLY aspects explicitly discussed. Each aspect appears once.
If mixed sentiment on one aspect, choose the dominant sentiment, or neutral if balanced.
rating_guess is integer 1-5 inferred from the review, not an actual star rating.
would_recommend is boolean; if not explicit, infer cautiously from overall tone.
summary is exactly one concise sentence for the product team, grounded in the review.
Never invent claims or facts. Return valid JSON, no markdown."""

EXAMPLES = [
    ("Great quality and quick delivery. Highly recommended!", {"aspects":[{"aspect":"quality","sentiment":"positive"},{"aspect":"delivery","sentiment":"positive"}],"rating_guess":5,"would_recommend":True,"summary":"Customers praise the quality and fast delivery."}),
    ("Too expensive, the package arrived crushed, and I would not buy again.", {"aspects":[{"aspect":"price","sentiment":"negative"},{"aspect":"packaging","sentiment":"negative"}],"rating_guess":1,"would_recommend":False,"summary":"High pricing and damaged packaging are key concerns."})
]

def zero_shot(review):
    return [{"role":"system","content":RULES},{"role":"user","content":review}]

def few_shot(review):
    messages = [{"role":"system","content":RULES}]
    for sample, answer in EXAMPLES:
        messages += [{"role":"user","content":sample},{"role":"assistant","content":json.dumps(answer)}]
    return messages + [{"role":"user","content":review}]

def role_based(review):
    return [{"role":"system","content":"You are a careful product-feedback analyst reporting to a product manager. Prioritise evidence and actionable issues. " + RULES},{"role":"user","content":"Analyse this customer review without adding unsupported details: " + review}]

PROMPTS = {"zero_shot":zero_shot,"few_shot":few_shot,"role_based":role_based}
