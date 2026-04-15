import tempfile
from pathlib import Path
import zipfile
import pandas as pd

from src.executor import (
    load_task2_text_files,
    map_differences_to_kubescape_controls,
    execute_kubescape_scan,
    save_scan_results_to_csv,
)


def test_load_task2_text_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "a.txt"
        p2 = Path(tmpdir) / "b.txt"

        p1.write_text("hello", encoding="utf-8")
        p2.write_text("world", encoding="utf-8")

        text1, text2 = load_task2_text_files(str(p1), str(p2))

        assert text1 == "hello"
        assert text2 == "world"


def test_map_differences_to_kubescape_controls():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "controls.txt"

        name_diff = "authorization mode,PRESENT-IN-a,ABSENT-IN-b"
        req_diff = "network policies,ABSENT-IN-a,PRESENT-IN-b,REQ1"

        controls = map_differences_to_kubescape_controls(
            name_diff,
            req_diff,
            str(output_file),
        )

        text = output_file.read_text(encoding="utf-8")
        assert isinstance(controls, list)
        assert "C-0030" in controls
        assert "C-0030" in text


def test_execute_kubescape_scan(monkeypatch):
    fake_json = {
        "controlReports": [
            {
                "name": "RBAC Enabled",
                "severity": "medium",
                "resourceCounters": {"failed": 1, "all": 3},
                "score": 66,
                "filePath": "deployment.yaml",
            }
        ]
    }

    def fake_run(cmd, check, capture_output, text):
        output_index = cmd.index("--output") + 1
        output_path = Path(cmd[output_index])
        output_path.write_text(__import__("json").dumps(fake_json), encoding="utf-8")

        class Result:
            stdout = "ok"
            stderr = ""
            returncode = 0

        return Result()

    monkeypatch.setattr("src.executor.subprocess.run", fake_run)

    with tempfile.TemporaryDirectory() as tmpdir:
        controls_file = Path(tmpdir) / "controls.txt"
        controls_file.write_text("C-0030\n", encoding="utf-8")

        zip_path = Path(tmpdir) / "project-yamls.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            sample_yaml = Path(tmpdir) / "sample.yaml"
            sample_yaml.write_text("apiVersion: v1\nkind: Pod\n", encoding="utf-8")
            zf.write(sample_yaml, arcname="sample.yaml")

        df = execute_kubescape_scan(str(controls_file), str(zip_path))

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["Control name"] == "RBAC Enabled"


def test_save_scan_results_to_csv():
    df = pd.DataFrame([
        {
            "FilePath": "deployment.yaml",
            "Severity": "medium",
            "Control name": "RBAC Enabled",
            "Failed resources": 1,
            "All Resources": 3,
            "Compliance score": 66,
        }
    ])

    with tempfile.TemporaryDirectory() as tmpdir:
        output_csv = Path(tmpdir) / "results.csv"
        save_scan_results_to_csv(df, str(output_csv))

        assert output_csv.exists()
        text = output_csv.read_text(encoding="utf-8")
        assert "FilePath" in text
        assert "RBAC Enabled" in text