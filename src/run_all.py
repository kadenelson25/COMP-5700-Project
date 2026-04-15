from pathlib import Path
from src.extractor import process_two_pdfs, load_gemma
from src.comparator import (
    load_two_yaml_files,
    compare_kde_names,
    compare_kde_names_and_requirements,
)
from src.executor import (
    load_task2_text_files,
    map_differences_to_kubescape_controls,
    execute_kubescape_scan,
    save_scan_results_to_csv,
)


PDF_PAIRS = {
    1: ("cis-r1.pdf", "cis-r1.pdf"),
    2: ("cis-r1.pdf", "cis-r2.pdf"),
    3: ("cis-r1.pdf", "cis-r3.pdf"),
    4: ("cis-r1.pdf", "cis-r4.pdf"),
    5: ("cis-r2.pdf", "cis-r2.pdf"),
    6: ("cis-r2.pdf", "cis-r3.pdf"),
    7: ("cis-r2.pdf", "cis-r4.pdf"),
    8: ("cis-r3.pdf", "cis-r3.pdf"),
    9: ("cis-r3.pdf", "cis-r4.pdf"),
}


def validate_inputs():
    needed = [
        "cis-r1.pdf",
        "cis-r2.pdf",
        "cis-r3.pdf",
        "cis-r4.pdf",
        "project-yamls.zip",
    ]

    missing = [f for f in needed if not Path(f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required input files: {missing}")


def run_task1():
    base_output_dir = Path("outputs") / "Task 1"
    prompt_type = "few-shot"

    print("Loading Gemma once...")
    tokenizer, model = load_gemma()

    for i, (pdf1, pdf2) in PDF_PAIRS.items():
        input_dir = base_output_dir / f"input{i}"
        yaml_dir = input_dir / "yaml"
        text_dir = input_dir / "text"

        yaml_dir.mkdir(parents=True, exist_ok=True)
        text_dir.mkdir(parents=True, exist_ok=True)

        output_log_file = text_dir / "llm_outputs.txt"

        print(f"Task 1 - Input {i}: {pdf1} and {pdf2}")

        process_two_pdfs(
            pdf1=pdf1,
            pdf2=pdf2,
            prompt_type=prompt_type,
            output_yaml_dir=str(yaml_dir),
            output_log_file=str(output_log_file),
            tokenizer=tokenizer,
            model=model,
        )


def run_task2():
    task1_base = Path("outputs") / "Task 1"

    yaml_pairs = {
        1: ("cis-r1-kdes.yaml", "cis-r1-kdes.yaml"),
        2: ("cis-r1-kdes.yaml", "cis-r2-kdes.yaml"),
        3: ("cis-r1-kdes.yaml", "cis-r3-kdes.yaml"),
        4: ("cis-r1-kdes.yaml", "cis-r4-kdes.yaml"),
        5: ("cis-r2-kdes.yaml", "cis-r2-kdes.yaml"),
        6: ("cis-r2-kdes.yaml", "cis-r3-kdes.yaml"),
        7: ("cis-r2-kdes.yaml", "cis-r4-kdes.yaml"),
        8: ("cis-r3-kdes.yaml", "cis-r3-kdes.yaml"),
        9: ("cis-r3-kdes.yaml", "cis-r4-kdes.yaml"),
    }

    for input_num, (yaml1_name, yaml2_name) in yaml_pairs.items():
        base_dir = task1_base / f"input{input_num}"
        yaml_dir = base_dir / "yaml"

        yaml1_path = yaml_dir / yaml1_name
        yaml2_path = yaml_dir / yaml2_name

        output_dir = base_dir / "comparator"
        output_dir.mkdir(parents=True, exist_ok=True)

        names_output = output_dir / "element_name_differences.txt"
        full_output = output_dir / "element_requirement_differences.txt"

        yaml1_data, yaml2_data = load_two_yaml_files(str(yaml1_path), str(yaml2_path))

        compare_kde_names(
            yaml1_data,
            yaml2_data,
            str(names_output),
            yaml1_path.name,
            yaml2_path.name,
        )

        compare_kde_names_and_requirements(
            yaml1_data,
            yaml2_data,
            str(full_output),
            yaml1_path.name,
            yaml2_path.name,
        )

        print(f"Task 2 complete for input{input_num}")


def run_task3():
    task1_base = Path("outputs") / "Task 1"
    zip_file_path = "project-yamls.zip"

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

        print(f"Task 3 - input{input_num}")

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


def main():
    validate_inputs()
    run_task1()
    run_task2()
    run_task3()
    print("All tasks complete.")


if __name__ == "__main__":
    main()