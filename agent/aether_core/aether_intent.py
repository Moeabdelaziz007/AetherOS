"""AetherOS Intent Vectorization Module.

This module provides semantic vectorization capabilities for the AetherOS system,
enabling natural language intent to be mapped into high-dimensional vector space
for semantic similarity analysis and healing.

The module implements the AetherIntentVectorizer class which converts text
representations into numerical embeddings, allowing for semantic comparison
between intents. This is crucial for the "Semantic Healing" mechanism where
similar historical intents can be identified when exact matches fail.

Key Features:
    - Text-to-vector conversion using deterministic pseudo-embeddings
    - Cosine similarity calculation between intent vectors
    - Nearest neighbor search for semantic intent matching
    - Support for both local and remote embedding models

Key Classes:
    AetherIntentVectorizer: Main class for intent vectorization operations.

Key Methods:
    aether_vectorize: Converts text to a semantic vector.
    aether_calculate_similarity: Computes cosine similarity between vectors.
    aether_get_nearest_neighbors: Finds semantically similar intents.

Example:
    >>> vectorizer = AetherIntentVectorizer(use_remote=False)
    >>> vector = await vectorizer.aether_vectorize("book a flight")
    >>> similarity = vectorizer.aether_calculate_similarity(vector1, vector2)
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

# In a production environment, we would use vertexai.language_models.TextEmbeddingModel
# For the AetherOS prototype, we use a structured similarity fallback or mock embeddings.

logger = logging.getLogger("aether.intent")

class AetherIntentVectorizer:
    """The Semantic Compass of AetherOS."""
    
    def __init__(self, use_remote: bool = False) -> None:
        """Initialize the intent vectorizer.
        
        Args:
            use_remote: If True, use remote embedding service. If False,
                use deterministic pseudo-embeddings for local testing.
        
        Attributes:
            use_remote: Flag indicating whether to use remote embeddings.
            embedding_dim: Dimension of the embedding vectors (768 for Gecko/Vertex).
        """
        self.use_remote = use_remote
        self.embedding_dim = 768  # Standard for Gecko/Vertex
        
    async def aether_vectorize(self, text: str) -> List[float]:
        """Convert text into a semantic vector.
        
        This method transforms natural language text into a high-dimensional vector
        representation that captures semantic meaning. In local mode, it uses a
        deterministic pseudo-embedding based on character hashing for reproducibility.
        
        Args:
            text: The input text to vectorize.
        
        Returns:
            A list of floats representing the semantic vector with length
            equal to embedding_dim (768).
        
        Example:
            >>> vectorizer = AetherIntentVectorizer(use_remote=False)
            >>> vector = await vectorizer.aether_vectorize("book a flight")
            >>> len(vector)
            768
        """
        if not self.use_remote:
            # Deterministic pseudo-embedding for local testing
            # maps text to a fixed-size vector based on char-hash
            logger.debug(f"📐 Locally vectorizing: {text}")
            seed = sum(ord(c) for c in text)
            np.random.seed(seed)
            vector = np.random.uniform(-1, 1, self.embedding_dim).tolist()
            return vector
        
        # TODO: Integration with Vertex AI TextEmbeddingModel
        # model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        # embeddings = model.get_embeddings([text])
        # return embeddings[0].values
        return [0.0] * self.embedding_dim

    def aether_calculate_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two intent vectors.
        
        Cosine similarity measures the cosine of the angle between two vectors,
        providing a value between -1 and 1 where 1 indicates identical
        orientation, 0 indicates orthogonality, and -1 indicates opposite
        orientation.
        
        Args:
            vec_a: First vector as a list of floats.
            vec_b: Second vector as a list of floats.
        
        Returns:
            A float value between 0.0 and 1.0 representing the cosine
            similarity. Returns 0.0 if either vector is a zero vector.
        
        Raises:
            None: Handles zero vectors gracefully by returning 0.0.
        
        Example:
            >>> vectorizer = AetherIntentVectorizer()
            >>> similarity = vectorizer.aether_calculate_similarity([1.0, 0.0], [1.0, 0.0])
            >>> similarity
            1.0
        """
        a = np.array(vec_a)
        b = np.array(vec_b)
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        # Prevent ZeroDivisionError when either vector is a zero vector
        denominator = norm_a * norm_b
        if denominator == 0:
            return 0.0
        return dot_product / denominator

    async def aether_get_nearest_neighbors(self, query_text: str, candidates: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """Find the most semantically similar historical intents.
        
        This method is used for 'Semantic Healing' when an exact match fails.
        It vectorizes the query text and ranks candidates by semantic similarity,
        returning the top_k most similar intents.
        
        Args:
            query_text: The query text to find similar intents for.
            candidates: A list of candidate dictionaries, each potentially containing
                a 'vector' key with pre-computed embeddings.
            top_k: The number of top results to return. Defaults to 3.
        
        Returns:
            A list of dictionaries containing the top_k most similar candidates,
            each augmented with a 'similarity_score' key. Results are sorted
            by similarity in descending order.
        
        Example:
            >>> vectorizer = AetherIntentVectorizer()
            >>> candidates = [
            ...     {"intent": "book flight", "vector": [0.1, 0.2, ...]},
            ...     {"intent": "get weather", "vector": [0.3, 0.4, ...]}
            ... ]
            >>> results = await vectorizer.aether_get_nearest_neighbors(
            ...     "reserve airplane", candidates, top_k=2
            ... )
            >>> results[0]["similarity_score"] > results[1]["similarity_score"]
            True
        """
        query_vec = await self.aether_vectorize(query_text)
        ranked = []
        
        for cand in candidates:
            cand_vec = cand.get("vector")
            if not cand_vec:
                continue
            
            score = self.aether_calculate_similarity(query_vec, cand_vec)
            ranked.append({**cand, "similarity_score": score})
            
        # Sort by similarity descending
        ranked.sort(key=lambda x: x["similarity_score"], reverse=True)
        return ranked[:top_k]
