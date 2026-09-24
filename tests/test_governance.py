import tempfile
import unittest

from pathlib import Path

from src.governance import (
    build_lineage_report,
    find_model_node,
    sha256_file,
)


class TestGovernance(unittest.TestCase):

    def test_sha256_is_stable(self):

        with tempfile.TemporaryDirectory() as directory:

            path = (
                Path(directory)
                / "artifact.txt"
            )

            path.write_text(
                "retail-growth",
                encoding="utf-8",
            )

            first = sha256_file(
                path
            )

            second = sha256_file(
                path
            )

            self.assertEqual(
                first,
                second,
            )


    def test_sha256_changes_when_file_changes(
        self,
    ):

        with tempfile.TemporaryDirectory() as directory:

            path = (
                Path(directory)
                / "artifact.txt"
            )

            path.write_text(
                "version-1",
                encoding="utf-8",
            )

            first = sha256_file(
                path
            )

            path.write_text(
                "version-2",
                encoding="utf-8",
            )

            second = sha256_file(
                path
            )

            self.assertNotEqual(
                first,
                second,
            )


    def test_find_model_node(self):

        manifest = {
            "nodes": {
                "model.demo.target": {
                    "name": "target",
                    "resource_type":
                        "model",
                }
            }
        }

        unique_id, node = (
            find_model_node(
                manifest,
                "target",
            )
        )

        self.assertEqual(
            unique_id,
            "model.demo.target",
        )

        self.assertEqual(
            node["name"],
            "target",
        )


    def test_lineage_traces_source(
        self,
    ):

        manifest = {

            "nodes": {

                "model.demo.target": {
                    "name":
                        "target",

                    "resource_type":
                        "model",

                    "depends_on": {
                        "nodes": [
                            "model.demo.staging"
                        ]
                    },

                    "config": {
                        "materialized":
                            "table"
                    },
                },

                "model.demo.staging": {
                    "name":
                        "staging",

                    "resource_type":
                        "model",

                    "depends_on": {
                        "nodes": [
                            "source.demo.raw"
                        ]
                    },

                    "config": {
                        "materialized":
                            "view"
                    },
                },
            },

            "sources": {

                "source.demo.raw": {
                    "name":
                        "raw",

                    "resource_type":
                        "source",

                    "depends_on": {
                        "nodes": []
                    },
                }
            },
        }

        report = build_lineage_report(
            manifest,
            ["target"],
        )

        names = set(
            report["name"]
        )

        self.assertEqual(
            names,
            {
                "target",
                "staging",
                "raw",
            },
        )


if __name__ == "__main__":
    unittest.main()