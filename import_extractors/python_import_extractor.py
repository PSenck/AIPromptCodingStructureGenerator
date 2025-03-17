"""Gives imported Python module file names (ending with .py), their absolute paths,
details about the imported objects, recursively traces dependency trees, and if a definition
is not found in a module, looks up the imported module that provides it.

Supports multiple origin paths for resolving imports. If a whole module is imported (e.g.
"from tools import toolbox"), the full module content is returned.

This module also uses fallback logic to look up an object’s definition from another module
if it is re-exported.
"""

import os
import re
from typing import List, Dict, Optional, Union
from pathlib import Path


def resolve_module_file(module_name: str, defined_paths: List[Path]) -> Optional[Path]:
    """Resolves a module file from its name using a list of base paths.

    Args:
        module_name (str): The dotted module name (e.g. 'tools.toolbox').
        defined_paths (List[Path]): A list of base directories to search in.

    Returns:
        Optional[Path]: The resolved module file (either module.py or module/__init__.py),
                        or None if not found.
    """
    parts = module_name.split('.')
    for base in defined_paths:
        # Remove redundant base name if present.
        if parts and parts[0].lower() == base.name.lower():
            candidate = base.joinpath(*parts[1:])
        else:
            candidate = base.joinpath(*parts)
        if candidate.with_suffix('.py').exists():
            return candidate.with_suffix('.py')
        elif (candidate / "__init__.py").exists():
            return candidate / "__init__.py"
    return None


def extract_definition_from_source(source: str, name: str,
                                   project_root: Optional[Union[Path, List[Path]]] = None,
                                   current_module: Optional[Path] = None) -> str:
    """Extracts the definition of a given object (function, class, or variable) from source code.

    For functions and classes, returns the block based on indentation.
    For variables, returns the last assignment.
    If not found, looks for an import statement that re-exports the object and recursively
    extracts its definition.

    Args:
        source (str): The source code to search.
        name (str): The name of the object to find.
        project_root (Optional[Union[Path, List[Path]]]): Base directory(ies) for fallback lookup.
        current_module (Optional[Path]): The file where the lookup is occurring.

    Returns:
        str: The extracted definition or "Definition not found".
    """
    # Try to capture a function or class definition using indentation.
    pattern = re.compile(
        r'(?:def|class)\s+%s\b(?:\s*\(.*?\))?:\s*(?:\n[ \t]+.*)+' % re.escape(name),
        re.MULTILINE
    )
    match = pattern.search(source)
    if match:
        return match.group(0).rstrip()

    # Try variable assignment.
    pattern_var = re.compile(r'^%s\s*=\s*.*' % re.escape(name), re.MULTILINE)
    matches = pattern_var.findall(source)
    if matches:
        return matches[-1].strip()

    # Fallback: if not found, check for an import statement that imports the object.
    if project_root and current_module:
        pattern_import = re.compile(
            r'^\s*from\s+([\w\.]+)\s+import\s+.*\b%s\b' % re.escape(name),
            re.MULTILINE
        )
        match_import = pattern_import.search(source)
        if match_import:
            imported_module = match_import.group(1)
            bases = project_root if isinstance(project_root, list) else [project_root]
            candidate_file = resolve_module_file(imported_module, bases)
            if candidate_file:
                try:
                    with open(candidate_file, "r", encoding="utf-8", errors="ignore") as f:
                        new_source = f.read()
                    fallback_def = extract_definition_from_source(new_source, name, bases, candidate_file)
                    if fallback_def != "Definition not found":
                        return f"{fallback_def} (imported from {str(candidate_file.resolve())})"
                except Exception:
                    pass
    return "Definition not found"


def trace_imports_recursive(module_file_path: Path, project_root: Union[Path, List[Path]],
                            visited=None) -> Dict:
    """Recursively traces the import dependencies of a given Python module file.

    Args:
        module_file_path (Path): Path to the module file.
        project_root (Union[Path, List[Path]]): Base directory(ies) to restrict search.
        visited (optional): Set of visited files to prevent cycles.

    Returns:
        Dict: A dictionary with keys "module" (the file path) and "imports" (nested dependency tree).
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

    pattern = re.compile(r'^\s*(?:import|from)\s+([\w\.]+)', re.MULTILINE)
    imported_modules = [m.group(1) for m in pattern.finditer(content)]
    imported_modules = list(dict.fromkeys(imported_modules))
    bases = project_root if isinstance(project_root, list) else [project_root]
    dependencies = {}
    for mod in imported_modules:
        candidate_file = resolve_module_file(mod, bases)
        if candidate_file:
            dependencies[mod] = trace_imports_recursive(candidate_file, bases, visited)
    return {"module": str(resolved), "imports": dependencies}


class PythonImportExtractor:
    """Extractor for Python imports in a given feature.

    Attributes:
        path_where_imports_are_used (Path): Directory path to search for import statements.
        paths_where_imports_are_defined (List[Path]): List of base paths where imported modules are defined.
        exclude_files (Set[Path]): Set of file paths to exclude.
        whole_module_content (bool): Flag to determine whether to extract full module content or only definitions.
    """

    def __init__(self, path_where_imports_are_used: str,
                 path_where_imports_are_defined: Union[str, List[str]],
                 exclude_files, whole_module_content):
        self.path_where_imports_are_used = Path(path_where_imports_are_used)
        if isinstance(path_where_imports_are_defined, list):
            self.paths_where_imports_are_defined = [Path(p) for p in path_where_imports_are_defined]
        else:
            self.paths_where_imports_are_defined = [Path(path_where_imports_are_defined)]
        self.exclude_files = {Path(f).resolve() for f in (exclude_files or [])}
        self.whole_module_content = whole_module_content

    def extract_import_information(self,
                                   path_where_imports_are_used: Optional[str] = None,
                                   exclude_files: Optional[List[str]] = None) -> List[Dict]:
        """Extracts import statements from Python files.

        Args:
            path_where_imports_are_used (Optional[str]): Directory path to search (defaults to the configured one).
            exclude_files (Optional[List[str]]): Files to exclude.

        Returns:
            List[Dict]: A list of dictionaries, each representing an import statement with keys:
                        'imported_in_file_path', 'import_command', and 'imported_objects'.
        """
        extracted_imports = []
        use_path = Path(path_where_imports_are_used or self.path_where_imports_are_used)
        pattern_import = re.compile(r'^\s*import\s+([\w\.]+)')
        pattern_from_import = re.compile(r'^\s*from\s+([\w\.]+)\s+import\s+(.+)')
        for root, _, files in os.walk(use_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix != ".py":
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        seen_lines = set()
                        for line in f:
                            norm_line = line.strip()
                            if not norm_line or norm_line in seen_lines:
                                continue
                            seen_lines.add(norm_line)
                            m = pattern_import.match(line)
                            if m:
                                module_name = m.group(1)
                                extracted_imports.append({
                                    "imported_in_file_path": str(file_path.resolve()).strip(),
                                    "import_command": norm_line,
                                    "imported_objects": [{"name": module_name, "type": "module"}]
                                })
                            else:
                                m = pattern_from_import.match(line)
                                if m:
                                    module_name = m.group(1)
                                    imported_items = [item.strip() for item in m.group(2).split(',') if item.strip()]
                                    imported_items = list(dict.fromkeys(imported_items))
                                    items = [{"name": module_name, "type": "module"}] + [
                                        {"name": itm, "type": "object"} for itm in imported_items
                                    ]
                                    extracted_imports.append({
                                        "imported_in_file_path": str(file_path.resolve()).strip(),
                                        "import_command": norm_line,
                                        "imported_objects": items
                                    })
                except Exception:
                    continue
        return extracted_imports

    def extract_imported_file_content(self,
                                      extracted_import_information: List[Dict],
                                      path_where_imports_are_defined: Optional[Union[str, List[str]]] = None,
                                      whole_module_content: Optional[bool] = None,
                                      exclude_files: Optional[List[str]] = None) -> List[Dict]:
        """Extracts the content of imported modules.

        Groups import statements by module file and the file in which they were imported.
        For each group, it extracts either the full module content (if whole_module_content is True
        or forced by grouping) or only the definitions for the imported objects.
        Also builds a dependency tree for each module.

        Args:
            extracted_import_information (List[Dict]): List of extracted import statements.
            path_where_imports_are_defined (Optional[Union[str, List[str]]]): Base paths where modules are defined.
            whole_module_content (Optional[bool]): Flag to determine full content or definitions only.
            exclude_files (Optional[List[str]]): Files to exclude from processing.

        Returns:
            List[Dict]: A list of dictionaries, each with keys: 'module', 'module_path',
                        'imported_in', and 'dependency_tree'.
        """
        if path_where_imports_are_defined:
            defined_paths = [Path(p) for p in path_where_imports_are_defined] if isinstance(path_where_imports_are_defined, list) else [Path(path_where_imports_are_defined)]
        else:
            defined_paths = self.paths_where_imports_are_defined

        used_path = self.path_where_imports_are_used.resolve()
        whole_module_content = whole_module_content if whole_module_content is not None else self.whole_module_content
        exclude_content_set = {Path(f).resolve() for f in (exclude_files or [])}

        groups = {}  # key: (resolved_module_path, imported_in), value: dict with merged import info
        for info in extracted_import_information:
            module_name = None
            group_full_flag = False  # flag to force full content
            for obj in info.get("imported_objects", []):
                if obj.get("type") == "module":
                    module_name = obj.get("name")
                    break
            if module_name:
                # Check if any imported object appended to the module name resolves to a module.
                for obj in info.get("imported_objects", []):
                    if obj.get("type") == "object":
                        candidate_name = module_name + '.' + obj.get("name")
                        if resolve_module_file(candidate_name, defined_paths):
                            module_name = candidate_name
                            group_full_flag = True
                            break
            if not module_name:
                continue
            module_file_path = resolve_module_file(module_name, defined_paths)
            if not module_file_path:
                continue
            if str(module_file_path.resolve()).startswith(str(used_path)):
                continue
            if module_file_path.resolve() in exclude_content_set:
                continue

            imported_in = info.get("imported_in_file_path", "Unknown").strip().lower()
            key = (str(module_file_path.resolve()), imported_in)
            if key not in groups:
                groups[key] = {
                    "imported_objects": [],
                    "module_file_path": module_file_path,
                    "imported_in": imported_in,
                    "force_full": group_full_flag
                }
            else:
                if group_full_flag:
                    groups[key]["force_full"] = True
            for obj in info.get("imported_objects", []):
                if obj["type"] == "object":
                    if not any(existing["name"].strip() == obj["name"].strip() for existing in groups[key]["imported_objects"] if existing["type"] == "object"):
                        groups[key]["imported_objects"].append(obj)
                else:
                    if not any(existing["name"] == obj["name"] for existing in groups[key]["imported_objects"]):
                        groups[key]["imported_objects"].append(obj)

        extracted_modules = []
        for key, group in groups.items():
            module_file_path = group["module_file_path"]
            imported_in = group["imported_in"]
            try:
                with open(module_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if whole_module_content or group.get("force_full", False):
                    final_content = content
                else:
                    extracted_obj_contents = {}
                    for imp_obj in group["imported_objects"]:
                        if imp_obj["type"] == "object":
                            obj_name = imp_obj["name"].strip()
                            definition = extract_definition_from_source(content, obj_name, defined_paths, module_file_path)
                            extracted_obj_contents[obj_name] = definition
                    final_content = "\n\n".join(extracted_obj_contents.values()).strip()
                dep_tree = trace_imports_recursive(module_file_path, defined_paths)
                extracted_modules.append({
                    "module": final_content,
                    "module_path": str(module_file_path.resolve()),
                    "imported_in": imported_in,
                    "dependency_tree": dep_tree
                })
            except Exception:
                continue
        return extracted_modules
