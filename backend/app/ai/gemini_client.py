"""
ResQNet AI - Gemini Client Wrapper
Initializes the Google GenAI SDK and handles asynchronous structured generation.
"""

from typing import Type, TypeVar, Optional, Any
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel
from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Global client instances
_genai_client: Optional[genai.Client] = None


def init_gemini_client() -> None:
    """Initialize the Google GenAI Client using settings."""
    global _genai_client
    settings = get_settings()

    if not settings.GEMINI_API_KEY:
        logger.warning(
            "⚠️ GEMINI_API_KEY is not set. AI agents will run in fallback heuristic mode."
        )
        return

    try:
        logger.info("Initializing Google GenAI client...")
        # Under google-genai 1.0+, Client takes an api_key parameter
        _genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Google GenAI client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI client: {e}")
        _genai_client = None


def get_gemini_client() -> Optional[genai.Client]:
    """Retrieve the global Gemini client instance."""
    global _genai_client
    if _genai_client is None:
        # Try dynamic initialization if key became available
        init_gemini_client()
    return _genai_client


async def generate_structured_output(
    prompt: str,
    response_schema: Type[T],
    system_instruction: Optional[str] = None,
    temperature: float = 0.1,
) -> Optional[T]:
    """
    Generate structured outputs from Gemini using Pydantic schema validation.
    Falls back to returning None if API key fails, quota limits are reached, or network errors occur.
    """
    client = get_gemini_client()
    if not client:
        logger.warning("Gemini client not initialized. Skipping API call.")
        return None

    settings = get_settings()
    model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"

    try:
        logger.info(f"Sending prompt to {model_name} (structured output)...")
        # Build config
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature,
            system_instruction=system_instruction,
        )

        # Call async SDK method
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )

        if not response or not response.text:
            logger.error("Empty response received from Gemini.")
            return None

        # Parse text into Pydantic model
        logger.info("Successfully received response from Gemini API.")
        return response_schema.model_validate_json(response.text)

    except Exception as e:
        logger.error(f"Error during Gemini structured generation: {e}")
        # Return None to trigger rule-based downstream fallback
        return None
