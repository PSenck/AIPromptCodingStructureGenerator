"""Gives imported C# module file names (ending with .cs) and information about the using directives,
recursively traces dependency trees, and attempts to extract definitions (classes, variables, etc.).

Supports multiple origin paths.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Union


def resolve_module_file(module_name: str, defined_paths: List[Path]) -> Optional[Path]:
    """Resolves a C# module file given a namespace by using the last segment as the file name.

    Args:
        module_name (str): The namespace (e.g. 'MyCompany.Utils').
        defined_paths (List[Path]): A list of base directories.

    Returns:
        Optional[Path]: The resolved .cs file, or None.
    """
    last_part = module_name.split('.')[-1]
    for base in defined_paths:
        candidate = base.rglob(last_part + ".cs")
        for path in candidate:
            return path
    return None


def extract_definition_from_source(source: str, name: str,
                                   project_root: Optional[Union[Path, List[Path]]] = None,
                                   current_module: Optional[Path] = None) -> str:
    """Extracts a C# class or variable definition from source.

    Args:
        source (str): The C# source code.
        name (str): The name of the entity to extract.
        project_root (Optional[Union[Path, List[Path]]]): Base directory(ies) for fallback.
        current_module (Optional[Path]): The current module file.

    Returns:
        str: The extracted definition or "Definition not found".
    """
    # Class definition pattern.
    pattern_class = re.compile(
        r'(public\s+|internal\s+|private\s+|protected\s+)?class\s+' + re.escape(name) +
        r'\b(?:.|\n)*?(?=^\s*(public|internal|private|protected|$))',
        re.MULTILINE
    )
    match = pattern_class.search(source)
    if match:
        return match.group(0).rstrip()
    # Variable definition pattern (simplified).
    pattern_var = re.compile(
        r'(public|internal|private|protected)\s+[\w<>,\s]+\s+' + re.escape(name) + r'\s*=\s*.*;',
        re.MULTILINE
    )
    matches = pattern_var.findall(source)
    if matches:
        m = re.search(pattern_var, source, re.MULTILINE)
        if m:
            return m.group(0).strip()
    return "Definition not found"


def trace_imports_recursive(module_file_path: Path, project_root: Union[Path, List[Path]], visited=None) -> Dict:
    """Recursively traces C# using directives.

    Args:
        module_file_path (Path): The .cs file path.
        project_root (Union[Path, List[Path]]): Base directory(ies).
        visited (optional): Set of visited files.

    Returns:
        Dict: A dependency tree with "module" and "imports".
    """
    if visited is None:
        visited = set()
    resolved = module_file_path.resolve()
    if resolved in visited:
        return {"module": str(resolved), "imports": "cycle"}
    visited.add(resolved)
    try:
        with open(module_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return {"module": str(resolved), "error": str(e)}
    pattern = re.compile(r'using\s+([\w\.]+)\s*;', re.MULTILINE)
    imported_modules = [m.group(1) for m in pattern.finditer(content)]
    imported_modules = list(dict.fromkeys(imported_modules))
    bases = project_root if isinstance(project_root, list) else [project_root]
    dependencies = {}
    for mod in imported_modules:
        candidate_file = resolve_module_file(mod, bases)
        if candidate_file:
            dependencies[mod] = trace_imports_recursive(candidate_file, bases, visited)
    return {"module": str(resolved), "imports": dependencies}


class CsharpImportExtractor:
    """Extractor for C# imports based on using directives.

    Attributes:
        path_where_imports_are_used (Path): Directory to search for C# files.
        paths_where_imports_are_defined (List[Path]): List of base directories for C# modules.
        exclude_files (Set[Path]): Files to exclude.
        whole_module_content (bool): Flag for full file content vs. partial extraction.
    """

    def __init__(self, path_where_imports_are_used: str,
                 path_where_imports_are_defined: Union[str, List[str]],
                 exclude_files, whole_module_content):
        self.path_where_imports_are_used = Path(path_where_imports_are_used)
        if isinstance(path_where_imports_are_defined, list):
            self.paths_where_imports_are_defined = [Path(p) for p in path_where_imports_are_defined]
        else:
            self.paths_where_imports_are_defined = [Path(path_where_imports_are_defined)]
        self.exclude_files = set(Path(f).resolve() for f in (exclude_files if exclude_files else []))
        self.whole_module_content = whole_module_content

    def extract_import_information(self, path_where_imports_are_used: Optional[str]=None,
                                   exclude_files: Optional[List[str]]=None) -> List[Dict]:
        """Extracts using directives from C# files.

        Args:
            path_where_imports_are_used (Optional[str]): Directory to search.
            exclude_files (Optional[List[str]]): Files to exclude.

        Returns:
            List[Dict]: A list of dictionaries representing using directives.
        """
        extracted_imports = []
        use_path = Path(path_where_imports_are_used or self.path_where_imports_are_used)
        for cs_file in use_path.rglob("*.cs"):
            try:
                with open(cs_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
            for match in re.finditer(r'using\s+([\w\.]+)\s*;', content):
                extracted_imports.append({
                    "imported_in_file_path": str(cs_file.resolve()),
                    "import_command": match.group(0),
                    "module": match.group(1),
                    "imported_objects": []  # C# using statements import a namespace
                })
        return extracted_imports

    def extract_imported_file_content(self, extracted_import_information: List[Dict],
                                      path_where_imports_are_defined: Optional[Union[str, List[str]]]=None,
                                      whole_module_content: Optional[bool]=None) -> List[Dict]:
        """Extracts the content of imported C# modules.

        Args:
            extracted_import_information (List[Dict]): List of using directive info.
            path_where_imports_are_defined (Optional[Union[str, List[str]]]): Base directories.
            whole_module_content (Optional[bool]): Flag for full content vs. partial.

        Returns:
            List[Dict]: A list of dictionaries with module content and dependency trees.
        """
        if path_where_imports_are_defined:
            defined_paths = [Path(p) for p in path_where_imports_are_defined] if isinstance(path_where_imports_are_defined, list) else [Path(path_where_imports_are_defined)]
        else:
            defined_paths = self.paths_where_imports_are_defined
        whole_module_content = whole_module_content if whole_module_content is not None else self.whole_module_content
        extracted_contents = []
        for imp in extracted_import_information:
            module_name = imp.get("module")
            candidate = resolve_module_file(module_name, defined_paths)
            if candidate:
                file_path = candidate
                if file_path.resolve() in self.exclude_files:
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()
                except Exception:
                    continue
                content_to_show = file_content if whole_module_content else file_content[:300]
                dep_tree = trace_imports_recursive(file_path, defined_paths)
                extracted_contents.append({
                    "module": module_name,
                    "file_path": str(file_path.resolve()),
                    "content": content_to_show,
                    "dependency_tree": dep_tree
                })
        return extracted_contents
