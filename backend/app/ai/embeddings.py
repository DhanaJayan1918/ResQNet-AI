"""
ResQNet AI - Text Embeddings Helper
Wraps sentence-transformers to generate vector representations of report texts.
"""

import logging
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

# Global model cache
_model = None
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    logger.warning("⚠️  sentence-transformers library not installed. Vector embeddings will be unavailable.")


def get_embeddings_model() -> Optional[Any]:
    """Retrieve the cached SentenceTransformer model instance."""
    global _model
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None

    if _model is None:
        try:
            logger.info(f"Loading SentenceTransformer model: {EMBEDDING_MODEL_NAME}...")
            # Load local or remote model
            _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            _model = None

    return _model


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate a vector embedding for the input text."""
    model = get_embeddings_model()
    if model is None:
        return None

    try:
        if not text or not text.strip():
            # Return zero vector if text is empty
            return [0.0] * 384
            
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None
