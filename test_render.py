import json
try:
    with open('roles/data/postgres_pgvector/templates/postgres_pgvector.yml.j2', 'r', encoding='utf-8') as f:
        content = f.read()
    print("Read content successfully")
except Exception as e:
    print("Error reading:", e)
