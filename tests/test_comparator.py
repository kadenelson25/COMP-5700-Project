import tempfile
from pathlib import Path

from src.comparator import (
    load_two_yaml_files,
    compare_kde_names,
    compare_kde_names_and_requirements,
)


def test_load_two_yaml_files():
    yaml1 = """
element1:
  name: audit logs
  requirements:
    - Enable audit logs
"""
    yaml2 = """
element1:
  name: client ca file
  requirements:
    - Ensure that a Client CA File is Configured
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = Path(tmpdir) / "a.yaml"
        path2 = Path(tmpdir) / "b.yaml"

        path1.write_text(yaml1, encoding="utf-8")
        path2.write_text(yaml2, encoding="utf-8")

        data1, data2 = load_two_yaml_files(str(path1), str(path2))

        assert isinstance(data1, dict)
        assert isinstance(data2, dict)
        assert data1["element1"]["name"] == "audit logs"
        assert data2["element1"]["name"] == "client ca file"


def test_compare_kde_names():
    yaml1_data = {
        "element1": {
            "name": "audit logs",
            "requirements": ["Enable audit logs"]
        }
    }

    yaml2_data = {
        "element1": {
            "name": "client ca file",
            "requirements": ["Ensure that a Client CA File is Configured"]
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "name_diff.txt"

        differences = compare_kde_names(
            yaml1_data,
            yaml2_data,
            str(output_file),
            "file1.yaml",
            "file2.yaml",
        )

        assert len(differences) == 2
        text = output_file.read_text(encoding="utf-8")
        assert "audit logs" in text
        assert "client ca file" in text


def test_compare_kde_names_and_requirements():
    yaml1_data = {
        "element1": {
            "name": "audit logs",
            "requirements": [
                "Enable audit logs",
                "Collect audit logs"
            ]
        }
    }

    yaml2_data = {
        "element1": {
            "name": "audit logs",
            "requirements": [
                "Enable audit logs"
            ]
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "full_diff.txt"

        differences = compare_kde_names_and_requirements(
            yaml1_data,
            yaml2_data,
            str(output_file),
            "file1.yaml",
            "file2.yaml",
        )

        assert len(differences) == 1
        text = output_file.read_text(encoding="utf-8")
        assert "audit logs" in text
        assert "Collect audit logs" in text