"""PII Masking Utility.

Automatically masks sensitive customer columns (email, phone, full names)
before query results are passed to LLM prompts, logs, or non-admin responses.
"""

import re
from typing import Any, Dict, List


PII_EMAIL_COLUMNS = {"email", "user_email", "customer_email"}
PII_PHONE_COLUMNS = {"phone", "phone_number", "mobile", "contact_number"}
PII_NAME_COLUMNS = {"first_name", "last_name", "full_name", "customer_name"}

EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")


def mask_email(value: Any) -> Any:
    """Mask an email address like 'rohan.sharma@example.com' -> 'r***@example.com'."""
    if not isinstance(value, str) or "@" not in value:
        return value
    local, domain = value.split("@", 1)
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}***@{domain}"


def mask_phone(value: Any) -> Any:
    """Mask a phone number like '+91-9876543210' -> '******3210'."""
    if not isinstance(value, str) or not value.strip():
        return value
    digits = re.sub(r"\D", "", value)
    if len(digits) <= 4:
        return "****"
    return "*" * (len(digits) - 4) + digits[-4:]


def mask_name(value: Any) -> Any:
    """Mask a personal name like 'Rohan' -> 'R***'."""
    if not isinstance(value, str) or not value.strip():
        return value
    s = value.strip()
    if len(s) <= 1:
        return "*"
    return f"{s[0]}***"


def mask_rows(rows: List[Dict[str, Any]], mask_pii: bool = True) -> List[Dict[str, Any]]:
    """Return a copy of rows with PII columns masked when mask_pii is True."""
    if not mask_pii or not rows:
        return rows

    masked_rows: List[Dict[str, Any]] = []
    for row in rows:
        new_row: Dict[str, Any] = {}
        for col, val in row.items():
            col_lower = col.lower()
            if col_lower in PII_EMAIL_COLUMNS:
                new_row[col] = mask_email(val)
            elif col_lower in PII_PHONE_COLUMNS:
                new_row[col] = mask_phone(val)
            elif col_lower in PII_NAME_COLUMNS:
                new_row[col] = mask_name(val)
            elif isinstance(val, str) and EMAIL_REGEX.search(val):
                new_row[col] = EMAIL_REGEX.sub(lambda m: mask_email(m.group(0)), val)
            else:
                new_row[col] = val
        masked_rows.append(new_row)
    return masked_rows
