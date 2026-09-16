{% macro generate_transaction_key(transaction_id, client_id) %}

    sha2(
        concat_ws(
            '||',
            coalesce(cast({{ transaction_id }} as varchar), '__NULL__'),
            coalesce(cast({{ client_id }} as varchar), '__NULL__')
        ),
        256
    )

{% endmacro %}