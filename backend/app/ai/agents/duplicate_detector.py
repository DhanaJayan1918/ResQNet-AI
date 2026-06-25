"""
ResQNet AI - Duplicate Detector Agent
Performs semantic and spatiotemporal deduplication on incoming crisis reports.
Supports ChromaDB vector similarity and falls back to TF-IDF cosine similarity.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from bson import ObjectId

from app.db.mongodb import get_database
from app.db.chromadb_client import CHROMA_AVAILABLE, get_collection
from app.ai.embeddings import generate_embedding
from app.utils.geo import haversine_distance

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity of TF-IDF vectors for two texts."""
    if not SKLEARN_AVAILABLE or not text1 or not text2:
        # Fall back to token jaccard similarity
        t1_set = set(text1.lower().split())
        t2_set = set(text2.lower().split())
        if not t1_set or not t2_set:
            return 0.0
        return len(t1_set & t2_set) / len(t1_set | t2_set)

    try:
        vectorizer = TfidfVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.todense()
        # Todense returns a numpy matrix, convert to array for list calculations
        import numpy as np
        vec1 = np.asarray(vectors[0])
        vec2 = np.asarray(vectors[1])
        
        dot_product = np.dot(vec1, vec2.T)[0][0]
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))
    except Exception as e:
        logger.error(f"Error computing TF-IDF similarity: {e}")
        return 0.0


async def find_duplicate_incident(
    text: str,
    latitude: float,
    longitude: float,
    max_distance_km: float = 1.0,
    time_window_hours: int = 24,
    similarity_threshold: float = 0.60
) -> Optional[str]:
    """
    Search for a duplicate active incident within spatial and temporal bounds.
    Returns the incident_id of the matching duplicate primary if found.
    """
    db = get_database()
    
    # 1. Fetch active incidents (excluding resolved, closed, and duplicate statuses)
    # Filter by time window (e.g. past 24 hours) to narrow down the check
    cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
    
    query = {
        "status": {"$nin": ["resolved", "closed", "duplicate"]},
        "created_at": {"$gte": cutoff_time}
    }
    
    cursor = db.incidents.find(query)
    candidates = await cursor.to_list(length=100)
    
    logger.info(f"Deduplication: found {len(candidates)} candidate reports in the last {time_window_hours}h.")
    
    best_candidate_id: Optional[str] = None
    best_similarity = 0.0

    for candidate in candidates:
        # Extract coordinates
        loc_coords = candidate.get("location", {}).get("coordinates", [])
        if len(loc_coords) < 2:
            continue
        
        cand_lon, cand_lat = loc_coords[0], loc_coords[1]
        dist = haversine_distance(latitude, longitude, cand_lat, cand_lon)
        
        # Space check
        if dist > max_distance_km:
            continue
            
        cand_text = candidate.get("raw_report", {}).get("text", "")
        cand_inc_id = candidate.get("incident_id")
        
        similarity = 0.0
        
        # 2. Check similarity
        # Try ChromaDB first
        chroma_success = False
        if CHROMA_AVAILABLE:
            try:
                coll = get_collection("report_embeddings")
                # Query by incident ID
                res = coll.get(ids=[cand_inc_id], include=["embeddings"])
                if res and res["embeddings"] and len(res["embeddings"]) > 0:
                    cand_embedding = res["embeddings"][0]
                    new_embedding = generate_embedding(text)
                    
                    if new_embedding and cand_embedding:
                        # Cosine distance to similarity (1 - dist)
                        import numpy as np
                        dot = np.dot(new_embedding, cand_embedding)
                        norm_new = np.linalg.norm(new_embedding)
                        norm_cand = np.linalg.norm(cand_embedding)
                        if norm_new > 0 and norm_cand > 0:
                            similarity = float(dot / (norm_new * norm_cand))
                            chroma_success = True
            except Exception as ex:
                logger.warning(f"ChromaDB lookup failed during duplicate check: {ex}")
                
        # If ChromaDB is unavailable or failed, fall back to TF-IDF cosine similarity
        if not chroma_success:
            similarity = calculate_tfidf_similarity(text, cand_text)
            
        logger.info(f"Comparing with {cand_inc_id}: dist={dist:.2f}km, similarity={similarity:.2f}")
        
        if similarity >= similarity_threshold and similarity > best_similarity:
            best_similarity = similarity
            best_candidate_id = cand_inc_id

    if best_candidate_id:
        logger.info(f"Duplicate match found: {best_candidate_id} with similarity {best_similarity:.2f}")
        return best_candidate_id
        
    return None


async def save_report_embedding(incident_id: str, text: str) -> None:
    """Save the report text embedding into ChromaDB for future duplicate checks."""
    if not CHROMA_AVAILABLE:
        return

    try:
        embedding = generate_embedding(text)
        if not embedding:
            return

        coll = get_collection("report_embeddings")
        coll.add(
            ids=[incident_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"incident_id": incident_id, "timestamp": datetime.utcnow().isoformat()}]
        )
        logger.info(f"Successfully saved embedding in ChromaDB for incident {incident_id}")
    except Exception as e:
        logger.error(f"Failed to save report embedding in ChromaDB: {e}")
