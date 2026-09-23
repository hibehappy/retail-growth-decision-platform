# ============================================================
# Retail Growth — synthetic streaming events
#
# These events are used only for the Kafka/Spark demonstration.
#
# They are NOT X5 observations and must never be mixed with
# the project's historical retail datasets.
# ============================================================


def base_events():

    return [
        {
            "event_id": "STREAM_A100",
            "client_id": "stream_customer_a",
            "event_ts": "2026-09-23 10:00:00",
            "amount": "25.50",
            "schema_version": "1",
        },
        {
            "event_id": "STREAM_B100",
            "client_id": "stream_customer_b",
            "event_ts": "2026-09-23 10:01:00",
            "amount": "12.00",
            "schema_version": "1",
        },
        {
            "event_id": "STREAM_C100",
            "client_id": "stream_customer_c",
            "event_ts": "2026-09-23 10:02:00",
            "amount": "48.25",
            "schema_version": "1",
        },
        {
            "event_id": "STREAM_D100",
            "client_id": "stream_customer_d",
            "event_ts": "2026-09-23 10:03:00",
            "amount": "17.75",
            "schema_version": "1",
        },

        # Exact retry of A100.
        {
            "event_id": "STREAM_A100",
            "client_id": "stream_customer_a",
            "event_ts": "2026-09-23 10:00:00",
            "amount": "25.50",
            "schema_version": "1",
        },

        # Invalid amount.
        {
            "event_id": "STREAM_F100",
            "client_id": "stream_customer_f",
            "event_ts": "2026-09-23 10:04:00",
            "amount": "not_a_number",
            "schema_version": "1",
        },

        # Invalid event timestamp.
        {
            "event_id": "STREAM_G100",
            "client_id": "stream_customer_g",
            "event_ts": "not_a_timestamp",
            "amount": "14.00",
            "schema_version": "1",
        },
    ]


def retry_event():

    return {
        "event_id": "STREAM_A100",
        "client_id": "stream_customer_a",
        "event_ts": "2026-09-23 10:00:00",
        "amount": "25.50",
        "schema_version": "1",
    }