import os
from pathlib import Path
from datetime import datetime

START_N_START_MULTIPLIER = 2
START_N_END_MULTIPLIER = 2
END_N_START_MULTIPLIER = 2
END_N_END_MULTIPLIER = 2


FILE_CONTENT_START = "----------------------------------File content of >>> {file_path.name} <<< start-----------------------------------"
FILE_CONTENT_END= "----------------------------------File content of >>> {file_path.name} <<< end-----------------------------------" #* 0
PROJECT_STRUCTURE_START = "----------------------------------project structure start-----------------------------------"
PROJECT_STRUCTURE_END = "----------------------------------project structure end-----------------------------------" #* 0
OUTPUTTING_FILE_CONTENT_OF_EACH_FILE_START = "----------------------------------outputting file content of each file start-----------------------------------"
OUTPUTTING_FILE_CONTENT_OF_EACH_FILE_END = "----------------------------------outputting file content of each file end-----------------------------------" #* 0



def show_structure_and_list_file_content(
    base_path: str,
    file_types=None,
    give_file_content=False,
    save_output=False,
    print_output=False,
    output_path=None,
    exclude_files=None,
    exclude_folders=None,
    exclude_empty_files=False,
    only_files_to_look_for=None,
    exclude_also_from_structure=False
):
    """
    Lists files and directory structures, optionally filtering by file type and certain files or folders.
    Can also output file contents and save the results to a file.

    Args:
        base_path (str): The directory path to start listing files and folders from.
        file_types (list, optional): List of file extensions to include. If None, all file types are included.
        give_file_content (bool, optional): If True, include the contents of the files in the output.
        save_output (bool, optional): If True, save the structure and contents to a text file.
        print_output (bool, optional): If True, print the structure and contents formatted output to the console.
        output_path (Path or str, optional): Directory where the output file will be saved. Defaults to a subdirectory of the script's location.
        exclude_files (list or str, optional): Specific filenames or paths to exclude. Can be a single path or a list of paths.
        exclude_folders (list or str, optional): Specific folders or paths to exclude. Can be a single path or a list of paths.
        exclude_empty_files (bool, optional): If True, exclude empty files from the output.
        only_files_to_look_for (list or str, optional): Specific filenames or paths to include exclusively in the search.
        exclude_also_from_structure (bool, optional): If True, only show directory structure for files meeting all criteria.

    Returns:
        dict: Contains the complete project structure, list of files found, used arguments, and full output string.
    """

    # Initialize file type list if not provided
    if file_types is None:
        file_types = []

    # Handle list conversion for various inputs where necessary
    if isinstance(exclude_files, str):
        exclude_files = [exclude_files]
    elif exclude_files is None:
        exclude_files = []

    if isinstance(exclude_folders, str):
        exclude_folders = [exclude_folders]
    elif exclude_folders is None:
        exclude_folders = []

    if isinstance(only_files_to_look_for, str):
        only_files_to_look_for = [only_files_to_look_for]
    elif only_files_to_look_for is None:
        only_files_to_look_for = []

    # Resolve paths for exclude lists and only-look-for lists
    exclude_files_set = {Path(f).resolve() for f in exclude_files}
    exclude_folders_set = {Path(f).resolve() for f in exclude_folders}
    only_files_to_look_for_paths = {Path(f).resolve() for f in only_files_to_look_for}

    files_found = []
    full_output_parts = []

    def should_include_file(file_path):
        """
        Determine whether a file should be included based on its name, type, conditions like emptiness or exclusion,
        and only-files-to-look-for criteria.

        Args:
            file_path (Path): Path object representing the file to check.

        Returns:
            bool: True if the file should be included; False otherwise.
        """
        # Exclusions checks
        if file_path in exclude_files_set or any(file_path.match(f'*{ex}') for ex in exclude_files):
            return False

        # Only-look-for checks
        if only_files_to_look_for:
            if file_path.name not in only_files_to_look_for and file_path not in only_files_to_look_for_paths and not any(
                    file_path.match(f'*{Path(name)}') for name in only_files_to_look_for):
                return False

        # Type and condition checks
        include_based_on_type = not file_types or any(file_path.name.endswith(ft) for ft in file_types)
        exclude_based_on_conditions = (
            (exclude_empty_files and file_path.stat().st_size == 0)
        )

        return include_based_on_type and not exclude_based_on_conditions

    def should_include_directory(item):
        """
        Determine whether a directory should be included in structure output when exclude_also_from_structure is True.

        Args:
            item (Path): Path object representing the directory to check.

        Returns:
            bool: True if the directory should be included; False otherwise.
        """
        if item in exclude_folders_set or any(item.match(f'*{ex}') for ex in exclude_folders):
            return False

        # Check if directory contains files meeting inclusion criteria
        for subitem in item.rglob('*'):
            if should_include_file(subitem):
                return True

        return False

    def print_structure(base_path, indent='', file_output=None, collect_structure=True):
        """
        Recursively writes the directory structure to output based on exclusion and collateral constraint settings.

        Args:
            base_path (Path): Directory path to iterate over
            indent (str): Indentation string for nested directory structures
            file_output (file object, optional): File object to write structure to if indicated
            collect_structure (bool): Flag to collect output into full_output_parts for final output construction
        """
        items = sorted(base_path.iterdir(), key=lambda x: (x.is_file(), str(x).lower()))

        for item in items:
            if item.is_dir():
                # Deciding inclusion of directories based on exclusion settings and matching criteria
                if not exclude_also_from_structure or should_include_directory(item):
                    line = f"{indent}• {item.name}\n"
                    full_output_parts.append(line)
                    if file_output:
                        file_output.write(line)
                    print_structure(item, indent + "\t", file_output, collect_structure)
            elif item.is_file() and (not exclude_also_from_structure or should_include_file(item)):
                line = f"{indent}○ {item.name}\n"
                files_found.append(str(item.resolve()))
                full_output_parts.append(line)
                if file_output:
                    file_output.write(line)

    def print_file_contents(base_path, file_output=None):
        """
        Recursively writes content of specified files in the directory to components

        Args:
            base_path (Path): Directory path to iterate over
            file_output (file object, optional): File object to write contents in if specified
        """
        items = sorted(base_path.iterdir(), key=lambda x: (x.is_file(), str(x).lower()))
        for item in items:
            if item.is_file() and should_include_file(item):
                if not (exclude_empty_files and item.stat().st_size == 0):
                    file_content(item, file_output)
            elif item.is_dir() and (not exclude_also_from_structure or should_include_directory(item)):
                print_file_contents(item, file_output)

    def file_content(file_path, file_output):
        """
        Append the file content along with its start-and-end markers to output components.

        Args:
            file_path (Path): Path to the file whose content is being written
            file_output (file object, optional): File object to write content to if specified
        """
        content_start = f"{file_path}\n"
        content_start += "\n" * START_N_START_MULTIPLIER + FILE_CONTENT_START.replace("{file_path.name}", file_path.name) + "\n" * START_N_END_MULTIPLIER
        full_output_parts.append(content_start)
        if file_output:
            file_output.write(content_start)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                full_output_parts.append(line)
                if file_output:
                    file_output.write(line)

        content_end = "\n" * END_N_START_MULTIPLIER + FILE_CONTENT_END.replace("{file_path.name}", file_path.name)  + "\n" * END_N_END_MULTIPLIER
        full_output_parts.append(content_end)
        if file_output:
            file_output.write(content_end)

    # Default output path initialization, ensuring directory exists
    script_folder = Path(__file__).parent.resolve()
    default_output_folder = script_folder / 'output_project_feature_structure_visualizer'
    if output_path is None:
        output_path = default_output_folder

    output_path = Path(output_path)
    if save_output and not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    # Prepare header and footer for output structure
    file_types_str = ", ".join(file_types) if file_types else "all files"
    header = f"Structure [{file_types_str}] from folder [{base_path}]:\n"
    header += "\n" * START_N_START_MULTIPLIER + PROJECT_STRUCTURE_START + "\n" * START_N_END_MULTIPLIER
    footer = "\n" * END_N_START_MULTIPLIER + PROJECT_STRUCTURE_END + "\n" * END_N_END_MULTIPLIER

    # Constructing full output with headers
    full_output_parts.insert(0, header)
    full_output_parts.append(footer)

    # Display empty or selective structure based on `exclude_also_from_structure`
    print_structure(Path(base_path).resolve())

    # If specified, generate content output within designated sections
    if give_file_content:
        full_output_parts.append(
            "\n" * START_N_START_MULTIPLIER + OUTPUTTING_FILE_CONTENT_OF_EACH_FILE_START + "\n" * START_N_END_MULTIPLIER)
        print_file_contents(Path(base_path).resolve())
        full_output_parts.append(
            "\n" * END_N_START_MULTIPLIER + OUTPUTTING_FILE_CONTENT_OF_EACH_FILE_END + "\n" * END_N_END_MULTIPLIER)

    full_output = "".join(full_output_parts)

    # Console interaction to communicate output decision
    if print_output:
        print(full_output)

    # Write to selected file if directed
    if save_output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = output_path / f"output_{os.path.basename(__file__).split('.py')[0]}_{timestamp}.txt"
        with open(output_file_path, "w", encoding="utf-8") as file_output:
            file_output.write(full_output)
        print(f"Output saved to {output_file_path}")

    # Clear outputs and return statement reflecting used arguments
    used_args = {
        "base_path": base_path,
        "file_types": file_types,
        "give_file_content": give_file_content,
        "save_output": save_output,
        "output_path": output_path,
        "exclude_files": exclude_files,
        "exclude_empty_files": exclude_empty_files,
        "exclude_also_from_structure": exclude_also_from_structure,
        "exclude_folders": exclude_folders,
        "print_output": print_output,
        "only_files_to_look_for": only_files_to_look_for
    }

    return {
        "project_structure": header + "".join(full_output_parts[1:-1]) + footer,
        "files": files_found,
        "used_args": used_args,
        "full_output": full_output
    }


# Usage example
base_path = r"/home/tadpole420/pCloudDrive/Code/Python/Free_Projects/AI_Assistance/example_project"
file_types = [".csv", ".py", ".json", ".xml", ""]
give_file_content = True
save_output = True
print_output = True
output_path = None  # Use None to default to the script directory in 'output_project_feature_visualizer'
exclude_files = [
    "ABT-874_module4_overgiven_from_frontend.json",
    "file2.py",
]  # Example files to be excluded from content output
exclude_folders = ["__pycache__"]  # Example folders to be conditionally excluded
exclude_empty_files =  False# Exclude empty files from file content output
only_files_to_look_for = []  # Example of specific files to look for
exclude_also_from_structure = True # Exclude specified files also from structure at the beginning


result = show_structure_and_list_file_content(
    base_path,
    file_types,
    give_file_content,
    save_output,
    print_output,
    output_path,
    exclude_files,
    exclude_folders,
    exclude_empty_files,
    only_files_to_look_for,
    exclude_also_from_structure
)
print(result)

