"""
Caching system for code index
Stores indexed code and embeddings to avoid re-processing unchanged files
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import pickle


class IndexCache:
    """
    SQLite-based cache for code index and embeddings
    Following best practices: hash-based invalidation, efficient storage
    """
    
    def __init__(self, cache_dir: str = '.code_index_cache'):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory to store cache database
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.db_path = self.cache_dir / 'index.db'
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for file index cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_index (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                language TEXT,
                index_data TEXT,  -- JSON
                indexed_at TIMESTAMP,
                num_definitions INTEGER
            )
        ''')
        
        # Table for embeddings cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                definition_name TEXT,
                definition_type TEXT,
                signature_text TEXT,
                embedding BLOB,  -- Pickled numpy array or list
                embedding_dim INTEGER,
                created_at TIMESTAMP
            )
        ''')
        
        # Table for project-level metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP
            )
        ''')
        
        # Indices for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_file_hash 
            ON file_index(file_hash)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_embeddings_file 
            ON embeddings(file_path)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_file_index(self, file_path: str, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get cached index for a file if hash matches
        
        Args:
            file_path: Path to file
            file_hash: Current SHA256 hash of file
            
        Returns:
            Cached index data or None if not found or hash mismatch
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_hash, index_data
            FROM file_index
            WHERE file_path = ?
        ''', (file_path,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        cached_hash, index_data_json = row
        
        # Check if hash matches (file unchanged)
        if cached_hash != file_hash:
            return None
        
        # Parse JSON
        try:
            return json.loads(index_data_json)
        except:
            return None
    
    def save_file_index(self, file_path: str, file_hash: str, index_data: Dict[str, Any]):
        """
        Save file index to cache
        
        Args:
            file_path: Path to file
            file_hash: SHA256 hash of file
            index_data: Index data from TreeSitterIndexer
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO file_index
            (file_path, file_hash, language, index_data, indexed_at, num_definitions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            file_path,
            file_hash,
            index_data.get('language'),
            json.dumps(index_data),
            datetime.now().isoformat(),
            index_data.get('num_definitions', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def get_embeddings(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get all cached embeddings for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            List of embedding records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT definition_name, definition_type, signature_text, 
                   embedding, embedding_dim
            FROM embeddings
            WHERE file_path = ?
        ''', (file_path,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            name, dtype, signature, embedding_blob, dim = row
            
            # Unpickle embedding
            try:
                embedding = pickle.loads(embedding_blob) if embedding_blob else None
            except:
                embedding = None
            
            results.append({
                'name': name,
                'type': dtype,
                'signature': signature,
                'embedding': embedding,
                'embedding_dim': dim
            })
        
        return results
    
    def save_embeddings(self, file_path: str, definitions: List[Dict[str, Any]]):
        """
        Save embeddings for file definitions
        
        Args:
            file_path: Path to file
            definitions: List of definitions with 'embedding' field
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing embeddings for this file
        cursor.execute('DELETE FROM embeddings WHERE file_path = ?', (file_path,))
        
        # Insert new embeddings
        for defn in definitions:
            embedding = defn.get('embedding')
            if not embedding:
                continue
            
            # Pickle the embedding
            embedding_blob = pickle.dumps(embedding)
            
            cursor.execute('''
                INSERT INTO embeddings
                (file_path, definition_name, definition_type, signature_text, 
                 embedding, embedding_dim, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_path,
                defn.get('name', ''),
                defn.get('type', ''),
                defn.get('signature', ''),
                embedding_blob,
                len(embedding),
                datetime.now().isoformat()
            ))
            
            # Also save children embeddings
            for child in defn.get('children', []):
                child_embedding = child.get('embedding')
                if child_embedding:
                    cursor.execute('''
                        INSERT INTO embeddings
                        (file_path, definition_name, definition_type, signature_text,
                         embedding, embedding_dim, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        file_path,
                        child.get('name', ''),
                        child.get('type', ''),
                        child.get('signature', ''),
                        pickle.dumps(child_embedding),
                        len(child_embedding),
                        datetime.now().isoformat()
                    ))
        
        conn.commit()
        conn.close()
    
    def delete_file(self, file_path: str):
        """
        Remove file from cache (when deleted or moved)
        
        Args:
            file_path: Path to file
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM file_index WHERE file_path = ?', (file_path,))
        cursor.execute('DELETE FROM embeddings WHERE file_path = ?', (file_path,))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM file_index')
        num_files = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(num_definitions) FROM file_index')
        total_definitions = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        num_embeddings = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'cached_files': num_files,
            'total_definitions': total_definitions,
            'total_embeddings': num_embeddings,
            'cache_dir': str(self.cache_dir),
            'db_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM file_index')
        cursor.execute('DELETE FROM embeddings')
        cursor.execute('DELETE FROM metadata')
        
        conn.commit()
        conn.close()
    
    def set_metadata(self, key: str, value: str):
        """Store project-level metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_metadata(self, key: str) -> Optional[str]:
        """Retrieve project-level metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM metadata WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        conn.close()
        
        return row[0] if row else None
