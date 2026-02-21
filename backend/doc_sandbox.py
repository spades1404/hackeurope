"""
Sandboxed document generation.

When a compliance document needs to be produced:
1. The AI agent is prompted with the obligation details + available data schema
2. It generates a Python script that queries data and computes the filing
3. The script runs in a subprocess sandbox with injected DB data
4. Output is parsed into the standard document JSON structure
5. Script + output are stored for audit

The sandbox receives pre-fetched data (NOT direct DB access) to keep it safe.
"""

import subprocess
import tempfile
import json
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

EXECUTION_TIMEOUT = 30  # seconds — tax calculations may need more time than simple analysis
MAX_OUTPUT_SIZE = 100000  # chars

# Prompt sent to the AI to generate the script
SCRIPT_GENERATION_PROMPT = """You are a tax computation engine. Generate a Python script that:

1. Reads financial data from the pre-loaded `data` dictionary
2. Performs the required calculations for: {obligation_name} ({form_number})
3. Jurisdiction: {jurisdiction} | Period: {period}
4. Tax rules to apply:
{tax_rules}

5. Outputs a JSON document to stdout using print(json.dumps(result))

The `data` dict contains:
- data["transactions"]: list of transaction dicts with keys: id, amount, currency, transaction_type, category, date, jurisdiction
- data["summary"]: pre-aggregated financial summary with keys like gross_revenue, cost_of_goods_sold, operating_expenses, etc.
- data["company"]: company profile dict
- data["obligation"]: the obligation details from the knowledge base

Your output JSON MUST have this structure:
{{
    "document_type": "string",
    "form": "string",
    "title": "string",
    "jurisdiction": "string",
    "period": "string",
    "sections": [
        {{
            "name": "Section Name",
            "fields": {{"Field Label": "Computed Value"}}
        }}
    ],
    "computed_values": {{
        "taxable_income": 0,
        "tax_rate": 0,
        "tax_liability": 0,
        "net_tax_payable": 0
    }},
    "warnings": [],
    "notes": "Explanation of computation methodology"
}}

Available imports: json, math, statistics, datetime, collections, decimal, re
Use print(json.dumps(result, indent=2, default=str)) as the LAST line.
Do NOT import anything else. Do NOT use file I/O. Do NOT make network calls.
"""


async def generate_document_via_ai(
    obligation: dict,
    company_profile: dict,
    financial_data: dict,
    transactions: list,
    llm_chat_fn: callable,
) -> dict:
    """
    Full pipeline:
    1. Ask AI to generate computation script
    2. Run script in sandbox with data
    3. Parse output
    4. Return document + script for audit
    """

    # Step 1: Generate the script via AI
    tax_rules = _build_tax_rules_context(obligation)
    prompt = SCRIPT_GENERATION_PROMPT.format(
        obligation_name=obligation.get("name", "Tax Filing"),
        form_number=obligation.get("form", "N/A"),
        jurisdiction=obligation.get("jurisdiction_name", "Unknown"),
        period=obligation.get("period", "Current"),
        tax_rules=tax_rules,
    )

    ai_response = await llm_chat_fn(
        messages=[{"role": "user", "content": prompt}],
        system="You are a precise tax computation engine. Output ONLY the Python script, no markdown fences, no explanation.",
        temperature=0.2,  # Low temp for deterministic code generation
    )

    script_code = _extract_code(ai_response.get("content", ""))
    if not script_code:
        return {"error": "AI failed to generate a valid script", "raw_response": ai_response}

    # Step 2: Prepare data context
    data_context = {
        "transactions": transactions,
        "summary": financial_data,
        "company": company_profile,
        "obligation": obligation,
    }

    # Step 3: Execute in sandbox
    exec_result = await execute_in_sandbox(script_code, data_context)

    if not exec_result["success"]:
        # Retry once with error feedback
        retry_prompt = f"The previous script had an error:\n{exec_result['error']}\n\nFix the script and try again. Output ONLY the corrected Python script."
        retry_response = await llm_chat_fn(
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": script_code},
                {"role": "user", "content": retry_prompt},
            ],
            system="You are a precise tax computation engine. Output ONLY the Python script.",
            temperature=0.1,
        )
        script_code = _extract_code(retry_response.get("content", ""))
        if script_code:
            exec_result = await execute_in_sandbox(script_code, data_context)

    if not exec_result["success"]:
        return {
            "error": f"Script execution failed: {exec_result['error']}",
            "script": script_code,
        }

    # Step 4: Parse output
    try:
        document = json.loads(exec_result["output"])
    except json.JSONDecodeError:
        return {
            "error": "Script output was not valid JSON",
            "raw_output": exec_result["output"],
            "script": script_code,
        }

    # Step 5: Attach metadata
    document["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "generated_by": "ai_sandbox",
        "script_hash": hash(script_code),
        "status": "draft",
        "requires_approval": True,
    }
    document["_audit"] = {
        "script": script_code,
        "execution_output": exec_result["output"][:5000],
    }

    return document


async def execute_in_sandbox(code: str, data_context: dict) -> dict:
    """Run AI-generated Python in a restricted subprocess."""

    validation = _validate_code(code)
    if not validation["safe"]:
        return {"success": False, "output": "", "error": validation["reason"]}

    sandbox_script = f'''
import json, math, statistics, datetime, collections, decimal, re
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

_raw = """{json.dumps(data_context, default=str).replace(chr(92), chr(92)+chr(92)).replace('"', chr(92)+'"')}"""
data = json.loads(_raw.replace('\\\\"', '"'))

transactions = data.get("transactions", [])
summary = data.get("summary", {{}})
company = data.get("company", {{}})
obligation = data.get("obligation", {{}})

{code}
'''

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sandbox_script)
            f.flush()
            result = subprocess.run(
                [sys.executable, "-u", f.name],
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT,
                env={"PATH": "/usr/bin:/usr/local/bin", "PYTHONDONTWRITEBYTECODE": "1"},
            )
        output = result.stdout[:MAX_OUTPUT_SIZE]
        error = result.stderr[:MAX_OUTPUT_SIZE] if result.returncode != 0 else None
        return {"success": result.returncode == 0, "output": output, "error": error}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Execution timed out ({EXECUTION_TIMEOUT}s limit)"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
    finally:
        try:
            os.unlink(f.name)
        except:
            pass


def _validate_code(code: str) -> dict:
    blocked = [
        "import os", "import sys", "import subprocess", "import shutil",
        "import socket", "import http", "import urllib", "import requests",
        "open(", "__import__", "exec(", "eval(", "compile(",
        "import pickle", "import sqlite3", "import asyncio",
        "globals()", "locals()", "getattr", "setattr", "delattr",
        "breakpoint()", "import signal", "import ctypes",
    ]
    for pattern in blocked:
        if pattern in code:
            return {"safe": False, "reason": f"Blocked: {pattern}"}
    return {"safe": True, "reason": None}


def _extract_code(text: str) -> str:
    """Extract Python code from AI response, stripping markdown fences."""
    text = text.strip()
    if text.startswith("```python"):
        text = text[len("```python"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text if text else None


def _build_tax_rules_context(obligation: dict) -> str:
    """Build a text description of the tax rules the AI should apply."""
    rules = []
    if obligation.get("tax_rate"):
        rules.append(f"- Tax rate: {obligation['tax_rate'] * 100:.1f}%")
    if obligation.get("standard_rate"):
        rules.append(f"- Standard VAT/GST rate: {obligation['standard_rate'] * 100:.0f}%")
    if obligation.get("reduced_rate"):
        rules.append(f"- Reduced rate: {obligation['reduced_rate'] * 100:.0f}%")
    if obligation.get("small_profits_rate"):
        rules.append(f"- Small profits rate: {obligation['small_profits_rate'] * 100:.1f}% (threshold: {obligation.get('small_profits_threshold', 'N/A')})")
    if obligation.get("penalty_for_late_filing"):
        rules.append(f"- Late filing penalty: {obligation['penalty_for_late_filing']}")
    rules.append(f"- Required data fields: {', '.join(obligation.get('required_data', []))}")
    return "\n".join(rules) if rules else "Standard computation rules apply."
