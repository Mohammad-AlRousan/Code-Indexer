# 📊 Embedding Storage & Flow - Complete Guide

## Where Embeddings Are Stored

### Storage Location
```
.code_index_cache/
└── index.db (SQLite database - currently 1.5 MB)
```

### Database Schema

The SQLite database has **3 main tables**:

#### 1. `file_index` Table
Stores indexed code signatures (without embeddings)
```sql
CREATE TABLE file_index (
    file_path TEXT PRIMARY KEY,
    file_hash TEXT NOT NULL,           -- SHA256 hash for cache invalidation
    language TEXT,                     -- python, javascript, etc.
    index_data TEXT,                   -- JSON: all function/class signatures
    indexed_at TIMESTAMP,
    num_definitions INTEGER
)
```

#### 2. `embeddings` Table ⭐ **This is where embeddings live!**
```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,           -- Which file
    definition_name TEXT,              -- Function/class name (e.g., "calculate_total")
    definition_type TEXT,              -- "function", "class", "method"
    signature_text TEXT,               -- The code signature
    embedding BLOB,                    -- ⭐ PICKLED NUMPY ARRAY (1536 floats)
    embedding_dim INTEGER,             -- 1536 (text-embedding-ada-002)
    created_at TIMESTAMP
)
```

**Current State**: 102 embeddings stored, each ~13,842 bytes

#### 3. `metadata` Table
```sql
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
)
```
Stores: last indexed directory, whether embeddings enabled, etc.

---

## 🔄 Complete Flow: OpenAI Embedding Call

### Phase 1: Indexing with Embeddings

```
User runs:
python src/cli.py index . --with-embeddings
│
├─► STEP 1: Parse Code (Tree-sitter)
│   ├─ src/indexer.py: TreeSitterIndexer.index_directory()
│   ├─ Extracts signatures: "def calculate_total(items: list) -> float"
│   └─ Result: {'index': {filepath: {definitions: [...]}}}
│
├─► STEP 2: Generate Embeddings (Azure OpenAI)
│   ├─ src/embeddings.py: AzureEmbeddingsService.embed_index()
│   │
│   ├─ For each definition:
│   │   ├─ Create rich text: "function calculate_total: def calculate_total(items: list) -> float in sample.py"
│   │   └─ Add to batch (max 16 items)
│   │
│   ├─ Call Azure OpenAI API:
│   │   ┌─────────────────────────────────────────┐
│   │   │  🌐 HTTPS POST REQUEST                  │
│   │   │  Endpoint: YourOpenAIResource.openai.azure.com│
│   │   │  Model: text-embedding-ada-002          │
│   │   │  Input: ["function calculate...",       │
│   │   │          "class ShoppingCart...", ...]  │
│   │   └─────────────────────────────────────────┘
│   │                     ↓
│   │   ┌─────────────────────────────────────────┐
│   │   │  ✅ RESPONSE FROM AZURE OPENAI          │
│   │   │  {                                      │
│   │   │    "data": [                            │
│   │   │      {                                  │
│   │   │        "embedding": [0.123, -0.456,     │
│   │   │                      0.789, ...]        │
│   │   │        // 1536 float values             │
│   │   │      },                                 │
│   │   │      ...                                │
│   │   │    ]                                    │
│   │   │  }                                      │
│   │   └─────────────────────────────────────────┘
│   │
│   └─ Returns: List of 1536-dimensional vectors
│
└─► STEP 3: Save to SQLite Cache
    ├─ src/cache.py: IndexCache.save_embeddings()
    │
    ├─ For each definition with embedding:
    │   ├─ Pickle the embedding array: pickle.dumps([0.123, -0.456, ...])
    │   │  // Converts Python list to binary blob (~13,842 bytes)
    │   │
    │   └─ INSERT INTO embeddings:
    │       ├─ file_path: "sample.py"
    │       ├─ definition_name: "calculate_total"
    │       ├─ definition_type: "function"
    │       ├─ signature_text: "def calculate_total(items: list) -> float"
    │       ├─ embedding: <13KB binary blob>
    │       └─ embedding_dim: 1536
    │
    └─ ✅ Saved to .code_index_cache/index.db
```

### Phase 2: Semantic Search

```
User runs:
python src/cli.py search "calculate average" --top-k 3
│
├─► STEP 1: Generate Query Embedding
│   ├─ src/embeddings.py: generate_embedding("calculate average")
│   │
│   ├─ Call Azure OpenAI API:
│   │   ┌─────────────────────────────────────────┐
│   │   │  🌐 HTTPS POST REQUEST                  │
│   │   │  Input: "calculate average"             │
│   │   └─────────────────────────────────────────┘
│   │                     ↓
│   │   ┌─────────────────────────────────────────┐
│   │   │  ✅ RESPONSE                            │
│   │   │  embedding: [0.234, -0.567, 0.891, ...] │
│   │   │  // 1536 floats                         │
│   │   └─────────────────────────────────────────┘
│   │
│   └─ Query vector: [0.234, -0.567, ...]
│
├─► STEP 2: Load Cached Embeddings
│   ├─ src/cache.py: get_all_embeddings()
│   │
│   ├─ SELECT * FROM embeddings
│   │   // Gets all 102 embeddings from database
│   │
│   ├─ For each row:
│   │   └─ Unpickle blob: pickle.loads(embedding_blob)
│   │       // Converts binary back to [float, float, ...]
│   │
│   └─ Result: 102 definitions with embeddings
│
├─► STEP 3: Calculate Similarity (CPU - No API Call)
│   ├─ src/embeddings.py: cosine_similarity()
│   │
│   ├─ For each cached embedding:
│   │   ├─ Compute: dot(query_vec, cached_vec) / (norm(query) * norm(cached))
│   │   └─ Example: 0.746 for "calculate_total"
│   │
│   └─ Sort by similarity score
│
└─► STEP 4: Return Top Results
    └─ ✅ Top 3 most similar definitions
```

---

## 💾 Storage Details

### Embedding Data Format

**In Memory (Python)**:
```python
embedding = [0.123, -0.456, 0.789, ..., 0.321]  # 1536 floats
```

**In Database (SQLite)**:
```python
# Before storage
embedding_blob = pickle.dumps(embedding)
# Result: b'\x80\x04\x95...' (13,842 bytes binary)

# On retrieval
embedding = pickle.loads(embedding_blob)
# Result: [0.123, -0.456, 0.789, ..., 0.321]
```

### Storage Efficiency

| Item | Size |
|------|------|
| 1 embedding (1536 floats) | ~13,842 bytes (~13.5 KB) |
| 102 embeddings | ~1.4 MB |
| Full database | 1.5 MB |

**Calculation**: 1536 floats × 8 bytes/float + pickle overhead = ~13.8 KB

---

## 🔍 API Call Summary

### When API Calls Happen

| Operation | API Calls | Location |
|-----------|-----------|----------|
| **Index with embeddings** | ✅ YES - Batch calls (16 items/call) | `embed_index()` |
| **Search** | ✅ YES - 1 call for query | `generate_embedding()` |
| **Similarity calculation** | ❌ NO - Local CPU | `cosine_similarity()` |
| **Load from cache** | ❌ NO - SQLite read | `get_all_embeddings()` |
| **Map generation** | ❌ NO - Uses cached data | `create_map_string()` |

### API Call Examples

#### 1. Initial Indexing (6 files, 60 definitions)
```
Batch 1: 16 definitions → 1 API call
Batch 2: 16 definitions → 1 API call
Batch 3: 16 definitions → 1 API call
Batch 4: 12 definitions → 1 API call
Total: 4 API calls for 60 embeddings
```

#### 2. Search Query
```
Query: "calculate average"
Total: 1 API call (generates query embedding)
Then: 102 local cosine similarity calculations (no API)
```

#### 3. Re-indexing (Cache Hit)
```
File unchanged (hash matches)
→ Load from cache
→ 0 API calls! ✅
```

---

## 🚀 Performance Optimization

### Caching Strategy

```python
def index_file_with_cache(file_path):
    # 1. Calculate file hash
    file_hash = hashlib.sha256(content).hexdigest()
    
    # 2. Check cache
    cached = cache.get_file_index(file_path, file_hash)
    if cached:
        return cached  # ✅ No API call needed!
    
    # 3. File changed - re-index
    index = indexer.index_file(file_path)
    
    # 4. Generate embeddings (API call)
    embeddings = service.embed_code_definitions(index)
    
    # 5. Save to cache
    cache.save_embeddings(file_path, embeddings)
```

### Batch Processing

```python
# ❌ BAD: 60 API calls
for definition in definitions:
    embedding = generate_embedding(definition)  # 1 call each

# ✅ GOOD: 4 API calls (60 / 16 batch size)
embeddings = generate_embeddings_batch(definitions)  # 16 at a time
```

---

## 📊 Real Example from Your Database

```sql
-- Sample row from embeddings table
id: 1
file_path: "sample.js"
definition_name: "validateInput"
definition_type: "function"
signature_text: "function validateInput(data)"
embedding: <binary blob 13,842 bytes>
    ↓ (unpickled)
    [0.0234, -0.0156, 0.0178, ..., 0.0091]  -- 1536 floats
embedding_dim: 1536
created_at: "2025-11-03T10:26:15.123456"
```

---

## 🎯 Key Takeaways

1. **Storage**: SQLite database at `.code_index_cache/index.db`
2. **Format**: Embeddings stored as pickled blobs (binary)
3. **Size**: ~13.8 KB per embedding (1536 floats)
4. **API Calls**: 
   - Indexing: ~1 call per 16 definitions (batch)
   - Search: 1 call per query
   - Similarity: 0 calls (local CPU)
5. **Caching**: Hash-based - unchanged files = 0 API calls
6. **Efficiency**: 96% token reduction vs sending full files

**The system is designed for minimal API usage and maximum speed through aggressive caching!** 🚀
