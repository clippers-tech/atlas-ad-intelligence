"""CSV parser for bulk lead imports.

Expected columns: email, name, stage, revenue, notes
All columns except email are optional.
"""

import csv
import io
import logging
import re

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

_REQUIRED_COLUMNS = {"email"}
_OPTIONAL_COLUMNS = {"name", "stage", "revenue", "notes"}
_ALL_COLUMNS = _REQUIRED_COLUMNS | _OPTIONAL_COLUMNS


def _is_valid_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def _decode_bytes(content: bytes) -> str:
    """Try common encodings; fall back to latin-1 (never raises)."""
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("latin-1", errors="replace")


def parse_lead_csv(file_content: bytes) -> list[dict]:
    """Parse a CSV file of leads and return validated rows.

    Args:
        file_content: Raw bytes of the uploaded CSV file.

    Returns:
        List of dicts with keys: email, name, stage, revenue, notes.
        Rows with invalid or missing email are skipped with a warning.

    Raises:
        ValueError: If the CSV is missing the required `email` column.
    """
    text = _decode_bytes(file_content)
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise ValueError("CSV appears to be empty — no header row found")

    normalised_fields = {f.strip().lower() for f in reader.fieldnames}
    if "email" not in normalised_fields:
        raise ValueError(
            f"CSV must contain an 'email' column. Found: {list(reader.fieldnames)}"
        )

    results: list[dict] = []
    skipped = 0

    for line_num, raw_row in enumerate(reader, start=2):
        # Normalise keys to lowercase and strip whitespace
        row = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items()}

        email = row.get("email", "")
        if not email or not _is_valid_email(email):
            logger.warning("csv_parser: skipping row %d — invalid email %r", line_num, email)
            skipped += 1
            continue

        revenue_raw = row.get("revenue", "")
        revenue: float | None = None
        if revenue_raw:
            try:
                revenue = float(revenue_raw.replace(",", "").replace("£", "").replace("$", ""))
            except ValueError:
                logger.debug("csv_parser: row %d — could not parse revenue %r", line_num, revenue_raw)

        results.append(
            {
                "email": email.lower(),
                "name": row.get("name", ""),
                "stage": row.get("stage", ""),
                "revenue": revenue,
                "notes": row.get("notes", ""),
            }
        )

    logger.info(
        "csv_parser: parsed %d valid rows, skipped %d rows with invalid emails",
        len(results),
        skipped,
    )
    return results
