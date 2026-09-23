
# ============================================================
# Retail Growth — Synthetic incremental ingestion data
#
# Purpose:
# Generate two small batches with known expected outcomes.
#
# These records are SYNTHETIC.
# They are not historical or newly observed X5 purchases.
#
# Run from the repository root:
# python scripts/generate_incremental_demo.py
# ============================================================

import csv
from pathlib import Path


# ------------------------------------------------------------
# 1. Define the source data contract.
#
# The field names and their order are part of the CSV
# interface agreed upon by the producer and consumer.
# ------------------------------------------------------------

EXPECTED_COLUMNS = [
    "event_id",
    "client_id",
    "event_ts",
    "amount",
    "schema_version",
]


# ------------------------------------------------------------
# 2. Create deterministic example batches.
#
# Batch 01:
#   Four valid events.
#
# Batch 02:
#   A repeated event_id with identical contents.
#   One new valid event.
#   One invalid monetary amount.
#   One invalid timestamp.
#
# Event timestamps are illustrative synthetic timestamps.
# ------------------------------------------------------------

BATCHES = {
    "batch_01.csv": [
        ["A100", "demo_customer_a", "2026-09-22 09:00:00", "25.50", "1"],
        ["B100", "demo_customer_b", "2026-09-22 09:05:00", "12.00", "1"],
        ["C100", "demo_customer_c", "2026-09-22 09:10:00", "48.25", "1"],
        ["D100", "demo_customer_d", "2026-09-22 09:15:00", "17.75", "1"],
    ],

    "batch_02.csv": [
        # Exact repeat of A100 from the first batch.
        ["A100", "demo_customer_a", "2026-09-22 09:00:00", "25.50", "1"],

        # One genuinely new valid event.
        ["E100", "demo_customer_e", "2026-09-22 10:00:00", "32.00", "1"],

        # Deliberately invalid amount.
        ["F100", "demo_customer_f", "2026-09-22 10:05:00", "not_a_number", "1"],

        # Deliberately invalid timestamp.
        ["G100", "demo_customer_g", "not_a_timestamp", "14.00", "1"],
    ],
}


# ------------------------------------------------------------
# 3. Validate file headers before upload.
#
# This detects missing, additional, or reordered columns.
#
# A CSV loader using positional fields could otherwise
# assign a value to the wrong destination column.
# ------------------------------------------------------------

def validate_csv_header(path):

    with Path(path).open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.reader(file)
        actual_columns = next(reader, None)

    if actual_columns != EXPECTED_COLUMNS:

        raise ValueError(
            "CSV header does not match the expected schema. "
            f"Expected {EXPECTED_COLUMNS}; "
            f"received {actual_columns}."
        )

    return True


# ------------------------------------------------------------
# 4. Write both batches.
#
# The same input always produces the same file contents.
# This makes reruns and unit tests reproducible.
# ------------------------------------------------------------

def generate_demo_files(output_dir):

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths = []

    for filename, rows in BATCHES.items():

        path = output_dir / filename

        with path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:

            writer = csv.writer(file)

            writer.writerow(EXPECTED_COLUMNS)
            writer.writerows(rows)

        validate_csv_header(path)

        paths.append(path)

    return paths


if __name__ == "__main__":

    project_root = (
        Path(__file__).resolve().parents[1]
    )

    output_dir = (
        project_root
        / "data"
        / "synthetic"
        / "incremental_demo"
    )

    paths = generate_demo_files(
        output_dir
    )

    for path in paths:
        print(f"Generated: {path}")