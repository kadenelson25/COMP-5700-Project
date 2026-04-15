from pathlib import Path
from src.executor import (
    load_task2_text_files,
    map_differences_to_kubescape_controls,
    execute_kubescape_scan,
    save_scan_results_to_csv,
)


def main():
    task1_base = Path("outputs") / "Task 1"

    for input_num in range(1, 10):
        base_dir = task1_base / f"input{input_num}"
        comparator_dir = base_dir / "comparator"
        executor_dir = base_dir / "executor"

        executor_dir.mkdir(parents=True, exist_ok=True)

        name_diff_file = comparator_dir / "element_name_differences.txt"
        req_diff_file = comparator_dir / "element_requirement_differences.txt"

        controls_output_file = executor_dir / "kubescape_controls.txt"
        csv_output_file = executor_dir / "kubescape_scan_results.csv"
        raw_json_output_file = executor_dir / "kubescape_raw_results.json"

        zip_file_path = "project-yamls.zip"

        if not name_diff_file.exists():
            raise FileNotFoundError(f"Missing file: {name_diff_file}")
        if not req_diff_file.exists():
            raise FileNotFoundError(f"Missing file: {req_diff_file}")

        print(f"Running Task 3 for input{input_num}...")

        name_diff_text, req_diff_text = load_task2_text_files(
            str(name_diff_file),
            str(req_diff_file),
        )

        map_differences_to_kubescape_controls(
            name_diff_text,
            req_diff_text,
            str(controls_output_file),
        )

        scan_df = execute_kubescape_scan(
            str(controls_output_file),
            zip_file_path,
            raw_json_output_path=str(raw_json_output_file),
        )

        save_scan_results_to_csv(scan_df, str(csv_output_file))

        print(f"Task 3 complete for input{input_num}")

    print("Task 3 executor complete for all inputs.")


if __name__ == "__main__":
    main()