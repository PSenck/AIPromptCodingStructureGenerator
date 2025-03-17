# AIPromptCodingStructureGenerator
AIPromptCodingStructureGenerator
AI Coding Assistance – Project Structure and Import Visualizer

This repository contains a set of Python modules that work together to provide detailed information about your code base. The tools can generate:

    A full directory and file structure listing for a given feature.
    The content of each file (optionally).
    Detailed information on imported modules from various programming languages (Python, JavaScript, Vue, C#, and C++).
    A dependency tree for each imported module.
    Fallback lookup of definitions (e.g. functions, classes, variables) so that if an import re-exports an object, the tool traces it back to its original definition.

These outputs are intended to feed information to your AI Coding Assistance, so that the AI receives only relevant code (and not all project content).
Repository Structure

.
├── import_extractors
│   ├── cpp_import_extractor.py         # Extracts #include statements and definitions from C++ files
│   ├── cs_import_extractor.py          # Extracts using directives and definitions from C# files
│   ├── javascript_import_extractor.py  # Extracts ES6 import statements and definitions from JavaScript files
│   ├── python_import_extractor.py      # Extracts Python import statements, definitions, and dependency trees
│   └── vue_import_extractor.py         # Extracts import statements and definitions from Vue (.vue) files
├── project_feature_import_visualizer.py  # Combines extracted import info into a formatted output string
├── project_feature_structure_visualizer.py  # Generates a directory and file content structure for a feature
├── visualize_structure_file_content_and_imports.py  # Combines structure and import outputs and saves them to a text file
├── test_project_visualizer.py          # Pytest tests for the overall structure and import visualizers
└── test_project_feature_structure_visualizer.py  # Additional tests for the structure visualizer

Features

    Multiple Origin Paths:
    Each extractor supports one or more "origin" directories where imported modules are defined. This allows you to set, for example, both your project's internal tools folder and an external library folder as search locations.

    Selective Extraction:
    You can choose to extract either the full module content or only the definitions (functions, classes, variables) that are actually imported.

    Dependency Tracing:
    Each extractor builds a recursive dependency tree for imported modules so that you can track how modules are inter-connected.

    Language Support:
    The repository currently includes extractors for:
        Python (.py)
        JavaScript (.js)
        Vue (.vue)
        C# (.cs)
        C++ (via #include, e.g. .cpp, .h)

    Integration:
    The visualize_structure_file_content_and_imports.py script combines the file structure output (from project_feature_structure_visualizer.py) with the import information (from project_feature_import_visualizer.py) into one combined text file output.

Prerequisites

    Python 3.8 or higher
    pytest (for running tests)

You may install the dependencies with:

pip install -r requirements.txt

(Note: If you don’t have a requirements.txt yet, you can create one listing pytest or any other required packages.)
Usage
Running the Visualizers

    Project Structure Visualizer
    To generate a directory structure and file content output for a feature, run:

python project_feature_structure_visualizer.py

Project Import Visualizer
To extract import information and dependency trees from external modules, run:

python project_feature_import_visualizer.py

Combined Visualizer
To generate a combined output with both the structure and import information, run:

    python visualize_structure_file_content_and_imports.py

    This script calls both visualizers and saves the combined output into an output_combined folder.

Configuration

Each script accepts various parameters (either via configuration variables or command‑line arguments, depending on your integration). For example, in the combined visualizer you can configure:

    path_where_imports_are_used: The feature path where import statements are present.
    path_where_imports_are_defined: One or more paths where imported modules can be found.
    whole_module_content: Boolean flag indicating if you want full module content (True) or only definitions (False).
    exclude_files: Files to ignore (e.g. those already shown by the structure visualizer).
    file_types: File extensions to process (e.g. [".py", ".js", ".vue"]).

Review the inline comments in each module for more details.
Running the Tests

The repository includes pytest-based tests. To run the tests, simply execute:

pytest test_project_visualizer.py

or

pytest test_project_feature_structure_visualizer.py

These tests verify that both the structure and import visualizers produce output with the expected keys and content.
Extending the Functionality

If you need to add support for additional programming languages or modify the extraction logic for a specific language, update the corresponding extractor in the import_extractors folder. The design follows a consistent pattern:

    Module Resolution: The resolve_module_file function searches for the module file using the provided base paths.
    Definition Extraction: The extract_definition_from_source function uses language‑specific regex patterns to capture definitions.
    Dependency Tracing: The trace_imports_recursive function recursively builds a dependency tree.

You can then update the extractor_dict in project_feature_import_visualizer.py to include the new extractor for the relevant file extension.
License

MIT License
Acknowledgments

This project was built to enhance AI coding assistance by providing detailed context about code features, including file structure, file content, and import dependencies. Special thanks to the community and previous AI contributions that helped shape this tool.
