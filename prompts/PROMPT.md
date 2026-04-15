# Zero-shot

```text
You are analyzing a security requirements document.

Identify the key data elements (KDEs) in the document.
For each KDE:
1. Provide the KDE name
2. List all requirements associated with that KDE

Return the result in valid YAML using this structure:

element1:
  name: "example name"
  requirements:
    - "requirement 1"
    - "requirement 2"

Only return YAML. Do not include explanations.

Document:
{doc_text}

You are analyzing a security requirements document.

Example input:
The system shall encrypt passwords.
Passwords must be at least 12 characters long.

Example output:
element1:
  name: "passwords"
  requirements:
    - "The system shall encrypt passwords."
    - "Passwords must be at least 12 characters long."

Now analyze the following document and return only valid YAML.

Document:
{doc_text}

You are analyzing a security requirements document.

Think through the document carefully to determine:
1. What the key data elements are
2. Which requirements belong to each key data element

Then return only the final answer in valid YAML.

Use this structure:

element1:
  name: "example name"
  requirements:
    - "requirement 1"
    - "requirement 2"

Document:
{doc_text}

