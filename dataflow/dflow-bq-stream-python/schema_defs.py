from google.cloud import bigquery

# python client library schema definitions
ccl_messages_schema = [
    bigquery.SchemaField('pos_id', 'INT64', mode='REQUIRED'),
    bigquery.SchemaField('ts', 'DATETIME', mode='REQUIRED'),
    bigquery.SchemaField('zip', 'STRING', mode='REQUIRED'),
    bigquery.SchemaField('sale_amount', 'FLOAT', mode='REQUIRED')
]

ccl_messages_nested_schema = [
    bigquery.SchemaField('window_ending', 'DATETIME', mode='REQUIRED'),
    bigquery.SchemaField('pos_id', 'INT64', mode='REQUIRED'),
    bigquery.SchemaField(
        'transactions', 
        'RECORD', 
        mode='REPEATED',
        fields=[
            bigquery.SchemaField('ts', 'DATETIME', mode='REQUIRED'),
            bigquery.SchemaField('zip', 'STRING', mode='REQUIRED'),
            bigquery.SchemaField('sale_amount', 'FLOAT', mode='REQUIRED')
        ]
    )
]

# beam biqueryio schema definitions
beam_messages_schema = {
    "fields": [
        {
            "name": "pos_id",
            "type": "INT64",
            "mode": 'REQUIRED'
        },
        {
            "name": "ts",
            "type": "DATETIME",
            "mode": 'REQUIRED'
        },
        {
            "name": "zip",
            "type": "STRING",
            "mode": 'REQUIRED'
        },
        {
            "name": "sale_amount",
            "type": "FLOAT",
            "mode": 'REQUIRED'
        }
    ]
}

beam_messages_nested_schema = {
    "fields": [
        {
            "name": "window_ending",
            "type": "DATETIME",
            "mode": 'REQUIRED'
        },
        {
            "name": "post_id",
            "type": "INT64",
            "mode": 'REQUIRED'
        },
        {
            "name": "transactions",
            "type": "RECORD",
            "mode": 'REPEATED',
            "fields": [
                {
                    "name": "ts",
                    "type": "DATETIME",
                    "mode": 'REQUIRED'
                },
                {
                    "name": "zip",
                    "type": "STRING",
                    "mode": 'REQUIRED'
                },
                {
                    "name": "sale_amount",
                    "type": "float",
                    "mode": 'REQUIRED'
                },
            ]
        }
    ]
}