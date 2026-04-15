from pathlib import Path
from pypdf import PdfReader
import yaml
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re
from collections import OrderedDict


MODEL_ID = "google/gemma-3-1b-it"


def load_pdf_text(pdf_path: str) -> str:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"{pdf_path} not found")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"{pdf_path} is not a PDF file")

    reader = PdfReader(pdf_path)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    full_text = "\n".join(text_parts).strip()

    if not full_text:
        raise ValueError(f"No text could be extracted from {pdf_path}")

    return full_text


def load_two_documents(pdf1: str, pdf2: str) -> tuple[str, str]:
    return load_pdf_text(pdf1), load_pdf_text(pdf2)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_pdf_text_for_extraction(doc_text: str) -> str:
    text = doc_text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    # Cut off appendix / mapping sections that pollute extraction
    end_markers = [
        "Appendix: CIS Controls",
        "Appendix CIS Controls",
        "Mapped Recommendations",
        "Recommendation Set Correctly",
        "CIS Controls v7",
        "CIS Controls v8",
    ]
    for marker in end_markers:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
            break

    return text


def extract_candidate_requirements(doc_text: str) -> list[str]:
    """
    Extract complete CIS control titles like:
    3.2.4 Ensure that the --read-only-port is disabled (Manual)

    This avoids broken fragments such as:
    3.2.4 Ensure that
    """
    text = clean_pdf_text_for_extraction(doc_text)

    # This finds only numbered controls whose title ends with (Manual) or (Automated)
    pattern = re.compile(
        r"(\d+\.\d+\.\d+\s+.*?\((?:Manual|Automated)\))",
        re.IGNORECASE
    )

    matches = pattern.findall(text)

    cleaned = []
    seen = set()

    for match in matches:
        req = normalize_space(match)

        # Throw away obvious bad captures
        lower = req.lower()
        if any(bad in lower for bad in [
            "table of contents",
            "terms of use",
            "copyright",
            "contact information",
            "intended audience",
            "typographical conventions",
            "recommendation definitions",
            "overview",
            "summary",
            "key stakeholders",
            "exceptions",
            "references",
            "assessment status",
            "profile",
            "description",
            "rationale statement",
            "impact statement",
            "audit procedure",
            "audit method",
            "remediation",
            "example",
            "page ",
            "cis legal",
            "kubectl proxy",
            "curl http",
            "sudo less",
            "cat /etc/",
            "ps -ef | grep kubelet",
        ]):
            continue

        # Remove repeated section headers accidentally glued on
        req = re.sub(r"\b\d+\s+Worker Nodes\b.*?$", "", req, flags=re.IGNORECASE)
        req = re.sub(r"\b\d+\.\d+\s+Kubelet\b.*?$", "", req, flags=re.IGNORECASE)
        req = re.sub(r"\b\d+\s+Policies\b.*?$", "", req, flags=re.IGNORECASE)
        req = re.sub(r"\b\d+\.\d+\s+RBAC and Service Accounts\b.*?$", "", req, flags=re.IGNORECASE)
        req = re.sub(r"\b\d+\.\d+\s+CNI Plugin\b.*?$", "", req, flags=re.IGNORECASE)
        req = normalize_space(req)

        # Must still look like a full control title
        if not re.match(
            r"^\d+\.\d+\.\d+\s+(Ensure that|Enable|Prefer|Disable|Minimize|Avoid|Consider|Apply|Create|Restrict|Manage|Encrypt)\b.+\((Manual|Automated)\)$",
            req,
            re.IGNORECASE
        ):
            continue

        # Reject super-short fragments
        body = re.sub(r"^\d+\.\d+\.\d+\s+", "", req)
        if len(body.split()) < 5:
            continue

        if req not in seen:
            cleaned.append(req)
            seen.add(req)

    return cleaned


def heuristic_kde_name(requirement: str) -> str:
    req = requirement.lower()
    req = re.sub(r"^\d+\.\d+\.\d+\s+", "", req).strip()

    patterns = [
        ("audit logs", ["audit logs", "audit logging"]),
        ("kubeconfig file", ["kubeconfig file"]),
        ("kubelet configuration file", ["kubelet configuration file"]),
        ("anonymous auth", ["anonymous auth"]),
        ("authorization mode", ["authorization-mode", "authorization mode"]),
        ("client ca file", ["client ca file"]),
        ("read-only-port", ["read-only-port"]),
        ("streaming connection idle timeout", ["streaming-connection-idle-timeout"]),
        ("protect kernel defaults", ["protect-kernel-defaults"]),
        ("iptables util chains", ["make-iptables-util-chains"]),
        ("hostname override", ["hostname-override"]),
        ("event record qps", ["eventrecordqps", "event record qps"]),
        ("rotate certificates", ["rotate-certificates"]),
        ("rotate kubelet server certificate", ["rotatekubeletservercertificate", "rotate kubelet server certificate"]),
        ("container optimized os", ["container-optimized os"]),
        ("cluster-admin role", ["cluster-admin role"]),
        ("secrets", ["secrets"]),
        ("roles and clusterroles", ["roles and clusterroles"]),
        ("create pods", ["create pods"]),
        ("default service accounts", ["default service accounts"]),
        ("service account tokens", ["service account tokens"]),
        ("system masters group", ["system:masters group"]),
        ("privileged containers", ["privileged containers"]),
        ("host process id namespace", ["host process id namespace"]),
        ("host ipc namespace", ["host ipc namespace"]),
        ("host network namespace", ["host network namespace"]),
        ("allowprivilegeescalation", ["allowprivilegeescalation"]),
        ("root containers", ["root containers"]),
        ("added capabilities", ["added capabilities"]),
        ("capabilities assigned", ["capabilities assigned"]),
        ("cni plugin", ["cni plugin"]),
        ("network policies", ["network policies"]),
        ("secrets as files", ["secrets as files"]),
        ("external secret storage", ["external secret storage"]),
        ("namespaces", ["namespaces"]),
        ("security context", ["security context"]),
        ("default namespace", ["default namespace"]),
        ("image vulnerability scanning", ["image vulnerability scanning"]),
        ("amazon ecr access", ["amazon ecr"]),
        ("container registries", ["container registries"]),
        ("dedicated eks service accounts", ["dedicated eks service accounts"]),
        ("control plane endpoint", ["control plane endpoint"]),
        ("private endpoint", ["private endpoint"]),
        ("private nodes", ["private nodes"]),
        ("network policy", ["network policy"]),
        ("fargate", ["fargate"]),
        ("iam authenticator", ["iam authenticator"]),
    ]

    for name, keys in patterns:
        if any(k in req for k in keys):
            return name

    m = re.search(r"ensure that (.+?)( is | are | argument | file | port | should )", req)
    if m:
        phrase = m.group(1).strip(" -")
        if phrase:
            return phrase[:60]

    words = re.findall(r"[a-zA-Z0-9\-]+", req)
    return " ".join(words[:4]).lower() if words else "general security setting"


def build_grouping_prompt(requirements: list[str]) -> str:
    joined = "\n".join(f"- {r}" for r in requirements)

    return f"""
You are helping group security benchmark requirements into key data elements.

For each requirement below, assign a short KDE name.

Return exactly one line per requirement in this format:
KDE: <short name> || REQ: <full requirement>

Rules:
- Keep KDE names short and specific
- Use names like: audit logs, kubeconfig file, anonymous auth, client ca file, read-only-port
- Do not explain
- Do not use markdown
- Do not omit any requirement
- Do not rewrite the requirement text
- Every requirement must appear exactly once

Requirements:
{joined}
""".strip()


def build_zero_shot_prompt(doc_text: str) -> str:
    return build_grouping_prompt(extract_candidate_requirements(doc_text))


def build_few_shot_prompt(doc_text: str) -> str:
    requirements = extract_candidate_requirements(doc_text)
    joined = "\n".join(f"- {r}" for r in requirements)

    return f"""
You are helping group security benchmark requirements into key data elements.

Example:
KDE: audit logs || REQ: 2.1.1 Enable audit Logs (Manual)
KDE: read-only-port || REQ: 3.2.4 Ensure that the --read-only-port is disabled (Manual)
KDE: client ca file || REQ: 3.2.3 Ensure that a Client CA File is Configured (Manual)

Now do the same for the requirements below.

Rules:
- Keep KDE names short and specific
- Do not explain
- Do not use markdown
- Do not omit any requirement
- Do not rewrite the requirement text
- Every requirement must appear exactly once

Requirements:
{joined}
""".strip()


def build_chain_of_thought_prompt(doc_text: str) -> str:
    requirements = extract_candidate_requirements(doc_text)
    joined = "\n".join(f"- {r}" for r in requirements)

    return f"""
Think privately about the best KDE name for each requirement.

Then output only lines in this format:
KDE: <short name> || REQ: <full requirement>

Do not explain your reasoning.
Do not omit any requirement.
Do not rewrite the requirement text.

Requirements:
{joined}
""".strip()


def load_gemma():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        dtype=torch.float32
    )
    return tokenizer, model


def generate_llm_output(prompt: str, tokenizer, model, max_new_tokens: int = 400) -> str:
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False
    )
    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True)


def parse_kde_assignment_output(output_text: str, original_requirements: list[str]) -> dict:
    grouping = OrderedDict()
    assigned_originals = set()

    for raw_line in output_text.splitlines():
        line = normalize_space(raw_line)
        if not line:
            continue

        m = re.match(r"^KDE:\s*(.*?)\s*\|\|\s*REQ:\s*(.+)$", line)
        if not m:
            continue

        kde = m.group(1).strip()
        req = m.group(2).strip()

        if not kde:
            kde = heuristic_kde_name(req)

        matched_req = None
        for original in original_requirements:
            if req == original:
                matched_req = original
                break
            if req in original or original in req:
                matched_req = original
                break

        if matched_req is None:
            matched_req = req

        if kde not in grouping:
            grouping[kde] = []

        if matched_req not in grouping[kde]:
            grouping[kde].append(matched_req)

        assigned_originals.add(matched_req)

    for req in original_requirements:
        if req not in assigned_originals:
            kde = heuristic_kde_name(req)
            if kde not in grouping:
                grouping[kde] = []
            if req not in grouping[kde]:
                grouping[kde].append(req)

    result = {}
    i = 1
    for kde_name, reqs in grouping.items():
        if reqs:
            result[f"element{i}"] = {
                "name": kde_name,
                "requirements": reqs
            }
            i += 1

    return result


def save_kdes_to_yaml(kde_dict: dict, output_file: str) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(kde_dict, f, sort_keys=False, allow_unicode=True)


def save_llm_log(llm_name: str, prompt_used: str, prompt_type: str, llm_output: str, output_file: str) -> None:
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"*LLM Name*\n{llm_name}\n")
        f.write(f"*Prompt Used*\n{prompt_used}\n")
        f.write(f"*Prompt Type*\n{prompt_type}\n")
        f.write(f"*LLM Output*\n{llm_output}\n")
        f.write("\n" + "=" * 80 + "\n\n")


def extract_kdes_from_pdf(
    pdf_path: str,
    prompt_type: str,
    output_yaml_dir: str,
    output_log_file: str,
    tokenizer,
    model
) -> dict:
    doc_text = load_pdf_text(pdf_path)
    requirements = extract_candidate_requirements(doc_text)

    if not requirements:
        kde_dict = {}
        pdf_name = Path(pdf_path).stem
        output_yaml_path = Path(output_yaml_dir) / f"{pdf_name}-kdes.yaml"
        save_kdes_to_yaml(kde_dict, str(output_yaml_path))
        save_llm_log(
            llm_name=MODEL_ID,
            prompt_used="NO REQUIREMENTS EXTRACTED",
            prompt_type=prompt_type,
            llm_output="NO REQUIREMENTS EXTRACTED",
            output_file=output_log_file,
        )
        return kde_dict

    if prompt_type == "zero-shot":
        prompt = build_grouping_prompt(requirements)
    elif prompt_type == "few-shot":
        prompt = build_few_shot_prompt(doc_text)
    elif prompt_type == "chain-of-thought":
        prompt = build_chain_of_thought_prompt(doc_text)
    else:
        raise ValueError("prompt_type must be 'zero-shot', 'few-shot', or 'chain-of-thought'")

    llm_output = generate_llm_output(prompt, tokenizer, model, max_new_tokens=400)
    kde_dict = parse_kde_assignment_output(llm_output, requirements)

    pdf_name = Path(pdf_path).stem
    output_yaml_path = Path(output_yaml_dir) / f"{pdf_name}-kdes.yaml"

    save_kdes_to_yaml(kde_dict, str(output_yaml_path))

    save_llm_log(
        llm_name=MODEL_ID,
        prompt_used=prompt,
        prompt_type=prompt_type,
        llm_output=llm_output,
        output_file=output_log_file,
    )

    return kde_dict


def process_two_pdfs(
    pdf1: str,
    pdf2: str,
    prompt_type: str,
    output_yaml_dir: str,
    output_log_file: str,
    tokenizer,
    model
) -> tuple[dict, dict]:
    kde_dict1 = extract_kdes_from_pdf(pdf1, prompt_type, output_yaml_dir, output_log_file, tokenizer, model)
    kde_dict2 = extract_kdes_from_pdf(pdf2, prompt_type, output_yaml_dir, output_log_file, tokenizer, model)
    return kde_dict1, kde_dict2