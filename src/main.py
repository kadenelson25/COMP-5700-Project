from pathlib import Path
from src.extractor import process_two_pdfs, load_gemma


def main():
    pdf_pairs = [
        ("cis-r1.pdf", "cis-r1.pdf"),
        ("cis-r1.pdf", "cis-r2.pdf"),
        ("cis-r1.pdf", "cis-r3.pdf"),
        ("cis-r1.pdf", "cis-r4.pdf"),
        ("cis-r2.pdf", "cis-r2.pdf"),
        ("cis-r2.pdf", "cis-r3.pdf"),
        ("cis-r2.pdf", "cis-r4.pdf"),
        ("cis-r3.pdf", "cis-r3.pdf"),
        ("cis-r3.pdf", "cis-r4.pdf"),
    ]

    prompt_type = "few-shot"
    base_output_dir = Path("outputs")

    print("Loading Gemma once...")
    tokenizer, model = load_gemma()

    for i, (pdf1, pdf2) in enumerate(pdf_pairs, start=1):
        input_dir = base_output_dir / f"input{i}"
        yaml_dir = input_dir / "yaml"
        text_dir = input_dir / "text"

        yaml_dir.mkdir(parents=True, exist_ok=True)
        text_dir.mkdir(parents=True, exist_ok=True)

        output_log_file = text_dir / "llm_outputs.txt"

        print(f"Processing Input-{i}: {pdf1} and {pdf2}")

        process_two_pdfs(
            pdf1=pdf1,
            pdf2=pdf2,
            prompt_type=prompt_type,
            output_yaml_dir=str(yaml_dir),
            output_log_file=str(output_log_file),
            tokenizer=tokenizer,
            model=model
        )

    print("Task 1 complete.")


if __name__ == "__main__":
    main()