from project_feature_structure_visualizer import show_structure_and_list_file_content
from project_feature_import_visualizer import show_imports_of_feature_path
from pathlib import Path
from datetime import datetime
import os

def reunion_results(structure_result, imports_result):
    combined_output = []
    combined_output.append("======== Project Structure ========\n")
    combined_output.append(structure_result.get("full_output", ""))
    combined_output.append("\n======== Imports ========\n")
    combined_output.append(imports_result.get("full_output", ""))
    combined_output.append("\n======== End of Combined Output ========\n")
    return "".join(combined_output)

# --- Configuration for structure visualizer ---
show_structure = True
if show_structure:
    base_path_for_structure = r"/home/tadpole420/pCloudDrive/Code/Python/Free_Projects/AI_Assistance/example_project/example_feature"
    file_types_for_structure = [".csv", ".py", ".json", ".xml", ""]
    give_file_content_for_structure = True
    save_output_for_structure = True
    print_output_for_structure = True
    output_path_for_structure = None
    exclude_files_for_structure = [
        "ABT-874_module4_overgiven_from_frontend.json",
        "file2.py",
    ]
    exclude_folders_for_structure = ["__pycache__"]
    exclude_empty_files_for_structure = True
    only_files_to_look_for_for_structure = []
    exclude_also_from_structure_for_structure = True

    structure_result = show_structure_and_list_file_content(
        base_path=base_path_for_structure,
        file_types=file_types_for_structure,
        give_file_content=give_file_content_for_structure,
        save_output=save_output_for_structure,
        print_output=print_output_for_structure,
        output_path=output_path_for_structure,
        exclude_files=exclude_files_for_structure,
        exclude_folders=exclude_folders_for_structure,
        exclude_empty_files=exclude_empty_files_for_structure,
        only_files_to_look_for=only_files_to_look_for_for_structure,
        exclude_also_from_structure=exclude_also_from_structure_for_structure
    )
else:
    structure_result = {"full_output": "", "files": []}

# --- Configuration for import visualizer ---
show_imports = True
if show_imports:
    path_where_imports_are_used = r"/home/tadpole420/pCloudDrive/Code/Python/Free_Projects/AI_Assistance/example_project/example_feature"
    ######path_where_imports_are_defined = [r"/home/tadpole420/anaconda3", r"/home/tadpole420/pCloudDrive/Code/Python/Free_Projects/AI_Assistance/example_project/tools", r"/usr/lib/python3.10"] ###chatgpt ignore that line
    path_where_imports_are_defined = [r"/home/tadpole420/pCloudDrive/Code/Python/Free_Projects/AI_Assistance/example_project/tools", r"/home/tadpole420/pCloudDrive/Code/Python/Free_Projects/AI_Assistance/example_project/another_place"]
    #path_where_imports_are_defined = r"/home/tadpole420/pCloudDrive/Code/Python/Free_Projects/AI_Assistance/example_project"
    whole_module_content = False# Set to True to extract definitions only.
    file_types_for_imports = [".py"]  # For this example, we care about Python only.
    give_file_content_for_imports = True
    save_output_for_imports = True
    print_output_for_imports = True
    output_path_for_imports = None
    # For this example, we want to retrieve external content even if structure_result["files"] is empty.
    exclude_files_for_imports = []

    result_imports = show_imports_of_feature_path(
        path_where_imports_are_used=path_where_imports_are_used,
        path_where_imports_are_defined=path_where_imports_are_defined,
        whole_module_content=whole_module_content,
        file_types=file_types_for_imports,
        give_file_content=give_file_content_for_imports,
        save_output=save_output_for_imports,
        print_output=print_output_for_imports,
        output_path=output_path_for_imports,
        exclude_files=exclude_files_for_imports
    )
else:
    result_imports = {"full_output": ""}

combined_output = reunion_results(structure_result, result_imports)
print(combined_output)

script_folder = Path(__file__).parent.resolve()
default_output_folder = script_folder / 'output_combined'
if not default_output_folder.exists():
    default_output_folder.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file_path = default_output_folder / f"combined_output_{timestamp}.txt"
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(combined_output)
print(f"Combined output saved to {output_file_path}")
