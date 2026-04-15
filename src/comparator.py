from pathlib import Path
import yaml


def load_two_yaml_files(yaml1_path: str, yaml2_path: str) -> tuple[dict, dict]:
    path1 = Path(yaml1_path)
    path2 = Path(yaml2_path)

    if not path1.exists():
        raise FileNotFoundError(f"{yaml1_path} not found")
    if not path2.exists():
        raise FileNotFoundError(f"{yaml2_path} not found")

    if path1.suffix.lower() not in [".yaml", ".yml"]:
        raise ValueError(f"{yaml1_path} is not a YAML file")
    if path2.suffix.lower() not in [".yaml", ".yml"]:
        raise ValueError(f"{yaml2_path} is not a YAML file")

    with open(path1, "r", encoding="utf-8") as f:
        data1 = yaml.safe_load(f) or {}

    with open(path2, "r", encoding="utf-8") as f:
        data2 = yaml.safe_load(f) or {}

    if not isinstance(data1, dict):
        raise ValueError(f"{yaml1_path} does not contain a valid YAML dictionary")
    if not isinstance(data2, dict):
        raise ValueError(f"{yaml2_path} does not contain a valid YAML dictionary")

    return data1, data2


def _build_name_to_requirements_map(yaml_data: dict) -> dict[str, list[str]]:
    result = {}

    for _, value in yaml_data.items():
        if not isinstance(value, dict):
            continue

        name = value.get("name")
        requirements = value.get("requirements", [])

        if not name:
            continue

        if not isinstance(requirements, list):
            requirements = []

        cleaned_requirements = []
        for req in requirements:
            if isinstance(req, str):
                cleaned_requirements.append(req.strip())

        result[name.strip()] = cleaned_requirements

    return result


def compare_kde_names(
    yaml1_data: dict,
    yaml2_data: dict,
    output_file: str,
    yaml1_filename: str,
    yaml2_filename: str,
) -> list[str]:
    map1 = _build_name_to_requirements_map(yaml1_data)
    map2 = _build_name_to_requirements_map(yaml2_data)

    names1 = set(map1.keys())
    names2 = set(map2.keys())

    only_in_1 = sorted(names1 - names2)
    only_in_2 = sorted(names2 - names1)

    differences = []

    for name in only_in_1:
        differences.append(f"{name},PRESENT-IN-{yaml1_filename},ABSENT-IN-{yaml2_filename}")

    for name in only_in_2:
        differences.append(f"{name},ABSENT-IN-{yaml1_filename},PRESENT-IN-{yaml2_filename}")

    with open(output_file, "w", encoding="utf-8") as f:
        if differences:
            for line in differences:
                f.write(line + "\n")
        else:
            f.write("NO DIFFERENCES IN REGARDS TO ELEMENT NAMES\n")

    return differences


def compare_kde_names_and_requirements(
    yaml1_data: dict,
    yaml2_data: dict,
    output_file: str,
    yaml1_filename: str,
    yaml2_filename: str,
) -> list[str]:
    map1 = _build_name_to_requirements_map(yaml1_data)
    map2 = _build_name_to_requirements_map(yaml2_data)

    names1 = set(map1.keys())
    names2 = set(map2.keys())

    differences = []

    only_in_1 = sorted(names1 - names2)
    only_in_2 = sorted(names2 - names1)
    common_names = sorted(names1 & names2)

    for name in only_in_1:
        differences.append(f"{name},ABSENT-IN-{yaml2_filename},PRESENT-IN-{yaml1_filename},NA")

    for name in only_in_2:
        differences.append(f"{name},ABSENT-IN-{yaml1_filename},PRESENT-IN-{yaml2_filename},NA")

    for name in common_names:
        reqs1 = set(map1[name])
        reqs2 = set(map2[name])

        missing_from_2 = sorted(reqs1 - reqs2)
        missing_from_1 = sorted(reqs2 - reqs1)

        for req in missing_from_2:
            differences.append(f"{name},ABSENT-IN-{yaml2_filename},PRESENT-IN-{yaml1_filename},{req}")

        for req in missing_from_1:
            differences.append(f"{name},ABSENT-IN-{yaml1_filename},PRESENT-IN-{yaml2_filename},{req}")

    with open(output_file, "w", encoding="utf-8") as f:
        if differences:
            for line in differences:
                f.write(line + "\n")
        else:
            f.write("NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS\n")

    return differences