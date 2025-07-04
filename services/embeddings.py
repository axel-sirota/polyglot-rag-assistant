from openai import AsyncOpenAI
import numpy as np
from typing import List, Union
import os
import logging
import tiktoken

logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "text-embedding-3-small"
        self.dimension = 1536
        self.encoding = tiktoken.encoding_for_model("text-embedding-ada-002")  # Close approximation
        self.max_tokens = 8191  # Max tokens for embedding model
    
    async def embed(self, text: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embeddings for text or list of texts.
        Supports multilingual text automatically.
        """
        try:
            # Ensure text is a list
            texts = [text] if isinstance(text, str) else text
            
            # Truncate texts if too long
            truncated_texts = [self._truncate_text(t) for t in texts]
            
            # Generate embeddings
            response = await self.client.embeddings.create(
                model=self.model,
                input=truncated_texts,
                dimensions=self.dimension  # Using full dimensions for better quality
            )
            
            # Extract embeddings
            embeddings = [np.array(item.embedding) for item in response.data]
            
            # Return single embedding or list based on input
            return embeddings[0] if isinstance(text, str) else embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Return zero vector on error
            zero_embedding = np.zeros(self.dimension)
            return zero_embedding if isinstance(text, str) else [zero_embedding] * len(texts)
    
    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit within token limits"""
        try:
            tokens = self.encoding.encode(text)
            if len(tokens) > self.max_tokens:
                # Truncate and decode back to text
                truncated_tokens = tokens[:self.max_tokens]
                return self.encoding.decode(truncated_tokens)
            return text
        except Exception as e:
            logger.warning(f"Error truncating text: {e}")
            # Fallback to character-based truncation
            max_chars = self.max_tokens * 4  # Rough approximation
            return text[:max_chars]
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[np.ndarray]:
        """
        Embed multiple texts in batches for efficiency.
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.embed(batch)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        return np.dot(embedding1, embedding2) / (norm1 * norm2)
    
    async def find_most_similar(
        self, 
        query_embedding: np.ndarray, 
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[tuple[int, float]]:
        """
        Find the most similar embeddings to a query embedding.
        
        Returns:
            List of tuples (index, similarity_score) sorted by similarity
        """
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            sim = self.similarity(query_embedding, candidate)
            similarities.append((i, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]