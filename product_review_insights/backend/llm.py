import json
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from openai import APIConnectionError, AzureOpenAI, OpenAIError
from pydantic import ValidationError

from .schemas import Insights, JudgeResult
from .prompts import PROMPTS

load_dotenv()

class LLMUnavailable(Exception):
    pass

def client():
    required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise LLMUnavailable("Missing Azure OpenAI configuration: " + ", ".join(missing))
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].strip()
    parsed_endpoint = urlparse(endpoint)
    if parsed_endpoint.scheme != "https" or not parsed_endpoint.hostname:
        raise LLMUnavailable("AZURE_OPENAI_ENDPOINT must be the HTTPS endpoint of your Azure OpenAI resource.")
    if any(marker in endpoint.upper() for marker in ("YOUR-", "YOUR_", "REPLACE_", "PLACEHOLDER")):
        raise LLMUnavailable("AZURE_OPENAI_ENDPOINT is still a placeholder. Set it to your Azure OpenAI resource URL in .env.")
    return AzureOpenAI(azure_endpoint=endpoint, api_key=os.environ["AZURE_OPENAI_API_KEY"], api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"), timeout=30.0, max_retries=1)

def validated_completion(messages, schema):
    api = client()
    history = list(messages)
    for attempt in range(2):
        try:
            response = api.chat.completions.create(model=os.environ["AZURE_OPENAI_DEPLOYMENT"], messages=history, temperature=0, response_format={"type":"json_object"})
            content = response.choices[0].message.content or ""
            return schema.model_validate_json(content)
        except (ValidationError, ValueError) as exc:
            if attempt == 1:
                raise ValueError("Model output failed validation after one retry") from exc
            history.extend([{"role":"assistant","content":content},{"role":"user","content":"Your previous JSON failed schema validation: " + str(exc) + ". Return corrected JSON only."}])
        except APIConnectionError as exc:
            raise LLMUnavailable("Could not connect to Azure OpenAI. Check AZURE_OPENAI_ENDPOINT and your network, DNS, firewall, or proxy settings.") from exc
        except OpenAIError as exc:
            raise LLMUnavailable("Azure OpenAI request failed") from exc

def analyze(review, technique):
    return validated_completion(PROMPTS[technique](review), Insights)

JUDGE_RULES = """You are an independent product review summary evaluator. Compare the summary ONLY with the original review. Score 1-5 using this rubric:
1 = misleading or largely invented, not useful;
2 = major omissions or inaccuracies;
3 = mostly correct but missing important product-team information;
4 = accurate and useful with minor omissions;
5 = fully faithful, concise, actionable and captures main positives/negatives.
Return JSON with integer score and a brief reason. Do not assess the predicted rating or aspects."""

def judge(review, summary):
    messages = [{"role":"system","content":JUDGE_RULES + " Return JSON only."},{"role":"user","content":json.dumps({"review":review,"summary":summary})}]
    return validated_completion(messages, JudgeResult)
