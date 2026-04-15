import tempfile
from pathlib import Path

import yaml
import pytest

from src import extractor


def test_load_two_documents_validation():
    with pytest.raises(FileNotFoundError):
        extractor.load_two_documents("missing1.pdf", "missing2.pdf")


def test_build_zero_shot_prompt_returns_string():
    prompt = extractor.build_zero_shot_prompt(
        "3.1.1 Ensure that the kubeconfig file permissions are set to 644 or more restrictive (Manual)"
    )
    assert isinstance(prompt, str)
    assert "KDE:" in prompt or "key data elements" in prompt


def test_build_few_shot_prompt_returns_string():
    prompt = extractor.build_few_shot_prompt(
        "3.2.3 Ensure that a Client CA File is Configured (Manual)"
    )
    assert isinstance(prompt, str)
    assert "Example:" in prompt or "client ca file" in prompt.lower()


def test_build_chain_of_thought_prompt_returns_string():
    prompt = extractor.build_chain_of_thought_prompt(
        "3.2.4 Ensure that the --read-only-port is disabled (Manual)"
    )
    assert isinstance(prompt, str)
    assert "Think privately" in prompt or "KDE:" in prompt


def test_extract_kdes_from_pdf_writes_yaml(monkeypatch):
    sample_doc_text = """
    3.1.1 Ensure that the kubeconfig file permissions are set to 644 or more restrictive (Manual)
    3.2.1 Ensure that the Anonymous Auth is Not Enabled (Automated)
    3.2.3 Ensure that a Client CA File is Configured (Manual)
    """

    fake_output = """
KDE: kubeconfig file || REQ: 3.1.1 Ensure that the kubeconfig file permissions are set to 644 or more restrictive (Manual)
KDE: anonymous auth || REQ: 3.2.1 Ensure that the Anonymous Auth is Not Enabled (Automated)
KDE: client ca file || REQ: 3.2.3 Ensure that a Client CA File is Configured (Manual)
""".strip()

    monkeypatch.setattr(extractor, "load_pdf_text", lambda _: sample_doc_text)
    monkeypatch.setattr(extractor, "load_gemma", lambda: ("fake_tokenizer", "fake_model"))
    monkeypatch.setattr(extractor, "generate_llm_output", lambda *args, **kwargs: fake_output)

    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = Path(tmpdir) / "yaml"
        text_dir = Path(tmpdir) / "text"
        yaml_dir.mkdir()
        text_dir.mkdir()

        result = extractor.extract_kdes_from_pdf(
            pdf_path="cis-r1.pdf",
            prompt_type="few-shot",
            output_yaml_dir=str(yaml_dir),
            output_log_file=str(text_dir / "llm_outputs.txt"),
            tokenizer="fake_tokenizer",
            model="fake_model",
        )

        output_yaml = yaml_dir / "cis-r1-kdes.yaml"
        assert output_yaml.exists()
        assert isinstance(result, dict)
        assert "element1" in result

        with open(output_yaml, "r", encoding="utf-8") as f:
            saved = yaml.safe_load(f)

        assert isinstance(saved, dict)
        assert any(v["name"] == "kubeconfig file" for v in saved.values())


def test_process_two_pdfs_returns_two_dicts(monkeypatch):
    sample_doc_text = """
    3.1.1 Ensure that the kubeconfig file permissions are set to 644 or more restrictive (Manual)
    3.2.1 Ensure that the Anonymous Auth is Not Enabled (Automated)
    """

    fake_output = """
KDE: kubeconfig file || REQ: 3.1.1 Ensure that the kubeconfig file permissions are set to 644 or more restrictive (Manual)
KDE: anonymous auth || REQ: 3.2.1 Ensure that the Anonymous Auth is Not Enabled (Automated)
""".strip()

    monkeypatch.setattr(extractor, "load_pdf_text", lambda _: sample_doc_text)
    monkeypatch.setattr(extractor, "generate_llm_output", lambda *args, **kwargs: fake_output)

    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = Path(tmpdir) / "yaml"
        text_dir = Path(tmpdir) / "text"
        yaml_dir.mkdir()
        text_dir.mkdir()

        result1, result2 = extractor.process_two_pdfs(
            pdf1="cis-r1.pdf",
            pdf2="cis-r2.pdf",
            prompt_type="few-shot",
            output_yaml_dir=str(yaml_dir),
            output_log_file=str(text_dir / "llm_outputs.txt"),
            tokenizer="fake_tokenizer",
            model="fake_model",
        )

        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert "element1" in result1
        assert "element1" in result2