"""Gives imported Vue module file names (ending with .vue) and details about the import,
recursively traces dependency trees, and if a definition isn’t found, attempts fallback lookup.

Supports multiple origin paths.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Union


def resolve_module_file(module_name: str, defined_paths: List[Path]) -> Optional[Path]:
    """Resolves a Vue module file from its name using defined base paths.

    Args:
        module_name (str): The module name (e.g. 'components.MyComponent').
        defined_paths (List[Path]): Base directories.

    Returns:
        Optional[Path]: The resolved .vue file, or None.
    """
    parts = module_name.split('.')
    for base in defined_paths:
        if parts and parts[0].lower() == base.name.lower():
            candidate = base.joinpath(*parts[1:])
        else:
            candidate = base.joinpath(*parts)
        candidate_vue = candidate.with_suffix('.vue')
        if candidate_vue.exists():
            return candidate_vue
    return None


def extract_definition_from_source(source: str, name: str,
                                   project_root: Optional[Union[Path, List[Path]]] = None,
                                   current_module: Optional[Path] = None) -> str:
    """Extracts a definition from a Vue file by looking inside the export default object.

    Args:
        source (str): The Vue file content.
        name (str): The name of the property to extract.
        project_root (Optional[Union[Path, List[Path]]]): Base directories.
        current_module (Optional[Path]): The current Vue file.

    Returns:
        str: The extracted property definition or "Definition not found".
    """
    pattern = re.compile(r'export\s+default\s+\{(?:.|\n)*?\b' + re.escape(name) + r'\s*:\s*([^,\n\}]+)', re.MULTILINE)
    match = pattern.search(source)
    if match:
        return f"{name} : {match.group(1).strip()}"
    return "Definition not found"


def trace_imports_recursive(module_file_path: Path, project_root: Union[Path, List[Path]], visited=None) -> Dict:
    """Recursively traces Vue import dependencies.

    Args:
        module_file_path (Path): Path to the Vue file.
        project_root (Union[Path, List[Path]]): Base directories.
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
    pattern = re.compile(r'import\s+(?:\{[\w\s,]+\}\s+from\s+|[\w]+\s+from\s+)?[\'"]([^\'"]+)[\'"]', re.MULTILINE)
    imported_modules = [m.group(1) for m in pattern.finditer(content)]
    imported_modules = list(dict.fromkeys(imported_modules))
    bases = project_root if isinstance(project_root, list) else [project_root]
    dependencies = {}
    for mod in imported_modules:
        candidate_file = resolve_module_file(mod, bases)
        if candidate_file:
            dependencies[mod] = trace_imports_recursive(candidate_file, bases, visited)
    return {"module": str(resolved), "imports": dependencies}


class VueImportExtractor:
    """Extractor for Vue imports.

    Attributes:
        path_where_imports_are_used (Path): Directory to search for .vue files.
        paths_where_imports_are_defined (List[Path]): Base directories for module definitions.
        exclude_files (Set[Path]): Files to exclude.
        whole_module_content (bool): Flag to return full content or only definitions.
    """

    def __init__(self, path_where_imports_are_used, path_where_imports_are_defined, exclude_files,
                 whole_module_content):
        self.path_where_imports_are_used = Path(path_where_imports_are_used)
        if isinstance(path_where_imports_are_defined, list):
            self.paths_where_imports_are_defined = [Path(p) for p in path_where_imports_are_defined]
        else:
            self.paths_where_imports_are_defined = [Path(path_where_imports_are_defined)]
        self.exclude_files = set(Path(f).resolve() for f in (exclude_files if exclude_files else []))
        self.whole_module_content = whole_module_content

    def extract_import_information(self, path_where_imports_are_used: Optional[str] = None,
                                   exclude_files: Optional[List[str]] = None) -> List[Dict]:
        """Extracts import statements from Vue files.

        Args:
            path_where_imports_are_used (Optional[str]): Directory to search.
            exclude_files (Optional[List[str]]): Files to exclude.

        Returns:
            List[Dict]: A list of dictionaries with import information.
        """
        extracted_imports = []
        use_path = Path(path_where_imports_are_used or self.path_where_imports_are_used)
        for vue_file in use_path.rglob("*.vue"):
            try:
                with open(vue_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
            for match in re.finditer(r'import\s+(?:\{([\w\s,]+)\}\s+from\s+|([\w]+)\s+from\s+)?[\'"]([^\'"]+)[\'"]',
                                     content):
                imported_objects = []
                if match.group(1):
                    for obj in match.group(1).split(','):
                        imported_objects.append({"name": obj.strip(), "type": "unknown"})
                elif match.group(2):
                    imported_objects.append({"name": match.group(2).strip(), "type": "unknown"})
                extracted_imports.append({
                    "imported_in_file_path": str(vue_file.resolve()),
                    "import_command": match.group(0),
                    "module": match.group(3),
                    "imported_objects": imported_objects
                })
        return extracted_imports

    def extract_imported_file_content(self, extracted_import_information: List[Dict],
                                      path_where_imports_are_defined: Optional[Union[str, List[str]]] = None,
                                      whole_module_content: Optional[bool] = None) -> List[Dict]:
        """Extracts the content of imported Vue modules.

        Args:
            extracted_import_information (List[Dict]): Import info extracted from Vue files.
            path_where_imports_are_defined (Optional[Union[str, List[str]]]): Base directories.
            whole_module_content (Optional[bool]): Flag for full content vs. definitions.

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
            module_path = imp.get("module")
            candidate = list(defined_paths[0].rglob(module_path + ".vue"))
            if candidate:
                file_path = candidate[0]
                if file_path.resolve() in self.exclude_files:
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()
                except Exception:
                    continue
                if whole_module_content or not imp["imported_objects"]:
                    content_to_show = file_content
                else:
                    objects_content = {}
                    for obj in imp["imported_objects"]:
                        objects_content[obj["name"]] = extract_definition_from_source(file_content, obj["name"], defined_paths, file_path)
                    content_to_show = objects_content
                dep_tree = trace_imports_recursive(file_path, defined_paths)
                extracted_contents.append({
                    "module": module_path,
                    "file_path": str(file_path.resolve()),
                    "content": content_to_show,
                    "dependency_tree": dep_tree
                })
        return extracted_contents
