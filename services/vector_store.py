import faiss
import numpy as np
from typing import List, Dict, Optional, Any
import pickle
import os
import logging
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging_config import setup_logging

logger = setup_logging('vector_store')

class FAISSVectorStore:
    def __init__(self, dimension: int = 1536, index_type: str = "flat"):
        """
        Initialize FAISS vector store.
        
        Args:
            dimension: Dimension of embeddings
            index_type: Type of FAISS index ("flat", "ivf", "hnsw")
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.documents = []  # Store associated documents
        self.metadata = []   # Store metadata for each vector
        
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize FAISS index based on type"""
        if self.index_type == "flat":
            # Exact search - good for demo purposes
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "ivf":
            # Inverted file index - faster for large datasets
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        elif self.index_type == "hnsw":
            # Hierarchical Navigable Small World - very fast approximate search
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        
        logger.info(f"Initialized FAISS {self.index_type} index with dimension {self.dimension}")
    
    def add(self, embeddings: np.ndarray, documents: List[str], metadata: Optional[List[Dict]] = None):
        """
        Add embeddings and associated documents to the index.
        
        Args:
            embeddings: Numpy array of shape (n_samples, dimension)
            documents: List of document strings
            metadata: Optional list of metadata dicts
        """
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} doesn't match index dimension {self.dimension}")
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype(np.float32)
        
        # Train index if needed (for IVF)
        if self.index_type == "ivf" and not self.index.is_trained:
            logger.info("Training IVF index...")
            self.index.train(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store documents and metadata
        self.documents.extend(documents)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))
        
        logger.info(f"Added {len(documents)} documents to index. Total: {len(self.documents)}")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for the k most similar documents.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of dicts with 'content', 'score', and 'metadata'
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        # Ensure query is the right shape and type
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype(np.float32)
        
        # Limit k to the number of indexed documents
        k = min(k, self.index.ntotal)
        
        # Search
        distances, indices = self.index.search(query_embedding, k)
        
        # Prepare results
        results = []
        for i in range(k):
            idx = indices[0][i]
            if idx >= 0:  # Valid index
                results.append({
                    "content": self.documents[idx],
                    "score": float(distances[0][i]),
                    "metadata": self.metadata[idx],
                    "index": idx
                })
        
        return results
    
    def remove(self, indices: List[int]):
        """
        Remove documents by their indices.
        Note: This rebuilds the entire index, so use sparingly.
        """
        if not indices:
            return
        
        # Get all embeddings
        all_embeddings = []
        for i in range(self.index.ntotal):
            embedding = self.index.reconstruct(i)
            all_embeddings.append(embedding)
        
        # Remove specified indices
        indices_set = set(indices)
        new_embeddings = []
        new_documents = []
        new_metadata = []
        
        for i, (emb, doc, meta) in enumerate(zip(all_embeddings, self.documents, self.metadata)):
            if i not in indices_set:
                new_embeddings.append(emb)
                new_documents.append(doc)
                new_metadata.append(meta)
        
        # Rebuild index
        self._initialize_index()
        if new_embeddings:
            self.add(np.array(new_embeddings), new_documents, new_metadata)
        else:
            self.documents = []
            self.metadata = []
    
    def save(self, path: str):
        """Save index and associated data to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{path}.index")
        
        # Save documents and metadata
        with open(f"{path}.data", "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata,
                "dimension": self.dimension,
                "index_type": self.index_type
            }, f)
        
        logger.info(f"Saved index to {path}")
    
    def load(self, path: str):
        """Load index and associated data from disk"""
        # Load FAISS index
        self.index = faiss.read_index(f"{path}.index")
        
        # Load documents and metadata
        with open(f"{path}.data", "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.metadata = data["metadata"]
            self.dimension = data["dimension"]
            self.index_type = data["index_type"]
        
        logger.info(f"Loaded index from {path} with {len(self.documents)} documents")
    
    def clear(self):
        """Clear all data from the index"""
        self._initialize_index()
        self.documents = []
        self.metadata = []
        logger.info("Cleared vector store")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            "total_documents": len(self.documents),
            "index_type": self.index_type,
            "dimension": self.dimension,
            "index_size": self.index.ntotal if self.index else 0,
            "is_trained": self.index.is_trained if hasattr(self.index, "is_trained") else True
        }
    
    # Demo-specific methods for populating with sample data
    def add_sample_travel_data(self):
        """Add sample travel-related documents for demo purposes"""
        sample_docs = [
            {
                "content": "When booking international flights, it's often cheaper to book on Tuesdays and Wednesdays. Airlines typically release deals on Monday evenings.",
                "metadata": {"category": "booking_tips", "language": "en"}
            },
            {
                "content": "Para vuelos internacionales, es recomendable llegar al aeropuerto al menos 3 horas antes. Para vuelos domésticos, 2 horas es suficiente.",
                "metadata": {"category": "travel_tips", "language": "es"}
            },
            {
                "content": "Les meilleures périodes pour voyager en Europe sont le printemps (avril-mai) et l'automne (septembre-octobre) pour éviter les foules.",
                "metadata": {"category": "travel_seasons", "language": "fr"}
            },
            {
                "content": "Budget airlines often charge extra for carry-on bags, seat selection, and even water. Factor these costs when comparing prices.",
                "metadata": {"category": "budget_travel", "language": "en"}
            },
            {
                "content": "日本への旅行では、JRパスを購入すると新幹線が乗り放題になり、個別にチケットを買うよりもお得です。",
                "metadata": {"category": "travel_tips", "language": "ja"}
            },
            {
                "content": "Bei Flugverspätungen von über 3 Stunden haben Sie in der EU Anspruch auf Entschädigung zwischen 250-600 Euro.",
                "metadata": {"category": "passenger_rights", "language": "de"}
            },
            {
                "content": "The best way to find cheap flights is to be flexible with your dates. Use fare comparison tools and set up price alerts.",
                "metadata": {"category": "booking_tips", "language": "en"}
            },
            {
                "content": "Always check visa requirements before booking international flights. Some countries require visas to be obtained weeks in advance.",
                "metadata": {"category": "travel_documents", "language": "en"}
            }
        ]
        
        # Return sample docs for embedding
        return sample_docs