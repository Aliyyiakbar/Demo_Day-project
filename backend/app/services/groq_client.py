import json

from groq import Groq

from app.core.config import settings

# Prefer models with solid availability and enough context for JSON roadmaps.
GROQ_MODELS = [
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
]

_client: Groq | None = None


class GroqServiceError(Exception):
    """Raised when the Groq API cannot complete a request."""


def _get_client() -> Groq:
    global _client
    api_key = settings.groq_api_key.strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Add your Groq API key to backend/.env and restart the server.")
    if _client is None:
        _client = Groq(api_key=api_key)
    return _client


def _should_try_next_model(message: str) -> bool:
    lowered = message.lower()
    retry_hints = [
        "rate limit",
        "too many requests",
        "timeout",
        "timed out",
        "temporarily",
        "unavailable",
        "overloaded",
        "service",
        "try again",
        "context length",
        "maximum context",
        "model",
    ]
    return any(hint in lowered for hint in retry_hints) or any(code in message for code in ("429", "500", "502", "503", "504"))


def _format_error(error: Exception) -> str:
    message = str(error)
    if "401" in message or "403" in message or "unauthorized" in message.lower():
        return "Invalid GROQ_API_KEY. Create a new key at https://console.groq.com/keys"
    if "429" in message or "rate limit" in message.lower():
        return "Groq rate limit exceeded. Wait a moment and try again."
    return f"Groq API error: {message}"


def create_json_completion(messages: list[dict], json_schema: dict | None = None) -> str:
    client = _get_client()

    extra_system = None
    if json_schema:
        extra_system = (
            "Return valid JSON only, with no markdown fences. "
            f"Expected JSON shape: {json.dumps(json_schema)}"
        )

    last_error: Exception | None = None
    for model in GROQ_MODELS:
        try:
            request_messages = list(messages)
            if extra_system:
                request_messages.append({"role": "system", "content": extra_system})

            response = client.chat.completions.create(
                model=model,
                messages=request_messages,
                temperature=0.2,
                max_tokens=4096,
            )
            text = ((response.choices[0].message.content or "").strip() if response.choices else "")
            if not text:
                raise ValueError("Groq returned an empty response")
            return text
        except ValueError:
            raise
        except Exception as error:
            last_error = GroqServiceError(_format_error(error))
            if _should_try_next_model(str(error)):
                continue
            raise last_error from error

    if last_error:
        raise last_error
    raise GroqServiceError("No Groq model could complete the request.")
