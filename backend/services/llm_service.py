
from google import genai
from google.genai import types

from backend.config import settings


_client = None


def get_gemini_client():
    """Create and reuse the Gemini client."""

    global _client

    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing. Check your .env file."
        )

    if _client is None:
        http_options = types.HttpOptions(
            timeout=30000,
            retry_options=types.HttpRetryOptions(
                attempts=1
            )
        )

        _client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=http_options
        )

    return _client


def generate_response(
    prompt: str,
    system_instruction: str | None = None,
    max_output_tokens: int = 1024
) -> str:
    """Send a prompt to Gemini and return its response."""

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    client = get_gemini_client()

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.7,
        max_output_tokens=max_output_tokens,
        automatic_function_calling=(
            types.AutomaticFunctionCallingConfig(
                disable=True
            )
        )
    )

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=config
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return response.text
