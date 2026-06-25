"""
ResQNet AI - ChromaDB Connection Manager
Manages vector store collections for duplicate detection and RAG retrieval.
"""

from typing import Any
import logging
from app.config import get_settings

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    ChromaSettings = None
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

_chroma_client: Any = None


def connect_chromadb() -> None:
    """Initialize ChromaDB client with persistent storage."""
    global _chroma_client
    if not CHROMA_AVAILABLE:
        logger.warning("⚠️  ChromaDB library not installed. Vector features will be disabled.")
        return

    settings = get_settings()

    logger.info(f"Connecting to ChromaDB (persist_dir: {settings.CHROMADB_PERSIST_DIR})...")

    _chroma_client = chromadb.PersistentClient(
        path=settings.CHROMADB_PERSIST_DIR,
        settings=ChromaSettings(
            anonymized_telemetry=False,
        ),
    )

    # Initialize collections
    _init_collections()
    logger.info("ChromaDB connected and collections initialized")


def _init_collections() -> None:
    """Create or get required ChromaDB collections."""
    client = get_chromadb()

    # Collection for report duplicate detection
    client.get_or_create_collection(
        name="report_embeddings",
        metadata={
            "description": "Report text embeddings for semantic duplicate detection",
            "hnsw:space": "cosine",
        },
    )

    # Collection for disaster SOPs (RAG)
    client.get_or_create_collection(
        name="disaster_sops",
        metadata={
            "description": "Emergency SOPs and protocols for RAG retrieval",
            "hnsw:space": "cosine",
        },
    )

    # Collection for historical incidents (pattern matching)
    client.get_or_create_collection(
        name="historical_incidents",
        metadata={
            "description": "Past incident embeddings for pattern matching",
            "hnsw:space": "cosine",
        },
    )

    logger.info("ChromaDB collections initialized: report_embeddings, disaster_sops, historical_incidents")


def get_chromadb() -> Any:
    """Get the ChromaDB client instance."""
    if _chroma_client is None:
        raise RuntimeError("ChromaDB is not connected. Call connect_chromadb() first.")
    return _chroma_client


def get_collection(name: str) -> Any:
    """Get a specific ChromaDB collection by name."""
    client = get_chromadb()
    return client.get_collection(name)


def close_chromadb() -> None:
    """Clean up ChromaDB resources."""
    global _chroma_client
    _chroma_client = None
    logger.info("ChromaDB connection closed")
