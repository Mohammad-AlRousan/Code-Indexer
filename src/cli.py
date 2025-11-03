"""
Command-line interface for code indexer
Provides commands: index, search, map, stats, clear
"""

import click
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

from indexer import TreeSitterIndexer
from embeddings import AzureEmbeddingsService
from cache import IndexCache


# Load environment variables
load_dotenv()


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    Code Indexer - Fast semantic code search using Tree-sitter and Azure OpenAI
    
    Index your codebase once, search semantically forever.
    """
    pass


@cli.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
@click.option('--with-embeddings/--no-embeddings', default=True,
              help='Generate Azure OpenAI embeddings for semantic search')
@click.option('--cache-dir', default='.code_index_cache',
              help='Directory to store cache')
@click.option('--ignore-patterns', '-i', multiple=True,
              help='Additional patterns to ignore (e.g., test_*.py)')
@click.option('--force', '-f', is_flag=True,
              help='Force re-indexing even if files unchanged')
def index(directory: str, with_embeddings: bool, cache_dir: str, 
          ignore_patterns: tuple, force: bool):
    """
    Index a directory of code files
    
    Example:
        code-indexer index ./my-project --with-embeddings
    """
    click.echo(f"🔍 Indexing {directory}...")
    
    # Initialize cache
    cache = IndexCache(cache_dir)
    
    # Get ignore patterns from environment + CLI
    env_ignore = os.getenv('CODE_INDEXER_IGNORE_PATTERNS', '').split(',')
    all_ignore_patterns = [p.strip() for p in env_ignore if p.strip()] + list(ignore_patterns)
    
    # Initialize indexer
    indexer = TreeSitterIndexer()
    
    # Index directory
    click.echo("📁 Scanning files...")
    result = indexer.index_directory(
        directory, 
        ignore_patterns=all_ignore_patterns
    )
    
    if not result or 'index' not in result:
        click.echo("❌ No files to index", err=True)
        return
    
    index_result = result['index']
    stats = result['stats']
    
    # Show stats
    click.echo(f"✅ Indexed {stats['files_indexed']} files, {stats['total_definitions']} definitions")
    
    if stats['errors']:
        click.echo(f"⚠️  {len(stats['errors'])} errors occurred")
        for error in stats['errors'][:3]:  # Show first 3 errors
            click.echo(f"   {error}", err=True)
    
    # Save to cache
    click.echo("💾 Saving to cache...")
    for file_path, file_data in index_result.items():
        cache.save_file_index(file_path, file_data['hash'], file_data)
    
    # Generate embeddings if requested
    if with_embeddings:
        click.echo("🤖 Generating embeddings with Azure OpenAI...")
        
        # Check for required environment variables
        if not os.getenv('AZURE_OPENAI_ENDPOINT'):
            click.echo("❌ AZURE_OPENAI_ENDPOINT not set", err=True)
            return
        
        if not os.getenv('AZURE_OPENAI_API_KEY'):
            click.echo("❌ AZURE_OPENAI_API_KEY not set", err=True)
            return
        
        # Initialize embeddings service
        embeddings_service = AzureEmbeddingsService(
            endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            deployment_name=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
        )
        
        # Embed the entire index
        try:
            click.echo("Generating embeddings for all definitions...")
            embedded_result = embeddings_service.embed_index(result)
            embedded_index = embedded_result.get('index', {})
            
            # Save embeddings to cache
            for file_path, file_data in embedded_index.items():
                definitions = file_data.get('definitions', [])
                if definitions:
                    cache.save_embeddings(file_path, definitions)
        except Exception as e:
            import traceback
            click.echo(f"\n⚠️  Error embedding: {e}", err=True)
            click.echo(traceback.format_exc(), err=True)
        
        click.echo("✅ Embeddings generated and cached")
    
    # Save metadata
    cache.set_metadata('last_index_directory', directory)
    cache.set_metadata('index_with_embeddings', str(with_embeddings))
    
    # Show stats
    stats = cache.get_stats()
    click.echo(f"\n📊 Cache stats:")
    click.echo(f"   Files: {stats['cached_files']}")
    click.echo(f"   Definitions: {stats['total_definitions']}")
    click.echo(f"   Embeddings: {stats['total_embeddings']}")
    click.echo(f"   Cache size: {stats['db_size_mb']:.2f} MB")


@cli.command()
@click.argument('query')
@click.option('--top-k', '-k', default=10, help='Number of results to return')
@click.option('--threshold', '-t', default=0.7, help='Similarity threshold (0-1)')
@click.option('--cache-dir', default='.code_index_cache', help='Cache directory')
@click.option('--type', '-T', multiple=True, 
              help='Filter by definition type (function, class, method)')
@click.option('--file-pattern', '-f', help='Filter by file pattern (e.g., *.py)')
def search(query: str, top_k: int, threshold: float, cache_dir: str,
           type: tuple, file_pattern: Optional[str]):
    """
    Search code semantically using natural language
    
    Example:
        code-indexer search "function that parses JSON"
        code-indexer search "HTTP request handler" --top-k 5
    """
    click.echo(f"🔎 Searching for: {query}")
    
    # Initialize cache
    cache = IndexCache(cache_dir)
    
    # Check cache has embeddings
    stats = cache.get_stats()
    if stats['total_embeddings'] == 0:
        click.echo("❌ No embeddings in cache. Run 'index' first with --with-embeddings", err=True)
        return
    
    # Initialize embeddings service
    if not os.getenv('AZURE_OPENAI_ENDPOINT'):
        click.echo("❌ AZURE_OPENAI_ENDPOINT not set", err=True)
        return
    
    embeddings_service = AzureEmbeddingsService(
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        deployment_name=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
    )
    
    # Generate query embedding
    click.echo("🤖 Generating query embedding...")
    try:
        query_embedding = embeddings_service.generate_embedding(query)
    except Exception as e:
        click.echo(f"❌ Error generating embedding: {e}", err=True)
        return
    
    # Get all cached embeddings
    click.echo("🔍 Searching cache...")
    
    # This is simplified - in production, you'd want to use a vector database
    # For now, load all embeddings and compute similarity
    import sqlite3
    import pickle
    import numpy as np
    
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    
    # Build query
    sql = 'SELECT file_path, definition_name, definition_type, signature_text, embedding FROM embeddings'
    conditions = []
    params = []
    
    if type:
        placeholders = ','.join(['?'] * len(type))
        conditions.append(f'definition_type IN ({placeholders})')
        params.extend(type)
    
    if file_pattern:
        conditions.append('file_path LIKE ?')
        params.append(file_pattern.replace('*', '%'))
    
    if conditions:
        sql += ' WHERE ' + ' AND '.join(conditions)
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Compute similarities
    results = []
    for row in rows:
        file_path, name, dtype, signature, embedding_blob = row
        
        # Deserialize embedding safely using numpy
        try:
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
        except:
            continue
        # Compute similarity
        similarity = embeddings_service.cosine_similarity(query_embedding, embedding)
        
        if similarity >= threshold:
            results.append({
                'file': file_path,
                'name': name,
                'type': dtype,
                'signature': signature,
                'similarity': similarity
            })
    
    # Sort by similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)
    results = results[:top_k]
    
    # Display results
    if not results:
        click.echo(f"❌ No results found (threshold={threshold})")
        return
    
    click.echo(f"\n✅ Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        click.echo(f"{i}. {result['name']} ({result['type']}) - {result['similarity']:.3f}")
        click.echo(f"   📁 {result['file']}")
        click.echo(f"   📝 {result['signature']}")
        click.echo()


@cli.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
@click.option('--cache-dir', default='.code_index_cache', help='Cache directory')
@click.option('--output', '-o', type=click.File('w'), default='-',
              help='Output file (default: stdout)')
def map(directory: str, cache_dir: str, output):
    """
    Generate a human-readable map of the codebase (Plandex style)
    
    Example:
        code-indexer map ./my-project
        code-indexer map ./src --output map.txt
    """
    # Initialize
    cache = IndexCache(cache_dir)
    indexer = TreeSitterIndexer()
    
    # Check if directory is indexed
    stats = cache.get_stats()
    if stats['cached_files'] == 0:
        click.echo("⚠️  No cached index. Indexing now...", err=True)
        # Run indexing
        result = indexer.index_directory(directory)
    else:
        # Load from cache
        click.echo("📂 Loading from cache...")
        import sqlite3
        
        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path, index_data FROM file_index')
        rows = cursor.fetchall()
        conn.close()
        
        import json
        index = {}
        for file_path, index_data_json in rows:
            try:
                index[file_path] = json.loads(index_data_json)
            except:
                continue
        
        result = {'index': index}
    
    # Generate map string
    map_string = indexer.create_map_string(result)
    
    # Write to output
    output.write(map_string)
    
    if output.name != '<stdout>':
        click.echo(f"✅ Map saved to {output.name}")


@cli.command()
@click.option('--cache-dir', default='.code_index_cache', help='Cache directory')
def stats(cache_dir: str):
    """Show cache statistics"""
    cache = IndexCache(cache_dir)
    stats = cache.get_stats()
    
    click.echo("\n📊 Code Index Statistics\n")
    click.echo(f"Cache directory: {stats['cache_dir']}")
    click.echo(f"Cache size: {stats['db_size_mb']:.2f} MB")
    click.echo(f"Cached files: {stats['cached_files']}")
    click.echo(f"Total definitions: {stats['total_definitions']}")
    click.echo(f"Total embeddings: {stats['total_embeddings']}")
    
    # Get metadata
    last_dir = cache.get_metadata('last_index_directory')
    with_embeddings = cache.get_metadata('index_with_embeddings')
    
    if last_dir:
        click.echo(f"\nLast indexed directory: {last_dir}")
    if with_embeddings:
        click.echo(f"Embeddings enabled: {with_embeddings}")


@cli.command()
@click.option('--cache-dir', default='.code_index_cache', help='Cache directory')
@click.confirmation_option(prompt='Are you sure you want to clear the cache?')
def clear(cache_dir: str):
    """Clear the index cache"""
    cache = IndexCache(cache_dir)
    cache.clear_cache()
    click.echo("✅ Cache cleared")


if __name__ == '__main__':
    cli()
