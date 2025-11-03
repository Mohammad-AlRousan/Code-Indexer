"""
Azure OpenAI Embeddings Integration
Generates vector embeddings for code signatures using Azure OpenAI
"""

import os
from typing import List, Dict, Any, Optional
import time
import numpy as np

try:
    from openai import AzureOpenAI
except ImportError:
    print("Warning: openai not installed. Run: pip install openai")
    AzureOpenAI = None


class AzureEmbeddingsService:
    """
    Service for generating embeddings using Azure OpenAI
    Following best practices for production use
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment_name: Optional[str] = None
    ):
        """
        Initialize Azure OpenAI client
        
        Args:
            endpoint: Azure OpenAI endpoint (or use AZURE_OPENAI_ENDPOINT env var)
            api_key: API key (or use AZURE_OPENAI_API_KEY env var)
            api_version: API version (or use AZURE_OPENAI_API_VERSION env var)
            deployment_name: Embedding model deployment name
        """
        if AzureOpenAI is None:
            raise ImportError("openai library not installed. Run: pip install openai")
        
        self.endpoint = endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = api_key or os.getenv('AZURE_OPENAI_API_KEY')
        self.api_version = api_version or os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
        self.deployment_name = deployment_name or os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
        
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OpenAI credentials not provided. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables "
                "or pass them as arguments."
            )
        
        # Initialize client
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        # Rate limiting
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        # Batch settings
        self.max_batch_size = 16  # Azure OpenAI recommended batch size
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return None
        
        # Truncate if too long (Azure OpenAI has token limits)
        max_chars = 8000  # Approximate limit
        if len(text) > max_chars:
            text = text[:max_chars]
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    input=text,
                    model=self.deployment_name
                )
                
                return response.data[0].embedding
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"Embedding API error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to generate embedding after {self.max_retries} attempts: {e}")
                    return None
        
        return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (same order as input)
        """
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            
            # Filter empty texts
            batch_filtered = [t for t in batch if t and t.strip()]
            
            if not batch_filtered:
                embeddings.extend([None] * len(batch))
                continue
            
            for attempt in range(self.max_retries):
                try:
                    response = self.client.embeddings.create(
                        input=batch_filtered,
                        model=self.deployment_name
                    )
                    
                    # Extract embeddings in order
                    batch_embeddings = [item.embedding for item in response.data]
                    
                    # Map back to original batch (accounting for filtered texts)
                    result_idx = 0
                    for text in batch:
                        if text and text.strip():
                            embeddings.append(batch_embeddings[result_idx])
                            result_idx += 1
                        else:
                            embeddings.append(None)
                    
                    break
                    
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        print(f"Batch embedding API error, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        print(f"Failed to generate batch embeddings: {e}")
                        embeddings.extend([None] * len(batch))
            
            # Rate limiting between batches
            if i + self.max_batch_size < len(texts):
                time.sleep(0.5)  # Small delay between batches
        
        return embeddings
    
    def embed_code_definitions(self, definitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add embeddings to code definitions
        
        Args:
            definitions: List of code definition dicts from indexer
            
        Returns:
            List of definitions with 'embedding' field added
        """
        # Prepare texts for embedding
        texts = []
        for defn in definitions:
            # Create rich text representation for better embeddings
            sig = defn.get('signature', '')
            name = defn.get('name', '')
            dtype = defn.get('type', '')
            file_path = defn.get('file_path', '')
            
            # Format: "type name signature in file"
            text = f"{dtype} {name}: {sig} in {file_path}"
            texts.append(text)
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} definitions...")
        embeddings = self.generate_embeddings_batch(texts)
        
        # Add embeddings to definitions
        enriched_definitions = []
        for defn, embedding in zip(definitions, embeddings):
            enriched = defn.copy()
            if embedding:
                enriched['embedding'] = embedding
                enriched['embedding_dim'] = len(embedding)
            else:
                enriched['embedding'] = None
            enriched_definitions.append(enriched)
        
        return enriched_definitions
    
    def embed_index(self, index_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add embeddings to entire index
        
        Args:
            index_result: Output from TreeSitterIndexer.index_directory()
            
        Returns:
            Index with embeddings added to all definitions
        """
        index = index_result.get('index', {})
        
        # Flatten all definitions
        all_definitions = []
        definition_locations = []  # Track where each definition came from
        
        for filepath, file_data in index.items():
            definitions = file_data.get('definitions', [])
            for defn in definitions:
                all_definitions.append(defn)
                definition_locations.append((filepath, defn))
                
                # Also process children (methods in classes)
                children = defn.get('children', [])
                for child in children:
                    all_definitions.append(child)
                    definition_locations.append((filepath, child))
        
        # Generate embeddings for all
        enriched = self.embed_code_definitions(all_definitions)
        
        # Put embeddings back into the index structure
        enriched_index = {}
        enriched_idx = 0
        
        for filepath, file_data in index.items():
            enriched_file = file_data.copy()
            enriched_definitions = []
            
            for defn in file_data.get('definitions', []):
                enriched_defn = enriched[enriched_idx].copy()
                enriched_idx += 1
                
                # Process children
                if defn.get('children'):
                    enriched_children = []
                    for child in defn['children']:
                        enriched_child = enriched[enriched_idx].copy()
                        enriched_idx += 1
                        enriched_children.append(enriched_child)
                    enriched_defn['children'] = enriched_children
                
                enriched_definitions.append(enriched_defn)
            
            enriched_file['definitions'] = enriched_definitions
            enriched_index[filepath] = enriched_file
        
        return {
            **index_result,
            'index': enriched_index,
            'embeddings_generated': True
        }
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_similar_definitions(
        self,
        query: str,
        index_with_embeddings: Dict[str, Any],
        top_k: int = 10,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find code definitions similar to a query using semantic search
        
        Args:
            query: Natural language query or code snippet
            index_with_embeddings: Index with embeddings from embed_index()
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
            
        Returns:
            List of definitions sorted by similarity score
        """
        # Generate embedding for query
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            print("Failed to generate query embedding")
            return []
        
        # Collect all definitions with embeddings
        all_definitions = []
        index = index_with_embeddings.get('index', {})
        
        for filepath, file_data in index.items():
            for defn in file_data.get('definitions', []):
                if defn.get('embedding'):
                    all_definitions.append(defn)
                
                # Include children
                for child in defn.get('children', []):
                    if child.get('embedding'):
                        all_definitions.append(child)
        
        # Calculate similarities
        results = []
        for defn in all_definitions:
            similarity = self.cosine_similarity(query_embedding, defn['embedding'])
            
            if similarity >= min_similarity:
                result = defn.copy()
                result['similarity_score'] = similarity
                results.append(result)
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:top_k]
