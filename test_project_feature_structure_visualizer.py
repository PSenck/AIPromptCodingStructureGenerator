import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from project_feature_structure_visualizer import show_structure_and_list_file_content  # Replace `script_name` with the actual name of your script file


# Helper function to create test files and directories
def setup_test_environment(base_path):
    # Creating subdirectories and files
    (base_path / "dir1").mkdir(parents=True, exist_ok=True)
    (base_path / "dir2").mkdir(parents=True, exist_ok=True)
    (base_path / "dir1" / "file1.py").write_text("print('Hello from file1!')")
    (base_path / "dir1" / "file2.csv").write_text("column1,column2\nvalue1,value2")
    (base_path / "dir2" / "file3.py").write_text("")
    (base_path / "dir2" / "file4.xml").write_text("<note><body>Test</body></note>")
    (base_path / "file5.json").write_text("{}")


# Test Cases
def test_list_files_structure():
    with TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        setup_test_environment(base_path)

        result = show_structure_and_list_file_content(base_path=str(base_path), print_output=False)

        assert isinstance(result, dict)
        assert "project_structure" in result
        assert "files" in result
        assert "used_args" in result

        # Check that the structure includes expected directories and files
        structure = result["project_structure"]
        assert "dir1" in structure
        assert "dir2" in structure
        assert "file1.py" in structure
        assert "file2.csv" in structure
        assert "file3.py" in structure
        assert "file4.xml" in structure
        assert "file5.json" in structure


def test_exclude_files():
    with TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        setup_test_environment(base_path)

        exclude_files = ["file1.py", (base_path / "dir2" / "file4.xml").as_posix()]
        result = show_structure_and_list_file_content(base_path=str(base_path), exclude_files=exclude_files,
                                                      print_output=False)

        # Ensure excluded files are not in the structure
        structure = result["project_structure"]
        assert "file1.py" not in structure
        assert "file4.xml" not in structure


def test_exclude_folders():
    with TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        setup_test_environment(base_path)

        exclude_folders = ["dir1"]
        result = show_structure_and_list_file_content(base_path=str(base_path), exclude_folders=exclude_folders,
                                                      print_output=False)

        # Ensure excluded folder is not in the output
        structure = result["project_structure"]
        assert "dir1" not in structure


def test_give_file_content():
    with TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        setup_test_environment(base_path)

        result = show_structure_and_list_file_content(base_path=str(base_path), give_file_content=True,
                                                      print_output=False)

        full_output = result["full_output"]
        assert "Hello from file1!" in full_output
        assert "<note><body>Test</body></note>" in full_output


def test_exclude_empty_files():
    with TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        setup_test_environment(base_path)

        result = show_structure_and_list_file_content(base_path=str(base_path), exclude_empty_files=True,
                                                      print_output=False)

        # Ensure empty file is not included in structure
        structure = result["project_structure"]
        assert "file3.py" not in structure


def test_file_types_filter():
    with TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        setup_test_environment(base_path)

        file_types = [".py"]
        result = show_structure_and_list_file_content(base_path=str(base_path), file_types=file_types,
                                                      print_output=False)

        # Ensure only .py files are included
        assert "file1.py" in result["project_structure"]
        assert "file2.csv" not in result["project_structure"]
        assert "file4.xml" not in result["project_structure"]

# Run this file with pytest to automatically test the functionality
