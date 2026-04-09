"""
Setup script to create BigQuery dataset and table for Deep Agent v2.0 analytics
Run: python setup_bigquery.py
"""

from google.cloud import bigquery

PROJECT_ID = ""
DATASET_ID = "analytics"
TABLE_ID = "query_logs"

def setup_bigquery():
    client = bigquery.Client(project=PROJECT_ID)
    
    # Create dataset
    dataset_id_full = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_id_full)
    dataset.location = "us-central1"
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"✅ Dataset {dataset_id_full} ready")
    
    # Create table
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("query", "STRING"),
        bigquery.SchemaField("agent", "STRING"),
        bigquery.SchemaField("complexity", "STRING"),
        bigquery.SchemaField("confidence", "FLOAT64"),
        bigquery.SchemaField("tier", "STRING"),
        bigquery.SchemaField("model_key", "STRING"),
        bigquery.SchemaField("model_label", "STRING"),
        bigquery.SchemaField("latency_ms", "INTEGER"),
        bigquery.SchemaField("routing_latency_ms", "INTEGER"),
        bigquery.SchemaField("tokens", "INTEGER"),
        bigquery.SchemaField("cost", "FLOAT64"),
        bigquery.SchemaField("fallback", "STRING"),
        bigquery.SchemaField("upgraded_from", "STRING"),
    ]
    
    table_id_full = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    table = bigquery.Table(table_id_full, schema=schema)
    table.clustering_fields = ["timestamp"]
    table = client.create_table(table, exists_ok=True)
    print(f"✅ Table {table_id_full} created with schema")
    print("\n📊 Table Schema:")
    for field in table.schema:
        print(f"  - {field.name}: {field.field_type}")

if __name__ == "__main__":
    try:
        setup_bigquery()
        print("\n✨ BigQuery setup complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have authenticated with: gcloud auth application-default login")
