from pathlib import Path
import subprocess
import tempfile
import zipfile
import json
import pandas as pd


def load_task2_text_files(name_diff_path: str, requirement_diff_path: str) -> tuple[str, str]:
    path1 = Path(name_diff_path)
    path2 = Path(requirement_diff_path)

    if not path1.exists():
        raise FileNotFoundError(f"{name_diff_path} not found")
    if not path2.exists():
        raise FileNotFoundError(f"{requirement_diff_path} not found")

    if path1.suffix.lower() != ".txt":
        raise ValueError(f"{name_diff_path} is not a TXT file")
    if path2.suffix.lower() != ".txt":
        raise ValueError(f"{requirement_diff_path} is not a TXT file")

    text1 = path1.read_text(encoding="utf-8").strip()
    text2 = path2.read_text(encoding="utf-8").strip()

    return text1, text2


def map_differences_to_kubescape_controls(
    name_diff_text: str,
    requirement_diff_text: str,
    output_file: str
) -> list[str]:
    combined_text = f"{name_diff_text}\n{requirement_diff_text}".lower()

    if (
        "no differences in regards to element names" in name_diff_text.lower()
        and "no differences in regards to element requirements" in requirement_diff_text.lower()
    ):
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("NO DIFFERENCES FOUND\n")
        return []

    control_map = {
        "container registries": "C-0001",
        "allowprivilegeescalation": "C-0016",
        "root containers": "C-0013",
        "default service accounts": "C-0034",
        "cluster-admin role": "C-0035",
        "network policies": "C-0030",
        "roles and clusterroles": "C-0035",
        "secrets": "C-0015",
        "security context": "C-0013",
        "privileged containers": "C-0057",
        "host network namespace": "C-0041",
        "host ipc namespace": "C-0040",
        "host process id namespace": "C-0039",
        "service account tokens": "C-0020",
        "amazon ecr access": "C-0001",
        "create pods": "C-0035",
        "namespaces": "C-0030",
        "added capabilities": "C-0058",
        "capabilities assigned": "C-0058",
        "iam authenticator": "C-0035",
        "control plane endpoint": "C-0030",
        "encrypt traffic to https": "C-0030",
    }

    matched_controls = []
    for key, control_id in control_map.items():
        if key in combined_text and control_id not in matched_controls:
            matched_controls.append(control_id)

    with open(output_file, "w", encoding="utf-8") as f:
        if matched_controls:
            for control in matched_controls:
                f.write(control + "\n")
        else:
            f.write("NO DIFFERENCES FOUND\n")

    return matched_controls


def _extract_rows_from_control_objects(control_objects: list) -> list[dict]:
    rows = []

    for control in control_objects:
        if not isinstance(control, dict):
            continue

        control_name = (
            control.get("name")
            or control.get("controlName")
            or control.get("controlID")
            or control.get("id")
            or "Unknown Control"
        )

        severity = control.get("severity") or control.get("status", "Unknown")
        compliance_score = control.get("score", control.get("complianceScore", ""))

        failed_resources = 0
        all_resources = 0

        if isinstance(control.get("resourceCounters"), dict):
            failed_resources = control["resourceCounters"].get("failed", 0)
            all_resources = control["resourceCounters"].get("all", 0)
        elif isinstance(control.get("ResourceCounters"), dict):
            rc = control["ResourceCounters"]
            failed_resources = rc.get("failedResources", 0)
            all_resources = (
                rc.get("failedResources", 0)
                + rc.get("passedResources", 0)
                + rc.get("skippedResources", 0)
            )
        else:
            failed_list = control.get("failedResources") or control.get("failedresources") or []
            all_list = control.get("allResources") or control.get("resources") or []
            if isinstance(failed_list, list):
                failed_resources = len(failed_list)
            if isinstance(all_list, list):
                all_resources = len(all_list)

        file_path = control.get("filePath", "project-yamls.zip")

        rows.append({
            "FilePath": file_path,
            "Severity": severity,
            "Control name": control_name,
            "Failed resources": failed_resources,
            "All Resources": all_resources,
            "Compliance score": compliance_score,
        })

    return rows


def _extract_rows_from_results(results: object) -> list[dict]:
    rows = []

    if not isinstance(results, dict):
        return rows

    # Format 1: old/test format
    if isinstance(results.get("controlReports"), list):
        rows.extend(_extract_rows_from_control_objects(results["controlReports"]))

    if isinstance(results.get("controls"), list):
        rows.extend(_extract_rows_from_control_objects(results["controls"]))

    # Format 2: real Kubescape format
    summary = results.get("summaryDetails", {})
    controls_dict = summary.get("controls", {})

    if isinstance(controls_dict, dict):
        for control_id, control in controls_dict.items():
            if not isinstance(control, dict):
                continue

            control_name = control.get("name", control_id)
            severity = control.get("severity", "Unknown")

            rc = control.get("ResourceCounters", {})
            failed_resources = rc.get("failedResources", 0)
            all_resources = (
                rc.get("failedResources", 0)
                + rc.get("passedResources", 0)
                + rc.get("skippedResources", 0)
            )

            compliance_score = control.get("complianceScore", "")

            rows.append({
                "FilePath": "project-yamls.zip",
                "Severity": severity,
                "Control name": control_name,
                "Failed resources": failed_resources,
                "All Resources": all_resources,
                "Compliance score": compliance_score,
            })

    # dedupe
    unique_rows = []
    seen = set()
    for row in rows:
        key = (
            row["FilePath"],
            row["Severity"],
            row["Control name"],
            row["Failed resources"],
            row["All Resources"],
            row["Compliance score"],
        )
        if key not in seen:
            unique_rows.append(row)
            seen.add(key)

    return unique_rows


def execute_kubescape_scan(
    controls_file: str,
    zip_file_path: str,
    kubescape_command: str = "kubescape",
    raw_json_output_path: str | None = None,
) -> pd.DataFrame:
    controls_path = Path(controls_file)
    zip_path = Path(zip_file_path)

    if not controls_path.exists():
        raise FileNotFoundError(f"{controls_file} not found")
    if not zip_path.exists():
        raise FileNotFoundError(f"{zip_file_path} not found")

    controls_text = controls_path.read_text(encoding="utf-8").strip()

    with tempfile.TemporaryDirectory() as tmpdir:
        extract_dir = Path(tmpdir) / "project_yamls"
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        output_json = Path(tmpdir) / "kubescape_results.json"

        base_cmd = [
            kubescape_command,
            "scan",
            str(extract_dir),
            "--format",
            "json",
            "--output",
            str(output_json),
        ]

        cmd = list(base_cmd)

        if controls_text != "NO DIFFERENCES FOUND":
            controls = [line.strip() for line in controls_text.splitlines() if line.strip()]
            if controls:
                cmd.extend(["--controls", ",".join(controls)])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            subprocess.run(base_cmd, check=True, capture_output=True, text=True)

        if not output_json.exists():
            raise FileNotFoundError("Kubescape did not generate the expected JSON output")

        with open(output_json, "r", encoding="utf-8") as f:
            results = json.load(f)

        if raw_json_output_path is not None:
            Path(raw_json_output_path).write_text(
                json.dumps(results, indent=2),
                encoding="utf-8"
            )

    rows = _extract_rows_from_results(results)

    df = pd.DataFrame(
        rows,
        columns=[
            "FilePath",
            "Severity",
            "Control name",
            "Failed resources",
            "All Resources",
            "Compliance score",
        ],
    )

    return df


def save_scan_results_to_csv(scan_df: pd.DataFrame, output_csv_path: str) -> None:
    required_columns = [
        "FilePath",
        "Severity",
        "Control name",
        "Failed resources",
        "All Resources",
        "Compliance score",
    ]

    for col in required_columns:
        if col not in scan_df.columns:
            raise ValueError(f"Missing required column: {col}")

    scan_df.to_csv(output_csv_path, index=False)