
import os

from openai import APIConnectionError, OpenAIError

from backend.llm import LLMUnavailable, client


def main():
    try:
        response = client().chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            messages=[{"role": "user", "content": "Say hello and confirm the connection works."}],
            temperature=0,
        )
    except LLMUnavailable as exc:
        raise SystemExit(str(exc)) from exc
    except APIConnectionError as exc:
        raise SystemExit(
            "Could not connect to Azure OpenAI. Check AZURE_OPENAI_ENDPOINT and your network, DNS, firewall, or proxy settings."
        ) from exc
    except OpenAIError as exc:
        raise SystemExit(
            "Azure OpenAI request failed. Check the deployment name, API version, and resource settings."
        ) from exc

    print("Azure OpenAI response:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
