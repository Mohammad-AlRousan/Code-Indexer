"""
Tree-sitter based code indexer
Extracts function/class signatures without implementation bodies
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import pathspec

try:
    from tree_sitter import Language, Parser
    
    # Import individual language parsers
    try:
        import tree_sitter_python as ts_python
    except ImportError:
        ts_python = None
    
    try:
        import tree_sitter_javascript as ts_javascript
    except ImportError:
        ts_javascript = None
    
    try:
        import tree_sitter_typescript as ts_typescript
    except ImportError:
        ts_typescript = None
    
    try:
        import tree_sitter_go as ts_go
    except ImportError:
        ts_go = None
    
    try:
        import tree_sitter_rust as ts_rust
    except ImportError:
        ts_rust = None
    
    try:
        import tree_sitter_java as ts_java
    except ImportError:
        ts_java = None
    
    try:
        import tree_sitter_cpp as ts_cpp
    except ImportError:
        ts_cpp = None
    
    try:
        import tree_sitter_c as ts_c
    except ImportError:
        ts_c = None
    
    try:
        import tree_sitter_c_sharp as ts_csharp
    except ImportError:
        ts_csharp = None
    
    try:
        import tree_sitter_ruby as ts_ruby
    except ImportError:
        ts_ruby = None
    
except ImportError:
    print("Warning: tree_sitter not installed. Run: pip install tree-sitter")
    Language = None
    Parser = None


@dataclass
class CodeDefinition:
    """Represents a code definition (function, class, method, etc.)"""
    type: str  # 'function', 'class', 'method', 'variable'
    name: str
    signature: str
    line: int
    file_path: str
    language: str
    children: List['CodeDefinition'] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        if self.children:
            result['children'] = [c.to_dict() for c in self.children]
        return result


class TreeSitterIndexer:
    """
    Code indexer using Tree-sitter for language-aware parsing
    Extracts signatures without implementation bodies (Plandex approach)
    """
    
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'tsx',
        '.jsx': 'javascript',
        '.go': 'go',
        '.rs': 'rust',
        '.java': 'java',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.cs': 'c_sharp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
    }
    
    def __init__(self):
        """Initialize the indexer"""
        self.parsers = {}
        self.languages = {}
        self.language_modules = {
            'python': ts_python,
            'javascript': ts_javascript,
            'typescript': ts_typescript,
            'tsx': ts_typescript,
            'go': ts_go,
            'rust': ts_rust,
            'java': ts_java,
            'cpp': ts_cpp,
            'c': ts_c,
            'c_sharp': ts_csharp,
            'ruby': ts_ruby,
        }
        
    def get_parser(self, language: str):
        """Get or create a parser for the given language"""
        if language not in self.parsers:
            if Parser is None:
                raise ImportError("tree_sitter not installed")
            
            # Get the language module
            lang_module = self.language_modules.get(language)
            if lang_module is None:
                raise ImportError(f"Language parser for '{language}' not installed")
            
            # Create parser and set language
            parser = Parser()
            lang = Language(lang_module.language())
            parser.language = lang
            
            self.parsers[language] = parser
            self.languages[language] = lang
            
        return self.parsers[language]
    
    def get_language_for_file(self, filepath: str) -> Optional[str]:
        """Determine language from file extension"""
        ext = Path(filepath).suffix.lower()
        return self.LANGUAGE_MAP.get(ext)
    
    def get_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of file for cache invalidation"""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def index_file(self, filepath: str) -> Dict[str, Any]:
        """
        Index a single file
        Returns dict with definitions and metadata
        """
        language = self.get_language_for_file(filepath)
        if not language:
            return {
                'error': f'Unsupported file type: {filepath}',
                'file_path': filepath,
                'definitions': []
            }
        
        try:
            with open(filepath, 'rb') as f:
                source_code = f.read()
            
            parser = self.get_parser(language)
            tree = parser.parse(source_code)
            source_str = source_code.decode('utf8')
            
            definitions = self._extract_definitions(
                tree.root_node,
                source_str,
                filepath,
                language
            )
            
            return {
                'file_path': filepath,
                'language': language,
                'hash': self.get_file_hash(filepath),
                'definitions': [d.to_dict() for d in definitions],
                'num_definitions': len(definitions)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'file_path': filepath,
                'definitions': []
            }
    
    def _extract_definitions(
        self,
        node,
        source: str,
        filepath: str,
        language: str
    ) -> List[CodeDefinition]:
        """
        Extract function/class signatures without implementation bodies
        This is the core of Plandex's approach
        """
        definitions = []
        
        def visit(n, parent_name=None):
            node_type = n.type
            
            # Python
            if language == 'python':
                if node_type == 'function_definition':
                    defn = self._extract_python_function(n, source, filepath, language, parent_name)
                    if defn:
                        definitions.append(defn)
                elif node_type == 'class_definition':
                    defn = self._extract_python_class(n, source, filepath, language)
                    if defn:
                        definitions.append(defn)
            
            # JavaScript/TypeScript
            elif language in ['javascript', 'typescript', 'tsx']:
                if node_type in ['function_declaration', 'function', 'arrow_function']:
                    defn = self._extract_js_function(n, source, filepath, language)
                    if defn:
                        definitions.append(defn)
                elif node_type in ['class_declaration', 'class']:
                    defn = self._extract_js_class(n, source, filepath, language)
                    if defn:
                        definitions.append(defn)
                elif node_type == 'method_definition':
                    defn = self._extract_js_method(n, source, filepath, language, parent_name)
                    if defn:
                        definitions.append(defn)
            
            # Go
            elif language == 'go':
                if node_type == 'function_declaration':
                    defn = self._extract_go_function(n, source, filepath, language)
                    if defn:
                        definitions.append(defn)
                elif node_type == 'method_declaration':
                    defn = self._extract_go_method(n, source, filepath, language)
                    if defn:
                        definitions.append(defn)
            
            # Recurse into children
            current_parent = parent_name
            if node_type in ['class_definition', 'class_declaration', 'class']:
                name_node = n.child_by_field_name('name')
                if name_node:
                    current_parent = source[name_node.start_byte:name_node.end_byte]
            
            for child in n.children:
                visit(child, current_parent)
        
        visit(node)
        return definitions
    
    def _extract_python_function(self, node, source, filepath, language, parent_name=None):
        """Extract Python function signature"""
        name_node = node.child_by_field_name('name')
        params_node = node.child_by_field_name('parameters')
        
        if not name_node or not params_node:
            return None
        
        name = source[name_node.start_byte:name_node.end_byte]
        
        # Find signature end (before body)
        sig_end = params_node.end_byte
        
        # Include return type annotation if present
        for child in node.children:
            if child.type == 'type':
                sig_end = child.end_byte
        
        signature = source[node.start_byte:sig_end].strip()
        
        return CodeDefinition(
            type='method' if parent_name else 'function',
            name=name,
            signature=signature,
            line=node.start_point[0] + 1,
            file_path=filepath,
            language=language,
            children=[]
        )
    
    def _extract_python_class(self, node, source, filepath, language):
        """Extract Python class signature and methods"""
        name_node = node.child_by_field_name('name')
        
        if not name_node:
            return None
        
        name = source[name_node.start_byte:name_node.end_byte]
        body_node = node.child_by_field_name('body')
        
        # Get class header (without body)
        if body_node:
            sig = source[node.start_byte:body_node.start_byte].strip()
        else:
            sig = source[node.start_byte:node.end_byte].strip()
        
        # Extract methods
        methods = []
        if body_node:
            for child in body_node.children:
                if child.type == 'function_definition':
                    method = self._extract_python_function(child, source, filepath, language, name)
                    if method:
                        methods.append(method)
        
        return CodeDefinition(
            type='class',
            name=name,
            signature=sig,
            line=node.start_point[0] + 1,
            file_path=filepath,
            language=language,
            children=methods
        )
    
    def _extract_js_function(self, node, source, filepath, language):
        """Extract JavaScript/TypeScript function signature"""
        name_node = node.child_by_field_name('name')
        params_node = node.child_by_field_name('parameters')
        
        if not params_node:
            return None
        
        # For arrow functions, might not have a name
        if name_node:
            name = source[name_node.start_byte:name_node.end_byte]
        else:
            # Try to find parent variable declarator
            parent = node.parent
            if parent and parent.type == 'variable_declarator':
                name_node = parent.child_by_field_name('name')
                if name_node:
                    name = source[name_node.start_byte:name_node.end_byte]
                else:
                    name = '<anonymous>'
            else:
                name = '<anonymous>'
        
        # Find signature end (before body)
        body_node = node.child_by_field_name('body')
        if body_node:
            sig_end = body_node.start_byte
        else:
            sig_end = params_node.end_byte
        
        # Include return type if present (TypeScript)
        for child in node.children:
            if child.type == 'type_annotation' and child.start_byte < sig_end:
                sig_end = child.end_byte
        
        signature = source[node.start_byte:sig_end].strip()
        
        return CodeDefinition(
            type='function',
            name=name,
            signature=signature,
            line=node.start_point[0] + 1,
            file_path=filepath,
            language=language,
            children=[]
        )
    
    def _extract_js_class(self, node, source, filepath, language):
        """Extract JavaScript/TypeScript class signature"""
        name_node = node.child_by_field_name('name')
        
        if not name_node:
            return None
        
        name = source[name_node.start_byte:name_node.end_byte]
        body_node = node.child_by_field_name('body')
        
        # Get class header
        if body_node:
            sig = source[node.start_byte:body_node.start_byte].strip()
        else:
            sig = source[node.start_byte:node.end_byte].strip()
        
        # Extract methods
        methods = []
        if body_node:
            for child in body_node.children:
                if child.type == 'method_definition':
                    method = self._extract_js_method(child, source, filepath, language, name)
                    if method:
                        methods.append(method)
        
        return CodeDefinition(
            type='class',
            name=name,
            signature=sig,
            line=node.start_point[0] + 1,
            file_path=filepath,
            language=language,
            children=methods
        )
    
    def _extract_js_method(self, node, source, filepath, language, parent_name):
        """Extract JavaScript/TypeScript method signature"""
        name_node = node.child_by_field_name('name')
        params_node = node.child_by_field_name('parameters')
        
        if not name_node or not params_node:
            return None
        
        name = source[name_node.start_byte:name_node.end_byte]
        body_node = node.child_by_field_name('body')
        
        if body_node:
            sig_end = body_node.start_byte
        else:
            sig_end = node.end_byte
        
        signature = source[node.start_byte:sig_end].strip()
        
        return CodeDefinition(
            type='method',
            name=name,
            signature=signature,
            line=node.start_point[0] + 1,
            file_path=filepath,
            language=language,
            children=[]
        )
    
    def _extract_go_function(self, node, source, filepath, language):
        """Extract Go function signature"""
        name_node = node.child_by_field_name('name')
        params_node = node.child_by_field_name('parameters')
        
        if not name_node or not params_node:
            return None
        
        name = source[name_node.start_byte:name_node.end_byte]
        
        # Find signature end (before body)
        body_node = node.child_by_field_name('body')
        if body_node:
            sig_end = body_node.start_byte
        else:
            sig_end = node.end_byte
        
        signature = source[node.start_byte:sig_end].strip()
        
        return CodeDefinition(
            type='function',
            name=name,
            signature=signature,
            line=node.start_point[0] + 1,
            file_path=filepath,
            language=language,
            children=[]
        )
    
    def _extract_go_method(self, node, source, filepath, language):
        """Extract Go method signature"""
        name_node = node.child_by_field_name('name')
        receiver_node = node.child_by_field_name('receiver')
        
        if not name_node:
            return None
        
        name = source[name_node.start_byte:name_node.end_byte]
        
        # Find signature end (before body)
        body_node = node.child_by_field_name('body')
        if body_node:
            sig_end = body_node.start_byte
        else:
            sig_end = node.end_byte
        
        signature = source[node.start_byte:sig_end].strip()
        
        return CodeDefinition(
            type='method',
            name=name,
            signature=signature,
            line=node.start_point[0] + 1,
            file_path=filepath,
            language=language,
            children=[]
        )
    
    def _load_gitignore(self, directory: str) -> Optional[pathspec.PathSpec]:
        """Load and parse .gitignore file if it exists"""
        gitignore_path = os.path.join(directory, '.gitignore')
        if not os.path.exists(gitignore_path):
            return None
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                patterns = f.read().splitlines()
            return pathspec.PathSpec.from_lines('gitwildmatch', patterns)
        except Exception as e:
            print(f"Warning: Could not load .gitignore: {e}")
            return None
    
    def index_directory(
        self,
        directory: str,
        ignore_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Index all supported files in a directory
        Returns dict mapping file paths to their definitions
        Respects .gitignore patterns automatically
        """
        if ignore_patterns is None:
            ignore_patterns = [
                'node_modules', '__pycache__', '.git', '.venv',
                'venv', 'dist', 'build', '.pytest_cache'
            ]
        
        index = {}
        stats = {
            'files_indexed': 0,
            'files_skipped': 0,
            'total_definitions': 0,
            'errors': []
        }
        
        directory_path = Path(directory)
        
        # Load .gitignore patterns
        gitignore_spec = self._load_gitignore(directory)
        
        for root, dirs, files in os.walk(directory):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_patterns]
            
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, directory)
                
                # Check .gitignore
                if gitignore_spec and gitignore_spec.match_file(rel_path):
                    stats['files_skipped'] += 1
                    continue
                
                # Check if supported
                if not self.get_language_for_file(filepath):
                    stats['files_skipped'] += 1
                    continue
                
                # Check file size (skip very large files)
                try:
                    file_size = os.path.getsize(filepath)
                    if file_size > 5 * 1024 * 1024:  # 5MB
                        stats['files_skipped'] += 1
                        continue
                except:
                    continue
                
                # Index the file
                result = self.index_file(filepath)
                
                if 'error' in result:
                    stats['errors'].append(f"{rel_path}: {result['error']}")
                    stats['files_skipped'] += 1
                else:
                    index[rel_path] = result
                    stats['files_indexed'] += 1
                    stats['total_definitions'] += result.get('num_definitions', 0)
        
        return {
            'index': index,
            'stats': stats,
            'directory': directory
        }
    
    def create_map_string(self, index_result: Dict[str, Any]) -> str:
        """
        Create a human-readable map string (Plandex style)
        This is what you feed to the AI for context
        """
        output = []
        index = index_result.get('index', {})
        
        for filepath, file_data in sorted(index.items()):
            output.append(f"\n### {filepath}")
            output.append(f"Language: {file_data.get('language', 'unknown')}")
            
            definitions = file_data.get('definitions', [])
            
            for defn in definitions:
                self._format_definition(defn, output, indent=0)
        
        return "\n".join(output)
    
    def _format_definition(self, defn: Dict, output: List[str], indent: int = 0):
        """Format a definition for the map string"""
        indent_str = "  " * indent
        sig = defn.get('signature', '')
        
        # Truncate very long signatures
        if len(sig) > 150:
            sig = sig[:147] + "..."
        
        output.append(f"{indent_str}{sig}")
        
        # Recursively format children
        children = defn.get('children', [])
        if children:
            for child in children:
                self._format_definition(child, output, indent + 1)
