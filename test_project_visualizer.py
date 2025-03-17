"""Tests for the project feature visualizers.

These tests use pytest to verify that the structure visualizer and import visualizer
return output with the expected keys and content.
"""

import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from project_feature_structure_visualizer import show_structure_and_list_file_content
from project_feature_import_visualizer import show_imports_of_feature_path

# Helper to create a sample test environment.
def setup_test_environment(base_path: Path):
    """Creates a sample directory structure with files for testing."""
    # Create directories
    (base_path / "dir1").mkdir(parents=True, exist_ok=True)
    (base_path / "dir2").mkdir(parents=True, exist_ok=True)
    # Create test files
    (base_path / "dir1" / "file1.py").write_text("def foo():\n    return 'foo'\n")
    (base_path / "dir1" / "file2.json").write_text('{"key": "value"}')
    (base_path / "dir2" / "file3.py").write_text("")
    (base_path / "dir2" / "file4.xml").write_text("<note>Test</note>")
    (base_path / "file5.csv").write_text("col1,col2\nval1,val2\n")

def test_structure_visualizer():
    """Test that the structure visualizer returns the expected keys and includes test files."""
    with TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        setup_test_environment(base_path)
        result = show_structure_and_list_file_content(base_path=str(base_path), print_output=False)
        assert isinstance(result, dict)
        assert "project_structure" in result
        structure = result["project_structure"]
        assert "dir1" in structure
        assert "dir2" in structure
        assert "file1.py" in structure
        assert "file2.json" in structure

def test_import_visualizer_excludes_files():
    """Test that the import visualizer excludes files provided in the exclude_files argument."""
    with TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        # Create a dummy structure with a Python file importing a module.
        (base_path / "feature").mkdir()
        (base_path / "tools").mkdir()
        (base_path / "feature" / "example.py").write_text("from tools.toolbox import add\n")
        (base_path / "tools" / "toolbox.py").write_text("def add(x,y):\n    return x+y\n")
        # Run structure visualizer to collect files (simulate exclude_files)
        structure_result = show_structure_and_list_file_content(base_path=str(base_path / "feature"), print_output=False)
        exclude_files = structure_result["files"]
        import_result = show_imports_of_feature_path(
            path_where_imports_are_used=str(base_path / "feature"),
            path_where_imports_are_defined=str(base_path),
            whole_module_content=False,
            file_types=[".py"],
            give_file_content=True,
            save_output=False,
            print_output=False,
            exclude_files=exclude_files
        )
        # In this test, since toolbox.py is not in the feature path, it should appear in the import visualizer.
        output = import_result["full_output"]
        assert "toolbox.py" in output

# To run the tests, execute: pytest test_project_feature_visualizer.py

