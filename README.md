<<<<<<< HEAD
# COMP 5700 Project

## Team Members
- Kade Nelson — kjn0014@auburn.edu

## LLM Used for Task 1
- `google/gemma-3-1b-it`

## Project Structure
- `src/extractor.py` — Task 1: KDE extraction from PDF requirements documents
- `src/comparator.py` — Task 2: comparison of KDE YAML outputs
- `src/executor.py` — Task 3: Kubescape control mapping and scan execution
- `src/run_all.py` — end-to-end runner for Tasks 1, 2, and 3
- `tests/` — test cases for Tasks 1, 2, and 3
- `outputs/` — generated outputs for all input combinations
- `requirements.txt` — Python dependencies
- `.github/workflows/tests.yml` — GitHub Actions workflow for automated test execution

## Outputs Structure

All outputs are organized by input combination:

`outputs/Task 1/inputX/`

Each input folder corresponds to one of the nine required input combinations.

Inside each input folder:

- `yaml/` → Task 1 YAML outputs for KDE extraction
- `text/` → Task 1 LLM logs and prompt/output text
- `comparator/` → Task 2 TEXT outputs for KDE and requirement differences
- `executor/` → Task 3 outputs:
  - `kubescape_controls.txt`
  - `kubescape_raw_results.json`
  - `kubescape_scan_results.csv`

## Required Input Combinations

The project processes the following nine PDF input pairs:

1. `cis-r1.pdf` and `cis-r1.pdf`
2. `cis-r1.pdf` and `cis-r2.pdf`
3. `cis-r1.pdf` and `cis-r3.pdf`
4. `cis-r1.pdf` and `cis-r4.pdf`
5. `cis-r2.pdf` and `cis-r2.pdf`
6. `cis-r2.pdf` and `cis-r3.pdf`
7. `cis-r2.pdf` and `cis-r4.pdf`
8. `cis-r3.pdf` and `cis-r3.pdf`
9. `cis-r3.pdf` and `cis-r4.pdf`

## How to Run

### Option 1: Run with Python
1. Create and activate a Python virtual environment
2. Install dependencies:
   `pip install -r requirements.txt`
3. Make sure the following files are in the project root:
   - `cis-r1.pdf`
   - `cis-r2.pdf`
   - `cis-r3.pdf`
   - `cis-r4.pdf`
   - `project-yamls.zip`
4. Run the full project:
   `python -m src.run_all`

### Option 2: Run with the provided launcher
Use:

`run_project.bat`

This runs the project inside the Python virtual environment and executes the full pipeline.

## GitHub Actions

This repository includes a GitHub Actions workflow file:

`/.github/workflows/tests.yml`

The workflow automatically runs all test cases for Tasks 1, 2, and 3 on supported GitHub events such as:
- `push`
- `pull_request`
- `workflow_dispatch`

## Binary / Execution Note

A PyInstaller-built executable is included in the repository to satisfy the binary deliverable.

Because this project depends on PyTorch and Transformers, the frozen executable may encounter Windows DLL initialization issues on some systems. For reliable execution in the TA’s Python virtual environment, use:

`run_project.bat`

This launcher runs the same full pipeline using the project’s virtual environment and source code.

## Task Summary

### Task 1: Extractor
- loads PDF requirements documents
- builds zero-shot, few-shot, and chain-of-thought prompts
- uses `google/gemma-3-1b-it`
- outputs KDE YAML files and LLM logs

### Task 2: Comparator
- loads two Task 1 YAML files
- compares KDE names
- compares KDE names and requirements
- outputs difference reports as text files

### Task 3: Executor
- loads Task 2 difference files
- maps differences to Kubescape controls
- runs Kubescape on `project-yamls.zip`
- exports results to CSV format

## Notes
The LLM used for Task 1 is `google/gemma-3-1b-it`.
=======
# COMP-5700-Project
>>>>>>> c390fad4ab813e2173ca68fa6ce56a32cfbdff19
