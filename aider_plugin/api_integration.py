"""
Aider plugin for Code-Indexer API integration

Uses REST API to communicate with Code-Indexer server

Installation:
1. Start API server: python src/api_server.py
2. Load this plugin in Aider

Usage:
    /api-search "authentication functions"
    /api-index --directory src/
"""

import requests
import json


class CodeIndexerAPIPlugin:
    """Integrate Code-Indexer via REST API"""
    
    def __init__(self, io, coder, api_url="http://127.0.0.1:8080"):
        self.io = io
        self.coder = coder
        self.api_url = api_url
    
    def cmd_api_search(self, args):
        """
        Search via API and add files to chat
        
        Usage: /api-search "query" [--top-k N]
        """
        # Parse args
        parts = args.split('--top-k')
        query = parts[0].strip().strip('"')
        top_k = int(parts[1].strip()) if len(parts) > 1 else 5
        
        try:
            # Call API
            response = requests.post(
                f"{self.api_url}/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "threshold": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data['results']
                
                self.io.tool_output(f"Found {data['total']} results:\n")
                
                for i, result in enumerate(results, 1):
                    self.io.tool_output(
                        f"{i}. {result['name']} ({result['type']}) - "
                        f"{result['similarity']:.3f}\n"
                        f"   📁 {result['file_path']}\n"
                        f"   📝 {result['signature']}\n"
                    )
                
                # Ask to add files
                file_paths = [r['file_path'] for r in results]
                for file_path in file_paths:
                    if self.io.confirm_ask(f"Add {file_path}?", default="y"):
                        self.coder.add_rel_fname(file_path)
                        self.io.tool_output(f"✅ Added {file_path}")
            else:
                self.io.tool_error(f"API error: {response.json()}")
        
        except requests.RequestException as e:
            self.io.tool_error(f"Failed to connect to API: {e}")
    
    def cmd_api_index(self, args):
        """
        Trigger re-indexing via API
        
        Usage: /api-index [--directory path]
        """
        directory = "."
        if "--directory" in args:
            directory = args.split("--directory")[1].strip()
        
        try:
            response = requests.post(
                f"{self.api_url}/index",
                json={
                    "directory": directory,
                    "with_embeddings": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.io.tool_output(
                    f"✅ Indexed {data['files_indexed']} files, "
                    f"{data['definitions_found']} definitions"
                )
            else:
                self.io.tool_error(f"API error: {response.json()}")
        
        except requests.RequestException as e:
            self.io.tool_error(f"Failed to connect to API: {e}")
    
    def cmd_api_stats(self, args):
        """Show API cache stats"""
        try:
            response = requests.get(f"{self.api_url}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                self.io.tool_output("\n📊 Code Index Statistics\n")
                self.io.tool_output(f"Cached files: {stats['cached_files']}")
                self.io.tool_output(f"Total definitions: {stats['total_definitions']}")
                self.io.tool_output(f"Total embeddings: {stats['total_embeddings']}")
            else:
                self.io.tool_error(f"API error: {response.json()}")
        
        except requests.RequestException as e:
            self.io.tool_error(f"Failed to connect to API: {e}")


def register(commands_registry):
    """Register API plugin commands"""
    plugin = CodeIndexerAPIPlugin(
        commands_registry.io,
        commands_registry.coder
    )
    
    commands_registry.register("api-search", plugin.cmd_api_search, "Search via API")
    commands_registry.register("api-index", plugin.cmd_api_index, "Index via API")
    commands_registry.register("api-stats", plugin.cmd_api_stats, "API stats")
