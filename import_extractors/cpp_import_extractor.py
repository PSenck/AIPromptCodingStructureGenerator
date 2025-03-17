"""Gives imported C++ module file names (typically via #include "file.h" or "file.hpp") and the imported file information,
recursively traces dependency trees, and attempts to extract definitions (classes, structs, variables).

Supports multiple origin paths.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Union


def resolve_module_file(module_file: str, defined_paths: List[Path]) -> Optional[Path]:
    """Resolves a C++ module file from its filename using defined base paths.

    Args:
        module_file (str): The header file name (e.g. 'MyHeader.h').
        defined_paths (List[Path]): List of base directories to search.

    Returns:
        Optional[Path]: The first matching file, or None.
    """
    for base in defined_paths:
        candidate = list(base.rglob(module_file))
        if candidate:
            return candidate[0]
    return None


def extract_definition_from_source(source: str, name: str,
                                   project_root: Optional[Union[Path, List[Path]]] = None,
                                   current_module: Optional[Path] = None) -> str:
    """Extracts a C++ class/struct or variable definition from source.

    Args:
        source (str): The C++ source code.
        name (str): The name of the entity.
        project_root (Optional[Union[Path, List[Path]]]): Base directories for fallback.
        current_module (Optional[Path]): The current file.

    Returns:
        str: The extracted definition or "Definition not found".
    """
    # Match class or struct definitions.
    pattern_class = re.compile(
        r'(?:class|struct)\s+' + re.escape(name) + r'\b(?:.|\n)*?(?=^;|\Z)',
        re.MULTILINE
    )
    match = pattern_class.search(source)
    if match:
        return match.group(0).rstrip()
    # Match variable assignments.
    pattern_var = re.compile(r'\b' + re.escape(name) + r'\s*=\s*.*;', re.MULTILINE)
    matches = pattern_var.findall(source)
    if matches:
        return matches[-1].strip()
    return "Definition not found"


def trace_imports_recursive(module_file_path: Path, project_root: Union[Path, List[Path]], visited=None) -> Dict:
    """Recursively traces C++ #include dependencies.

    Args:
        module_file_path (Path): Path to the C++ file.
        project_root (Union[Path, List[Path]]): Base directories.
        visited (optional): Set of visited files.

    Returns:
        Dict: A dependency tree with keys "module" and "includes".
    """
    if visited is None:
        visited = set()
    resolved = module_file_path.resolve()
    if resolved in visited:
        return {"module": str(resolved), "includes": "cycle"}
    visited.add(resolved)
    try:
        with open(module_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return {"module": str(resolved), "error": str(e)}
    pattern = re.compile(r'#include\s+"([^"]+)"')
    included_files = [m.group(1) for m in pattern.finditer(content)]
    included_files = list(dict.fromkeys(included_files))
    bases = project_root if isinstance(project_root, list) else [project_root]
    dependencies = {}
    for inc in included_files:
        candidate_file = resolve_module_file(inc, bases)
        if candidate_file:
            dependencies[inc] = trace_imports_recursive(candidate_file, bases, visited)
    return {"module": str(resolved), "includes": dependencies}


class CppImportExtractor:
    """Extractor for C++ import statements (#include).

    Attributes:
        path_where_imports_are_used (Path): Directory where C++ files are searched.
        path_where_imports_are_defined (Path): Base directory for resolving includes.
        exclude_files (Set[Path]): Files to exclude.
        whole_module_content (bool): Flag for returning full file content vs. a snippet.
    """

    def __init__(self, path_where_imports_are_used: str,
                 path_where_imports_are_defined: str,
                 exclude_files, whole_module_content):
        self.path_where_imports_are_used = Path(path_where_imports_are_used)
        self.path_where_imports_are_defined = Path(path_where_imports_are_defined)
        self.exclude_files = set(Path(f).resolve() for f in (exclude_files if exclude_files else []))
        self.whole_module_content = whole_module_content

    def extract_import_information(self, path_where_imports_are_used: Optional[str] = None,
                                   exclude_files: Optional[List[str]] = None) -> List[Dict]:
        """Extracts #include statements from C++ source files.

        Args:
            path_where_imports_are_used (Optional[str]): Directory to search.
            exclude_files (Optional[List[str]]): Files to exclude.

        Returns:
            List[Dict]: A list of dictionaries with #include information.
        """
        extracted_imports = []
        use_path = Path(path_where_imports_are_used or self.path_where_imports_are_used)
        for cpp_file in use_path.rglob("*.cpp"):
            try:
                with open(cpp_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
            for match in re.finditer(r'#include\s+"([^"]+)"', content):
                extracted_imports.append({
                    "imported_in_file_path": str(cpp_file.resolve()),
                    "import_command": match.group(0),
                    "module": match.group(1),
                    "imported_objects": []  # C++ includes do not import objects
                })
        return extracted_imports

    def extract_imported_file_content(self, extracted_import_information: List[Dict],
                                      path_where_imports_are_defined: Optional[Union[str, List[str]]] = None,
                                      whole_module_content: Optional[bool] = None) -> List[Dict]:
        """Extracts the content of imported C++ modules (header files).

        Args:
            extracted_import_information (List[Dict]): List of #include info.
            path_where_imports_are_defined (Optional[Union[str, List[str]]]): Base directories.
            whole_module_content (Optional[bool]): Flag for full content.

        Returns:
            List[Dict]: A list of dictionaries with module content and dependency tree.
        """
        if path_where_imports_are_defined is None:
            path_where_imports_are_defined = self.path_where_imports_are_defined
        else:
            path_where_imports_are_defined = Path(path_where_imports_are_defined)
        if whole_module_content is None:
            whole_module_content = self.whole_module_content
        extracted_contents = []
        for imp in extracted_import_information:
            module_file = imp.get("module")
            candidate = resolve_module_file(module_file, [self.path_where_imports_are_defined])
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
                dep_tree = trace_imports_recursive(file_path, self.path_where_imports_are_defined)
                extracted_contents.append({
                    "module": module_file,
                    "file_path": str(file_path.resolve()),
                    "content": content_to_show,
                    "dependency_tree": dep_tree
                })
        return extracted_contents
