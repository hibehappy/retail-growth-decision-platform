# ============================================================
# Retail Growth — CI quality gates
#
# Purpose:
# Run deterministic repository checks that do NOT require:
#
# - Snowflake credentials
# - AWS credentials
# - MLflow local state
# - Airflow services
#
# The same script can run:
# 1. On a developer machine before committing.
# 2. On a clean GitHub Actions runner after a push or PR.
#
# Run from the repository root:
#
# python scripts/ci_checks.py
# ============================================================

from pathlib import Path
import subprocess
import sys
import tempfile

import yaml


# ------------------------------------------------------------
# 1. Locate the repository
# ------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

DBT_PROJECT_DIR = (
    PROJECT_ROOT / "dbt"
)


# ------------------------------------------------------------
# 2. Small command runner
#
# check=True means:
#
# A nonzero exit code immediately fails the CI process.
#
# This is exactly what we want for a quality gate:
# one failed check means the overall build should fail.
# ------------------------------------------------------------

def run_command(
    command,
    *,
    cwd=PROJECT_ROOT,
):

    printable = " ".join(
        str(part)
        for part in command
    )

    print(
        f"\n{'=' * 70}\n"
        f"RUNNING: {printable}\n"
        f"{'=' * 70}"
    )

    subprocess.run(
        command,
        cwd=cwd,
        check=True,
    )


# ------------------------------------------------------------
# 3. Repository hygiene
#
# These paths contain:
#
# - generated datasets
# - model artifacts
# - local databases
# - credentials
# - Python environments
#
# They should NEVER be tracked by Git.
#
# .gitignore prevents future additions, but this check also
# catches files that were already tracked before the ignore
# rule was added.
# ------------------------------------------------------------

FORBIDDEN_TRACKED_PREFIXES = (
    "data/processed/",
    "data/models/",
    "data/mlflow/",
    "data/deployment/",
    "data/airflow/",
    "data/synthetic/",
    "project_env/",
    "airflow_env/",
)

FORBIDDEN_TRACKED_FILES = {
    ".env",
}


def check_repository_hygiene():

    result = subprocess.run(
        [
            "git",
            "ls-files",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    tracked_files = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    violations = []

    for file_path in tracked_files:

        if file_path in FORBIDDEN_TRACKED_FILES:

            violations.append(
                file_path
            )

            continue

        if any(
            file_path.startswith(prefix)
            for prefix
            in FORBIDDEN_TRACKED_PREFIXES
        ):

            violations.append(
                file_path
            )

    if violations:

        formatted = "\n".join(
            f"  - {path}"
            for path in violations
        )

        raise RuntimeError(
            "Forbidden generated/private files "
            "are tracked by Git:\n"
            f"{formatted}"
        )

    print(
        "PASS: Repository hygiene check."
    )


# ------------------------------------------------------------
# 4. Python syntax validation
#
# compileall parses the Python source without executing the
# application or requiring external services.
#
# This catches syntax errors in:
#
# - FastAPI code
# - reusable business logic
# - scripts
# - Airflow DAG Python files
#
# It does NOT replace unit tests.
# ------------------------------------------------------------

def check_python_syntax():

    paths = [
        "api",
        "src",
        "scripts",
        "orchestration/dags",
    ]

    existing_paths = [
        path
        for path in paths
        if (
            PROJECT_ROOT / path
        ).exists()
    ]

    run_command(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            *existing_paths,
        ]
    )

    print(
        "PASS: Python syntax check."
    )


# ------------------------------------------------------------
# 5. Unit tests
#
# These tests use synthetic inputs and temporary artifacts.
#
# They should NOT require Snowflake, AWS, Airflow, or a
# running FastAPI server.
# ------------------------------------------------------------

def check_unit_tests():

    run_command(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_*.py",
        ]
    )

    print(
        "PASS: Python unit tests."
    )


# ------------------------------------------------------------
# 6. dbt static parsing
#
# We want CI to answer:
#
# "Can dbt understand this project?"
#
# We do NOT want CI connecting to Snowflake.
#
# dbt still expects a profile, so create a temporary dummy
# Snowflake profile using the profile name declared in
# dbt_project.yml.
#
# dbt parse evaluates the project graph without executing
# warehouse SQL.
# ------------------------------------------------------------

def check_dbt_parse():

    project_config = yaml.safe_load(
        (
            DBT_PROJECT_DIR
            / "dbt_project.yml"
        ).read_text(
            encoding="utf-8"
        )
    )

    profile_name = (
        project_config.get("profile")
        or project_config["name"]
    )

    dummy_profile = {
        profile_name: {
            "target": "ci",
            "outputs": {
                "ci": {
                    "type": "snowflake",
                    "account":
                        "ci_placeholder",
                    "user":
                        "ci_placeholder",
                    "password":
                        "ci_placeholder",
                    "role":
                        "ci_placeholder",
                    "database":
                        "RETAIL_GROWTH",
                    "warehouse":
                        "RETAIL_DEV_WH",
                    "schema":
                        "CI",
                    "threads": 1,
                }
            },
        }
    }

    with tempfile.TemporaryDirectory() as directory:

        profiles_dir = Path(
            directory
        )

        (
            profiles_dir
            / "profiles.yml"
        ).write_text(
            yaml.safe_dump(
                dummy_profile,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        run_command(
            [
                "dbt",
                "parse",
                "--project-dir",
                str(DBT_PROJECT_DIR),
                "--profiles-dir",
                str(profiles_dir),
                "--no-partial-parse",
            ]
        )

    print(
        "PASS: dbt static parse."
    )


# ------------------------------------------------------------
# 7. Run all quality gates
# ------------------------------------------------------------

def main():

    print(
        "\nRetail Growth CI Quality Gates\n"
    )

    check_repository_hygiene()

    check_python_syntax()

    check_unit_tests()

    check_dbt_parse()

    print(
        "\n"
        "=" * 70
    )

    print(
        "PASS: All offline quality gates completed."
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()