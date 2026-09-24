# ============================================================
# Retail Growth — Governance and lineage utilities
#
# Purpose:
#
# - calculate artifact checksums
# - inspect dbt lineage
# - trace upstream dependencies
# - create reusable governance reports
#
# dbt's manifest.json acts as the machine-readable source
# for transformation lineage.
# ============================================================

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


# ------------------------------------------------------------
# 1. File checksum
#
# SHA-256 provides a reproducible fingerprint of an artifact.
#
# If the file changes by even one byte, the checksum changes.
# ------------------------------------------------------------

def sha256_file(path):

    path = Path(path)

    hasher = hashlib.sha256()

    with path.open("rb") as file:

        while True:

            block = file.read(
                1024 * 1024
            )

            if not block:
                break

            hasher.update(
                block
            )

    return hasher.hexdigest()


# ------------------------------------------------------------
# 2. Load JSON artifact
# ------------------------------------------------------------

def load_json(path):

    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


# ------------------------------------------------------------
# 3. Locate a dbt model by its model name
#
# Example:
#
# mart_uplift_training
#
# becomes something like:
#
# model.retail_growth.mart_uplift_training
# ------------------------------------------------------------

def find_model_node(
    manifest,
    model_name,
):

    matches = []

    for unique_id, node in (
        manifest
        .get("nodes", {})
        .items()
    ):

        if (
            node.get("resource_type")
            == "model"
            and node.get("name")
            == model_name
        ):

            matches.append(
                (
                    unique_id,
                    node,
                )
            )

    if len(matches) != 1:

        raise ValueError(
            "Expected exactly one dbt model "
            f"named {model_name!r}; "
            f"found {len(matches)}."
        )

    return matches[0]


# ------------------------------------------------------------
# 4. Resolve any dbt resource
#
# Resources can live in:
#
# - nodes
# - sources
#
# This lets us trace all the way back to declared source
# tables rather than stopping at the first staging model.
# ------------------------------------------------------------

def resolve_resource(
    manifest,
    unique_id,
):

    if unique_id in manifest.get(
        "nodes",
        {},
    ):

        return manifest[
            "nodes"
        ][unique_id]

    if unique_id in manifest.get(
        "sources",
        {},
    ):

        return manifest[
            "sources"
        ][unique_id]

    return None


# ------------------------------------------------------------
# 5. Recursively trace upstream dependencies
# ------------------------------------------------------------

def collect_upstream_dependencies(
    manifest,
    unique_id,
    *,
    depth=0,
    visited=None,
):

    if visited is None:

        visited = set()

    if unique_id in visited:

        return []

    visited.add(
        unique_id
    )

    resource = resolve_resource(
        manifest,
        unique_id,
    )

    if resource is None:

        return []

    rows = []

    for parent_id in (
        resource
        .get(
            "depends_on",
            {},
        )
        .get(
            "nodes",
            [],
        )
    ):

        parent = resolve_resource(
            manifest,
            parent_id,
        )

        if parent is None:

            continue

        rows.append(
            {
                "unique_id":
                    parent_id,

                "name":
                    parent.get("name"),

                "resource_type":
                    parent.get(
                        "resource_type"
                    ),

                "depth":
                    depth + 1,

                "relation_name":
                    parent.get(
                        "relation_name"
                    ),

                "materialized":
                    parent.get(
                        "config",
                        {},
                    ).get(
                        "materialized"
                    ),
            }
        )

        rows.extend(
            collect_upstream_dependencies(
                manifest,
                parent_id,
                depth=depth + 1,
                visited=visited,
            )
        )

    return rows


# ------------------------------------------------------------
# 6. Build a tabular lineage report
# ------------------------------------------------------------

def build_lineage_report(
    manifest,
    model_names,
):

    rows = []

    for model_name in model_names:

        unique_id, node = (
            find_model_node(
                manifest,
                model_name,
            )
        )

        rows.append(
            {
                "target_model":
                    model_name,

                "unique_id":
                    unique_id,

                "name":
                    node.get("name"),

                "resource_type":
                    "model",

                "depth":
                    0,

                "relation_name":
                    node.get(
                        "relation_name"
                    ),

                "materialized":
                    node.get(
                        "config",
                        {},
                    ).get(
                        "materialized"
                    ),
            }
        )

        upstream = (
            collect_upstream_dependencies(
                manifest,
                unique_id,
            )
        )

        for row in upstream:

            rows.append(
                {
                    "target_model":
                        model_name,
                    **row,
                }
            )

    return (
        pd.DataFrame(rows)
        .drop_duplicates(
            subset=[
                "target_model",
                "unique_id",
            ]
        )
        .sort_values(
            [
                "target_model",
                "depth",
                "resource_type",
                "name",
            ]
        )
        .reset_index(
            drop=True
        )
    )