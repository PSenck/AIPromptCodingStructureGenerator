"""Visualizes imports in a project feature path for external modules.

It uses the appropriate language extractor (e.g. Python, Vue, JavaScript, C#, C++) based on the file extension.
It then compiles the output showing:
  - Where each module is defined,
  - Where it is imported,
  - The extracted content (either full module content or only definitions),
  - And the dependency tree.

Files already displayed by the structure visualizer are excluded.
"""

import os
from pathlib import Path
from datetime import datetime
from import_extractors.python_import_extractor import PythonImportExtractor
# Additional extractors can be imported here as needed, e.g. VueImportExtractor, etc.

# Dictionary mapping file extensions to the corresponding extractor classes.
extractor_dict = {
    ".py": PythonImportExtractor,
    # ".vue": VueImportExtractor,
    # ".js": JavaScriptImportExtractor,
    # ".cs": CsharpImportExtractor,
    # ".cpp": CppImportExtractor,
}


def show_imports_of_feature_path(
        path_where_imports_are_used: str,
        path_where_imports_are_defined: str,
        whole_module_content: bool = True,
        file_types: list = None,
        give_file_content: bool = True,
        save_output: bool = False,
        print_output: bool = False,
        output_path: str = None,
        exclude_files: list = None,
        exclude_folders: list = None,
        exclude_empty_files: bool = False,
        only_files_to_look_for: list = None
):
    """Generates a combined output string showing imported modules and their extracted content.

    Args:
        path_where_imports_are_used (str): Directory where import statements are located.
        path_where_imports_are_defined (str): Base directory for module definitions.
        whole_module_content (bool): If True, returns full module content; otherwise, only definitions.
        file_types (list): List of file extensions to consider (e.g. [".py", ".js", ".vue"]).
        give_file_content (bool): Flag to include the file content in the output.
        save_output (bool): Flag to save the output to a text file.
        print_output (bool): Flag to print the output to the console.
        output_path (str): Directory to save the output file.
        exclude_files (list): Files to exclude (absolute paths) from processing.
        exclude_folders (list): Folders to exclude.
        exclude_empty_files (bool): Exclude files with no content.
        only_files_to_look_for (list): Specific files to include exclusively.

    Returns:
        Dict: Contains the full import structure output, list of files processed, and used arguments.
    """
    file_types = file_types or list(extractor_dict.keys())
    full_output_parts = []

    # For simplicity, here we only support Python (.py) in this example.
    extractor_class = extractor_dict.get(".py")
    if extractor_class is None:
        return {"import_structure": "", "files": [], "used_args": {}, "full_output": ""}
    extractor = extractor_class(
        path_where_imports_are_used,
        path_where_imports_are_defined,
        exclude_files,
        whole_module_content
    )
    import_info = extractor.extract_import_information()
    module_contents = extractor.extract_imported_file_content(import_info, exclude_files=exclude_files)

    full_output_parts.append("Imported Module Contents:\n\n")
    for module in module_contents:
        full_output_parts.append(f"Defined at: {module.get('module_path', '')}\n")
        full_output_parts.append(f"Imported in: {module.get('imported_in', 'Unknown')}\n")
        full_output_parts.append("Content:\n\n")
        full_output_parts.append(module.get("module", "") + "\n\n")
    full_output = "\n".join(full_output_parts)

    if save_output:
        script_folder = Path(__file__).parent.resolve()
        default_output_folder = script_folder / 'output_project_feature_import_visualizer'
        if output_path is None:
            output_path = default_output_folder
        output_path = Path(output_path)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = output_path / f"output_{Path(__file__).stem}_{timestamp}.txt"
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(full_output)
        if print_output:
            print(f"Combined output saved to {output_file_path}")

    if print_output:
        print(full_output)

    used_args = {
        "path_where_imports_are_used": path_where_imports_are_used,
        "path_where_imports_are_defined": path_where_imports_are_defined,
        "whole_module_content": whole_module_content,
        "file_types": file_types,
        "give_file_content": give_file_content,
        "save_output": save_output,
        "output_path": str(output_path) if output_path else None,
        "exclude_files": exclude_files,
    }

    return {
        "import_structure": full_output,
        "files": [info.get("imported_in_file_path", "") for info in import_info],
        "used_args": used_args,
        "full_output": full_output
    }
