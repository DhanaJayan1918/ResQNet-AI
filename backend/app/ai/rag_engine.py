"""
ResQNet AI - RAG Retrieval Engine
Loads, indexes, and retrieves disaster Standard Operating Procedures (SOPs)
using ChromaDB or fallback scikit-learn TF-IDF keyword indexing.
"""

import os
import glob
import logging
from typing import List, Dict, Any, Optional

from app.db.chromadb_client import CHROMA_AVAILABLE, get_collection
from app.ai.embeddings import generate_embedding

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

# Directory where emergency SOPs are stored
SOP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "sops"
)

# InMemory cache for TF-IDF fallback
_in_memory_sop_chunks: List[Dict[str, str]] = []


def load_sop_files() -> List[Dict[str, str]]:
    """Reads all markdown files from the SOP directory and splits them into logical chunks."""
    chunks = []
    
    # Ensure directory exists
    os.makedirs(SOP_DIR, exist_ok=True)
    
    sop_files = glob.glob(os.path.join(SOP_DIR, "*.md"))
    logger.info(f"RAG: Scanning {SOP_DIR} for SOP documents. Found {len(sop_files)} files.")
    
    # Create default SOP files if none exist to make it immediately operational
    if not sop_files:
        _create_default_sop_files()
        sop_files = glob.glob(os.path.join(SOP_DIR, "*.md"))

    for filepath in sop_files:
        filename = os.path.basename(filepath)
        category = filename.replace("_sop.md", "")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Split by double newline or header markers
            raw_segments = content.split("\n## ")
            title = filename
            
            # First block might contain general title
            if raw_segments:
                first_block = raw_segments.pop(0)
                if first_block.strip():
                    chunks.append({
                        "category": category,
                        "title": title,
                        "content": first_block.strip()
                    })
                    
            for segment in raw_segments:
                if not segment.strip():
                    continue
                # Split segment into header and body
                lines = segment.split("\n", 1)
                header = lines[0].strip()
                body = lines[1].strip() if len(lines) > 1 else ""
                
                chunks.append({
                    "category": category,
                    "title": f"{filename} - {header}",
                    "content": f"{header}\n{body}"
                })
        except Exception as e:
            logger.error(f"Failed to read SOP file {filename}: {e}")
            
    return chunks


def _create_default_sop_files() -> None:
    """Creates initial emergency SOP markdown files in data/sops/ if missing."""
    os.makedirs(SOP_DIR, exist_ok=True)
    
    sops = {
        "flood_sop.md": (
            "# Flood Emergency Response Protocol (SOP-FL-01)\n\n"
            "## 1. Life Safety and Active Water Rescue\n"
            "Immediately deploy rescue boats to priority points. Prioritize families trapped on roofs, "
            "vulnerable children, and the elderly. All field officers must wear high-buoyancy life jackets.\n\n"
            "## 2. Relief Camp and Shelter Operations\n"
            "Direct displaced persons to high-ground schools and community shelters. Setup clean water filtration "
            "stations and distribute food rations. Coordinate medical checkups for waterborne disease prevention.\n\n"
            "## 3. Power Grid and Electrical Isolation\n"
            "Isolate sub-stations in inundated regions. Coordinate with utility companies to shut down power grids "
            "where water levels exceed 3 feet to prevent electrocution hazards.\n"
        ),
        "earthquake_sop.md": (
            "# Earthquake Structural Collapse Response (SOP-EQ-02)\n\n"
            "## 1. Search and Rescue in Rubble\n"
            "Use heavy rescue equipment, sonar detectors, and canine teams. Clear access routes for ambulances immediately. "
            "Triage injuries on-site: Red tag (immediate), Yellow tag (delayed), Green tag (minor).\n\n"
            "## 2. Hospital Load Management\n"
            "Divert non-critical victims to peripheral medical centers. Keep tertiary hospitals clear for surgeries. "
            "Check structural integrity of hospital buildings before admitting emergency cases inside.\n\n"
            "## 3. Emergency Shelter Setup\n"
            "Establish open-air tent shelters in parks or stadiums. Avoid setting up indoor shelters near tall structures "
            "subject to collapse during aftershocks.\n"
        ),
        "wildfire_sop.md": (
            "# Wildfire Evacuation and Containment (SOP-WF-03)\n\n"
            "## 1. Wildfire Evacuation Corridors\n"
            "Identify safe escape routes away from wind direction. Coordinate with police to enforce one-way outbound lanes "
            "on narrow forest corridors. Set up check-points at evacuation exits.\n\n"
            "## 2. Air Quality and Public Safety\n"
            "Issue high-level smoke alerts. Distribute N95 respirators to volunteers and citizens. Instruct residents "
            "within a 5-mile radius to close all windows and stay indoors.\n\n"
            "## 3. Firefighting Asset Allocation\n"
            "Prioritize aerial water drops on windward fronts to block fire expansion toward residential communities.\n"
        ),
        "medical_sop.md": (
            "# Medical Triage and Epidemic Containment (SOP-MD-04)\n\n"
            "## 1. Mass Casualty Triage Protocols\n"
            "Establish on-scene medical triage areas. Triage levels: Category 1 (immediate resuscitation), "
            "Category 2 (major trauma / stabilization), Category 3 (walking wounded).\n\n"
            "## 2. Contagion and Waterborne Disease Control\n"
            "Isolate patients showing symptoms of cholera, gastroenteritis, or typhoid. Treat relief camp water sources "
            "with chlorine. Ensure clean sanitary facilities are separated from dining zones.\n"
        )
    }
    
    for name, content in sops.items():
        filepath = os.path.join(SOP_DIR, name)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Created default SOP file: {name}")
        except Exception as e:
            logger.error(f"Failed to create default SOP file {name}: {e}")


def initialize_sop_db() -> None:
    """Loads all SOP files and indexes them in ChromaDB (if available) or in-memory fallback cache."""
    global _in_memory_sop_chunks
    
    chunks = load_sop_files()
    _in_memory_sop_chunks = chunks
    logger.info(f"Loaded {len(chunks)} SOP chunks into local cache.")

    if not CHROMA_AVAILABLE:
        logger.info("ChromaDB not available. Standard RAG will run on TF-IDF in-memory fallback.")
        return

    try:
        coll = get_collection("disaster_sops")
        
        # Clear existing collection items
        existing = coll.get()
        if existing and existing["ids"]:
            coll.delete(ids=existing["ids"])
            
        ids = [f"sop-{i}" for i in range(len(chunks))]
        documents = [c["content"] for c in chunks]
        metadatas = [{"category": c["category"], "title": c["title"]} for c in chunks]
        
        embeddings = []
        for doc in documents:
            emb = generate_embedding(doc)
            embeddings.append(emb or [0.0] * 384) # zero vector fallback

        coll.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Successfully loaded and indexed {len(chunks)} SOP chunks in ChromaDB disaster_sops.")
    except Exception as e:
        logger.error(f"Failed to load SOPs into ChromaDB: {e}. Falling back to in-memory mode.")


def retrieve_relevant_sops(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve the top relevant disaster SOP sections matching the query.
    Uses ChromaDB vector search or TF-IDF fallback if ChromaDB is unavailable.
    """
    if not query or not query.strip():
        return []

    # Try ChromaDB first
    if CHROMA_AVAILABLE:
        try:
            embedding = generate_embedding(query)
            if embedding:
                coll = get_collection("disaster_sops")
                results = coll.query(
                    query_embeddings=[embedding],
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
                
                retrieved = []
                if results and results["documents"] and len(results["documents"][0]) > 0:
                    for i in range(len(results["documents"][0])):
                        doc = results["documents"][0][i]
                        meta = results["metadatas"][0][i]
                        dist = results["distances"][0][i]
                        retrieved.append({
                            "title": meta.get("title", "SOP Document"),
                            "category": meta.get("category", "general"),
                            "content": doc,
                            "score": round(1.0 - float(dist), 2) # Cosine distance to similarity
                        })
                    return retrieved
        except Exception as e:
            logger.warning(f"ChromaDB SOP query failed: {e}. Falling back to TF-IDF.")

    # Fallback to TF-IDF scikit-learn search
    if not _in_memory_sop_chunks:
        # Load if not loaded
        load_sop_files()

    if not _in_memory_sop_chunks:
        return []

    if not SKLEARN_AVAILABLE:
        # Simplest keyphrase overlap fallback
        results = []
        words = set(query.lower().split())
        for chunk in _in_memory_sop_chunks:
            chunk_words = set(chunk["content"].lower().split())
            overlap = len(words & chunk_words)
            if overlap > 0:
                results.append((chunk, overlap))
        results.sort(key=lambda x: x[1], reverse=True)
        return [{
            "title": r[0]["title"],
            "category": r[0]["category"],
            "content": r[0]["content"],
            "score": float(r[1])
        } for r in results[:limit]]

    try:
        corpus = [c["content"] for c in _in_memory_sop_chunks]
        vectorizer = TfidfVectorizer().fit(corpus)
        
        corpus_vectors = vectorizer.transform(corpus)
        query_vector = vectorizer.transform([query])
        
        similarities = cosine_similarity(query_vector, corpus_vectors)[0]
        
        ranked_indices = similarities.argsort()[::-1]
        
        retrieved = []
        for idx in ranked_indices[:limit]:
            sim = similarities[idx]
            if sim > 0.05: # minimum similarity filter
                chunk = _in_memory_sop_chunks[idx]
                retrieved.append({
                    "title": chunk["title"],
                    "category": chunk["category"],
                    "content": chunk["content"],
                    "score": round(float(sim), 2)
                })
        return retrieved
    except Exception as e:
        logger.error(f"Error executing TF-IDF SOP retrieval: {e}")
        # Default returns first N chunks
        return [{
            "title": c["title"],
            "category": c["category"],
            "content": c["content"],
            "score": 0.50
        } for c in _in_memory_sop_chunks[:limit]]
