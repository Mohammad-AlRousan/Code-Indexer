"""
Code Indexer API Server for Aider Integration

Provides REST API for semantic search and indexing
Can be called from Aider plugins, scripts, or other tools

Usage:
    python api_server.py --port 8080
    
API Endpoints:
    POST /search       - Semantic search
    POST /index        - Index directory
    GET  /map          - Get codebase map
    GET  /stats        - Get cache stats
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import click
import os
from pathlib import Path

# Import Code Indexer components
import sys
sys.path.insert(0, str(Path(__file__).parent))
from indexer import TreeSitterIndexer
from embeddings import AzureEmbeddingsService
from cache import IndexCache


app = Flask(__name__)
CORS(app)

# Global instances
cache = None
indexer = None
embeddings_service = None


def init_services(cache_dir: str = '.code_index_cache'):
    """Initialize indexer, cache, and embeddings service"""
    global cache, indexer, embeddings_service
    
    cache = IndexCache(cache_dir)
    indexer = TreeSitterIndexer()
    
    if os.getenv('AZURE_OPENAI_ENDPOINT'):
        embeddings_service = AzureEmbeddingsService(
            endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            deployment_name=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
        )


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'embeddings_enabled': embeddings_service is not None
    })


@app.route('/search', methods=['POST'])
def search():
    """
    Semantic search endpoint
    
    Body:
        {
            "query": "search query",
            "top_k": 10,
            "threshold": 0.7,
            "type_filter": ["function", "class"],
            "file_pattern": "*.py"
        }
    """
    data = request.json
    query = data.get('query')
    top_k = data.get('top_k', 10)
    threshold = data.get('threshold', 0.7)
    type_filter = data.get('type_filter', [])
    file_pattern = data.get('file_pattern')
    
    if not query:
        return jsonify({'error': 'query is required'}), 400
    
    if not embeddings_service:
        return jsonify({'error': 'Azure OpenAI not configured'}), 500
    
    try:
        # Generate query embedding
        query_embedding = embeddings_service.generate_embedding(query)
        
        # Get all cached embeddings
        all_embeddings = cache.get_all_embeddings()
        
        if not all_embeddings:
            return jsonify({'error': 'No embeddings in cache'}), 404
        
        # Compute similarities
        from scipy.spatial.distance import cosine
        results = []
        
        for file_path, def_name, def_type, signature, embedding in all_embeddings:
            similarity = 1 - cosine(query_embedding, embedding)
            
            if similarity >= threshold:
                # Apply filters
                if type_filter and def_type not in type_filter:
                    continue
                if file_pattern and not Path(file_path).match(file_pattern):
                    continue
                
                results.append({
                    'file_path': file_path,
                    'name': def_name,
                    'type': def_type,
                    'signature': signature,
                    'similarity': float(similarity)
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:top_k]
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/index', methods=['POST'])
def index_directory():
    """
    Index directory endpoint
    
    Body:
        {
            "directory": ".",
            "with_embeddings": true,
            "force": false,
            "ignore_patterns": ["test_*.py"]
        }
    """
    data = request.json
    directory = data.get('directory', '.')
    with_embeddings = data.get('with_embeddings', True)
    force = data.get('force', False)
    ignore_patterns = data.get('ignore_patterns', [])
    
    try:
        # Index directory
        result = indexer.index_directory(
            directory,
            ignore_patterns=ignore_patterns if ignore_patterns else None
        )
        
        # Save to cache
        for file_path, file_data in result['index'].items():
            if force or not cache.is_file_cached(file_path, file_data['hash']):
                cache.save_file_index(file_path, file_data['hash'], file_data)
        
        # Generate embeddings if requested
        if with_embeddings and embeddings_service:
            embeddings_service.embed_index(cache, result['index'])
        
        return jsonify({
            'success': True,
            'files_indexed': result['files_indexed'],
            'definitions_found': result['definitions_found'],
            'with_embeddings': with_embeddings and embeddings_service is not None
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/map', methods=['GET'])
def get_map():
    """
    Get codebase map
    
    Query params:
        ?directory=.
    """
    directory = request.args.get('directory', '.')
    
    try:
        # Load from cache or index
        import sqlite3
        import json
        
        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path, index_data FROM file_index')
        rows = cursor.fetchall()
        conn.close()
        
        index = {}
        for file_path, index_data_json in rows:
            try:
                index[file_path] = json.loads(index_data_json)
            except:
                continue
        
        result = {'index': index}
        map_string = indexer.create_map_string(result)
        
        return jsonify({
            'map': map_string,
            'files': len(index)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get cache statistics"""
    try:
        stats = cache.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@click.command()
@click.option('--port', '-p', default=8080, help='Port to run server on')
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind to')
@click.option('--cache-dir', default='.code_index_cache', help='Cache directory')
def main(port: int, host: str, cache_dir: str):
    """Run Code Indexer API server"""
    from dotenv import load_dotenv
    load_dotenv()
    
    click.echo(f"🚀 Starting Code Indexer API server on {host}:{port}")
    
    # Initialize services
    init_services(cache_dir)
    
    click.echo("✅ Services initialized")
    click.echo(f"📊 Cache directory: {cache_dir}")
    click.echo(f"🤖 Azure OpenAI: {'Enabled' if embeddings_service else 'Disabled'}")
    click.echo("")
    
    # Run server
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()
