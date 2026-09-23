
# ============================================================
# Incremental ingestion source-contract tests
#
# No AWS credentials or Snowflake connection required.
# ============================================================

import csv
import tempfile
import unittest

from pathlib import Path

from scripts.generate_incremental_demo import (
    EXPECTED_COLUMNS,
    generate_demo_files,
    validate_csv_header,
)


class TestIncrementalDemo(unittest.TestCase):

    def test_generator_creates_expected_batches(self):

        with tempfile.TemporaryDirectory() as directory:

            paths = generate_demo_files(
                directory
            )

            self.assertEqual(
                len(paths),
                2,
            )

            for path in paths:

                self.assertTrue(
                    validate_csv_header(path)
                )

                with path.open(
                    newline="",
                    encoding="utf-8",
                ) as file:

                    rows = list(
                        csv.reader(file)
                    )

                # One header plus four data rows.
                self.assertEqual(
                    len(rows),
                    5,
                )


    def test_rejects_reordered_columns(self):

        with tempfile.TemporaryDirectory() as directory:

            path = (
                Path(directory)
                / "bad_header.csv"
            )

            with path.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as file:

                writer = csv.writer(file)

                writer.writerow(
                    list(reversed(EXPECTED_COLUMNS))
                )

                writer.writerow(
                    ["1", "2", "3", "4", "5"]
                )

            with self.assertRaises(ValueError):

                validate_csv_header(
                    path
                )


    def test_rejects_additional_column(self):

        with tempfile.TemporaryDirectory() as directory:

            path = (
                Path(directory)
                / "extra_column.csv"
            )

            with path.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as file:

                writer = csv.writer(file)

                writer.writerow(
                    EXPECTED_COLUMNS + ["unexpected"]
                )

            with self.assertRaises(ValueError):

                validate_csv_header(
                    path
                )


if __name__ == "__main__":
    unittest.main()