# tests/test_no_date_imports.py

import os
import ast

CALMOJI_DIR = os.path.join(os.path.dirname(__file__), "..", "calmoji")

def test_no_date_imports():
    offending = []

    for root, _, files in os.walk(CALMOJI_DIR):
        for fname in files:
            if not fname.endswith(".py"):
                continue

            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module == "datetime":
                            for alias in node.names:
                                if alias.name == "date":
                                    offending.append((filepath, node.lineno, "from datetime import date"))
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == "datetime.date":
                                offending.append((filepath, node.lineno, "import datetime.date"))

    assert not offending, (
        "Found disallowed 'date' imports:\n" +
        "\n".join(f"{file}:{line} — {code}" for file, line, code in offending)
    )
