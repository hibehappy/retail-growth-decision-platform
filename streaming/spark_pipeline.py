# ============================================================
# Retail Growth — Kafka + Spark Structured Streaming pipeline
#
# Purpose:
#
# Kafka
#   ↓
# parse JSON
#   ↓
# apply data contract
#   ↓
# valid / invalid split
#   ↓
# watermark + stateful event-ID deduplication
#   ↓
# Parquet trusted + quarantine outputs
#
# The pipeline uses Spark checkpoints to preserve streaming
# offsets and state across application restarts.
# ============================================================

from pathlib import Path
import argparse
import shutil

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StringType,
    StructField,
    StructType,
)


# ------------------------------------------------------------
# 1. Project paths
# ------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

STREAM_DIR = (
    PROJECT_ROOT
    / "data"
    / "streaming"
)

VALID_OUTPUT = (
    STREAM_DIR
    / "output"
    / "valid"
)

QUARANTINE_OUTPUT = (
    STREAM_DIR
    / "output"
    / "quarantine"
)

VALID_CHECKPOINT = (
    STREAM_DIR
    / "checkpoints"
    / "valid"
)

QUARANTINE_CHECKPOINT = (
    STREAM_DIR
    / "checkpoints"
    / "quarantine"
)


BOOTSTRAP_SERVERS = "localhost:9092"

TOPIC = "retail-growth-events"


# ------------------------------------------------------------
# 2. Incoming JSON contract
#
# Preserve potentially invalid amount/timestamp values as
# strings first.
#
# Parsing and validation happen AFTER deserialization.
# ------------------------------------------------------------

EVENT_SCHEMA = StructType(
    [
        StructField(
            "event_id",
            StringType(),
            True,
        ),
        StructField(
            "client_id",
            StringType(),
            True,
        ),
        StructField(
            "event_ts",
            StringType(),
            True,
        ),
        StructField(
            "amount",
            StringType(),
            True,
        ),
        StructField(
            "schema_version",
            StringType(),
            True,
        ),
    ]
)


def build_spark():

    # Spark's Kafka connector is an external package.
    #
    # Spark 4 uses Scala 2.13, so the connector artifact
    # uses the _2.13 suffix.
    return (
        SparkSession.builder
        .appName(
            "retail-growth-streaming"
        )
        .config(
            "spark.jars.packages",
            (
                "org.apache.spark:"
                "spark-sql-kafka-0-10_2.13:"
                "4.2.0"
            ),
        )
        .config(
            "spark.sql.shuffle.partitions",
            "3",
        )
        .getOrCreate()
    )


def build_stream(spark):

    # --------------------------------------------------------
    # Kafka exposes each message with metadata including:
    #
    # key
    # value
    # topic
    # partition
    # offset
    # timestamp
    #
    # Spark receives key/value as bytes, so cast them
    # explicitly to strings.
    # --------------------------------------------------------

    kafka_stream = (
        spark.readStream
        .format("kafka")
        .option(
            "kafka.bootstrap.servers",
            BOOTSTRAP_SERVERS,
        )
        .option(
            "subscribe",
            TOPIC,
        )
        .option(
            "startingOffsets",
            "earliest",
        )
        .load()
    )

    decoded = (
        kafka_stream
        .select(
            F.col("key")
            .cast("string")
            .alias("kafka_key"),

            F.col("value")
            .cast("string")
            .alias("raw_json"),

            F.col("partition")
            .alias("kafka_partition"),

            F.col("offset")
            .alias("kafka_offset"),

            F.col("timestamp")
            .alias("kafka_timestamp"),
        )
    )

    # --------------------------------------------------------
    # Deserialize JSON.
    #
    # Invalid JSON returns a null parsed structure and can
    # therefore be quarantined rather than crashing the job.
    # --------------------------------------------------------

    parsed = (
        decoded
        .withColumn(
            "payload",
            F.from_json(
                F.col("raw_json"),
                EVENT_SCHEMA,
            ),
        )
        .select(
            "kafka_key",
            "raw_json",
            "kafka_partition",
            "kafka_offset",
            "kafka_timestamp",

            F.col("payload.event_id")
            .alias("event_id"),

            F.col("payload.client_id")
            .alias("client_id"),

            F.col("payload.event_ts")
            .alias("event_ts_raw"),

            F.col("payload.amount")
            .alias("amount_raw"),

            F.col("payload.schema_version")
            .alias("schema_version"),

            F.col("payload")
            .isNull()
            .alias("invalid_json"),
        )
    )

    # --------------------------------------------------------
    # Spark 4 uses ANSI SQL behavior.
    #
    # TRY_CAST / TRY_TO_TIMESTAMP return NULL for invalid
    # source values rather than terminating the stream.
    # --------------------------------------------------------

    typed = (
        parsed
        .withColumn(
            "event_ts",
            F.expr(
                "try_to_timestamp(event_ts_raw)"
            ),
        )
        .withColumn(
            "amount",
            F.expr(
                "try_cast(amount_raw "
                "AS DECIMAL(12,2))"
            ),
        )
    )

    # --------------------------------------------------------
    # Apply the incoming event data contract.
    # --------------------------------------------------------

    classified = (
        typed
        .withColumn(
            "rejection_reason",

            F.when(
                F.col("invalid_json"),
                F.lit("INVALID_JSON"),
            )
            .when(
                F.col("event_id").isNull()
                | (
                    F.trim(
                        F.col("event_id")
                    ) == ""
                ),
                F.lit("MISSING_EVENT_ID"),
            )
            .when(
                F.col("client_id").isNull()
                | (
                    F.trim(
                        F.col("client_id")
                    ) == ""
                ),
                F.lit("MISSING_CLIENT_ID"),
            )
            .when(
                F.col("schema_version") != "1",
                F.lit(
                    "UNSUPPORTED_SCHEMA_VERSION"
                ),
            )
            .when(
                F.col("event_ts").isNull(),
                F.lit(
                    "INVALID_EVENT_TIMESTAMP"
                ),
            )
            .when(
                F.col("amount").isNull()
                | (
                    F.col("amount") < 0
                ),
                F.lit("INVALID_AMOUNT"),
            )
        )
    )

    return classified


def start_queries(classified):

    # --------------------------------------------------------
    # Invalid records:
    #
    # Preserve source JSON and Kafka provenance.
    # --------------------------------------------------------

    quarantine = (
        classified
        .filter(
            F.col(
                "rejection_reason"
            ).isNotNull()
        )
        .select(
            "event_id",
            "client_id",
            "event_ts_raw",
            "amount_raw",
            "schema_version",
            "rejection_reason",
            "raw_json",
            "kafka_partition",
            "kafka_offset",
            "kafka_timestamp",
        )
    )

    # --------------------------------------------------------
    # Valid records:
    #
    # Apply a 10-minute event-time watermark.
    #
    # dropDuplicatesWithinWatermark maintains streaming state
    # so retries of the same event_id can be suppressed while
    # that key remains inside the watermark horizon.
    # --------------------------------------------------------

    valid = (
        classified
        .filter(
            F.col(
                "rejection_reason"
            ).isNull()
        )
        .select(
            "event_id",
            "client_id",
            "event_ts",
            "amount",
            "schema_version",
            "kafka_partition",
            "kafka_offset",
            "kafka_timestamp",
        )
        .withWatermark(
            "event_ts",
            "10 minutes",
        )
        .dropDuplicatesWithinWatermark(
            ["event_id"]
        )
    )

    # --------------------------------------------------------
    # AvailableNow:
    #
    # Process everything currently available in Kafka and
    # stop once the backlog has been consumed.
    #
    # This gives us deterministic notebook demonstrations
    # while still using the Structured Streaming engine.
    # --------------------------------------------------------

    valid_query = (
        valid.writeStream
        .format("parquet")
        .outputMode("append")
        .option(
            "path",
            str(VALID_OUTPUT),
        )
        .option(
            "checkpointLocation",
            str(VALID_CHECKPOINT),
        )
        .trigger(
            availableNow=True
        )
        .start()
    )

    quarantine_query = (
        quarantine.writeStream
        .format("parquet")
        .outputMode("append")
        .option(
            "path",
            str(QUARANTINE_OUTPUT),
        )
        .option(
            "checkpointLocation",
            str(
                QUARANTINE_CHECKPOINT
            ),
        )
        .trigger(
            availableNow=True
        )
        .start()
    )

    valid_query.awaitTermination()

    quarantine_query.awaitTermination()


def reset_stream_state():

    # --------------------------------------------------------
    # Reset BOTH outputs and checkpoints together.
    #
    # Deleting only checkpoints while keeping output data
    # could cause previously processed Kafka records to be
    # written again.
    # --------------------------------------------------------

    if STREAM_DIR.exists():

        shutil.rmtree(
            STREAM_DIR
        )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--reset",
        action="store_true",
    )

    args = parser.parse_args()

    if args.reset:

        reset_stream_state()

    spark = build_spark()

    spark.sparkContext.setLogLevel(
        "WARN"
    )

    try:

        classified = build_stream(
            spark
        )

        start_queries(
            classified
        )

    finally:

        spark.stop()

    print(
        "Streaming backlog processed."
    )