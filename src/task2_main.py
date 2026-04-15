from pathlib import Path
from src.comparator import (
    load_two_yaml_files,
    compare_kde_names,
    compare_kde_names_and_requirements,
)


def main():
    task1_base = Path("outputs") / "Task 1"

    input_pairs = {
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

    for input_num, (yaml1_name, yaml2_name) in input_pairs.items():
        base_dir = task1_base / f"input{input_num}"
        yaml_dir = base_dir / "yaml"

        yaml1_path = yaml_dir / yaml1_name
        yaml2_path = yaml_dir / yaml2_name

        if not yaml1_path.exists():
            raise FileNotFoundError(f"Missing file: {yaml1_path}")
        if not yaml2_path.exists():
            raise FileNotFoundError(f"Missing file: {yaml2_path}")

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

    print("Task 2 comparator complete for all inputs.")


if __name__ == "__main__":
    main()