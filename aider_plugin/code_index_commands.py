"""
Aider plugin for Code-Indexer integration
Adds /index-search command to Aider sessions

Installation:
1. Copy this file to your Aider plugins directory
2. Or import in .aider.conf.yml

Usage in Aider:
    /index-search "authentication functions"
    /index-map src/
    /index-refresh
"""

import subprocess
import json
from pathlib import Path


class CodeIndexerPlugin:
    """Integrate Code-Indexer semantic search into Aider"""
    
    def __init__(self, io, coder):
        self.io = io
        self.coder = coder
        self.indexer_path = Path(__file__).parent.parent / "src" / "cli.py"
    
    def cmd_index_search(self, args):
        """
        Search codebase semantically and add relevant files to chat
        
        Usage: /index-search "your search query" [--top-k N]
        """
        query = args.strip()
        if not query:
            self.io.tool_error("Usage: /index-search \"your search query\"")
            return
        
        # Run Code-Indexer search
        cmd = [
            "python", str(self.indexer_path),
            "search", query,
            "--top-k", "5",
            "--threshold", "0.7"
        ]
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            
            # Parse results and extract file paths
            files_to_add = self._parse_search_results(result.stdout)
            
            # Display results
            self.io.tool_output(result.stdout)
            
            # Ask to add files to chat
            if files_to_add:
                self.io.tool_output(f"\nFound {len(files_to_add)} relevant files")
                for file in files_to_add:
                    if self.io.confirm_ask(f"Add {file} to chat?", default="y"):
                        self.coder.add_rel_fname(file)
                        self.io.tool_output(f"✅ Added {file}")
        
        except subprocess.CalledProcessError as e:
            self.io.tool_error(f"Search failed: {e.stderr}")
    
    def cmd_index_map(self, args):
        """
        Generate and load codebase map into context
        
        Usage: /index-map [directory]
        """
        directory = args.strip() or "."
        
        # Generate map
        cmd = [
            "python", str(self.indexer_path),
            "map", directory,
            "--output", ".aider-index-map.txt"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            
            # Add to read-only files
            self.coder.abs_read_only_fnames.add(
                Path(".aider-index-map.txt").absolute()
            )
            self.io.tool_output("✅ Codebase map loaded into context")
        
        except subprocess.CalledProcessError as e:
            self.io.tool_error(f"Map generation failed: {e}")
    
    def cmd_index_refresh(self, args):
        """
        Re-index the codebase
        
        Usage: /index-refresh [--force]
        """
        force = "--force" if "--force" in args else ""
        
        cmd = [
            "python", str(self.indexer_path),
            "index", ".",
            "--with-embeddings"
        ]
        
        if force:
            cmd.append("--force")
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            self.io.tool_output(result.stdout)
            self.io.tool_output("✅ Index refreshed")
        
        except subprocess.CalledProcessError as e:
            self.io.tool_error(f"Indexing failed: {e.stderr}")
    
    def _parse_search_results(self, output: str) -> list:
        """Extract file paths from search output"""
        files = []
        for line in output.split('\n'):
            if line.strip().startswith('📁'):
                # Extract file path
                file_path = line.split('📁')[1].strip()
                files.append(file_path)
        return files


# Register commands
def register(commands_registry):
    """Register plugin commands with Aider"""
    plugin = CodeIndexerPlugin(commands_registry.io, commands_registry.coder)
    
    commands_registry.register(
        "index-search",
        plugin.cmd_index_search,
        "Search codebase semantically"
    )
    commands_registry.register(
        "index-map",
        plugin.cmd_index_map,
        "Generate and load codebase map"
    )
    commands_registry.register(
        "index-refresh",
        plugin.cmd_index_refresh,
        "Re-index the codebase"
    )
